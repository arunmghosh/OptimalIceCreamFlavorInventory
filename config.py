"""Simulation configuration and parameter defaults for the Ice Cream Truck experiment."""

from typing import Dict, List, Tuple

# Available flavors
FLAVORS: Tuple[str, ...] = ("vanilla", "chocolate", "strawberry")

# Truck & inventory parameters
TOTAL_CAPACITY: int = 300
INITIAL_STOCK_RATIO: Dict[str, float] = {
    "vanilla": 1.0 / 3.0,
    "chocolate": 1.0 / 3.0,
    "strawberry": 1.0 / 3.0,
}

# Cost & pricing parameters (in USD)
UNIT_COST: float = 2.00  # Cost per unit paid to vendor
INITIAL_UNIT_PRICE: float = 3.00  # Default selling price per unit to customer
INITIAL_PRICES: Dict[str, float] = {
    "vanilla": INITIAL_UNIT_PRICE,
    "chocolate": INITIAL_UNIT_PRICE,
    "strawberry": INITIAL_UNIT_PRICE,
}
HOLDING_COST_PER_UNIT: float = 1.00  # Cost per unsold unit per night

# Daily customer traffic distribution
# Normal distribution: mean = 90, std = 10/3 (~99.7% between 80 and 100)
CUSTOMER_TRAFFIC_MEAN: float = 90.0
CUSTOMER_TRAFFIC_STD: float = 10.0 / 3.0
CUSTOMER_TRAFFIC_MIN: int = 80
CUSTOMER_TRAFFIC_MAX: int = 100

# Person parameters
POPULATION_SIZE: int = 150
CUSTOMER_BUDGET: float = 10.00
MIN_FLAVOR_PREFERENCE: float = 0.25

# Ground truth population preference distribution (unknown to vendor initially)
# Must satisfy: x + y + z = 1.0 and min(x, y, z) >= 0.25
DEFAULT_POPULATION_PREFERENCES: Dict[str, float] = {
    "vanilla": 0.45,
    "chocolate": 0.30,
    "strawberry": 0.25,
}

# Simulation duration
TRIAL_DAYS: int = 30

# Experiment parameters
NUM_TRIALS_DEFAULT: int = 100
CONFIDENCE_LEVEL: float = 0.90

# Phase 2 price variations relative to $3.00
# -25%, -15%, -5%, +5%, +15%, +25%
PRICE_VARIATIONS: List[float] = [-0.25, -0.15, -0.05, 0.05, 0.15, 0.25]
