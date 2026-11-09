"""Historical lookup timing and candidate-label safeguards."""

import unittest

from demos.graph_demo.demo import DemoError
from src.defi_pulse.historical_states import anchor, assess_pair


class HistoricalStateTests(unittest.TestCase):
    def test_exact_timestamp_and_nonadjacent_indexed_blocks_are_distinguished(self):
        before = [{"blockNumber": "10", "timestamp": "100"}]
        after = [{"blockNumber": "13", "timestamp": "136"}]
        self.assertEqual(anchor(before, after, 100, 20)["timing_quality"], "exact_cutoff_timestamp")
        r = anchor(before, after, 115, 20)
        self.assertEqual(r["cutoff_gap_seconds"], 15)
        self.assertEqual(r["timing_quality"], "earlier_indexed_transaction_block")

    def test_missing_future_or_unbracketed_transactions_fail(self):
        before = [{"blockNumber": "10", "timestamp": "100"}]
        after = [{"blockNumber": "11", "timestamp": "112"}]
        for a, b, cutoff in ((before, [], 100), (None, after, 100), (before, after, 113)):
            with self.assertRaises(DemoError):
                anchor(a, b, cutoff, 20)

    def test_threshold_precision_zero_policies_and_timing(self):
        a = {"tvl_usd": "100", "timing_quality": "exact_cutoff_timestamp"}
        b = {"tvl_usd": "20", "timing_quality": "exact_cutoff_timestamp"}
        self.assertEqual(assess_pair(a, b)[0], 1)
        self.assertEqual(assess_pair(a, {**b, "tvl_usd": "20.000000000000000001"})[0], 0)
        self.assertIsNone(assess_pair(a, {**b, "tvl_usd": "0"})[0])
        self.assertIsNone(assess_pair({**a, "tvl_usd": "0"}, b)[0])
        self.assertIsNone(assess_pair(a, {**b, "timing_quality": "earlier_indexed_transaction_block"})[0])
        self.assertIsNone(assess_pair(a, {**b, "tvl_usd": "NaN"})[0])


if __name__ == "__main__":
    unittest.main()
