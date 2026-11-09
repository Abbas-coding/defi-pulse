# Data-Source Feasibility Checklist

## Current Status

Partially executed on 2026-11-09: 20 canonical pools, 43 live network attempts, cached replay verified. See [the source-probe report](feasibility_report.md). Reliable endpoint reconstruction and final labels remain unresolved, so the full pilot gate is not passed.

## Preparation

- [x] Establish instructor approval status before formal implementation (user confirmed 2026-11-09).
- [x] Verify the selected deployment and account access without publishing credentials (bounded authenticated pilot).
- [x] Inspect live schema and entity/filter types; preserve a schema fingerprint for the fields used by the probe.
- [ ] Confirm free usage conditions and select a conservative request cap.
- [ ] Freeze pilot dates, maturity buffer, selection settings, and query versions.

## Pilot Evidence

- [ ] Discover 20–30 historical pool candidates reproducibly, without choosing by outcome.
- [ ] Check WETH orientation and canonical-pool selection across fee tiers.
- [ ] Preserve raw responses and normalization provenance.
- [ ] Inspect bucket boundaries and available history at all three cutoffs.
- [ ] Demonstrate trustworthy hour-24/day-8 state reconstruction with observation timestamps.
- [ ] Investigate absent buckets, inactive pools, stale states, and unreliable valuations.
- [ ] Measure event-query or historical-state feasibility where hourly data are insufficient.
- [ ] Test cache reuse, budget enforcement, pagination, and error handling.

## Required Report

Create `docs/feasibility_report.md` after executing the pilot. Include:

| Evidence | Required reporting |
|---|---|
| Source | Deployment, schema fingerprint, retrieval date, verified fields and limitations |
| Selection | Candidate range, selection algorithm, counts and rejection reasons |
| Timing | Requested cutoffs, bucket coverage, actual endpoint times and staleness |
| Completeness | Usable observations and labels per pool and per window |
| Outcome | Positive/negative/unlabeled counts; no performance claims from this small pilot |
| Cost | Network attempts including retries, cache hits, bytes, duration, disk usage |
| Failures | Representative missing/invalid records and reproducible diagnostics |
| Reproduction | Configuration, commands, manifest references, relevant test results |

## Decision Gate

Proceed only if a documented subset supports defensible early histories and labels within the verified free budget. Present actual usable counts and losses rather than inventing a numerical acceptance threshold in advance of source evidence.

If the core measurements are unavailable, do not scale extraction or train against fabricated endpoints. Report the blocker and propose the smallest justified change for user review. A successful pilot establishes extraction feasibility, not model usefulness or full-population representativeness.
