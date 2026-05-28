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
crf = (discount_rate * (discount_rate + 1) ** year /
       ((discount_rate + 1) ** year - 1))
npv_factor = 0
for i in range(1, year + 1):
    npv_factor += 1 / (1 + discount_rate) ** i

"""Number of decimals for rounding the system NPV"""
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
        """Implementing Monte Carlo simulation to obtain the distribution of the system NPV in B$"""

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
                                                             (1 - income_tax) * npv_factor), MC_decimal[self.year]))         # M$
                                        if expenses_temp_revenue != 0:
                                            break
                                if expenses_temp_feedstock != 0:
                                    break
                        if expenses_temp_opex != 0:
                            break
                if expenses_temp_capex != 0:
                    break




        """Frequency distribution of the system NPV (histogram)"""
        npv_frequency = {}
        for i in npv:
            npv_frequency.setdefault(i, npv.count(i))
        npv_frequency_sorted = dict(sorted(npv_frequency.items()))

        """Relative frequency distribution of the system NPV (Relative histogram)"""
        npv_relative_frequency = {}
        for m, n in npv_frequency_sorted.items():
            npv_relative_frequency.setdefault(m, n / len(npv))

        """Empirical PDF of the system NPV"""
        npv_PDF = {}
        for m, n in npv_relative_frequency.items():
            npv_PDF.setdefault(m, n * 1.1 / ((max(npv) - min(npv)) /
                                              len(list(npv_frequency_sorted.keys()))))

        """Empirical CDF of the system NPV"""
        npv_CDF = {}
        for m, n in npv_frequency_sorted.items():
            CDF_values = list(npv_CDF.values())
            counter = len(CDF_values)
            if counter == 0:
                npv_CDF.setdefault(m, n / len(npv))
            else:
                npv_CDF.setdefault(m, n / len(npv) + CDF_values[counter - 1])


        """This creates an excel file containing the PDF and CDF of the system NPV at a specific period and sample size"""
        pdf_exel = pd.DataFrame(data=npv_PDF, index=[0])
        cdf_exel = pd.DataFrame(data=npv_CDF, index=[0])
        pdf_exel = pdf_exel.T
        cdf_exel = cdf_exel.T
        writer = pd.ExcelWriter(f'NPV_system_{self.year}_{self.sample_size}.xlsx', mode='w')
        pdf_exel.to_excel(writer, sheet_name='PDF&CDF', header=False, startcol=1, startrow=0)
        cdf_exel.to_excel(writer, sheet_name='PDF&CDF', header=False, startcol=3, startrow=0)
        writer.close()


        return [npv_PDF, npv_CDF]




"""The more the number of sample_size, more accurate would be the results, but longer time is required"""
"""Periods must be considered as: 2030, '2040_base', '2040_SAF', '2050_base', '2050_SAF' """
sample = economic(sample_size=100, year='2040_base')
print(sample.npv())



