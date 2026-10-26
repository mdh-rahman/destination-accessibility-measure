# Build the Data Axle healthcare GeoPackage
#
# Runs after case-studies/austin/destinations/healthcare/02_clean_dataaxle_healthcare.R.
#
# Writes to case-studies/austin/data/destinations/healthcare/processed/:
#   healthcare_dataaxle.gpkg                    one layer per proposed type, all
#                                         map-ready candidates
#   healthcare_dataaxle_analysis_ready.csv      screened-in records only
#   healthcare_dataaxle_h7_counts.csv / _h8_counts.csv
#
# Run from the repository root:
#   Rscript case-studies/austin/destinations/healthcare/04_build_dataaxle_healthcare_gpkg.R

source("R/packages.R")
setup_project_packages(c("tidyverse", "digest", "sf", "h3jsr"))
source("case-studies/austin/destinations/R/destination_paths.R")
source("case-studies/austin/destinations/R/dataaxle_config.R")
source("case-studies/austin/destinations/R/dataaxle_helpers.R")

ax_build_destination("healthcare")
