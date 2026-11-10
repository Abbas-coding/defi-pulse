# DeFi Pulse — Master Project Context & Implementation Specification for Codex

> **Subsequent implementation, 2026-11-10:** the [baseline pipeline](docs/baselines.md) now builds separate versioned candidate targets and activity features, applies the shared embargoed splits, and runs fixed experimental classification/regression baselines. Source pricing remains unverified; final labels, tree models, SHAP, and named DS statistical tests remain pending. Statements below about a documentation-only update describe the earlier specification revision.

> **Current revision: 2026-11-10.** The latest user-approved modeling specification is [docs/modeling_update.md](docs/modeling_update.md): 30% classification, percentage-change regression, SHAP for both tasks, and Tableau extracts. This revision updates design intent only. Existing collectors and historical 80% outputs are preserved; modeling remains planned.

> **Repository:** `defi-pulse`  
> **Project type:** Combined undergraduate **Data Science (DS)** + **Machine Learning (ML)** research/engineering project  
> **ML project title:** **DeFi Pulse: Explainable Early Liquidity Risk Assessment in Uniswap v3**  
> **DS project title:** **DeFi Pulse: Behavioral Analysis of Early Liquidity Deterioration in Ethereum Uniswap v3 Pools**  
> **Team:** 3 students; one has prior blockchain data-engineering experience; two are learning blockchain  
> **Target duration:** approximately 6 weeks, CPU-friendly, zero mandatory spending  
> **Document status:** Project specification and Codex handoff, **not a claim that the implementation or datasets already exist**  
> **Prepared:** 2026-11-06  
> **Audience:** Codex (implementation agent), teammates, course instructors, and future research reviewers

---

## 0. START HERE, CODEX — Read Before Taking Any Action

You are assisting a three-person undergraduate team building **DeFi Pulse**. Treat this document as the project's design intent and constraints. **Do not assume an existing implementation unless you inspect the repository and find one.** The next action is to **audit the repository, prepare a short implementation plan, and complete the data-source feasibility milestone**, not to generate a polished dashboard or claim that a classifier works.

**Your first responsibilities:**

1. Inspect current repository structure, dependencies, Git state, README, tests, and any existing data; summarize what is and is not implemented.
2. Check whether the selected Ethereum **Uniswap v3 subgraph** is actually queryable through **The Graph** with the user's available, free credentials. Do not invent a live endpoint or hard-code a stale URL.
3. Inspect the live subgraph's **GraphQL schema**; confirm the exact entities, field names, filter types, pagination behavior, and relevant historical availability **before** implementing collectors.
4. Design a reproducible **20–30-pool historical pilot**. Build a small, cache-aware extraction path and produce a **feasibility report** with data completeness, query counts, and blockers.
5. Stop after the approved milestone and give the team its results, tests, known caveats, and proposed next step. Do not silently broaden the project scope.
6. Keep all code understandable to students: small modules, type hints, clear names, minimal dependencies, explanations of why steps exist, and tests for important invariants.

**Non-negotiables:**

- Do **not** download full Ethereum blocks, full chain history, or every Ethereum transaction.
- Do **not** build or deploy smart contracts, tokens, bots, a wallet product, or a paid cloud service.
- Do **not** include any information from after prediction time in the model features.
- Do **not** treat USD-TVL decline as proof of liquidity theft, fraudulent activity, or a rug pull.
- Do **not** invent model results, accuracy numbers, source completeness, dataset sizes, or live API availability.
- Do **not** confuse the **1h/6h/24h observation periods** with three single-point snapshots. Use the **history available throughout each period**.
- Do **not** feed the seven-day future outcome to the model as an input. It exists solely to construct the training/evaluation target.
- Do **not** spend money or enable billable plans on the team's behalf.
- **Faculty approval:** The course's CCA instructions require instructor approval before formal project implementation. Confirm that approval/permission is in place; permissible preparatory work can be separated from the formal graded build if needed.

### Source-of-truth priority

If documents conflict, use this order and explicitly report the discrepancy:

1. Latest **instructor requirements** and grading rubric.
2. Latest **approved ML project proposal** (especially the fixed label definition).
3. This **master implementation specification**, incorporating subsequent team decisions.
4. Earlier **DS project proposal** and terminology guide.
5. Earlier brainstorming/conversation exports.
6. Generic assumptions from frameworks, blogs, or tutorials.

Never silently rewrite an approved experiment definition. Document any proposed changes in `docs/decisions.md` and request instructor/team approval when they affect claims, labels, scope, or deliverables.

---

## 1. Executive Summary — What Are We Building?

**DeFi Pulse** is an **explainable, historical early-liquidity-risk assessment prototype** for newly created trading pools on **Uniswap v3**, a decentralized exchange (DEX) running on **Ethereum Mainnet**.

A **liquidity pool** is a smart contract containing two assets so users can exchange one for the other. Some pools maintain liquidity over time; others lose much of their **USD-denominated total value locked (TVL)**. We investigate whether early pool behavior contains signals associated with later deterioration.

For each **historically newly created ERC-20/WETH pool**, the team will:

1. Obtain its creation time, token/pair identity, and relevant hourly pool data from a **Uniswap v3 subgraph** indexed by **The Graph**.
2. Analyze its **full first 1, 6, and 24 hours of observable activity**, not merely the value at three individual timestamps.
3. Produce descriptive/statistical findings (the **Data Science** submission).
4. Train supervised classifiers for ≥30% hour-24-to-day-8 deterioration and regressors for continuous percentage change over the same endpoint interval (the **Machine Learning** submission).
5. Present a **calibrated model-estimated risk probability**, a **Low / Medium / High** band, **influential model features**, and a **plain-language explanation**.
6. Export classification/regression predictions and SHAP summaries to cleaned Parquet/CSV for Tableau historical case studies, clearly separating inputs, predictions, and observed future results; the earlier Streamlit interface is optional.

**The project is NOT:** a cryptocurrency price predictor, a rug-pull/fraud detector, an investment recommendation engine, a trading bot, or a production financial risk platform.

### Simple example (fictional)

A pool `ABC/WETH` was created on July 24, 2026. For training:

- Data from creation to **hour 1** builds the 1h feature row.
- Data from creation to **hour 6** builds the 6h feature row.
- Data from creation to **hour 24** builds the 24h feature row.
- The **hour-24 TVL** and **day-8 TVL** determine the **same future label** for all three models.
- A 30% or greater USD-TVL decrease from hour 24 to day 8 is the current **primary research definition** of a severe deterioration event.

At prediction time, each model sees **only its permitted early-period features**. The day-8 result remains hidden.

---

## 2. Finalized and Non-Finalized Decisions

### 2.1 Fixed project scope

| Area | Decision |
|---|---|
| Chain | **Ethereum Mainnet** only |
| DEX / protocol | **Uniswap v3** only |
| Market mechanism | **Concentrated-liquidity automated market maker (AMM)** |
| Pool pair | One target **ERC-20 token** paired with **WETH** (Wrapped Ether) |
| Cross-chain | **Out of scope**; no bridge tracking, cross-chain asset analysis, or second chain |
| Multiple DEX versions | **Out of scope**; exclude Uniswap v2/v4 and other DEXs |
| Main sampling unit | A **historically newly created pool**; one **canonical pool per target token** |
| Pool selection | Prefer **earliest eligible TOKEN/WETH Uniswap v3 pool per target token**; specify the eligibility algorithm precisely before selection |
| Input history | Full first **1 hour**, **6 hours**, and **24 hours** (hourly aggregates, optional selected events) |
| Target horizon | **7 days after hour 24**, evaluated at **day 8 from creation** |
| Primary outcomes | Binary **≥30% USD-TVL deterioration** and continuous **USD-TVL percentage change**, not fraud |
| ML task | Supervised **binary classification** plus continuous **TVL percentage-change regression** |
| Main models | Classification: Dummy, Logistic Regression, Random Forest Classifier, XGBoost Classifier; regression: mean/median Dummy, Linear/Ridge, Random Forest Regressor, XGBoost Regressor |
| Explainability | Global/local **SHAP** analysis of selected compatible classification and regression models |
| Risk bands | **Low / Medium / High**; boundaries chosen **using validation data only** |
| Primary data API | The Graph → Ethereum Uniswap v3 **subgraph** → GraphQL |
| Local storage | Raw JSON/JSONL cache, cleaned **Parquet**, optionally **DuckDB** |
| Compute | Local Python/Jupyter on CPU |
| Visualization | Matplotlib/Plotly; cleaned Parquet/CSV predictions and SHAP summaries for **Tableau**; earlier Streamlit demo optional |
| Pilot | **20–30** historical pools before any scale-up |
| Target corpus | Approximately **300–1,000 usable pools**, **conditional on feasibility and class balance** |
| Spending | **$0 mandatory**; use free quotas/tools; stop before any paid requirement |

**Important terminology correction:** “newly created” refers to the **pool's creation time in historical data**, not a pool necessarily created today. A newly created **pool** does not guarantee that its underlying token was deployed recently. Unless token deployment-age information is independently verified, do **not** claim the token itself is newly launched.

### 2.2 Items that require empirical verification, not guesses

The following should be settled in the **pilot** and written down:

