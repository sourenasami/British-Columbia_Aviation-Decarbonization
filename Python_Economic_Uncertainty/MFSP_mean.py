import random
import numpy as np
import pandas as pd

import CAPEX
import OPEX
import feedstock
import revenue


year = 25
year_h = 8000
historical_jetA1_price = 16     # $/GJ




class economic:

    def __init__(self, sample_size: int, year: int):
        self.sample_size = sample_size
        self.year = year
        self.mixing_factor = {2030: 0.1, '2040_base': 0.35, '2040_SAF': 0.35, '2050_base': 0.7, '2050_SAF': 0.7}
        self.capex_import = CAPEX.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=2, year=self.year).kde_estimation()[1].items()
        self.opex_import = OPEX.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=2, year=self.year).kde_estimation()[1]
        self.feedstock_import = feedstock.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=2, year=self.year).kde_estimation()[1]
        self.revenue_import = revenue.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=800, year=self.year, mode_MFSP=1).kde_Monte_Carlo()[3]
        self.capacity = CAPEX.cap_individual[self.year]




    def mfsp(self):
        """Implementing Monte Carlo simulation to obtain the distribution of the system mean MFSP in $/GJ
                against various discount rates and income tax rates"""

        discount_rate_range = [0.02, 0.06, 0.1, 0.14, 0.18]
        income_tax_range = [0, 0.1, 0.2, 0.3, 0.4]
        mfsp_mean = {}
        final_fuel_price_mean = {}
        for discount in discount_rate_range:
            npv_factor = 0
            for year_step in range(1, year + 1):
                npv_factor += 1 / (1 + discount) ** year_step

            mfsp_mean.setdefault(discount, [])
            final_fuel_price_mean.setdefault(discount, [])
            for tax in income_tax_range:
                mfsp = []
                decimal_number = 2
                for i in range(0, self.sample_size):
                    mfsp_temp = []
                    for m, n in self.capex_import:
                        expenses_temp = 0
                        expenses_temp_capex = 0
                        expenses_temp_opex = 0
                        expenses_temp_feedstock = 0
                        expenses_temp_revenue = 0
                        random_CDF_capex = random.uniform(0, 1)
                        for w, z in enumerate(n[-1]):
                            if round(random_CDF_capex, decimal_number) == round(z, decimal_number):
                                expenses_temp_capex += n[0][w] / (npv_factor * (1 - tax))
                                expenses_temp += expenses_temp_capex
                                random_CDF_opex = random.uniform(0, 1)
                                for a, b in enumerate(self.opex_import[m][-1]):
                                    if round(random_CDF_opex, decimal_number) == round(b, decimal_number):
                                        expenses_temp_opex += self.opex_import[m][0][a]
                                        expenses_temp += expenses_temp_opex
                                        random_CDF_feedstock = random.uniform(0, 1)
                                        for q, w in enumerate(self.feedstock_import[m][-1]):
                                            if round(random_CDF_feedstock, decimal_number) == round(w, decimal_number):
                                                expenses_temp_feedstock += self.feedstock_import[m][0][q]
                                                expenses_temp += expenses_temp_feedstock
                                                random_CDF_revenue = random.uniform(0, 1)
                                                for e, d in self.revenue_import[m].items():
                                                    if round(random_CDF_revenue, decimal_number) == round(d, decimal_number):
                                                        expenses_temp_revenue += e
                                                        expenses_temp -= expenses_temp_revenue
                                                        mfsp_temp.append(
                                                            (expenses_temp * 1e6 / (self.capacity[m] * 8000))
                                                            * self.capacity[m] / sum(self.capacity.values()))  # $/GJ
                                                    if expenses_temp_revenue != 0:
                                                        break
                                            if expenses_temp_feedstock != 0:
                                                break
                                    if expenses_temp_opex != 0:
                                        break
                            if expenses_temp_capex != 0:
                                break

                    if len(mfsp_temp) == len(self.revenue_import.keys()):
                        mfsp.append(round(sum(mfsp_temp), 0))       # $/GJ
                    else:
                        continue

                mean = np.mean(mfsp)
                mfsp_mean[discount].append(mean)
                final_fuel_price_mean[discount].append(mean * self.mixing_factor[self.year] +
                                                       historical_jetA1_price * (1 - self.mixing_factor[self.year]))



        """This creates an excel file containing the PDF and CDF of the system mean MFSP at a specific period and sample size"""
        writer = pd.ExcelWriter(f'MFSP_mean_output_{self.year}_{self.sample_size}.xlsx', mode='w')
        for i, j in enumerate(mfsp_mean.values()):
            mfsp_mean_exel = pd.DataFrame(data=j)
            mfsp_mean_exel.to_excel(writer, sheet_name='MFSP_mean', header=False, startcol=i*2, startrow=0)
        writer.close()


        return





"""A sample size of 5000 was considered for the current work"""
"""Periods must be considered as: 2030, '2040_base', '2040_SAF', '2050_base', '2050_SAF' """
sample = economic(sample_size=5000, year='2050_base')
print(sample.mfsp())



