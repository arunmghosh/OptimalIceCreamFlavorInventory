"""Command-Line Interface (CLI) runner for the Ice Cream Truck experiment."""

import argparse
import json
import sys
import time
from typing import Any, Dict

from config import (
    DEFAULT_POPULATION_PREFERENCES,
    FLAVORS,
    INITIAL_PRICES,
    INITIAL_STOCK_RATIO,
    NUM_TRIALS_DEFAULT,
    TOTAL_CAPACITY,
    TRIAL_DAYS,
)
from experiment import ExperimentOrchestrator, plot_demand_curves
from models import TrialRecord
from simulation import IceCreamTruckSimulation
from stats import aggregate_trials_summary


def format_ci(ci_dict: Dict[str, float]) -> str:
    """Format a confidence interval dictionary as a readable string."""
    mean = ci_dict.get("mean", 0.0)
    lower = ci_dict.get("ci_lower", 0.0)
    upper = ci_dict.get("ci_upper", 0.0)
    return f"{mean:.2f} [90% CI: {lower:.2f}, {upper:.2f}]"


def run_custom_trial(args: argparse.Namespace) -> None:
    """Run a custom simulation trial from command-line arguments."""
    prices = {
        "vanilla": args.prices[0],
        "chocolate": args.prices[1],
        "strawberry": args.prices[2],
    }
    ratios = {
        "vanilla": args.ratios[0],
        "chocolate": args.ratios[1],
        "strawberry": args.ratios[2],
    }

    print("=" * 60)
    print("🍦 RUNNING CUSTOM ICE CREAM TRUCK SIMULATION")
    print(f"   Trials: {args.trials} | Days per trial: {args.days} | Capacity: {args.capacity}")
    print(f"   Prices: Vanilla=${prices['vanilla']:.2f}, Chocolate=${prices['chocolate']:.2f}, Strawberry=${prices['strawberry']:.2f}")
    print(f"   Stock Ratios: Vanilla={ratios['vanilla']:.2f}, Chocolate={ratios['chocolate']:.2f}, Strawberry={ratios['strawberry']:.2f}")
    print("=" * 60)

    trials = []
    for i in range(args.trials):
        seed = None if args.seed is None else (args.seed + i)
        sim = IceCreamTruckSimulation(
            prices=prices,
            stock_ratios=ratios,
            total_capacity=args.capacity,
            trial_days=args.days,
            seed=seed,
        )
        trials.append(sim.run_trial(trial_id=i + 1))

    summary = aggregate_trials_summary(trials)
    print("\n--- RESULTS ---")
    for f in FLAVORS:
        print(f"   {f.capitalize()} Daily Sales: {format_ci(summary['sales_ci'][f])}")
    print(f"   Total Daily Sales:      {format_ci(summary['total_sales_ci'])}")
    print(f"   Average Daily Profit:   ${format_ci(summary['profit_ci'])}")
    print("=" * 60)


def run_smoke_test(seed: int = 42) -> None:
    """Run a quick smoke test across all 3 phases (2 trials each) to verify functionality."""
    print("=" * 60)
    print("🍦 RUNNING RAPID INTEGRATION SMOKE TEST (All 3 Phases)")
    print("=" * 60)

    start = time.time()
    orchestrator = ExperimentOrchestrator(base_seed=seed)

    print("▶ Testing Phase 1 (2 trials)...", end="", flush=True)
    p1 = orchestrator.run_phase_1(num_trials=2)
    print(f" Done. (Predicted Favorite: {p1.predicted_favorite})")

    print("▶ Testing Phase 2 (2 trials per configuration)...", end="", flush=True)
    p2 = orchestrator.run_phase_2(p1, num_trials=2)
    print(" Done.")
    for f in FLAVORS:
        opt = p2.optimal_pairs[f]
        print(f"   - Optimal {f.capitalize()}: Price=${opt.price:.2f}, Qty={opt.mean_quantity:.1f}, Profit=${opt.individual_profit:.2f}")

    print("▶ Testing Phase 3 (2 trials)...", end="", flush=True)
    p3 = orchestrator.run_phase_3(p1, p2, num_trials=2)
    print(f" Done. (Phase 3 Profit: ${p3.summary['raw_profit_mean']:.2f}/day | Success: {p3.is_success})")

    elapsed = time.time() - start
    print("=" * 60)
    print(f"✅ Smoke test completed successfully in {elapsed:.2f}s!")
    print("=" * 60)


