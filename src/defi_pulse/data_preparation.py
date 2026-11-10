"""Pure, versioned target/feature preparation from existing diagnostic artifacts."""

import hashlib
import math
from datetime import datetime
from decimal import Decimal, InvalidOperation, localcontext

from demos.graph_demo.demo import DemoError
from .pilot import DAY

CLASS_VERSION = "tvl_decline_30pct_h24_day8_v2"
REG_VERSION = "tvl_change_pct_h24_day8_v1"
FEATURE_VERSION = "observed_swap_activity_v1"
NUMERIC_FEATURES = ["swap_count", "swap_transaction_count", "active_hours", "swap_volume_usd"]
CATEGORICAL_FEATURES = ["fee_tier"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def timestamp(value: str) -> int:
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise DemoError("Timestamps must carry an explicit UTC offset.")
    return int(date.timestamp())


def targets(pool: dict, left: dict, right: dict, head: int) -> dict:
    """Preserve quality exclusions and exact Decimal class comparisons; never impute."""
    result = {
        "pool_address": pool["id"], "classification_definition_version": CLASS_VERSION,
        "regression_definition_version": REG_VERSION,
        "hour24_tvl_usd": left.get("tvl_usd"), "day8_tvl_usd": right.get("tvl_usd"),
        "candidate_y_class": None, "candidate_y_reg": None,
        "final_y_class": None, "final_y_reg": None,
        "pricing_quality": "unverified_indexed_usd_valuation", "structurally_eligible": False,
        "exclusion_reason": None, "audit_flags": [],
        "hour24_requested_as_of_utc": left.get("requested_as_of_utc"),
        "day8_requested_as_of_utc": right.get("requested_as_of_utc"),
        "hour24_block_number": left.get("block_number"), "day8_block_number": right.get("block_number"),
    }
    def reject(reason: str) -> dict:
        result["exclusion_reason"] = reason
        return result
    try:
        for row, endpoint, elapsed in ((left, "hour24", DAY), (right, "day8", 8 * DAY)):
            if row["pool_address"] != pool["id"] or row["endpoint"] != endpoint:
                return reject("endpoint_identity_mismatch")
            expected = int(pool["createdAtTimestamp"]) + elapsed
            if timestamp(row["requested_as_of_utc"]) != expected:
                return reject("requested_endpoint_mismatch")
            if (row["timing_quality"] != "exact_cutoff_timestamp" or row["cutoff_gap_seconds"] != 0
                    or timestamp(row["block_timestamp_utc"]) != expected):
                return reject("nonexact_endpoint_timing")
            if not 0 < int(row["block_number"]) <= head or row["quality"] != "historical_indexed_state":
                return reject("invalid_source_state")
            for name in ("token0_balance", "token1_balance"):
                value = Decimal(row[name])
                if not value.is_finite() or value < 0:
                    return reject("invalid_token_balance")
        a, b = Decimal(left["tvl_usd"]), Decimal(right["tvl_usd"])
        if not a.is_finite() or a <= 0:
            return reject("invalid_or_zero_hour24_tvl")
        if not b.is_finite() or b < 0:
            return reject("invalid_day8_tvl")
        if b == 0:
            return reject("zero_day8_policy_pending")
        with localcontext() as context:
            context.prec = max(100, len(a.as_tuple().digits) + len(b.as_tuple().digits) + 20)
            label = int(b <= Decimal("0.70") * a)
            change = (b - a) / a * Decimal(100)
        if not math.isfinite(float(change)):
            return reject("regression_target_outside_numeric_range")
        result.update(candidate_y_class=label, candidate_y_reg=str(change), structurally_eligible=True)
        if a < 1:
            result["audit_flags"].append("hour24_tvl_below_one_usd_descriptive_only")
        if change > 1000:
            result["audit_flags"].append("gain_over_1000_percent_untrimmed")
        if (a == b and left["token0_balance"] == right["token0_balance"]
                and left["token1_balance"] == right["token1_balance"]):
            result["audit_flags"].append("unchanged_balances_and_stored_usd")
    except (KeyError, TypeError, ValueError, InvalidOperation, OverflowError):
        return reject("malformed_endpoint")
    return result


def chronological_splits(pools: list[dict]) -> list[dict]:
    """Split all pools first by time; purge earlier outcomes across fixed boundaries."""
    ordered = sorted(pools, key=lambda p: (int(p["createdAtTimestamp"]), p["id"]))
    if len({p["id"] for p in pools}) != len(pools):
        raise DemoError("A pool cannot appear twice in split assignment.")
    tokens = [target_token(p) for p in pools]
    if len(set(tokens)) != len(tokens):
        raise DemoError("Canonical target tokens must be unique across pools.")
    n = len(ordered)
    first, second = n * 70 // 100, n * 85 // 100
    if not 0 < first < second < n:
        raise DemoError("Too few pools for chronological train/validation/test assignment.")
    val_start = int(ordered[first]["createdAtTimestamp"])
    test_start = int(ordered[second]["createdAtTimestamp"])
    rows = []
    for index, pool in enumerate(ordered):
        created = int(pool["createdAtTimestamp"])
        nominal = "train" if index < first else "validation" if index < second else "test"
        boundary = val_start if nominal == "train" else test_start if nominal == "validation" else None
        purged = boundary is not None and created + 8 * DAY > boundary
        rows.append({"pool_address": pool["id"], "target_token_address": target_token(pool),
                     "created_at_unix": created, "nominal_split": nominal,
                     "split": "embargo" if purged else nominal, "embargo_seconds": 8 * DAY,
                     "reason": "outcome_window_crosses_next_creation_boundary" if purged else None})
    # Check actual retained time relationships, not just nominal row proportions.
    for earlier, later in (("train", "validation"), ("validation", "test")):
        a, b = [r for r in rows if r["split"] == earlier], [r for r in rows if r["split"] == later]
        if a and b and max(r["created_at_unix"] for r in a) + 8 * DAY > min(r["created_at_unix"] for r in b):
            raise DemoError("Chronological embargo invariant violated.")
    return rows


def target_token(pool: dict) -> str:
    weth = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    if pool["token0"]["id"] == weth:
        return pool["token1"]["id"]
    if pool["token1"]["id"] == weth:
        return pool["token0"]["id"]
    raise DemoError("Expected a WETH pair.")


def feature_row(pool: dict, summary: dict, window: int) -> dict:
    """Whitelist only same-window factual activity; no day-8 or later-window fields."""
    if window not in (1, 6, 24) or summary["pool_address"] != pool["id"]:
        raise DemoError("Unsupported feature window or mismatched pool identity.")
    row = {"pool_address": pool["id"], "window_hours": window,
           "feature_cutoff_unix": int(pool["createdAtTimestamp"]) + window * 3600,
           "feature_definition_version": FEATURE_VERSION, "fee_tier": str(pool["feeTier"]),
           "swap_count": summary[f"swap_count_{window}h"],
           "swap_transaction_count": summary[f"swap_transaction_count_{window}h"],
           "active_hours": summary[f"active_elapsed_hours_{window}h"],
           "swap_volume_usd": summary[f"swap_volume_usd_{window}h"],
           "feature_eligible": summary["swap_history_complete"] is True,
           "feature_exclusion_reason": None,
           "volume_quality": "unverified_source_usd_valuation"}
    if not row["feature_eligible"]:
        row["feature_exclusion_reason"] = "incomplete_swap_history"
        return row
    try:
        for name in NUMERIC_FEATURES:
            value = Decimal(str(row[name]))
            if not value.is_finite() or value < 0 or not math.isfinite(float(value)):
                raise ValueError()
        counts = [Decimal(str(row[name])) for name in NUMERIC_FEATURES[:3]]
        if any(value != int(value) for value in counts):
            raise ValueError()
        if row["swap_transaction_count"] > row["swap_count"] or not 0 <= row["active_hours"] <= window:
            raise ValueError()
        if (row["swap_count"] == 0) != (row["active_hours"] == 0):
            raise ValueError()
    except (InvalidOperation, TypeError, ValueError, OverflowError):
        row.update(feature_eligible=False, feature_exclusion_reason="invalid_feature_value")
    return row


def file_hash(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
