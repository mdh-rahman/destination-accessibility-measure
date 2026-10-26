# Download City of Austin recreation centers
#
# Source: City of Austin Open Data (Socrata), dataset 8dff-2vkt
#         https://data.austintexas.gov/d/8dff-2vkt
# City-operated recreation and community centers.
#
# Writes case-studies/austin/data/destinations/recreation_centers/raw/austin_open_data/recreation_centers.json + recreation_centers_manifest.json
#
# Run from the repository root:
#   Rscript case-studies/austin/destinations/recreation_centers/01_pull_austin_open_data_recreation_centers.R

source("R/packages.R")
setup_project_packages(c("tidyverse", "sf", "httr2", "jsonlite", "digest"))
source("case-studies/austin/destinations/R/destination_paths.R")
source("case-studies/austin/destinations/R/socrata_helpers.R")

pull_austin_open_data("recreation_centers", layer_name = "recreation_centers", dataset_id = "8dff-2vkt", format = "json")
