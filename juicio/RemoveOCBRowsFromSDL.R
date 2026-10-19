library(data.table)
library(tidyverse)

options(scipen = 999)

# ------------------------------------------------------------------------------
# 1. DEFINE OMAHA-COUNCIL BLUFFS CORE 3 COUNTIES
# ------------------------------------------------------------------------------
# Douglas County, NE   -> State 31, County 055
# Sarpy County, NE     -> State 31, County 153
# Pottawattamie, IA    -> State 19, County 155

omaha_core_counties <- data.frame(
  STATEFP  = c("31", "31", "19"),
  COUNTYFP = c("055", "153", "155")
)

# ------------------------------------------------------------------------------
# 2. READ FULL NATIONAL FILE & FILTER METRO ROWS
# ------------------------------------------------------------------------------
input_file  <- "EPA_SmartLocationDatabase_V3_Jan_2021_Final.csv"
output_file <- "EPA_SmartLocationDatabase_Omaha_Core3.csv"

# Fast read using data.table while keeping state/county FP zero-padded
sld_full <- fread(
  input_file,
  colClasses = c(STATEFP = "character", COUNTYFP = "character")
)

# Zero-pad FIPS codes to ensure 2-digit state and 3-digit county alignment
sld_full[, STATEFP := str_pad(STATEFP, width = 2, side = "left", pad = "0")]
sld_full[, COUNTYFP := str_pad(COUNTYFP, width = 3, side = "left", pad = "0")]

# Keep only rows corresponding to Douglas, Sarpy, and Pottawattamie counties
sld_omaha_core <- sld_full[omaha_core_counties, on = .(STATEFP, COUNTYFP), nomatch = 0]

# ------------------------------------------------------------------------------
# 3. WRITE EXPORT CSV
# ------------------------------------------------------------------------------
fwrite(sld_omaha_core, output_file)

cat("Successfully exported", nrow(sld_omaha_core), "block groups across", ncol(sld_omaha_core), 
    "columns to", output_file, "\n")