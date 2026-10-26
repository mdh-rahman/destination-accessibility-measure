# Build the Data Axle parks GeoPackage
#
# Runs after case-studies/austin/destinations/parks/02_clean_dataaxle_parks.R.
#
# Writes to case-studies/austin/data/destinations/parks/processed/:
#   parks_dataaxle.gpkg                    one layer per proposed type, all
#                                         map-ready candidates
#   parks_dataaxle_analysis_ready.csv      screened-in records only
#   parks_dataaxle_h7_counts.csv / _h8_counts.csv
#
# Run from the repository root:
#   Rscript case-studies/austin/destinations/parks/04_build_dataaxle_parks_gpkg.R

source("R/packages.R")
setup_project_packages(c("tidyverse", "digest", "sf", "h3jsr"))
source("case-studies/austin/destinations/R/destination_paths.R")
source("case-studies/austin/destinations/R/dataaxle_config.R")
source("case-studies/austin/destinations/R/dataaxle_helpers.R")

ax_build_destination("parks")
