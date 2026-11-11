"""Protect evaluation data from being used as DS tuning feedback."""

import importlib.util
import unittest

AVAILABLE = all(importlib.util.find_spec(name) for name in ("pandas", "numpy", "scipy"))


@unittest.skipUnless(AVAILABLE, "Optional modeling dependencies required")
class StatisticalTests(unittest.TestCase):
    def fixture(self):
        import pandas as pd
        from src.defi_pulse.data_preparation import NUMERIC_FEATURES
        features = pd.DataFrame([{"pool_address": str(i), "split": "train" if i < 8 else "test",
                                  "feature_eligible": True, "fee_tier": str(i % 2),
                                  **{feature: i for feature in NUMERIC_FEATURES}} for i in range(10)])
        labels = pd.DataFrame([{"pool_address": str(i), "candidate_y_class": i % 2,
                                "structurally_eligible": True} for i in range(10)])
        return features, labels

    def test_evaluation_rows_do_not_change_test_statistics(self):
        import pandas as pd
        from src.defi_pulse.statistical_analysis import training_tests
        features, labels = self.fixture()
        expected = training_tests({1: features}, labels)
        changed = features.copy()
        changed.loc[changed.split == "test", "swap_count"] = 999999
        labels.loc[labels.pool_address.isin(["8", "9"]), "candidate_y_class"] = 1
        actual = training_tests({1: changed}, labels)
        for left, right in zip(expected, actual):
            pd.testing.assert_frame_equal(left, right)

    def test_sparse_chi_square_does_not_present_valid_significance(self):
        from src.defi_pulse.statistical_analysis import training_tests
        features, labels = self.fixture()
        continuous, categorical = training_tests({1: features}, labels)
        self.assertEqual(continuous.family_size.tolist(), [4] * 4)
        self.assertFalse(categorical.iloc[0].assumptions_supported)
        self.assertTrue(categorical.p_value.isna().all())


if __name__ == "__main__":
    unittest.main()
