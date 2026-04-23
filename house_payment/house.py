from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import math

class PaymentStrategy(Enum):
    TERM_REDUCTION = "term_reduction"
    PAYMENT_REDUCTION = "payment_reduction" 

@dataclass
class MonthState:
    month: int
    debt: float             # remaining debt
    payment: float          # base payment
    interest: float         # interest charged this month
    ammortization: float    # ammortization of the debt
    extra_payment: float    # additional contribution
    strategy: PaymentStrategy
    months_left: float
    additional_savings: int

    def compute_months_left(self) -> float:
        h0 = math.log(self.payment / (self.payment - self.interest/12 * self.debt))
        h1 = math.log(1 + self.interest/12)
        return h0/h1
    
    def __post_init__(self):
        
    
    def compute_next_month(self) -> MonthState:
        return MonthState(
            month=self.month + 1,
            debt=self.debt - self.ammortization,
            interest=self.interest,
            payment=self.payment,
            extra_payment=self.extra_payment,
            strategy=self.strategy,
            months_left=self.compute_months_left(),
            additional_savings=self.additional_savings,
        )

schedule: list[MonthState] = []


def simulate_loan(
    house_price: float,
    down_payment: float,
    taeg: float,
    loan_term: int,
    extra_payment: float,
    strategy: PaymentStrategy,
):
    # Store parameters
    params = {
        "house_price": house_price,
        "down_payment": down_payment,
        "taeg": taeg,
        "loan_term": loan_term,
        "extra_payment": extra_payment,
        "strategy": strategy,
    }
    
    # Monthly schedule
    schedule: list[MonthState] = []
    
    # First month
    schedule.append(MonthState(
        month=0,
        debt=house_price - down_payment,
        interest=0,
        payment=0,
        extra_payment=0,
        strategy=strategy,
    ))
    
    if __name__ == "__main__":
        simulate_loan(
            house_price=300000,
            down_payment=60000,
            taeg=3.5,
            loan_term=40,
            extra_payment=1000,
            strategy=PaymentStrategy.TERM_REDUCTION,
        )