- Exact Uniswap v3 Ethereum subgraph **deployment/ID/Graph Explorer listing**, available endpoint, auth headers, terms, and live schema.
- Whether the chosen subgraph has sufficiently complete **historical pool creation, hourly, and day-8 data**.
- How it represents **hours with no events**, and whether a reliable as-of TVL can be reconstructed.
- Whether it exposes sufficient **Mint/Burn/Swap** event history to support additional liquidity-flow features within quota.
- Pool inclusion thresholds: minimum starting TVL, minimum trading activity, sufficient observed 24h coverage, acceptable USD-pricing quality.
- Historical sample date range and reproducible cutoff (must have elapsed at least 8 days plus indexing buffer by collection time).
- Confidence in the ratio of deteriorated/non-deteriorated pools and whether the sample is large enough for calibration/SHAP conclusions.
- Exact **risk-band cutoffs** and whether probability calibration materially improves reliability.
- Choice of fixed-hour TVL reconstruction policy and tolerances.
- Actual number of API requests, bytes transferred, download duration, and raw/processed disk consumption.

Do not present any of these as measured facts until the team has evidence.

---

## 3. Blockchain Primer for New Team Members

These are the **minimum necessary concepts**. Team members do **not** need to learn the whole Ethereum Virtual Machine, run a node, decode every Ethereum transaction, or learn Solidity before extracting indexed data.

| Term | Plain-English meaning | Why it matters here |
|---|---|---|
| **Blockchain** | A publicly verifiable ledger of digital events/transactions | Underlying source of the activity |
| **Ethereum Mainnet** | The public Ethereum blockchain network | Only network analyzed |
| **ETH** | Native Ethereum asset | Native asset is **not** directly an ERC-20 token |
| **WETH** | Wrapped Ether, an ERC-20-compatible representation of ETH | Common asset in every studied pair |
| **ERC-20** | Ethereum token interface/standard | The other token in TOKEN/WETH pools |
| **Smart contract** | Program running on Ethereum | Each Uniswap pool is a smart contract |
| **Wallet/address** | On-chain identifier of an account/contract | May appear in swap/liquidity events |
| **DEX** | Decentralized exchange | Uniswap is the selected exchange |
| **AMM** | Automated market maker, pricing through pool mechanics | Basic mechanism behind Uniswap trading |
| **Pool** | Contract with two trading assets | Our unit of analysis |
| **Liquidity provider (LP)** | Participant who deposits assets into a pool | Can add/remove pool assets |
| **Liquidity/TVL** | Value of assets associated with the pool (definitions differ) | Used to study deterioration |
| **Swap** | Exchange of one pool token for the other | Source of volume/activity signals |
| **Fee tier** | Percentage fee setting for the Uniswap v3 pool | Useful categorical feature |
| **Concentrated liquidity** | LPs choose price ranges where their liquidity is active | Critical distinction between TVL and **active/in-range liquidity** |
| **Tick / sqrtPrice** | On-chain price representation and price-range system | For understanding v3 internals, not required for every model |
| **Mint / Burn** | Liquidity addition/removal events in Uniswap v3 | Optional advanced features and interpretation |
| **The Graph** | Blockchain data indexing and GraphQL querying infrastructure | Lets us request filtered indexed pool records |
| **Subgraph** | Indexed API with entities and schema for a chosen blockchain app | Specifically the Uniswap v3 Ethereum dataset |
| **GraphQL** | API query language to request selected fields | We request only relevant records, not full blocks |
| **JSON** | Structured API response format | Raw response stored and transformed locally |
| **Parquet / DuckDB** | Compact analytical storage / embedded SQL database | Reproducible research dataset |
| **Rug pull** | Fraud-like exit scheme | **Not** a claim that can be inferred solely from TVL decline |

### How everything connects

```text
Ethereum Mainnet
  └── Uniswap v3 smart contracts
        └── newly created ERC-20 / WETH pools
              ├── pool creation and fee tier
              ├── swaps (trades)
              ├── liquidity additions/removals (if available)
              └── hourly / daily pool metrics
                   │
                   ▼
         The Graph indexes selected contract data
                   │
                   ▼
             GraphQL queries
                   │
                   ▼
             Python + HTTPX
                   │
                   ▼
           JSON → Parquet/DuckDB
                   │
         ┌─────────┴──────────┐
         ▼                    ▼
    Data Science        Machine Learning
    EDA + statistics    risk classification
         └─────────┬──────────┘
                   ▼
         Explainable historical dashboard
```

**Avoid the raw-block misconception:** the team is **not** collecting all blocks, all transactions in each block, or a complete Ethereum archive. The dataset consists of **selectively queried records** about selected Uniswap v3 pools.

---

## 4. Research Questions and Academic Separation

### 4.1 Data Science (DS) project

**Full title:** *DeFi Pulse: Behavioral Analysis of Early Liquidity Deterioration in Ethereum Uniswap v3 Pools*

**Question:** Which early trading, liquidity, and price-activity patterns **are associated with** severe later USD-TVL deterioration?

**Core DS responsibilities:**

1. Source and document the public data and extraction process.
2. Define the eligible pool population, a clear sample selection policy, and dataset caveats.
3. Validate identifiers, time zones, timestamp units, token pair orientation, missing data, duplicates, outliers, and USD-valuations.
4. Construct pool-by-hour and pool-level analytical tables.
5. Engineer understandable early-period variables (trends, volatility, counts, volume, ratios).
6. Describe distributions, class prevalence, pool sizes, fee tiers, activity rates, and behavior differences.
7. Test a small number of hypotheses with appropriate methods, effect sizes, and uncertainty.
8. Investigate whether USD-TVL declines plausibly reflect price changes and/or liquidity changes; avoid causal overclaims.
9. Produce a repeatable DS notebook/report/dashboard views and a documented dataset for the ML project.

**DS demo:** raw vs cleaned data, sample-filter funnel, feature definitions, EDA graphs, hypothesis tests, data-quality checks, temporal trends, research findings, and a source-to-dataset explanation.

**DS is NOT merely:** loading a CSV and showing a correlation heatmap. The pipeline, domain-aware data checks, features, and statistical reasoning are core contributions.

### 4.2 Machine Learning (ML) project

**Full title:** *DeFi Pulse: Explainable Early Liquidity Risk Assessment in Uniswap v3*

**Question:** Can we produce **reliable, interpretable model-estimated probabilities** of severe day-8 USD-TVL deterioration using only early observations?

**Core ML responsibilities:**

1. Use DS-produced, leakage-checked features and targets.
2. Compare performance at **1h vs 6h vs 24h** information availability.
3. Establish DummyClassifier and Logistic Regression baselines.
4. Compare Random Forest and XGBoost models, with controlled tuning.
5. Evaluate on **chronologically later pools** with a proper embargo/purge around split boundaries.
6. Measure discrimination **and calibration**, not accuracy alone.
7. Map validated estimated probabilities to Low / Medium / High risk bands.
8. Use SHAP to report global and per-pool influential variables.
9. Generate template-driven natural-language explanations that reflect feature contributions **without pretending to prove causes**.
10. Build a demonstrable, honest historical prediction interface.

**ML demo:** input features available at hour 1/6/24, held-out predictions, precision-recall curve, confusion matrix, calibration chart, risk band, SHAP explanations, and actual historical outcome shown **separately** after inference.

### 4.3 Shared components, separate academic outputs

Both projects share the **same collection pipeline, cleaned dataset, sampling decisions, and feature definitions**. They are **not two unrelated applications**. The DS submission explains what behavior exists and what the data supports; the ML submission evaluates whether those observations predict future events.

---

## 5. Exact Observation Windows, Outcome Definition, and Leakage Rules

This section is especially important. Do not simplify it to “read the values at hours 1, 6, and 24.”

Let:

- `t0` = pool's creation time (UTC, Unix seconds).
- `t1 = t0 + 1 hour`.
- `t6 = t0 + 6 hours`.
- `t24 = t0 + 24 hours`.
- `t8d = t0 + 8 days` (= `t24 + 7 days`).

### 5.1 Features available at each prediction time

| Experiment | May use | Must NOT use |
|---|---|---|
| `model_1h` | Pool information and pool activity **from t0 through t1**, inclusively or with explicit `(start,end]` convention | Any measurements learned after `t1` |
| `model_6h` | From `t0` through `t6` | Measurements after `t6` |
| `model_24h` | From `t0` through `t24` | Measurements after `t24` |

**Hourly aggregation alignment:** Uniswap `PoolHourData.periodStartUnix` is a **UTC hourly bucket start**, not necessarily an hour measured from pool creation. The first 24 hours after an arbitrary creation timestamp may overlap **25 clock-hour buckets**, and boundary buckets may contain activity from **before or after** a prediction cutoff. **Do not casually include a full boundary bucket if it would leak post-cutoff activity.**

Implement an explicit, tested policy:

- **Preferred for exact window features:** use event timestamps (swaps/mints/burns) or available **as-of historical state** to respect the actual `t0 + 1h/6h/24h` cutoffs.
- **Resource-limited hourly-only alternative:** use **completed UTC clock-hour buckets ending at or before the cutoff**, exclude partially overlapping end buckets, and note coverage loss; creation-hour partial buckets are allowed only when no pre-creation activity can exist for that pool.
- Document the exact time-bucket convention in the dataset card and evaluation notebooks.
- Never pretend sparse hourly bucket coverage is a complete minute-level or transaction-level history.

