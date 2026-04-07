# House Payment Studies

Analysis and simulations around mortgage decisions, helping understand the real cost of buying a house over time.

## Current Scripts

| File | Description |
|------|-------------|
| `buy_house.py` | Main simulation: sweeps house price, down payment, interest rate, loan term, and extra yearly payments. Plots debt evolution and cost-to-price ratio. |
| `utils.py` | Core financial functions: monthly payment formula (French amortization), debt-over-time simulation, cumulative interest tracking. |

---

## Projects to Explore

### 1. TAEG Variance Analysis
**Goal:** Understand how small changes in TAEG (TAN + additional costs like insurance, fees, notary) compound into large differences in total money lost.

Key questions:
- How much does a 0.1% difference in TAEG translate to in total interest paid over 20/30 years?
- At what loan size does TAEG precision matter most?
- What is the "hidden cost" ratio: how much of TAEG is TAN vs. spread costs?

Variables to sweep:
- TAN range: e.g. 2.0% – 5.0% in 0.1% steps
- Additional annual costs (insurance, bank fees): e.g. 0.1% – 1.0% of loan
- Loan term: 15, 20, 25, 30 years
- House price: 100k – 400k €

Output ideas:
- Heatmap: TAEG vs. loan term → total money lost
- Line chart: fixed TAN, varying spread costs → cumulative interest over time
- Breakeven table: "at X% TAEG difference, you lose Y extra €"

---

### 2. Extra Payments Impact
**Goal:** Quantify how much early extra payments reduce total interest vs. later ones.

Key questions:
- If you pay an extra 1000€ in year 1 vs. year 10, what is the difference in total interest saved?
- What is the optimal moment to make bulk extra payments?

---

### 3. Rent vs. Buy Break-Even
**Goal:** Find the time horizon at which buying becomes cheaper than renting.

Key questions:
- Given a monthly rent, at what year does the total cost of ownership (mortgage + maintenance) fall below cumulative rent paid?
- How does TAEG affect the break-even point?

---

### 4. Down Payment Sensitivity
**Goal:** Find the optimal down payment percentage.

Key questions:
- More down payment → less interest, but more opportunity cost (money not invested elsewhere).
- What is the crossover point given a market return assumption (e.g. 5–7% annual)?

---

### 5. Fixed vs. Variable Rate Simulation
**Goal:** Compare fixed-rate loans against variable-rate scenarios.

Key questions:
- Under what interest rate trajectory does a variable rate end up cheaper?
- What is the maximum rate increase a variable loan can sustain before losing to fixed?

---

## Notes

- All interest calculations use French amortization (constant monthly payment).
- `total_money_lost` in `utils.py` is currently defined as `installment * years - house_price` — this does not account for down payment or additional TAEG costs. Worth revisiting for TAEG studies.
- TAEG in Portugal/EU = effective annual rate including all credit costs (TAN + spreads + insurance + fees).
