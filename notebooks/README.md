# DeFi Pulse Notebook

Open `01_defi_pulse_end_to_end.ipynb` for the complete implemented baseline
workflow, with executed tables and embedded charts. It covers cached inputs,
provenance, target validation, missingness, EDA, the three-day comparison,
chronological splits and embargo, training-only statistical comparisons,
preprocessing, training, evaluation, coefficients, and pool-level predictions.

Classification is the approved 30% decline; regression is signed percentage
change from hour 24 to day 8. Outcomes remain provisional because source USD
pricing is not independently verified. The already-explored cohort is development
data. No Graph requests, credentials, model tuning, calibration, or synthetic
measurements are required. Tree models and SHAP are future modeling work;
coefficient plots in this notebook are explicitly not SHAP.

## Read the existing outputs

In VS Code connected to WSL, open the `.ipynb` file. Its executed outputs can be
read without rerunning. A standalone copy is generated at:

```text
data/notebook_outputs/defi_pulse_baseline/notebook.html
```

Open that HTML file in a browser to read tables, code, and charts without a
Jupyter server. Individual charts are in the adjacent `charts/` directory as
PNG and SVG. Notebook outputs and generated data are ignored by Git; the
executed `.ipynb` itself is a reviewable repository artifact.

## Setup and run

Use the repository root in WSL. Python 3.12 is the tested environment.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-notebooks.lock
.venv/bin/jupyter lab notebooks/01_defi_pulse_end_to_end.ipynb
```

Choose the `.venv` Python kernel and **Restart Kernel and Run All**. In VS Code,
use the notebook's **Select Kernel** menu to choose `.venv/bin/python`.

To execute and regenerate the notebook/HTML without opening the UI:

```bash
.venv/bin/python scripts/execute_notebook.py
.venv/bin/python -m unittest discover -s tests -v
```

The runner uses the current Python interpreter for its kernel and temporary
runtime/cache directories. It executes the notebook from the repository root,
fails visibly on cell errors, and publishes the executed notebook and HTML only
after successful execution.

## Cached data and exports

The existing `data/diagnostic_200/` cohort, `manifest.live.json`, activity
summaries, and historical states are required. Its first-day hourly CSV and
three-day CSV provide the EDA plots. Generated datasets are not in Git: a fresh
clone needs those cached artifacts restored from the original project machine.
The notebook does not silently recollect them or download a substitute dataset.

Outputs are isolated under `data/notebook_outputs/defi_pulse_baseline/`:

- Targets, split assignments, and per-window features in CSV/Parquet.
- Predictions and metrics in CSV/Parquet, plus saved model bundles.
- Training-only Mann–Whitney U and chi-square result tables.
- Nineteen chart figures, each exported as PNG and SVG.
- Linear coefficients, source/output hashes, package versions, and limitations.
- A standalone HTML copy of the executed notebook.

The notebook checks that its predictions reproduce the CLI baseline outputs
when those are present. It preserves the original collectors and diagnostic
files. Statistical significance is not presented when chi-square cell-count
assumptions fail. All p-values are exploratory and use only training pools.

Direct notebook dependencies are in `requirements-notebooks.in`; the lockfile
includes their full tested environment and preserves the pinned baseline
runtime. The core collectors still need only Python's standard library.
