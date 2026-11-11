# DeFi Pulse

## Approved Modeling Update — 2026-11-10

The modeling specification now uses **at least 30% USD-TVL deterioration** from hour 24 to day 8 for classification and adds **continuous TVL percentage-change regression** over the same interval. Both tasks retain the first 1h/6h/24h histories and the specified chronological 70/15/15 split with an eight-day embargo. Mann–Whitney U and chi-square remain the specified statistical tests.

Planned outputs include task-specific SHAP explanations and cleaned Parquet/CSV prediction and explanation extracts for Tableau. See the [approved specification](docs/modeling_update.md). The original collectors and reports retain historical **80%** candidate outputs. The new offline [baseline module](docs/baselines.md) separately builds versioned **30%**/regression candidate targets and runs explicit experimental baselines. Final USD label validation, tree models, and SHAP remain pending.

An academic Data Science and Machine Learning project investigating early liquidity-value deterioration in historical Ethereum Uniswap v3 pools. The research pipeline has an initial bounded feasibility collector; fixed exploratory baselines now run on provisional targets; no validated risk model exists yet.

## Start With the Graph Learning Demo

The separate educational demo retrieves one completed UTC hour for up to ten WETH pools. It includes response caching, offline replay, bounded retries, request limits, live schema checks, raw JSON, a CSV table, and a provenance manifest. Python 3.11+ is the only local dependency.

