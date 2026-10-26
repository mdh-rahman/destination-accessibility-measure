# Build the Data Axle libraries GeoPackage
#
# Runs after case-studies/austin/destinations/libraries/02_clean_dataaxle_libraries.R.
#
# Writes to case-studies/austin/data/destinations/libraries/processed/:
#   libraries_dataaxle.gpkg                    one layer per proposed type, all
#                                         map-ready candidates
#   libraries_dataaxle_analysis_ready.csv      screened-in records only
#   libraries_dataaxle_h7_counts.csv / _h8_counts.csv
#
# Run from the repository root:
#   Rscript case-studies/austin/destinations/libraries/04_build_dataaxle_libraries_gpkg.R

source("R/packages.R")
setup_project_packages(c("tidyverse", "digest", "sf", "h3jsr"))
source("case-studies/austin/destinations/R/destination_paths.R")
source("case-studies/austin/destinations/R/dataaxle_config.R")
source("case-studies/austin/destinations/R/dataaxle_helpers.R")

ax_build_destination("libraries")
