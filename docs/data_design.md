# Data Acquisition and Dataset Design

## Source and Granularity

The planned primary source is a verified Ethereum Uniswap v3 subgraph through The Graph. Request selected pool metadata, early hourly aggregates, and reliable outcome states. Timestamped Swap/Mint/Burn records are optional when justified by temporal alignment or a research hypothesis.

The plan does not collect every transaction involving a pool address. Source access, entity names, field semantics, historical-state support, pagination, and free quota remain unverified. Do not encode a guessed endpoint or quota.

## Reproducible Sampling

1. Freeze a historical candidate date range and collection cutoff with an indexing buffer.
2. Discover pools having canonical Ethereum WETH on either token side; verify the address before use.
3. Identify the target token by address, normalize case, and sort by creation timestamp then pool address.
4. Verify the earliest canonical pool policy, including older pools outside the candidate date range. The exact lookup method is unresolved.
5. Apply documented pricing, activity, coverage, and initial-TVL eligibility rules without selecting for favorable future outcomes.
6. Require elapsed outcome maturity through creation plus eight days and the indexing buffer.
7. Record exclusions and counts at every stage. Do not substitute later fee-tier pools merely because their future data look better.

Choose dates and thresholds from feasibility evidence before full extraction. Report the bias introduced when 24h eligibility filters select the cohort used for 1h predictions.

## Measurements and Timing

Collect identity, creation timestamp/block, fee tier, token addresses/decimals, hourly TVL, volume, counts, and relevant price fields if verified in the schema. Treat string-encoded numeric fields carefully; preserve precision for label comparisons. Normalize price orientation and label units explicitly.

Use UTC and creation-relative cutoffs. A creation time of 10:37 implies a 1h cutoff of 11:37. The full 11:00–12:00 aggregate is not admissible. Initially use buckets ending at or before the cutoff; permit the creation bucket only under verified no-precreation-activity semantics. Measure coverage loss. Exact timestamped events or historical state may improve alignment if feasible.

Outcome states need both their requested as-of time and actual observation time. Daily buckets are not automatically exact day-8 observations. Define a justified staleness tolerance before labeling. Under the user-approved `empty_hour_assumed_no_trades_v1` policy, absent hourly records from successful, structurally valid API responses are assumed to indicate no trading. Preserve the absence as `quality = missing` with a separate `assumed_no_trades` flag. This is an assumption, not proof of complete source coverage. Do not zero-fill TVL, price, or liquidity, or interpret API errors/null collections as inactivity. Never backfill early histories with later observations.

## Table Contracts

| Table | Grain / key | Required content |
|---|---|---|
| `pools` | One selected pool, network-qualified address | Token identities, creation, fee, cohort, source, eligibility |
| `pool_hours` | Pool and UTC bucket start | Metrics, units, source ID, bucket bounds, quality flag |
| `outcome_states` | Pool and requested as-of time | TVL, observed time, age, source ID, quality |
| `labels` | One pool | Hour-24/day-8 values, ratio, nullable `y_class` (30% decline), nullable `y_reg` (percentage change), both definition versions |
| `features_1h/6h/24h` | One eligible pool per window | Cutoff, coverage, permitted features |
| `model_scores` | Pool, window, model version | Task identity, class score/decision or regression percentage-change prediction, split, model/target versions, quality and calibration/transform status |

Store outcome labels separately from feature matrices. Pool/token identifiers support joins and grouping, not default predictive inputs.

## Planned Tableau Extracts

Preserve existing ETL and feature contracts. Add versioned cleaned Parquet/CSV prediction extracts keyed by pool, window, task, model version, and shared split. Include `y_class`, `y_reg`, class score/probability and decision, `predicted_tvl_change_pct`, endpoint quality, and definition versions. Observed outcomes are display/evaluation fields, never inference inputs. Export separate global feature-level mean absolute SHAP summaries and local pool-feature signed SHAP contributions with base value and output scale; avoid ambiguous joins that duplicate prediction rows. Details: [approved contracts](modeling_update.md#tableau-export-contracts).

## Extraction and Provenance

Use parameterized GraphQL, bounded server-side filters, deterministic pagination, duplicate checks, and a cache keyed by deployment/query/variables. Count actual network attempts, including retries, against the request budget. Cache hits do not consume that budget.

Manifests record source/deployment and schema fingerprint, query/config versions, retrieval time, candidate range, cutoffs, request/error counts, cache hits, bytes, durations, and artifact hashes. Retain small public-data fixtures for tests and exclude credentials and large generated datasets from Git.