**Practical initial solution:** collect full per-pool `PoolHourData` first, preserve timestamps, document bucket coverage, and calculate robust features from safe complete buckets. Add event-level precision only if feasible. For 1h observations there may be very few completed hourly buckets: that is a real limitation, not a reason to fabricate observations.

### 5.2 Common target label for all three models — preserve proposal definition

Let `TVL_24h` be the reconstructed pool **USD TVL** at hour 24 and `TVL_day8` the USD TVL as-of day 8.

Define **primary binary target**:

```python
# Pseudocode: only after validating nonmissing, positive, time-aligned TVL
y_class = int(
    tvl_usd_day8 <= 0.70 * tvl_usd_hour24
)
```

- `1` = severe deterioration (at least **30% fall in USD TVL**).
- `0` = no severe deterioration under this **specific endpoint definition**.
- Do not label a case if `TVL_24h` is zero/invalid or the day-8 state is untrustworthy/unavailable.
- This is an **endpoint** definition: a pool that dips severely then recovers by day 8 may be labeled `0`. State this as a limitation.
- Keep the **same target** across the 1h, 6h, and 24h model comparisons.
- Use **day-8 data only for labeling, outcome visualization, and evaluation**; it must never appear as an input feature.
- Any `hour24` value used to define the target must likewise **not be exposed as a feature to the 1h/6h models**.

**Mathematical definition:**

```text
y_class = 1 if TVL_USD(t0 + 8 days) / TVL_USD(t0 + 24 hours) <= 0.70
    0 otherwise
```

### 5.2a Continuous regression target — approved 2026-11-10

```text
y_reg = ((TVL_USD(t0 + 8 days) - TVL_USD(t0 + 24 hours)) / TVL_USD(t0 + 24 hours)) * 100
```

Use the same validated endpoints and saved chronological split as classification. Preserve missing/invalid-outcome and zero-policy safeguards. A log-ratio alternative for extreme right-skew requires explicit transform/zero handling, definition versioning, and percentage-change output after inverse transformation. Targets never enter inference features. See [the approved update](docs/modeling_update.md).

### 5.3 Why this is only a proxy for liquidity risk

Uniswap v3 `tvlUSD` is the USD value of pool-held assets. It can decline because:

- liquidity providers remove assets;
- token market prices decline;
- an asset is repriced because of an unreliable USD estimate;
- positions change relative to the active price range;
- combinations of these effects.

**Crucial:** `PoolHourData.liquidity` generally describes **in-range liquidity**, not the same thing as USD TVL. Do **not** equate changes in in-range liquidity to dollars deposited/withdrawn; do not use `Mint`/`Burn` values blindly as USD flow without proper accounting and units. When possible, analyze TVL alongside price changes and selected liquidity events. The report must explain the proxy's limitations and avoid any categorical fraud claim.

### 5.4 Suggested sensitivity/robustness checks

After the main model is working, test alternate thresholds (e.g., 50%, 70%, and the former 80% decline), alternative minimum initial TVL thresholds, and subgroup outcomes by fee tier / liquidity size. **Do not tune the final headline target retrospectively to maximize scores**; preregister the primary 30% endpoint definition and treat alternatives as robustness checks.

### 5.5 Temporal split and leakage controls

- Sort pools by `created_at_utc`.
- Train on older cohorts; validate on later cohorts; test on newest eligible cohorts.
- Retain the specified 70% / 15% / 15% split by **creation date**; use actual date ranges, not random row assignments.
- Ensure **all rows for the same pool/token** remain in the same split.
- **Purge/embargo overlapping target windows** at train/validation/test boundaries (retain the specified 8-day embargo based on the fixed label horizon), and verify that evaluation labels cannot leak across boundary-dependent features/selection. Reuse the same saved split assignments for classification and regression.
- Fit scalers, imputers, feature selectors, calibrators, risk thresholds, and hyperparameter choices using only permitted **training/validation** periods.
- The chronological **test set is never used to choose thresholds or models**.
- Capture market regime/date-range differences; avoid treating random K-fold cross-validation as the default.

---

## 6. Data Source and Exactly What We Collect

### 6.1 Primary source

**Public Ethereum Uniswap v3 data indexed by The Graph**, accessed through an explicitly selected, verified **Uniswap v3 subgraph** using GraphQL over HTTPS. The Graph is an indexing/query layer; it is not an alternative blockchain and we are not running our own Ethereum archive node.

The Graph's documentation, checked on **2026-11-06**, describes a free plan of **100,000 subgraph queries per month**. This allowance is **not** a guarantee of exact endpoint access, query speed, archive completeness, or a particular per-minute rate limit. Confirm the current rules and available subgraph before implementation.

**Required credentials:** an API key, if required by the selected query URL. Use environment variables, never Git-tracked files.

### 6.2 Core query entities (verify against the selected deployment)

Based on the published Uniswap v3 subgraph schema:

| GraphQL entity | Fields of interest | Use |
|---|---|---|
| `Pool` / `pools` | `id`, `createdAtTimestamp`, `createdAtBlockNumber`, `token0`, `token1`, `feeTier` | Identify creation time and pair |
| `Token` | `id`, `symbol`, `decimals` | Identity/normalization; address is authoritative |
| `PoolHourData` / `poolHourDatas` | `id`, `pool`, `periodStartUnix`, `tvlUSD`, `volumeUSD`, `txCount`, `open`, `high`, `low`, `close`, `token0Price`, `token1Price`, `liquidity` | **Primary early observation series** |
| `PoolDayData` / `poolDayDatas` | `date`, `tvlUSD`, `volumeUSD`, `txCount`, price fields | **Daily outcome trajectory/quality checks**, but not automatically exact t0+8d state |
| `Swap` / `swaps` | `id`, `timestamp`, `pool`, token amounts, `amountUSD`, sender/recipient if available | Optional high-resolution activity and time alignment |
| `Mint`, `Burn` | Timestamp, pool, amounts, initiator/owner (as available) | Optional context for additions/removals |

**Schema caution:** `PoolHourData.open/high/low/close` are **pool token0 price fields** in the source schema, so a `TOKEN/WETH` pool must normalize orientation explicitly when token0 is WETH. Do not casually call raw `open` “token USD price.” If converting to USD, use documented valuation assumptions and contemporaneous ETH/USD conversion.

**GraphQL data may be represented as numbers encoded as strings** (`BigInt`, `BigDecimal`). Convert carefully using Python `Decimal` where precision matters, then controlled numeric conversions for ML.

**Do not use a current Pool entity's all-time aggregate values** as if they were known at pool creation; a present-day cumulative `volumeUSD`, `txCount`, or `totalValueLockedUSD` would contaminate early features. Use time-bounded aggregates or verified historical-block state.

### 6.3 Collection scope by pool

**Minimum required:**

- Pool address, target token address, WETH address, creation timestamp and fee tier.
- Safe hourly series for **first 24 hours**, including pool TVL, volume, counts, relevant prices.
- Reliable **hour-24 TVL** and **day-8 TVL** reconstruction with timestamps/quality flags.
- Optional daily TVL series between day 1 and day 8 for case-study plots.

**Not required for MVP:** every raw swap, every tick, every LP position, every token holder, gas market information, token metadata from external APIs, every Ethereum block.

The preferred first pilot uses only the fields necessary for one credible 24h observation and an accurate day-8 target. Query extras **only when justified by a hypothesis**.

### 6.4 Finding eligible pools

A reproducible selection procedure is required. Initial candidate algorithm:

1. Query pool creation records inside a bounded, **historical** date range. Candidate pools must have **either `token0` or `token1` equal to canonical Ethereum WETH** (address verified from reliable documentation/configuration).
2. Let the other token be `target_token_address`. Exclude WETH/WETH and inappropriate known assets under **explicit, documented rules**; do not blacklist by token symbol alone.
3. Sort candidates by `createdAtTimestamp`, then by pool address for deterministic ties.
4. Select **one canonical WETH pool per target token**. To avoid retrospectively choosing only “successful” pools, prefer the **earliest WETH pool per token**, then apply transparent minimum-quality eligibility filters; do not silently switch to a later pool because its future data look better.
5. Include only pools with full elapsed outcome maturity (`created_at + 8d + buffer <= frozen_collection_cutoff`).
6. Enforce timestamp accuracy, usable USD pricing, adequate measurement coverage, and documented minimum activity/TVL filters.
7. Record **every rejection reason**. Report how many candidates were lost at each stage.

**Potential selection bias:** requiring 24h data or meaningful activity can exclude highly inactive or failed pools. Document it. If an early-window model is evaluated on a dataset preselected using later 24h activity, this is a cohort-selection limitation; avoid treating such filters as real-time preconditions available at 1h. Consider window-specific eligibility sensitivity checks.

### 6.5 Missing hourly records — do not invent data

Some hour buckets may not exist because the subgraph did not create/update an hourly entity during inactivity or because data are incomplete. A missing bucket is **not automatically `TVL=0`**, **not automatically `volume=0`**, and not automatically a technical failure.

- Preserve original timestamps and an explicit `observed`/`imputed`/`missing` quality flag.
- For event counts/volume, zero may be acceptable only if independently validated as an actual no-event interval under the source semantics.
- For stock/state variables (TVL/price), consider **as-of forward fill** only when the last trustworthy value predates the cutoff and permitted staleness is not exceeded. Never backfill from future rows into earlier features.
- Flag large gaps and investigate them before labeling.
- Prefer dropping poorly supported outcomes rather than making up `TVL_day8`.
- Distinguish **UTC clock hours** from **elapsed hours since pool creation**.

