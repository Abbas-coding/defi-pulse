# DeFi Pulse Project Documentation

## Implemented Baselines — 2026-11-10

The [first baseline run](baselines.md) now prepares 30%/regression candidate targets, activity feature tables, and shared embargoed splits. Fifteen fixed experimental models fitted; results are poor or inconclusive, pricing remains unverified, and final labels remain unset. Trees, SHAP, named DS statistical tests, and final untouched evaluation remain pending.

## Current Modeling Specification — 2026-11-10

Read the [approved classification, regression, SHAP, and Tableau update](modeling_update.md) first. Classification now targets a **30%** hour-24-to-day-8 decline; regression predicts percentage change over the same interval. The intended 1h/6h/24h features, chronological 70/15/15 split, eight-day embargo, Mann–Whitney U, and chi-square methods are preserved. The first fixed baselines are implemented as described above; remaining modeling/statistical components are planned.

All diagnostic class counts below refer to the **previous 80% definition**. They are historical evidence, not new 30% results; the original collectors and diagnostic artifacts have not been relabeled; new versioned targets live in a separate baseline output directory.

Status: planning baseline, prepared 2026-11-06. The research implementation has an initial source probe; labels, features, models, and the interface remain planned. A separate [ten-pool Graph learning demo](graph_demo.md) is implemented with offline tests; authenticated extraction has succeeded for ten pools and one UTC hour in the learning demo. A bounded 20-pool research source probe has now run; see [measured findings](feasibility_report.md) and [source evidence](source_schema.md). Endpoint feasibility remains unresolved. No model or performance result exists.

These documents develop the [project context](../DEFI_PULSE_CODEX_PROJECT_CONTEXT.md) into an actionable engineering and research plan. The context remains a reference, not an immutable specification. Departures require user approval before adoption; open choices are recorded explicitly.

## Three-Day Comparison

The [day-1/day-2/day-3 comparison](three_day_activity.md) is complete for the same 200 pools. Most pools became quieter: 177 had no swaps on day 2 and 180 on day 3. Extending observation did not broaden the set reaching ten cumulative swaps. Prediction windows and target are unchanged.

## 200-Pool Diagnostic

The user-approved [200-pool diagnostic](diagnostic_200.md) is complete: 3,041 first-day swaps, 13 positive and 169 negative candidate outcomes, with 18 unresolved cases. Valuation review remains necessary before final labels or training.

## Latest Research Evidence

The [historical-state follow-up](historical_state_report.md) retrieved hour-24 and day-8 states for all 20 pilot pools. All cutoff timestamps matched, but USD pricing still requires review and there are no positive candidate outcomes in this cohort.

## Learning Demo

Start with [The Graph setup and learning demo](graph_demo.md) to configure a local API key, retrieve one UTC hour for ten WETH pools, and inspect cached JSON and CSV. This is separate from the research pilot.

## Reading Order

1. [Project plan](plan.md): objectives, scope, milestones, and acceptance gates.
2. [Architecture](architecture.md): components, dependencies, and artifact flow.
3. [Data design](data_design.md): sampling, collection, temporal semantics, and table contracts.
4. [Research methodology](methodology.md): labels, features, comparisons, and evaluation.
5. [Implementation](implementation.md): concrete work packages and verification.
6. [Demo design](design.md): historical exploration and prediction experience.
7. [Decisions](decisions.md): baseline commitments, unresolved questions, and proposed changes.
8. [Feasibility checklist](feasibility.md): evidence required before scaling collection.

## Working Rules

- Treat proposed paths and commands as designs until implementation makes them executable.
- Record measured facts separately from assumptions and targets.
- Keep the 1h/6h/24h histories and common outcome as the baseline; later windows remain a proposal.
- Obtain user agreement before adopting departures from the context. Verify instructor approval before formal graded implementation; this documentation does not establish that approval.
- Update the relevant document when an approved decision changes. Keep experiment definitions versioned so old results remain interpretable.
- Preserve the original context and `AGENTS.md` unless separately authorized to edit them.
