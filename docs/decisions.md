# Decision Register

## Status Definitions

**Baseline** means retained from the context, not newly verified. **Open** means a choice or fact still needs evidence. **Proposed** means a departure has been discussed but not approved. The user requested consultation before changes to the context are adopted.

| ID | Decision | Status | Resolution/evidence needed |
|---|---|---|---|
| D01 | Ethereum Mainnet, Uniswap v3, TOKEN/WETH | Baseline | Verify source and WETH identity during discovery |
| D02 | One canonical pool per token | Baseline; algorithm open | Verify earliest-pool lookup beyond candidate date range |
| D03 | Full available 1h/6h/24h histories | Baseline | Quantify safe hourly coverage; determine need for events |
| D04 | Common hour-24→day-8, ≥80% USD-TVL decline | Baseline | Freeze exact endpoint reconstruction and definition version |
| D05 | Verified zero day-8 TVL | Open; user decision required | Formula implies positive label; context tests reject zero outcome. Proposed distinction: valid measured zero versus invalid/missing zero |
| D06 | The Graph as primary source | Baseline preference | Live endpoint, schema, historical access, free terms, actual account availability |
| D07 | 20–30-pool pilot before scale-up | Baseline | Review measured completeness, costs, and selection losses |
| D08 | 300–1,000-pool target | Conditional baseline | Usable class counts and temporal coverage, not nominal pool count |
| D09 | Sampling dates, eligibility thresholds, staleness | Open | Pilot evidence; document before full extraction |
| D10 | Calibration and risk bands | Conditional baseline | Separate permitted validation data and adequate class counts |
| D11 | 48h/72h observation comparison | Proposed, not approved | User approval and choice of common versus shifted target; acknowledge ongoing-outcome information |
| D12 | Instructor approval and actual rubric | Instructor approval confirmed by user, 2026-11-09; original rubric not independently reviewed | Formal research implementation authorized; obtain course-owned files for final submission |
| D13 | Final model and SHAP display semantics | Open | Evaluation and compatibility; distinguish estimator score from calibrated output |
| D14 | Python version, lock tool, exact dependencies | Open implementation detail | Environment inspection and compatible reproducible setup |

## Approved Missingness Policy (2026-11-09)

The user approved treating an absent hourly record as assumed no trading in that interval when the API response succeeds, has no GraphQL errors, and has the expected response structure. Policy version: `empty_hour_assumed_no_trades_v1`. This replaces the earlier requirement to verify every absent hour with swap queries.

Keep `quality = missing` for the absent raw measurement and add `assumed_no_trades = true` in research exports. Preserve missing TVL, price, liquidity, and raw volume/count fields; the assumption is not an observed zero. API errors, null collections, malformed records, and reported indexing errors must fail visibly rather than becoming assumed inactivity. Do not infer no Mint/Burn events or remove a pool solely because an hour is absent. Source incompleteness can still violate this assumption and must remain a reported limitation.

Instructor approval was separately confirmed by the user on the same date.

## Approved 200-Pool Diagnostic Expansion (2026-11-09)

The user authorized a 200-pool diagnostic after reviewing the 20-pool limitations. Select 50 canonical TOKEN/WETH pools from each fixed interval January 1–7, April 1–7, July 1–7, and October 1–7, 2026 (UTC). Fully paginate candidate discovery within each interval, rank candidates using the fixed `defi-pulse-diagnostic-200-v1` seed and pool address, and verify earliest WETH pools across all dates. Freeze selection before fetching activity or outcomes. Keep inactive pools and exclusions; do not replace candidates based on later measurements.

Fetch individual swap events with deterministic ID pagination for `[creation, creation + 24h)`. Compute separate 1h/6h/24h swap counts, distinct swap transaction counts, volume, and elapsed-hour activity. Preserve source hourly transaction counts as separate measurements over completed buckets. Retrieve hour-24/day-8 historical states for the same cohort. This authorizes a diagnostic expansion, not training or changing the target. Zero-outcome, valuation, and approximate timing policies remain open. Live collection uses an explicit cap of 600 network attempts, including retries; the initial schema probe was separately bounded to one attempt.

## Approved Three-Day Activity Comparison (2026-11-09)

The user authorized checking separate days 1, 2, and 3 for the same frozen 200-pool cohort. Reuse cached day-1 events, retrieve swaps for hours 24–48 and 48–72 at the original indexed snapshot, and compare daily swap counts, volumes, active hours, and delayed starts. Keep cumulative counts separate from daily changes. New extraction is capped at 200 network attempts, including retries, with bounded event pagination.

This approval covers a descriptive diagnostic only. It does not approve 48h/72h model inputs, a shifted outcome target, activity-based pool exclusions, or model training. Existing labels and early windows remain the baseline.

## Change Procedure

For a departure, record the proposed change, reason, evidence, alternatives, and impact on claims, workload, and comparability. Ask the user before adopting it. If instructor-approved deliverables are affected, establish whether instructor agreement is also needed.

Record approvals with date and scope. Then update affected documentation and version any changed data/experiment contracts. Do not relabel a proposal as approved because implementation would be convenient.

## Known Document Discrepancies

- The original `AGENTS.md` describes the initial README-only scaffold. It remains unchanged under the user's preservation instruction; this documentation index describes the newer planning files.
- The context handoff references `PROJECT_CONTEXT.md`; the actual reference file is `DEFI_PULSE_CODEX_PROJECT_CONTEXT.md`.
- Zero outcome handling is internally inconsistent as described in D05. Neither interpretation has been silently selected.
- The context calls several decisions locked; the user's later instruction permits reconsideration with prior consultation. Retain the baseline until a change is approved.
