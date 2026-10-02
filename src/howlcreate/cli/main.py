"""Command-line interface for HowlCreate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from howlcreate import __version__
from howlcreate.engine.pipeline import CreativePipeline, PipelineConfig
from howlcreate.engine.storage import RunStorage
from howlcreate.formatting import (
    export_howlframe_contract,
    export_howlplane_contract,
    format_markdown_report,
    to_ascii_tree,
    to_mermaid,
)
from howlcreate.operators.assumptions import AssumptionOperator
from howlcreate.operators.reframing import ReframingOperator
from howlcreate.providers.registry import registry
from howlcreate.providers.runtime import RemoteCommandProvider, TrackedProvider, FallbackProvider
from howl_provider_core import CallBudget, CommandConfig


def _provider(args):
    def resolve(name):
        if name == "command":
            if getattr(args, "model", None):
                raise ValueError("command model selection belongs in reviewed argv, not --model")
            if not getattr(args, "command_config", None):
                raise ValueError("command requires explicit --command-config")
            return RemoteCommandProvider(CommandConfig.read(Path(args.command_config)))
        return registry.get_provider(name, allow_local=getattr(args, "allow_local", False))

    primary = resolve(args.provider)
    fallback = getattr(args, "fallback", [])
    if fallback:
        # Resolve and validate the entire authorized chain before the first call.
        return FallbackProvider([primary] + [resolve(name) for name in fallback], args.provider)
    return primary


def _print_step(phase: str, payload: dict) -> None:
    if phase == "phase":
        print(f"  [>] {payload.get('name')}...", flush=True)
    elif phase == "start":
        print(f"\n[HowlCreate] Initializing creative run: {payload.get('run_id')}")
        print(f'  Problem: "{payload.get("problem")}"\n')
    elif phase == "complete":
        print(
            f"\n[HowlCreate] Exploration finished: {payload.get('total_concepts_explored')} concepts explored across divergent branches."
        )
        print(f"  Converged to {payload.get('finalists_selected')} top diverse finalists.\n")


def cmd_explore(args: argparse.Namespace) -> int:
    """Execute the full divergent & convergent creative exploration pipeline."""
    hard_constraints = (
        getattr(args, "hard_constraints", None) or getattr(args, "hard_constraint", None) or []
    )
    config = PipelineConfig(
        top_n=args.top_n,
        max_calls=args.max_calls,
        repair_attempts=args.repair_attempts,
        ecosystem_fit_weight=args.ecosystem_fit_weight,
        provider_name=args.provider,
        hard_constraints=hard_constraints,
        on_step_callback=_print_step if not args.quiet else None,
    )
    pipeline = CreativePipeline(config=config)

    # Optional model override
    provider = _provider(args)
    if args.model:
        provider.model_name = args.model

    source = None
    if args.from_dream:
        from howlcreate.engine.candidate_ingestion import validate_dream_source

        source = validate_dream_source(json.loads(args.from_dream.read_text()))
    if not args.problem and source is None:
        raise ValueError("explore requires a problem or --from-dream")
    record = pipeline.execute(
        args.problem or source["objective"], provider=provider, source_candidate=source
    )

    format_type = args.format
    if not format_type:
        if args.output and args.output.endswith(".json"):
            format_type = "json"
        else:
            format_type = "markdown"

    if format_type == "json":
        output_text = json.dumps(record.to_dict(), indent=2)
    else:
        output_text = format_markdown_report(record)

    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
        print(f"[Saved] Output written to: {args.output}")
    else:
        print(output_text)

    return 0 if record.metadata.get("status") == "COMPLETE" else 1


def cmd_resume(args):
    pipeline = CreativePipeline()
    record = pipeline.resume(args.run_id, provider=_provider(args))
    text = json.dumps(record.to_dict(), indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0 if record.metadata.get("status") == "COMPLETE" else 1


def cmd_assumptions(args: argparse.Namespace) -> int:
    """Extract explicit & implicit assumptions and generate inversions."""
    provider = _provider(args)
    if args.model:
        provider.model_name = args.model

    op = AssumptionOperator()
    provider = TrackedProvider(provider, CallBudget(args.max_calls), args.provider)
    res = op.execute(args.problem, provider)

    print(f'\n# Assumptions & Inversions for: "{args.problem}"\n')
    for a in res.assumptions:
        print(f"- Assumption ({'Implicit' if a.is_implicit else 'Explicit'}): {a.statement}")
        if a.vulnerability:
            print(f"  Vulnerability: {a.vulnerability}")
        for inv in a.inversions:
            print(f"  * Radical Inversion: {inv}")
        print()

    if res.ideas:
        print("### Derived Inversion Concepts:")
        for idea in res.ideas:
            print(f"- {idea.title}: {idea.core_mechanism or idea.description}")
        print()

    return 0


def cmd_reframe(args: argparse.Namespace) -> int:
    """Reframe a problem through diverse stakeholder perspectives."""
    provider = _provider(args)
    if args.model:
        provider.model_name = args.model

    op = ReframingOperator()
    provider = TrackedProvider(provider, CallBudget(args.max_calls), args.provider)
    res = op.execute(args.problem, provider)

    print(f'\n# Reframing Lenses for: "{args.problem}"\n')
    for r in res.reframings:
        print(f"## Perspective: {r.perspective}")
        print(f"  Reframed Question: {r.reframed_question}")
        print(f"  Focus: {r.core_focus}\n")

    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Display an existing run by ID or file path."""
    storage = RunStorage()
    try:
        record = storage.load_run(args.run_id)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(record.to_dict(), indent=2))
    else:
        print(format_markdown_report(record))
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    """Render concept lineage graph in Mermaid or ASCII tree."""
    storage = RunStorage()
    try:
        record = storage.load_run(args.run_id)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.mermaid:
        print(to_mermaid(record.graph))
    else:
        print(f"\nConcept Lineage Graph for Run: {record.run_id}\n")
        print(to_ascii_tree(record.graph))
        print()
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export machine-readable ecosystem handoff contract."""
    storage = RunStorage()
    try:
        record = storage.load_run(args.run_id)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.target == "plane":
        payload = export_howlplane_contract(record)
    elif args.target == "dream":
        from howlcreate.formatting.dream import export_dream_candidate

        if not args.candidate_id:
            raise ValueError("--target dream requires --candidate-id")
        payload = export_dream_candidate(record, args.candidate_id)
    elif args.target == "frame":
        payload = export_howlframe_contract(record)
    else:
        payload = record.to_dict()

    text = json.dumps(payload, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"[Exported] Contract written to {args.output}")
    else:
        print(text)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all persisted runs."""
    storage = RunStorage()
    runs = storage.list_runs()
    if not runs:
        print("No stored runs found.")
        return 0

    print(f"\n{'Run ID':<16} {'Created':<26} {'Finalists':<10} Problem")
    print("-" * 80)
    for r in runs:
        print(
            f"{r['run_id']:<16} {r['created_at'][:19]:<26} {r['finalists_count']:<10} {r['problem'][:35]}..."
        )
    print()
    return 0


