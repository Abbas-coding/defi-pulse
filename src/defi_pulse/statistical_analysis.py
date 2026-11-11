"""Exploratory, training-only DS tests with visible small-cell limitations."""

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, mannwhitneyu

from .data_preparation import NUMERIC_FEATURES


def training_tests(features_by_window: dict, labels: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Freeze test families; evaluation-period values never enter these comparisons."""
    continuous, categorical = [], []
    label_columns = labels[["pool_address", "candidate_y_class", "structurally_eligible"]]
    if label_columns.pool_address.duplicated().any():
        raise ValueError("One target per pool is required.")
    for window, features in features_by_window.items():
        train = features[(features["split"] == "train") & features["feature_eligible"]].merge(
            label_columns, on="pool_address", validate="one_to_one")
        train = train[train.structurally_eligible].copy()
        for feature in NUMERIC_FEATURES:
            x = pd.to_numeric(train.loc[train.candidate_y_class == 1, feature], errors="raise").to_numpy(float)
            y = pd.to_numeric(train.loc[train.candidate_y_class == 0, feature], errors="raise").to_numpy(float)
            row = {"window_hours": window, "feature": feature, "positive_n": len(x), "negative_n": len(y),
                   "positive_median": float(np.median(x)) if len(x) else None,
                   "negative_median": float(np.median(y)) if len(y) else None,
                   "u_statistic": None, "rank_biserial_positive_higher": None, "p_value": None,
                   "method": "two_sided_mann_whitney_u_asymptotic_tie_and_continuity_correction",
                   "scope": "training_only_provisional_outcome_groups"}
            if min(len(x), len(y)) >= 2 and np.isfinite(x).all() and np.isfinite(y).all():
                result = mannwhitneyu(x, y, alternative="two-sided", method="asymptotic", use_continuity=True)
                row.update(u_statistic=float(result.statistic), p_value=float(result.pvalue),
                           rank_biserial_positive_higher=float(2 * result.statistic / (len(x) * len(y)) - 1))
            continuous.append(row)
        table = pd.crosstab(train.fee_tier.astype(str), train.candidate_y_class).reindex(columns=[0, 1], fill_value=0)
        row = {"window_hours": window, "feature": "fee_tier", "n": len(train),
               "chi2": None, "degrees_of_freedom": None, "cramers_v": None, "p_value": None,
               "minimum_expected_count": None, "assumptions_supported": False,
               "reason": "insufficient_categories_or_outcome_classes",
               "scope": "training_only_provisional_outcome_groups",
               "observed_table": table.to_json()}
        if len(table) >= 2 and (table.sum(axis=0) > 0).all():
            result = chi2_contingency(table.to_numpy())
            supported = bool((result.expected_freq >= 5).all() and (table.to_numpy() >= 5).all())
            row.update(chi2=float(result.statistic), degrees_of_freedom=int(result.dof),
                       cramers_v=float(np.sqrt(result.statistic / (len(train) * min(table.shape[0] - 1, 1)))),
                       minimum_expected_count=float(result.expected_freq.min()), assumptions_supported=supported,
                       p_value=float(result.pvalue) if supported else None,
                       reason="supported" if supported else "sparse_cells_inferential_p_value_withheld")
        categorical.append(row)
    # Include every prespecified comparison in its family, not only attractive results.
    for rows in (continuous, categorical):
        family = len(rows)
        for row in rows:
            row["family_size"] = family
            row["p_bonferroni"] = min(1.0, row["p_value"] * family) if row["p_value"] is not None else None
    return pd.DataFrame(continuous), pd.DataFrame(categorical)