### 6.6 Pagination, rate limits, retry, and caching

- Use the subgraph's query capabilities to filter **server-side** by pool(s) and timestamps.
- Request only specified fields.
- Respect returned page-size limits (often **up to 1,000 records per collection**); use cursor/id pagination when available, not huge `skip` offsets.
- Query all pages deterministically; detect repeats/missing pages.
- Handle HTTP errors, GraphQL errors in otherwise HTTP-200 responses, authentication errors, partial results, timeouts, and transient rate limits.
- Use bounded exponential backoff with jitter for retryable failures; never infinite retry loops.
- Include a **request-count budget**, `--max-requests` and `--max-pools`/`--dry-run` options.
- Cache responses with stable query+variables+deployment fingerprints so reruns don't refetch unchanged historical data.
- Record query time, endpoint deployment ID/schema version, source range, retrieval timestamp, and cache provenance.
- Do not print API keys or write secrets into exception logs.

### 6.7 Very rough data-volume planning

For **1,000 pools**, 24 hourly buckets per pool would be ~**24,000 hourly observations**, not 1,000 × 8 days of all Ethereum blocks. Add a small set of day-8/daily records and metadata. These aggregated records are generally **small (MB-scale to tens of MB)**, depending on field count and raw-response retention. Optional **individual swap/event histories** could raise storage substantially and are unpredictable; measure before enabling.

**No firm GB estimate is a requirement.** Earlier conversation estimates were cautious upper bounds, not measured storage. The 20–30-pool pilot must report **actual** bytes before the team budgets for full extraction.

---

## 7. Suggested Local Dataset Contract

Use stable identifiers. Prefer `pool_address` and `token_address` (lowercase, network-qualified), **never token symbols as unique keys**. Use UTC timestamps and document units.

### 7.1 Tables / files

**`pools`** (1 row per selected pool)

```text
chain
protocol
pool_address                # primary key with chain/protocol
created_at_utc
created_at_unix
created_at_block_number
weth_address
target_token_address
token0_address
token1_address
token0_decimals
token1_decimals
fee_tier_raw                # actual Uniswap v3 fee-tier integer
sample_cohort
source_deployment_id
eligibility_status
rejection_reason
```

**`pool_hours`** (0+ rows per UTC hour per pool; key = pool+period_start)

```text
pool_address
period_start_unix
period_start_utc
tvl_usd
volume_usd
tx_count
open_token0_price
high_token0_price
low_token0_price
close_token0_price
token0_price
token1_price
in_range_liquidity_raw
source_record_id
observation_quality_flag
```

**`pool_daily` / `outcome_states`** (day-8 state and optional daily trajectory)

```text
pool_address
as_of_timestamp_utc
observed_timestamp_utc
source_record_id
tvl_usd
state_age_seconds
state_quality
```

**`labels`** (one row per canonical pool)

```text
pool_address
created_at_utc
tvl_usd_hour24
tvl_usd_day8
tvl_ratio_day8_over_hour24
y_class                     # 0 or 1 at the 30% threshold; nullable when invalid
y_reg                       # signed percentage change; nullable when invalid
label_quality
label_definition_version
regression_definition_version
```

**`features_1h` / `features_6h` / `features_24h`** (one row per pool **per window**, if eligible)

```text
pool_address
created_at_utc
observation_window_hours     # 1, 6 or 24
feature_cutoff_utc
feature_coverage_ratio
<features available by cutoff only>
```

**`model_scores`** (output table, never joined into feature matrix)

```text
pool_address
observation_window_hours
model_version
risk_probability_raw
risk_probability_calibrated
risk_band
predicted_binary_at_selected_threshold
actual_label                 # only in offline evaluation/historical view
split_name
```

### 7.2 Data provenance artifacts

Store:

- `data/raw/...` — exact compressed JSON/JSONL responses (may be Git-ignored when large).
- `data/interim/...` — normalized intermediate artifacts.
- `data/processed/...` — canonical feature and label Parquet.
- `data/manifests/<run-id>.json` — source deployment, query version, dates, eligibility settings, sample count, hashes, raw byte count, request count, error summary.
- `docs/dataset_card.md` — selection, units, missingness, known biases, schema, reproducibility.

Prefer saving **a small anonymization-unnecessary public-data fixture** for tests; never commit credentials. Consider public-address sensitivity in UI narratives (public ≠ automatically risk-free for reputational labeling).

---

## 8. Feature Engineering — Full History, Not Three Point-in-Time Snapshots

**Core approach:** use the history available **within each observation window** to calculate a compact **tabular feature vector**. Do not feed an entire raw time series into XGBoost without explanation or accidentally use future buckets. Keep original hourly series for DS visualizations and debugging.

### 8.1 Candidate feature families

| Family | Possible features | Preconditions |
|---|---|---|
| Initial pool context | Initial trustworthy TVL, Uniswap fee tier | Must be knowable by cutoff |
| Liquidity value | Earliest/end TVL within permitted period, percentage change, minimum/maximum observed TVL, drawdown | Validate time coverage and price effects |
| Trading activity | Total swap/transaction count, volume USD, mean volume per observed hour, number of active hours | Count source semantics; no future buckets |
| Activity shape | Volume slope, early-vs-late volume ratio, number of increasing/decreasing activity hours | Require enough completed observations |
| Price behavior | Window return, realized volatility from observed prices, intrawindow high-low range, max drawdown | Normalize pair orientation and missingness |
| Liquidity-event behavior (optional) | Mint/Burn counts, approximate changes with explicit unit semantics | Only if events available and meaningful |
| Price/liquidity interaction | TVL decline alongside token price decline, volatility conditional on volume | Interpret as association only |
| Data quality | Number of observed complete buckets, staleness, percentage missing | Useful as quality flags; investigate whether proxying label leakage |

**Do not use:** day-8 TVL, future minimum TVL, post-cutoff transactions, full-pool lifetime volume, post-cutoff token price, later pool metadata snapshots, future survival status, token future popularity, or features calculated using the entire available history independent of the window.

### 8.2 Separate features for the three windows

The same **feature names** can exist for each horizon, but their values must be computed independently from that horizon's permitted history. Keep the window-specific feature-generation function pure and unit tested.

Example conceptual calculation:

```python
def build_features(pool_history, prediction_cutoff_utc):
    """Return features using observations that are verifiably available by cutoff.

    Required invariants:
    - timestamps <= prediction_cutoff_utc (subject to bucket-end semantics)
    - no post-cutoff values used for imputation
    - no future-derived aggregate fields
    - quality flags capture short/sparse histories
    """
    ...
```

For the **1h model**, many temporal statistics may be undefined because little history exists. Use an explicit missing-value policy and omit features that inherently require many time points; don't create fake volatility from one observation.

### 8.3 Unit and orientation safety

- Normalize `TOKEN/WETH` direction based on verified **token addresses**, not symbols or token0 position.
- Clearly distinguish **WETH per token**, **token per WETH**, and **USD per token**.
- `feeTier` is a v3 integer representation and must be decoded/documented, not mistakenly read as a percentage.
- All TVL and volume magnitudes should have currency/valuation qualifiers.
- Calculate change rates only when denominator is valid and stable; handle zero/near-zero gracefully.
- Avoid inf/nan leaking into downstream estimators.

---

## 9. Data Science Deliverables and Experiments

### 9.1 Required DS analyses

1. **Acquisition and filtering funnel:** number of candidates, number with WETH pair, number of canonical pools, rejected reasons, final usable pool count.
2. **Data-quality profile:** missing hourly buckets, invalid USD TVL, stale end-state values, malformed token info, duplicates, event gaps.
3. **Descriptive statistics:** TVL distribution (log-scale when appropriate), volume, swap counts, fee tiers, cohort dates.
4. **Early trajectory plots:** first-24-hour TVL, normalized price, hourly volume, and activity for illustrative pools.
5. **Outcome stratification:** compare characteristics of pools with `label=1` vs `label=0`, reporting sample sizes and medians/intervals.
6. **Hypothesis tests:** e.g. trading intensity / volatility / early TVL-change differences using suitable tests, effect sizes, and multiple-testing caution.
7. **Liquidity interpretation:** show the limitations of USD TVL and any evidence from price or LP events.
8. **Robustness and bias:** compare inclusion thresholds, historical cohorts, activity sizes, and alternate event thresholds if time permits.
9. **Reproducible report:** concise findings, equations, plots, dataset card, and observed limitations.

### 9.2 Suggested DS hypotheses (not assumed results)

- H1: The distribution of first-24-hour price volatility differs between later-deteriorated and non-deteriorated pools.
- H2: First-day trading activity differs between those groups.
- H3: Early negative TVL change is associated with day-8 deterioration.
- H4 (exploratory): Characteristics vary across fee tiers or pool size strata.

Report **actual** confidence intervals, effect sizes, p-values (if used), and limitations. Do not write conclusions until the data support them. Be mindful that multiple pools may behave similarly during shared market conditions.

Preserve **Mann–Whitney U** for the specified continuous-variable comparisons and **chi-square** for categorical comparisons. The approved 30% labels change group membership, so outcome-dependent tests must be recomputed without changing the test methods. No statistical-test implementation or results are claimed by this specification.

