import random
from scipy.integrate import cumulative_trapezoid
from KDEpy import FFTKDE



"""Number of decimals for rounding the system CAPEX"""
MC_decimal = {2030: 2, '2040_base': 2, '2040_SAF': 2, '2050_base': 2, '2050_SAF': 2}

"""The ratio of CAPEX reduction for each decade compared to 2020"""
year_capexReduction = {2030: 1.34, '2040_base': 1.55, '2040_SAF': 1.55, '2050_base': 1.77, '2050_SAF': 1.77}

""""Capex of electrolysis, DAC, and CCS in $/kWel, $/tCO2/y, and $/kW, respectively"""
electrolysis_capex = {2030: 683, '2040_base': 508, '2040_SAF': 508, '2050_base': 394, '2050_SAF': 394}
DAC_capex = {2030: 420, '2040_base': 296, '2040_SAF': 296, '2050_base': 219, '2050_SAF': 219}
CCS_capex = {'BtL_FT_CCS': 77, 'PtL_CCS': 54, 'HEFA': 0, 'AtJ_starch': 0, 'GtL_ATR_CCS': 155}

"""CEPCI from 2005 to 2023"""
CEPCI_ref = {2005: 486, 2006: 500, 2007: 524, 2008: 575, 2009: 522, 2010: 550, 2011: 586, 2012: 585, 2013: 567,
             2014: 576, 2015: 592, 2016: 542, 2017: 567, 2018: 603, 2019: 607, 2020: 596, 2021: 656, 2022: 816, 2023: 803}
CEPCI_project = [2020, 596]

"""The average of cost scaling factor from the literature"""
cost_scaling_factor = 0.65

"""Production capacity of each pathway in GJ for base and SAF scenarios"""
cap_individual = {2030: {'BtL_FT_CCS': 728, 'PtL_CCS': 1232, 'HEFA': 0, 'AtJ_starch': 0, 'GtL_ATR_CCS': 0},
                               '2040_base': {'BtL_FT_CCS': 728, 'PtL_CCS': 3196, 'HEFA': 475, 'AtJ_starch': 272, 'GtL_ATR_CCS': 5629},
                               '2040_SAF': {'BtL_FT_CCS': 728, 'PtL_CCS': 9572, 'HEFA': 0, 'AtJ_starch': 0, 'GtL_ATR_CCS': 0},
                               '2050_base': {'BtL_FT_CCS': 728, 'PtL_CCS': 3196, 'HEFA': 475, 'AtJ_starch': 272, 'GtL_ATR_CCS': 22529},
                               '2050_SAF': {'BtL_FT_CCS': 728, 'PtL_CCS': 25725, 'HEFA': 475, 'AtJ_starch': 272, 'GtL_ATR_CCS': 0}}

"""CAPEX (M$), plant scale (GJ), and year of data points found in the literature for each pathway"""
reference_data = {'BtL_FT_CCS': [[670, 1157, 2015], [635, 720, 2023], [644, 903, 2018], [724, 1030, 2007], [2829, 4655, 2014]],
                               'PtL_CCS': [[379, 647, 2016], [365, 456, 2020], [428, 595, 2023], [293, 314, 2022], [1100, 1303, 2021]],
                               'HEFA': [[737, 4720, 2014], [151, 903, 2018], [74, 235, 2017], [156, 503, 2017],
                                        [230, 1143, 2016], [422, 1563, 2017], [565, 3300, 2021]],
                               'AtJ_starch': [[720, 4666, 2014], [390, 903, 2018], [383, 787, 2011], [300, 688, 2012]],
                               'GtL_ATR_CCS': [[690, 1018, 2020], [8160, 20640, 2015], [10800, 20296, 2008], [12000, 24080, 2008],
                                               [15000, 24080, 2008], [4200, 24080, 2006]]}




