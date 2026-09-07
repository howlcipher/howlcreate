# Engineering Journal: Session 01 — Project Initialization, Architecture, and Initial Dogfooding

- **Date**: 2026-09-06
- **Branch**: `main`
- **Objective**: Establish `howlcipher/howlcreate`, define hard ecosystem boundaries, implement the complete divergent-then-convergent computational creativity engine with 12 composable operators, multi-dimensional evaluation, lineage graph, benchmark suite, and execute real dogfood runs.

---

## 1. Context & Mission Alignment

HowlCreate was commissioned as the creative reasoning and open-ended problem-solving layer of the Howl ecosystem, answering:
> *"What could we do?"*

A strict architectural boundary was established:
- **HowlCreate**: Imagination, reframing, lateral exploration, cross-domain analogies, concept mutation, synthesis, multi-criteria evaluation. Proposes possibilities and preserves concept lineage.
- **HowlFrame**: Reasoning grounding, evidence verification, assertions, and uncertainty bounds.
- **HowlPlane**: Planning, task decomposition, agent selection, model/tool routing, and execution graphs.
- **HowlChangeOps**: Authorization, execution gates, and safety verification.
- **HowlWriter**: Grounded drafting, humanization, voice calibration, and communication.

---

## 2. Work Completed

### Repository & Infrastructure
- Created GitHub repository `howlcipher/howlcreate` via GitHub CLI.
- Configured local directory at `/var/home/howlcipher/howlcreate` and linked to `/run/media/system/tallgeese/dev/howlcreate`.
- Initialized clean Python 3.14 project with standard packaging (`pyproject.toml`), zero required runtime external dependencies, and optional dev extras (`pytest`, `flake8`, `ruff`).
- Configured GitHub Actions CI (`.github/workflows/ci.yml`) testing on Python 3.11, 3.12, 3.13 with compileall, flake8, and pytest.
- Exposed CLI entrypoint `howlcreate` linked into `~/.local/bin/howlcreate`.

### Core Data Models (`src/howlcreate/models/`)
- `EpistemicStatus`: Formal categorical boundary distinguishing `FACT`, `ASSUMPTION`, `SPECULATION`, `HYPOTHESIS`, `IMAGINED_POSSIBILITY`, `ANALOGY`, and `PREDICTION`.
- `ConceptStatus`: Lifecycle state (`CANDIDATE`, `MUTATED`, `COMBINED`, `CHALLENGED`, `FINALIST`, `SET_ASIDE`, `MERGED`).
- `Idea`: Full concept entity capturing titles, core mechanisms, assumptions, changed assumptions, constraints, analogies, speculations, evidence needs, criticisms, and evaluations.
- `LineageGraph`: Directed Acyclic Graph (DAG) with edge tracking (`parent_id`, `child_id`, `operator`, `rationale`), cycle detection (`validate_dag()`), and bi-directional ancestor/descendant traversal.
- `RunRecord`: Durable JSON-serializable execution artifact capturing full run history, assumptions, reframings, DAG, finalists, and convergence rationale.

### 12 Composable Creative Operators (`src/howlcreate/operators/`)
1. `AssumptionOperator`: Extracts explicit and implicit premises and formulates radical inversions.
2. `ReframingOperator`: Reframes problems through contrasting stakeholder lenses (adversary, resource-constrained, future self, outsider).
3. `IndependentBranchingOperator`: Generates isolated branches under distinct explorer archetypes.
4. `ConstraintMutationOperator`: Mutates operational constraints (zero budget, offline-first, extreme asynchrony).
5. `AnalogicalReasoningOperator`: Structural isomorphisms from biology/mycology, supply chain, game theory, ecology, and civil engineering.
6. `ForcedCombinationOperator`: Collides orthogonal ideas into emergent hybrid concepts.
7. `AdversarialCritiqueOperator`: Red-teams concepts for brittleness and single points of failure; generates hardened mutations.
8. `SecondOrderOperator`: Extrapolates feedback loops and macro equilibria when solutions scale.
9. `ExtremeSolutionsOperator`: Pushes variables to radical caricatures to extract governing engineering principles.
10. `SimplificationOperator`: Explores how the problem space itself can dissolve rather than require solving.
11. `SubstitutionOperator`: Swaps conventional components for alternative media.
12. `SynthesisOperator`: Synthesizes complementary strengths across branches into unified architectures.

