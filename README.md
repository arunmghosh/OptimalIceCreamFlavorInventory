# Gauging Optimal Inventory For Ice Cream Flavors From Sales Data

A discrete-event, inventory management model trying to measure demand for three different flavors of ice cream: vanilla, chocolate, and strawberry, in order to maximize profit from flavor stock proportions and price choices.

---

## Experimental Design

This experiment consists of three phases. Phase one is a study of the model in the initial state, with no control over flavor proportions (must restock each flavor to 1/3 of total capacity every night) and a fixed price for all flavors ($3.00/unit). The goal of this phase is to establish a guess of which flavor is the most popular based on the sales data. 

Phase two still keeps the flavor proportions at the start of each day constant at 1/3 of total capacity going to each flavor. However, we allow the price to change in order to estimate demand functions for each flavor, and compute elasticities to measure the substitution effect (when the price of one flavor increases, do people buy different flavors at the same rate, lower rate, or higher rate?). The purpose of estimating the true demand functions is to come up with optimal price/quantity points to maximize the profit from each individual flavor. These prices will be the guesses for the optimal prices to maximize overall profit, and the quantities will be compared to estimate the optimal stock proportion to maximize total profit. We also need to look at the elasticities to confirm our guess of the most popular flavor from phase one (people will tend to substitute toward that flavor at a higher rate than when they substitute away from it). 

Lastly, phase three takes our guess for the optimal prices and stock proportions and confirms that this configuration produces the highest average daily profit we've seen (more than the initial state and any of the states in phase two). If so, this experiment will be considered a success. If not, we will reevaluate our guess and/or the experimental design. 

---

## Simulation Specification

- **Simulation Parameters**:
  - **Stock Capacity**: 300 units 
  - **Inventory State**: # of units of each flavor in stock, set to 100 units per flavor initially
  - **Unit Cost To Vendor**: $2.00/unit
  - **Unit Price To Customer**: Initially $3.00/unit for each flavor
  - **Daily Customer Traffic**: Normal distribution, mean of 90, standard deviation of 10/3
  - **Holding Cost**: $1.00/unit per night

- **Person Parameters**:
  - **Flavor Preferences**: A probability distribution {x: vanilla, y: chocolate, z: strawberry}, where x + y + z = 1, and min(x, y. z) >= 0.25
  - **Preference Multipliers**: Preferred flavor (corresponds to max(x,y,z)) is assigned 1. If x was chosen, the multipliers are {vanilla: 1, chocolate: x/y, strawberry: x/z}. Call these multipliers x_hat, y_hat, and z_hat.
  - **Budget per order**: $10.00
  - **Diminishing Returns Coefficient (ε)**: Product of the flavor multipliers (x_hat * y_hat * z_hat > 1)

- **Ordering Algorithm**:
  - **Skew flavor costs with preferences**: ex/ true_p(vanilla) = price(vanilla) * vanilla_multiplier
  - **Buy 1 unit of the cheapest flavor left in stock**: Subtract unit price (not true price) from the budget, decrement stock of that flavor
  - **Adjust true price of that flavor**: ex/ true_p(vanilla) = true_p(vanilla) * ε
  - **Repeat steps 2-3**: The exit condition is when the customer doesn't have enough money to afford the true price of a unit of any flavor (they never go over budget)
    
- **Simulation Flow (1 Trial)**:
  - **Set flavor stock proportions and prices**: These are kept constant for the duration of the trial.
  - **Draw random number of orders for day 1**: From the normal distribution described above (mean 90, standard deviation 10/3).
  - **Serve the orders**: Update state variables, track total profit and units sold, both in general and for each flavor
  - **Day 1 ends**: Subtracting holding cost for each unsold unit
  - **Make stock order**: Fill stock to the max capacity, with the constant flavor proportions. Payment and delivery happens overnight.
  - **Repeat steps 2-5**: Stopping condition is reaching the end of day 30.
  - **Aggregate data**: Calculate the average daily profit and units sold, both in general and for each flavor. 

---

## How To Replicate This Experiment

### Phase 1
- Run 100 trials of the simulation in the initial state (equal flavor proportions, unit price of $3.00)
- Report 90% confidence intervals for average daily sales of each flavor, and overall

