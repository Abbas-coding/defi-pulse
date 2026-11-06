# Implementation Work Packages

## Current State

Documentation only. The following paths, commands, and tests are planned and do not yet exist. Build incrementally in the order below; do not generate placeholder implementations or simulated research results.

## 1. Preparation and Source Probe

- Establish instructor approval status and obtain the actual rubric/proposal when available.
- Select a compatible Python environment and dependency lock strategy; add package configuration, pytest, Ruff, and ignore rules.
- Add `.env.example` with placeholders; read credentials locally without displaying them.
- Verify the live source and schema through official evidence and a minimal query.
- Document exact available fields, filter types, pagination, hourly semantics, historical support, deployment identity, and retrieval date in `docs/source_schema.md`.

Acceptance: a real bounded query succeeds, errors are visible, and no paid requirement is enabled.

## 2. Bounded Collector and Pilot

- Implement an HTTP client with timeouts, bounded retry/backoff, GraphQL error checks, request counters, and redacted diagnostics.
- Implement cache fingerprints, deterministic discovery/pagination, and canonical selection.
- Retrieve a fixed 20–30-pool cohort, early histories, and outcome evidence.
- Normalize to Parquet and write a manifest and rejection report.
- Complete the [feasibility checklist](feasibility.md); stop for milestone review before expansion.

Acceptance: rerunning cached work avoids unnecessary queries; requests stay capped; timing and quality policies are evidenced.

## 3. Data and DS

- Resolve label ambiguity and finalize timing/eligibility policies before constructing production labels.
- Implement pure feature and label builders with explicit contracts.
- Validate a 100-pool checkpoint before conditional scale-up.
- Build source/pilot, cleaning, EDA, and statistical-findings notebooks.
- Add a dataset card covering provenance, units, missingness, selection bias, and reproducibility.

Acceptance: cached inputs reproduce tables and findings; each output can be traced to source records and settings.

## 4. Models and Evaluation

- Save chronological split assignments and the frozen experiment configuration.
- Implement training-only preprocessing, baselines, model comparisons, and budgeted tuning.
- Save reproducible metrics with class counts and uncertainty limitations.
- Assess calibration; implement supported bands and explanations with a versioned scoring bundle.

Acceptance: scoring enforces feature order/window compatibility; no test feedback influences selection; all reported claims match artifacts.

## 5. Demo and Academic Handoff

- Implement the [historical interface](design.md) using cached data and saved bundles.
- Complete ML notebooks, DS/ML reports, dataset card, and actual team contribution record.
- Document executable setup/replay commands in the root README once implemented.
- Reproduce the workflow from a fresh environment and rehearse the instructor-required notebook submission.

## Proposed CLI

```text
python -m defi_pulse.cli source-check --dry-run
python -m defi_pulse.cli pilot --config configs/pilot.yaml --max-pools 20 --max-requests 500
python -m defi_pulse.cli normalize
python -m defi_pulse.cli build-labels
python -m defi_pulse.cli build-features --window 24
python -m defi_pulse.cli train --window 24
python -m defi_pulse.cli evaluate --window 24
```

Dry-run validates configuration and previews work without sending requests; a real source check is a separate explicit invocation. The request cap above is an example, subject to verified account limits.

## Required Semantic Tests

| Area | Invariant |
|---|---|
| Requests | Partial GraphQL errors fail visibly; retries count toward budget |
| Pagination/cache | No duplicated pools; identical cached requests do not refetch |
| Selection | WETH can appear on either side; one canonical pool per token |
| Features | Changing hour 5 leaves 1h unchanged; changing hour 20 leaves 1h/6h unchanged |
| Leakage | Changing day-8 TVL changes only labels; future-ending buckets are excluded |
| Labels | 100→20 is positive; 100→21 is negative; invalid denominator is unlabeled |
| Splits | Tokens do not cross splits; temporal outcome boundaries are respected |
| Scoring | Correct feature order, bounded probability, monotonic bands, accurate explanation scale |

Add meaningful tests with each component. Run relevant pytest checks and Ruff after implementation changes; no test pass or live-source success is claimed by this plan.