### 9.3 DS notebooks

Recommended:

- `notebooks/01_data_source_and_pilot.ipynb`
- `notebooks/02_cleaning_and_quality.ipynb`
- `notebooks/03_exploratory_analysis.ipynb`
- `notebooks/04_statistical_findings.ipynb`

The data and graph creation logic should live in reusable `src/` modules where reasonable, so notebooks remain readable.

---

## 10. Machine Learning Training and Research Protocol

### 10.1 Models

- `DummyClassifier` (majority class and/or stratified baselines); record event prevalence and average precision.
- **Logistic Regression** — simple interpretable supervised baseline.
- **Random Forest** — nonlinear feature interactions.
- **XGBoost** — tabular boosting comparator; use CPU-friendly parameters and moderate search budget.

**Deep learning, GNNs, LSTMs, neural time-series encoders and trading agents are excluded from the six-week core scope.**

**Regression comparators:** Linear/Ridge Regression, Random Forest Regressor, and XGBoost Regressor, against mean/median Dummy Regressor. Both tasks reuse the same 70/15/15 chronological pool split with the eight-day embargo and the same permitted feature windows.

### 10.2 Reproducibility and fitting

- Use fixed random seeds and log library versions.
- Build a `Pipeline` / `ColumnTransformer` for train-only imputation/scaling/encoding.
- Keep target/identity/date fields outside the feature matrix unless a field is intentionally allowed and evaluated.
- Prefer chronological validation; if tuning via multiple folds, use purpose-built, temporally safe splits and embargoes.
- Choose parameters on validation only.
- Preserve model artifact + preprocessing + feature ordering + calibration object + threshold policy as **one versioned scoring bundle**.

### 10.3 Evaluation metrics

At minimum:

| Metric | Why |
|---|---|
| **Precision** | Fraction of high-alert detections actually meeting the target |
| **Recall** | How many true deterioration events were caught |
| **F1** | Precision/recall tradeoff |
| **PR-AUC / Average Precision** | More informative than accuracy when positive events are rare |
| **Confusion matrix** | Concrete missed/false warning counts |
| **ROC-AUC** | Secondary discrimination perspective (if both classes present) |
| **Brier score** | Probability quality |
| **Reliability / calibration curve** | Is predicted risk consistent with observed event frequency? |
| **Event prevalence** | Needed to interpret all metrics |

Include a **simple baseline** and class prevalence alongside every report. Avoid a headline “accuracy” number without context. Add uncertainty intervals/bootstrap appropriate to time cohorts if feasible. Do not make calibration claims with very few positive outcomes.

**Regression metrics:** RMSE, MAE, and R². Evaluate percentage-change predictions in percentage points for MAE/RMSE and report target-transform metadata. Explain regression in its actual output scale; do not apply classification risk bands or probability calibration to regression outputs.

### 10.4 Probability calibration and risk bands

Classifiers' `predict_proba` values are **not automatically calibrated risks**. Inspect holdout reliability and Brier score. Where enough data are available, use **sigmoid/Platt calibration** on data separate from model fitting (or a proven temporally safe equivalent). Isotonic regression may overfit with a small dataset; justify the choice.

Risk bands are a **presentation layer**, not separately trained classes:

```text
model score → (optional) validated calibrator → probability p
                                                   │
                                                   ├── Low
                                                   ├── Medium
                                                   └── High
```

- Choose Low/Medium/High thresholds on **validation data only**, based on empirical event rates, alert volume, and calibration evidence.
- Save the exact thresholds with the model bundle.
- If the validation set is too small or unreliable, **label these bands provisional**, or show only an uncalibrated model score clearly identified as such; never invent statistical confidence.
- The dashboard must state that probability means **model-estimated chance of the specific defined USD-TVL endpoint event**, not chance of scam, token-price decline, total investor loss, or guaranteed loss.

### 10.5 Explainability and explanations

Use the `shap` library for global and per-pool influence summaries on the selected best compatible tree/linear classification and regression models. Generate summary/beeswarm and bar plots globally, plus waterfall/force plots locally. Export SHAP summaries and regression predictions alongside classification outputs in cleaned Parquet/CSV for Tableau. Preserve task, window, split, model/target versions, base values, and explanation units. Key requirements:

- Distinguish **features increasing versus decreasing the model output**.
- Check the **explanation output space** (raw margin/log-odds vs probability) before showing numerical SHAP contributions. Do not assert that SHAP values add to probability percentages unless the explainer is configured/validated in probability space.
- **SHAP is associational attribution, not causal evidence.**
- Never manufacture a narrative that conflicts with the actual SHAP sign/rank.
- Generate **deterministic, template-based explanation text** from the top verified features. No LLM API is necessary.
- Show the top 3–5 indicators with human-friendly definitions, ideally alongside model observations and a “not investment advice” disclaimer.

**Illustrative output only (not real measurements):**

```text
Pool: ABC/WETH
Observation history: first 24 hours
Estimated severe USD-TVL deterioration risk: 0.82 (illustrative)
Risk band: High (illustrative)

Why this score?
- Early USD-TVL decreased substantially within the observation period.
- Price volatility was elevated.
- Sustained trading activity offset some risk.

Outcome being assessed: >=30% drop in USD TVL at day 8 vs hour 24.
This is a research estimate, not a prediction of fraud or investment advice.
```

### 10.6 Fair 1h / 6h / 24h comparison

- Use the **same target label** (hour-24 → day-8) and, where possible, same eligible pool cohort and chronological splits.
- State when data sufficiency leads to different sample sizes per window.
- Compare like-for-like metric definitions, positive event counts, and calibration procedure.
- Include a table and chart showing how early warnings improve (or fail to improve) as more history becomes available.
- If a simpler model beats XGBoost, report that honestly.

### 10.7 ML notebooks

Recommended:

- `notebooks/05_ml_baselines.ipynb`
- `notebooks/06_ml_early_windows.ipynb`
- `notebooks/07_probability_calibration.ipynb`
- `notebooks/08_explainability_and_cases.ipynb`

---

## 11. Demonstration Dashboard (MVP Only)

Use versioned cleaned Parquet/CSV prediction and SHAP extracts for a **Tableau** historical dashboard. The earlier **Streamlit** interface described below remains optional. No real-time continuous ingestion, account system, wallet connection, trade execution, React frontend, or production hosting required.

### Page A — Data Science explorer

- Dataset size, date range, eligibility funnel, and data-quality warnings.
- Historical pool selector and 24h early TVL/volume/price plots.
- Outcome-group plots and 1–3 key DS findings.

### Page B — Early risk assessment

- Select a **historical held-out pool** and information cutoff: 1h, 6h, or 24h.
- Show only early features supplied to the model.
- Display **model version**, estimated probability (calibrated only if supported), risk category (validated/provisional), and top SHAP indicators.
- Show concise explanation and explicit event definition.
- Provide an optional **“Reveal historical outcome”** section below the model prediction; never use it in scoring.
- Include missing-data flags and warnings when inference reliability is weak.

### Page C — Model evaluation (optional)

- Model comparison table and PR curves.
- Calibration plot / Brier score.
- Window comparison and disclaimer.

**Honesty rule:** until real trained artifacts exist, show only **clearly labeled illustrative/synthetic demo data**, never pass mock scores off as measured predictions.

---

## 12. Suggested Technical Stack and Repo Architecture

### 12.1 Stack

- **Python 3.11+** (choose one pinned version supported by current dependencies).
- **HTTPX** for HTTP requests; **GraphQL documents** as `.graphql` files.
- **Pandas, NumPy** for preprocessing and features.
- **PyArrow / Parquet**, optionally **DuckDB** for local analytics.
- **SciPy / statsmodels (if needed)** for statistical analysis.
- **scikit-learn** for ML/pipelines/metrics/calibration.
- **XGBoost** for gradient-boosted trees.
- **SHAP** for explanations.
- **Matplotlib or Plotly** for plots (avoid unnecessary frontend infrastructure).
- **Tableau** consumes cleaned Parquet/CSV prediction and SHAP extracts; **Streamlit** remains optional.
- **Jupyter Notebook** for instructor-required deliverables.
- **pytest, Ruff**, and **mypy** (optional) for tests/quality.
- **Git/GitHub** for version control.

### 12.2 Proposed repo layout (may adapt after inspecting repo)