### Engine & Pipeline (`src/howlcreate/engine/`)
- `ConceptDeduplicator`: Token Jaccard + Cosine similarity clustering with outlier detection.
- `ConvergenceEngine`: Multi-dimensional evaluation across 5 criteria (`novelty`, `feasibility`, `usefulness`, `simplicity`, `strategic_fit`) with explicit uncertainty intervals. Implements diversity-preserving finalist selection across distinct clusters.
- `RunStorage`: Atomic JSON persistence to `~/.local/share/howlcreate/runs/` with search and retrieval.
- `CreativePipeline`: Full 10-phase pipeline orchestrator executing divergence before convergence.

### Provider Architecture (`src/howlcreate/providers/`)
- `DeterministicProvider`: Algorithmic mock provider for 100% offline, reproducible CI and unit testing.
- `OllamaProvider`: Native local HTTP provider for Ollama (`qwen2.5-coder:7b-instruct` or any local model) using standard library HTTP.
- `OpenAICompatibleProvider`: Standard library HTTP client for OpenAI, DeepSeek, vLLM, or LiteLLM endpoints.
- `ProviderRegistry`: Dynamic provider resolution and multi-role routing.

### CLI & Ecosystem Handoff (`src/howlcreate/cli/`, `src/howlcreate/formatting/`)
- Commands: `explore`, `assumptions`, `reframe`, `show`, `graph`, `export`, `list`.
- Mermaid diagram and ASCII tree lineage visualizers.
- Formal handoff contracts for HowlPlane (`export_howlplane_contract`) and HowlFrame (`export_howlframe_contract`).

### Verification & Benchmarking
- 35 unit and integration tests passing in 0.32s (`pytest`).
- Zero flake8 lint errors (`--select=F821,F401,E9`).
- Clean bytecode compilation (`python -m compileall`).
- Benchmark catalog with 12 domain problems and quantitative signal extractors (`benchmarks/suite.py`).

---

## 3. Real Failures & Discoveries During Build
1. **Global Plugin Pollution**: A global `langsmith` pytest plugin in `~/.local/lib/python3.14/site-packages` was missing its `httpx` dependency, crashing generic `pytest` invocations. Solved cleanly by establishing an isolated virtualenv under `.venv/` and configuring `pyproject.toml`.
2. **Heuristic Keyword Collisions in Deterministic Mock**: The deterministic provider's keyword matching collided when `adversarial.py` contained the word `"assumption"` in its prompt instructions, causing the assumption response to be returned instead of critique. Solved by refining dispatch rules to prioritize exact operator signatures and placing specific checks before generic substrings.
3. **Similarity Shingle Sparsity**: 2-shingle Jaccard on short titles produced false negatives (missing obvious duplicates). Added unigram Jaccard + token cosine blending, achieving reliable cluster assignment for paraphrased concepts.

---

## 4. Next Highest-Value Work
- Complete Dogfood Target 1 execution and preserve analysis artifacts in `dogfood/`.
- Execute Dogfood Target 2 (Self-Architecture exploration).
- Commit and push to `origin main`.
- Update `HANDOFF.md`.

---

## 5. Dogfood Target 1 Analysis (Remote-Work Problem)

- **Input Question**: *"How could the Howl ecosystem create meaningful remote-work opportunities rather than merely being software about remote work?"*
- **Execution Run ID**: `run-64f4d1d9` (Ollama provider with `qwen2.5-coder:7b-instruct`)
- **Total Concepts Explored**: 29 across 10 divergent phases
- **Selected Finalists**:
  1. `idea-1a9c95`: **Flexible Work Arrangements** (Spectrum model combining remote and on-site with self-set boundaries; composite score 0.80)
  2. `idea-fb064e`: **Cultural Integration for Remote Work** (Prioritizing organizational trust, mentorship, and interpersonal cohesion over pure tooling; composite score 0.80)
  3. `idea-2a22ff`: **Shadow Market Analysis** (Adversarial reframing targeting exploitable vulnerabilities and market inefficiencies; composite score 0.80)

