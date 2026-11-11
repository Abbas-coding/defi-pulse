# First Classification and Regression Baselines — 2026-11-10

Follow-up (2026-11-11): the [executed notebook](../notebooks/01_defi_pulse_end_to_end.ipynb) now presents these same results with EDA, training, 19 charts, and training-only statistical comparisons. Original baseline results below are preserved.

This implementation prepares versioned 30%/percentage-change candidate targets,
shared chronological splits, and first-1h/6h/24h activity feature tables entirely
from cached diagnostic data. Fixed exploratory baselines are available behind
an explicit provisional-target flag. These are development-cohort diagnostics;
final financial label verification and an untouched test cohort remain pending.

## Targets and Audit

Use the inclusive Decimal comparison `day8 <= 0.70 * hour24` for the class and
`((day8 - hour24) / hour24) * 100` for signed percentage change. Version both
definitions as specified in [the modeling update](modeling_update.md).
Retain exact endpoint amounts and regression target strings before conversion
to numeric estimator inputs; rounding does not determine the class.

Of 200 pools, 182 pass structural checks: endpoint identity, exact requested
time, reference block, finite positive baseline TVL, nonnegative balances, and
finite target values. These produce **25 positive and 157 negative candidates**.
Ten zero/invalid baselines and eight nonexact endpoint pairs remain excluded;
no staleness or zero-outcome policy was silently changed. No labels were imputed.

This structural audit does **not** independently verify USD pricing. All final
labels remain null. Descriptive flags identify 111 eligible hour-24 values below
$1, 130 unchanged balance/USD pairs, and one percentage gain exceeding 1,000%.
These flags are not exclusion rules. No tiny pool, extreme target, or inactive
pool was silently removed. Eligible regression targets range from approximately
-100% to +64,495.77%; no clipping, winsorization, or log-target switch is used.

The default command stops at audit/data exports. The explicit
`--allow-provisional-targets` mode permits an experimental run using the source
valuation candidates. It does not promote those candidates to validated labels.

## Features and Preprocessing

Each window has one row per pool with only that window's:

- swap count;
- distinct transactions containing swaps;
- active elapsed hours;
- source-reported USD swap volume;
- immutable fee-tier category.

Feature eligibility requires complete swap extraction and finite, nonnegative,
internally consistent activity values. All 600 window/pool rows pass these
checks; no imputation is needed. Genuine zero trading stays zero. USD volume
still has the source-pricing caveat. TVL features and unsupported volatility
statistics are excluded from this first baseline pending validation, not filled
with invented values.

Numeric features use fixed `log1p` followed by a StandardScaler fitted on training
pools only. Fee tier uses training-fitted one-hot encoding with unseen categories
ignored. The raw feature exports remain unchanged by these model transforms.
Pool/token IDs, dates, future outcomes, later-window features, and day-2/day-3
activity do not enter the estimator matrix. Existing ETL and collectors remain
unchanged.

## Fixed Chronological Experiment

Sort the full frozen cohort by creation time/address before looking at target
eligibility. Assign nominal 70/15/15 positions and purge earlier rows whose
eight-day outcome interval crosses the next nominal split's creation boundary.
Both tasks and all feature windows reuse these assignments.

| Split | Nominal pools | Retained after embargo | Eligible targets/features |
|---|---:|---:|---:|
| Training | 140 | 100 | 93 (18 positive, 75 negative) |
| Validation | 30 | 10 | 10 (0 positive, 10 negative) |
| Test | 30 | 30 | 27 (4 positive, 23 negative) |

Sixty pools are embargoed. The four disjoint sampling weeks make the retained
sizes differ substantially from the nominal proportions. No boundary was moved
to improve event counts. All ten validation regression targets are zero too.
Consequently validation cannot support classification discrimination, regression
R², calibration, or a meaningful best-model selection. Previously explored
outcomes also mean that the test partition is a chronological development
diagnostic, not a pristine final test.

Fixed models, chosen before fitting and saved in `configuration.json`:

- Classification: prior-probability DummyClassifier and Logistic Regression
  (`C=1`, balanced training class weights, maximum 2,000 iterations, seed 42).
- Regression: mean and median DummyRegressor, and Ridge (`alpha=1`).
- Classification decision threshold: 0.5. Regression target: raw signed
  percentage change. No search, threshold tuning, calibration, resampling,
  clipping, or winner selection.

## Metrics

Classification exports F1, Precision, Recall, trapezoidal PR-AUC, separately
named Average Precision, ROC-AUC, a `[0,1]` confusion matrix, prevalence, and
Brier score. Single-class evaluation leaves discrimination/positive-class
metrics undefined rather than presenting a high accuracy as success.
Trapezoidal PR-AUC and Average Precision differ, especially for constant
scores; compare the explicitly named metrics against the dummy baseline.