```text
defi-pulse/
├── README.md
├── PROJECT_CONTEXT.md               # copy of this handoff, or link to it
├── pyproject.toml                   # or requirements.txt; choose one strategy
├── .env.example                     # placeholders ONLY
├── .gitignore
├── configs/
│   ├── source.yaml                  # chain, subgraph, WETH address, dates
│   ├── pilot.yaml                   # max pools, request cap, QA thresholds
│   └── experiments.yaml             # label version, windows, temporal splits
├── docs/
│   ├── architecture.md
│   ├── decisions.md
│   ├── dataset_card.md
│   ├── feasibility_report.md
│   ├── methodology.md
│   ├── ml_evaluation.md
│   ├── source_schema.md
│   ├── terminology.md
│   └── team_contributions.md
├── queries/
│   ├── introspection.graphql
│   ├── list_pools.graphql
│   ├── pool_hours.graphql
│   └── pool_outcomes.graphql
├── src/defi_pulse/
│   ├── __init__.py
│   ├── config.py
│   ├── sources/
│   │   ├── graph_client.py
│   │   ├── schema_probe.py
│   │   ├── pool_discovery.py
│   │   └── pool_history.py
│   ├── data/
│   │   ├── cache.py
│   │   ├── normalize.py
│   │   ├── quality.py
│   │   ├── sample.py
│   │   ├── feature_engineering.py
│   │   ├── labels.py
│   │   └── storage.py
│   ├── analysis/
│   │   ├── eda.py
│   │   └── statistics.py
│   ├── ml/
│   │   ├── splits.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   ├── calibrate.py
│   │   ├── explain.py
│   │   ├── risk_bands.py
│   │   └── bundle.py
│   └── cli.py
├── notebooks/
│   ├── 01_data_source_and_pilot.ipynb
│   ├── 02_cleaning_and_quality.ipynb
│   ├── 03_exploratory_analysis.ipynb
│   ├── 04_statistical_findings.ipynb
│   ├── 05_ml_baselines.ipynb
│   ├── 06_ml_early_windows.ipynb
│   ├── 07_probability_calibration.ipynb
│   └── 08_explainability_and_cases.ipynb
├── app/
│   └── streamlit_app.py
├── tests/
│   ├── fixtures/
│   ├── test_graph_client.py
│   ├── test_pool_selection.py
│   ├── test_time_windows.py
│   ├── test_features_no_leakage.py
│   ├── test_labels.py
│   ├── test_missing_hour_policy.py
│   ├── test_temporal_splits.py
│   └── test_scoring_bundle.py
├── data/
│   ├── raw/                      # generally ignored by Git
│   ├── interim/                  # ignored
│   ├── processed/                # ignored or sample-only
│   └── manifests/
└── models/                        # ignored or stored carefully
```

Do **not** create every file merely to match a tree. Implement incrementally and keep the repo simple enough to review in six weeks.

### 12.3 Suggested CLI interface (design proposal, not implemented commands)

```bash
# Verify subgraph access and field availability
python -m defi_pulse.cli source-check --dry-run

# Bounded live API pilot, after approved config and credentials
python -m defi_pulse.cli pilot --config configs/pilot.yaml --max-pools 20 --max-requests 500

# Purely local steps, no network after raw cache exists
python -m defi_pulse.cli normalize
python -m defi_pulse.cli build-labels
python -m defi_pulse.cli build-features --window 1
python -m defi_pulse.cli build-features --window 6
python -m defi_pulse.cli build-features --window 24
python -m defi_pulse.cli train --window 24
python -m defi_pulse.cli evaluate --window 24

# Historical demo
streamlit run app/streamlit_app.py
```

Codex may choose Typer/argparse or small scripts, but must document actual commands once implemented. Before then, these are **desired user-facing APIs**, not a claim they work.

---

## 13. Implementation Order and Acceptance Gates

### Phase 0 — Repository & source discovery (first task)

- [ ] Check what already exists.
- [ ] Create/update README with goals, installation, and “not a trading bot” disclaimer.
- [ ] Confirm Python environment and formatting/test configuration.
- [ ] Discover exact **live** Uniswap v3 Ethereum subgraph and API requirements.
- [ ] Inspect schema for required entity/field/filter support.
- [ ] Verify WETH address and token order handling.
- [ ] Write `docs/source_schema.md` with evidence, successful minimal query, and known limitations.
- [ ] Implement/mock only minimal safe HTTP client with **timeouts, retries, rate controls, and secrets via environment**.

**Done when:** a valid, small query returns verifiable structured data; the team's API key is safe; no billable service is required.

### Phase 1 — 20–30-pool feasibility pilot (mandatory)

- [ ] Select reproducible pool candidates across a fixed historical range.
- [ ] Verify canonical TOKEN/WETH selection and fee-tier diversity.
- [ ] Query 24h hourly history and day-8 outcome for each pool.
- [ ] Demonstrate timestamp/bucket correctness for 1h, 6h, and 24h.
- [ ] Cache raw JSON, create normalized Parquet, and preserve manifest/query fingerprints.
- [ ] Calculate actual record availability, outcome-label success, source quality, API calls, elapsed time, and disk bytes.
- [ ] Create a report with **examples of missing/stale/invalid data and the team's policy**.

**Done when:** the team can reconstruct defensible labels and multiple early-window features for at least a substantial, documented subset of pilot pools, and can explain why any were excluded. This is a feasibility test, **not evidence of ML performance**.

**Go/no-go gate:** If the source cannot reliably provide both early histories and day-8 states, **stop** scaling and propose a narrowly scoped change with evidence; do not build the full app around fake or cherry-picked data.

### Phase 2 — Data pipeline and DS

- [ ] Scale **only after** the pilot; attempt ~100 pools first, then toward 300–1,000 if feasible.
- [ ] Create deterministic selection/filter logic and rejection statistics.
- [ ] Clean/normalize timestamps, USD fields, token orientation, missing hours.
- [ ] Document the label construction, coverage policy, and quality flags.
- [ ] Build three leakage-safe feature tables and one labels table.
- [ ] Create DS notebooks and hypothesis tests with actual data.

**Done when:** all exported features can be reproduced, source data are cached, unit checks pass, and DS findings are supported by visual/statistical evidence.

### Phase 3 — ML baselines and scientific evaluation

- [ ] Chronological split with embargo and grouping by token/pool.
- [ ] DummyClassifier + Logistic Regression for all feasible windows.
- [ ] Random Forest + XGBoost classifiers with modest tuning.
- [ ] Mean/median Dummy Regressor, Linear/Ridge, Random Forest Regressor, and XGBoost Regressor on the same saved split; RMSE, MAE, and R².
- [ ] Same positive label across the three experiments.
- [ ] Precision/recall/F1/PR-AUC, prevalence, confusion matrix, Brier/calibration.
- [ ] Check results by sample size and cohort; log failures honestly.

**Done when:** saved evaluations reproduce and provide a credible comparison to simple baselines without temporal leakage.

### Phase 4 — Risk probabilities and explainability

- [ ] Validate raw risk probability reliability; calibrate on permitted validation data if feasible.
- [ ] Choose/provisionally label risk bands from validation-only evidence.
- [ ] Compute global summary/beeswarm/bar and local waterfall/force SHAP for selected compatible classification and regression models; preserve each output scale.
- [ ] Test narrative templates against feature contribution signs and available feature values.
- [ ] Document claims that **cannot** be inferred (fraud, investment returns, causal withdrawal).

**Done when:** each shown risk score can be traced to a model artifact, input cutoff, calibration status, band threshold policy, and SHAP explanation.

### Phase 5 — Demo, academic deliverables, and handoff

- [ ] Versioned Tableau classification/regression and global/local SHAP extracts; optional Streamlit DS and ML pages.
- [ ] Historical held-out example showing prediction **before** revealing day-8 outcome.
- [ ] ML and DS Jupyter notebooks run with cached data.
- [ ] DS report, ML report, reproducibility README and dataset card.
- [ ] `docs/team_contributions.md` records meaningful work by each team member.
- [ ] Run tests/lint; verify no credentials or large unwanted files in Git.

**Done when:** a new teammate can install, replay cached data, execute notebooks, verify major claims, and see the historical demo without paid services.

---

## 14. Six-Week Plan for Three Students

| Week | Focus | Observable output |
|---|---|---|
| 1 | Domain concepts, live schema verification, 20–30-pool pilot | Feasibility report, working collector, source decisions |
| 2 | Robust collection, 100-pool checkpoint, normalization, QA | Raw cache, manifest, normalized tables |
| 3 | Larger validated sample; features and DS analysis | `features_1h/6h/24h`, labels, DS charts/statistics |
| 4 | Baselines, temporal splits, Random Forest/XGBoost | Reproducible training/evaluation notebooks |
| 5 | Calibration, risk bands, SHAP, historical demo | Explainable model + small Streamlit interface |
| 6 | Sensitivity analysis, report, CCA documentation, viva/demo rehearsal | Final DS/ML deliverables with honest limitations |

### Team roles (shared understanding remains mandatory)

**Member A — Blockchain/context + Data Engineering:** schema verification, endpoint/key setup, canonical pool selection, bounded GraphQL collection, caching, source semantics, extraction tests.

**Member B — Data Science + Quality/Labels:** cleaning, missing-hour policy, USD/price interpretation, feature definitions, labeling, DS charts/statistics, dataset card.

**Member C — Machine Learning + Evaluation/Explainability:** splits, baselines, model comparisons, calibration, thresholds, SHAP, historical dashboard/report.

Everyone must be able to explain the target definition, what each early model sees, why The Graph is used, what TVL measures, why leakage matters, and why a risk score is **not a fraud accusation**.

---

## 15. Course / CCA Requirements — Must Remain Visible

The **Bahria University Karachi Campus, Fall 2026, AIL-301 Machine Learning Lab Complex Computing Activity (CCA)** instructions say that the project:

- may be completed by **2 or 3 students**;
- must address a **real-world problem** using a **public or self-collected dataset** sufficiently rich for model fitting/evaluation and different from routine lab datasets;
- must apply at least one suitable supervised or unsupervised algorithm and justify the selection;
- must include **data handling/preprocessing, EDA, feature engineering, model training/tuning/evaluation, and limitations**;
- must explicitly satisfy **at least THREE** Seoul Accord complex-activity characteristics;
- requires **instructor approval** via the prescribed template;
- requires submission of a folder containing the **proposal, code as Jupyter Notebook(s), and report**, with honest team contributions.

