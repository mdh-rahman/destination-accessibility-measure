# Download City of Austin public library locations
#
# Source: City of Austin Open Data (Socrata), dataset tc36-hn4j
#         https://data.austintexas.gov/d/tc36-hn4j
# Austin Public Library branches. Other library systems in the metro need separate sources.
#
# Writes case-studies/austin/data/destinations/libraries/raw/austin_open_data/libraries.json + libraries_manifest.json
#
# Run from the repository root:
#   Rscript case-studies/austin/destinations/libraries/01_pull_austin_open_data_libraries.R

source("R/packages.R")
setup_project_packages(c("tidyverse", "sf", "httr2", "jsonlite", "digest"))
source("case-studies/austin/destinations/R/destination_paths.R")
source("case-studies/austin/destinations/R/socrata_helpers.R")

pull_austin_open_data("libraries", layer_name = "libraries", dataset_id = "tc36-hn4j", format = "json")
