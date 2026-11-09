# 200-Pool Diagnostic — 2026-11-09

The expanded sample contains actual first-day swap histories for 200 canonical
TOKEN/WETH pools, plus 400 historical endpoint states. Both candidate outcome
classes are present, but most pools are quiet and only 13 meet the deterioration
threshold provisionally. This supports further dataset validation, not a claim
that accurate prediction or calibrated risk estimates are established.

## Selection Frozen Before Activity and Outcomes

The user authorized the expansion after reviewing the initial 20-pool pilot.
Candidate discovery fully paginates both WETH orientations, in these UTC weeks:

| Creation period, inclusive dates | Candidates | Selected |
|---|---:|---:|
| January 1–7, 2026 | 344 | 50 |
| April 1–7, 2026 | 204 | 50 |
| July 1–7, 2026 | 2,080 | 50 |
| October 1–7, 2026 | 145 | 50 |

The 2,773 candidates were ranked within each period by SHA-256 of fixed seed
`defi-pulse-diagnostic-200-v1` plus pool address. Earliest WETH pools were checked
across all creation dates and both orientations; three examined pools were
excluded because an earlier pool existed. Stop at 50 eligible pools per period.
Candidates after the selection boundary are not reported as quality exclusions.
All selected tokens and pool addresses are unique. No activity, TVL threshold,
or outcome was used to choose or replace pools.

This equally weighted temporal sample is not proportional to creation volume
and is not a population prevalence estimate. Creation refers to the pool, not
verified token deployment age. No models or train/test splits were fitted.

## First-Day Trading

Individual swap events were queried for each pool over `[creation, creation +
24h)`, using deterministic ID pagination, at frozen block `26378658`. Event
counts, distinct transaction hashes, volume, and active elapsed hours were
computed separately for 1h, 6h, and 24h. Source hourly `txCount` is retained as
a separate sum over safe completed buckets, not presented as a swap count.

| First-day swaps | Pools |
|---|---:|
| 0 | 19 |
| 1–9 | 149 |
| 10–99 | 28 |
| 100 or more | 4 |

Total swaps: **3,041**. Median per pool: **2**; range: **0–922**. All 200
histories completed within the configured page cap; no counts are lower-bound
substitutes in this executed sample. The collector marks incomplete histories
and leaves exact counts blank if a future run reaches its swap-page cap.

The unique hourly grid has 4,800 pool-hour rows: 379 observed, 4,421 absent.
The median pool has one observed completed first-day bucket. The creation bucket
can be partial; the final partial clock-hour is excluded from hourly features.
Timestamped swap counts cover the full exact elapsed window, including that
final partial hour. Overlapping 1h/6h/24h inputs do not duplicate hourly rows.

**Zero completed missing hourly buckets contained an indexed swap** in this
sample. This is consistent with the approved assumed-inactivity policy, within
the selected source's coverage. It is not independent proof that the indexer
captured every on-chain event. Missing state measurements remain blank.

## Historical Outcomes

The same archive method as the [earlier follow-up](historical_state_report.md)
returned all 400 pool states. Of these, 392 have an indexed transaction at the
exact requested timestamp; eight reference blocks precede cutoff by 12 seconds.
No tolerance was silently adopted: those eight pools' candidate labels remain
unresolved. Ten other pools have zero or invalid hour-24 denominators.

| Period | Candidate ≥80% decline | Candidate below threshold | Unresolved |
|---|---:|---:|---:|
| January | 6 | 39 | 5 |
| April | 2 | 46 | 2 |
| July | 0 | 47 | 3 |
| October | 5 | 37 | 8 |
| **Total** | **13** | **169** | **18** |

These are candidate labels using the source's stored USD TVL. Final labels are
unset pending valuation review. A historical entity can preserve a stale USD
estimate; a correctly timed block does not establish fresh or reliable pricing.
Token balances are retained alongside TVL for review. The verified-zero day-8
policy remains open; it did not block a candidate in this sample.

## What This Means for the Study

The larger sample supplies both candidate classes, unlike the first 20 pools.
However, 13 positive candidates across four periods are insufficient evidence
for confident evaluation and calibration. July has no positive candidates;
chronological split choices must be justified, not tuned to produce better
scores. First-day trajectories remain sparse, so volatility and slope features
cannot be fabricated for quiet pools.

**Twelve of the thirteen deterioration candidates had fewer than ten first-day
swaps, including three with none.** Restricting the sample to pools with at least
ten swaps would retain only one positive candidate. Do not adopt an activity
filter merely to reduce missingness. Simple event-count, volume, and activity
features may be more broadly supported than rich time-series features; their
predictive value has not yet been evaluated.

Next: audit valuation quality on a documented subset of positive and negative
candidates, review the eight 12-second timing gaps, then freeze feature and
label policies. Any additional sample expansion should use a fixed,
outcome-independent design. The main target and 1h/6h/24h cutoffs are unchanged.

## Artifacts and Reproduction

```bash
PYTHONPATH=src python3 -m defi_pulse.diagnostic --max-requests 600
PYTHONPATH=src python3 -m defi_pulse.diagnostic --max-requests 600 --offline
python3 -m unittest discover -s tests -v
```

All generated data are ignored by Git under `data/diagnostic_200/`:

- `activity_summary.csv`: one pool per row; exact swap and distinct swap-
  transaction counts, volumes, active hours, hourly coverage, completion status.
- `pool_hours.csv`: 4,800 unique pool-hour rows and raw hourly measurements.
- `pools.json`, `cohort_manifest.json`, `candidates_*.json`, `exclusions.json`:
  frozen sample and selection evidence.
- `swaps/<pool>.json`: raw selected swap fields and history completion status.
- `historical_states/states.csv`: TVL, token balances, requested/actual times,
  block references, and quality flags.
- `historical_states/label_candidates.csv`: provisional outcomes and blockers.
- `manifest.live.json` and `manifest.json`: executed live and latest replay
  evidence, queries, source identity, request counts, and artifact hashes.

Source deployment: `QmTZ8ejXJxRo7vDBS4uwqBeGoxLSWbhaA7oXa1RvxunLy7`.
The live batch used **280 network attempts**, reusing the one separately
executed schema query from cache: **281 requests total for this diagnostic**.
The batch took 135.803 seconds. Cached response files total 3,148,146 bytes;
this is stored response size, not total wire transfer.

Offline replay used **zero network requests and 281 cache hits**. Cohort,
activity, hourly, and historical-state artifact hashes match the live run.
Checks confirm 200 unique pools/tokens and 4,800 unique pool-hour keys.
Twenty-one semantic tests passed. No test accuracy or model performance is
claimed. Account dashboard consumption remains separately unverified.
