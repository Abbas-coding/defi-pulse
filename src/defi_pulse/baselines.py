"""Offline, provisional classification/regression baselines on the development cohort."""

import argparse
import importlib.metadata
import json
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    auc, average_precision_score, brier_score_loss, confusion_matrix, f1_score,
    mean_absolute_error, precision_recall_curve, precision_score, r2_score,
    recall_score, roc_auc_score, root_mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from demos.graph_demo.demo import DemoError, save_json
from .data_preparation import (
    CATEGORICAL_FEATURES, CLASS_VERSION, FEATURES, FEATURE_VERSION, NUMERIC_FEATURES,
    REG_VERSION, chronological_splits, feature_row, file_hash, targets,
)

CONFIG = {
    "classification_version": CLASS_VERSION, "regression_version": REG_VERSION,
    "feature_version": FEATURE_VERSION, "features": FEATURES, "windows": [1, 6, 24],
    "nominal_split": [0.70, 0.15, 0.15], "embargo_days": 8,
    "seed": 42, "logistic_C": 1.0, "logistic_class_weight": "balanced",
    "ridge_alpha": 1.0, "decision_threshold": 0.5,
    "regression_transform": "identity_percentage_change", "imputation": "none",
    "numeric_transform": "fixed_log1p_then_training_only_standard_scaler",
    "categorical_transform": "training_only_one_hot_fee_tier_unknown_ignore",
    "model_selection": "none_fixed_baselines_no_tuning_or_calibration",
    "evaluation_status": "exploratory_development_cohort_not_pristine_final_test",
}


def preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("numeric", Pipeline([("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
                               ("scale", StandardScaler())]), NUMERIC_FEATURES),
        ("fee", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
    ])


def fit_baseline(task: str, name: str, x_train: pd.DataFrame, y_train: np.ndarray) -> Pipeline:
    estimators = {
        "dummy_prior": DummyClassifier(strategy="prior"),
        "logistic_regression": LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000, random_state=42),
        "dummy_mean": DummyRegressor(strategy="mean"),
        "dummy_median": DummyRegressor(strategy="median"),
        "ridge": Ridge(alpha=1.0),
    }
    if list(x_train.columns) != FEATURES:
        raise DemoError("Feature order does not match the versioned contract.")
    if task == "classification" and len(np.unique(y_train)) != 2:
        raise DemoError("Classification training requires both classes.")
    pipeline = Pipeline([("preprocess", preprocessor()), ("model", clone(estimators[name]))])
    pipeline.fit(x_train, y_train)
    return pipeline


def classification_metrics(y: np.ndarray, probability: np.ndarray) -> dict:
    decisions = (probability >= CONFIG["decision_threshold"]).astype(int)
    result = {"n": len(y), "positive_count": int(y.sum()),
              "prevalence": float(np.mean(y)),
              "confusion_matrix": confusion_matrix(y, decisions, labels=[0, 1]).tolist(),
              "brier_score": float(brier_score_loss(y, probability)),
              "decision_threshold": CONFIG["decision_threshold"],
              "pr_auc_definition": "trapezoidal_area_of_precision_recall_curve"}
    if len(np.unique(y)) < 2:
        result.update({k: None for k in ("f1", "precision", "recall", "pr_auc", "average_precision", "roc_auc")})
        result["metric_warning"] = "single_class_evaluation_no_discrimination_or_positive_recall_evidence"
        return result
    precision, recall, _ = precision_recall_curve(y, probability)
    result.update(f1=float(f1_score(y, decisions, zero_division=0)),
                  precision=float(precision_score(y, decisions, zero_division=0)),
                  recall=float(recall_score(y, decisions, zero_division=0)),
                  pr_auc=float(auc(recall, precision)),
                  average_precision=float(average_precision_score(y, probability)),
                  roc_auc=float(roc_auc_score(y, probability)))
    result["metric_warning"] = "few_events_and_development_cohort_exploratory_only"
    return result


def regression_metrics(y: np.ndarray, prediction: np.ndarray) -> dict:
    varied = len(y) >= 2 and len(np.unique(y)) > 1
    return {"n": len(y), "rmse": float(root_mean_squared_error(y, prediction)),
            "mae": float(mean_absolute_error(y, prediction)),
            "r2": float(r2_score(y, prediction)) if varied else None,
            "error_units": "percentage_points", "predictions_below_minus100": int((prediction < -100).sum()),
            "metric_warning": "exploratory_unverified_valuation_and_unclipped_extreme_targets" if varied else "r2_undefined_constant_or_insufficient_targets"}


def export_table(out: Path, name: str, rows: list[dict]) -> None:
    frame = pd.DataFrame(rows)
    for column in ("candidate_y_class", "final_y_class", "predicted_class"):
        if column in frame:
            frame[column] = pd.array(frame[column], dtype="Int64")
    frame.to_csv(out / f"{name}.csv", index=False)
    frame.to_parquet(out / f"{name}.parquet", index=False)


