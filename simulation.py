"""Discrete-event simulation engine for the Ice Cream Truck inventory experiment."""

from typing import Dict, List, Optional
import numpy as np

from config import (
    CONFIDENCE_LEVEL,
    CUSTOMER_TRAFFIC_MAX,
    CUSTOMER_TRAFFIC_MEAN,
    CUSTOMER_TRAFFIC_MIN,
    CUSTOMER_TRAFFIC_STD,
    DEFAULT_POPULATION_PREFERENCES,
    FLAVORS,
    INITIAL_PRICES,
    INITIAL_STOCK_RATIO,
    MIN_FLAVOR_PREFERENCE,
    TOTAL_CAPACITY,
    TRIAL_DAYS,
)
from models import DailyRecord, Person, TrialRecord


def allocate_capacity(
    total_capacity: int,
    stock_ratios: Dict[str, float],
) -> Dict[str, int]:
    """Allocate integer unit capacities for each flavor based on stock ratios.

    Guarantees that the sum of allocated units strictly equals total_capacity.

    Args:
        total_capacity: Total maximum capacity of the truck (e.g. 300).
        stock_ratios: Proportions of capacity for each flavor (must sum to ~1.0).

    Returns:
        Dict mapping flavor name to integer target capacity.
    """
    raw_alloc = {f: total_capacity * stock_ratios[f] for f in FLAVORS}
    int_alloc = {f: int(np.floor(raw_alloc[f])) for f in FLAVORS}
    remainder = total_capacity - sum(int_alloc.values())

    # Distribute remaining fractional units by highest fractional part
    fractions = sorted(
        FLAVORS,
        key=lambda f: raw_alloc[f] - int_alloc[f],
        reverse=True,
    )
    for i in range(remainder):
        int_alloc[fractions[i % len(fractions)]] += 1

    return int_alloc


def sample_customer_preferences(
    population_mean: Dict[str, float],
    rng: np.random.Generator,
    heterogeneous: bool = False,
) -> Dict[str, float]:
    """Sample a customer's flavor preference distribution.

    Args:
        population_mean: Base population preference distribution.
        rng: Numpy random generator instance.
        heterogeneous: If True, draws individual preferences with Dirichlet perturbation
            ensuring min preference >= MIN_FLAVOR_PREFERENCE and sum == 1.0.
            If False, returns population_mean directly.

    Returns:
        Dict mapping flavor name to preference probability.
    """
    if not heterogeneous:
        return dict(population_mean)

    # Sample from Dirichlet distribution centered around population mean
    # Excess above minimum 0.25 is distributed via Dirichlet
    excess_weights = np.array([
        max(1e-4, population_mean[f] - MIN_FLAVOR_PREFERENCE) for f in FLAVORS
    ])
    concentration = 15.0  # Controls dispersion around mean
    alpha = excess_weights * concentration
    alpha = np.maximum(alpha, 0.5)

    excess_sample = rng.dirichlet(alpha)
    total_excess = 1.0 - (MIN_FLAVOR_PREFERENCE * len(FLAVORS))
    prefs = {}
    for i, f in enumerate(FLAVORS):
        prefs[f] = float(MIN_FLAVOR_PREFERENCE + excess_sample[i] * total_excess)

    # Normalize to avoid floating point drift
    s = sum(prefs.values())
    return {f: p / s for f, p in prefs.items()}


