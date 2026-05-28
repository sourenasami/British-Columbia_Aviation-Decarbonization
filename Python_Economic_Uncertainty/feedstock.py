import random
from scipy.integrate import cumulative_trapezoid
from KDEpy import FFTKDE
import CAPEX


"""Number of decimals for rounding the system feedstock"""
MC_decimal = {2030: 3, '2040_base': 3, '2040_SAF': 3, '2050_base': 3, '2050_SAF': 3}

"Fuel conversion efficiency for each process"
eff_individual = {'BtL_FT_CCS': 0.443, 'PtL_CCS': 0.416, 'HEFA': 0.79, 'AtJ_starch': 0.74, 'GtL_ATR_CCS': 0.474}

"Range of feedstock prices for each pathway found in the literature"
dataP_feedstock = {'BtL_FT_CCS': [80, 106.6, 59.2, 76.8, 110.4, 72, 65.6, 124.8],
                                'PtL_CCS': [55.08, 88.2, 59.8, 56.9, 45, 87.12, 64.8, 79.9, 46.08],
                                'HEFA': [1028, 792, 810, 685, 571],
                                'AtJ_starch': [176, 158, 250, 283],
                                'GtL_ATR_CCS': [4.64, 10, 8, 2.77, 8.6, 11.1, 3.4]}                # forest residues in $/t, hydropower in $/MWh, canola oil in $/t, starchy crops in $/t, and NG in $/GJ



class KDE:

    def __init__(self, kernel: str, bandwidth: (str, int), sample_size: int, year: int):

        self.kernel = kernel
        self.bandwidth = bandwidth
        self.sample_size = sample_size
        self.year = year
        self.capex_import = CAPEX.KDE(kernel='gaussian', bandwidth='ISJ', sample_size=2, year=self.year)
        self.cap_individual = CAPEX.cap_individual[self.year]           # Production capacity of each pathway in GJ

        self.dataP_feedstock_million = {}
        for i, j in dataP_feedstock.items():
            if self.cap_individual[i] == 0:
                continue
            else:
                self.dataP_feedstock_million.setdefault(i, [])
                if i == 'PtL_CCS':
                    for p in j:
                        self.dataP_feedstock_million[i].append(p * self.cap_individual[i] * 8000 /
                                                               (eff_individual[i] * 3.6 * 1e6))
                elif i == 'BtL_FT_CCS' or i == 'HEFA' or i == 'AtJ_starch':
                    for p in j:
                        self.dataP_feedstock_million[i].append(p * self.cap_individual[i] * 8000 /
                                                               (eff_individual[i] * 0.016 * 1e3 * 1e6))
                else:
                    for p in j:
                        self.dataP_feedstock_million[i].append(p * self.cap_individual[i] * 8000 /
                                                               (eff_individual[i] * 1e6))

        self.dataP_feedstock_transform = {}
        for i, j in self.cap_individual.items():
            if j == 0:
                continue
            else:
                self.dataP_feedstock_transform.setdefault(i, [])
                for p in self.dataP_feedstock_million[i]:
                    self.dataP_feedstock_transform[i].append((p - min(self.dataP_feedstock_million[i])) /
                                                        (max(self.dataP_feedstock_million[i]) - min(self.dataP_feedstock_million[i])))




    def kde_estimation(self):
        """Finding the range of PDF and CDF values for the feedstock cost of each pathway"""

        kde_feedstock = {}
        for m, n in self.dataP_feedstock_transform.items():
            x_kde, y_kde = FFTKDE(kernel=self.kernel, bw=self.bandwidth).fit(n).evaluate()
            kde_feedstock.setdefault(m, [])
            x = []
            for a in x_kde:
                x.append(a * (max(self.dataP_feedstock_million[m]) - min(self.dataP_feedstock_million[m])) + min(self.dataP_feedstock_million[m]))
            y = []
            for f in y_kde:
                y.append(f / (max(self.dataP_feedstock_million[m]) - min(self.dataP_feedstock_million[m])))
            kde_feedstock[m].append(x)
            kde_feedstock[m].append(y)

        kde_cdf_feedstock = {}
        for i, j in kde_feedstock.items():
            kde_cdf_feedstock.setdefault(i, [])
            kde_cdf_feedstock[i].append(j[0])
            cdf = cumulative_trapezoid(j[-1], j[0], initial=0)
            cdf /= cdf[-1]
            kde_cdf_feedstock[i].append(cdf)


        return [kde_feedstock, kde_cdf_feedstock]




    def kde_Monte_Carlo(self):

        kde_cdf_feedstock = self.kde_estimation()

        """Implementing Monte Carlo simulation to obtain the distribution of the system feedstock cost in B$"""
        feedstock_total = []
        for i in range(0, self.sample_size):
            feedstock_total_temporary = 0
            for m, n in kde_cdf_feedstock[-1].items():
                random_CDF = random.uniform(0, 1)
                for j, k in enumerate(n[-1]):
                    if round(random_CDF, 2) == round(k, 2):
                        feedstock_total_temporary += kde_cdf_feedstock[0][m][0][j]
                        break
            feedstock_total.append(round(feedstock_total_temporary / 1e3, MC_decimal[self.year]))



        """Frequency distribution of the system feedstock (histogram)"""
        feedstock_total_frequency = {}
        for h in feedstock_total:
            feedstock_total_frequency.setdefault(h, feedstock_total.count(h))
        feedstock_total_frequency_sorted = dict(sorted(feedstock_total_frequency.items()))

        """Relative frequency distribution of the system feedstock (Relative histogram)"""
        feedstock_total_relative_frequency = {}
        for a, b in feedstock_total_frequency_sorted.items():
            feedstock_total_relative_frequency.setdefault(a, b / self.sample_size)

        """Empirical PDF of the system feedstock"""
        feedstock_total_PDF = {}
        for c, d in feedstock_total_relative_frequency.items():
            feedstock_total_PDF.setdefault(c, d * 1.1 / ((max(feedstock_total) - min(feedstock_total)) /
                                               len(list(feedstock_total_frequency_sorted.keys()))))

        """Empirical CDF of the system feedstock"""
        feedstock_total_CDF = {}
        for e, f in feedstock_total_frequency_sorted.items():
            feedstock_total_CDF_values = list(feedstock_total_CDF.values())
            counter3 = len(feedstock_total_CDF_values)
            if counter3 == 0:
                feedstock_total_CDF.setdefault(e, f / self.sample_size)
            else:
                feedstock_total_CDF.setdefault(e, f / self.sample_size + feedstock_total_CDF_values[counter3 - 1])


        return [feedstock_total_PDF, feedstock_total_CDF]

