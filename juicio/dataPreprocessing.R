# ==============================================================================
# EPA Smart Location Database - Preprocessing & Pipeline Setup
# Metro Area: Omaha-Council Bluffs (Douglas, Sarpy, Pottawattamie Counties)
# Focus: Auto Dependency & Urban Equity Analysis
# ==============================================================================

# 1. Load Required Packages
library(tidyverse)
library(tidymodels)

# Set seed for reproducible cross-validation and sampling
set.seed(402)

# ==============================================================================
# 2. Data Loading & Flexible Preprocessing
# ==============================================================================

# Read raw dataset
raw_data <- read_csv("EPA_SDL_OmahaCouncilBluffs.csv", show_col_types = FALSE)

# Clean and transform features
clean_data <- raw_data %>%
  # Filter out non-residential block groups using 'HH' column
  filter(!is.na(HH) & HH > 0) %>%
  
  # Compute Target Variable: Average Vehicles per Household
  mutate(
    # Handle possible variations in AutoOwn column names
    Auto0  = coalesce(pick(any_of(c("AutoOwn0", "AUTOOWN0")))[[1]], 0),
    Auto1  = coalesce(pick(any_of(c("AutoOwn1", "AUTOOWN1")))[[1]], 0),
    Auto2p = coalesce(pick(any_of(c("AutoOwn2p", "AUTOOWN2P")))[[1]], 0),
    
    Avg_Vehicles = ((0 * Auto0) + (1 * Auto1) + (2 * Auto2p)) / HH
  ) %>%
  
  # Ensure transit and demographic variables are present and handle NAs
  mutate(
    # Replace NA transit metrics with 0 (areas outside active transit coverage)
    D4A = if ("D4A" %in% names(.)) coalesce(D4A, 0) else 0,
    D4D = if ("D4D" %in% names(.)) coalesce(D4D, 0) else 0,
    
    # Extract Walkability & Income with safe fallback defaults if absent
    NatWalkInd = if ("NatWalkInd" %in% names(.)) NatWalkInd else 1,
    MedIncome  = if ("MedIncome" %in% names(.)) MedIncome else if ("MEDINCOME" %in% names(.)) MEDINCOME else NA_real_,
    
    # Compute Engineered Equity Features & Interaction Ratios
    Forced_Car_Index  = Avg_Vehicles / (NatWalkInd + 1),
    Transit_Disparity  = MedIncome / (D4A + 1),
    
    # Extract County FIPS code for Spatial Group Cross-Validation (First 5 digits of GEOID)
    GEOID_str   = as.character(pick(any_of(c("GEOID10", "GEOID", "geoid10")))[[1]]),
    County_FIPS = as.factor(substr(GEOID_str, 1, 5))
  ) %>%
  
  # Select only predictor variables, target, grouping column, and identifier
  select(
    # Identifiers & Spatial Grouping
    GEOID10 = any_of(c("GEOID10", "GEOID", "geoid10")),
    County_FIPS,
    
    # Target Variable (y)
    Avg_Vehicles,
    
    # Predictor Features (Density, Diversity, Design, Transit, Demographics)
    any_of(c(
      "D1A", "D1C", "D2A_JENT", "D2B_E8MIX", "D3B", 
      "D4A", "D4D", "MedIncome", "Pct_LowInc", "NatWalkInd"
    )),
    
    # Engineered Equity Ratios
    Forced_Car_Index,
    Transit_Disparity
  )

# ==============================================================================
# 3. Train / Test Split & Spatial Group K-Fold Cross-Validation
# ==============================================================================

# Initial 80/20 train/test split stratified by County FIPS to maintain geographical balance
data_split <- initial_split(clean_data, prop = 0.80, strata = County_FIPS)
train_data <- training(data_split)
test_data  <- testing(data_split)

# Spatial Cross-Validation: Group K-Fold by County/Sub-region (County_FIPS)
# Prevents spatial autocorrelation leakage between adjacent census blocks across training folds
spatial_cv_folds <- group_vfold_cv(train_data, group = County_FIPS)

# ==============================================================================
# 4. Feature Engineering Recipe (`tidymodels`)
# ==============================================================================

# Define tidymodels processing recipe
prep_recipe <- recipe(Avg_Vehicles ~ ., data = train_data) %>%
  # Keep identifiers for tracking but do not use them as training predictors
  update_role(GEOID10, County_FIPS, new_role = "ID") %>%
  
  # Impute any remaining missing numeric values using median strategy
  step_impute_median(all_numeric_predictors()) %>%
  
  # Remove near-zero variance predictors
  step_nzv(all_numeric_predictors()) %>%
  
  # Center and scale numeric features (critical for regularized linear models)
  step_normalize(all_numeric_predictors())

# Fit recipe parameters explicitly on training set
prepped_recipe_fit <- prep(prep_recipe, training = train_data)

# Process and extract clean matrices
X_train_preprocessed <- bake(prepped_recipe_fit, new_data = NULL)
X_test_preprocessed  <- bake(prepped_recipe_fit, new_data = test_data)

# ==============================================================================
# 5. Output Verification
# ==============================================================================

cat("Preprocessing Complete!\n")
cat("--------------------------------------------------\n")
cat("Training Set Rows: ", nrow(X_train_preprocessed), "\n")
cat("Testing Set Rows:  ", nrow(X_test_preprocessed), "\n")
cat("Spatial CV Folds:  ", length(spatial_cv_folds$splits), "\n")
cat("Predictors Count:  ", ncol(X_train_preprocessed) - 3, "\n") # Excludes target & 2 IDs
cat("--------------------------------------------------\n")

# Preview prepared data structure
glimpse(X_train_preprocessed)

