# Initial Research Source Probe — 2026-11-09

> **Historical evidence:** this report describes the experiment run before the 2026-11-10 modeling update. Any classification labels/counts refer to the former **80% decline** target. They have not been recomputed for the approved **30%** target or regression task. See [the current specification](modeling_update.md).

## Follow-up

The [historical-state check](historical_state_report.md) subsequently retrieved all 40 endpoint states. The hourly-only findings below describe the initial probe. Historical lookup improves endpoint coverage but does not establish pricing reliability or provide positive outcome examples.

## Decision

Do not scale or train yet. The bounded 20-pool extraction succeeded, but the
current hourly-only approach does not establish reliable hour-24/day-8 labels.
This is partial feasibility evidence, not completion of the full M1 milestone.

Instructor approval was confirmed by the user before this extraction. The
user-approved absence policy is `empty_hour_assumed_no_trades_v1`: a valid absent
hour is assumed to contain no trading, while TVL and price remain unknown.

## Reproducible Selection

- Creation interval: October 1, 2026 00:00 UTC inclusive through October 8 exclusive.
- Frozen indexed block: `26378389`; no indexing errors reported.
- Deployment: `QmTZ8ejXJxRo7vDBS4uwqBeGoxLSWbhaA7oXa1RvxunLy7`.
- Discovery returned 126 distinct candidates, bounded to 100 per WETH orientation.
  One side reached that cap; this is not exhaustive discovery of the interval.
- Process candidates in pool-address order. Independently query each token's
  earliest WETH pool across both orientations and all dates, then select up to
  20 unique target tokens. Exclude ambiguous earliest-time ties for review.
- Selected 20 pools; one examined candidate was excluded because an earlier
  WETH pool existed. Remaining candidates were not examined after reaching 20.
- No future-outcome, snapshot-TVL, or activity threshold selected this cohort.
  These pools are a bounded convenience sample, not a population estimate.

## Observations

| Window | Permitted clock-hour buckets | Observed | Absent / assumed no trades |
|---|---:|---:|---:|
| 1h | 20 | 20 | 0 |
| 6h | 120 | 34 | 86 |
| 24h | 480 | 46 | 434 |

Windows overlap: do not sum these rows as independent observations. Every pool
has at least one observed bucket in each window. This does not establish rich
temporal coverage: a creation bucket may be only a partial elapsed hour, and
the final partial bucket is excluded to prevent post-cutoff leakage.

Observed early TVL ranges from USD 0 to approximately USD 5,204.92. This cohort
is much smaller in TVL than the earlier top-TVL educational sample. Do not
replace pools merely to make coverage or later model results look better.

## Outcomes and Blockers

The collector retains the latest completed hourly bucket in the first day as
an hour-24 candidate, and searches a 24-hour interval preceding day 8 for a
completed candidate. A candidate is evidence to inspect, not an exact endpoint.

- Hour-24 candidate: 20/20 pools; three candidate TVL values are zero.
- Day-8 candidate: 2/20 pools.
- Both candidates present: 2/20 pools.
- Final valid labels: **0**. Positive/negative prevalence is not established.

The hourly entity does not expose the precise time of its last state update.
The export records bucket bounds and a conservative upper bound on state age,
not an invented observation timestamp. Some hour-24 candidates are nearly a
day old. No staleness threshold or automatic carry-forward has been adopted.

For example, pool `0x016bc8f988a267a19e3440b15007f0de97d6a5f6` has an
hour-24 cutoff at October 6 22:07:35 UTC, but its latest completed early record
is the 08:00–09:00 bucket. Its requested day-8 lookback has no hourly record.
Pool `0x01d8b358a3f5fc053bad2f5f2684bc440c0492a6` has an hour-24 candidate
whose conservative state-age bound is 88,919 seconds. Neither is a trustworthy
exact-cutoff label simply because the API query succeeded.

Assumed no trades cannot reconstruct USD valuation or establish that no
liquidity events occurred. Zero hour-24 denominators are unusable for the
relative target. The separate verified-zero day-8 policy remains unresolved.

## Requests, Storage, and Replay

- Live run: 43 successful network attempts; no cache hits; 18.076 seconds.
- Budget: 80 attempts, including retries. Collection stopped after 20 pools.
- Request breakdown: one schema probe, one discovery, 21 canonical lookups,
  and 20 batched early/day-8 history requests.
- Cached response files: 194,149 bytes. This measures stored response data,
  not total on-wire transfer including headers or compression.
- Initial evidence exports plus the copied live manifest: approximately 382 KB,
  excluding cache. Both exports and raw cached responses are ignored by Git.
- Exact offline replay: **0 network attempts, 43 cache hits**, same data hashes.
- Semantic verification: 14 standard-library tests passed.

Account dashboard consumption has not been reconciled. The earlier swap-check
dashboard stayed at six despite two successful requests; do not subtract this
pilot's local request count from an assumed allowance and call it verified.

```bash
PYTHONPATH=src python3 -m defi_pulse.pilot --pools 20 --max-requests 80
PYTHONPATH=src python3 -m defi_pulse.pilot --pools 20 --max-requests 80 --offline
python3 -m unittest discover -s tests -v
```

`data/pilot/manifest.live.json` preserves the executed live run. The latest
`manifest.json` records the offline verification. Queries, variables, schema
fingerprint, exclusions, and artifact hashes are recorded in those manifests.
Raw responses remain under `cache/`; normalized outputs are `pool_hours.csv`
and `outcome_states.csv`. Parquet, full pagination, event-based reconstruction,
and a production feature/label pipeline are not implemented yet.

## Next Milestone Work

Investigate exact historical pool state at cutoff blocks, including a reliable
timestamp-to-block source and the selected deployment's archive support. Compare
it against these same cached cases before increasing sample size. If exact state
is unavailable, present evidence for a documented as-of/staleness alternative.
Resolve zero day-8 handling before constructing final labels. Keep the original
target and do not train against missing or fabricated outcomes.
