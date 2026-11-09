"""Event counting, completeness, and deterministic diagnostic sampling."""

import unittest

from demos.graph_demo.demo import DemoError
from src.defi_pulse.diagnostic import activity, collect_page, rank


POOL = {"id": "pool", "createdAtTimestamp": "0", "period": "test",
        "token0": {"id": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"},
        "token1": {"id": "token", "symbol": "TEST"}}


def event(identity: str, timestamp: int, transaction: str = "tx") -> dict:
    return {"id": identity, "timestamp": str(timestamp), "amountUSD": "2.50",
            "transaction": {"id": transaction}}


class DiagnosticTests(unittest.TestCase):
    def test_trade_count_and_transaction_count_differ_and_cutoffs_exclude_future(self):
        swaps = [event("a", 1), event("b", 3599), event("c", 3600, "other"), event("d", 21600)]
        result = activity(POOL, swaps, [], True)
        self.assertEqual(result["swap_count_1h"], 2)
        self.assertEqual(result["swap_transaction_count_1h"], 1)
        self.assertEqual(result["swap_count_6h"], 3)
        self.assertEqual(result["swap_count_24h"], 4)
        self.assertEqual(result["swap_volume_usd_1h"], "5.00")
        self.assertEqual(result["active_elapsed_hours_24h"], 3)
        self.assertEqual(result["absent_completed_buckets_with_swaps"], 3)

    def test_incomplete_history_never_looks_like_exact_zero_activity(self):
        result = activity(POOL, [], [], False)
        self.assertIsNone(result["swap_count_24h"])
        self.assertEqual(result["swap_count_lower_bound_24h"], 0)
        self.assertIsNone(result["swap_volume_usd_24h"])
        self.assertEqual(activity(POOL, [], [], True)["swap_count_24h"], 0)

    def test_page_cursor_rejects_duplicates_wrong_order_and_outside_window(self):
        seen = set()
        self.assertEqual(collect_page([event("a", 1), event("b", 2)], "", POOL, seen), "b")
        for page in ([event("b", 3)], [event("d", 3), event("c", 4)], [event("z", 86400)], None):
            with self.subTest(page=page), self.assertRaises(DemoError):
                collect_page(page, "b", POOL, set(seen))

    def test_activity_does_not_change_sample_rank(self):
        self.assertEqual(rank(POOL), rank({**POOL, "totalValueLockedUSD": "999", "future_label": 1}))


if __name__ == "__main__":
    unittest.main()
