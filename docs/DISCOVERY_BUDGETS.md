# Dream selection and budget-aware development

```bash
export HOWL_FORBID_LOCAL_INFERENCE=1
howlcreate scaffold --from-dream candidate.json --output scaffold.json
howlcreate develop --from-dream candidate.json --provider command --command-config PROFILE.json
howlcreate explore --from-dream candidate.json --provider deterministic --max-calls 8
```

`--from-dream` validates the typed advisory Dream candidate and rejects contradictions,
REJECTED status and authority escalation. It records explicit operator selection for
advisory development only. Ordinary candidate/assessment ingestion is still available.
`develop` still requires an explicit model provider; fixture plans use `scaffold`.
Exploration preserves the complete source once in `metadata.source_dream_candidate`,
with compact references on generated concepts. Prompts receive the selected opportunity,
claims, assumptions, uncertainty and evidence needs as unverified source data. Declared
Dream hard constraints are added to Create's existing hard-constraint gate.

Finite pipelines publish `metadata.budget_plan`: mandatory assumptions, one independent
branch, synthesis and evaluation; skipped optional phases; deferred evaluation IDs;
minimum and actual total calls. Reservations include one configured repair per required
stage and evaluation batch. Default repair-enabled minimum is eight calls (four without
repair). Smaller budgets stop before inference with
`INSUFFICIENT_BUDGET_FOR_REQUESTED_PIPELINE`. Reduced successful runs report
`COMPLETE_REDUCED_PIPELINE`; completed phase ordering includes named skipped phases for
checkpoint compatibility, and `skipped_phases` distinguishes these from executed stages.

Optional exploration cannot spend reserved downstream capacity. If provider output
exceeds evaluation capacity, a diverse cluster-round-robin subset is evaluated, preferring
new synthesis representatives. Deferred nodes stay in the graph without invented scores;
only evaluated eligible nodes can become finalists. This is explicitly reduced coverage,
not an evaluation of every concept. Arbitrary transport/fallback failures can still yield
PARTIAL. Resume preserves plans, source identity, budgets and historical failures.
Candidate development is a separate one-call design stage, not silently included in the
exploration pipeline or its budget. Invoke it with a separately declared budget.

Convergence retains existing weights, diverse balanced finalists and novelty wildcard.
It additionally reports eligible-only `advisory_dimension_leaders`: highest novelty,
feasibility, objective fit, usefulness and weighted balance. This preserves a valuable
creative contribution even when conventional feasibility wins the balanced ranking.
Scores remain evaluator judgments with uncertainty, not empirical validation or authority.
Evidence compatibility and implementation value require explicit external evaluation;
they are not inferred from feasibility. Use Dream's `audit-report` on a product report
with declared validation provenance and exact claim bindings.
