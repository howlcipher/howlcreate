# HowlCreate Engineering Handoff

**Current Status**: Milestone 1 Complete / Actively Dogfooding
**Repository**: `howlcipher/howlcreate`
**Branch**: `main`
**Last Updated**: 2026-09-06

---

## 1. System Summary

HowlCreate is the computational creativity and open-ended problem-solving layer of the Howl ecosystem (*"What could we do?"*). It systematically explores possibilities through a divergent-then-convergent operator search, tracks the full concept lineage DAG, evaluates ideas across independent dimensions with uncertainty bounds, and produces structured handoff contracts for HowlFrame and HowlPlane.

---

## 2. What Works Right Now

1. **CLI Commands**:
   - `howlcreate explore "<problem>" [--provider auto|ollama|deterministic|openai] [--top-n 3] [--output path]`: Full 10-phase exploration run.
   - `howlcreate assumptions "<problem>"`: Extracts explicit and implicit premises with radical inversions.
   - `howlcreate reframe "<problem>"`: Formulates problem from 5 stakeholder lenses.
   - `howlcreate show <run_id>`: Displays full markdown or JSON report of past runs.
   - `howlcreate graph <run_id> [--mermaid]`: Prints ASCII lineage tree or Mermaid diagram.
   - `howlcreate export <run_id> [--target plane|frame|raw]`: Produces JSON contracts.
   - `howlcreate list`: Lists all stored runs in `~/.local/share/howlcreate/runs/`.
2. **12 Composable Operators**:
   - All 12 operators (`AssumptionOperator`, `ReframingOperator`, `IndependentBranchingOperator`, `ConstraintMutationOperator`, `AnalogicalReasoningOperator`, `ForcedCombinationOperator`, `AdversarialCritiqueOperator`, `SecondOrderOperator`, `ExtremeSolutionsOperator`, `SimplificationOperator`, `SubstitutionOperator`, `SynthesisOperator`) are fully implemented and unit-tested.
3. **Lineage DAG**:
   - Every idea tracks parent IDs, operator used, mutations, and epistemic category. Cycle detection and topological ancestry traversal are verified.
4. **Provider Backends**:
   - `DeterministicProvider`: 100% offline, reproducible for CI and unit tests.
   - `OllamaProvider`: Native local HTTP inference (`qwen2.5-coder:7b-instruct` verified on localhost:11434).
   - `OpenAICompatibleProvider`: Standard HTTP client for any `/v1/chat/completions` endpoint.
5. **Testing & Quality**:
   - 35 unit/integration tests passing (`.venv/bin/pytest -v`).
   - Zero flake8 errors.
   - GitHub Actions CI configured for Python 3.11, 3.12, 3.13.

---

## 3. What Is in Progress / Known Limitations

- **Dogfood Runs**: Dogfood Target 1 (remote work) is running/being analyzed. Dogfood Target 2 (self-architecture challenge) is next.
- **Model Latency**: Local 7B model generation across 10 distinct phases takes ~3-4 minutes on Ollama. For quick checks, use `--provider deterministic`.
- **Vector Embeddings**: Near-duplicate clustering currently uses fast unigram Jaccard + Cosine token matching. A future milestone will add optional local embedding support.

---

## 4. Key Files & Architecture

- `src/howlcreate/models/idea.py`: `Idea`, `LineageGraph`, `EpistemicStatus`, `ConceptEvaluation`.
- `src/howlcreate/models/run.py`: `RunRecord`, `ConvergenceDecision`.
- `src/howlcreate/operators/`: Composable operator implementations.
- `src/howlcreate/engine/pipeline.py`: 10-phase divergent & convergent orchestrator.
- `src/howlcreate/engine/dedup.py`: Semantic deduplication and clustering.
- `src/howlcreate/engine/convergence.py`: Multi-dimensional evaluation and diversity-preserving convergence.
- `src/howlcreate/providers/`: Deterministic, Ollama, and OpenAI-compatible backends.
- `src/howlcreate/formatting/`: Markdown reports, Mermaid DAGs, and HowlPlane/HowlFrame exports.
- `benchmarks/suite.py`: 12-problem creativity benchmark catalog and signal extractors.

---

## 5. Commands to Resume Work

```bash
cd /var/home/howlcipher/howlcreate

# Run all tests
.venv/bin/pytest -v

# Run linting and compilation checks
flake8 src/ tests/ benchmarks/ --select=F821,F401,E9
python -m compileall src/ tests/ benchmarks/

# Test CLI
howlcreate --version
howlcreate explore "Test problem" --provider deterministic --quiet
```
