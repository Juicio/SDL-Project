# Integration instructions (transit section only)

**Do not replace the shared `variables.rmd` file.** Copy only relevant, non-duplicate definitions from `VARIABLES_TO_ADD_TO_SHARED_variables.rmd` and merge them in alphabetical order. The variable file includes dataset fields used in source preparation and descriptive analysis.

To merge the report, insert the text from `METHODS_for_team_paper.Rmd` under the main paper's Methods section, and insert the text from `RESULTS_for_team_paper.Rmd` under its Results section. The `abhijith_fig()` helper in the Results file resolves figure paths when knitted from the repository root or this folder. Keep the figure chunk labels as written: they generate numbered captions and allow LaTeX figure references during PDF rendering.

The analysis has been shortened to three principal figures: a comparison of modeled access to jobs by transit, a breakdown of the 47 relative-gap candidates and 51 higher-car-free records without scores, and a county-level data-coverage check. Supporting figures, code and detailed CSV tables remain in `figures/` and `results/`, but do not need to appear in the paper.

All comparisons are descriptive. Candidate block groups are a screening list, **not an official standard or confirmed transit deserts**. Do not claim the Iowa side has no service or compare Omaha versus Council Bluffs from the nearly absent Iowa-side measurements. Verify geographic identifiers before mapping specific candidates.

`Transit_Employment_Accessibility_Integration.Rmd` provides a standalone reference version with the same content. An independent PDF preview is included, but this environment has not run RStudio Knit, so the PDF knit step must still be checked in RStudio.
