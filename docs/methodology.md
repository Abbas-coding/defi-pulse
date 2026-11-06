# Research and Evaluation Methodology

## Questions

DS: Which early activity, price, and TVL patterns are associated with later severe USD-TVL deterioration?

ML: Do 1h, 6h, or 24h histories predict the defined endpoint better than simple baselines on later pools? How reliable and interpretable are the estimates?

Useful early predictive signal is a hypothesis, not a deliverable we can guarantee.

## Primary Outcome

For creation time `t0`, the baseline target is:

```text
y = 1 when TVL(t0 + 8 days) <= 0.20 * TVL(t0 + 24 hours)
y = 0 otherwise, provided both endpoint measurements are valid
```

Invalid/missing outcomes remain unlabeled. The hour-24 denominator must be positive. Treatment of a verified zero day-8 value is pending approval because the context's formula and label-test wording conflict; see [decisions](decisions.md).

This endpoint does not capture every temporary collapse, prove liquidity removal, or identify fraud. USD valuation changes and source quality complicate interpretation.

## Features and Windows

Each model uses the available history throughout its window, not a single endpoint snapshot. Candidate features include initial/end TVL, changes, extrema, drawdown, cumulative volume/counts, activity patterns, and price return/variability. Only compute statistics supported by the observation count and source semantics.

The 1h feature set may be smaller. Missing-value policies must not fabricate trends or volatility. Never use current lifetime pool aggregates, future observations, future outcomes, or later backfills. Use the same labels and comparable pool cohorts across windows; disclose coverage-driven differences.

## DS Protocol

Produce a selection funnel, quality profile, distribution summaries, early trajectories, and outcome-group comparisons. Start with the context's hypotheses about volatility, activity, and early TVL changes. Report effect sizes, uncertainty, sample counts, and multiple-comparison limitations. Treat broad exploratory discoveries as exploratory.

Separate exploratory training-period findings from final test assessment. Freeze model-relevant choices before inspecting test outcomes. DS outcome summaries must not become an indirect route to tuning against the test set.

## ML Protocol

1. Split by creation date into older training, later validation, and newest test periods; approximately 70/15/15 is an initial design, not a guaranteed allocation.
2. Keep each token/pool in one split and purge overlapping outcome windows at boundaries. Start from the context's suggested eight-day gap and verify actual timestamp relationships.
3. Fit preprocessing only on training data. Use temporally safe tuning folds if needed.
4. Compare Dummy, Logistic Regression, Random Forest, and XGBoost with modest CPU budgets.
5. Choose models, thresholds, and any calibration procedure without test feedback. Specify separate fitting/calibration/tuning slices or a temporally safe equivalent before training.
6. Evaluate the frozen pipeline once on the held-out test period. Report insufficient class counts instead of forcing misleading metrics.

Report prevalence, precision, recall, F1, confusion matrices, average precision, secondary ROC-AUC where defined, Brier score, and reliability plots. Distinguish average precision from trapezoidal PR-AUC in metric names. Compare probability quality against a constant-prevalence baseline. Add time-aware uncertainty estimates where feasible.

## Interpretation

Calibration and Low/Medium/High bands require adequate validation evidence; otherwise identify scores or bands as experimental. Save threshold policy with each model bundle.

SHAP explains model contributions, not causes. Record its output scale and whether it explains the underlying estimator or displayed calibrated output. Generate deterministic explanations from verified signs and feature definitions.

## Pending Extensions

A 48h/72h comparison has been discussed but is not approved. Keeping the existing target would expose part of the outcome period; moving the target would change the experiment. Do not implement either interpretation without agreement. Optional threshold sensitivity analyses must not replace the primary target retrospectively.
