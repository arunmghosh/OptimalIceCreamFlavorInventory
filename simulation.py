"""Discrete-event simulation engine for the Ice Cream Truck inventory experiment."""

from typing import Dict, List, Optional
import numpy as np

from config import (
    CONFIDENCE_LEVEL,
    CUSTOMER_BUDGET,
    CUSTOMER_TRAFFIC_MAX,
    CUSTOMER_TRAFFIC_MEAN,
    CUSTOMER_TRAFFIC_MIN,
    CUSTOMER_TRAFFIC_STD,
    DEFAULT_POPULATION_PREFERENCES,
    FLAVORS,
    INITIAL_PRICES,
    INITIAL_STOCK_RATIO,
    MIN_FLAVOR_PREFERENCE,
    POPULATION_SIZE,
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


def generate_population(
    size: int = POPULATION_SIZE,
    population_preferences: Optional[Dict[str, float]] = None,
    seed: Optional[int] = None,
) -> List[Person]:
    """Generate a fixed population of individuals with diverse flavor preferences.

    Preferences follow the underlying population distribution, sum to 1.0, and
    strictly satisfy min(x, y, z) >= MIN_FLAVOR_PREFERENCE (0.25).

    Args:
        size: Number of people in the population (default: 150).
        population_preferences: True underlying mean population preferences.
        seed: Random seed for reproducible population generation.

    Returns:
        List of Person instances with fixed preference distributions.
    """
    rng = np.random.default_rng(seed)
    pop_mean = dict(population_preferences or DEFAULT_POPULATION_PREFERENCES)

    # Excess above 0.25 threshold
    excess_total = 1.0 - (MIN_FLAVOR_PREFERENCE * len(FLAVORS))
    weights = [max(1e-4, pop_mean[f] - 0.24) for f in FLAVORS]
    alpha = np.array(weights) * 8.0  # Controls dispersion around mean

    population: List[Person] = []
    for _ in range(size):
        d = rng.dirichlet(alpha)
        prefs = {
            f: float(MIN_FLAVOR_PREFERENCE + d[i] * excess_total)
            for i, f in enumerate(FLAVORS)
        }
        # Normalize to ensure exact 1.0 sum
        s = sum(prefs.values())
        norm_prefs = {f: p / s for f, p in prefs.items()}
        population.append(Person(norm_prefs, budget=CUSTOMER_BUDGET))

    return population


class IceCreamTruckSimulation:
    """Manages a single multi-day trial of the ice cream truck inventory system."""

    def __init__(
        self,
        prices: Optional[Dict[str, float]] = None,
        stock_ratios: Optional[Dict[str, float]] = None,
        population_preferences: Optional[Dict[str, float]] = None,
        population: Optional[List[Person]] = None,
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
            population: Fixed population of individuals to sample daily arrivals from.
            total_capacity: Total storage capacity of truck (default: 300).
            trial_days: Number of days to simulate (default: 30).
            heterogeneous_customers: Legacy flag for continuous customer resampling.
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

        # Fixed population of people to sample daily foot traffic from
        if population is not None:
            self.population = population
        else:
            self.population = generate_population(
                size=POPULATION_SIZE,
                population_preferences=self.population_preferences,
                seed=seed,
            )

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

        # Sample num_customers individuals without replacement from the fixed population
        sample_size = min(num_customers, len(self.population))
        cust_indices = self.rng.choice(len(self.population), size=sample_size, replace=False)

        for idx in cust_indices:
            # Check if truck has any inventory left
            if sum(self.inventory.values()) <= 0:
                break

            # Fresh person instance with this individual's fixed preferences and full budget
            person = Person(
                self.population[idx].preferences,
                budget=CUSTOMER_BUDGET,
            )

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
