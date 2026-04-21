import numpy as np
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dataclasses import dataclass, field

# ── Mortgage Model ─────────────────────────────────────────────────────────────

@dataclass
class MortgageSchedule:
    """
    Full amortization schedule for a fixed-rate mortgage.

    All series are numpy arrays of length `payoff_months`.

    strategy:
      'reduce_time'    – installment fixed; extra monthly payment shortens term.
                         Fully vectorised via closed-form balance formula.
      'reduce_payment' – term fixed; installment recalculated each month on the
                         reduced balance. Inherently sequential.
    """
    loan: float
    annual_rate: float
    years: int
    monthly_extra: float = 0.0
    strategy: str = "reduce_time"

    # Populated by __post_init__
    pmt:           float      = field(init=False)
    balance:       np.ndarray = field(init=False)
    interest:      np.ndarray = field(init=False)
    principal:     np.ndarray = field(init=False)
    pmt_evolution: np.ndarray = field(init=False)
    cum_interest:  np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        if self.loan <= 0:
            z = np.zeros(self.years * 12)
            self.pmt = 0.0
            self.balance = self.interest = self.principal = z
            self.pmt_evolution = self.cum_interest = z
            return

        r = self.annual_rate / 12
        n = self.years * 12
        self.pmt = self.loan * r / (1 - (1 + r) ** -n) if r > 1e-10 else self.loan / n

        if self.strategy == "reduce_time":
            self._reduce_time(r, n)
        else:
            self._reduce_payment(r, n)

        self.cum_interest = np.cumsum(self.interest)

    # ── Strategies ────────────────────────────────────────────────────────────

    def _reduce_time(self, r: float, n: int) -> None:
        """
        Closed-form: treat (pmt + extra) as the effective monthly payment.

          B[k] = loan·(1+r)^k − eff·[(1+r)^k − 1] / r

        Payoff month solved analytically:
          n* = ceil( log(eff / (eff − r·loan)) / log(1+r) )
        """
        eff = self.pmt + self.monthly_extra

        if r > 1e-10:
            n_actual = int(min(
                np.ceil(np.log(eff / (eff - r * self.loan)) / np.log(1 + r)),
                n,
            ))
        else:
            n_actual = int(np.ceil(self.loan / eff))

        k      = np.arange(1, n_actual + 1, dtype=float)
        growth = (1 + r) ** k

        balance = np.maximum(0.0, self.loan * growth - eff * (growth - 1) / r)

        # Previous-month balance (loan for k=1)
        prev = np.empty(n_actual)
        prev[0]  = self.loan
        prev[1:] = balance[:-1]

        interest  = prev * r
        # Principal = installment share only; clipped so it never exceeds what is owed
        principal = np.clip(self.pmt - interest, 0.0, prev)

        self.balance       = balance
        self.interest      = interest
        self.principal     = principal
        self.pmt_evolution = np.full(n_actual, self.pmt)

    def _reduce_payment(self, r: float, n: int) -> None:
        """
        Sequential (unavoidable): installment is recalculated every month
        based on the current balance and remaining term.
        """
        debt = self.loan
        bal, intr, prin, pmts = [], [], [], []

        for k in range(1, n + 1):
            if debt < 0.01:
                break
            remaining = n - k + 1
            pmt_k = (debt * r / (1 - (1 + r) ** -remaining)
                     if r > 1e-10 else debt / remaining)
            i = debt * r
            p = min(pmt_k - i, debt)
            debt = max(0.0, debt - p - self.monthly_extra)
            bal.append(debt); intr.append(i)
            prin.append(p);   pmts.append(pmt_k)

        self.balance       = np.array(bal)
        self.interest      = np.array(intr)
        self.principal     = np.array(prin)
        self.pmt_evolution = np.array(pmts)

    # ── Derived scalars ───────────────────────────────────────────────────────

    @property
    def payoff_months(self) -> int:
        return len(self.balance)

    @property
    def total_interest(self) -> float:
        return float(self.interest.sum())

    @property
    def total_paid(self) -> float:
        return float(self.pmt_evolution.sum()) + self.monthly_extra * self.payoff_months


# ── Utilities ──────────────────────────────────────────────────────────────────