Regression exports RMSE and MAE in **percentage points**, plus R² when the
evaluation targets vary. R² is null for the constant validation targets.
Predictions below -100% are counted and left visible rather than clipped.

## Executed Development Results

All 15 fixed baselines fitted successfully: five models for each of three
windows. Each used the same 93 training pools. The run exported 555 held-out
prediction rows and 30 model/window/split metric records. No model or threshold
was selected using these results.

Classification on the chronological development test (27 pools, four positive
candidates):

| Model/window | F1 | Precision | Recall | PR-AUC (trapezoidal) | Average Precision | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Dummy prior, all windows | 0.000 | 0.000 | 0.000 | 0.574 | 0.148 | 0.500 |
| Logistic, 1h | 0.118 | 0.077 | 0.250 | 0.340 | 0.366 | 0.424 |
| Logistic, 6h | 0.111 | 0.071 | 0.250 | 0.330 | 0.353 | 0.337 |
| Logistic, 24h | 0.111 | 0.071 | 0.250 | 0.328 | 0.352 | 0.326 |

Logistic Regression catches one of four positive candidates at every window,
with 12 false positives at 1h and 13 at 6h/24h. The dummy predicts no positive
cases. The conflicting AP/ROC perspectives and very small event count do not
establish useful discrimination. Full confusion matrices and probability
quality are in `metrics.json`; no accuracy headline or calibrated risk claim is
made. Single-class validation metrics remain explicitly undefined.

Regression on the same 27 test pools:

| Model/window | RMSE (percentage points) | MAE (percentage points) | R² |
|---|---:|---:|---:|
| Dummy mean, all windows | 681.58 | 676.03 | -60.664 |
| Dummy median, all windows | 87.33 | 38.90 | -0.012 |
| Ridge, 1h | 3,174.96 | 2,146.89 | -1,337.080 |
| Ridge, 6h | 3,205.39 | 2,257.14 | -1,362.849 |
| Ridge, 24h | 2,414.10 | 1,972.94 | -772.599 |

Ridge is substantially worse than the median dummy in this diagnostic. The
extreme +64,495.77% training target, small denominators, weak features, and
source-pricing uncertainty require investigation before interpreting the task.
No extreme value was silently removed. Ridge also produces physically invalid
below-minus-100% predictions for 6, 3, and 8 test pools respectively; these are
flagged and kept visible. Validation R² is undefined because all actual changes
are zero. These poor results are evidence to report, not a reason to tune on
this already-examined test partition.

Next work: independently audit USD valuation semantics, investigate tiny
baseline values and the extreme gain, and collect suitably spaced new cohorts
with genuine validation/test events using a fixed sampling design. Any target
transform or eligibility-policy change must be recorded before a new experiment;
do not relabel these results or use them as an untouched final evaluation.

## Reproduction and Artifacts

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-baselines.lock
PYTHONPATH=src .venv/bin/python -m defi_pulse.baselines
PYTHONPATH=src .venv/bin/python -m defi_pulse.baselines --allow-provisional-targets
.venv/bin/python -m unittest discover -s tests -v
```

The two modes write separately to `data/baselines_30pct/audit/` and
`data/baselines_30pct/experimental/`. Generated data and models are ignored by
Git. An output directory cannot be reused for a different input/configuration
without choosing a new path.

CSV/Parquet outputs include `targets`, `splits`, `features_1h/6h/24h`, `metrics`,
and `predictions`. Prediction rows identify task/window/model version, source
quality, split, target/feature versions, and whether a class score or percentage
change is being predicted. Future outcomes are explicitly provisional display/
evaluation fields, never estimator inputs. Models are saved with preprocessing,
feature order, configuration, and input hashes in task/window-specific bundles.
No SHAP values are fabricated; tree models, SHAP, statistical-test implementation,
and final calibrated dashboard outputs remain subsequent work.

The manifest records source/input and output hashes, package/Python versions,
quality/split counts, model paths, limitations, and zero API requests. Historical
80% diagnostic outputs are preserved.

## Technical References

The implementation uses scikit-learn's [Logistic Regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html),
[Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html),
and explicitly named [evaluation metrics](https://scikit-learn.org/stable/modules/model_evaluation.html).

## Verification

Thirty-three semantic tests pass in the locked modeling environment, including training-only scaling/encoding, window leakage, exact threshold arithmetic, invalid targets, embargo boundaries, and undefined-metric handling. The dependency check reports no broken requirements. Audit mode produces no model files; the experimental run and scoring use zero Graph requests.

A second experimental run reproduced the metric records and CSV/Parquet prediction/target/split hashes. All 15 saved pipelines were reloaded and reproduced the 555 exported predictions within numerical tolerance. Input hashes remain unchanged; audit-mode predictions are empty and no audit-mode model files exist.
