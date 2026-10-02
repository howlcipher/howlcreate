# Change log

## Unreleased

Native HowlWriter consumption and sandbox materialization (Run 5 CF04, DF-C2, DF-C4, CF02):
`develop`/`scaffold --from-writer` validate `howlwriter.copy_package/v1` into a typed
`writer_copy` slot with Dream/Writer/Create lineage. The new `materialize` command renders a
deterministic static prototype plus `create-artifact-manifest.json` into an explicit,
symlink-safe sandbox that denies live repositories by default. Schema errors now name the
field and size. Added `python -m howlcreate.cli`.

Pinned the final reviewed provider core with portable command tests. CI preserves
`HOWL_FORBID_LOCAL_INFERENCE=1` for all verification commands.

## 0.2.0

Added shared restrictive provider policy, trusted remote command adapters, explicit
fallback accounting, batched evaluation, and a default 32-attempt budget with partial
persistence. Unknown providers fail and auto no longer discovers Ollama. Added typed
Dream exports, strict ingestion, preserved source artifacts, and candidate-specific
provider-backed develop. The former template behavior is now scaffold; the two-argument
Python API is deprecated. Removed fixed domain branches and fixture substring routing;
strategic_fit now scores the user's objective, with optional explicit ecosystem weighting.
Runtime dependencies now include pinned howl-provider-core and jsonschema.

## Resilience hardening (2026-10-02)

- Added one bounded budgeted structured repair, usage preservation and sampling records.
- Added atomic phase checkpoints and compatible same-provider resume with retained IDs/history.
- Optional malformed later phases and partial evaluations may converge valid surviving work.
- Added compact Create constraint metadata to the existing advisory Dream handoff.

- Resume retains prior valid finalists and decisions when recovery stops before new convergence.

- Pin provider-core nested CLI response-shape telemetry fix.

## Discovery integration and budget integrity

- Accept direct typed Dream candidates for advisory selection, preserving source identity,
  claims, constraints, uncertainty and provenance.
- Reserve synthesis and evaluated convergence including bounded repairs; publish reduced
  plans, deferred evaluation IDs and insufficient-budget failures.
- Retain eligible dimension leaders beside balanced finalists and existing hard gates.
