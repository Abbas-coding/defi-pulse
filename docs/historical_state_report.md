# Historical TVL Follow-up — 2026-11-09

> **Historical evidence:** this report describes the experiment run before the 2026-11-10 modeling update. Any classification labels/counts refer to the former **80% decline** target. They have not been recomputed for the approved **30%** target or regression task. See [the current specification](modeling_update.md).

Historical pool-state queries retrieved all 40 requested TVL values for the
existing 20-pool cohort. This resolves the absence of hourly records as a
retrieval blocker for these endpoints. Stored USD valuations still need quality
review, and the cohort does not contain both candidate outcome classes.

## Method and Evidence

The Graph supports querying entity state at a specified historical block
([official API documentation](https://thegraph.com/docs/en/subgraphs/querying/graphql-api/)).
The selected deployment returned null historical `_meta.block.timestamp` and
hash fields, so they could not locate or independently verify cutoff times.

Instead, retrieve the latest indexed Uniswap transaction at or before each
cutoff, plus the earliest transaction after it, at the pilot's pinned source
snapshot. Each transaction exposes its timestamp and block number. Reject
missing or improperly ordered anchors. Query the pool at the earlier block and
verify its address, returned block, deployment, and indexing-error flag.

For **all 40 endpoints in this cohort**, the earlier transaction timestamp
equals the requested cutoff exactly. Therefore there is no cutoff-to-block time
gap in these results. A future lookup may return an older block; the tool marks
that explicitly and does not silently accept it as an exact endpoint. Reading
the pool at the end of that block matches the chosen block-timestamp convention.

Source deployment remains `QmTZ8ejXJxRo7vDBS4uwqBeGoxLSWbhaA7oXa1RvxunLy7`,
with discovery snapshot block `26378389`. No RPC provider, new data vendor,
full-block download, or paid service was used.

## Before and After

| Measurement | Initial hourly-only probe | Historical pool-state follow-up |
|---|---:|---:|
| Hour-24 candidate TVL retrieved | 20/20, potentially stale | 20/20 at the cutoff timestamp |
| Day-8 candidate TVL retrieved | 2/20 | 20/20 at the cutoff timestamp |
| Zero hour-24 values | 3 | 1 |

For pool `0x016bc8f988a267a19e3440b15007f0de97d6a5f6`, the original
hour-24 proxy was an old hourly record with TVL USD 15.633799. The actual indexed
pool state at the hour-24 cutoff is USD 9.833502; day-8 state is USD 9.057378.
An old hourly value should not be substituted automatically for cutoff TVL.

## Candidate Outcomes and Remaining Limits

Nineteen pools have finite, positive TVL at both endpoints. None meets the
primary 80% decline criterion in the retrieved stored USD values. One pool has
zero TVL at hour 24 and is ineligible for the relative-decline target. No
zero-day-8 policy was needed to classify these particular candidates.

These are **candidate outcomes**. Final labels remain unset pending USD pricing
quality review. Historical `totalValueLockedUSD` is the indexer's stored derived
valuation; its existence at a block does not prove the dollar value was freshly
recalculated at that time. The export preserves token balances to support that
review. An unchanged state is not itself evidence of corruption or fresh pricing.

The cohort cannot support training a binary classifier because it currently
contains no positive candidate examples. The fixed target also deliberately
does not label losses that happened before hour 24 as later deterioration. Do
not move the target baseline or select known positive pools to improve balance.

This follow-up does not improve the first-day price trajectory or hourly
coverage. It improves endpoint retrieval. Next, validate valuation semantics
and define outcome-independent eligibility before a reviewed, broader-date
sample. Full M1 acceptance and model-training readiness are not claimed.

## Reproduction and Requests

```bash
PYTHONPATH=src python3 -m defi_pulse.historical_states --max-requests 20
PYTHONPATH=src python3 -m defi_pulse.historical_states --max-requests 20 --offline
python3 -m unittest discover -s tests -v
```

Outputs: `data/pilot/historical_states/states.csv` and `label_candidates.csv`,
JSON equivalents, raw response cache, exact queries, variables, and hashes.
The original cohort and hourly exports are preserved.

- Three preliminary successful requests tested metadata timestamps, transaction
  anchors, and one historical pool. The null metadata timestamps were a valid
  response and are retained in `probe.json`.
- The 20-pool batch used 16 successful Graph requests: eight anchor batches and
  eight pool-state batches. Total for this follow-up: **19 network requests**.
- Offline replay: **0 network requests, 16 cache hits**; data hashes match.
- Seventeen semantic tests passed, including future-time rejection, missing
  anchors, exact threshold arithmetic, and invalid/zero TVL handling.
- Account dashboard billing/allowance remains separately unverified.

`manifest.live.json` records the batch live run; `manifest.json` records the
latest replay. This report extends, rather than replaces, the earlier
[feasibility findings](feasibility_report.md).
