# Approved DS/ML Context Update — 2026-11-10

> **Subsequent implementation, 2026-11-10:** the [baseline pipeline](baselines.md) now builds separate versioned candidate targets and activity features, applies the shared embargoed splits, and runs fixed experimental classification/regression baselines. Source pricing remains unverified; final labels, tree models, SHAP, and named DS statistical tests remain pending. Statements below about a documentation-only update describe the earlier specification revision.

This document records the user's approved changes to the modeling specification.
It supersedes the previous 80% classification threshold and classification-only
scope. This update changes documentation only; it does not claim that models,
new labels, SHAP artifacts, or Tableau exports have been implemented or run.

## Preserved Pipeline

Keep the existing ETL and GraphQL collection code, sampling, source snapshots,
quality checks, and first 1h/6h/24h feature-window logic unchanged. Preserve
chronological train/validation/test allocation of 70/15/15 with an eight-day
embargo, grouping each pool/token into one split. Record actual retained counts
after embargo and quality exclusions instead of forcing exact percentages by
breaking time boundaries. Both tasks and all windows reuse the same saved split
assignments; report task/window-specific missingness exclusions separately.

Preserve Mann–Whitney U for the specified continuous-variable comparisons and
chi-square for the specified categorical comparisons. Their method does not
change; group membership and results must be recalculated for the 30% label.
Continue reporting sample sizes, effect sizes, assumptions, uncertainty, and
multiple-comparison limitations. Do not reuse old test results as new findings.

Repository status: the collectors and activity diagnostics exist. Final feature
engineering, model training, split assignment, the named statistical tests,
SHAP generation, and Tableau model exports are planned, not implemented. The
user's preservation instruction fixes their intended methods; it does not
establish that code for those methods already exists.

## Versioned Targets

Let `A = TVL_USD(t0 + 24 hours)` and `B = TVL_USD(t0 + 8 days)`.
Apply the existing endpoint validity, timing, valuation, and missingness rules
before constructing either target; `A` must be strictly positive.

```text
classification_definition_version = tvl_decline_30pct_h24_day8_v2
y_class = 1 if B <= 0.70 * A else 0

regression_definition_version = tvl_change_pct_h24_day8_v1
y_reg = ((B - A) / A) * 100
```

The classification event is **at least 30% USD-TVL deterioration**; regression
predicts the signed percentage change over the same endpoint interval. For
valid endpoints, the event corresponds to `y_reg <= -30`. Use precise endpoint
comparisons, not rounded dashboard percentages, to assign the class.

| Hour-24 TVL | Day-8 TVL | `y_class` | `y_reg` |
|---:|---:|---:|---:|
| 100 | 70 | 1 | -30% |
| 100 | 71 | 0 | -29% |
| 100 | 120 | 0 | +20% |

Missing/invalid endpoints produce no target; do not impute outcomes. Previously
unresolved verified-zero day-8 handling remains an endpoint-quality decision;
this update does not silently resolve it. A log-ratio regression alternative
may be documented and versioned if extreme right-skew warrants it. It requires
positive endpoints and an explicit zero-value policy. Export its transform and
inverse-transform metadata and evaluate dashboard predictions in percentage
change units. Do not silently substitute log units for percentages.

Neither target nor day-8 measurements may enter inference features. Hour-24
values are unavailable to the 1h/6h feature builders. The separate day-2/day-3
diagnostic does not authorize 48h/72h model inputs.

## Models and Evaluation

| Task | Baseline | Comparators | Required metrics |
|---|---|---|---|
| Classification | Dummy Classifier | Logistic Regression, Random Forest Classifier, XGBoost Classifier | F1, Precision, Recall, PR-AUC, ROC-AUC, Confusion Matrix |
| Regression | Mean and/or median Dummy Regressor | Linear/Ridge Regression, Random Forest Regressor, XGBoost Regressor | RMSE, MAE, R² |

Keep existing class-prevalence, probability-quality, calibration, and risk-band
safeguards. Define the PR-AUC integration convention; report average precision
separately if used, rather than silently treating the two as identical metrics.
MAE/RMSE on `y_reg` are in percentage points. Report undefined metrics and
insufficient evaluation counts explicitly; R² is not classification accuracy.

Fit preprocessing on training data only. Select hyperparameters, the best model
for each task/window, classification decision thresholds, and optional target
transforms using permitted validation data, never final test feedback. Choose
and record task-specific model-selection criteria before comparison. Keep
scoring bundles separate for classification and regression while reusing the
same feature and split versions. Regression does not require probability
calibration or classification risk bands.

## Explainability

Add the `shap` dependency when implementing modeling; retain the existing
standard-library-only collector setup. Use compatible tree/linear explainers
for selected best-performing classification and regression models.

- Global: summary/beeswarm and mean absolute SHAP bar plots.
- Local: waterfall and/or force plots for selected historical pools.
- Save feature values, signed SHAP values, expected/base value, model output,
  task, window, model version, explanation output scale, and background-data
  provenance. Background data must come from the permitted training cohort.
- Verify base value plus contributions reconstructs the explained model output
  within tolerance. Classification may explain margin/log-odds or probability;
  never display log-odds as probability percentage points. Explain any difference
  between the underlying estimator and a displayed calibrated probability.
- Regression explanations must identify percentage-point or transformed target
  units. Nonlinear inverse transformation does not automatically convert SHAP
  contributions into additive percentage-point contributions.

SHAP describes model contributions, not causes of withdrawals or fraud.

## Tableau Export Contracts

Planned cleaned Parquet/CSV extracts share stable pool/window/split/model keys.
Dashboard views can join predictions and explanatory summaries; inference
builders continue to keep future outcomes separate from model inputs.

| Extract | Grain | Required content |
|---|---|---|
| Predictions | Pool, window, task, model version | Class score/probability and decision; regression prediction in percentage-change units; optional observed targets; both definition versions, feature version, split, quality, calibration/transform status |
| Global SHAP | Task, window, model version, feature, explained cohort | Mean absolute SHAP, rank, sample count, output scale, cohort/split and background provenance |
| Local SHAP | Pool, task, window, model version, feature | Feature value, signed contribution, base value, explained output, scale and explanation version |

Expose `predicted_tvl_change_pct` alongside classification output and label it
as a percentage change, not predicted TVL in dollars. Keep task identifiers to
prevent multiplying prediction rows through an ambiguous SHAP join. All exports
must carry definition versions so historical 80% results cannot be confused
with 30% outputs. Actual clean extracts and plots are future deliverables.

## Migration and Historical Evidence

Existing collectors still calculate **80% candidate labels**. Do not rename or
overwrite them as 30% results. A later implementation will derive versioned
`y_class`/`y_reg` from validated cached endpoints and rerun outcome-dependent DS
comparisons, training, evaluation, and exports. Historical reports retain their
original numbers and explicitly identify the 80% definition. No new class
balance, regression score, SHAP plot, or model quality is claimed by this update.