class KDE:

    def __init__(self, kernel: str, bandwidth: (str, int), sample_size: int, year: int):

        self.kernel = kernel
        self.bandwidth = bandwidth
        self.sample_size = sample_size
        self.year = year

        self.dataP_CAPEX_million = {}               # Processes CAPEX in MUS$
        self.dataP_CAPEX_transform = {}
        for i, j in reference_data.items():
            if cap_individual[self.year][i] == 0:
                continue
            else:
                self.dataP_CAPEX_million.setdefault(i, [])
                self.dataP_CAPEX_transform.setdefault(i, [])
                if i == 'PtL_CCS':
                    a_electrolysis = (electrolysis_capex[self.year] * cap_individual[self.year][i] * 1e6 / (0.416 * 3600 * 1e6))
                    a_DAC = (DAC_capex[self.year] * cap_individual[self.year][i] * 75 * 8000/(1e6*1e3))
                    a_CCS = (cap_individual[self.year][i] * CCS_capex[i] * 1e6 / (3600 * 1e6))
                    self.dataP_CAPEX_million[i].append((cap_individual[self.year][i] * 950 * year_capexReduction[2030] * 1e6
                                                       / (year_capexReduction[self.year] * 3600 * 1e6)) + a_electrolysis + a_DAC + a_CCS)
                    self.dataP_CAPEX_million[i].append((cap_individual[self.year][i] * 1998 * year_capexReduction[2030] * 1e6
                                                       / (year_capexReduction[self.year] * 3600 * 1e6)) + a_electrolysis + a_DAC + a_CCS)
                    for m in j:
                        a = ( a_electrolysis + a_DAC +
                              (m[0] / year_capexReduction[self.year]) * (cap_individual[self.year][i] / m[1]) ** cost_scaling_factor *
                             (CEPCI_project[-1] / CEPCI_ref[m[-1]]) + a_CCS)
                        self.dataP_CAPEX_million[i].append(a)
                else:
                    a_CCS = (cap_individual[self.year][i] * CCS_capex[i] * 1e6 / (3600 * 1e6))
                    for m in j:
                        a = ((m[0] / year_capexReduction[self.year]) * (cap_individual[self.year][i] / m[1]) ** cost_scaling_factor *
                             (CEPCI_project[-1] / CEPCI_ref[m[-1]])) + a_CCS
                        self.dataP_CAPEX_million[i].append(a)   # M$
                for n in self.dataP_CAPEX_million[i]:
                    self.dataP_CAPEX_transform[i].append((n - min(self.dataP_CAPEX_million[i])) /
                                                         (max(self.dataP_CAPEX_million[i]) - min(self.dataP_CAPEX_million[i])))




    def kde_estimation(self):
        """Finding the range of PDF and CDF values for the CAPEX of each pathway"""

        kde_CAPEX = {}
        for m, n in self.dataP_CAPEX_transform.items():
            x_kde, y_kde = FFTKDE(kernel=self.kernel, bw=self.bandwidth).fit(n).evaluate()
            kde_CAPEX.setdefault(m, [])
            x = []
            for a in x_kde:
                x.append(a * (max(self.dataP_CAPEX_million[m]) - min(self.dataP_CAPEX_million[m])) +
                         min(self.dataP_CAPEX_million[m]))
            y = []
            for f in y_kde:
                y.append(f / (max(self.dataP_CAPEX_million[m]) - min(self.dataP_CAPEX_million[m])))
            kde_CAPEX[m].append(x)
            kde_CAPEX[m].append(y)

        kde_cdf_CAPEX = {}
        for i, j in kde_CAPEX.items():
            kde_cdf_CAPEX.setdefault(i, [])
            kde_cdf_CAPEX[i].append(j[0])
            cdf = cumulative_trapezoid(j[-1], j[0], initial=0)
            cdf /= cdf[-1]
            kde_cdf_CAPEX[i].append(cdf)


        return [kde_CAPEX, kde_cdf_CAPEX]




    def kde_Monte_Carlo(self):

        kde_cdf_CAPEX = self.kde_estimation()

        """Implementing Monte Carlo simulation to obtain the distribution of the system CAPEX in B$"""
        capex_total = []
        for i in range(0, self.sample_size):
            capex_total_temporary = 0
            for m, n in kde_cdf_CAPEX[-1].items():
                random_CDF = random.uniform(0, 1)
                for j, k in enumerate(n[-1]):
                    if round(random_CDF, 2) == round(k, 2):
                        capex_total_temporary += kde_cdf_CAPEX[0][m][0][j]
                        break
            capex_total.append(round(capex_total_temporary / 1e3, MC_decimal[self.year]))


        """Frequency distribution of the system CAPEX (histogram)"""
        capex_total_frequency = {}
        for h in capex_total:
            capex_total_frequency.setdefault(h, capex_total.count(h))
        capex_total_frequency_sorted = dict(sorted(capex_total_frequency.items()))

        """Relative frequency distribution of the system CAPEX (Relative histogram)"""
        capex_total_relative_frequency = {}
        for a, b in capex_total_frequency_sorted.items():
            capex_total_relative_frequency.setdefault(a, b / self.sample_size)

        """Empirical PDF of the system CAPEX"""
        capex_total_PDF = {}
        for c, d in capex_total_relative_frequency.items():
            capex_total_PDF.setdefault(c, d * 1.1 / ((max(capex_total) - min(capex_total)) /
                                               len(list(capex_total_frequency_sorted.keys()))))

        """Empirical CDF of the system CAPEX"""
        capex_total_CDF = {}
        for e, f in capex_total_frequency_sorted.items():
            capex_total_CDF_values = list(capex_total_CDF.values())
            counter3 = len(capex_total_CDF_values)
            if counter3 == 0:
                capex_total_CDF.setdefault(e, f / self.sample_size)
            else:
                capex_total_CDF.setdefault(e, f / self.sample_size + capex_total_CDF_values[counter3 - 1])


        return [capex_total_PDF, capex_total_CDF]

