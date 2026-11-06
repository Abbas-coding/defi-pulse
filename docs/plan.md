# Project Plan

## Objective

Build a reproducible, local Data Science and Machine Learning study of historical Ethereum Mainnet Uniswap v3 TOKEN/WETH pools. Investigate whether early behavior is associated with, and can predict, severe later USD-TVL deterioration.

The DS submission explains data quality, behavioral patterns, statistical evidence, and limitations. The ML submission evaluates predictive performance and explanations on later unseen pools. Both share one data pipeline.

## Baseline Scope

- One canonical pool per target token; historical pool creation does not imply recent token deployment.
- Features summarize available history from creation through 1h, 6h, or 24h.
- Common target: at least 80% USD-TVL decline between hour 24 and day 8.
- The Graph is the preferred source, subject to verified access and historical completeness.
- CPU execution, no mandatory spending, and a small historical Streamlit demo.
- Compare Dummy, Logistic Regression, Random Forest, and XGBoost; calibration and risk bands depend on sufficient evidence.

Exclude trading, wallets, smart-contract deployment, full-chain indexing, live monitoring, additional chains/protocols, and deep learning.

## Milestones and Acceptance Gates

| Milestone | Deliverable | Gate before proceeding |
|---|---|---|
| M0: preparation and source discovery | Environment, schema evidence, minimal authenticated query | Instructor approval status established before formal build; usable source verified without paid requirements |
| M1: feasibility pilot | Reproducible 20–30-pool extraction and report | Defensible early observations and endpoint labels for a documented subset; costs and exclusions measured |
| M2: dataset and DS | 100-pool checkpoint, conditional expansion toward 300–1,000 pools, quality report and DS notebooks | Reproducible selection, usable outcomes, leakage checks, and transparent filtering |
| M3: predictive evaluation | Chronological baseline and model comparisons for feasible windows | Untouched test period, meaningful class counts, reproducible metrics and limitations |
| M4: interpretation | Calibration assessment, risk-band policy, SHAP and templates | Output claims match evidence and explanation scale |
| M5: handoff | Historical demo, notebooks, reports, dataset card, contribution record | Another teammate can replay cached data and reproduce principal outputs |

Stop and report after the agreed pilot milestone. Scaling follows review of its evidence; missing data must not be replaced with invented records.

## Provisional Six-Week Schedule

Weeks 1–2 cover access, pilot, and robust collection. Week 3 covers features and DS analysis. Week 4 covers baselines and model comparisons. Week 5 covers probability assessment, explanation, and the demo. Week 6 covers robustness, academic reports, and reproduction rehearsal. These are targets, not established deadlines.

Suggested responsibilities: member A owns acquisition; B owns quality, labels, and DS; C owns evaluation and explanations. Confirm assignments with the team. Everyone must understand the target and leakage rules.

## Success and Failure

Success means a defensible study, not a promised accuracy score. Early windows may show little predictive value. Report negative results and compare against simple baselines. If data cannot support the target or later evaluation cohorts, pause the affected work and request an evidence-based scope decision.
