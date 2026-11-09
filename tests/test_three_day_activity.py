"""Separate daily intervals and incomplete-history safeguards."""

import unittest

from demos.graph_demo.demo import DemoError
from src.defi_pulse.diagnostic import collect_page
from src.defi_pulse.three_day_activity import aggregate, day_summary, pool_comparison


POOL = {"id": "p", "period": "test", "createdAtTimestamp": "37"}


def event(identity, stamp, amount="2"):
    return {"id": identity, "timestamp": str(stamp), "amountUSD": amount, "transaction": {"id": "tx"}}


class ThreeDayTests(unittest.TestCase):
    def test_boundary_trade_belongs_to_following_day_only(self):
        e = event("a", 37 + 86400)
        with self.assertRaises(DemoError):
            collect_page([e], "", POOL, set())
        self.assertEqual(collect_page([e], "", POOL, set(), 86400, 172800), "a")
        self.assertEqual(day_summary(POOL, 2, [e], True)["active_hours"], 1)

    def test_cumulative_growth_does_not_imply_daily_growth_and_volume_is_separate(self):
        rows = [day_summary(POOL, 1, [event("a", 38), event("b", 39)], True),
                day_summary(POOL, 2, [event("c", 86438, "10")], True),
                day_summary(POOL, 3, [], True)]
        result = pool_comparison(rows)
        self.assertEqual(result["cumulative_swap_count_48h"], 3)
        self.assertFalse(result["swaps_increased_day2_vs_day1"])
        self.assertTrue(result["volume_increased_day2_vs_day1"])
        self.assertEqual(result["first_trading_day"], 1)

    def test_delayed_first_trade_and_incomplete_day_are_distinguished(self):
        rows = [day_summary(POOL, 1, [], True), day_summary(POOL, 2, [], True),
                day_summary(POOL, 3, [event("a", 172838)], True)]
        self.assertEqual(pool_comparison(rows)["first_trading_day"], 3)
        rows[2] = day_summary(POOL, 3, [], False)
        result = pool_comparison(rows)
        self.assertIsNone(result["day3_swap_count"])
        self.assertIsNone(result["cumulative_swap_count_72h"])
        self.assertEqual(result["first_trading_day"], "unknown_incomplete")
        self.assertEqual(aggregate(rows, [result])["days"]["3"]["complete_pools"], 0)

    def test_duplicate_days_fail(self):
        r = day_summary(POOL, 1, [], True)
        with self.assertRaises(DemoError):
            pool_comparison([r, r, r])


if __name__ == "__main__":
    unittest.main()
