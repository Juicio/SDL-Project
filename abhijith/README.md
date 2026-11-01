# Transit and Employment Accessibility — clarified research-paper version

## What the analysis means
Transit access tends to be better in **measured neighborhoods with more car-free households**. Yet **47 higher-car-free block groups with transit-job data have comparatively low modeled access to employment**. Those 47 are candidates for further investigation, not confirmed transit deserts. Another 51 higher-car-free block groups could not be screened because transit employment data were missing.

## Files to share with the team
- `Transit_Employment_Accessibility_Clear_Report.pdf`: PDF report with paragraph-style Results, clear captions, and urban-planning implications. This PDF was typeset separately from RStudio.
- `Transit_Employment_Accessibility.Rmd`: aligned text and charts; R code hidden. It reads only `results/` and `figures/` within this folder. In RStudio, open it here and Knit to PDF or HTML (PDF Knit also needs a LaTeX distribution).
- `figures/`: five figures, beginning with the key 47-candidate finding.
- `results/`: descriptive tables and the candidate list.
- `reproduce_analysis.py`: optional detailed analysis code; requires original large dataset and creates a separate set of technical figures. Not required to Knit the report.

## Verification
Underlying results checked against the existing cleaned analysis files: 727 block groups; 362 measured transit-job observations; 182 higher-car-free block groups, including 131 measured and 51 unmeasured; 47 relative-gap screening candidates. PDF exported and checked visually. This environment cannot run RStudio Knit, so the R Markdown needs local testing before claiming that Knit-to-PDF succeeds.

## Uploading
Do not upload the ZIP itself into the existing team folder. Upload the contents of `abhijith` into the existing `SDL-Project/abhijith` directory, replacing superseded reports and figures as appropriate. The assistant has not made changes to the GitHub repository.