def _pad(arr: np.ndarray, n: int, *, hold_last: bool = False) -> np.ndarray:
    """
    Extend arr to length n.
    - Debt arrays → hold_last=False (debt is 0 after payoff).
    - Cumulative arrays → hold_last=True (never decreases after payoff).
    """
    diff = n - len(arr)
    if diff <= 0:
        return arr[:n]
    fill = float(arr[-1]) if hold_last and len(arr) else 0.0
    return np.pad(arr, (0, diff), constant_values=fill)


def fmt(v: float) -> str:
    """€850 → '€850'  |  €12 500 → '€12.5k'  |  €1 870 000 → '€1.87M'"""
    a = abs(v)
    if a >= 1_000_000:
        return f"€{v/1_000_000:.2f}M"
    if a >= 1_000:
        return f"€{v/1_000:.1f}k"
    return f"€{v:.0f}"


# ── Layout helpers ─────────────────────────────────────────────────────────────

def metric_card(label: str, id_: str) -> dbc.Card:
    return dbc.Card(dbc.CardBody([
        html.P(label, className="text-muted small mb-1"),
        html.H5("–", id=id_, className="mb-0 fw-bold"),
    ], style={"textAlign": "center"}), className="h-100 shadow-sm")


CHART_H   = {"height": "360px"}
LAYOUT_BASE = dict(template="plotly_white", xaxis_title="Years",
                   legend=dict(x=0.6, y=0.9), margin=dict(t=40, b=40))

# ── App ────────────────────────────────────────────────────────────────────────

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

controls = dbc.Card(dbc.CardBody([
    html.H5("Parameters", className="fw-bold mb-3"),

    html.Label("House Price (€)"),
    dcc.Slider(50_000, 1_000_000, step=10_000, value=300_000, id="price",
               marks={i: f"{i//1000}k" for i in range(100_000, 1_100_000, 200_000)},
               tooltip={"placement": "bottom", "always_visible": True}),

    html.Label("Down Payment (€)", className="mt-3"),
    dcc.Slider(0, 300_000, step=1_000, value=60_000, id="down_abs",
               marks={i: f"{i//1000}k" for i in range(0, 300_001, 50_000)},
               tooltip={"placement": "bottom", "always_visible": True}),

    html.Label("TAEG Range (%)", className="mt-3"),
    dcc.RangeSlider(1.0, 12.0, step=0.1, value=[3.0, 7.0], id="rate_range",
                    marks={i: f"{i}%" for i in range(1, 13)},
                    tooltip={"placement": "bottom", "always_visible": True}),

    html.Label("Loan Term (years)", className="mt-3"),
    dcc.Slider(5, 40, step=1, value=30, id="years",
               marks={i: str(i) for i in range(5, 45, 5)},
               tooltip={"placement": "bottom", "always_visible": True}),

    html.Label("Monthly Extra Payment (€)", className="mt-3"),
    dcc.Slider(0, 10_000, step=100, value=0, id="extra",
               marks={i: f"{i//1000}k" for i in range(0, 11_000, 1_000)},
               tooltip={"placement": "bottom", "always_visible": True}),

    html.Label("Extra Payment Strategy", className="mt-3"),
    dbc.RadioItems(
        id="strategy",
        options=[
            {"label": "Reduce Time",    "value": "reduce_time"},
            {"label": "Reduce Payment", "value": "reduce_payment"},
        ],
        value="reduce_time",
        inline=True,
    ),
]), className="sticky-top")

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H3("House Mortgage Simulator", className="my-3 fw-bold"))),
    dbc.Row([

        # ── Left column: Parameters + Metrics ───────────────────────────────────
        dbc.Col([
            controls,
            dbc.Card(dbc.CardBody([
                html.H5("Metrics", className="fw-bold mb-3"),
                dbc.Row([
                    dbc.Col(metric_card("Monthly Payment", "m_pmt"),      width=6),
                    dbc.Col(metric_card("Total Interest",  "m_interest"),  width=6),
                ], className="g-2 mb-2"),
                dbc.Row([
                    dbc.Col(metric_card("Total Cost",      "m_total"),    width=6),
                    dbc.Col(metric_card("Payoff",          "m_payoff"),   width=6),
                ], className="g-2 mb-2"),
                dbc.Row([
                    dbc.Col(metric_card("Interest / Loan", "m_ratio"),    width=6),
                    dbc.Col(metric_card("Extra Savings",   "m_savings"),  width=6),
                ], className="g-2 mb-2"),
                dbc.Row([
                    dbc.Col(metric_card("Time Saved",    "m_time_saved"), width=6),
                    dbc.Col(metric_card("Initial LTV",   "m_ltv"),        width=6),
                ], className="g-2"),
            ]), className="mt-3 shadow-sm"),
        ], width=3),

        # ── Right column: charts ─────────────────────────────────────────────────
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Graph(id="g_debt",     style=CHART_H), width=6),
                dbc.Col(dcc.Graph(id="g_interest", style=CHART_H), width=6),
            ], className="mb-2"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="g_combined", style=CHART_H), width=12),
            ]),
        ], width=9),

    ]),
], fluid=True)


