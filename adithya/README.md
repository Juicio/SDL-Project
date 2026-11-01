# Adithya's neighborhood-archetype analysis

This folder contains the revised, portable report and its supporting analysis files.

## Knit the report

1. Keep this entire `adithya` folder together. Do not move the R Markdown file away from `results/`.
2. Open `Neighborhood_Archetypes_Report.Rmd` in RStudio.
3. Select **Knit > Knit to PDF**.

The report uses only three local PNG files from `results/`. It does not download Census geography, execute analysis code, or depend on an absolute path while knitting. The included `Neighborhood_Archetypes_Report.pdf` was compiled from this exact R Markdown source.

## Files used directly by the report

- `results/neighborhood_archetype_map.png`
- `results/cluster_profiles_zscore.png`
- `results/zero_car_households_by_cluster.png`

## Analysis and reproducibility

- `neighborhood_clustering.py` contains the clustering workflow.
- The remaining files in `results/` contain model-selection, cluster-profile, assignment, stability, and robustness outputs.

The report hides all code, avoids the previous oversized table, explains the results in planning language, places the map first in the Results section, and provides a caption below every figure.
