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


def _print_step(phase: str, payload: dict) -> None:
    if phase == "phase":
        print(f"  [>] {payload.get('name')}...", flush=True)
    elif phase == "start":
        print(f"\n[HowlCreate] Initializing creative run: {payload.get('run_id')}")
        print(f"  Problem: \"{payload.get('problem')}\"\n")
    elif phase == "complete":
        print(f"\n[HowlCreate] Exploration finished: {payload.get('total_concepts_explored')} concepts explored across divergent branches.")
        print(f"  Converged to {payload.get('finalists_selected')} top diverse finalists.\n")


def cmd_explore(args: argparse.Namespace) -> int:
    """Execute the full divergent & convergent creative exploration pipeline."""
    config = PipelineConfig(
        top_n=args.top_n,
        provider_name=args.provider,
        on_step_callback=_print_step if not args.quiet else None,
    )
    pipeline = CreativePipeline(config=config)

    # Optional model override
    provider = registry.get_provider(args.provider)
    if args.model:
        provider.model_name = args.model

    record = pipeline.execute(args.problem, provider=provider)

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

    return 0


def cmd_assumptions(args: argparse.Namespace) -> int:
    """Extract explicit & implicit assumptions and generate inversions."""
    provider = registry.get_provider(args.provider)
    if args.model:
        provider.model_name = args.model

    op = AssumptionOperator()
    res = op.execute(args.problem, provider)

    print(f"\n# Assumptions & Inversions for: \"{args.problem}\"\n")
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
    provider = registry.get_provider(args.provider)
    if args.model:
        provider.model_name = args.model

    op = ReframingOperator()
    res = op.execute(args.problem, provider)

    print(f"\n# Reframing Lenses for: \"{args.problem}\"\n")
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
        print(f"{r['run_id']:<16} {r['created_at'][:19]:<26} {r['finalists_count']:<10} {r['problem'][:35]}...")
    print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="howlcreate",
        description="Computational creativity and open-ended problem solving layer for the Howl ecosystem.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # explore / run / create
    explore_parser = subparsers.add_parser("explore", aliases=["run", "create"], help="Run full creative exploration pipeline")
    explore_parser.add_argument("problem", type=str, help="Problem statement to explore")
    explore_parser.add_argument("--provider", type=str, default="auto", help="Provider (auto, deterministic, ollama, openai)")
    explore_parser.add_argument("--model", type=str, default=None, help="Model identifier")
    explore_parser.add_argument("--top-n", type=int, default=3, help="Number of diverse finalists to converge to")
    explore_parser.add_argument("--output", "-o", type=str, help="Save report to file")
    explore_parser.add_argument("--format", choices=["markdown", "json"], default=None, help="Output format (defaults to json if --output ends with .json, otherwise markdown)")
    explore_parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")
    explore_parser.set_defaults(func=cmd_explore)

    # assumptions
    asm_parser = subparsers.add_parser("assumptions", help="Extract and invert implicit assumptions")
    asm_parser.add_argument("problem", type=str, help="Problem statement")
    asm_parser.add_argument("--provider", type=str, default="auto", help="Provider")
    asm_parser.add_argument("--model", type=str, default=None, help="Model identifier")
    asm_parser.set_defaults(func=cmd_assumptions)

    # reframe
    reframe_parser = subparsers.add_parser("reframe", help="Reframe problem from multiple stakeholder lenses")
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
    graph_parser.add_argument("--mermaid", action="store_true", help="Render as Mermaid diagram code")
    graph_parser.set_defaults(func=cmd_graph)

    # export
    export_parser = subparsers.add_parser("export", help="Export handoff contract for HowlPlane or HowlFrame")
    export_parser.add_argument("run_id", type=str, help="Run ID or file path")
    export_parser.add_argument("--target", choices=["plane", "frame", "raw"], default="plane", help="Target ecosystem contract")
    export_parser.add_argument("--output", "-o", type=str, help="Output destination file")
    export_parser.set_defaults(func=cmd_export)

    # list
    list_parser = subparsers.add_parser("list", help="List all stored runs")
    list_parser.set_defaults(func=cmd_list)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if hasattr(args, "func"):
        return args.func(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
