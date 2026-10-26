# Build the Data Axle community_organizations GeoPackage
#
# Runs after case-studies/austin/destinations/community_organizations/02_clean_dataaxle_community_organizations.R.
#
# Writes to case-studies/austin/data/destinations/community_organizations/processed/:
#   community_organizations_dataaxle.gpkg                    one layer per proposed type, all
#                                         map-ready candidates
#   community_organizations_dataaxle_analysis_ready.csv      screened-in records only
#   community_organizations_dataaxle_h7_counts.csv / _h8_counts.csv
#
# Run from the repository root:
#   Rscript case-studies/austin/destinations/community_organizations/04_build_dataaxle_community_organizations_gpkg.R

source("R/packages.R")
setup_project_packages(c("tidyverse", "digest", "sf", "h3jsr"))
source("case-studies/austin/destinations/R/destination_paths.R")
source("case-studies/austin/destinations/R/dataaxle_config.R")
source("case-studies/austin/destinations/R/dataaxle_helpers.R")

ax_build_destination("community_organizations")