class IceCreamTruckSimulation:
    """Manages a single multi-day trial of the ice cream truck inventory system."""

    def __init__(
        self,
        prices: Optional[Dict[str, float]] = None,
        stock_ratios: Optional[Dict[str, float]] = None,
        population_preferences: Optional[Dict[str, float]] = None,
        total_capacity: int = TOTAL_CAPACITY,
        trial_days: int = TRIAL_DAYS,
        heterogeneous_customers: bool = False,
        seed: Optional[int] = None,
    ) -> None:
        """Initialize simulation with parameters.

        Args:
            prices: Unit selling price for each flavor (default: $3.00 each).
            stock_ratios: Proportion of total capacity for each flavor (default: 1/3 each).
            population_preferences: True underlying population preferences.
            total_capacity: Total storage capacity of truck (default: 300).
            trial_days: Number of days to simulate (default: 30).
            heterogeneous_customers: Whether individual customers have personal variations.
            seed: Optional random seed for reproducibility.
        """
        self.prices = dict(prices if prices is not None else INITIAL_PRICES)
        self.stock_ratios = dict(
            stock_ratios if stock_ratios is not None else INITIAL_STOCK_RATIO
        )
        self.population_preferences = dict(
            population_preferences
            if population_preferences is not None
            else DEFAULT_POPULATION_PREFERENCES
        )
        self.total_capacity = total_capacity
        self.trial_days = trial_days
        self.heterogeneous_customers = heterogeneous_customers
        self.rng = np.random.default_rng(seed)

        # Target inventory allocation per flavor
        self.target_stock = allocate_capacity(self.total_capacity, self.stock_ratios)

        # Initial inventory starts fully stocked to target proportions
        self.inventory: Dict[str, int] = dict(self.target_stock)

    def draw_daily_traffic(self) -> int:
        """Draw number of customer orders for the day from normal distribution.

        Mean = 90, Std = 10/3, clipped to [80, 100].
        """
        draw = self.rng.normal(CUSTOMER_TRAFFIC_MEAN, CUSTOMER_TRAFFIC_STD)
        traffic = int(np.round(np.clip(draw, CUSTOMER_TRAFFIC_MIN, CUSTOMER_TRAFFIC_MAX)))
        return traffic

    def simulate_day(self, day_num: int) -> DailyRecord:
        """Simulate a single operating day for the truck.

        Args:
            day_num: Current day index (1-indexed).

        Returns:
            DailyRecord of sales, end-of-day stock, costs, and profit.
        """
        num_customers = self.draw_daily_traffic()
        daily_sales: Dict[str, int] = {f: 0 for f in FLAVORS}

        for _ in range(num_customers):
            # Check if truck has any inventory left
            if sum(self.inventory.values()) <= 0:
                break

            # Customer arrives with preferences
            cust_prefs = sample_customer_preferences(
                self.population_preferences,
                self.rng,
                heterogeneous=self.heterogeneous_customers,
            )
            person = Person(cust_prefs)

            # Customer purchases according to ordering algorithm
            order = person.buy_order(self.prices, self.inventory)
            for f, qty in order.items():
                daily_sales[f] += qty

        # Day ends:
        # Snapshot end-of-day unsold stock before restocking
        end_of_day_stock = dict(self.inventory)

        # Overnight restocking:
        # Refill stock back to target capacity according to fixed stock ratio
        restock_units: Dict[str, int] = {}
        for f in FLAVORS:
            needed = max(0, self.target_stock[f] - self.inventory[f])
            restock_units[f] = needed
            self.inventory[f] += needed

        record = DailyRecord(
            day=day_num,
            num_customers=num_customers,
            units_sold=daily_sales,
            end_of_day_stock=end_of_day_stock,
            restock_units=restock_units,
            prices=dict(self.prices),
        )
        return record

    def run_trial(self, trial_id: int = 1) -> TrialRecord:
        """Execute the full 30-day trial and return trial record.

        Args:
            trial_id: Identifier for this trial.

        Returns:
            TrialRecord aggregating all 30 days.
        """
        # Reset inventory to full target stock at start of trial
        self.inventory = dict(self.target_stock)
        daily_records: List[DailyRecord] = []

        for day in range(1, self.trial_days + 1):
            daily_records.append(self.simulate_day(day))

        return TrialRecord(
            trial_id=trial_id,
            daily_records=daily_records,
            prices=dict(self.prices),
            stock_ratios=dict(self.stock_ratios),
        )
