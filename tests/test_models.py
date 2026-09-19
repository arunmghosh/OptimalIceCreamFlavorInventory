"""Unit tests for models.py: Person, customer ordering, DailyRecord, TrialRecord."""

import unittest
from config import CUSTOMER_BUDGET, FLAVORS
from models import DailyRecord, Person, TrialRecord


class TestPersonModel(unittest.TestCase):
    """Test suite for Person customer modeling and ordering logic."""

    def test_person_initialization_valid(self):
        prefs = {"vanilla": 0.50, "chocolate": 0.25, "strawberry": 0.25}
        person = Person(prefs, budget=10.0)
        self.assertEqual(person.favorite_flavor, "vanilla")
        self.assertEqual(person.multipliers["vanilla"], 1.0)
        self.assertEqual(person.multipliers["chocolate"], 2.0)
        self.assertEqual(person.multipliers["strawberry"], 2.0)
        # Epsilon = product of multipliers = 1 * 2 * 2 = 4.0
        self.assertAlmostEqual(person.epsilon, 4.0)

    def test_person_validation_errors(self):
        # Preference below 0.25
        with self.assertRaises(ValueError):
            Person({"vanilla": 0.60, "chocolate": 0.20, "strawberry": 0.20})

        # Preferences do not sum to 1.0
        with self.assertRaises(ValueError):
            Person({"vanilla": 0.30, "chocolate": 0.30, "strawberry": 0.30})

    def test_person_order_diminishing_returns(self):
        """Verify that after buying a unit, true price is multiplied by epsilon (> 1), causing diversification."""
        prefs = {"vanilla": 0.50, "chocolate": 0.25, "strawberry": 0.25}
        person = Person(prefs, budget=10.0)
        prices = {"vanilla": 3.0, "chocolate": 3.0, "strawberry": 3.0}
        stock = {"vanilla": 10, "chocolate": 10, "strawberry": 10}

        order = person.buy_order(prices, stock)
        # 1st: vanilla (true_p 3.0 vs 6.0), then vanilla true_p becomes 3*4 = 12.0
        # 2nd: chocolate or strawberry (true_p 6.0 < 12.0), say chocolate, budget remaining = 4.0
        # 3rd: budget is 4.0, unit price is 3.0, true prices are:
        #   vanilla: 12.0 (> 4.0, cannot afford true price)
        #   chocolate: 6*4 = 24.0 (> 4.0, cannot afford true price)
        #   strawberry: 6.0 (> 4.0, cannot afford true price)
        # Therefore customer stops after 2 units!
        total_bought = sum(order.values())
        self.assertEqual(total_bought, 3)
        self.assertEqual(order["vanilla"], 1)
        self.assertEqual(order["chocolate"], 1)
        self.assertEqual(order["strawberry"], 1)
        self.assertEqual(person.remaining_budget, 1.0)

    def test_person_never_exceeds_budget(self):
        prefs = {"vanilla": 0.40, "chocolate": 0.35, "strawberry": 0.25}
        person = Person(prefs, budget=5.0)
        prices = {"vanilla": 3.0, "chocolate": 3.0, "strawberry": 3.0}
        stock = {"vanilla": 10, "chocolate": 10, "strawberry": 10}

        order = person.buy_order(prices, stock)
        total_spent = sum(order[f] * prices[f] for f in FLAVORS)
        self.assertLessEqual(total_spent, 5.0)
        self.assertGreaterEqual(person.remaining_budget, 0.0)

    def test_person_substitutes_when_favorite_out_of_stock(self):
        prefs = {"vanilla": 0.50, "chocolate": 0.25, "strawberry": 0.25}
        person = Person(prefs, budget=10.0)
        prices = {"vanilla": 3.0, "chocolate": 3.0, "strawberry": 3.0}
        # Vanilla is out of stock!
        stock = {"vanilla": 0, "chocolate": 10, "strawberry": 10}

        order = person.buy_order(prices, stock)
        self.assertEqual(order["vanilla"], 0)
        self.assertGreater(order["chocolate"] + order["strawberry"], 0)


class TestRecordModels(unittest.TestCase):
    """Test suite for DailyRecord and TrialRecord accounting."""

    def test_daily_record_accounting(self):
        record = DailyRecord(
            day=1,
            num_customers=90,
            units_sold={"vanilla": 40, "chocolate": 30, "strawberry": 20},
            end_of_day_stock={"vanilla": 60, "chocolate": 70, "strawberry": 80},
            restock_units={"vanilla": 40, "chocolate": 30, "strawberry": 20},
            prices={"vanilla": 3.0, "chocolate": 3.0, "strawberry": 3.0},
        )
        self.assertEqual(record.total_units_sold, 90)
        self.assertEqual(record.total_unsold_units, 210)
        self.assertEqual(record.revenue, 270.0)  # 90 * 3.00
        self.assertEqual(record.holding_cost, 210.0)  # 210 * 1.00
        self.assertEqual(record.restock_cost, 180.0)  # 90 * 2.00
        self.assertEqual(record.net_profit, 270.0 - 210.0 - 180.0)  # -120.0

    def test_trial_record_aggregation(self):
        d1 = DailyRecord(
            day=1,
            num_customers=90,
            units_sold={"vanilla": 30, "chocolate": 30, "strawberry": 30},
            end_of_day_stock={"vanilla": 70, "chocolate": 70, "strawberry": 70},
            restock_units={"vanilla": 30, "chocolate": 30, "strawberry": 30},
            prices={"vanilla": 3.0, "chocolate": 3.0, "strawberry": 3.0},
        )
        d2 = DailyRecord(
            day=2,
            num_customers=90,
            units_sold={"vanilla": 40, "chocolate": 30, "strawberry": 20},
            end_of_day_stock={"vanilla": 60, "chocolate": 70, "strawberry": 80},
            restock_units={"vanilla": 40, "chocolate": 30, "strawberry": 20},
            prices={"vanilla": 3.0, "chocolate": 3.0, "strawberry": 3.0},
        )
        trial = TrialRecord(trial_id=1, daily_records=[d1, d2])
        self.assertEqual(trial.num_days, 2)
        self.assertEqual(trial.total_units_sold["vanilla"], 70)
        self.assertEqual(trial.average_daily_sales["vanilla"], 35.0)
        self.assertEqual(trial.average_daily_sales_all, 90.0)


if __name__ == "__main__":
    unittest.main()
