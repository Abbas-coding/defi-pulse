"""Optional modeling tests; standard-library collection tests need no ML installs."""

import importlib.util
import unittest

AVAILABLE = all(importlib.util.find_spec(p) is not None for p in ("sklearn", "numpy", "pandas", "pyarrow"))


@unittest.skipUnless(AVAILABLE, "Install requirements-baselines.lock for modeling tests")
class BaselineTests(unittest.TestCase):
    def test_scaling_and_encoding_fit_on_training_only(self):
        import numpy as np
        import pandas as pd
        from src.defi_pulse.baselines import fit_baseline
        from src.defi_pulse.data_preparation import FEATURES
        train = pd.DataFrame([[0, 0, 0, 0, "500"], [2, 2, 1, 20, "3000"],
                              [4, 3, 1, 40, "500"], [8, 5, 1, 80, "3000"]], columns=FEATURES)
        fitted = fit_baseline("classification", "logistic_regression", train, np.array([0, 1, 0, 1]))
        scaler = fitted.named_steps["preprocess"].named_transformers_["numeric"].named_steps["scale"]
        expected = np.log1p(train[FEATURES[:4]].astype(float)).mean(axis=0).to_numpy()
        np.testing.assert_allclose(scaler.mean_, expected)
        held = pd.DataFrame([[100000, 100000, 1, 99999999, "unknown"]], columns=FEATURES)
        prediction = fitted.predict_proba(held)[0, 1]
        self.assertTrue(0 <= prediction <= 1)
        np.testing.assert_allclose(scaler.mean_, expected)

    def test_single_class_validation_is_not_reported_as_successful_discrimination(self):
        import numpy as np
        from src.defi_pulse.baselines import classification_metrics
        result = classification_metrics(np.array([0, 0, 0]), np.array([0.1, 0.8, 0.2]))
        self.assertIsNone(result["roc_auc"])
        self.assertIsNone(result["average_precision"])
        self.assertIsNone(result["recall"])
        self.assertEqual(result["confusion_matrix"], [[2, 1], [0, 0]])

    def test_regression_errors_are_percentage_points_and_constant_r2_is_undefined(self):
        import numpy as np
        from src.defi_pulse.baselines import regression_metrics
        result = regression_metrics(np.array([-30.0, -30.0]), np.array([-20.0, -40.0]))
        self.assertEqual(result["mae"], 10)
        self.assertEqual(result["rmse"], 10)
        self.assertIsNone(result["r2"])


if __name__ == "__main__":
    unittest.main()