### Phase 2
- Repeat Phase 1 for different price configurations (report the same statistics)
- Change only one flavor price from the initial state (25% decrease, 15% decrease, 5% decrease, 5% increase, 15% increase, 25% increase)
- Do this for each price change for each flavor
- For each trial, also compute substitutability between the flavor whose price changed and each of the other flavors (i.e. %change in price / % change in quanity sold of other flavor, relative to $3.00 and mean sales of that flavor in phase 1)
- Also report 90% confidence intervals for those substitutability values aggregated over the 100 trials
- Use the price and mean number of units sold pairs (7 data points for each flavor given the different price changes and the $3.00 trial from phase 1) to estimate demand functions for each flavor (plot them visually)
- Report which pair maximized profit for that individual flavor

### Phase 3
- Compute optimal stock ratio from the optimal units sold for each flavor found from the estimated demand functions in phase 2
- Set prices to the optimal prices found from the estimated demand functions in phase 2
- Run 100 trials in that state, reporting a 90% confidence interval for the average daily profit
- Compare to average daily profit of all phase 1 and phase 2 configurations, checking in the phase 3 profit is the maximum
---

## Results & Analysis

Here were my results from running the full experiment:

### 1. Initial State

Phase 1 evaluated 100 independent 30-day trials in the steady state (equal stock capacity of 100 units per flavor, fixed $3.00/unit price). Daily customer traffic followed $\mathcal{N}(90, (10/3)^2)$.

#### Daily Sales & Profit Summary (90% Confidence Intervals)
| Metric | Mean | Std Dev | Std Error | 90% Confidence Interval |
|---|---|---|---|---|
| **Vanilla Daily Sales** | 90.00 | 0.65 | 0.06 | [89.89, 90.11] |
| **Chocolate Daily Sales** | 90.00 | 0.65 | 0.06 | [89.89, 90.11] |
| **Strawberry Daily Sales** | 90.00 | 0.65 | 0.06 | [89.89, 90.11] |
| **Total Daily Sales** | 270.00 | 1.94 | 0.19 | [269.68, 270.32] |
| **Average Daily Profit** | **$240.00** | $3.89 | $0.39 | **[$239.35, $240.64]** |

- **Predicted Population Favorite**: **Vanilla** (assigned by tie-breaker).
- **Behavioral Note**: Because customers have a $10.00 budget and ice cream costs $3.00/unit, each customer purchased exactly 3 units ($3 \times \$3.00 = \$9.00$, leaving $1.00 unspent). Due to diminishing returns ($\epsilon > 1$), customers systematically diversified across all three flavors (1 vanilla, 1 chocolate, 1 strawberry per customer), resulting in identical sales of 90.00 units/day for every flavor.
- **Inventory Accounting**: With 270 units sold out of 300 capacity, exactly 30 units remained unsold each night. Daily holding costs were $30.00 ($1.00/unit), wholesale restock costs were $540.00 ($2.00/unit), and revenue was $810.00 ($3.00/unit), yielding net profit $\pi = 810 - 540 - 30 = \$240.00/\text{day}$.

---

### 2. Varying Price

In Phase 2, the selling price of each flavor was individually varied by -25%, -15%, -5%, +5%, +15%, and +25% relative to the baseline $3.00 price, while keeping the other two flavors at $3.00 and maintaining equal stock capacity (100 units each). Each of the 18 configurations was evaluated over 100 trials (30 days/trial).