1. Create a query API key in [Subgraph Studio](https://thegraph.com/studio/) using the free plan.
2. Copy `.env.example` to `.env` and enter `GRAPH_API_KEY` locally.
3. Run from the repository root:

```bash
python3 -m demos.graph_demo
```

See [the demo guide](docs/graph_demo.md) for explicit hour selection, offline replay, field meanings, source references, and limitations. Live extraction has been verified for ten pools and one historical UTC hour; your local runs still require credentials or matching cached responses. This demo is not the project's research dataset or a trading system.

## Repository Layout

- `demos/graph_demo/`: standalone standard-library extraction demo.
- `src/defi_pulse/`: bounded research feasibility collector.
- `tests/`: offline semantic tests using synthetic API responses.
- `docs/`: implementation plan, architecture, methodology, design, decisions, and demo instructions.
- `notebooks/`: executed baseline/EDA walkthrough and setup guide.
- `scripts/execute_notebook.py`: reproducible notebook execution and HTML export.
- `data/demo/`: generated cache and exports, ignored by Git.
- `DEFI_PULSE_CODEX_PROJECT_CONTEXT.md`: original project context.

## Research Feasibility Pilot

Instructor approval was confirmed on 2026-11-09. Python 3.11+ and the same local Graph key are sufficient; no third-party dependencies or installation step are required. Run from the repository root:

```bash
PYTHONPATH=src python3 -m defi_pulse.pilot --pools 20 --max-requests 80
PYTHONPATH=src python3 -m defi_pulse.pilot --pools 20 --max-requests 80 --offline
```

Defaults select candidates created during October 1–7, 2026. Generated evidence is stored under `data/pilot/`; use a different `--output` directory to preserve a separate experiment. The pilot preserves missing state values and flags assumed no-trade hours. Endpoint evidence is provisional: no final labels, features, or models are generated. See the [feasibility report](docs/feasibility_report.md) for results and blockers.

Code uses four-space indentation, snake_case names, type hints on public functions, and standard-library `unittest` semantic tests.

## Historical TVL Check

The follow-up retrieves historical balances for the existing pilot pools:

```bash
PYTHONPATH=src python3 -m defi_pulse.historical_states --max-requests 20
PYTHONPATH=src python3 -m defi_pulse.historical_states --max-requests 20 --offline
```

All 40 endpoint states were retrieved. Pricing review and broader class coverage are still needed; see the [historical-state report](docs/historical_state_report.md).

## 200-Pool Activity Diagnostic

The expanded diagnostic selects 50 canonical pools from each of four fixed 2026 weeks, counts actual swaps during their first 1h/6h/24h, and retrieves historical outcome states. It keeps inactive pools. Python standard library only; run from the repository root:

```bash
PYTHONPATH=src python3 -m defi_pulse.diagnostic --max-requests 600
PYTHONPATH=src python3 -m defi_pulse.diagnostic --max-requests 600 --offline
```

Outputs are under `data/diagnostic_200/`. Start with `activity_summary.csv` (one row per pool), `pool_hours.csv` (unique pool-hour rows), and `historical_states/label_candidates.csv`. See [the diagnostic report](docs/diagnostic_200.md) for evidence and limitations. This is a dataset assessment; no model is trained.

## Separate Day-1 / Day-2 / Day-3 Comparison

Reuse the frozen 200-pool cohort and cached day 1, then compare the next two elapsed days:

```bash
PYTHONPATH=src python3 -m defi_pulse.three_day_activity --max-requests 200
PYTHONPATH=src python3 -m defi_pulse.three_day_activity --max-requests 200 --offline
```

Outputs under `data/diagnostic_200/three_day_activity/` include `daily_activity.csv` (one pool per day), `pool_comparison.csv` (one pool per row), and `summary.json`. Daily changes and cumulative totals are separate. This diagnostic does not change the prediction windows or target. See the [three-day findings](docs/three_day_activity.md).

## Notebook: EDA, Charts, Preprocessing, and Training

Open [notebooks/01_defi_pulse_end_to_end.ipynb](notebooks/01_defi_pulse_end_to_end.ipynb) for the complete implemented baseline walkthrough, including executed tables and charts. It covers source quality, target/feature preparation, chronological splits, training-only Mann–Whitney U and chi-square checks, baseline training, evaluation curves, residuals, coefficients, and pool predictions. It reads the existing cached dataset and sends no Graph queries.

```bash
.venv/bin/python -m pip install -r requirements-notebooks.lock
.venv/bin/jupyter lab notebooks/01_defi_pulse_end_to_end.ipynb
```

Select the project `.venv` kernel and **Restart Kernel and Run All**, or execute headlessly:

```bash
.venv/bin/python scripts/execute_notebook.py
```

The runner also creates a browser-readable HTML copy at `data/notebook_outputs/defi_pulse_baseline/notebook.html`, with standalone PNG/SVG charts in `charts/`. All generated notebook data, models, and figures are isolated from the original diagnostic/CLI outputs. See [notebook setup and artifact guide](notebooks/README.md). The notebook uses provisional targets and does not claim final financial labels, calibrated risks, tree-model results, or SHAP values.

## Optional Baseline Modeling Environment

Collectors still require only the standard library. The new offline baseline module uses a separate Python 3.12 environment (tested with 3.12.3):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-baselines.lock
PYTHONPATH=src .venv/bin/python -m defi_pulse.baselines
PYTHONPATH=src .venv/bin/python -m defi_pulse.baselines --allow-provisional-targets
.venv/bin/python -m unittest discover -s tests -v
```

The default command audits and exports data without fitting models because USD valuation quality is unresolved. The explicit experimental command fits fixed Dummy/Logistic Regression and mean/median Dummy/Ridge baselines for 1h/6h/24h using provisional 30%/percentage-change targets. Outputs are isolated under `data/baselines_30pct/audit/` and `data/baselines_30pct/experimental/`, in CSV/Parquet plus model bundles and manifests. It sends no API requests and preserves the collected diagnostic artifacts.

All 200 pools are development data because their outcomes have already been explored. Results are not a final untouched-test claim, calibrated risks, or verified financial labels. See [the baseline report](docs/baselines.md). Direct modeling dependencies are in `requirements-baselines.in`; all installed runtime dependencies are pinned in `requirements-baselines.lock`. Ruff formatting settings are in `pyproject.toml`; Ruff is not required for collection or included in the modeling runtime lock.

## Verification

```bash
python3 -m unittest discover -s tests -v
```

No application build is implemented. The baseline modeling command above is available; tree models, SHAP, and final-label training remain pending. The initial research collector is under `src/defi_pulse/`; see the [documentation index](docs/README.md).
