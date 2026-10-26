# Build the City of Austin public library GeoPackage
#
# Runs after case-studies/austin/destinations/libraries/01_pull_austin_open_data_libraries.R.
#
# Reads the saved point records, screens coordinates, and keeps locations
# inside the 2024 City boundary buffered by destination_buffer_miles.
#
# Writes case-studies/austin/data/destinations/libraries/processed/:
#   libraries_austin_open_data.gpkg   layer: libraries
#   libraries_austin_open_data.csv
#
# Run from the repository root:
#   Rscript case-studies/austin/destinations/libraries/04_build_austin_open_data_libraries_gpkg.R

source("R/packages.R")
setup_project_packages(c("tidyverse", "sf", "tigris", "jsonlite", "h3jsr"))
source("case-studies/austin/destinations/R/destination_paths.R")
source("case-studies/austin/destinations/R/socrata_helpers.R")
options(tigris_use_cache = TRUE)

raw_path <- file.path(destination_dir("libraries", "raw", "austin_open_data", create = FALSE), "libraries.json")
if (!file.exists(raw_path)) stop("Missing ", raw_path, ". Run 01_pull_austin_open_data_libraries.R first.")

points <- normalize_socrata_points(raw_path, "libraries", category = "libraries", dataset_id = "tc36-hn4j",
                                   location_field = "address", name_field = "name")
build_austin_open_data_layer(points, "libraries", "libraries")
