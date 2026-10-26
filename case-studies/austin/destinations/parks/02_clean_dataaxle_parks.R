# Standardize and screen Data Axle parks exports
#
# Source: Data Axle Reference Solutions, manual CSV exports (licensed; kept
#         out of git under data/). Put every export batch, unchanged, in
#         case-studies/austin/data/destinations/parks/raw/dataaxle/
#
# Reads all batches, merges repeated records, applies the NAICS screening rules
# in case-studies/austin/destinations/R/dataaxle_config.R, and applies documented manual decisions
# from case-studies/austin/data/destinations/manual/. No downloads or geocoding.
#
# Writes:
#   case-studies/austin/data/destinations/parks/interim/dataaxle/dataaxle_standardized.{rds,csv}
#   case-studies/austin/data/destinations/parks/qaqc/dataaxle/  (review, geocoding, duplicate queues)
#
# Run from the repository root:
#   Rscript case-studies/austin/destinations/parks/02_clean_dataaxle_parks.R

source("R/packages.R")
setup_project_packages(c("tidyverse", "digest", "sf", "h3jsr"))
source("case-studies/austin/destinations/R/destination_paths.R")
source("case-studies/austin/destinations/R/dataaxle_config.R")
source("case-studies/austin/destinations/R/dataaxle_helpers.R")

ax_clean_destination("parks")
