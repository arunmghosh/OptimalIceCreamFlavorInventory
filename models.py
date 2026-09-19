"""Data models for Person, customer orders, daily outcomes, and trial results."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

from config import (
    CUSTOMER_BUDGET,
    FLAVORS,
    HOLDING_COST_PER_UNIT,
    MIN_FLAVOR_PREFERENCE,
    UNIT_COST,
)


class Person:
    """A customer with flavor preferences, a budget, and a diminishing returns ordering algorithm."""

    def __init__(
        self,
        preferences: Dict[str, float],
        budget: float = CUSTOMER_BUDGET,
        validate: bool = True,
    ) -> None:
        """Initialize customer with preference distribution and budget.

        Args:
            preferences: Dict mapping flavor names to preference probabilities.
                Must sum to ~1.0 and each value >= 0.25 (when validate=True).
            budget: Total spending budget for the order (default: $10.00).
            validate: Whether to validate preference constraints.
        """
        self.preferences = dict(preferences)
        self.budget = float(budget)
        self.remaining_budget = float(budget)

        if validate:
            self._validate_preferences()

        # Determine favorite flavor (highest value in preference distribution)
        # In case of ties, max selects deterministically
        self.favorite_flavor: str = max(self.preferences, key=lambda f: self.preferences[f])
        favorite_pref = self.preferences[self.favorite_flavor]

        # Preference multipliers:
        # Favorite flavor is assigned 1.0
        # Others are assigned favorite_flavor_pref / other_flavor_pref
        self.multipliers: Dict[str, float] = {}
        for flavor in FLAVORS:
            pref = self.preferences.get(flavor, 0.0)
            if pref <= 0:
                self.multipliers[flavor] = float("inf")
            elif flavor == self.favorite_flavor:
                self.multipliers[flavor] = 1.0
            else:
                self.multipliers[flavor] = favorite_pref / pref

        # Diminishing returns coefficient (ε):
        # Product of the flavor multipliers (x_hat * y_hat * z_hat > 1)
        self.epsilon: float = 1.0
        for m in self.multipliers.values():
            self.epsilon *= m

    def _validate_preferences(self) -> None:
        """Validate that preferences sum to 1 and each is >= MIN_FLAVOR_PREFERENCE."""
        for flavor in FLAVORS:
            val = self.preferences.get(flavor, 0.0)
            if val < MIN_FLAVOR_PREFERENCE - 1e-6:
                raise ValueError(
                    f"Flavor '{flavor}' preference {val:.4f} is below minimum {MIN_FLAVOR_PREFERENCE}"
                )
        total = sum(self.preferences.get(flavor, 0.0) for flavor in FLAVORS)
        if not math.isclose(total, 1.0, rel_tol=1e-4, abs_tol=1e-4):
            raise ValueError(f"Preferences sum to {total:.4f}, expected 1.0")

    def buy_order(
        self,
        prices: Dict[str, float],
        stock: Dict[str, int],
    ) -> Dict[str, int]:
        """Execute the ordering algorithm against the truck's current stock.

        Algorithm steps:
        1. Skew flavor costs with preference multipliers: true_p(f) = price(f) * multiplier(f).
        2. Buy 1 unit of cheapest eligible flavor left in stock:
           - Subtract unit price (not true price) from budget.
           - Decrement truck stock of that flavor.
        3. Adjust true price of that flavor: true_p(f) = true_p(f) * ε.
        4. Repeat steps 2-3 until customer cannot afford true price of any flavor
           or cannot afford unit price (never goes over budget).

        Args:
            prices: Current selling prices per unit for each flavor.
            stock: Mutable inventory dictionary of current truck stock.

        Returns:
            Dict mapping each flavor to number of units purchased in this order.
        """
        purchased: Dict[str, int] = {f: 0 for f in FLAVORS}

        # Step 1: Skew flavor costs with preferences
        true_p: Dict[str, float] = {
            f: prices[f] * self.multipliers[f] for f in FLAVORS
        }

        while True:
            # Step 2: Find all eligible flavors left in stock
            # Condition: stock > 0, budget >= unit price (never over budget)
            eligible: List[str] = [
                f for f in FLAVORS
                if stock.get(f, 0) > 0
                and self.remaining_budget >= prices[f]
                and (not getattr(self, "require_true_price", False) or self.remaining_budget >= true_p[f])
            ]

            if not eligible:
                break

            # Choose the cheapest flavor left in stock (lowest true_p)
            # Tie-breaker: lower unit price, then alphabetical order
            cheapest = min(eligible, key=lambda f: (true_p[f], prices[f], f))

            # Buy 1 unit: subtract unit price from budget, decrement stock
            self.remaining_budget -= prices[cheapest]
            stock[cheapest] -= 1
            purchased[cheapest] += 1

            # Step 3: Adjust true price of that flavor by diminishing returns coefficient ε
            true_p[cheapest] = true_p[cheapest] * self.epsilon

        return purchased


@dataclass
class DailyRecord:
    """Detailed record of a single day of sales, costs, and inventory."""

    day: int
    num_customers: int
    units_sold: Dict[str, int]
    end_of_day_stock: Dict[str, int]
    restock_units: Dict[str, int]
    prices: Dict[str, float]

    @property
    def total_units_sold(self) -> int:
        return sum(self.units_sold.values())

    @property
    def total_unsold_units(self) -> int:
        return sum(self.end_of_day_stock.values())

    @property
    def revenue(self) -> float:
        return sum(self.units_sold[f] * self.prices[f] for f in FLAVORS)

    @property
    def holding_cost(self) -> float:
        return self.total_unsold_units * HOLDING_COST_PER_UNIT

    @property
    def restock_cost(self) -> float:
        return sum(self.restock_units.values()) * UNIT_COST

    @property
    def net_profit(self) -> float:
        return self.revenue - self.holding_cost - self.restock_cost


@dataclass
class TrialRecord:
    """Record of a 30-day trial under a fixed price and stock ratio configuration."""

    trial_id: int
    daily_records: List[DailyRecord] = field(default_factory=list)
    prices: Dict[str, float] = field(default_factory=dict)
    stock_ratios: Dict[str, float] = field(default_factory=dict)

    @property
    def num_days(self) -> int:
        return len(self.daily_records)

    @property
    def total_units_sold(self) -> Dict[str, int]:
        totals = {f: 0 for f in FLAVORS}
        for day in self.daily_records:
            for f in FLAVORS:
                totals[f] += day.units_sold.get(f, 0)
        return totals

    @property
    def total_units_sold_all(self) -> int:
        return sum(self.total_units_sold.values())

    @property
    def average_daily_sales(self) -> Dict[str, float]:
        days = max(1, self.num_days)
        totals = self.total_units_sold
        return {f: totals[f] / days for f in FLAVORS}

    @property
    def average_daily_sales_all(self) -> float:
        days = max(1, self.num_days)
        return self.total_units_sold_all / days

    @property
    def total_revenue(self) -> float:
        return sum(day.revenue for day in self.daily_records)

    @property
    def total_holding_cost(self) -> float:
        return sum(day.holding_cost for day in self.daily_records)

    @property
    def total_restock_cost(self) -> float:
        return sum(day.restock_cost for day in self.daily_records)

    @property
    def total_profit(self) -> float:
        return sum(day.net_profit for day in self.daily_records)

    @property
    def average_daily_profit(self) -> float:
        days = max(1, self.num_days)
        return self.total_profit / days