The grading is **20 marks** total: proposal 2.5, methodology 10, teamwork 5, report 2.5. **Methodology is the largest assessment component**, so prioritize reproducible experiments over aesthetic complexity.

### Seoul Accord mapping (include at least three; we can discuss all five)

| Characteristic | Concrete evidence in this project |
|---|---|
| **Range of resources** | Indexed blockchain data, GraphQL, Python, Parquet/DuckDB, statistical tools, ML libraries, team knowledge |
| **Level of interactions** | Resolve missing/outlier data, temporal leakage, TVL-price confounds, class imbalance, calibration-vs-interpretability trade-offs |
| **Innovation** | Explainable, early-window (1h/6h/24h) liquidity-risk assessment on self-collected Ethereum DEX data |
| **Consequences to society/environment** | Better understanding of risk information for public decentralized trading markets; risk of misleading users if outputs overclaim |
| **Familiarity** | Independently investigate blockchain indexing, data quality, time-aware evaluation, SHAP, calibration beyond routine ML labs |

The current ML proposal uses the university's five-page form and keeps its **fixed deliverables** unchanged. Do not replace the form with generic project documentation for final submission.

---

## 16. Engineering Quality and Tests — Mandatory Safety Checks

The most valuable tests are **semantic**, not just unit tests that a function executes.

### 16.1 Data-source tests

- Query construction and GraphQL variables do not interpolate untrusted strings unsafely.
- API errors and GraphQL partial errors are surfaced, not interpreted as empty data.
- Pagination is deterministic and avoids duplicates.
- Re-running a cached query does not unnecessarily spend API quota.
- Requests obey timeout, retry, and `--max-requests` safeguards.
- Same token in two v3 fee-tier pools yields **one canonical selected pool** under documented policy.
- The WETH side is detected correctly whether it is `token0` or `token1`.

### 16.2 Timestamp / feature leakage tests

Construct synthetic pool records with exaggerated future values:

- Change only hour-5 data; the **1h feature vector must not change**.
- Change only hour-20 data; the **1h and 6h feature vectors must not change**.
- Change only day-8 TVL; **no 1h/6h/24h feature vector may change**, only the label.
- A bucket whose end time is after cutoff cannot leak into early-window features.
- Missing earliest hours are not backfilled with later states.
- Final train/validation/test groups do not overlap by pool/token.
- Test set labels are not used in calibration/threshold selection.

### 16.3 Label tests

- `TVL_24h = 100`, `TVL_day8 = 70` ⇒ label `1` (exact 30% decline).
- `TVL_24h = 100`, `TVL_day8 = 71` ⇒ label `0`.
- Zero, negative, NaN, or stale/untrusted outcome TVL ⇒ invalid / missing label, **not automatic deterioration**.
- Day-8 timing must be based on creation + 8 days, not calendar midnight eight days later unless clearly documented as an approximation.
- Consistent label regardless of observation window.

### 16.4 ML tests

- Every model sees strictly the correct feature names/order for its window.
- Preprocessing fit is training-only.
- Probability is in `[0,1]`, and raw/calibrated fields are distinct.
- Band policy is monotonic (higher risk probability cannot produce a lower risk band).
- SHAP narrative uses the correct feature direction and model output scale.
- Test metrics are reproducible from saved run metadata.
- Fail visibly when held-out cohort contains only one class or is insufficient for meaningful evaluation.

### 16.5 Code quality

- Type-annotate public functions, validate external-data payloads, and maintain input/output contracts.
- Keep functions small and testable; avoid a 1,000-line notebook cell.
- Use dataset manifests, structured logs, and pure transforms where possible.
- No giant `try/except: pass` that hides data corruption.
- No secret/API key in committed code, notebooks, screenshots, or test fixtures.
- Do not delete or rewrite team code without inspecting and preserving intent.

---

## 17. Zero-Cost, Quota, Security, and Reproducibility Rules

- **Never** make paid queries, create a billable cloud deployment, or sign blockchain transactions.
- Use The Graph's currently available free plan only, within the user-provisioned account conditions.
- Put `GRAPH_API_KEY` / `SUBGRAPH_URL` (if appropriate) in local environment; provide `.env.example` with placeholders.
- Prefer validated POST GraphQL requests, with transparent request counts.
- Cache immutable historical responses so repeated DS/ML experiments are offline.
- Use a **local CPU**, open-source packages, and free editor/tooling.
- Avoid storing full blockchain blocks or unnecessary personally linked wallet data.
- Pin package versions after a working environment is established; provide lock/config and reproducible commands.
- Keep intermediate datasets under `data/` and Git-ignore large outputs; optionally publish small legally shareable fixtures and a script to regenerate larger research datasets.
- Store experiment config and exact cutoff dates so another student can reproduce the same cohort.
- Ensure model and dataset artifacts record source version and retrieval date, because indexed data can be reprocessed or revised.
- Retain a reproducible decision log of any manual filtering; **never delete inconvenient pools to improve scores**.

---

## 18. Research-Paper Potential (Optional Future Work)

The DS and ML parts could become **one combined research paper**, but publication is **not an assignment acceptance criterion** and must not be promised.

**Suggested future paper title:** *Explainable Early-Warning Assessment of Liquidity-Value Deterioration in Uniswap v3: A Leakage-Aware Historical Study*.

Potential research questions:

- RQ1: Which early trading and liquidity-value patterns correlate with subsequent USD-TVL deterioration?
- RQ2: How does prediction quality change when observing 1h versus 6h versus 24h?
- RQ3: How well are risk probabilities calibrated, and which features drive predictions?
- RQ4: Does performance generalize to pools created later in time?
- RQ5 (optional): How sensitive are results to the distinction between falling asset prices and actual liquidity removal?

**Claims of novelty require a real literature review.** Prior work already studies blockchain/DeFi fraud, risk prediction, and Uniswap liquidity. Keep contributions focused on reproducible sampling, clear financial proxies, honest temporal validation, probability reliability, and interpretability. Do not claim to have invented blockchain risk prediction.

---

## 19. Out of Scope — Explicitly Reject Feature Creep

The following are **not part of the agreed six-week MVP**:

- Running Ethereum clients/validators or archiving the full chain.
- Direct raw Ethereum block-by-block indexing as the main extraction method.
- Writing Solidity, deploying a token, creating or funding liquidity pools.
- Connecting user wallets, handling funds, DeFi trading, flash loans, leverage, or financial execution.
- Cross-chain bridges, Solana/Base/BNB cross-chain comparisons, or adding new chains.
- Uniswap v2/v4, PancakeSwap, SushiSwap, aggregator route selection.
- Modeling all fee tiers across multiple pools of the **same token** as independent train/test samples.
- Price forecasting, portfolio returns, arbitrage, or trading strategies.
- Binary accusations of scam/rug-pull/fraud based solely on TVL decline.
- Graph Neural Networks, Transformers, LSTMs, reinforcement learning.
- Real-time inference/stream processing, paid hosting, mobile app, React dashboard, auth system.
- Any complex feature requiring expensive raw data acquisition before core labels and baselines are proven.

Stretch tasks require explicit team approval **after** the basic results are complete.

---

## 20. Failure Modes, Contingencies, and Decisions to Escalate

| Risk | How to detect | Safe action |
|---|---|---|
| Uniswap subgraph unavailable/restricted | Schema/query probe fails | Verify current Graph Explorer deployment and permissions; do not invent endpoint |
| Free query budget insufficient | Pilot query count high | Reduce sample, batch fields, cache, prioritize aggregates; ask before source change |
| Missing/poor day-8 TVL | Outcome reconstruction fails | Investigate supported as-of state and staleness; exclude unreliable labels |
| Hour buckets misaligned with t0 | Boundary timestamps overlap cutoff | Use completed buckets/verified event timestamps; test anti-leakage |
| Too few positive events | Label prevalence very low | Show limitations, adjust sampling **without outcome cherry-picking**; alternative endpoint only via documented approval |
| USD valuation unreliable | Price/TVL discrepancies | Flag/exclude or use sensitivity analysis; do not overclaim |
| Same token appears in multiple pools | Duplicate token addresses | Deterministic canonical selection and grouped splitting |
| Model badly calibrated | Brier/reliability poor | Report probabilities as experimental scores; calibrate if enough data |
| Strong apparent scores but leakage | Time audit / random split artifacts | Rebuild features/splits; never market result as valid |
| DS and ML reports blur together | Same plots/results copied | Enforce separate questions, evidence, deliverables |
| Too much work for 6 weeks | Missed weekly checkpoints | Remove optional event-level and dashboard polish; prioritize defensible study |

**Escalate rather than silently decide** when: chain/protocol changes; target definition changes; a paid data source becomes necessary; no reliably aligned observations exist; or source/sampling changes fundamentally alter research claims.

---

## 21. External Documentation and Reading List

These resources describe how the intended external systems work. They **do not prove our selected endpoint/dataset has been tested**.

### Ethereum / Uniswap concepts

