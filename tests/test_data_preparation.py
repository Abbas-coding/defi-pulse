"""Target precision, embargo, and feature leakage invariants."""

import unittest
from datetime import datetime, timezone

from demos.graph_demo.demo import DemoError
from src.defi_pulse.data_preparation import chronological_splits, feature_row, targets

WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"


def pool(index=1, created=0):
    return {"id": str(index), "createdAtTimestamp": str(created), "feeTier": "3000",
            "token0": {"id": WETH}, "token1": {"id": f"token{index}"}}


def state(endpoint, value):
    stamp = 86400 if endpoint == "hour24" else 8 * 86400
    return {"pool_address": "1", "endpoint": endpoint, "tvl_usd": value,
            "requested_as_of_utc": datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
            "block_timestamp_utc": datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
            "timing_quality": "exact_cutoff_timestamp", "cutoff_gap_seconds": 0,
            "block_number": 10 if endpoint == "hour24" else 20,
            "quality": "historical_indexed_state", "token0_balance": "1", "token1_balance": "1"}


class PreparationTests(unittest.TestCase):
    def test_exact_thirty_percent_boundary_and_regression_units(self):
        a = state("hour24", "100")
        positive = targets(pool(), a, state("day8", "70"), 30)
        self.assertEqual(positive["candidate_y_class"], 1)
        self.assertEqual(float(positive["candidate_y_reg"]), -30)
        self.assertIsNone(positive["final_y_class"])
        near = targets(pool(), a, state("day8", "70.000000000000000000000000000000000000001"), 30)
        self.assertEqual(near["candidate_y_class"], 0)
        gain = targets(pool(), a, state("day8", "120"), 30)
        self.assertEqual(float(gain["candidate_y_reg"]), 20)

    def test_invalid_missing_zero_and_future_states_do_not_become_targets(self):
        a, b = state("hour24", "100"), state("day8", "70")
        for bad_left, bad_right in (({**a, "tvl_usd": "0"}, b), (a, {**b, "tvl_usd": "0"}),
                                    (a, {**b, "tvl_usd": "NaN"}), (a, {}),
                                    (a, {**b, "cutoff_gap_seconds": 12}),
                                    (a, {**b, "block_number": 31})):
            result = targets(pool(), bad_left, bad_right, 30)
            self.assertFalse(result["structurally_eligible"])
            self.assertIsNone(result["candidate_y_class"])
            self.assertIsNone(result["candidate_y_reg"])

    def test_extreme_valid_change_is_preserved_and_flagged_not_trimmed(self):
        result = targets(pool(), state("hour24", "0.1"), state("day8", "100"), 30)
        self.assertTrue(result["structurally_eligible"])
        self.assertEqual(float(result["candidate_y_reg"]), 99900)
        self.assertEqual(result["candidate_y_class"], 0)
        self.assertIn("gain_over_1000_percent_untrimmed", result["audit_flags"])

    def test_splits_are_fixed_before_labels_and_respect_eight_day_embargo(self):
        pools = [pool(i, i * 86400) for i in range(100)]
        result = chronological_splits(pools)
        for left, right in (("train", "validation"), ("validation", "test")):
            a = [r["created_at_unix"] for r in result if r["split"] == left]
            b = [r["created_at_unix"] for r in result if r["split"] == right]
            self.assertLessEqual(max(a) + 8 * 86400, min(b))
        self.assertEqual(result, chronological_splits([{**p, "future_label": 1} for p in pools]))
        self.assertEqual(sum(r["nominal_split"] == "train" for r in result), 70)
        self.assertTrue(any(r["split"] == "embargo" for r in result))
        with self.assertRaises(DemoError):
            chronological_splits(pools + [pools[0]])
        ninety = chronological_splits(pools[:90])
        self.assertEqual(sum(r["nominal_split"] == "train" for r in ninety), 63)

    def test_feature_whitelist_excludes_later_windows_and_targets(self):
        summary = {"pool_address": "1", "swap_history_complete": True,
                   "swap_count_1h": 2, "swap_transaction_count_1h": 1,
                   "active_elapsed_hours_1h": 1, "swap_volume_usd_1h": "4"}
        first = feature_row(pool(), summary, 1)
        changed = feature_row(pool(), {**summary, "swap_count_24h": 999, "tvl_day8": 999,
                                      "y_reg": 999, "future_label": 1}, 1)
        self.assertEqual(first, changed)
        incomplete = feature_row(pool(), {**summary, "swap_history_complete": False}, 1)
        self.assertFalse(incomplete["feature_eligible"])


if __name__ == "__main__":
    unittest.main()
