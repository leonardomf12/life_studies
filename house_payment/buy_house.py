import argparse
import IPython
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from utils import *
from tqdm import tqdm
import time

import itertools


def arg_parse():
    parser = argparse.ArgumentParser(description="Calculate down house payment simulations!")
    parser.add_argument("--price", type=int, default=150000, help="House price (€)")
    parser.add_argument("--down", type=float, default=0.1, help="Down payment as fraction (e.g., 0.1 for 10%)")
    parser.add_argument("--interest_rate", type=float, default=0.05, help="Annual interest rate as fraction (e.g., 0.06 for 6%)")
    parser.add_argument("--years", type=int, default=30, help="Loan term in years")
    parser.add_argument("--bank-insurance", type=float, default=0.0, help="Bank Insurance during down payment")
    return parser.parse_args()


def create_ind_plot(results: dict, axs: Axes, idxs: tuple[int, int]):
    """Create individual subplot with debt evolution metrics.

    Args:
        results: Dictionary containing calculation results
        axs: Matplotlib axes array for subplots
        idxs: Tuple of (row, column) indices for current subplot
    """
    ax = axs[idxs[0], idxs[1]]

    # Plot debt evolution
    months = np.arange(len(results.debt_evolution))
    ax.plot(months / 12, results.debt_evolution / 1000, 'b-', label='Debt')

    # Plot cost to price ratio
    ax2 = ax.twinx()
    ax2.plot(months / 12, results.cost_to_price_ratio, 'r--', label='Cost Ratio')
    ax2.plot(months / 12, results.cumulative_interest / 1000, 'g:', label='Cum. Interest')

    # Styling
    ax.grid(True)
    ax.set_xlabel('Years')
    ax.set_ylabel('Amount (k€)')
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')

    ax.set_title(f'Year {idxs[0]}, Price {idxs[1]}')


def create_plot(
        house_price = np.arange(50, 300, 50) * 1000,
        down_payment = np.arange(10, 10 + (5 * 6), 5) * 1000,
        interest_rate = np.linspace(1.5, 4, 6),
        years = np.arange(10, 45, 10),
        extra = np.arange(0, 1100, 100)
):
    fig, axs = plt.subplots(len(years), len(house_price))
    
    for y_idx in range(len(years)):
        for hp_idx in range(len(house_price)):
            print(f"Year: {years[y_idx]} -- House Price: {house_price[hp_idx]}€ -- Combinations: {len(down_payment) * len(interest_rate) * len(extra)}")
            for dp, ir, e in tqdm(itertools.product(down_payment, interest_rate, extra)):
                start = time.time()
                results = calculate_debt_overtime(
                    house_price = house_price[hp_idx],
                    down_payment=dp,
                    interest_rate=ir,
                    years=years[y_idx],
                    extra=e
                )
                print(time.time() - start)
                start = time.time()
                create_ind_plot(
                    results=results,
                    axs=axs,
                    idxs=(y_idx, hp_idx)
                )

                print(time.time() - start)
    
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    args = arg_parse()

    create_plot()