[![DOI](https://zenodo.org/badge/265254045.svg)](https://zenodo.org/doi/10.5281/zenodo.10442485)

# eldardiry-etal_2026

**Reservoir Drought Resilience Under Future Warming Scenarios: Regional Disparities Across Heavily Regulated US Basins**

Hisham Eldardiry<sup>1,2,3\*</sup>, Ning Sun<sup>1</sup>, and Nathalie Voisin<sup>1,4</sup>

<sup>1</sup> Pacific Northwest National Laboratory, Richland, WA, USA

<sup>2</sup> School of Civil and Environmental Engineering, Cornell University, Ithaca, NY, USA

<sup>3</sup> Faculty of Engineering, Alexandria University, Alexandria, Egypt

<sup>4</sup> University of Washington, Seattle, WA, USA

\* corresponding author: Hisham Eldardiry, hisham.eldardiry@cornell.edu

## Abstract
Reservoir drought, a form of hydrological drought, is characterized by abnormally low reservoir storage levels, reflecting combined impacts of natural water shortages and water management practices. Despite their profound impacts on water, energy, and agricultural sectors, systematic projections of how reservoir drought and resilience may evolve remain scarce. This study addresses this gap by quantifying shifts in reservoir drought signatures (onset, severity, duration, recovery and frequency) across five heavily regulated US basins under rising temperatures. By coupling atmosphere-land-river models with reservoir operations at ~12-km resolution, we simulated multi-decadal reservoir storage dynamics and characterized drought signatures for individual reservoirs. We follow a no-adaptation scenario, holding water demands and operational rules fixed, to isolate warming-driven stress on reservoir systems under present-day management conditions. Our findings reveal significant regional and functional disparities in reservoir drought resilience under the scenarios of rising temperature. Reservoirs in the Texas-Gulf region are projected to become more resilient, while systems in the Upper Colorado and South Atlantic-Gulf regions face increased risk due to prolonged drought durations (increasing by ~6–10 months) and slower recovery (with recovery times increasing by up to three- to fourfold). With respect to primary function, reservoirs used for irrigation and hydropower, particularly those with smaller storage capacity and lower degrees of regulation, are most susceptible to future drought stress. Overall, this study provides a novel continental-scale benchmark for reservoir droughts to support evolving multi-sectoral drought mitigation efforts.

## Journal reference
Eldardiry, H., Sun, N., and Voisin, N. (2026). Reservoir Drought Resilience Under Future Warming Scenarios: Regional Disparities Across Heavily Regulated US Basins. *Earth's Future*, 14(7), e2025EF007984.

## Code reference
_your software reference here_

## Data reference

### Input data
- TGW-WRF. https://tgw-data.msdlive.org/. DOI: https://doi.org/10.1038/s41597-023-02485-5, https://doi.org/10.57931/1885756
- GCAM-SELECT-Demeter. https://data.msdlive.org/records/vy529-6eg15. DOI: https://doi.org/10.57931/2502083

### Output data
- CLM5 soil moisture and GPP simulations. https://data.msdlive.org/uploads/v0j35-eqv54. DOI: https://doi.org/10.57931/3420371

## Contributing modeling software
| Model | Version | Repository Link | DOI |
|-------|---------|-----------------|-----|
| CLM5 | ctsm5.1.dev118 | https://github.com/IMMM-SFA/im3-clm | https://zenodo.org/records/6653705 |
| IM3 Components | 0cf45e8 | https://github.com/IMMM-SFA/im3components/tree/main/im3components/wrf_to_clm | |

## Reproduce my experiment
Clone the CLM5 repository ([https://github.com/ESCOMP/CTSM/tree/ctsm5.1.dev118](https://github.com/ESCOMP/CTSM/tree/ctsm5.1.dev118)) to set up the CLM5 model. You will need to download the TGW forcing data ([https://data.msdlive.org/records/ksw6r-2xv06](https://data.msdlive.org/records/ksw6r-2xv06)) and convert it into CLM input format using these scripts ([wrf_to_clm](https://github.com/IMMM-SFA/im3components/tree/main/im3components/wrf_to_clm)).

You will also need to replace the default CLM surface and land use timeseries files using data from GCAM-SELECT-Demeter ([https://data.msdlive.org/records/vy529-6eg15](https://data.msdlive.org/records/vy529-6eg15)). In addition, hydrological parameter values in the default parameter file and the user namelist file should be updated based on the behavioral parameter values ([https://data.msdlive.org/records/41bw1-3q739](https://data.msdlive.org/records/41bw1-3q739)).

The output data repository ([https://data.msdlive.org/uploads/v0j35-eqv54](https://data.msdlive.org/uploads/v0j35-eqv54)) already contains the soil moisture and GPP output from the CLM5 model, so you can skip rerunning the CLM5 model if you want to save time.

## Reproduce my figures
Use the scripts found in the "figures" directory to reproduce the drought resilience map and drought signature changes figure used in this publication.
