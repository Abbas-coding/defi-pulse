# Source Evidence — Initial Pilot

Authenticated queries succeeded on 2026-11-09. This evidence concerns the
selected deployment and bounded queries, not all possible historical records.

| Item | Verified value |
|---|---|
| Gateway | `https://gateway.thegraph.com/api/subgraphs/id/<subgraph-id>` |
| Subgraph ID | `5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV` |
| Deployment | `QmTZ8ejXJxRo7vDBS4uwqBeGoxLSWbhaA7oXa1RvxunLy7` |
| Pilot block | `26378389` |
| Authentication | Bearer header from local `GRAPH_API_KEY`; never persisted |
| Schema/probe fingerprint | `131ad3df186396d91b49b9d3bb059f1be23a81dc7d601f578de58afcaeb99473` |
| Address filter scalar | `String`, verified by introspection and successful discovery |

The live probe checks Pool, Token, and PoolHourData fields and root arguments.
`Pool_filter` includes token0/token1 and creation timestamp bounds. Discovery
uses creation `BigInt` bounds and canonical Ethereum WETH on either side.
Canonical lookups omit creation bounds so older pools outside the sample range
can disqualify a candidate. All pool data queries use the frozen block.

Pool metadata fetched: `id`, `createdAtTimestamp`, `feeTier`, snapshot
`totalValueLockedUSD`, and token0/token1 `id`, `symbol`, `decimals`. The snapshot
TVL is retained as metadata; it does not enter early features or eligibility.
Creation block numbers are not yet collected.

Hourly fields fetched: `id`, `periodStartUnix`, `tvlUSD`, `volumeUSD`, `txCount`,
`open`, `high`, `low`, `close`, `token0Price`, `token1Price`, `liquidity`.
Hourly filtering uses integer `periodStartUnix_gte`/`periodStartUnix_lt` bounds
and pool address; ordering is by bucket start. At most 25 buckets can fall in
each requested range, below the request's `first: 26` bound. No historical
hourly pagination is needed for these particular bounded ranges.

Do not equate source `txCount` with swap count without mapping verification.
Preserve raw prices and liquidity units; target-token price normalization and
USD valuation accounting are future work. No exact update timestamp is exposed
in the fetched hourly fields.

Separately, a schema query verified Swap `id`/`timestamp` and pool/timestamp
filters. A bounded `swaps(first: 1)` query for WBTC/WETH during November 8
15:00–16:00 UTC returned an empty list at original demo block `26378164`, with
the same deployment and no reported indexing errors. The user subsequently
approved using valid hourly absence as assumed no trading without checking
every absent hour against swaps.

Follow-up: `transactions` filtering by `timestamp_lte` and `timestamp_gt`, with timestamp ordering and `blockNumber`, succeeded. Historical `pool(id:, block:)` returned TVL and token balances for all 40 endpoints. Historical `_meta` timestamps/hash were null; indexed transaction timestamps supplied verified exact-cutoff blocks for this cohort. See [the follow-up report](historical_state_report.md).

Initial probe limitations: discovery is deliberately capped, archive state at exact cutoff
blocks has not been verified, missing entities do not establish complete event
coverage, and account quota is not exposed by these subgraph data queries.
See [the measured source-probe report](feasibility_report.md).
