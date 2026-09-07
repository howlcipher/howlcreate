# HowlCreate Creative Operators

HowlCreate replaces monolithic single-pass prompt generation with composable, structured **Creative Operators**. Each operator embodies a specific cognitive technique for divergent search, reframing, critique, or synthesis.

---

## 1. Divergent & Lateral Operators

### `assumption_extraction`
- **Goal**: Unpack implicit and explicit premises taken for granted in the problem framing.
- **Example**: Problem: "How to speed up database query latency?" -> Assumptions: "Queries must be answered synchronously; storage is on disk; clients request data individually."

### `assumption_inversion`
- **Goal**: Deliberately negate, reverse, remove, or exaggerate identified assumptions.
- **Example**: "What if clients never query the database directly, but data pushes continuously to edge memory?"

### `reframing`
- **Goal**: View the problem through radically different stakeholder and observer lenses.
- **Lenses**:
  - `user`: What is the human actually trying to achieve?
  - `adversary`: How would someone weaponize or subvert this?
  - `outsider`: How would a non-technical novice explain this?
  - `future_self`: Looking back 10 years from now, what was trivial?
  - `resource_constrained`: What if we had 1% of the budget?
  - `unlimited_resources`: What if computing power and budget were virtually infinite?

### `constraint_mutation`
- **Goal**: Shift operational boundaries to reveal hidden trade-offs.
- **Mutations**:
  - Zero budget / Unlimited budget
  - Offline-only / Local-only / No internet
  - Single-person / Mass collective
  - Real-time / Asynchronous (one-year horizon)
  - Failure-tolerant / Zero-tolerance

### `analogical_reasoning`
- **Goal**: Map the structure of the problem onto non-computing domains.
- **Source Domains**:
  - *Biology & Ecology*: Mycelial networks, symbiotic mutualism, homeostasis.
  - *Manufacturing & Logistics*: Kanban, just-in-time, buffer decoupling.
  - *Game Design*: Incentive loops, fog of war, asymmetry.
  - *Economics*: Mechanism design, auction theory, tragedy of the commons.

### `independent_branching`
- **Goal**: Explore distinct branches without cross-contamination. Prevents early anchor bias.

### `extreme_solutions`
- **Goal**: Formulate absurd or radical caricatures of solutions to expose deep underlying principles.

### `simplification`
- **Goal**: Ask how the problem can dissolve or disappear entirely rather than requiring a solution.

### `substitution`
- **Goal**: Substitute the core agent, layer, protocol, or medium with an unexpected alternative.

---

## 2. Combinatorial & Convergent Operators

### `forced_combination`
- **Goal**: Merge two or more seemingly orthogonal ideas into a novel hybrid concept.

### `adversarial_critique`
- **Goal**: Attack an idea systematically:
  - What is the single point of catastrophic failure?
  - What hidden cost will make this unviable?
  - What would an attacker exploit?
- **Actionable Output**: Transform criticism into defensive mutations rather than mere rejection.

### `second_order_exploration`
- **Goal**: Project secondary and tertiary ripple effects. What happens when the primary solution succeeds at scale?

### `synthesis`
- **Goal**: Distill the strongest attributes from multiple candidate concepts into an integrated architecture.
