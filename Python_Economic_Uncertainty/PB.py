import numpy as np
import random
import pandas as pd
import CAPEX
import OPEX
import feedstock
import revenue


"""Economic factors"""
discount_rate = 0.1
income_tax = 0.28
year = 25
year_h = 8000



class economic:

    def __init__(self, sample_size: int, year: int):
        self.sample_size = sample_size
        self.year = year
        self.capex_import = CAPEX.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=300, year=self.year).kde_Monte_Carlo()[1].items()
        self.opex_import = OPEX.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=300, year=self.year).kde_Monte_Carlo()[1].items()
        self.feedstock_import = feedstock.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=300, year=self.year).kde_Monte_Carlo()[1].items()
        self.revenue_import = revenue.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=300, year=self.year, mode_MFSP=0).kde_Monte_Carlo()[1].items()
        self.capacity = sum(list(CAPEX.cap_individual[self.year].values())) * year_h




    def pb(self):
        """Implementing Monte Carlo simulation to obtain the distribution of the system PB"""

        pb = []         # year
        decimal_number = 2
        for i in range(1, self.sample_size + 1):
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

                                            payback_1 = (1 - income_tax) * (expenses_temp_revenue - expenses_temp_opex - expenses_temp_feedstock)
                                            payback_2 = payback_1 - expenses_temp_capex * discount_rate
                                            if (payback_1 / payback_2) > 0:
                                                payback = np.log(payback_1 / payback_2) / np.log(1 + discount_rate)
                                                if payback != 0 and payback <= year and payback >= -year:
                                                    pb.append(round(payback, 0))        # year
                                        if expenses_temp_revenue != 0:
                                            break
                                if expenses_temp_feedstock != 0:
                                    break
                        if expenses_temp_opex != 0:
                            break
                if expenses_temp_capex != 0:
                    break




        """Frequency distribution of the system PB (histogram)"""
        pb_frequency = {}
        for i in pb:
            if i > 0:
                pb_frequency.setdefault(i, pb.count(i))
        pb_frequency_sorted = dict(sorted(pb_frequency.items()))

        """Relative frequency distribution of the system PB (Relative histogram)"""
        pb_relative_frequency = {}
        for m, n in pb_frequency_sorted.items():
            pb_relative_frequency.setdefault(m, n / len(pb))

        """Empirical PDF of the system PB"""
        pb_PDF = {}
        for m, n in pb_relative_frequency.items():
            pb_PDF.setdefault(m, n * 1.1 / ((max(pb) - min(list(pb_frequency_sorted.keys()))) /
                                            len(list(pb_frequency_sorted.keys()))))

        """Empirical CDF of the system PB"""
        pb_CDF = {}
        for m, n in pb_frequency_sorted.items():
            CDF_values = list(pb_CDF.values())
            counter = len(CDF_values)
            if counter == 0:
                pb_CDF.setdefault(m, n / len(pb))
            else:
                pb_CDF.setdefault(m, n / len(pb) + CDF_values[counter - 1])


        """This creates an excel file containing the PDF and CDF of the system PB at a specific period and sample size"""
        pdf_exel = pd.DataFrame(data=pb_PDF, index=[0])
        cdf_exel = pd.DataFrame(data=pb_CDF, index=[0])
        pdf_exel = pdf_exel.T
        cdf_exel = cdf_exel.T
        writer = pd.ExcelWriter(f'PB_system_{self.year}_{self.sample_size}.xlsx', mode='w')
        pdf_exel.to_excel(writer, sheet_name='PDF&CDF', header=False, startcol=1, startrow=0)
        cdf_exel.to_excel(writer, sheet_name='PDF&CDF', header=False, startcol=3, startrow=0)
        writer.close()


        return [pb_PDF, pb_CDF]




"""The more the number of sample_size, more accurate would be the results, but longer time is required"""
"""Periods must be considered as: 2030, '2040_base', '2040_SAF', '2050_base', '2050_SAF' """
sample = economic(sample_size=100, year='2040_base')
print(sample.pb())


