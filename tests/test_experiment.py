"""Unit tests for experiment.py: phase flows, demand curve estimation, and stock ratio optimization."""

import unittest
from config import FLAVORS
from experiment import ExperimentOrchestrator


class TestExperimentFlow(unittest.TestCase):
    """Test suite for experimental phases."""

    def test_phases_orchestration_quick(self):
        # Run small-scale trials (2 trials each) to verify end-to-end phase coordination
        orchestrator = ExperimentOrchestrator(base_seed=999)

        # Phase 1
        p1 = orchestrator.run_phase_1(num_trials=2)
        self.assertEqual(p1.num_trials, 2)
        self.assertIn(p1.predicted_favorite, FLAVORS)
        for f in FLAVORS:
            self.assertIn(f, p1.baseline_sales_means)
            self.assertGreater(p1.baseline_sales_means[f], 0)

        # Phase 2
        p2 = orchestrator.run_phase_2(p1, num_trials=1)
        for f in FLAVORS:
            self.assertEqual(len(p2.demand_points[f]), 7)  # 6 variations + 1 baseline
            self.assertIn(f, p2.optimal_pairs)
            self.assertIn(f, p2.fitted_demand_models)
            # Check slope is present
            self.assertIn("slope", p2.fitted_demand_models[f])

        # Phase 3
        p3 = orchestrator.run_phase_3(p1, p2, num_trials=2)
        self.assertEqual(p3.num_trials, 2)
        self.assertAlmostEqual(sum(p3.optimal_stock_ratios.values()), 1.0, places=4)
        for f in FLAVORS:
            self.assertIn(f, p3.optimal_prices)


if __name__ == "__main__":
    unittest.main()
