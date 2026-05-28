import random
from scipy.integrate import cumulative_trapezoid
from KDEpy import FFTKDE
import CAPEX


"""Number of decimals for rounding the system OPEX"""
MC_decimal = {2030: 3, '2040_base': 3, '2040_SAF': 3, '2050_base': 3, '2050_SAF': 3}
opex_fix_factor = 0.03

"""OPEX of each pathway in $/MWh found in the literature"""
dataP_OPEX = {'BtL_FT_CCS': [35.6, 18, 13, 57, 81], 'PtL_CCS': [52.2, 53.2, 50, 49], 'HEFA': [11, 25, 9, 23, 12.6],
              'AtJ_starch': [13, 10, 21, 20], 'GtL_ATR_CCS': [18.6, 4.7, 21]}



class KDE:

    def __init__(self, kernel: str, bandwidth: (str, int), sample_size: int, year: int):

        self.kernel = kernel
        self.bandwidth = bandwidth
        self.sample_size = sample_size
        self.year = year
        self.capex_import = CAPEX.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=2, year=self.year)
        self.cap_individual = CAPEX.cap_individual[self.year]               # Production capacity of each pathway in GJ

        self.dataP_OPEX_million = {}
        for i, j in dataP_OPEX.items():
            if self.cap_individual[i] == 0:
                continue
            else:
                self.dataP_OPEX_million.setdefault(i, [])
                for p in j:
                    self.dataP_OPEX_million[i].append(p * self.cap_individual[i] * 8000 / (3.6 * 1e6))

        self.dataP_OPEX_transform = {}
        for i, j in self.cap_individual.items():
                if j == 0:
                    continue
                else:
                    self.dataP_OPEX_transform.setdefault(i, [])
                    for p in self.dataP_OPEX_million[i]:
                        self.dataP_OPEX_transform[i].append((p - min(self.dataP_OPEX_million[i])) /
                                                            (max(self.dataP_OPEX_million[i]) - min(self.dataP_OPEX_million[i])))





    def kde_estimation(self):
        """Finding the range of PDF and CDF values for the OPEX of each pathway"""

        kde_OPEX = {}
        for m, n in self.dataP_OPEX_transform.items():
            x_kde, y_kde = FFTKDE(kernel=self.kernel, bw=self.bandwidth).fit(n).evaluate()
            kde_OPEX.setdefault(m, [])
            x = []
            for a in x_kde:
                x.append(a * (max(self.dataP_OPEX_million[m]) - min(self.dataP_OPEX_million[m])) +
                         min(self.dataP_OPEX_million[m]))
            y = []
            for f in y_kde:
                y.append(f / (max(self.dataP_OPEX_million[m]) - min(self.dataP_OPEX_million[m])))
            kde_OPEX[m].append(x)
            kde_OPEX[m].append(y)

        kde_cdf_OPEX = {}
        for i, j in kde_OPEX.items():
            kde_cdf_OPEX.setdefault(i, [])
            kde_cdf_OPEX[i].append(j[0])
            cdf = cumulative_trapezoid(j[-1], j[0], initial=0)
            cdf /= cdf[-1]
            kde_cdf_OPEX[i].append(cdf)


        return [kde_OPEX, kde_cdf_OPEX]




    def kde_Monte_Carlo(self):

        kde_cdf_OPEX = self.kde_estimation()
        opex_fix_import = self.capex_import.kde_estimation()

        """Implementing Monte Carlo simulation to obtain the distribution of the system OPEX in B$"""
        opex_total = []
        for i in range(0, self.sample_size):
            opex_total_temporary = 0
            for m, n in kde_cdf_OPEX[-1].items():
                random_CDF = random.uniform(0, 1)
                for j, k in enumerate(n[-1]):
                    if round(random_CDF, 2) == round(k, 2):
                        opex_total_temporary += kde_cdf_OPEX[0][m][0][j]
                        break
            for m, n in opex_fix_import[-1].items():
                random_CDF = random.uniform(0, 1)
                for j, k in enumerate(n[-1]):
                    if round(random_CDF, 2) == round(k, 2):
                        opex_total_temporary += (opex_fix_import[0][m][0][j] * opex_fix_factor)
                        break
            opex_total.append(round(opex_total_temporary / 1e3, MC_decimal[self.year]))



        """Frequency distribution of the system OPEX (histogram)"""
        opex_total_frequency = {}
        for h in opex_total:
            opex_total_frequency.setdefault(h, opex_total.count(h))
        opex_total_frequency_sorted = dict(sorted(opex_total_frequency.items()))

        """Relative frequency distribution of the system OPEX (Relative histogram)"""
        opex_total_relative_frequency = {}
        for a, b in opex_total_frequency_sorted.items():
            opex_total_relative_frequency.setdefault(a, b / self.sample_size)

        """Empirical PDF of the system OPEX"""
        opex_total_PDF = {}
        for c, d in opex_total_relative_frequency.items():
            opex_total_PDF.setdefault(c, d * 1.1 / ((max(opex_total) - min(opex_total)) /
                                               len(list(opex_total_frequency_sorted.keys()))))

        """Empirical CDF of the system OPEX"""
        opex_total_CDF = {}
        for e, f in opex_total_frequency_sorted.items():
            capex_total_CDF_values = list(opex_total_CDF.values())
            counter3 = len(capex_total_CDF_values)
            if counter3 == 0:
                opex_total_CDF.setdefault(e, f / self.sample_size)
            else:
                opex_total_CDF.setdefault(e, f / self.sample_size + capex_total_CDF_values[counter3 - 1])


        return [opex_total_PDF, opex_total_CDF]

