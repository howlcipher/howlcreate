# HowlCreate Architecture

**HowlCreate** is the creative reasoning and open-ended problem-solving layer of the Howl ecosystem. It exists to answer the question:

> **What could we do?**

This document provides a comprehensive architectural specification of HowlCreate's data structures, operator pipeline, divergence-convergence dynamics, and epistemic boundaries.

---

## 1. Architectural Philosophy: Divergence Before Convergence

Conventional AI brainstorming tools collapse exploration by asking a large language model to immediately brainstorm and prioritize "top ideas" in a single prompt. This incurs severe cognitive failure modes:
1. **Premature Convergence**: Models anchor to the most statistically probable industry cliches and rank them before evaluating alternative paradigms.
2. **Cosmetic Diversity**: Generated options are often trivial phrasing variations of the same underlying architecture.
3. **Loss of Provenance**: Ideas appear ex nihilo with no record of which assumptions were changed or how concepts mutated.
4. **Epistemic Conflation**: Speculative leaps and ungrounded conjectures are presented with the same asserted certainty as empirical facts.

HowlCreate solves this by structuring creative reasoning into a **directed acyclic concept graph (DAG)** subjected to a pipeline of independent operators.

```
                                [ Problem Statement ]
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         [ Assumption Extraction ]                       [ Reframing Lenses ]
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          ▼
                             [ Independent Branching ]
                           (Multi-Archetype Explorers)
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
        [ Constraint Mutation ]  [ Analogical Reasoning ]  [ Extremes & Substitutions ]
                  │                       │                       │
                  └───────────────────────┼───────────────────────┘
                                          ▼
                            [ Near-Duplicate Clustering ]
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
       [ Forced Combination ]                         [ Adversarial Critique ]
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          ▼
                            [ Architectural Synthesis ]
                                          │
                                          ▼
                        [ Multi-Dimensional Evaluation ]
                                          │
                                          ▼
                        [ Diversity-Preserving Convergence ]
                                          │
                                          ▼
                            [ Lineage-Tracked Finalists ]
```

---

## 2. Core Data Models

### Epistemic Status Boundary
To prevent hallucinations and ungrounded claims from polluting downstream planning, every idea and assertion carries an explicit `EpistemicStatus`:
- `FACT`: Grounded empirical truth or verified constraint.
- `ASSUMPTION`: Unverified premise taken for granted in the problem formulation.
- `SPECULATION`: Explicitly acknowledged creative leap or unverified extrapolation.
- `HYPOTHESIS`: Testable proposed mechanism subject to verification.
- `IMAGINED_POSSIBILITY`: Radical hypothetical construct explored for insight.
- `ANALOGY`: Structural isomorphism imported from an external domain.
- `PREDICTION`: Projected second-order consequence.

### The Concept DAG (`LineageGraph`)
Concepts are not stored in a flat list. Every `Idea` record contains:
- `id`: Unique identifier (e.g. `idea-a8f3b2`).
- `parent_ids`: References to the antecedent idea(s) from which it was derived.
- `operator_used`: The specific cognitive operator that generated the idea.
- `origin`: Semantic tag indicating the lineage stream.
- `mutations`: Explicit list of what changed between parents and this concept.
- `evaluations`: Multi-dimensional scores with explicit uncertainty intervals.

The `LineageGraph` enforces acyclicity (`validate_dag()`) and supports bi-directional ancestor/descendant traversal.

---

## 3. Composable Creative Operators

Rather than relying on one mega-prompt, HowlCreate partitions creativity into discrete, testable cognitive operators:

| Operator | Class | Mechanism |
| :--- | :--- | :--- |
| **Assumption Extraction & Inversion** | `AssumptionOperator` | Identifies implicit dogmas and inverts them (false, reversed, removed, exaggerated). |
| **Reframing** | `ReframingOperator` | Re-articulates the core problem through contrasting stakeholder lenses (adversary, resource-constrained, future self). |
| **Independent Branching** | `IndependentBranchingOperator` | Dispatches independent explorers with isolated contexts to prevent anchor bias. |
| **Constraint Mutation** | `ConstraintMutationOperator` | Destroys standard parameters (e.g. zero bandwidth, zero budget, extreme asynchrony). |
| **Analogical Reasoning** | `AnalogicalReasoningOperator` | Maps structural isomorphisms from biology, supply chain, game theory, and ecology. |
| **Forced Combination** | `ForcedCombinationOperator` | Collides orthogonal ideas to produce emergent hybrid capabilities. |
| **Adversarial Critique** | `AdversarialCritiqueOperator` | Red-teams concepts for single points of failure, generating hardened mutations. |
| **Second-Order Exploration** | `SecondOrderOperator` | Extrapolates feedback loops and macro equilibria when solutions scale. |
| **Extreme Solutions** | `ExtremeSolutionsOperator` | Pushes variables to 10,000% to expose the underlying engineering principle. |
| **Simplification** | `SimplificationOperator` | Explores how the problem space itself can dissolve rather than require solving. |
| **Substitution** | `SubstitutionOperator` | Swaps out traditional actors (e.g. human managers) for alternative media (e.g. cryptographic escrow). |
| **Synthesis** | `SynthesisOperator` | Integrates complementary attributes from distinct branches into a unified architecture. |

---

## 4. Evaluation and Convergence

### Multi-Dimensional Evaluation
Ideas are never evaluated by a single flattened score. HowlCreate evaluates across independent dimensions:
1. `novelty`: Distance from conventional market solutions.
2. `feasibility`: Implementation viability with existing tools.
3. `usefulness`: Direct tangible impact on the core problem.
4. `simplicity`: Elegance and minimization of moving parts.
5. `strategic_fit`: Alignment with the sovereign, verifiable principles of the Howl ecosystem.

Crucially, every score records an **uncertainty bound** (e.g., `score: 0.85, uncertainty: 0.20`), preventing premature false precision.

### Diversity-Preserving Convergence
To prevent all finalists from being slight variations of the same high-scoring idea:
1. Ideas are clustered via `ConceptDeduplicator` (Jaccard + Cosine similarity threshold).
2. The highest-scoring candidate from **each distinct cluster** is promoted as a cluster champion.
3. Outliers with exceptionally high novelty are preserved as wildcards.
4. Every convergence decision records explicit, inspectable rationale (`ConvergenceDecision`), explaining why finalists survived and why others were set aside or merged.

---

## 5. Downstream Ecosystem Bridges

HowlCreate maintains strict separation from execution and communication:
- **Handoff to HowlFrame**: Concept hypotheses, explicit assumptions, and required evidence are exported via `export_howlframe_contract()` for formal verification and proof bounding.
- **Handoff to HowlPlane**: Selected finalists with core mechanisms, constraints, and dependencies are exported via `export_howlplane_contract()` for task decomposition, execution graphs, and agent routing.
