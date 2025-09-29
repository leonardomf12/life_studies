import IPython
import numpy as np
from typing import Tuple, List
from box import Box

def calculate_monthly_payment(house_price: int, interest_rate:float, years_to_pay:int) -> float:
    """Calculate the down payment"""
    month_interest_rate = interest_rate/12
    num_payments = years_to_pay * 12
    #return house_price * (month_interest_rate * (1 + month_interest_rate) ** num_payments) / ((1 + month_interest_rate) ** num_payments - 1) # SIMILAR
    return house_price * (month_interest_rate / (1 - (1 + month_interest_rate)**(-num_payments)))

def calculate_debt_overtime(
        house_price: float,
        down_payment: int,
        interest_rate: float,
        years,
        extra: int # yearly
):
    # Init
    installment = calculate_monthly_payment(house_price=house_price, interest_rate=interest_rate, years_to_pay=years)
    months = np.arange(0, years*12)

    # Progression overtime
    debt_record = []
    amortization_record = []
    interest_record = []
    # TODO optimize this function
    for y in range(1, years + 1):
        for m in range(1, 12 + 1):
            idx_month = y*m
            last_month_debt = house_price - down_payment if idx_month==1 else debt_record[idx_month - 2]

            # Calculations
            interest = last_month_debt * interest_rate/12
            amortization = installment - interest
    
            # Save to record
            debt_record.append(last_month_debt - amortization)
            amortization_record.append(amortization)
            interest_record.append(interest)
        debt_record[y * 12 - 1] -= extra
        

    # Evolution Metrics
    cost_to_price_ratio = installment * (months + 1) / house_price
    cumulative_interest = np.cumsum(interest_record)
    
    # Static Metrics
    total_money_lost = installment * years - house_price
    
    return Box({
        "debt_evolution": np.array(debt_record),
        "amortization_evolution": np.array(amortization_record),
        "interest_evolution": np.array(interest_record),
        "cost_to_price_ratio": cost_to_price_ratio,
        "cumulative_interest": cumulative_interest,
        "total_money_lost": total_money_lost
    })

def calculate_loan_amount(house_price: float, down_payment: float) -> float:
    """Calculate the total loan amount needed"""
    return house_price - down_payment


def validate_down_payment_percentage(percentage: float) -> bool:
    """Validate if down payment percentage is within acceptable range (3.5% - 100%)"""
    return 0.035 <= percentage <= 1.0


def calculate_total_interest(monthly_payment: float, loan_amount: float, years: int) -> float:
    """Calculate total interest paid over the life of the loan"""
    total_payments = monthly_payment * years * 12
    return total_payments - loan_amount


def generate_payment_evolution(loan_amount: float, annual_rate: float, years: int) -> Tuple[
    np.ndarray, np.ndarray, float]:
    """Generate monthly payment evolution including remaining balance"""
    monthly_rate = annual_rate / 12
    num_payments = years * 12
    monthly_payment = calculate_monthly_payment(loan_amount, annual_rate, years)

    months = np.arange(num_payments + 1)
    balance = loan_amount * (1 + monthly_rate) ** num_payments - \
              monthly_payment * ((1 + monthly_rate) ** months - 1) / monthly_rate

    return months, balance, monthly_payment
