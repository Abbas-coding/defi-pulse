# The Graph: Ten-Pool Learning Demo

## Scope

This is a separate educational demo, authorized before the formal research build. It selects up to ten Ethereum Uniswap v3 WETH pools and retrieves one completed UTC clock-hour aggregate for each. It trains no model, constructs no label, and does not establish research feasibility. Unlike the main project's sampling policy, these can be established pools and can share a target token.

One hour here means a shared calendar interval such as 12:00–13:00 UTC, not each pool's first hour. One aggregate summarizes that interval; it does not contain a minute-by-minute path or all transactions. Missing hourly entities stay missing, including when fewer than ten pools have observations. We do not replace inactive examples to make completeness look better.

## Prerequisites

- Python 3.11+ (local implementation tested with Python 3.12); no third-party package installation.
- Internet access for the first live extraction.
- A [Subgraph Studio](https://thegraph.com/studio/) account and query API key: API Keys → Create API Key.
- Access to the selected subgraph under your free account conditions. The Graph currently documents 100,000 free queries per month; check your account's remaining allowance. This script cannot inspect account billing and its local request cap is not a billing guarantee.

No Ethereum node, RPC key, contract deployment, or blockchain transaction is involved. If Studio requires an account authentication step, complete it yourself; the script only needs the resulting query key. Do not enable a paid plan for this demo.

## Configure Locally

From the repository root:

```bash
cp .env.example .env
```

Edit `.env` locally and set `GRAPH_API_KEY`. Do not paste the key into chat or commit it. `.env` and generated data are ignored by Git. Environment variables override the literal values in `.env`; shell expansion inside the file is not supported.

`GRAPH_SUBGRAPH_ID` defaults to `5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV`, the public v3 Mainnet example listed by Uniswap. This is a documentation-verified candidate, not a claim of successful live access. Uniswap cautions that its listed public deployments may not be actively maintained. The first authenticated run probes the actual schema and rejects unsupported fields or reported indexing errors.

## Run and Replay

```bash
# Defaults to the same UTC hour yesterday; up to ten pools, ten network attempts maximum.
python3 -m demos.graph_demo

# Pin a completed historical UTC hour for repeatable examples.
python3 -m demos.graph_demo --hour 2026-11-01T12:00:00Z

# Replay that exact request set with network access disabled, even without a key.
python3 -m demos.graph_demo --hour 2026-11-01T12:00:00Z --offline

# Deliberately replace the cached source snapshot.
python3 -m demos.graph_demo --hour 2026-11-01T12:00:00Z --refresh

# Offline tests using synthetic source fixtures.
python3 -m unittest discover -s tests -v
```

Use an hour that has already elapsed when you run the script. Default-hour selection changes with the clock; use the hour recorded in the manifest for exact replay. A historical run is queried at a frozen indexed block, not necessarily at the end of the historical hour.

## How the Pipeline Works

1. Send a metadata and schema introspection query. Check required entities, filters, address scalar, and root arguments; preserve the indexed block and deployment.
2. Query up to ten pools on each WETH side, ranked by snapshot TVL. Deduplicate and take the highest-TVL ten that existed before the selected hour. This favors readable active examples but is not unbiased research sampling or a guarantee of activity during that hour.
3. Request the selected hour for each pool in one GraphQL operation using aliases. Freeze discovery and hourly queries to the indexed block from step 1.
4. Cache each successful response under a SHA-256 fingerprint of subgraph ID, query, and variables. Reject partial GraphQL errors. Repeated requests reuse the stored snapshot until explicitly refreshed.
5. Preserve raw data and export one CSV row per selected pool, with explicit observation quality.

Normally there are three HTTP requests on the first run, potentially more attempts with retries, and zero requests for an exact cached replay. Aliases batch multiple entity selections into one request; actual account usage remains subject to gateway rules. The default cap is ten network attempts including retries. Requests have 30-second timeouts and at most three attempts per query, with backoff for network failures, HTTP 429, and server errors. GraphQL errors stop visibly rather than being retried indefinitely.

## Outputs

All generated outputs live under `data/demo/` by default:

| Artifact | What to inspect |
|---|---|
| `cache/*.json` | Successful raw GraphQL response data, keyed by request fingerprint |
| `schema.json` | Live introspection result and source metadata |
| `pools.json` | Selected addresses, token identities/decimals, creation, fee tier, snapshot TVL |
| `hours.json` | Hourly records exactly as selected from the API |
| `pool_hours.csv` | Pool/token identity, UTC interval, quality, and raw metric columns |
| `manifest.json` | Exact queries/variables, source deployment/block, time, cache references, request counts, bytes and caveats |

Numeric API values such as `tvlUSD` are often strings; exports retain that precision. `volumeUSD` is an interval flow; `tvlUSD` and `liquidity` are state values updated within the bucket, not interval sums. In-range liquidity is not USD TVL. `open/high/low/close` remain raw pool price fields: they are not normalized target-token USD prices. An hourly entity does not imply an exact measurement at the end of the hour. Pool-level `totalValueLockedUSD` is used only for convenience ranking at the pinned snapshot, not as the selected hour's historical TVL. These meanings must be checked against the selected deployment before research use.

The output folder holds the latest export, while cache entries preserve successful earlier requests. Use a different `--output` directory to retain separate complete demo runs. Cache hits preserve source snapshots; `retrieved_or_replayed_at_utc` is the current run time, not proof of a fresh fetch.

## Status and Troubleshooting

An authenticated demo run succeeded for 2026-11-01 12:00–13:00 UTC: ten selected WETH pools, ten observed hourly buckets, three network attempts. Outputs are in `data/demo/`. This convenience sample does not establish research-cohort completeness. Authentication failures require checking the key/account/subgraph permissions; schema failures require inspecting the actual deployment rather than guessing fields. Missing buckets remain missing. An offline cache miss means that request has not been successfully cached with the same settings.

## Sources Checked During Setup

- [The Graph: query setup and free plan](https://thegraph.com/docs/en/subgraphs/querying/introduction/)
- [The Graph: API key management and bearer authentication](https://thegraph.com/docs/en/subgraphs/providers/subgraph-studio/managing-api-keys/)
- [Uniswap: public subgraph endpoints and maintenance caveat](https://developers.uniswap.org/docs/ecosystem/subgraphs/overview)
- [Uniswap: v3 entity definitions](https://developers.uniswap.org/docs/ecosystem/subgraphs/concepts/v3/entities)

### HTTP 403 and Cloudflare 1010

A reproduced 403 contained `error code: 1010`. The default Python urllib client signature was rejected; adding the descriptive `DeFiPulse-LearningDemo/0.1` User-Agent returned valid metadata with the same key. The demo now includes this header and `Accept: application/json` by default. See [Cloudflare's explanation](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/).

Other 401/403 responses can still indicate access restrictions. The key owner can check Studio → API Keys → the key → Security for allowed domains and subgraphs, plus account usage and key status. The key's display name is only a label; it does not select Uniswap automatically. Never print the key or the complete upstream error body while diagnosing failures.
