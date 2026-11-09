"""Semantic invariants for research pilot preparation; fixtures are synthetic."""

import unittest

from demos.graph_demo.demo import DemoError, HOUR_FIELDS
from src.defi_pulse.pilot import canonical_pool, endpoint, validate_hours, window_rows


def hour(start: int, tvl: str = "100") -> dict:
    return {**{field: "1" for field in HOUR_FIELDS.split()},
            "periodStartUnix": start, "tvlUSD": tvl}


class PilotTests(unittest.TestCase):
    def test_missing_hour_assumes_no_trades_but_keeps_states_unknown(self):
        rows = window_rows({"id": "pool", "createdAtTimestamp": "2220"}, [], 1)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["assumed_no_trades"])
        self.assertEqual(rows[0]["quality"], "missing")
        self.assertIsNone(rows[0]["tvlUSD"])
        self.assertIsNone(rows[0]["volumeUSD"])

    def test_null_malformed_duplicate_and_out_of_range_are_not_inactivity(self):
        for records in (None, {}, [{}], [hour(0), hour(0)], [hour(3600)]):
            with self.subTest(records=records), self.assertRaises(DemoError):
                validate_hours(records, 0, 3600)
        self.assertEqual(validate_hours([], 0, 3600), [])

    def test_future_bucket_cannot_change_earlier_window(self):
        pool = {"id": "pool", "createdAtTimestamp": "2220"}
        original = [hour(0), hour(3600, "999999")]
        self.assertEqual(window_rows(pool, original, 1), window_rows(pool, original[:1], 1))
        self.assertFalse(window_rows(pool, original, 1)[0]["assumed_no_trades"])

    def test_hour20_and_day8_do_not_change_1h_or_6h(self):
        pool = {"id": "pool", "createdAtTimestamp": "0"}
        history = [hour(0)]
        for cutoff in (1, 6):
            self.assertEqual(window_rows(pool, history, cutoff),
                             window_rows(pool, history + [hour(20 * 3600), hour(8 * 86400)], cutoff))

    def test_endpoint_excludes_boundary_bucket_and_does_not_generate_label(self):
        pool = {"id": "pool", "createdAtTimestamp": "2220"}
        result = endpoint(pool, [hour(0), hour(3600, "0")], 3600)
        self.assertEqual(result["tvl_usd"], "100")
        self.assertIsNone(result["label"])
        self.assertEqual(result["state_age_upper_bound_seconds"], 5820)

    def test_canonical_pool_checks_both_orientations_and_flags_ties(self):
        older = {"id": "a", "createdAtTimestamp": "1"}
        newer = {"id": "b", "createdAtTimestamp": "2"}
        self.assertEqual(canonical_pool({"side0": [newer], "side1": [older]}), ("a", None))
        self.assertIsNotNone(canonical_pool({"side0": [older], "side1": [
            {"id": "b", "createdAtTimestamp": "1"} ]})[1])


if __name__ == "__main__":
    unittest.main()
