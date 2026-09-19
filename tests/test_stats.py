"""Unit tests for stats.py: confidence intervals, substitutability, and cross-price elasticity."""

import math
import unittest
import numpy as np
from stats import (
    compute_substitutability,
    confidence_interval_90,
)


class TestStatsModule(unittest.TestCase):
    """Test suite for statistical functions."""

    def test_confidence_interval_90_known_values(self):
        # Array with identical values: zero variance
        data_const = [10.0, 10.0, 10.0, 10.0]
        res_const = confidence_interval_90(data_const)
        self.assertEqual(res_const["mean"], 10.0)
        self.assertEqual(res_const["std"], 0.0)
        self.assertEqual(res_const["ci_lower"], 10.0)
        self.assertEqual(res_const["ci_upper"], 10.0)

        # Standard array
        data = [10.0, 12.0, 14.0, 16.0, 18.0]
        res = confidence_interval_90(data)
        self.assertAlmostEqual(res["mean"], 14.0)
        self.assertGreater(res["ci_upper"], res["mean"])
        self.assertLess(res["ci_lower"], res["mean"])
        self.assertEqual(res["n"], 5)

    def test_confidence_interval_edge_cases(self):
        # Empty array
        res_empty = confidence_interval_90([])
        self.assertEqual(res_empty["n"], 0)

        # Single element
        res_single = confidence_interval_90([42.0])
        self.assertEqual(res_single["mean"], 42.0)
        self.assertEqual(res_single["ci_lower"], 42.0)
        self.assertEqual(res_single["ci_upper"], 42.0)

    def test_compute_substitutability(self):
        # Baseline: price = 3.00, sales = 50.0, arrivals = 90.0
        # New: price = 3.75 (+25%), other flavor sales = 60.0 (+20%), arrivals = 90.0
        # Normalized Elasticity = (%Δ[Q/arrivals]) / (%ΔP) = 0.20 / 0.25 = 0.80
        metrics = compute_substitutability(
            p_baseline=3.00,
            p_new=3.75,
            q_baseline=50.0,
            q_new=60.0,
            arrivals_baseline=90.0,
            arrivals_new=90.0,
        )
        self.assertAlmostEqual(metrics["pct_change_price"], 0.25)
        self.assertAlmostEqual(metrics["pct_change_rate"], 0.20)
        self.assertAlmostEqual(metrics["elasticity"], 0.80)
        self.assertAlmostEqual(metrics["standard_cross_elasticity"], 0.80)

    def test_compute_substitutability_zero_division(self):
        # If price does not change (%ΔP == 0)
        metrics = compute_substitutability(
            p_baseline=3.00,
            p_new=3.00,
            q_baseline=50.0,
            q_new=55.0,
        )
        self.assertTrue(math.isnan(metrics["elasticity"]))


if __name__ == "__main__":
    unittest.main()