#### Price Perturbation Configurations & Empirical Performance
| Configuration | Changed Flavor | Price ($) | Vanilla Sales | Choc Sales | Straw Sales | Daily Profit ($) | 90% CI for Profit |
|---|---|---|---|---|---|---|---|
| `vanilla_-0.25` | Vanilla | $2.25 | 89.98 | 89.98 | 89.98 | $172.39 | [$171.87, $172.92] |
| `vanilla_-0.15` | Vanilla | $2.55 | 90.05 | 90.05 | 90.05 | $199.76 | [$199.19, $200.33] |
| `vanilla_-0.05` | Vanilla | $2.85 | 89.95 | 89.95 | 89.95 | $226.21 | [$225.63, $226.78] |
| `vanilla_+0.05` | Vanilla | $3.15 | 90.04 | 90.04 | 90.04 | $253.77 | [$253.07, $254.46] |
| `vanilla_+0.15` | Vanilla | $3.45 | 89.96 | 89.96 | 89.96 | $280.23 | [$279.58, $280.87] |
| `vanilla_+0.25` | Vanilla | $3.75 | 90.09 | 90.09 | 90.09 | **$308.14** | **[$307.44, $308.84]** |
| `chocolate_-0.25` | Chocolate | $2.25 | 90.03 | 90.03 | 90.03 | $172.65 | [$172.12, $173.18] |
| `chocolate_-0.15` | Chocolate | $2.55 | 89.89 | 89.89 | 89.89 | $198.90 | [$198.38, $199.41] |
| `chocolate_-0.05` | Chocolate | $2.85 | 90.04 | 90.04 | 90.04 | $226.71 | [$226.10, $227.31] |
| `chocolate_+0.05` | Chocolate | $3.15 | 90.03 | 90.03 | 90.03 | $253.70 | [$253.11, $254.29] |
| `chocolate_+0.15` | Chocolate | $3.45 | 90.12 | 90.12 | 90.12 | $281.25 | [$280.61, $281.88] |
| `chocolate_+0.25` | Chocolate | $3.75 | 90.03 | 90.03 | 90.03 | **$307.03** | **[$306.42, $307.65]** |
| `strawberry_-0.25` | Strawberry | $2.25 | 90.02 | 90.02 | 90.02 | $172.60 | [$172.07, $173.13] |
| `strawberry_-0.15` | Strawberry | $2.55 | 89.92 | 89.92 | 89.92 | $199.03 | [$198.51, $199.55] |
| `strawberry_-0.05` | Strawberry | $2.85 | 90.07 | 90.07 | 90.07 | $226.92 | [$226.32, $227.52] |
| `strawberry_+0.05` | Strawberry | $3.15 | 89.90 | 89.90 | 89.90 | $252.91 | [$252.23, $253.58] |
| `strawberry_+0.15` | Strawberry | $3.45 | 90.03 | 90.03 | 90.03 | $280.66 | [$280.04, $281.29] |
| `strawberry_+0.25` | Strawberry | $3.75 | 90.09 | 90.09 | 90.09 | **$307.13** | **[$306.34, $307.91]** |

#### Substitutability Analysis (%ΔPrice / %ΔQuantity)
Substitutability was calculated per trial between the altered flavor and the remaining flavors relative to Phase 1 baseline means:
$$\text{Substitutability} = \frac{(P_{\text{new}} - 3.00) / 3.00}{(Q_{\text{other}} - \bar{Q}_{\text{other, phase 1}}) / \bar{Q}_{\text{other, phase 1}}}$$

| Changed Flavor | %ΔPrice | Other Flavor | Mean Substitutability | 90% Confidence Interval |
|---|---|---|---|---|
| Vanilla | -25% | Chocolate / Strawberry | -3368.04 | [-5823.39, -912.69] |
| Vanilla | -15% | Chocolate / Strawberry | -1597.86 | [-2923.13, -272.58] |
| Vanilla | -5%  | Chocolate / Strawberry | -539.83  | [-981.33, -98.34] |
| Vanilla | +5%  | Chocolate / Strawberry | +541.33  | [+99.87, +982.78] |
| Vanilla | +15% | Chocolate / Strawberry | +1635.24 | [+311.28, +2959.21] |
| Vanilla | +25% | Chocolate / Strawberry | +2718.84 | [+512.00, +4925.67] |
| Chocolate | -25% | Vanilla / Strawberry | -2698.02 | [-4905.52, -490.52] |
| Chocolate | +25% | Vanilla / Strawberry | +1352.45 | [-224.71, +2929.62] |
| Strawberry | -25% | Vanilla / Chocolate | -678.16  | [-1799.33, +443.01] |
| Strawberry | +25% | Vanilla / Chocolate | +5.54    | [-24.37, +35.44] |

