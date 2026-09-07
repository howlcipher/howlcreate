# HowlCreate

**Computational creativity and open-ended problem solving for the Howl ecosystem.**

HowlCreate exists to answer:

> **What could we do?**

It deliberately explores possibilities before another system decides how to execute them.

HowlCreate is a computational creativity engine designed for divergent and convergent creative reasoning. Rather than issuing single-pass LLM brainstorming prompts, HowlCreate executes a disciplined, multi-operator search: extracting hidden assumptions, inverting constraints, analogizing across distant domains, branching independently to avoid premature convergence, challenging proposals through adversarial critique, synthesizing disparate ideas, and converging toward a defensible, lineage-tracked set of finalists.

---

## Ecosystem Boundary

A strict architectural boundary separates HowlCreate from the rest of the Howl ecosystem:

| System | Role | Core Question |
| :--- | :--- | :--- |
| **HowlCreate** | Imagination, reframing, lateral exploration, synthesis, concept evolution | *What could we do?* |
| **HowlFrame** | Structured reasoning, evidence verification, claims, uncertainty | *What do we know, why do we believe it, and what remains uncertain?* |
| **HowlPlane** | Planning, orchestration, task decomposition, agent routing, execution graphs | *How do we get this done?* |
| **HowlChangeOps** | Authority boundary, release gating, safety approvals, rollback | *Are we allowed to do this, and can we do it safely?* |
| **HowlWriter** | Source-grounded writing, humanization, voice adaptation, communication | *How should we communicate this?* |

> **Architectural Guardrail**: HowlCreate does not plan execution or orchestrate agent tasks. It generates and evaluates creative possibilities. Once a concept is selected, it can be handed off to HowlFrame (for verification of claims and evidence needs) and HowlPlane (for execution planning).

---

## Core Pipeline

Creative reasoning follows a disciplined divergent-then-convergent pipeline:

```
PROBLEM
   │
   ▼
UNDERSTAND & EXTRACT ASSUMPTIONS
   │
   ▼
REFRAME (Multiple Lenses & Perspectives)
   │
   ▼
DIVERGE (Independent Branching)
   │
   ▼
MUTATE (Constraints, Analogies, Extremes, Substitutions)
   │
   ▼
CROSS-POLLINATE & SYNTHESIZE (Forced Combinations)
   │
   ▼
CHALLENGE (Adversarial Critique & Brittleness Analysis)
   │
   ▼
EVALUATE (Multi-Dimensional Scoring & Uncertainty Tracking)
   │
   ▼
CONVERGE (Preserving Distinct Strategies & Wildcards)
   │
   ▼
OUTPUT CONCEPTS (Lineage-Tracked Finalists)
```

---

## Key Principles

1. **Divergence Before Convergence**: Never rank ideas immediately after generation. Premature evaluation suffocates exploration. The search budget is first spent discovering distant branches.
2. **Epistemic Truthfulness**: Facts, assumptions, speculation, hypotheses, analogies, and predictions are explicitly labeled. Speculation is never masqueraded as factual evidence.
3. **Lineage Preservation**: Every concept is a node in a directed acyclic graph (DAG) recording its origin, parent ideas, creative operator, mutated assumptions, and survival rationale.
4. **Provider-Agnostic Search**: Built-in support for deterministic/mock execution (for offline testing and CI), local Ollama models, and OpenAI-compatible endpoints.

---

## Installation & Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/howlcipher/howlcreate.git
cd howlcreate

# Install in development mode
pip install -e ".[dev]"
```

### Basic CLI Usage

```bash
# Run a full creative exploration pipeline
howlcreate explore "How could the Howl ecosystem create meaningful remote-work opportunities?"

# Extract and invert hidden assumptions
howlcreate assumptions "How to build an offline-first distributed database"

# Generate multi-perspective reframings
howlcreate reframe "Developer onboarding takes three weeks"

# Inspect a past run and lineage graph
howlcreate show <run-id>
howlcreate graph <run-id>

# Export structured JSON for downstream systems (HowlPlane / HowlFrame)
howlcreate export <run-id> --output concept.json
```

---

## Testing & Quality

```bash
# Run test suite
pytest -v

# Static checks
flake8 src/ tests/ --select=F821,F401,E9

# Verification build
python -m compileall src/ tests/
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
