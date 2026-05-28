import random
import pandas as pd
import numpy as np

import CAPEX
import OPEX
import feedstock
import revenue


year = 25
year_h = 8000
MC_decimal = {2030: 1, '2040_base': 0, '2040_SAF': 0, '2050_base': 0, '2050_SAF': 0}



class economic:

    def __init__(self, sample_size: int, year: int):
        self.sample_size = sample_size
        self.year = year
        self.capex_import = CAPEX.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=300, year=self.year).kde_Monte_Carlo()[1].items()
        self.opex_import = OPEX.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=300, year=self.year).kde_Monte_Carlo()[1].items()
        self.feedstock_import = feedstock.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=300, year=self.year).kde_Monte_Carlo()[1].items()
        self.revenue_import = revenue.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=300, year=self.year, mode_MFSP=0).kde_Monte_Carlo()[1].items()
        self.capacity = sum(list(CAPEX.cap_individual[self.year].values())) * year_h





    def npv(self):
        """Implementing Monte Carlo simulation to obtain the distribution of the system mean NPV in B$
        against various discount rates and income tax rates"""

        discount_rate_range = [0.02, 0.06, 0.1, 0.14, 0.18]
        income_tax_range = [0, 0.1, 0.2, 0.3, 0.4]
        npv_mean = {}
        for discount in discount_rate_range:
            npv_factor = 0
            for year_step in range(1, year + 1):
                npv_factor += 1 / (1 + discount) ** year_step

            npv_mean.setdefault(discount, [])
            for tax in income_tax_range:
                npv = []
                decimal_number = 2
                for i in range(0, self.sample_size):
                    expenses_temp_capex = 0
                    expenses_temp_opex = 0
                    expenses_temp_feedstock = 0
                    expenses_temp_revenue = 0
                    random_CDF_capex = random.uniform(0, 1)
                    for m, n in self.capex_import:
                        if round(random_CDF_capex, decimal_number) == round(n, decimal_number):
                            expenses_temp_capex += m
                            random_CDF_opex = random.uniform(0, 1)
                            for a, b in self.opex_import:
                                if round(random_CDF_opex, decimal_number) == round(b, decimal_number):
                                    expenses_temp_opex += a
                                    random_CDF_feedstock = random.uniform(0, 1)
                                    for q, w in self.feedstock_import:
                                        if round(random_CDF_feedstock, decimal_number) == round(w, decimal_number):
                                            expenses_temp_feedstock += q
                                            random_CDF_revenue = random.uniform(0, 1)
                                            for e, d in self.revenue_import:
                                                if round(random_CDF_revenue, decimal_number) == round(d, decimal_number):
                                                    expenses_temp_revenue += e
                                                    npv.append(round((-expenses_temp_capex +
                                                                      (expenses_temp_revenue - expenses_temp_opex - expenses_temp_feedstock) *
                                                                     (1 - tax) * npv_factor), MC_decimal[self.year]))         # M$
                                                if expenses_temp_revenue != 0:
                                                    break
                                        if expenses_temp_feedstock != 0:
                                            break
                                if expenses_temp_opex != 0:
                                    break
                        if expenses_temp_capex != 0:
                            break

                mean = np.mean(npv)
                npv_mean[discount].append(mean)



        """This creates an excel file containing the PDF and CDF of the system mean NPV at a specific period and sample size"""
        writer = pd.ExcelWriter(f'NPV_mean_output_{self.year}_{self.sample_size}.xlsx', mode='w')
        for i, j in enumerate(npv_mean.values()):
            npv_mean_exel = pd.DataFrame(data=j)
            npv_mean_exel.to_excel(writer, sheet_name='NPV_mean', header=False, startcol=i*2, startrow=0)
        writer.close()


        return




"""A sample size of 50000 was considered for the current work"""
"""Periods must be considered as: 2030, '2040_base', '2040_SAF', '2050_base', '2050_SAF' """
sample = economic(sample_size=10000, year='2040_base')
print(sample.npv())