*Observation*: Because a customer with a $10.00 budget could still easily afford all 3 scoops even when one flavor increased to $3.75 ($3.75 + $3.00 + $3.00 = $9.75 $\le$ $10.00$), quantity sold for all flavors remained essentially constant at 90.0 units/day. The denominator ($\% \Delta Q$) was pure zero-centered Monte Carlo noise from customer arrival fluctuations, producing massive, erratic substitutability ratios.

---

### 3. Estimated Demand Functions

Using the 7 empirical $(P, Q)$ data pairs for each flavor (the 6 price variations from Phase 2 plus the $3.00 baseline from Phase 1), linear demand curves were fitted using ordinary least squares:
$$Q(P) = \text{slope} \times P + \text{intercept}$$

![Demand Curves](demand_curves.png)

#### Fitted Demand Curve Models
- **Vanilla**: $Q(P) = 0.0386 \cdot P + 89.8944$
- **Chocolate**: $Q(P) = 0.0168 \cdot P + 89.9547$
- **Strawberry**: $Q(P) = -0.0201 \cdot P + 90.0430$

*Analysis of Demand Slopes*: The fitted slopes are practically zero ($|\text{slope}| \le 0.038$), indicating near-perfect demand inelasticity over the isolated price range [$2.25, $3.75]. Because customers always purchased 1 unit of each flavor as long as the total bundle cost remained under $10.00, raising any single price did not reduce units sold.

#### Individual Flavor Profit Maximization
Individual gross profit for each flavor was evaluated as $\pi_i = (P_i - \text{Unit Cost}) \times Q_i = (P_i - 2.00) \times Q_i$:
| Flavor | Optimal Price ($P^*$) | Mean Quantity Sold ($Q^*$) | Individual Profit ($\pi_i^*$) |
|---|---|---|---|
| **Vanilla** | **$3.75** | 90.09 units/day | $157.67 / day |
| **Chocolate** | **$3.75** | 89.93 units/day | $157.38 / day |
| **Strawberry** | **$3.75** | 89.94 units/day | $157.40 / day |

Because demand was completely inelastic when evaluated one flavor at a time, higher prices strictly yielded higher profit per unit with zero volume loss, causing the individual profit-maximizing price to hit the upper boundary of $3.75 for all three flavors.

---

### 4. Testing Our Optimal Guess

In Phase 3, the optimal configuration inferred from Phase 2 was tested over 100 independent 30-day trials:
- **Optimal Prices Chosen**: $P_V^* = \$3.75$, $P_C^* = \$3.75$, $P_S^* = \$3.75$
- **Optimal Stock Ratios Chosen**:
  - Vanilla: $90.09 / 269.97 = \mathbf{33.37\%}$ (100 units)
  - Chocolate: $89.93 / 269.97 = \mathbf{33.31\%}$ (100 units)
  - Strawberry: $89.94 / 269.97 = \mathbf{33.32\%}$ (100 units)

#### Phase 3 Experimental Results
| Metric | Value | 90% Confidence Interval |
|---|---|---|
| **Vanilla Daily Sales** | 60.00 units | [59.93, 60.07] |
| **Chocolate Daily Sales** | 60.00 units | [59.93, 60.07] |
| **Strawberry Daily Sales** | 60.00 units | [59.93, 60.07] |
| **Total Daily Sales** | **180.00 units** | [179.78, 180.22] |
| **Average Daily Profit** | **$195.02 / day** | **[$194.45, $195.59]** |

#### Comparative Profit Evaluation
- **Phase 1 Baseline Daily Profit**: **$240.00**
- **Phase 2 Maximum Single-Flavor Configuration Profit**: **$308.14** (`vanilla_+0.25`)
- **Phase 3 Optimal Configuration Daily Profit**: **$195.02**
- **Difference vs. Phase 1**: **-$44.98 / day (-18.7%)**
- **Difference vs. Phase 2 Max**: **-$113.12 / day (-36.7%)**
- **Experiment Outcome**: **FAILURE (`is_success: False`)**

The Phase 3 configuration yielded a daily profit substantially *lower* than the baseline state and all profitable Phase 2 configurations. 

---

### 5. Conclusions

Include both statistical and pragmatic interpretations of the results. 

---

## Codebase Architecture