def load_inputs(source: Path) -> tuple[list[dict], list[dict], list[dict], dict, dict]:
    manifest = json.loads((source / "manifest.live.json").read_text())
    hashes = {}
    for name in ("pools.json", "activity_summary.json", "historical_states/states.json"):
        expected = (manifest["historical"]["artifact_sha256"]["states.json"] if name.startswith("historical_states/")
                    else manifest["artifact_sha256"][name])
        hashes[name] = file_hash(source / name)
        if hashes[name] != expected:
            raise DemoError("Input hash mismatch; do not reuse a changed source as the same experiment.")
    return (*(json.loads((source / name).read_text()) for name in hashes), manifest, hashes)


def run(args: argparse.Namespace) -> dict:
    pools, activity, states, original, hashes = load_inputs(args.source)
    out = args.output / ("experimental" if args.allow_provisional_targets else "audit")
    out.mkdir(parents=True, exist_ok=True)
    previous = out / "manifest.json"
    if previous.exists():
        old = json.loads(previous.read_text())
        if old["input_sha256"] != hashes or old["configuration"] != CONFIG:
            raise DemoError("Output belongs to a different experiment; choose a new --output directory.")
    save_json(out / "configuration.json", CONFIG)  # Freeze before fitting or evaluation.
    if len({r["pool_address"] for r in activity}) != len(activity):
        raise DemoError("Duplicate activity summaries.")
    summaries = {r["pool_address"]: r for r in activity}
    indexed_states = {(r["pool_address"], r["endpoint"]): r for r in states}
    if len(indexed_states) != len(states):
        raise DemoError("Duplicate endpoint states.")
    splits = chronological_splits(pools)
    split_by_id = {r["pool_address"]: r for r in splits}
    head = int(original["source_metadata"]["block"]["number"])
    label_rows = [targets(pool, indexed_states.get((pool["id"], "hour24"), {}),
                          indexed_states.get((pool["id"], "day8"), {}), head) for pool in pools]
    label_by_id = {r["pool_address"]: r for r in label_rows}
    for row in label_rows:
        row["split"] = split_by_id[row["pool_address"]]["split"]
    all_features, experiment_rows = [], {}
    for window in (1, 6, 24):
        rows = []
        for pool in pools:
            row = feature_row(pool, summaries[pool["id"]], window)
            row["split"] = split_by_id[pool["id"]]["split"]
            rows.append(row)
        all_features.extend(rows)
        experiment_rows[window] = rows
        export_table(out, f"features_{window}h", rows)
    export_table(out, "targets", label_rows)
    export_table(out, "splits", splits)
    audit = {
        "pricing_status": "not_independently_verified_no_final_labels",
        "structurally_eligible_targets": sum(r["structurally_eligible"] for r in label_rows),
        "candidate_class_counts": dict(Counter(str(r["candidate_y_class"]) for r in label_rows)),
        "exclusion_counts": dict(Counter(r["exclusion_reason"] for r in label_rows if r["exclusion_reason"])),
        "nominal_split_counts": dict(Counter(r["nominal_split"] for r in splits)),
        "retained_split_counts_before_quality": dict(Counter(r["split"] for r in splits)),
        "eligible_class_counts_by_split": {split: dict(Counter(str(r["candidate_y_class"]) for r in label_rows
                                                              if r["split"] == split and r["structurally_eligible"]))
                                             for split in ("train", "validation", "test", "embargo")},
        "features": FEATURES, "features_with_missing_or_invalid_values": sum(not r["feature_eligible"] for r in all_features),
        "no_imputation": True,
        "usd_tvl_features": "excluded_until_valuation_quality_is_established",
        "source_volume_feature": "observed_source_value_unverified_pricing_experimental_only",
        "descriptive_target_flags_not_exclusions": dict(Counter(flag for row in label_rows for flag in row["audit_flags"])),
    }
    save_json(out / "data_quality_audit.json", audit)
    metrics, predictions, skipped, model_paths = [], [], [], []
    if args.allow_provisional_targets:
        (out / "models").mkdir(exist_ok=True)
        for window, rows in experiment_rows.items():
            eligible = [r for r in rows if r["feature_eligible"] and label_by_id[r["pool_address"]]["structurally_eligible"]
                        and r["split"] != "embargo"]
            frame = pd.DataFrame(eligible)
            if frame.empty:
                skipped.append({"window": window, "reason": "no_eligible_features_and_targets"})
                continue
            for col in NUMERIC_FEATURES:
                frame[col] = pd.to_numeric(frame[col], errors="raise").astype(float)
            frame["fee_tier"] = frame["fee_tier"].astype(str)
            train = frame[frame["split"] == "train"]
            if len(train) < 2:
                skipped.append({"window": window, "reason": "insufficient_training_rows"})
                continue
            for task, names, target_name in (
                    ("classification", ("dummy_prior", "logistic_regression"), "candidate_y_class"),
                    ("regression", ("dummy_mean", "dummy_median", "ridge"), "candidate_y_reg")):
                y_train = np.array([label_by_id[p][target_name] for p in train["pool_address"]],
                                   dtype=int if task == "classification" else float)
                if task == "classification" and len(np.unique(y_train)) != 2:
                    skipped.append({"window": window, "task": task, "reason": "single_class_training"})
                    continue
                for name in names:
                    model_version = f"baseline_v1_{window}h_{name}_{hashes['pools.json'][:12]}"
                    fitted = fit_baseline(task, name, train[FEATURES], y_train)
                    model_path = out / "models" / f"{window}h_{name}.joblib"
                    joblib.dump({"pipeline": fitted, "window_hours": window, "task": task,
                                 "features": FEATURES, "configuration": CONFIG,
                                 "model_version": model_version,
                                 "status": "experimental_provisional_usd_targets", "input_sha256": hashes}, model_path)
                    model_paths.append(str(model_path))
                    for split in ("validation", "test"):
                        held = frame[frame["split"] == split]
                        if held.empty:
                            skipped.append({"window": window, "task": task, "model": name, "split": split,
                                            "reason": "no_evaluation_rows"})
                            continue
                        actual = np.array([label_by_id[p][target_name] for p in held["pool_address"]],
                                          dtype=int if task == "classification" else float)
                        if task == "classification":
                            predicted = fitted.predict_proba(held[FEATURES])[:, 1]
                            measured = classification_metrics(actual, predicted)
                        else:
                            predicted = fitted.predict(held[FEATURES])
                            measured = regression_metrics(actual, predicted)
                        metrics.append({"window_hours": window, "task": task, "model": name,
                                        "model_version": model_version, "split": split,
                                        "status": "experimental_provisional_targets", **measured})
                        for pool_id, truth, prediction in zip(held["pool_address"], actual, predicted):
                            predictions.append({
                                "pool_address": pool_id, "window_hours": window, "task": task,
                                "model": name, "model_version": model_version, "split": split,
                                "observed_provisional_target": float(truth),
                                "classification_score": float(prediction) if task == "classification" else None,
                                "predicted_class": int(prediction >= 0.5) if task == "classification" else None,
                                "predicted_tvl_change_pct": float(prediction) if task == "regression" else None,
                                "classification_definition_version": CLASS_VERSION,
                                "regression_definition_version": REG_VERSION, "feature_definition_version": FEATURE_VERSION,
                                "target_quality": "provisional_usd_valuation",
                                "calibration_status": "not_calibrated" if task == "classification" else "not_applicable",
                                "evaluation_status": CONFIG["evaluation_status"],
                            })
                    print(f"Fitted {window}h {name} on {len(train)} training pools.", flush=True)
    else:
        skipped.append({"reason": "pricing_quality_unverified_use_explicit_experimental_mode_for_candidate_targets"})
    save_json(out / "metrics.json", metrics)
    save_json(out / "skipped.json", skipped)
    export_table(out, "metrics", [{**r, "confusion_matrix": json.dumps(r["confusion_matrix"]) if "confusion_matrix" in r else None} for r in metrics])
    export_table(out, "predictions", predictions)
    packages = {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "scikit-learn", "scipy", "pyarrow", "joblib")}
    result = {
        "run_status": "experimental_baselines_completed" if model_paths else "audit_only_no_models",
        "output": str(out), "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": CONFIG, "input_sha256": hashes, "source_metadata": original["source_metadata"],
        "training_target_policy": "explicit_provisional_candidate_opt_in" if args.allow_provisional_targets else "strict_no_unverified_targets",
        "python": platform.python_version(), "packages": packages, "network_attempts": 0,
        "models": model_paths, "prediction_rows": len(predictions), "metric_rows": len(metrics),
        "audit": audit, "skipped": skipped,
        "limitations": ["USD valuations and candidate targets are not independently verified; final labels remain null",
                        "All 200 pools were already explored, so test is a chronological development diagnostic only",
                        "Single-class validation prevents classification model selection or calibration",
                        "Small event counts and extreme regression targets limit interpretation",
                        "No synthetic observations, imputation, outcome clipping, or activity filtering"],
    }
    result["artifact_sha256"] = {str(p.relative_to(out)): file_hash(p) for p in out.rglob("*")
                                 if p.is_file() and p.name != "manifest.json"}
    save_json(out / "manifest.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/diagnostic_200"))
    parser.add_argument("--output", type=Path, default=Path("data/baselines_30pct"))
    parser.add_argument("--allow-provisional-targets", action="store_true",
                        help="Run explicitly experimental models using candidate USD-valued targets; no final-label claim.")
    try:
        result = run(parser.parse_args())
    except (DemoError, ValueError, KeyError, TypeError) as error:
        print(f"Baseline run stopped: {error}" if isinstance(error, DemoError) else
              "Baseline run stopped: invalid data or incompatible modeling environment.")
        raise SystemExit(1) from None
    print(json.dumps({k: result[k] for k in ("run_status", "output", "prediction_rows", "metric_rows", "audit")}, indent=2))


if __name__ == "__main__":
    main()
