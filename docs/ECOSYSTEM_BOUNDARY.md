# HowlCreate Ecosystem Boundary

This document defines the strict architectural boundaries between **HowlCreate** and the neighboring systems in the Howl ecosystem.

---

## 1. Boundary Matrix

| Component | Responsibility | Inputs | Outputs | Primary Question |
| :--- | :--- | :--- | :--- | :--- |
| **HowlCreate** | Creative reasoning, open-ended problem exploration, assumption challenging, reframing, concept evolution, multi-criteria evaluation, synthesis. | Problem statement, constraints, strategic hints. | Lineage-tracked concept candidates, assumption registers, evidence needs, risk profiles. | *What could we do?* |
| **HowlFrame** | Verification, proof systems, runtime capability gating, epistemic evidence modeling, certainty boundaries. | Proposed claims, assumptions, executable code, invariants. | Verified proofs, bounds checks, validated assertions. | *What do we know, why do we believe it, and what remains uncertain?* |
| **HowlPlane** | Planning, workflow orchestration, task breakdown, agent routing, dependency graph execution, recovery. | Selected concept candidates, project goals, resource constraints. | Work graphs, task executions, completed system mutations. | *How do we get this done?* |
| **HowlChangeOps** | Authority enforcement, deployment boundaries, human sign-off gates, audit logging, rollback safety. | Proposed changes, execution plans, blast radius assessments. | Approved/rejected action envelopes, release provenance. | *Are we allowed to do this, and can we do it safely?* |
| **HowlWriter** | Source-grounded synthesis, prose drafting, humanization, voice calibration, technical documentation. | Concept drafts, evidence claims, research papers, notes. | Final papers, announcements, manuals, docs. | *How should we communicate this?* |

---

## 2. Invariants & Negative Constraints

### What HowlCreate Must NEVER Do:
1. **Never schedule or orchestrate execution tasks.** Decomposing a concept into Jira-like tasks, DAG scheduling across worker pools, and tracking task completion belongs exclusively to **HowlPlane**.
2. **Never certify factual truth or verification guarantees.** HowlCreate explicitly tags its concepts with epistemic status (`HYPOTHESIS`, `SPECULATION`, `IMAGINED_POSSIBILITY`). Rigorous verification of claims and evidence requirements belongs to **HowlFrame**.
3. **Never execute consequential or side-effecting operations outside its own sandbox.** Modifying production systems, issuing deployment commands, or modifying external resources belongs to **HowlChangeOps**.
4. **Never silently invent facts under the guise of creativity.** Speculation must be isolated in structured fields (`speculations`, `unverified_hypotheses`, `evidence_needs`).

---

## 3. Downstream Handoff Contracts

### A. Handoff to HowlFrame
When HowlCreate produces a finalist concept, it exposes:
- `explicit_assumptions`: What must hold true for this concept to work.
- `unverified_hypotheses`: Claims needing empirical validation.
- `evidence_needs`: Specific experiments or facts required to reduce uncertainty.

### B. Handoff to HowlPlane
When a concept is selected for realization, HowlPlane receives:
- `concept_id`, `title`, `description`
- `core_mechanism`: How the concept operates conceptually.
- `strategic_tradeoffs`: Benefits, costs, and known risks.
- `dependencies` & `constraints`.
HowlPlane then formulates execution graphs, task decomposition, and agent allocation.
