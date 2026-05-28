# British Columbia-Python-Calliope
This repository contains Calliope and Python-based models designed to assess the potential of British Columbia, Canada,
to meet local jet fuel demand from 2030 to 2050, comparing both fossil and renewable pathways.

---

## Overview

There are two directories in this project, namely _Calliope_Modeling_ and _Economic_Uncertainty_.
- **_Calliope_Modeling_** contains the Calliope modeling files for the optimal planning of the base and SAF scenarios
from 2030 to 2050.
- **_Economic_Uncertainty_** includes Python files developed for economic uncertainty analysis.

The relevant files within each directory and their functions are explained in the following sections.

---

## Calliope modeling

For this research, Calliope version 0.6.10 was implemented. There are two directories within the main directory,
namely _configurations_ and _timeseries_data_:
- **_configurations_** includes all technologies defined in the system for all scenarios in the form of *.yaml files.
Additionally, _locations.yaml_ defines all modeled technologies along with the capacities of supply resources.
If the system is going to be run under different scenarios and decades, the decade name under _British_Columbia_2050_
must be changed, and irrelevant technologies must be hidden accordingly.
- **_timeseries_data_** includes a *.csv file that defines the production capacity of liquid fuels required for
each decade in GJ.

In the main directory, there is a single _model.yaml_ file. It defines the modeling configuration and the constraints for
limiting the production capacity of each technology under the base scenario.

---

## Economic uncertainty analysis

Within the _Economic_Uncertainty_ directory, Python files have been developed to simulate the effect of
uncertain input cost parameters on the economic behavior of the system. A Probabilistic Nonparametric Uncertainty method
was implemented for different scenarios and decades.

The mentioned files are divided into two categories:
- **CAPEX, OPEX, feedstock, and revenue** files form the cash flow of the system for a given scenario 
and decacde through the calculation of capital expenditure, operational expenditure, feedstock cost (raw input energies),
and revenue generated, respectively. Although running any of these files results in monitoring the 
relevant financial part of the system, the files are actually used to generate the economic 
analysis output of the study through MFSP, NPV, and PB. Among the mentioned files, OPEX, 
feedstock, and revenue depend on data included in the CAPEX and can not be used separately. 
- **MFSP, NPV, and PB** files are used to generate the minimum fuel selling price, net 
present value, and payback period of the system from the first category, respectively, before blending the 
produced synthetic jet fuel with conventional Jet A-1.

---

## Author

Sourena Sami    
Email: samisourena@gmail.com    
Google Scholar: https://scholar.google.com/citations?user=mQeEoOkAAAAJ&hl=en    
LinkedIn: https://www.linkedin.com/in/sourena-sami-b6556224b
