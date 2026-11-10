# Implementation Work Packages

## Current State

The standalone Graph demo is implemented. A standard-library research source probe now lives in `src/defi_pulse/pilot.py`, with semantic tests in `tests/test_pilot.py`. It collects a bounded canonical cohort, early hourly histories, and provisional endpoint evidence; it does not create final labels or models. The broader packages below remain planned. Instructor approval was confirmed by the user on 2026-11-09.

## Baseline Implementation — 2026-11-10

`src/defi_pulse/data_preparation.py` now constructs versioned candidate targets, fixed chronological splits with an eight-day embargo, and supported first-1h/6h/24h activity features. `src/defi_pulse/baselines.py` provides audit-only default behavior and explicit experimental Dummy/Logistic Regression/Dummy mean/median/Ridge training, CSV/Parquet exports, saved pipelines, and manifests. See [executed results](baselines.md). Final verified targets, tree models, SHAP, and DS statistical-test implementation remain pending.

## Approved Modeling Update — Original Documentation Revision

Follow the [2026-11-10 specification](modeling_update.md): version the 30% classification label and signed percentage-change regression target, preserve collectors/ETL and early feature logic, and reuse the specified chronological 70/15/15 split with an eight-day embargo for both tasks. Preserve Mann–Whitney U and chi-square methods. Existing collector candidate labels are still 80%; the separate baseline module now derives versioned 30%/regression candidates without changing those old files.

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
- Implement pure feature and target builders with explicit contracts for `y_class` (30% decline) and `y_reg` (percentage change), versioning both definitions. Preserve endpoint quality/zero-handling gates.
- Keep Mann–Whitney U and chi-square methods; recompute outcome-dependent comparisons for the new class groups.
- Validate a 100-pool checkpoint before conditional scale-up.
- Build source/pilot, cleaning, EDA, and statistical-findings notebooks.
- Add a dataset card covering provenance, units, missingness, selection bias, and reproducibility.

Acceptance: cached inputs reproduce tables and findings; each output can be traced to source records and settings.

## 4. Models and Evaluation

- Save the shared chronological 70/15/15 split assignments with an eight-day embargo and the frozen experiment configuration for both tasks.
- Implement training-only preprocessing, baselines, model comparisons, and budgeted tuning.
- Compare Dummy/Logistic Regression/Random Forest Classifier/XGBoost Classifier using F1, Precision, Recall, PR-AUC, ROC-AUC, and Confusion Matrix.
- Compare mean/median Dummy/Linear or Ridge/Random Forest Regressor/XGBoost Regressor using RMSE, MAE, and R² on the same saved splits.
- Save reproducible task-specific metrics with counts, units, and uncertainty limitations.
- Assess calibration; implement supported bands and explanations with a versioned scoring bundle.

Acceptance: scoring enforces feature order/window compatibility; no test feedback influences selection; all reported claims match artifacts.

## 5. Demo and Academic Handoff

- Add `shap` with modeling dependencies; generate global summary/beeswarm and bar plots plus local waterfall/force plots for selected compatible classification/regression models. Verify reconstruction and output units using training-only background data.
- Export class outputs, regression predictions, and global/local SHAP tables to versioned cleaned Parquet/CSV for Tableau.
- Implement the [historical interface](design.md) using these extracts and saved bundles; the earlier Streamlit implementation is optional.
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
| Labels | 100→70 is class 1/regression -30%; 100→71 is class 0/regression -29%; invalid denominator is unlabeled |
| Splits | Both tasks reuse split IDs; tokens do not cross splits; eight-day embargo is respected |
| Regression/SHAP | Percentage units and target transforms are explicit; contributions reconstruct the recorded output |
| Tableau | Prediction/SHAP joins preserve task/window/model keys and target versions |
| Scoring | Correct feature order, bounded probability, monotonic bands, accurate explanation scale |

Add meaningful tests with each component. Run relevant pytest checks and Ruff after implementation changes; no test pass or live-source success is claimed by this plan.