# ── Callbacks ──────────────────────────────────────────────────────────────────

@app.callback(
    Output("down_abs", "max"),
    Output("down_abs", "marks"),
    Output("down_abs", "value"),
    Input("price", "value"),
    dash.dependencies.State("down_abs", "value"),
)
def update_down_slider(price, current_down):
    marks = {i: f"{i//1000}k" for i in range(0, price + 1, 50_000)}
    value = min(current_down or 0, price)
    return price, marks, value


@app.callback(
    Output("m_pmt",       "children"),
    Output("m_interest",  "children"),
    Output("m_total",     "children"),
    Output("m_payoff",    "children"),
    Output("m_ratio",     "children"),
    Output("m_savings",   "children"),
    Output("m_time_saved","children"),
    Output("m_ltv",       "children"),
    Output("g_debt",      "figure"),
    Output("g_interest",  "figure"),
    Output("g_combined",  "figure"),
    Input("price",      "value"),
    Input("down_abs",   "value"),
    Input("rate_range", "value"),
    Input("years",      "value"),
    Input("extra",      "value"),
    Input("strategy",   "value"),
)
def update_dashboard(price, down_abs, rate_range, years, extra, strategy):
    extra = float(extra or 0)
    down  = float(down_abs or 0)
    loan  = max(0.0, price - down)
    r_lo, r_hi = rate_range[0] / 100, rate_range[1] / 100
    r_mid = (r_lo + r_hi) / 2

    lo           = MortgageSchedule(loan, r_lo,  years, extra,  strategy)
    mid          = MortgageSchedule(loan, r_mid, years, extra,  strategy)
    hi           = MortgageSchedule(loan, r_hi,  years, extra,  strategy)
    mid_no_extra = MortgageSchedule(loan, r_mid, years, 0.0,    strategy)

    n = max(lo.payoff_months, hi.payoff_months)
    x = np.arange(1, n + 1) / 12  # years on x-axis

    # ── Metrics ─────────────────────────────────────────────────────────────────
    m_pmt      = f"{fmt(lo.pmt)} – {fmt(hi.pmt)}"
    m_interest = f"{fmt(lo.total_interest)} – {fmt(hi.total_interest)}"
    m_total    = f"{fmt(price + lo.total_interest)} – {fmt(price + hi.total_interest)}"
    m_payoff   = f"{mid.payoff_months / 12:.1f} yrs"
    m_ratio    = f"{lo.total_interest/loan*100:.0f}% – {hi.total_interest/loan*100:.0f}%"
    savings    = mid_no_extra.total_interest - mid.total_interest
    m_savings  = fmt(savings) if extra > 0 else "N/A"
    initial_ltv = loan / price * 100
    m_ltv      = f"{initial_ltv:.1f}%"
    months_saved = mid_no_extra.payoff_months - mid.payoff_months
    if extra > 0 and months_saved > 0 and strategy == "reduce_time":
        yrs_, mos_ = divmod(months_saved, 12)
        m_time_saved = f"{int(yrs_)}y {int(mos_)}m sooner" if yrs_ else f"{int(mos_)}m sooner"
    else:
        m_time_saved = "N/A"

    # ── Band builder ─────────────────────────────────────────────────────────────
    # Traces: (1) invisible top edge, (2) bottom edge fills up to (1), (3) mid line.
    # Higher rate → more debt / more interest → hi-rate series is always the top.
    def band(x_, y_lo_, y_hi_, y_mid_, rgb, label_suffix="", yaxis=None):
        rv, gv, bv = rgb
        kw = {"yaxis": yaxis} if yaxis else {}
        label_range = f"{rate_range[0]}%–{rate_range[1]}%"
        return [
            go.Scatter(x=x_, y=y_hi_, mode="lines",
                       line=dict(width=0), showlegend=False, **kw),
            go.Scatter(x=x_, y=y_lo_, mode="lines", fill="tonexty",
                       fillcolor=f"rgba({rv},{gv},{bv},0.20)", line=dict(width=0),
                       name=f"Range {label_range}{label_suffix}", **kw),
            go.Scatter(x=x_, y=y_mid_, mode="lines",
                       line=dict(color=f"rgb({rv},{gv},{bv})", width=2.5),
                       name=f"Mid {r_mid*100:.1f}%{label_suffix}", **kw),
        ]

    # ── Debt chart ───────────────────────────────────────────────────────────────
    d_lo  = _pad(lo.balance,  n) / 1000
    d_mid = _pad(mid.balance, n) / 1000
    d_hi  = _pad(hi.balance,  n) / 1000

    fig_debt = go.Figure(band(x, d_lo, d_hi, d_mid, (31, 119, 180)))
    fig_debt.add_hline(y=loan / 1000, line_dash="dot", line_color="gray",
                       annotation_text="Initial Loan")
    fig_debt.update_layout(**LAYOUT_BASE, title="Remaining Debt Over Time",
                           yaxis_title="Remaining Debt (k€)")

    # ── Cumulative interest chart ─────────────────────────────────────────────────
    # hold_last=True: cumulative interest never decreases after payoff
    ci_lo  = _pad(lo.cum_interest,  n, hold_last=True) / 1000
    ci_mid = _pad(mid.cum_interest, n, hold_last=True) / 1000
    ci_hi  = _pad(hi.cum_interest,  n, hold_last=True) / 1000

    fig_int = go.Figure(band(x, ci_lo, ci_hi, ci_mid, (220, 53, 69)))
    fig_int.add_hline(y=loan / 1000, line_dash="dot", line_color="orange",
                      annotation_text="= Loan Amount")
    fig_int.update_layout(**LAYOUT_BASE, title="Cumulative Interest Paid",
                          yaxis_title="Interest Paid (k€)")

    # ── Combined: Monthly Breakdown (left y) + LTV (right y) ─────────────────────
    mo = np.arange(1, mid.payoff_months + 1) / 12

    # LTV: prepend t=0 with the initial value (loan/price before any payment)
    ltv_lo  = np.concatenate([[initial_ltv], _pad(lo.balance,  n) / price * 100])
    ltv_mid = np.concatenate([[initial_ltv], _pad(mid.balance, n) / price * 100])
    ltv_hi  = np.concatenate([[initial_ltv], _pad(hi.balance,  n) / price * 100])
    x_ltv   = np.concatenate([[0.0], x])

    fig_combined = go.Figure()

    # Left axis – stacked principal / interest
    fig_combined.add_trace(go.Scatter(
        x=mo, y=mid.principal, name="Principal",
        stackgroup="one", fillcolor="rgba(32,178,170,0.55)",
        line=dict(color="rgb(32,178,170)")))
    fig_combined.add_trace(go.Scatter(
        x=mo, y=mid.interest, name="Interest",
        stackgroup="one", fillcolor="rgba(255,99,71,0.55)",
        line=dict(color="rgb(255,99,71)")))
    if strategy == "reduce_payment":
        fig_combined.add_trace(go.Scatter(
            x=mo, y=mid.pmt_evolution, name="Monthly Payment",
            mode="lines", line=dict(color="rgb(148,103,189)", width=2.5, dash="dash")))

    # Right axis – LTV band (steel blue) + 80% threshold (amber)
    for t in band(x_ltv, ltv_lo, ltv_hi, ltv_mid, (70, 130, 180),
                  label_suffix=" LTV", yaxis="y2"):
        fig_combined.add_trace(t)


    fig_combined.update_layout(
        **LAYOUT_BASE,
        title=f"Monthly Breakdown & LTV — mid rate {r_mid*100:.1f}%",
        yaxis=dict(title="€ / month"),
        yaxis2=dict(title="LTV (%)", overlaying="y", side="right", range=[0, 105]),
    )

    return (m_pmt, m_interest, m_total, m_payoff, m_ratio, m_savings, m_time_saved,
            m_ltv, fig_debt, fig_int, fig_combined)


if __name__ == "__main__":
    app.run(debug=True)