### Key Observations & Critique:
- **Divergence**: The pipeline created diverse branches including mycelia-inspired nutrient gradient task routing, decentralized Kanban boards, and stigmergic collaboration media.
- **Lineage Integrity**: The lineage tree clearly reveals derivation paths (e.g. `Cultural Integration` -> `Culturally Informed Flexible Work Arrangements` via forced combination).
- **Adversarial Critique & Hardening**: Hardened mutations were generated addressing miscommunication risks in hybrid workflows.
- **Improvement Target**: The local 7B model scored dimensions with uniform granularity (0.80 / 0.70 / 0.90). Future iterations will refine the scoring prompt to require sharper relative contrast between competing concepts.

---

## 6. Dogfood Target 3 Analysis (HowlCreate & HowlRelay Cross-Repo Dogfood)

- **Input Question**: *"How can HowlCreate and HowlRelay dogfood each other so that creative problem solving becomes more useful while engineering continuity becomes more reliable, without creating tight coupling or duplicating HowlPlane?"*
- **Execution Run ID**: `run-3c13e4f4` (Ollama provider with `qwen2.5-coder:7b-instruct`)
- **Total Concepts Explored**: 26 across 10 divergent phases
- **Selected Finalists**:
  1. `idea-a64952`: **Decentralized Data Management** (Replacing HowlPlane with distributed file storage to eliminate single points of failure; composite score 0.795)
  2. `idea-b00b2d`: **Security Audit and Vulnerability Exploitation** (Conducting continuous adversarial fuzzing and bug bounty audits; composite score 0.795)
  3. `idea-78b3e7`: **Resource-Optimized Design** (Operating with minimal overhead, efficient data structures, and local-first execution; composite score 0.795)

### Key Observations & Coordination Defect in HowlRelay:
1. **Convergence Metric Granularity**: All 26 generated concepts collapsed to virtually identical scores (~0.80), leading to flat candidate selection.
2. **Ecosystem Boundary Confusion**: Finalist 1 suggested replacing HowlPlane with HDFS/GlusterFS, violating the ecosystem boundary constraint specified in the prompt.
3. **HowlRelay Continuity Parsing Failure**: Running `howlrelay handoff --repo ../howlcreate` completely failed to extract objectives, completed work, active work, and starting commands from `HANDOFF.md` because `ContinuityCollector` in HowlRelay strictly expected unnumbered exact markdown headers (`#+ Objective`) and hardcoded exact names, failing on numbered sections (`## 1. System Summary`, `## 2. What Works Right Now`, `## 5. Commands to Resume Work`).
4. **Preserved Artifacts**: Saved full run in `dogfood/03_cross_repo_dogfood.json` and report in `dogfood/03_cross_repo_dogfood.md`.

---

## 7. Diversity-Preserving Convergence & Calibration Fix

- **Defect Discovered During Dogfooding**:
  1. `ConvergenceEngine` allowed the novelty wildcard selection to pick ideas from clusters that were already represented in the finalists list, defeating the purpose of cluster-based diversity.
  2. Scoring prompts anchored models to uniform placeholder numbers (`0.7`, `0.8`), flattening evaluation contrast.
- **Remediation**:
  1. Updated `ConvergenceEngine.select_finalists` to strictly enforce distinct cluster representation when selecting both cluster champions and novelty wildcards.
  2. Enforced calibration instructions in scoring prompts to discourage uniform ratings and require differentiation across the 0.0 - 1.0 range.
  3. Added deterministic title-seeded hash scoring in `DeterministicProvider` to provide reproducible, distinct multi-dimensional scores across concepts.
  4. Added test coverage in `tests/test_convergence.py`.

