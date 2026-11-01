# Transit & Employment Accessibility — Abhijith's IDS section

This folder contains one independent, reproducible project section for the Omaha–Council Bluffs EPA Smart Location Database team project. It does **not** replace any teammate's work.

## Contents

- `Transit_Employment_Accessibility.Rmd` — **main deliverable** for the group's R Markdown workflow. Uses base R, with `knitr`/`rmarkdown` to render. Reads the root CSV; no Python required to knit.
- `Transit_Employment_Accessibility_Report.html` — revised Methods/Results report with planner-focused interpretation for each figure; open after extracting the full folder so relative images load.
- `Transit_Employment_Accessibility_Report_Standalone.html` — one-file revised HTML report with all five figures embedded; can be opened on its own.
- `VERIFICATION_NOTES.txt` — data/result integrity checks and the remaining RStudio Knit limitation.
- `Presentation_Summary.md` — slides/talking points for the final team presentation.
- `analysis_summary.txt` — quick QA figures.
- `figures/` — five publication-ready PNG charts.
- `results/` — clean output CSVs, including correlation/group comparison data, coverage table, relative-gap candidates and a cleaned analytic export.
- `reproduce_analysis.py` — optional Python script that rebuilds tables/figures/report (requires pandas, numpy, scipy, matplotlib).

## Data file placement

The filtered source CSV `EPA_SDL_OmahaCouncilBluffs.csv` belongs in the **repository root**, next to the team's `preliminaryEDA.Rmd`, *not* inside this folder. The full national EPA database is not required. Keep its name exactly as shown. The R Markdown script also supports the user's downloaded `(1)` filename as fallback.

Suggested repository structure:

```text
SDL-Project/
  EPA_SDL_OmahaCouncilBluffs.csv
  preliminaryEDA.Rmd
  abhijith/
    Transit_Employment_Accessibility.Rmd
    Transit_Employment_Accessibility_Report.html
    Presentation_Summary.md
    analysis_summary.txt
    README.md
    reproduce_analysis.py
    figures/
      01_coverage_by_county.png ...
    results/
      coverage_by_county.csv ...
```

## Feedback incorporated (November 1, 2026)

The report now separates **Methods** and **Results**. Methods contains data preparation, indicator definitions, missing-value handling, Spearman correlations, upper-quartile grouping, and the precise two-condition relative-gap screen. Results interprets Figures 1–5 with what each figure shows, why it matters, and possible use by city or regional planners. The 47 relative-gap candidates are presented as locations for follow-up evaluation using current GTFS, ridership and local data. Iowa-side missing values are explicitly **not** interpreted as no service or used for a direct Omaha–Council Bluffs comparison. The screening caveat reads **“not an official transit-service or planning standard.”**

Running `python reproduce_analysis.py` now regenerates both the figure-linked HTML and the standalone HTML, preserving this structure.

## How to use in RStudio

1. Open `Transit_Employment_Accessibility.Rmd` from the repo's `abhijith` folder.
2. Verify `../EPA_SDL_OmahaCouncilBluffs.csv` exists (one directory up).
3. Click **Knit** > **Knit to HTML**. If RStudio asks for dependencies, install `rmarkdown` and `knitr` once.
4. The rendered R Markdown section includes summary, data cleaning, coverage table, correlation table, five explanatory charts, screening candidates, planner-focused interpretation, and source citations.

All summary analyses have also been executed using the supplied filtered CSV in the included Python reproducer, with outputs available immediately. The R Markdown was authored to match those calculations, but the local environment did not contain `Rscript` to independently knit/verify its HTML here.

## Important data-integrity notes

- The provided `GEOID10` and `GEOID20` each have just **three** unique IDs despite **727** rows; they appear rounded/truncated. The reconstruction from `STATEFP` + `COUNTYFP` + `TRACTCE` + `BLKGRPCE` yields 727 unique **candidate** block group IDs. Confirm against an official geography file before GIS joins or maps. This report does not claim to have validated their spatial geometry.
- The EPA's sentinel `-99999` is **not zero**. It may denote a stop-distance cutoff or unavailable GTFS data. Missing transit job-access values are excluded, never interpreted as inadequate service.
- Missingness is highly geographically asymmetric, particularly for Pottawattamie County. Do not compare transit access across Omaha and Council Bluffs without accounting for it.
- The 2021 EPA SLD is historical; it is not current bus-service data. Correlations are descriptive, not causal.
- The low-access flag (top quartile car-free share AND below median measured transit job access) is a project-defined *relative screening heuristic*, not an official EPA benchmark.

## Source documentation

- https://www.epa.gov/smartgrowth/smart-location-mapping
- https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1014W9I.TXT
