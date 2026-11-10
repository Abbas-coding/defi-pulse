# Historical Demo Design

## Purpose and Users

Help teammates and instructors inspect the dataset, understand early behavior, and evaluate historical predictions. Use cleaned Parquet/CSV prediction and SHAP extracts for the Tableau dashboard after data and model validation. The earlier local Streamlit interface remains optional.

## Data Science Explorer

Show the cohort date range, pool counts, selection funnel, and data-quality summary. Selecting a historical pool reveals early TVL, volume, and normalized price trajectories. Charts use explicit units and distinguish observed from missing/imputed data.

Present a small set of DS findings with sample sizes and limitations. Provide feature definitions in plain language. Avoid interpreting USD-TVL decline as proof of fraud or withdrawal.

## Early Risk Assessment

1. Select a held-out historical pool and 1h/6h/24h cutoff.
2. Display creation time, prediction cutoff, observation coverage, and permitted history.
3. Score the matching feature row using the saved model bundle.
4. Display model version, score/probability status, supported risk band, and top explanatory features.
5. Offer a separate “Reveal historical outcome” section showing hour-24/day-8 TVL and the observed label.

Inference must not read the outcome. Every displayed score must be traceable to a stored bundle and feature artifact. Explain the event precisely: at least 30% day-8 USD-TVL deterioration relative to hour 24.

## Continuous Change and Explainability

For the same pool/window and split, show predicted signed TVL percentage change from hour 24 to day 8, separately from the classification probability. Identify the regression model and target transform, and reveal observed change only through the outcome display path. Global SHAP views use summary/beeswarm and bar plots; pool views use waterfall/force plots. Distinguish classification margin/probability units from regression percentage-point or transformed-target units. Read task-aware versioned extracts according to the [Tableau contracts](modeling_update.md#tableau-export-contracts).

## Evaluation View

An optional compact view compares models/windows with prevalence, event counts, precision-recall results, confusion matrices, and probability-quality plots, plus RMSE, MAE, and R² for regression. Display errors in percentage points and include dummy baselines for both tasks. Make weak or inconclusive results visible. Avoid a headline accuracy number detached from the baseline.

## Empty and Failure States

- No model artifact: explain that training has not been completed; do not invent a prediction.
- Insufficient history: show coverage and why a window cannot be scored.
- Missing outcome: allow supported inference but mark the historical outcome unavailable.
- Unvalidated calibration/bands: identify the score or band as experimental/provisional.
- Incompatible feature schema or bundle: stop scoring with a clear diagnostic.

## Presentation Principles

Use readable charts, consistent scales where comparisons require them, descriptive labels, and text alongside color-coded risk. Keep outcomes visually separate from early inputs. Show uncertainty and data quality near the affected result. No wallet connection, account system, trading controls, live feed, or paid hosting is planned.

Synthetic fixtures may support development, but any visible synthetic case must be labeled illustrative and excluded from reported research metrics.
