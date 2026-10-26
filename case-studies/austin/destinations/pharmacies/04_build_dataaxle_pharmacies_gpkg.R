# Build the Data Axle pharmacies GeoPackage
#
# Runs after case-studies/austin/destinations/pharmacies/02_clean_dataaxle_pharmacies.R.
#
# Writes to case-studies/austin/data/destinations/pharmacies/processed/:
#   pharmacies_dataaxle.gpkg                    one layer per proposed type, all
#                                         map-ready candidates
#   pharmacies_dataaxle_analysis_ready.csv      screened-in records only
#   pharmacies_dataaxle_h7_counts.csv / _h8_counts.csv
#
# Run from the repository root:
#   Rscript case-studies/austin/destinations/pharmacies/04_build_dataaxle_pharmacies_gpkg.R

source("R/packages.R")
setup_project_packages(c("tidyverse", "digest", "sf", "h3jsr"))
source("case-studies/austin/destinations/R/destination_paths.R")
source("case-studies/austin/destinations/R/dataaxle_config.R")
source("case-studies/austin/destinations/R/dataaxle_helpers.R")

ax_build_destination("pharmacies")
