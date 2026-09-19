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
  - **Diminishing Returns Coefficient (ε)**: x * y * z

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

Report the results of phase 1 here.

---

### 2. Varying Price

Report the results of phase 2 here, except for the demand functions.

---

### 3. Estimated Demand Functions

Show plots and captions describing them. 

---

### 4. Testing Our Optimal Guess

Report the results of Phase 3 here. 

---

### 5. Conclusions

Include both statistical and pragmatic interpretations of the results. 

---

## Codebase Architecture

---

## Installation & Usage

### Run the experiment

### Run unittests

### Run a custom trial