- Ethereum documentation: https://ethereum.org/en/developers/docs/
- Uniswap v3 concepts and docs: https://developers.uniswap.org/docs/get-started/concepts/liquidity-providers/concentrated-liquidity
- Uniswap v3 subgraph entity definitions (official developer docs): https://developers.uniswap.org/docs/ecosystem/subgraphs/concepts/v3/entities
- Uniswap v3 subgraph querying guide: https://developers.uniswap.org/docs/ecosystem/subgraphs/concepts/v3/queries
- Uniswap v3 subgraph source schema (verify current branch): https://github.com/Uniswap/v3-subgraph/blob/main/src/v3/schema.graphql

### The Graph / GraphQL

- What subgraphs are: https://thegraph.com/docs/en/subgraphs/overview/
- Finding a subgraph and its real query URL: https://thegraph.com/docs/en/subgraphs/querying/introduction/
- GraphQL API filters/pagination/historical-state queries: https://thegraph.com/docs/en/subgraphs/querying/graphql-api/
- GraphQL query best practices: https://thegraph.com/docs/en/subgraphs/querying/best-practices/
- Graph Explorer: https://thegraph.com/explorer

### Modeling / evaluation

- scikit-learn model evaluation: https://scikit-learn.org/stable/modules/model_evaluation.html
- scikit-learn probability calibration: https://scikit-learn.org/stable/modules/calibration.html
- scikit-learn `CalibratedClassifierCV`: https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html
- SHAP documentation: https://shap.readthedocs.io/en/latest/
- XGBoost documentation: https://xgboost.readthedocs.io/
- Streamlit documentation: https://docs.streamlit.io/

### Course-owned documents the team should keep nearby

- `ML-PROPOSAL-FORMAT-24102026-123207pm (1).docx` — prescribed five-page submission format.
- `CCA-ML-Lab-AIL-301-Fall2026p-28102026-090732pm.pdf` — instructor rubric and Complex Computing Activity expectations.
- `DeFi_Pulse_Explainable_Early_Liquidity_Risk_ML_Proposal.docx` — current updated ML proposal.
- `DeFi_Pulse_Data_Science_Project_Proposal.docx` — separate DS proposal.
- `DeFi_Pulse_Blockchain_Terminology_and_Learning_Guide.md` — optional detailed domain primer.

These source documents were available in the planning conversation; they may need to be copied into `docs/reference/` or supplied to Codex in its environment. **Do not assume Codex can read files that were not placed in its repository.**

---

## 22. Definition of Done — End-to-End

The six-week project is complete only if the team can demonstrate all of the following with **real, verified historical records**:

- [ ] A reproducible filter selects Ethereum Uniswap v3 **TOKEN/WETH** pools and keeps a canonical pool per target token.
- [ ] An auditable The Graph/GraphQL collector retrieves selective historical data without scanning raw Ethereum blocks or exceeding budget.
- [ ] Complete/partial availability, gap handling, and source limitations are documented.
- [ ] The fixed **hour-24-to-day-8 30% USD-TVL** target is reconstructed and quality-checked.
- [ ] Feature builders produce **1h, 6h, 24h** data with **tested no-leakage guarantees**.
- [ ] The DS project has defensible EDA, unchanged Mann–Whitney U/chi-square methods, findings, and a dataset card.
- [ ] Regression percentage-change targets and predictions share the classification splits; mean/median Dummy, Linear/Ridge, Random Forest Regressor, and XGBoost Regressor have RMSE/MAE/R² reports.
- [ ] Versioned cleaned Parquet/CSV prediction and global/local SHAP extracts support Tableau for both tasks.
- [ ] Dummy, Logistic Regression, Random Forest, and XGBoost receive a chronological evaluation.
- [ ] Metrics include **PR-AUC, precision, recall, F1, confusion matrix, and probability quality**.
- [ ] A calibrated probability is presented **only if calibrated and supported by holdout evidence**; otherwise status is explicitly experimental/uncalibrated.
- [ ] Low/Medium/High bands have saved, validation-derived threshold policies or are labeled provisional.
- [ ] SHAP analysis correctly identifies local/global **model** drivers, not proven causes.
- [ ] The historical demo cleanly separates input history, prediction, explanation, and subsequently revealed outcome.
- [ ] Source code/notebooks/data manifest/tests run locally, without mandatory payment.
- [ ] Reports meet instructor CCA criteria and document all three members' actual contributions.
- [ ] Any unachieved goals are documented plainly rather than simulated.

---

## 23. Codex Handoff Prompt — Copy This into a New Codex Session

> You are working in the `defi-pulse` repository. Read `PROJECT_CONTEXT.md` in full. We are building a six-week, three-person academic Data Science + Machine Learning project focused on **Ethereum Mainnet / Uniswap v3 / historical ERC-20-WETH pools**. The classification target is **30% or greater decrease in pool USD TVL between hour 24 and day 8 after pool creation**, and regression predicts the signed percentage change over those endpoints; 1h, 6h, and 24h experiments share that label, but features must use only history available by each cutoff. We will eventually produce calibrated risk probabilities (only if validated), Low/Medium/High bands, and SHAP-based non-causal explanations. **Do not** build a blockchain, download raw blocks, invent an endpoint, or build a real-time trading system. **First**, inspect the repository, check faculty approval status if relevant, find/validate the current Uniswap v3 Ethereum subgraph and schema from official sources, and make a short plan for a 20–30-pool extraction feasibility pilot. Explain exactly which fields and timestamp constraints you will request, how you will handle missing hourly records and hour-boundary leakage, and how you will stay within free query limits. Implement only the agreed first milestone, add tests, write a feasibility report, and report blockers honestly. Preserve existing files and code unless there is a documented reason to change them.

---

## 24. Maintenance Notes / Decision Log Starter

| ID | Decision | State | Rationale |
|---|---|---|---|
| D-001 | Single chain: Ethereum Mainnet | **Locked** | Limits domain/protocol variance |
| D-002 | Single DEX: Uniswap v3 | **Locked** | Consistent concentrated-liquidity AMM source |
| D-003 | ERC-20/WETH; one canonical pool per token | **Locked intent**; selection algorithm requires validation | Avoid mismatched quote assets/repeated target-token samples |
| D-004 | Model uses 1h/6h/24h **histories** | **Locked** | Captures trends rather than three snapshots |
| D-005 | Common target = hour-24-to-day-8 >=30% USD-TVL drop | **User-approved revision, 2026-11-10** | Supersedes the earlier 80% proposal definition; comparable early-warning experiments |
| D-006 | Primary data through The Graph subgraph | **Preferred**, requires live feasibility | Avoid raw-block ingestion |
| D-007 | Pilot 20–30 pools before scaling | **Locked** | Test costs and historical completeness |
| D-008 | Probabilities, risk bands, SHAP, explanations | **Locked intent**, dependent on statistical support | Interpretability and practical financial framing |
| D-009 | Live subgraph URL/schema, date range, QA thresholds | **Open** | Must be determined from a real pilot |
| D-010 | Missing-hour and as-of state policy | **Open**, with no-leakage safeguards fixed | Historical correctness |
| D-011 | Calibration choice/risk bands | **Open**, validation-dependent | Prevent misleading financial probabilities |

**Final instruction to Codex:** implement the scientifically defensible **smallest complete system**, prioritizing verified data and no-leakage evaluation. More lines of code, more blockchains, more models, and more UI pages do **not** make this project better if the historical data, target, or validation are wrong.


## 25. Approved Modeling Revision — 2026-11-10

The user explicitly approved replacing the old 80% event definition with a **30%** decline, adding regression over the same hour-24/day-8 endpoints, and extending SHAP and Tableau extracts. The active sections above reflect that change. The detailed current contract is [docs/modeling_update.md](docs/modeling_update.md).

- Classification version: `tvl_decline_30pct_h24_day8_v2`; `y_class = 1` when `TVL_day8 <= 0.70 * TVL_hour24` for valid endpoints.
- Regression version: `tvl_change_pct_h24_day8_v1`; signed percentage change. Linear/Ridge, Random Forest Regressor, XGBoost Regressor versus mean/median Dummy; RMSE, MAE, R².
- Classification models remain Logistic Regression, Random Forest Classifier, XGBoost Classifier versus Dummy; F1, Precision, Recall, PR-AUC, ROC-AUC, Confusion Matrix. Keep existing probability-quality safeguards and distinguish PR-AUC from average precision.
- Preserve collectors/ETL, full first 1h/6h/24h feature logic, chronological 70/15/15 allocation with the eight-day embargo, and Mann–Whitney U/chi-square methods. Both tasks share saved split IDs. Record actual counts after exclusions/embargo.
- SHAP for selected compatible tree/linear models in both tasks: global summary/beeswarm/bar, local waterfall/force; save signed contributions, feature values, base value, scale, task/window/model keys, and training-background provenance.
- Export `predicted_tvl_change_pct` alongside classification outputs plus separate global/local SHAP tables in versioned cleaned Parquet/CSV for Tableau. Future outcomes stay outside inference inputs.

Implementation status: collectors and diagnostics exist; final feature tables, chronological split code, named statistical tests, model training, SHAP, and Tableau modeling extracts remain planned. This revision changes Markdown only. Existing code and cached outputs still use the **old 80%** candidate definition. Historical diagnostic counts remain unchanged and explicitly historical; later code must build new versioned targets and rerun all dependent analyses. The original instructor-approval confirmation remains recorded; this update records the user's requested scope rather than claiming a newly reviewed course proposal.
