"""Experiment orchestration for Phase 1, Phase 2, and Phase 3 of the Ice Cream Truck study."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from config import (
    CONFIDENCE_LEVEL,
    DEFAULT_POPULATION_PREFERENCES,
    FLAVORS,
    INITIAL_PRICES,
    INITIAL_STOCK_RATIO,
    INITIAL_UNIT_PRICE,
    POPULATION_SIZE,
    PRICE_VARIATIONS,
    TOTAL_CAPACITY,
    UNIT_COST,
)
from models import TrialRecord
from simulation import IceCreamTruckSimulation, generate_population
from stats import (
    aggregate_trials_summary,
    compute_substitutability,
    confidence_interval_90,
)


@dataclass
class DemandPoint:
    """A price-quantity empirical observation for a single flavor."""

    price: float
    mean_quantity: float
    revenue: float
    individual_profit: float


@dataclass
class Phase1Result:
    """Results from Phase 1 initial state study."""

    num_trials: int
    trials: List[TrialRecord]
    summary: Dict[str, Any]
    baseline_sales_means: Dict[str, float]
    baseline_arrivals_mean: float
    predicted_favorite: str


@dataclass
class Phase2Result:
    """Results from Phase 2 price perturbation and elasticity analysis."""

    configurations: Dict[str, Any]
    demand_points: Dict[str, List[DemandPoint]]
    substitutability_cis: Dict[str, Any]
    optimal_pairs: Dict[str, DemandPoint]
    fitted_demand_models: Dict[str, Dict[str, float]]


@dataclass
class Phase3Result:
    """Results from Phase 3 optimal configuration validation."""

    optimal_prices: Dict[str, float]
    optimal_stock_ratios: Dict[str, float]
    num_trials: int
    trials: List[TrialRecord]
    summary: Dict[str, Any]
    phase1_profit_mean: float
    phase2_max_profit_mean: float
    is_success: bool


class ExperimentOrchestrator:
    """Coordinates and executes the three experimental phases."""

    def __init__(
        self,
        population_preferences: Optional[Dict[str, float]] = None,
        heterogeneous_customers: bool = False,
        base_seed: Optional[int] = 42,
    ) -> None:
        self.population_preferences = dict(
            population_preferences or DEFAULT_POPULATION_PREFERENCES
        )
        self.heterogeneous_customers = heterogeneous_customers
        self.base_seed = base_seed

        # Generate a true fixed population of 150 people with preferences following the unknown distribution
        self.population = generate_population(
            size=POPULATION_SIZE,
            population_preferences=self.population_preferences,
            seed=self.base_seed,
        )

    def run_phase_1(
        self,
        num_trials: int = 100,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> Phase1Result:
        """Execute Phase 1: 100 trials of the baseline initial state.

        Equal stock proportions (1/3 each), fixed $3.00 unit prices.
        """
        trials: List[TrialRecord] = []
        for i in range(num_trials):
            seed = None if self.base_seed is None else (self.base_seed + i)
            sim = IceCreamTruckSimulation(
                prices=INITIAL_PRICES,
                stock_ratios=INITIAL_STOCK_RATIO,
                population_preferences=self.population_preferences,
                population=self.population,
                heterogeneous_customers=self.heterogeneous_customers,
                seed=seed,
            )
            trials.append(sim.run_trial(trial_id=i + 1))
            if progress_cb:
                progress_cb(i + 1, num_trials)

        summary = aggregate_trials_summary(trials)
        baseline_means = {f: summary["raw_means"][f] for f in FLAVORS}
        baseline_arrivals = summary.get("raw_arrivals_mean", 90.0)
        predicted_favorite = summary["predicted_favorite"]

        return Phase1Result(
            num_trials=num_trials,
            trials=trials,
            summary=summary,
            baseline_sales_means=baseline_means,
            baseline_arrivals_mean=baseline_arrivals,
            predicted_favorite=predicted_favorite,
        )

    def run_phase_2(
        self,
        phase1_result: Phase1Result,
        num_trials: int = 100,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> Phase2Result:
        """Execute Phase 2: Price variations, substitutability, and demand curve estimation."""
        baseline_means = phase1_result.baseline_sales_means
        configurations_data: Dict[str, Any] = {}
        substitutability_cis: Dict[str, Any] = {}

        # 7 data points per flavor (6 price variations + 1 baseline $3.00)
        demand_points: Dict[str, List[DemandPoint]] = {f: [] for f in FLAVORS}

        # Seed the baseline $3.00 point from Phase 1
        for f in FLAVORS:
            p = INITIAL_UNIT_PRICE
            q = baseline_means[f]
            rev = p * q
            profit = (p - UNIT_COST) * q
            demand_points[f].append(
                DemandPoint(
                    price=p,
                    mean_quantity=q,
                    revenue=rev,
                    individual_profit=profit,
                )
            )

        total_configs = len(FLAVORS) * len(PRICE_VARIATIONS)
        config_idx = 0

        for changed_flavor in FLAVORS:
            substitutability_cis[changed_flavor] = {}
            for pct_change in PRICE_VARIATIONS:
                config_idx += 1
                new_price = round(INITIAL_UNIT_PRICE * (1.0 + pct_change), 2)
                prices = dict(INITIAL_PRICES)
                prices[changed_flavor] = new_price

                config_key = f"{changed_flavor}_{pct_change:+.2f}"
                trials: List[TrialRecord] = []

                # Track per-trial substitutability for the other two flavors
                other_flavors = [f for f in FLAVORS if f != changed_flavor]
                sub_per_flavor: Dict[str, List[float]] = {of: [] for of in other_flavors}

                for t_idx in range(num_trials):
                    trial_seed = (
                        None
                        if self.base_seed is None
                        else (self.base_seed + 1000 + config_idx * 1000 + t_idx)
                    )
                    sim = IceCreamTruckSimulation(
                        prices=prices,
                        stock_ratios=INITIAL_STOCK_RATIO,
                        population_preferences=self.population_preferences,
                        population=self.population,
                        heterogeneous_customers=self.heterogeneous_customers,
                        seed=trial_seed,
                    )
                    trial = sim.run_trial(trial_id=t_idx + 1)
                    trials.append(trial)

                    # Compute elasticity for each other flavor in this trial
                    trial_sales = trial.average_daily_sales
                    trial_arrivals = trial.average_daily_arrivals
                    for of in other_flavors:
                        q_other = trial_sales[of]
                        q_base = baseline_means[of]
                        sub_metrics = compute_substitutability(
                            p_baseline=INITIAL_UNIT_PRICE,
                            p_new=new_price,
                            q_baseline=q_base,
                            q_new=q_other,
                            arrivals_baseline=phase1_result.baseline_arrivals_mean,
                            arrivals_new=trial_arrivals,
                        )
                        sub_val = sub_metrics["elasticity"]
                        if not np.isnan(sub_val):
                            sub_per_flavor[of].append(sub_val)

                summary = aggregate_trials_summary(trials)
                configurations_data[config_key] = {
                    "changed_flavor": changed_flavor,
                    "pct_change": pct_change,
                    "new_price": new_price,
                    "summary": summary,
                }

                # 90% CIs for substitutability
                substitutability_cis[changed_flavor][f"{pct_change:+.2f}"] = {
                    of: confidence_interval_90(sub_per_flavor[of])
                    for of in other_flavors
                }

                # Record demand point for changed flavor
                q_mean = summary["raw_means"][changed_flavor]
                rev = new_price * q_mean
                profit = (new_price - UNIT_COST) * q_mean
                demand_points[changed_flavor].append(
                    DemandPoint(
                        price=new_price,
                        mean_quantity=q_mean,
                        revenue=rev,
                        individual_profit=profit,
                    )
                )

                if progress_cb:
                    progress_cb(config_idx, total_configs)

        # Sort demand points by price ascending for each flavor
        for f in FLAVORS:
            demand_points[f].sort(key=lambda dp: dp.price)

        # Fit linear demand curve Q = a + b * P for each flavor
        fitted_models: Dict[str, Dict[str, float]] = {}
        for f in FLAVORS:
            prices_arr = np.array([dp.price for dp in demand_points[f]])
            quantities_arr = np.array([dp.mean_quantity for dp in demand_points[f]])
            # Linear fit: Q = slope * P + intercept
            slope, intercept = np.polyfit(prices_arr, quantities_arr, 1)
            fitted_models[f] = {
                "slope": float(slope),
                "intercept": float(intercept),
            }

        # Joint price optimization subject to customer budget constraint:
        # Sum of prices across the 3 flavors must not exceed CUSTOMER_BUDGET ($10.00).
        # We test every combination of the 7 tested prices per flavor that sums to <= 10.00,
        # and select the combination that maximizes total estimated profit.
        import itertools

        dp_by_price = {
            f: {dp.price: dp for dp in demand_points[f]}
            for f in FLAVORS
        }
        prices_v = [dp.price for dp in demand_points["vanilla"]]
        prices_c = [dp.price for dp in demand_points["chocolate"]]
        prices_s = [dp.price for dp in demand_points["strawberry"]]

        best_combo = None
        best_total_profit = float("-inf")

        for pv, pc, ps in itertools.product(prices_v, prices_c, prices_s):
            if round(pv + pc + ps, 4) <= 10.00:
                dp_v = dp_by_price["vanilla"][pv]
                dp_c = dp_by_price["chocolate"][pc]
                dp_s = dp_by_price["strawberry"][ps]
                total_prof = (
                    dp_v.individual_profit + dp_c.individual_profit + dp_s.individual_profit
                )
                if total_prof > best_total_profit:
                    best_total_profit = total_prof
                    best_combo = {"vanilla": pv, "chocolate": pc, "strawberry": ps}

        optimal_pairs: Dict[str, DemandPoint] = {
            f: dp_by_price[f][best_combo[f]]
            for f in FLAVORS
        }

        return Phase2Result(
            configurations=configurations_data,
            demand_points=demand_points,
            substitutability_cis=substitutability_cis,
            optimal_pairs=optimal_pairs,
            fitted_demand_models=fitted_models,
        )

    def run_phase_3(
        self,
        phase1_result: Phase1Result,
        phase2_result: Phase2Result,
        num_trials: int = 100,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> Phase3Result:
        """Execute Phase 3: Test optimal stock ratio and optimal prices."""
        # Optimal prices from Phase 2
        optimal_prices: Dict[str, float] = {
            f: phase2_result.optimal_pairs[f].price for f in FLAVORS
        }

        # Optimal stock ratio derived from optimal units sold
        optimal_quantities = {
            f: phase2_result.optimal_pairs[f].mean_quantity for f in FLAVORS
        }
        total_opt_qty = sum(optimal_quantities.values())
        if total_opt_qty <= 0:
            optimal_stock_ratios = dict(INITIAL_STOCK_RATIO)
        else:
            optimal_stock_ratios = {
                f: optimal_quantities[f] / total_opt_qty for f in FLAVORS
            }

        trials: List[TrialRecord] = []
        for i in range(num_trials):
            seed = None if self.base_seed is None else (self.base_seed + 50000 + i)
            sim = IceCreamTruckSimulation(
                prices=optimal_prices,
                stock_ratios=optimal_stock_ratios,
                population_preferences=self.population_preferences,
                population=self.population,
                heterogeneous_customers=self.heterogeneous_customers,
                seed=seed,
            )
            trials.append(sim.run_trial(trial_id=i + 1))
            if progress_cb:
                progress_cb(i + 1, num_trials)

        summary = aggregate_trials_summary(trials)
        phase3_profit_mean = summary["raw_profit_mean"]

        # Baseline profit from Phase 1
        phase1_profit_mean = phase1_result.summary["raw_profit_mean"]

        # Find maximum profit across all Phase 2 configurations
        phase2_profits = [
            cfg["summary"]["raw_profit_mean"]
            for cfg in phase2_result.configurations.values()
        ]
        phase2_max_profit = max(phase2_profits) if phase2_profits else float("-inf")

        # Success check: Phase 3 profit is strictly higher than Phase 1 and Phase 2 configs
        is_success = (phase3_profit_mean > phase1_profit_mean) and (
            phase3_profit_mean > phase2_max_profit
        )

        return Phase3Result(
            optimal_prices=optimal_prices,
            optimal_stock_ratios=optimal_stock_ratios,
            num_trials=num_trials,
            trials=trials,
            summary=summary,
            phase1_profit_mean=phase1_profit_mean,
            phase2_max_profit_mean=phase2_max_profit,
            is_success=is_success,
        )


def plot_demand_curves(
    phase2_result: Phase2Result,
    save_path: str = "demand_curves.png",
) -> None:
    """Generate and save demand curve plots with labeled optimal points."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    colors = {"vanilla": "#F3E5AB", "chocolate": "#7B3F00", "strawberry": "#FC5A8D"}

    for idx, f in enumerate(FLAVORS):
        ax = axes[idx]
        pts = phase2_result.demand_points[f]
        prices = [dp.price for dp in pts]
        quantities = [dp.mean_quantity for dp in pts]

        # Empirical data points
        ax.scatter(
            quantities,
            prices,
            color=colors.get(f, "blue"),
            edgecolor="black",
            s=80,
            label="Simulated Sales",
            zorder=3,
        )

        # Fitted curve
        model = phase2_result.fitted_demand_models[f]
        p_line = np.linspace(min(prices) - 0.2, max(prices) + 0.2, 50)
        q_line = model["slope"] * p_line + model["intercept"]
        ax.plot(q_line, p_line, "k--", alpha=0.7, label="Fitted Demand Curve")

        # Highlight optimal point
        opt = phase2_result.optimal_pairs[f]
        ax.scatter(
            [opt.mean_quantity],
            [opt.price],
            color="red",
            s=160,
            marker="*",
            label=f"Max Profit (${opt.individual_profit:.2f}/day)",
            zorder=4,
        )

        ax.set_title(f"{f.capitalize()} Demand", fontsize=13, fontweight="bold")
        ax.set_xlabel("Mean Units Sold / Day", fontsize=11)
        if idx == 0:
            ax.set_ylabel("Unit Price ($)", fontsize=11)
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(fontsize=9, loc="best")

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