```
ice_cream_truck/
├── config.py                 # Simulation constants, price variations, traffic distribution, default preferences
├── models.py                 # Person customer model (ordering algorithm, ε diminishing returns), DailyRecord, TrialRecord
├── simulation.py             # IceCreamTruckSimulation discrete-event engine, capacity allocation, overnight restocking
├── stats.py                  # 90% Student's t confidence intervals, substitutability (%ΔP/%ΔQ), cross-price elasticity
├── experiment.py             # Phase 1, Phase 2, Phase 3 orchestrators, linear demand curve fitting, plot generation
├── runner.py                 # CLI interface for custom trials, rapid smoke tests, individual phases, and full runs
├── IceCreamTruckSimulation.pdf # Original mathematical problem specification
├── tests/                    # Automated unit and integration test suite
│   ├── test_models.py        # Person preferences, diminishing returns order logic, accounting checks
│   ├── test_simulation.py    # Capacity allocation invariant, daily traffic bounds, restocking mechanics
│   ├── test_stats.py         # Confidence intervals, edge cases, substitutability calculation
│   ├── test_experiment.py    # Multi-phase execution, demand curve fitting, optimal pair selection
│   └── test_smoke.py         # Rapid end-to-end integration smoke test
└── README.md                 # Project specification, experiment documentation, architecture, and usage
```

---

## Installation & Usage

### Prerequisites
The simulation codebase requires Python 3.10+ along with `numpy`, `scipy`, and `matplotlib`:
```bash
pip install numpy scipy matplotlib
```

### Run unittests
Run the complete automated test suite (16 unit and integration tests):
```bash
python3 -m unittest discover -s tests
```

### Run a quick smoke test
Verify all three experimental phases end-to-end with a rapid integration test (~0.5s):
```bash
python3 runner.py --smoke-test
```

### Run the experiment

#### 1. Run All 3 Phases (Full Experiment)
Run 100 trials across Phase 1 (baseline), Phase 2 (18 price perturbation configurations), and Phase 3 (optimal validation), plotting demand curves and saving results to JSON:
```bash
python3 runner.py --phase all --trials 100 --plot demand_curves.png --output results.json
```

#### 2. Run Individual Phases
- **Phase 1 Only** (Initial steady state with equal stock proportions and $3.00 price):
  ```bash
  python3 runner.py --phase 1 --trials 100
  ```

- **Phase 2 Only** (Price perturbations, substitutability matrices, and demand curve estimation):
  ```bash
  python3 runner.py --phase 2 --trials 100 --plot demand_curves.png
  ```

- **Phase 3 Only** (Evaluate optimal prices and stock ratios against baseline and Phase 2 states):
  ```bash
  python3 runner.py --phase 3 --trials 100
  ```

### Run a custom trial
Simulate a custom trial with arbitrary unit prices, stock capacity, duration, and flavor proportions:
```bash
# Example: 30-day trial with custom prices ($3.25 vanilla, $3.00 chocolate, $2.75 strawberry)
# and stock ratios (40% vanilla, 35% chocolate, 25% strawberry)
python3 runner.py --custom --trials 5 --days 30 --capacity 300 \
  --prices 3.25 3.00 2.75 \
  --ratios 0.40 0.35 0.25
```

### Command-Line Arguments Reference
| Argument | Description | Default |
|---|---|---|
| `--smoke-test` | Run a rapid end-to-end integration check across all 3 phases | `False` |
| `--custom` | Run a custom simulation trial with user-specified parameters | `False` |
| `--phase [1\|2\|3\|all]` | Run a specific phase or all phases in sequence | `None` |
| `--trials N` | Number of 30-day trials to run per configuration | `100` |
| `--days D` | Number of days simulated per trial | `30` |
| `--capacity C` | Total unit stock capacity of the truck | `300` |
| `--prices P_V P_C P_S` | Selling prices for vanilla, chocolate, strawberry | `3.00 3.00 3.00` |
| `--ratios R_V R_C R_S` | Capacity proportions for vanilla, chocolate, strawberry (sum to 1.0) | `0.333 0.333 0.334` |
| `--seed S` | Base random seed for reproducible comparisons | `42` |
| `--output PATH` | Path to export structured experimental results as JSON | `None` |
| `--plot PATH` | Path to save fitted demand curve plots (PNG) | `None` |
