# Transit and Employment Accessibility — Presentation Notes

**Research question:** Does the concentration of households without a car align with measured transit service and access to employment in the Omaha–Council Bluffs three-county study area?

## Slide 1 — Research question and Methods

- **Dataset:** EPA Smart Location Database v3 (2021 release); 727 census block groups from Douglas, Sarpy and Pottawattamie counties.
- **Indicators:** zero-vehicle household share (`Pct_AO0`), stop distance (`D4A`), peak frequency (`D4C`), transit job accessibility (`D5BR`), automobile job accessibility (`D5AR`).
- **Approach:** nonmissing, pairwise Spearman rank correlations; observed group medians; a relative screening rule.
- **Screen:** at least **8.68%** car-free households (full-sample upper quartile) **and** observed transit-job accessibility below **9,975** (observed D5BR median).
- **Important:** missing EPA `-99999` values are unavailable, never interpreted as zero service. The screen is **not an official transit-service or planning standard**.

**Suggested figure:** `figures/01_coverage_by_county.png`.

## Slide 2 — Results: overall transit alignment

- Among observed block groups, car-free share correlates **positively** with modeled transit access to jobs (Spearman **ρ = +0.257**, n=362) and peak-service frequency (**ρ = +0.334**, n=291).
- Car-free share correlates **negatively** with observed walking distance to a qualifying transit stop (**ρ = −0.264**, n=362); negative means closer stops.
- The median transit-job score is **29,142** for the observed higher-car-free group versus **6,031** for other measured block groups. These are decay-weighted scores, not literal counts of distinct accessible jobs.
- **Planner relevance:** service appears generally concentrated in areas with more car-free households, but neither positive regional associations nor close stops establish adequate service in each neighborhood.

**Suggested figures:** `figures/02_carfree_vs_transit_jobs.png` and `figures/03_carfree_vs_stop_distance.png`.

## Slide 3 — Results: exceptions and screening candidates

- Despite favorable overall associations, **47 of 131** measured higher-car-free block groups meet the relative low-transit-job-access screening definition (**35.9%**).
- These are **candidates for further investigation, not proven transit deserts**.
- **Planner relevance:** validate geography, then investigate jobs reachable via current GTFS schedules, service frequency, ridership, reliability, transfers and walking access before considering intervention.

**Suggested figure:** `figures/04_transit_jobs_by_group.png` plus the table from `results/relative_gap_candidates.csv`.

## Slide 4 — Results, limitations and practical next steps

- D5BR is usable for **362/727** study block groups, but just **1/93 in Pottawattamie County**. Missing Iowa-side scores do **not** mean no transit; do **not** directly compare Omaha and Council Bluffs using these scores.
- `D5BR` versus `D5AR` is a **modeled, assumption-dependent** accessibility comparison, not a simple percent of the same jobs available by each mode.
- Three counties include places outside both city limits; reconstructed block-group IDs must be confirmed against official geography before plotting candidate locations.
- **Planner next step:** update with current GTFS and ridership data, verify actual trip times to jobs, and collect local feedback before using the shortlist to set service priorities.
- **Team integration:** intersect flags with Adithya's neighborhood archetypes and interpret alongside Juicio's prediction. Noah's comparisons should disclose the Iowa-side coverage limitation.

**Suggested figure:** `figures/05_transit_vs_auto_jobs.png`.

## 45-second speaking script

“My part evaluates transit and employment accessibility across 727 block groups in the Omaha–Council Bluffs region using the EPA Smart Location Database. I measured relationships between households without a car, stop distance, frequency and jobs accessible by transit. In the areas with available data, transit generally appears more accessible where car-free households are more common. But that regional pattern masks 47 higher-car-free block groups with below-median modeled access to jobs by transit. These are screening candidates rather than confirmed service gaps, and planners would need current GTFS schedules, ridership and local feedback before acting. Our biggest limitation is missing transit-job data in Iowa: just 1 of 93 Pottawattamie block groups has a usable score, so we cannot use missing data to claim no transit or to directly compare Omaha and Council Bluffs.”
