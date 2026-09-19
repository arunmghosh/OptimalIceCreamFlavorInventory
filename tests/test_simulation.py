"""Unit tests for simulation.py: inventory allocation, traffic, and trial mechanics."""

import unittest
from config import FLAVORS, TOTAL_CAPACITY
from simulation import IceCreamTruckSimulation, allocate_capacity


class TestSimulation(unittest.TestCase):
    """Test suite for simulation engine and inventory logic."""

    def test_allocate_capacity_exact_sum(self):
        # Equal ratios
        ratios_equal = {"vanilla": 1/3, "chocolate": 1/3, "strawberry": 1/3}
        alloc = allocate_capacity(300, ratios_equal)
        self.assertEqual(sum(alloc.values()), 300)
        self.assertEqual(alloc["vanilla"], 100)
        self.assertEqual(alloc["chocolate"], 100)
        self.assertEqual(alloc["strawberry"], 100)

        # Uneven ratios requiring remainder resolution
        ratios_uneven = {"vanilla": 0.50, "chocolate": 0.30, "strawberry": 0.20}
        alloc2 = allocate_capacity(300, ratios_uneven)
        self.assertEqual(sum(alloc2.values()), 300)
        self.assertEqual(alloc2["vanilla"], 150)
        self.assertEqual(alloc2["chocolate"], 90)
        self.assertEqual(alloc2["strawberry"], 60)

        # Non-round capacity
        ratios_odd = {"vanilla": 0.40, "chocolate": 0.35, "strawberry": 0.25}
        alloc3 = allocate_capacity(250, ratios_odd)
        self.assertEqual(sum(alloc3.values()), 250)

    def test_simulation_day_invariants(self):
        sim = IceCreamTruckSimulation(trial_days=1, seed=42)
        day_record = sim.simulate_day(1)

        # Customer traffic within reasonable bounds
        self.assertGreaterEqual(day_record.num_customers, 70)
        self.assertLessEqual(day_record.num_customers, 110)

        # Total capacity conserved: units_sold + end_of_day_stock == target_stock
        for f in FLAVORS:
            sold = day_record.units_sold[f]
            left = day_record.end_of_day_stock[f]
            target = sim.target_stock[f]
            self.assertEqual(sold + left, target)
            self.assertEqual(day_record.restock_units[f], sold)

        # Truck refilled to target capacity overnight
        self.assertEqual(sum(sim.inventory.values()), TOTAL_CAPACITY)

    def test_trial_duration_30_days(self):
        sim = IceCreamTruckSimulation(trial_days=30, seed=123)
        trial = sim.run_trial(trial_id=1)

        self.assertEqual(trial.num_days, 30)
        self.assertEqual(len(trial.daily_records), 30)
        self.assertGreater(trial.total_units_sold_all, 0)
        self.assertIsInstance(trial.average_daily_profit, float)


if __name__ == "__main__":
    unittest.main()
