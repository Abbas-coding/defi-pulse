# DeFi Pulse

An academic Data Science and Machine Learning project investigating early liquidity-value deterioration in historical Ethereum Uniswap v3 pools. The research pipeline has an initial bounded feasibility collector; no trained risk model or measured performance exists yet.

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

## Verification

```bash
python3 -m unittest discover -s tests -v
```

No application build or model-training command is implemented. The initial research collector is under `src/defi_pulse/`; see the [documentation index](docs/README.md).
