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
4. **Provider-Agnostic Search**: Built-in support for deterministic/mock execution (for offline testing and CI), explicitly opted-in local Ollama, OpenAI-compatible endpoints, and trusted remote CLI commands.

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

## Provider safety and candidate development

Version 0.2.0 defaults to labeled authored fixtures, never automatic Ollama discovery.
`HOWL_FORBID_LOCAL_INFERENCE=1` overrides every local opt-in. Unknown providers fail.
Exploration defaults to 32 attempts and evaluates in batches of eight. Strategic fit
now means the user's objective; ecosystem weighting requires explicit opt-in.

`develop` requires an explicit model provider; use `scaffold` for deterministic plans.
Typed Dream exports preserve source identities and provenance. See
[providers, budgets, interoperability and migration](docs/PROVIDERS_AND_INTEROP.md).

Verification CI sets `HOWL_FORBID_LOCAL_INFERENCE=1`. The shared provider dependency
is pinned to its final reviewed commit, including portable command-provider tests.

## Recovery and bounded repair

```bash
export HOWL_FORBID_LOCAL_INFERENCE=1
howlcreate explore "Design an accessible museum queue" --provider deterministic \
  --repair-attempts 1 --max-calls 32 --format json --output run.json
howlcreate resume run.json --provider deterministic --output resumed.json
```

For a reviewed remote command, replace the provider with `--provider command
--command-config /absolute/path/profile.json`. The same explicit profile must be
supplied on resume; generated artifacts never select executable commands. Use
provider-core's `claude-json`, `openai-json`, `gemini-json`, `generic-json`, or raw
text adapters as appropriate to actual CLI output. Model/usage/cost come from
reported output, never the configured model label.

Structured responses have at most one schema-only repair call (disable with
`--repair-attempts 0`). Original and repaired attempts have separate execution
records and consume the same finite call budget. Failed parsing preserves known
usage/cost and bounded redacted decoded output plus its hash. Repair does not
invite creative regeneration. A repair call can add cost; no savings are assumed.

Atomic private JSON checkpoints persist at operator boundaries and pre-convergence.
They retain run/idea IDs, graph, assumptions, completed phases, mutation seed IDs,
constraints, scores, budget and execution history. Checkpoints use
`howlcreate.checkpoint/v1`; older saved reports cannot resume. Resume retains the
original total call limit and verifies provider identity/profile hash. It skips
completed phases and already-scored concepts, appending new execution records.
There is one writer per run; concurrent resume is unsupported. A crash during an
uncheckpointed in-flight call can leave its usage unknown; it cannot recover a
remote receipt that was never received. Historical failures remain visible and
keep a resumed run PARTIAL even after recovery.

If a later optional phase has malformed output after repair, surviving valid
concepts can converge. Finalists require valid evaluations and hard-constraint
eligibility. Failed evaluation batches retain earlier scores; unevaluated ideas
cannot become finalists. Status stays PARTIAL with completion_detail
PARTIAL_WITH_FINALISTS or PARTIAL_NO_FINALISTS and named phase failures.
Authentication/session/cancellation/budget failures dispatch no recovery calls.
No provider fallback is discovered or authorized automatically.

Executions record sampling requested/supported/applied. Commands and deterministic
fixtures do not claim sampling control; HTTP applied means transmitted in the
request, not independently verified backend behavior. Unknown usage/cost remains
unknown. This is a recovery workflow, not evidence that partial runs equal full runs.
