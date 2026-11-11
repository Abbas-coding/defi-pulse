# Research and Evaluation Methodology

Current specification: [approved update, 2026-11-10](modeling_update.md). Classification and regression share validated endpoints, feature windows, and split assignments. Fixed experimental baselines and training-only Mann–Whitney U/chi-square comparisons are implemented in the [executed notebook](../notebooks/01_defi_pulse_end_to_end.ipynb). Verified financial labels, tree models, SHAP, and final untouched evaluation remain pending.

## Questions

DS: Which early activity, price, and TVL patterns are associated with later USD-TVL deterioration?

ML: Do 1h, 6h, or 24h histories predict the defined endpoint better than simple baselines on later pools? How reliable and interpretable are the estimates?

Useful early predictive signal is a hypothesis, not a deliverable we can guarantee.

## Primary Outcome

For creation time `t0`, the baseline target is:

```text
y_class = 1 when TVL(t0 + 8 days) <= 0.70 * TVL(t0 + 24 hours)
y_class = 0 otherwise, provided both endpoint measurements are valid
y_reg = ((TVL(t0 + 8 days) - TVL(t0 + 24 hours)) / TVL(t0 + 24 hours)) * 100
```

Invalid/missing outcomes remain unlabeled. The hour-24 denominator must be positive. Treatment of a verified zero day-8 value is pending approval because the context's formula and label-test wording conflict; see [decisions](decisions.md).

This endpoint does not capture every temporary collapse, prove liquidity removal, or identify fraud. USD valuation changes and source quality complicate interpretation.

The primary class event is at least **30% deterioration**. The regression target is signed percentage change (negative for decline). Version definitions as `tvl_decline_30pct_h24_day8_v2` and `tvl_change_pct_h24_day8_v1`. A documented log-ratio alternative is permitted for extreme right-skew only with explicit domain/zero handling and inverse-transformed percentage-change predictions; do not silently change units. Preserve existing endpoint quality rules and do not impute outcomes.

## Features and Windows

Each model uses the available history throughout its window, not a single endpoint snapshot. Candidate features include initial/end TVL, changes, extrema, drawdown, cumulative volume/counts, activity patterns, and price return/variability. Only compute statistics supported by the observation count and source semantics.

The approved missingness policy treats a valid absent hourly record as assumed no trading, with a separate flag preserving that assumption. Missing state measurements remain unknown; do not interpret the assumption as measured zero TVL or price. Source incompleteness remains a limitation.

The 1h feature set may be smaller. Missing-value policies must not fabricate trends or volatility. Never use current lifetime pool aggregates, future observations, future outcomes, or later backfills. Use the same labels and comparable pool cohorts across windows; disclose coverage-driven differences.

## DS Protocol

Produce a selection funnel, quality profile, distribution summaries, early trajectories, and outcome-group comparisons. Start with the context's hypotheses about volatility, activity, and early TVL changes. Report effect sizes, uncertainty, sample counts, and multiple-comparison limitations. Treat broad exploratory discoveries as exploratory.

Retain **Mann–Whitney U** for the specified continuous-variable comparisons and **chi-square** for categorical comparisons. Preserve their assumptions and reporting; recompute outcome-group analyses after constructing the new 30% labels.

Separate exploratory training-period findings from final test assessment. Freeze model-relevant choices before inspecting test outcomes. DS outcome summaries must not become an indirect route to tuning against the test set.

## ML Protocol

1. Split by creation date into older training, later validation, and newest test periods; retain the specified 70/15/15 allocation and document retained counts after quality exclusions and embargo.
2. Keep each token/pool in one split and purge overlapping outcome windows at boundaries. Retain the eight-day embargo and verify actual timestamp relationships. Classification and regression reuse identical saved pool split assignments.
3. Fit preprocessing only on training data. Use temporally safe tuning folds if needed.
4. Classification: compare Dummy Classifier, Logistic Regression, Random Forest Classifier, and XGBoost Classifier. Regression: compare mean/median Dummy Regressor, Linear/Ridge Regression, Random Forest Regressor, and XGBoost Regressor, with modest CPU budgets.
5. Choose models, thresholds, and any calibration procedure without test feedback. Specify separate fitting/calibration/tuning slices or a temporally safe equivalent before training.
6. Evaluate the frozen pipeline once on the held-out test period. Report insufficient class counts instead of forcing misleading metrics.

Classification metrics: F1, Precision, Recall, PR-AUC, ROC-AUC, and Confusion Matrix, plus existing prevalence, average precision, Brier score, and reliability reporting where supported. Regression metrics: RMSE, MAE, and R²; MAE/RMSE are percentage-point errors for the percentage-change target. Report undefined metrics and insufficient sample counts explicitly. Distinguish average precision from trapezoidal PR-AUC in metric names. Compare probability quality against a constant-prevalence baseline. Add time-aware uncertainty estimates where feasible.

## Interpretation

Calibration and Low/Medium/High bands require adequate validation evidence; otherwise identify scores or bands as experimental. Save threshold policy with each model bundle.

SHAP explains model contributions, not causes. Record its output scale and whether it explains the underlying estimator or displayed calibrated output. Generate deterministic explanations from verified signs and feature definitions.

Use compatible SHAP explainers for the best validation-selected tree/linear models in each task/window. Generate global summary/beeswarm and bar plots, plus local waterfall/force plots. Explain regression in its recorded target units; transformed-target contributions are not automatically additive in percentage space. Use training-only background data and save base values, signed contributions, feature values, task/window/model identity, and output scale.

Export classification predictions, regression `predicted_tvl_change_pct`, global SHAP summaries, and local SHAP values in versioned cleaned Parquet/CSV extracts for Tableau. See [export contracts](modeling_update.md#tableau-export-contracts). Neither outcomes nor explanations become inference features.

## Pending Extensions

The day-2/day-3 descriptive comparison was approved and executed; 48h/72h model inputs remain unapproved. Keeping the existing target would expose part of the outcome period; moving the target would change the experiment. Do not implement either interpretation without agreement. Optional threshold sensitivity analyses must not replace the primary target retrospectively.