def cmd_develop(args: argparse.Namespace) -> int:
    """Ingest a candidate handoff and assessment, producing a deliberate development plan."""
    from howlcreate.engine.candidate_ingestion import (
        develop_candidate,
        scaffold_candidate,
        IngestionError,
        develop_from_dream,
    )

    try:
        if bool(args.candidate_file) == bool(args.from_dream):
            raise IngestionError("Supply a candidate file or --from-dream")
        candidate_path = args.from_dream or Path(args.candidate_file)
        cand_data = json.loads(candidate_path.read_text(encoding="utf-8"))
        if args.from_dream:
            if args.assessment:
                raise IngestionError("--from-dream is explicit selection; omit --assessment")
            if args.command == "develop" and args.provider in {"auto", "deterministic"}:
                raise IngestionError("develop requires an explicit model provider; use scaffold")
            dev_res = develop_from_dream(
                cand_data,
                _provider(args) if args.command == "develop" else None,
                max_calls=args.max_calls,
                scaffold=args.command == "scaffold",
            )
        else:
            if not args.assessment:
                raise IngestionError("Candidate ingestion requires --assessment or --from-dream")
            assess_data = json.loads(Path(args.assessment).read_text(encoding="utf-8"))
            if args.command == "scaffold":
                dev_res = scaffold_candidate(cand_data, assess_data)
            else:
                if args.provider in {"auto", "deterministic"}:
                    raise IngestionError(
                        "develop requires an explicit model provider; use scaffold"
                    )
                dev_res = develop_candidate(
                    cand_data, assess_data, _provider(args), max_calls=args.max_calls
                )
    except (IngestionError, OSError, ValueError) as error:
        print(f"Ingestion rejected: {error}", file=sys.stderr)
        return 2

    out_text = json.dumps(dev_res, indent=2)
    if args.output:
        Path(args.output).write_text(out_text, encoding="utf-8")
        print(f"[Saved] Development plan written to: {args.output}")
    else:
        print(out_text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="howlcreate",
        description="Computational creativity and open-ended problem solving layer for the Howl ecosystem.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # explore / run / create
    explore_parser = subparsers.add_parser(
        "explore", aliases=["run", "create"], help="Run full creative exploration pipeline"
    )
    explore_parser.add_argument("--from-dream", type=Path)
    explore_parser.add_argument("problem", nargs="?", type=str, help="Problem statement to explore")
    explore_parser.add_argument("--ecosystem-fit-weight", type=float, default=0.0)
    explore_parser.add_argument(
        "--provider",
        type=str,
        default="auto",
        help="Provider (auto, deterministic, ollama, openai)",
    )
    explore_parser.add_argument("--model", type=str, default=None, help="Model identifier")
    explore_parser.add_argument(
        "--top-n", type=int, default=3, help="Number of diverse finalists to converge to"
    )
    explore_parser.add_argument(
        "--hard-constraint",
        action="append",
        default=[],
        dest="hard_constraints",
        help="Mandatory requirement a candidate must satisfy to become a finalist",
    )
    explore_parser.add_argument("--output", "-o", type=str, help="Save report to file")
    explore_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default=None,
        help="Output format (defaults to json if --output ends with .json, otherwise markdown)",
    )
    explore_parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress progress output"
    )
    explore_parser.set_defaults(func=cmd_explore)

    explore_parser.add_argument("--repair-attempts", type=int, choices=[0, 1], default=1)
    resume_parser = subparsers.add_parser("resume", help="Resume a compatible saved checkpoint")
    resume_parser.add_argument("run_id", help="Run ID or checkpoint file")
    resume_parser.add_argument("--provider", default="auto")
    resume_parser.add_argument("--output", "-o")
    resume_parser.set_defaults(func=cmd_resume)

    # assumptions
    asm_parser = subparsers.add_parser(
        "assumptions", help="Extract and invert implicit assumptions"
    )
    asm_parser.add_argument("problem", type=str, help="Problem statement")
    asm_parser.add_argument("--provider", type=str, default="auto", help="Provider")
    asm_parser.add_argument("--model", type=str, default=None, help="Model identifier")
    asm_parser.set_defaults(func=cmd_assumptions)

    # reframe
    reframe_parser = subparsers.add_parser(
        "reframe", help="Reframe problem from multiple stakeholder lenses"
    )
    reframe_parser.add_argument("problem", type=str, help="Problem statement")
    reframe_parser.add_argument("--provider", type=str, default="auto", help="Provider")
    reframe_parser.add_argument("--model", type=str, default=None, help="Model identifier")
    reframe_parser.set_defaults(func=cmd_reframe)

    # show
    show_parser = subparsers.add_parser("show", help="Show past run report")
    show_parser.add_argument("run_id", type=str, help="Run ID or file path")
    show_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    show_parser.set_defaults(func=cmd_show)

    # graph
    graph_parser = subparsers.add_parser("graph", help="Show concept lineage DAG")
    graph_parser.add_argument("run_id", type=str, help="Run ID or file path")
    graph_parser.add_argument(
        "--mermaid", action="store_true", help="Render as Mermaid diagram code"
    )
    graph_parser.set_defaults(func=cmd_graph)

    # export
    export_parser = subparsers.add_parser(
        "export", help="Export handoff contract for HowlPlane or HowlFrame"
    )
    export_parser.add_argument("run_id", type=str, help="Run ID or file path")
    export_parser.add_argument(
        "--target",
        choices=["plane", "frame", "raw", "dream"],
        default="plane",
        help="Target ecosystem contract",
    )
    export_parser.add_argument("--output", "-o", type=str, help="Output destination file")
    export_parser.add_argument("--candidate-id")
    export_parser.set_defaults(func=cmd_export)

    # list
    list_parser = subparsers.add_parser("list", help="List all stored runs")
    list_parser.set_defaults(func=cmd_list)

    for name in ("develop", "scaffold"):
        sub = subparsers.add_parser(name, help="Candidate-specific advisory " + name)
        sub.add_argument("candidate_file", nargs="?")
        sub.add_argument("--from-dream", type=Path)
        sub.add_argument("--assessment", "-a")
        sub.add_argument("--output", "-o")
        sub.add_argument("--provider", default="auto")
        sub.set_defaults(func=cmd_develop)
    for sub in set(subparsers.choices.values()):
        if any(action.dest == "provider" for action in sub._actions):
            sub.add_argument(
                "--command-config",
                type=Path,
                help="Explicit trusted operator JSON profile (never discovered)",
            )
            sub.add_argument("--allow-local", action="store_true")
            if sub is not resume_parser:
                sub.add_argument("--max-calls", type=int, default=32)
            sub.add_argument("--fallback", nargs="*", default=[])

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if hasattr(args, "func"):
        try:
            return args.func(args)
        except (ValueError, RuntimeError, OSError) as error:
            message = str(error) if isinstance(error, ValueError) else "Provider or input failed"
            print(f"Error: {message}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
