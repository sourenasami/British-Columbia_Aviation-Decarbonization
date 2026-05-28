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
npv_factor = 0
historical_jetA1_price = 16     # $/GJ
for i in range(1, year+1):
    npv_factor += 1 / (1 + discount_rate) ** i



class economic:

    def __init__(self, sample_size: int, year: int):
        self.sample_size = sample_size
        self.year = year
        self.capex_import = CAPEX.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=2, year=self.year).kde_estimation()[1].items()
        self.opex_import = OPEX.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=2, year=self.year).kde_estimation()[1]
        self.feedstock_import = feedstock.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=2, year=self.year).kde_estimation()[1]
        self.revenue_import = revenue.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=800, year=self.year, mode_MFSP=1).kde_Monte_Carlo()[3]
        self.capacity = CAPEX.cap_individual[self.year]



    def mfsp(self):
        """Implementing Monte Carlo simulation to obtain the distribution of the system MFSP in $/GJ"""

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
                        expenses_temp_capex += n[0][w] / (npv_factor * (1 - income_tax))
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
                                                mfsp_temp.append((expenses_temp * 1e6 / (self.capacity[m] * 8000))
                                                              * self.capacity[m] / sum(self.capacity.values()))         # $/GJ
                                            if expenses_temp_revenue != 0:
                                                break
                                    if expenses_temp_feedstock != 0:
                                        break
                            if expenses_temp_opex != 0:
                                break
                    if expenses_temp_capex != 0:
                        break

            if len(mfsp_temp) == len(self.revenue_import.keys()):
                mfsp.append(round(sum(mfsp_temp), 0))            # $/GJ
            else:
                continue




        """Frequency distribution of the system MFSP (histogram)"""
        mfsp_frequency = {}
        for i in mfsp:
            mfsp_frequency.setdefault(i, mfsp.count(i))
        mfsp_frequency_sorted = dict(sorted(mfsp_frequency.items()))

        """Relative frequency distribution of the system MFSP (Relative histogram)"""
        mfsp_relative_frequency = {}
        for m, n in mfsp_frequency_sorted.items():
            mfsp_relative_frequency.setdefault(m, n / len(mfsp))

        """Empirical PDF of the system MFSP"""
        mfsp_PDF = {}
        for m, n in mfsp_relative_frequency.items():
            mfsp_PDF.setdefault(m, n * 1.1 / ((max(mfsp) - min(mfsp)) /
                                              len(list(mfsp_frequency_sorted.keys()))))

        """Empirical CDF of the system MFSP"""
        mfsp_CDF = {}
        for m, n in mfsp_frequency_sorted.items():
            CDF_values = list(mfsp_CDF.values())
            counter = len(CDF_values)
            if counter == 0:
                mfsp_CDF.setdefault(m, n / len(mfsp))
            else:
                mfsp_CDF.setdefault(m, n / len(mfsp) + CDF_values[counter - 1])


        """This creates an excel file containing the PDF and CDF of the system MFSP at a specific period and sample size"""
        pdf_exel = pd.DataFrame(data=mfsp_PDF, index=[0])
        cdf_exel = pd.DataFrame(data=mfsp_CDF, index=[0])
        pdf_exel = pdf_exel.T
        cdf_exel = cdf_exel.T
        writer = pd.ExcelWriter(f'MFSP_system_{self.year}_{self.sample_size}.xlsx', mode='w')
        pdf_exel.to_excel(writer, sheet_name='PDF&CDF', header=False, startcol=1, startrow=0)
        cdf_exel.to_excel(writer, sheet_name='PDF&CDF', header=False, startcol=3, startrow=0)
        writer.close()


        return [mfsp_PDF, mfsp_CDF]




"""The more the number of sample_size, more accurate would be the results, but longer time is required"""
"""Periods must be considered as: 2030, '2040_base', '2040_SAF', '2050_base', '2050_SAF' """
sample = economic(sample_size=100, year='2040_base')
print(sample.mfsp())


