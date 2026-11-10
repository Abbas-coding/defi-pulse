# Three-Day Activity Comparison — 2026-11-09

> **Historical evidence:** this report describes the experiment run before the 2026-11-10 modeling update. Any classification labels/counts refer to the former **80% decline** target. They have not been recomputed for the approved **30%** target or regression task. See [the current specification](modeling_update.md).

Extending observation to three days did not resolve sparse trading for most
pools in this fixed cohort. Of 200 pools, the same 32 reached ten cumulative
swaps at 24h and 72h. Most pools traded less on subsequent days; a few busy
pools dominate the totals. This is a descriptive diagnostic, not evidence of
model performance or a change to the approved prediction task.

## Methods

The user approved this comparison after reviewing the 200-pool results. Reuse
the same pool addresses and source snapshot, and compare three separate elapsed
intervals: day 1 `[creation, +24h)`, day 2 `[+24h, +48h)`, day 3 `[+48h, +72h)`.
Day 1 comes from the preserved raw swaps; only days 2 and 3 are newly queried.

Source deployment: `QmTZ8ejXJxRo7vDBS4uwqBeGoxLSWbhaA7oXa1RvxunLy7`.
Pinned block: `26378658`. The frozen cohort hash is
`6189d74e033218bcd7233af4822a70a91aeb2e906da2a711171790acfb6d01fc`.
Pool/day ranges use server-side pool and timestamp filters, ID cursor
pagination, a 1,000-event page size, and a 50-page per-pool/day cap. All 600
pool-day histories completed; no exact count below is a truncated lower bound.
Day-3 pagination retrieved 2,213 swaps for the busiest pool across three pages.

No pools were added, removed, or replaced. All day-1 raw files are hashed in the
new manifest. The original cohort, activity, hourly, and outcome files remain
unchanged. Trades exactly at a daily cutoff belong to the following day.

## Results

| Measurement | Day 1 | Day 2 | Day 3 |
|---|---:|---:|---:|
| Swaps across all pools | 3,041 | 1,023 | 2,547 |
| Source-reported USD trading volume | $633,141.77 | $226,878.75 | $578,486.57 |
| Pools with zero swaps | 19 | 177 | 180 |
| Pools with 1–9 swaps | 149 | 21 | 18 |
| Pools with at least 10 swaps | 32 | 2 | 2 |
| Median swaps per pool | 2 | 0 | 0 |
| Total active pool-hours | 321 | 73 | 76 |

An active hour is an elapsed hour containing at least one indexed swap, counted
separately per pool. USD totals are source valuations pending pricing review;
they are not independently verified dollar flows. Swap counts and volume are
different measures and are compared separately in the output.

For the same individual pools:

- Three had more swaps on day 2 than day 1; four had higher USD volume.
- Twelve had more swaps on day 3 than day 2; sixteen had higher USD volume.
- Two had more swaps on day 3 than day 1; four had higher USD volume.
- Of 19 pools with no day-1 trades, one first traded on day 2 (four swaps),
  none first traded on day 3, and 18 stayed inactive throughout all three days.
- Twelve pools traded on all three days.
- No pool below ten swaps on day 1 subsequently reached ten in either single
  later day. None crossed ten cumulatively by 72h either: 32 pools meet that
  threshold at both 24h and 72h; 168 remain below it.

The ten-swap threshold is an exploratory description, not a validated training
eligibility rule. Counting cumulative events alone would hide the lack of
broader activity: total swaps rise to 6,611 over three days, while the median
pool has no new trading on days 2 and 3.

## Concentration and Interpretation

Pool `0xc840bbd01f03121d47711728c010d5f371e69251` has 922, 512, and 2,213
swaps on days 1, 2, and 3 respectively. It alone supplies approximately 86.9%
of all day-3 swaps. The two busiest day-3 pools supply 2,514 of 2,547 swaps.
Thus the rebound in total activity on day 3 does not describe most pools.

These results do not support extending the model's window solely to obtain
more activity across this cohort. They also do not prove that first-day
features can or cannot predict the target. Simple inactivity/count features
may be valid observations; rich price trajectories remain unsupported for
many pools. The earlier 13 positive candidate outcomes remain subject to
valuation review, and the extra days do not increase the number of independent
pool examples.

Keep the approved 1h/6h/24h experiment while reviewing source USD pricing and
the supported feature set. A 48h/72h model would observe part of the current
hour-24-to-day-8 outcome period, so it needs a separately agreed experiment
definition. This diagnostic did not authorize or implement that change.

## Artifacts and Validation

```bash
PYTHONPATH=src python3 -m defi_pulse.three_day_activity --max-requests 200
PYTHONPATH=src python3 -m defi_pulse.three_day_activity --max-requests 200 --offline
python3 -m unittest discover -s tests -v
```

Generated outputs under `data/diagnostic_200/three_day_activity/`:

- `daily_activity.csv`: 600 unique pool/day rows, separate intervals, swap
  counts, distinct swap transaction counts, USD volume, and active hours.
- `pool_comparison.csv`: 200 rows comparing individual days, delayed starts,
  daily increases, and separately named cumulative totals.
- JSON equivalents and `summary.json`: exact source-derived values and totals.
- `swaps/day2/`, `swaps/day3/`: preserved event lists and completeness flags.
- `cache/`, `manifest.live.json`, `manifest.json`: cached responses, exact
  queries, source identity, input/output hashes, and live/replay request counts.

The live run used **83 network attempts** under a 200-attempt cap. Day 1 used
no new requests. Offline replay uses **0 network attempts and 83 cache hits**
and reproduces the artifact hashes. Twenty-five semantic tests pass, including
daily boundary assignment, duplicate-page rejection, partial-history handling,
and the distinction between daily and cumulative growth. The dashboard account
usage remains unverified; local attempts are reported separately from billing.
