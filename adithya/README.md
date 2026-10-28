# Adithya's analysis: neighborhood archetypes

This folder contains the unsupervised-learning portion of the Omaha-Council Bluffs Smart Location Database project.

## Main files

- `neighborhood_clustering.py`: cleans the selected variables, standardizes them, compares K-means solutions for `k = 2` through `8`, fits the five-cluster model, and exports the results.
- `Neighborhood_Archetypes_Report.Rmd`: report-ready explanation, tables, figures, statistical comparison, and an archetype map.
- `results/`: generated cluster assignments, profiles, validation tables, and figures.

## Run the analysis

Open a terminal in the repository's top-level folder and run:

```bash
python adithya/neighborhood_clustering.py
```

Required Python packages are `pandas`, `numpy`, `scipy`, `scikit-learn`, and `matplotlib`.

After the results are generated, open `Neighborhood_Archetypes_Report.Rmd` in RStudio and knit it. The map requires the R packages `tidyverse`, `sf`, `tigris`, `scales`, and `knitr`.

## Modeling choices

The model uses six dimensions:

| SLD field | Use |
|---|---|
| `D1B` | Population density |
| `D1C` | Employment density |
| `D2A_EPHHM` | Employment-household land-use mix |
| `D3B` | Weighted street-intersection density |
| `D4A_Ranked` | Transit access, including an explicit no-service rank |
| `D5CRI` | Automobile access to regional jobs |

`Pct_AO0`, the share of households without a vehicle, is not used to form the clusters. It is compared across clusters afterward, which keeps it independent from the clustering inputs and complements the group's supervised vehicle-ownership analysis.

## Robustness validation

The script performs 50 random-initialization checks, 100 refits using independently selected 80% subsamples, a comparison with Ward hierarchical clustering, five alternative feature specifications, and cluster-level silhouette diagnostics. The generated files are:

- `results/stability_runs.csv`
- `results/robustness_comparisons.csv`
- `results/cluster_silhouette_summary.csv`
- `results/robustness_validation.png`

## Geographic scope

The source file contains 727 census block groups from Douglas and Sarpy Counties in Nebraska and Pottawattamie County in Iowa. Results should be described as applying to the three-county Omaha-Council Bluffs study area, not strictly to the Omaha and Council Bluffs city limits.

## Source

U.S. Environmental Protection Agency, *Smart Location Database Technical Documentation and User Guide, Version 3.0*, 2021: https://www.epa.gov/sites/default/files/2021-06/documents/epa_sld_3.0_technicaldocumentationuserguide_may2021.pdf