def main() -> None:
    """CLI argument parsing and execution."""
    parser = argparse.ArgumentParser(
        description="Discrete-Event Ice Cream Truck Inventory & Price Optimization Experiment"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a rapid end-to-end integration smoke test across all phases",
    )
    parser.add_argument(
        "--custom",
        action="store_true",
        help="Run a custom trial with user-specified prices and stock ratios",
    )
    parser.add_argument(
        "--phase",
        type=str,
        choices=["1", "2", "3", "all"],
        default=None,
        help="Run a specific experiment phase (or 'all' for full experiment)",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=NUM_TRIALS_DEFAULT,
        help=f"Number of trials per configuration (default: {NUM_TRIALS_DEFAULT})",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=TRIAL_DAYS,
        help=f"Number of days per trial (default: {TRIAL_DAYS})",
    )
    parser.add_argument(
        "--capacity",
        type=int,
        default=TOTAL_CAPACITY,
        help=f"Truck total stock capacity (default: {TOTAL_CAPACITY})",
    )
    parser.add_argument(
        "--prices",
        nargs=3,
        type=float,
        default=[3.00, 3.00, 3.00],
        metavar=("VANILLA", "CHOCOLATE", "STRAWBERRY"),
        help="Unit prices for vanilla, chocolate, strawberry",
    )
    parser.add_argument(
        "--ratios",
        nargs=3,
        type=float,
        default=[1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0],
        metavar=("VANILLA", "CHOCOLATE", "STRAWBERRY"),
        help="Stock ratios for vanilla, chocolate, strawberry (must sum to 1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save JSON summary of results",
    )
    parser.add_argument(
        "--plot",
        type=str,
        default=None,
        help="Path to save demand curve plots (e.g. demand_curves.png)",
    )

    args = parser.parse_args()

    if args.smoke_test:
        run_smoke_test(seed=args.seed)
        return

    if args.custom:
        run_custom_trial(args)
        return

    if args.phase is not None:
        orchestrator = ExperimentOrchestrator(base_seed=args.seed)

        if args.phase in ["1", "all"]:
            print(f"--- Running Phase 1 ({args.trials} trials) ---")
            p1 = orchestrator.run_phase_1(num_trials=args.trials)
            print("Phase 1 Complete:")
            for f in FLAVORS:
                print(f"  {f.capitalize()} Daily Sales: {format_ci(p1.summary['sales_ci'][f])}")
            print(f"  Total Daily Sales:    {format_ci(p1.summary['total_sales_ci'])}")
            print(f"  Average Daily Profit: ${format_ci(p1.summary['profit_ci'])}")
            print(f"  Predicted Favorite:   {p1.predicted_favorite}")

        if args.phase in ["2", "all"]:
            if "p1" not in locals():
                p1 = orchestrator.run_phase_1(num_trials=args.trials)
            print(f"\n--- Running Phase 2 ({args.trials} trials per configuration) ---")
            p2 = orchestrator.run_phase_2(p1, num_trials=args.trials)
            print("Phase 2 Complete. Optimal points by flavor:")
            for f in FLAVORS:
                opt = p2.optimal_pairs[f]
                print(f"  {f.capitalize()}: Price=${opt.price:.2f}, Sales={opt.mean_quantity:.2f}, Profit=${opt.individual_profit:.2f}/day")
            if args.plot:
                plot_demand_curves(p2, save_path=args.plot)
                print(f"  Plot saved to {args.plot}")

        if args.phase in ["3", "all"]:
            if "p1" not in locals():
                p1 = orchestrator.run_phase_1(num_trials=args.trials)
            if "p2" not in locals():
                p2 = orchestrator.run_phase_2(p1, num_trials=args.trials)
            print(f"\n--- Running Phase 3 ({args.trials} trials) ---")
            p3 = orchestrator.run_phase_3(p1, p2, num_trials=args.trials)
            print("Phase 3 Complete:")
            print(f"  Optimal Prices: {p3.optimal_prices}")
            print(f"  Optimal Stock Ratios: {p3.optimal_stock_ratios}")
            print(f"  Phase 3 Average Daily Profit: ${format_ci(p3.summary['profit_ci'])}")
            print(f"  Phase 1 Baseline Daily Profit: ${p3.phase1_profit_mean:.2f}")
            print(f"  Phase 2 Max Daily Profit:      ${p3.phase2_max_profit_mean:.2f}")
            print(f"  Result: {'SUCCESS (Optimal configuration beat all previous states!)' if p3.is_success else 'FAILURE (Optimal configuration did not yield maximum profit)'}")

        if args.output:
            # Export summary
            data_to_export: Dict[str, Any] = {}
            if "p1" in locals():
                data_to_export["phase1"] = {
                    "baseline_means": p1.baseline_sales_means,
                    "predicted_favorite": p1.predicted_favorite,
                }
            if "p2" in locals():
                data_to_export["phase2"] = {
                    "optimal_pairs": {
                        f: {"price": p2.optimal_pairs[f].price, "qty": p2.optimal_pairs[f].mean_quantity, "profit": p2.optimal_pairs[f].individual_profit}
                        for f in FLAVORS
                    },
                    "fitted_models": p2.fitted_demand_models,
                }
            if "p3" in locals():
                data_to_export["phase3"] = {
                    "optimal_prices": p3.optimal_prices,
                    "optimal_stock_ratios": p3.optimal_stock_ratios,
                    "profit_mean": p3.summary["raw_profit_mean"],
                    "is_success": p3.is_success,
                }
            with open(args.output, "w") as fp:
                json.dump(data_to_export, fp, indent=2)
            print(f"Results exported to {args.output}")

        return

    parser.print_help()


if __name__ == "__main__":
    main()
