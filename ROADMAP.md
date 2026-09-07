# HowlCreate Roadmap

This roadmap tracks the development milestones and feature trajectories for **HowlCreate**.

---

## Phase 1: Core Engine & Deterministic Foundation (Completed ✅)
- [x] Strict ecosystem boundary definition (`docs/ECOSYSTEM_BOUNDARY.md`).
- [x] Standard data models for `Idea`, `LineageGraph`, `EpistemicStatus`, and `RunRecord`.
- [x] 12 Composable Creative Operators implemented and tested:
  - Assumption Extraction & Inversion
  - Multi-Perspective Reframing
  - Independent Branching
  - Constraint Mutation
  - Analogical Reasoning
  - Forced Combination
  - Adversarial Critique & Hardening
  - Second-Order Exploration
  - Extreme Solutions
  - Simplification / Dissolution
  - Substitution
  - Architectural Synthesis
- [x] Semantic deduplication and near-duplicate clustering (`ConceptDeduplicator`).
- [x] Multi-dimensional evaluation with uncertainty bounds (`ConvergenceEngine`).
- [x] Diversity-preserving convergence with inspectable rationale (`ConvergenceDecision`).
- [x] Deterministic mock provider for hermetic testing and offline CI (`DeterministicProvider`).
- [x] Local model integration via Ollama (`OllamaProvider`).
- [x] OpenAI-compatible endpoint support (`OpenAICompatibleProvider`).
- [x] Persistent JSON run storage (`RunStorage`).
- [x] Full CLI suite (`explore`, `assumptions`, `reframe`, `show`, `graph`, `export`, `list`).
- [x] Downstream handoff contracts for HowlPlane and HowlFrame.
- [x] Creativity benchmark suite (`benchmarks/suite.py`).
- [x] 35 unit and integration tests passing in CI.

---

## Phase 2: Dogfooding & Empirical Refinement (Active 🔄)
- [ ] Dogfood Target 1: Remote-work economic opportunities in the Howl ecosystem.
- [ ] Dogfood Target 2: Self-architectural challenge for HowlCreate.
- [ ] Incorporate dogfood critique into operator prompt engineering and schema robustness.
- [ ] Benchmark signal evaluation across 12 diverse domain problems.

---

## Phase 3: Advanced Cognitive Capabilities (Upcoming 🎯)
- [ ] **Vector & Embedding Similarity**: Optional fast local embeddings for high-dimensional semantic clustering when available.
- [ ] **Interactive Steering & Branch Pruning**: CLI interactive mode allowing human operator to pin or prune branches during the run.
- [ ] **Multi-Model Heterogeneous Swarms**: Simultaneously routing different operators to different models (e.g. Claude for synthesis, Qwen for lateral code analogies, GPT-4o for adversarial critique).
- [ ] **Continuous Search Budget Allocator**: Dynamic budgeting that expands search depth in under-explored conceptual territories.
- [ ] **Direct HowlPlane Task Dispatch**: Stable gRPC or CLI handoff protocol invoking HowlCreate from HowlPlane workflow steps.
- [ ] **HowlFrame Formal Assertion Linker**: Automatic generation of HowlFrame `.howl` verification fixtures directly from concept evidence requirements.
