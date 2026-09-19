"""Statistical utilities for confidence intervals, substitutability, and trial aggregation."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from config import CONFIDENCE_LEVEL, FLAVORS
from models import TrialRecord


def confidence_interval_90(
    data: List[float] | np.ndarray,
    confidence: float = CONFIDENCE_LEVEL,
) -> Dict[str, float]:
    """Calculate the sample mean and two-tailed confidence interval using Student's t-distribution.

    Args:
        data: Array or list of sample observations.
        confidence: Confidence level (default 0.90 for 90% CI).

    Returns:
        Dict with keys: 'mean', 'std', 'se', 'ci_lower', 'ci_upper', 'margin_of_error'.
    """
    arr = np.asarray(data, dtype=float)
    n = len(arr)
    if n == 0:
        return {
            "mean": 0.0,
            "std": 0.0,
            "se": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "margin_of_error": 0.0,
            "n": 0,
        }

    mean = float(np.mean(arr))
    if n == 1:
        return {
            "mean": mean,
            "std": 0.0,
            "se": 0.0,
            "ci_lower": mean,
            "ci_upper": mean,
            "margin_of_error": 0.0,
            "n": 1,
        }

    std = float(np.std(arr, ddof=1))
    se = float(std / np.sqrt(n))

    if std == 0.0:
        return {
            "mean": mean,
            "std": 0.0,
            "se": 0.0,
            "ci_lower": mean,
            "ci_upper": mean,
            "margin_of_error": 0.0,
            "n": n,
        }

    # Two-tailed t critical value: for 90% CI, alpha = 0.10, so tail = 0.95
    t_crit = float(stats.t.ppf((1.0 + confidence) / 2.0, df=n - 1))
    margin_of_error = t_crit * se

    return {
        "mean": mean,
        "std": std,
        "se": se,
        "ci_lower": mean - margin_of_error,
        "ci_upper": mean + margin_of_error,
        "margin_of_error": margin_of_error,
        "n": n,
    }


def compute_substitutability(
    p_baseline: float,
    p_new: float,
    q_baseline: float,
    q_new: float,
) -> Dict[str, float]:
    """Compute substitutability and cross-price elasticity.

    According to the simulation specification:
    Substitutability = (% change in price of changed flavor) / (% change in quantity sold of other flavor)
    relative to initial state ($3.00 baseline and Phase 1 mean sales).

    Also computes standard economic cross-price elasticity (%ΔQ / %ΔP) for comparison.

    Args:
        p_baseline: Baseline unit price ($3.00).
        p_new: New unit price for the changed flavor.
        q_baseline: Baseline mean sales of the other flavor in Phase 1.
        q_new: Mean or trial sales of the other flavor under the new price.

    Returns:
        Dict containing pct_change_price, pct_change_quantity, spec_substitutability,
        and standard_cross_elasticity.
    """
    pct_change_p = (p_new - p_baseline) / p_baseline if p_baseline != 0 else 0.0
    pct_change_q = (q_new - q_baseline) / q_baseline if q_baseline != 0 else 0.0

    # Specification definition: %ΔP / %ΔQ
    if abs(pct_change_q) < 1e-9:
        spec_substitutability = float("nan")
    else:
        spec_substitutability = pct_change_p / pct_change_q

    # Standard economic definition: %ΔQ / %ΔP
    if abs(pct_change_p) < 1e-9:
        standard_cross_elasticity = float("nan")
    else:
        standard_cross_elasticity = pct_change_q / pct_change_p

    return {
        "pct_change_price": pct_change_p,
        "pct_change_quantity": pct_change_q,
        "spec_substitutability": spec_substitutability,
        "standard_cross_elasticity": standard_cross_elasticity,
    }


def aggregate_trials_summary(trials: List[TrialRecord]) -> Dict[str, Any]:
    """Aggregate a batch of trials and compute 90% confidence intervals.

    Args:
        trials: List of TrialRecord instances.

    Returns:
        Dictionary containing sales metrics, profit metrics, and confidence intervals.
    """
    if not trials:
        return {}

    n = len(trials)
    sales_by_flavor: Dict[str, List[float]] = {f: [] for f in FLAVORS}
    total_sales: List[float] = []
    profits: List[float] = []

    for trial in trials:
        avg_sales = trial.average_daily_sales
        for f in FLAVORS:
            sales_by_flavor[f].append(avg_sales[f])
        total_sales.append(trial.average_daily_sales_all)
        profits.append(trial.average_daily_profit)

    summary: Dict[str, Any] = {
        "num_trials": n,
        "sales_ci": {
            flavor: confidence_interval_90(sales_by_flavor[flavor])
            for flavor in FLAVORS
        },
        "total_sales_ci": confidence_interval_90(total_sales),
        "profit_ci": confidence_interval_90(profits),
        "raw_means": {
            flavor: float(np.mean(sales_by_flavor[flavor])) for flavor in FLAVORS
        },
        "raw_profit_mean": float(np.mean(profits)),
    }

    # Identify empirical favorite flavor (highest average daily sales)
    favorite = max(summary["raw_means"], key=lambda f: summary["raw_means"][f])
    summary["predicted_favorite"] = favorite

    return summary
