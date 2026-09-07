"""Human-readable report generation in markdown and formatted terminal text."""

from __future__ import annotations

from typing import List
from howlcreate.models.run import RunRecord


def format_markdown_report(record: RunRecord) -> str:
    """Generate a comprehensive human-readable Markdown report for a creative run."""
    lines: List[str] = []

    lines.append(f"# HowlCreate Exploration Report: {record.problem}\n")
    lines.append(f"**Run ID**: `{record.run_id}` | **Generated**: {record.created_at} | **Total Explored**: {len(record.graph.nodes)} concepts\n")
    lines.append("---\n")

    # 1. Problem & Assumptions
    lines.append("## 1. Problem Formulation & Hidden Assumptions\n")
    lines.append(f"> **Core Problem**: {record.problem}\n")

    if record.assumptions:
        lines.append("### Uncovered Implicit Assumptions & Inversions")
        for a in record.assumptions:
            lines.append(f"- **Assumption**: *\"{a.statement}\"* ({'Implicit' if a.is_implicit else 'Explicit'})")
            if a.vulnerability:
                lines.append(f"  - *Vulnerability*: {a.vulnerability}")
            for inv in a.inversions:
                lines.append(f"  - *Radical Inversion*: **{inv}**")
        lines.append("")

    # 2. Reframings
    if record.reframings:
        lines.append("## 2. Alternative Framings & Stakeholder Lenses\n")
        for r in record.reframings:
            lines.append(f"- **Lens: {r.perspective}**")
            lines.append(f"  - *Reframed Question*: {r.reframed_question}")
            lines.append(f"  - *Focus*: {r.core_focus}")
        lines.append("")

    # 3. Finalists
    finalists = record.get_finalists()
    lines.append(f"## 3. Converged Finalist Concepts ({len(finalists)} Selected)\n")

    for i, idea in enumerate(finalists, 1):
        score = idea.composite_score()
        lines.append(f"### Finalist #{i}: {idea.title} (ID: `{idea.id}`)")
        lines.append(f"**Composite Score**: `{score:.2f}/1.00` | **Status**: `{idea.status.value}` | **Epistemic Class**: `{idea.epistemic_status.value}`\n")
        lines.append(f"**Description**: {idea.description}\n")
        if idea.core_mechanism:
            lines.append(f"**Core Mechanism**: {idea.core_mechanism}\n")
        if idea.origin:
            lines.append(f"**Provenance / Origin**: `{idea.origin}` (Operator: `{idea.operator_used}`)")
        if idea.parent_ids:
            lines.append(f"**Lineage Parents**: {', '.join(f'`{p}`' for p in idea.parent_ids)}")

        # Dimensions
        if idea.evaluations:
            ev = idea.evaluations[-1]
            lines.append("\n**Multi-Dimensional Evaluation**:")
            lines.append("| Dimension | Score | Uncertainty | Rationale |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for dim, detail in ev.scores.items():
                lines.append(f"| **{dim.title()}** | {detail.score:.2f} | ±{detail.uncertainty:.2f} | {detail.rationale} |")

            if ev.strengths:
                lines.append(f"\n- **Key Strengths**: {', '.join(ev.strengths)}")
            if ev.critical_risks:
                lines.append(f"- **Critical Risks & Fragilities**: {', '.join(ev.critical_risks)}")

        # Epistemic Bounds
        if idea.speculations:
            lines.append(f"- **Speculative Claims** (Unverified): {', '.join(idea.speculations)}")
        if idea.evidence_needs:
            lines.append(f"- **Verification / Evidence Needs** (For HowlFrame): {', '.join(idea.evidence_needs)}")

        # Convergence Rationale
        decision = record.decisions.get(idea.id)
        if decision:
            lines.append(f"- **Survival Rationale**: {decision.rationale}")

        lines.append("\n---\n")

    # 4. Set Aside Concepts & Rationale
    non_finalists = [node for node in record.graph.nodes.values() if node.id not in record.finalist_ids]
    if non_finalists:
        lines.append(f"## 4. Concepts Set Aside ({len(non_finalists)} Explored Concepts)\n")
        for nf in non_finalists:
            dec = record.decisions.get(nf.id)
            rat = dec.rationale if dec else "Lower overall multidimensional balance."
            lines.append(f"- **{nf.title}** (`{nf.id}`) [Score: {nf.composite_score():.2f}]: {rat}")
        lines.append("")

    # 5. Suggested Ecosystem Handoff
    lines.append("## 5. Ecosystem Handoff Boundaries\n")
    lines.append("### A. Next Step for HowlFrame (Verification & Evidence Grounding)")
    lines.append("1. Extract explicit evidence needs from selected finalists.")
    lines.append("2. Formulate HFIR verification assertions and test invariants to substantiate speculative claims.\n")
    lines.append("### B. Next Step for HowlPlane (Execution Planning)")
    lines.append("1. Take preferred finalist concept mechanism.")
    lines.append("2. Decompose into dependency execution graphs, agent allocation, and task milestones.\n")

    return "\n".join(lines)
