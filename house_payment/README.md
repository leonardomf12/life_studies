# House Payment Studies

Analysis and simulations around mortgage decisions, helping understand the real cost of buying a house over time.

## Files

| File | Description |
|------|-------------|
| `app.py` | Interactive Dash web app — see details below. |
| `buy_house.py` | Batch simulation: sweeps house price, down payment, interest rate, loan term, and extra yearly payments. Plots debt evolution and cost-to-price ratio. |
| `utils.py` | Core financial functions: monthly payment formula (French amortization), debt-over-time simulation, cumulative interest tracking. |

---

## Interactive Simulator (`app.py`)

A Dash web app for exploring mortgage scenarios interactively.

**Run:**
```bash
uv run python house_payment/app.py
# open http://127.0.0.1:8050
```

### Parameters

| Parameter | Range | Notes |
|-----------|-------|-------|
| House Price | €50k – €1M | Step €10k |
| Down Payment | €0 – house price | Step €1k, marks every €50k |
| TAEG Range | 1% – 12% | Range slider — drives the rate band on all charts |
| Loan Term | 5 – 40 years | |
| Monthly Extra Payment | €0 – €10k | Step €100 |
| Extra Payment Strategy | Reduce Time / Reduce Payment | See below |

**Reduce Time** — installment stays fixed; extra payment shortens the loan term.
**Reduce Payment** — term stays fixed; installment is recalculated each month on the reduced balance, so it decreases over time.

### Metrics

| Metric | Description |
|--------|-------------|
| Monthly Payment | Installment range across the TAEG band |
| Total Interest | Total interest paid across the TAEG band |
| Total Cost | House price + total interest |
| Payoff | Years to pay off at mid TAEG (with extra payments if set) |
| Interest / Loan | Total interest as % of the loan amount |
| Extra Savings | Interest saved at mid TAEG vs. no extra payment |
| Time Saved | Months saved vs. no extra payment (Reduce Time only) |
| Initial LTV | Loan-to-Value at signing: `(price − down) / price × 100` |

### Charts

| Chart | Description |
|-------|-------------|
| Remaining Debt | Balance over time — shaded band between min/max TAEG + mid line |
| Cumulative Interest | Total interest paid over time — same band format |
| Monthly Breakdown & LTV | Stacked area (principal / interest) on left axis; LTV band on right axis |

### Architecture

The computation is encapsulated in `MortgageSchedule`, a dataclass that produces all series in `__post_init__`:

- **`reduce_time`** — fully vectorised using the closed-form balance recurrence
  `B[k] = loan·(1+r)^k − eff·[(1+r)^k − 1] / r`
  where `eff = pmt + monthly_extra`. Payoff month is solved analytically.
- **`reduce_payment`** — sequential loop (inherently non-vectorisable because each month's installment depends on the previous balance).

All series are plain NumPy arrays of length `payoff_months`:
`.balance`, `.interest`, `.principal`, `.cum_interest`, `.pmt_evolution`.

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
