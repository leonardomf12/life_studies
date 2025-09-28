import numpy as np
import matplotlib.pyplot as plt


if __name__ == '__main__':

    # Prices
    price_eletricity = 0.19 # €/kWh
    price_gas = 1.7 # €/L
    price_diesel = 1.6 # €/L

    # Frequency
    month_gas_ref = 60 # €/month
    car_gas_comsuption = 7 # L/100km
    car_ele_consumption = 69/(253 * 1.6093) # kWh/km
    month_km = month_gas_ref * (1/price_gas) * (100/car_gas_comsuption) # km/month

    print(month_km)

    # Cost
    t = np.arange(0, 20*12)
    total_cost_gas = t * month_gas_ref * 1e-3
    total_cost_eletricity = t * month_km * car_ele_consumption * price_eletricity * 1e-3


    fontsize = 15
    plt.figure()
    plt.plot(t, total_cost_gas, label='Total Gasoline (€)')
    plt.plot(t, total_cost_eletricity, label='Total Electricity (€)')
    plt.plot(t, total_cost_gas- total_cost_eletricity, label='Difference (€)')
    plt.xticks(fontsize=fontsize)
    plt.yticks(fontsize=fontsize)
    plt.xlabel('Month', fontsize=fontsize)
    plt.ylabel('Total Cost (k€)', fontsize=fontsize)
    plt.legend()
    plt.grid()
    plt.show()

