#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(dplyr)
  library(httr2)
  library(jsonlite)
  library(readr)
  library(sf)
  library(tidyr)
  library(yaml)
})

root <- normalizePath(file.path(dirname(sub("--file=", "", commandArgs()[grep("--file=", commandArgs())])), "../.."), mustWork = TRUE)
cfg <- yaml::read_yaml(file.path(root, "population-access/config.yml"))
at_root <- function(path) file.path(root, path)
raw_dir <- at_root(cfg$paths$raw); processed_dir <- at_root(cfg$paths$processed)
dir.create(raw_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(processed_dir, recursive = TRUE, showWarnings = FALSE)

download_atomic <- function(url, path) {
  if (file.exists(path)) return(path)
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  temporary <- paste0(path, ".partial")
  on.exit(unlink(temporary), add = TRUE)
  response <- request(url) |> req_timeout(180) |> req_perform()
  writeBin(resp_body_raw(response), temporary)
  if (!file.rename(temporary, path)) stop("Could not finalize download: ", path)
  path
}

sum_codes <- function(...) unlist(list(...), use.names = FALSE)
groups <- list(
  total_population = list(label = "Total population", unit = "person", denominator = "total_population", codes = "B01001_001"),
  children_under_5 = list(label = "Children under 5", unit = "person", denominator = "total_population", codes = c("B01001_003", "B01001_027")),
  children_under_18 = list(label = "Children under 18", unit = "person", denominator = "total_population", codes = c(paste0("B01001_00", 3:6), paste0("B01001_0", 27:30))),
  adults_65_plus = list(label = "Adults age 65 and older", unit = "person", denominator = "total_population", codes = c(paste0("B01001_0", 20:25), paste0("B01001_0", 44:49))),
  poverty_universe = list(label = "Poverty-status universe", unit = "person", denominator = "poverty_universe", codes = "C17002_001", display = FALSE),
  below_poverty = list(label = "People below poverty", unit = "person", denominator = "poverty_universe", codes = c("C17002_002", "C17002_003")),
  below_200_poverty_universe = list(label = "Income-to-poverty universe", unit = "person", denominator = "below_200_poverty_universe", codes = "C17002_001", display = FALSE),
  below_200_poverty = list(label = "People below 200% of poverty", unit = "person", denominator = "below_200_poverty_universe", codes = paste0("C17002_00", 2:7)),
  disability_universe = list(label = "Civilian noninstitutionalized population", unit = "person", denominator = "disability_universe", codes = "B18101_001", display = FALSE, geography = "tract"),
  people_with_disability = list(label = "People with a disability", unit = "person", denominator = "disability_universe", codes = c("B18101_004","B18101_007","B18101_010","B18101_013","B18101_016","B18101_019","B18101_023","B18101_026","B18101_029","B18101_032","B18101_035","B18101_038"), geography = "tract"),
  race_ethnicity_universe = list(label = "Race and ethnicity universe", unit = "person", denominator = "race_ethnicity_universe", codes = "B03002_001", display = FALSE),
  nh_white_alone = list(label = "Non-Hispanic White alone", unit = "person", denominator = "race_ethnicity_universe", codes = "B03002_003"),
  people_of_color = list(label = "People of color", unit = "person", denominator = "race_ethnicity_universe", subtract = c("B03002_001", "B03002_003")),
  black_nh = list(label = "Black, non-Hispanic", unit = "person", denominator = "race_ethnicity_universe", codes = "B03002_004"),
  aian_nh = list(label = "American Indian or Alaska Native, non-Hispanic", unit = "person", denominator = "race_ethnicity_universe", codes = "B03002_005", display = FALSE),
  asian_nh = list(label = "Asian, non-Hispanic", unit = "person", denominator = "race_ethnicity_universe", codes = "B03002_006", display = FALSE),
  nhpi_nh = list(label = "Native Hawaiian or Pacific Islander, non-Hispanic", unit = "person", denominator = "race_ethnicity_universe", codes = "B03002_007", display = FALSE),
  other_multiracial_nh = list(label = "Other or multiracial, non-Hispanic", unit = "person", denominator = "race_ethnicity_universe", codes = c("B03002_008", "B03002_009"), display = FALSE),
  other_nh = list(label = "Other non-Hispanic residents", unit = "person", denominator = "race_ethnicity_universe", codes = paste0("B03002_00", 5:9)),
  hispanic_latino = list(label = "Hispanic or Latino", unit = "person", denominator = "race_ethnicity_universe", codes = "B03002_012"),
  vehicle_household_universe = list(label = "Occupied housing units reporting vehicle availability", unit = "household", denominator = "vehicle_household_universe", codes = "B25044_001", display = FALSE),
  no_vehicle_households = list(label = "Households with no vehicle", unit = "household", denominator = "vehicle_household_universe", codes = c("B25044_003", "B25044_010")),
  language_household_universe = list(label = "Households reporting language", unit = "household", denominator = "language_household_universe", codes = "C16002_001", display = FALSE),
  limited_english_households = list(label = "Limited-English-speaking households", unit = "household", denominator = "language_household_universe", codes = c("C16002_004", "C16002_007", "C16002_010", "C16002_013")),
  children_household_universe = list(label = "All households", unit = "household", denominator = "children_household_universe", codes = "B11005_001"),
  households_with_children = list(label = "Households with people under 18", unit = "household", denominator = "children_household_universe", codes = "B11005_002")
)

group_geography <- function(x) if (is.null(x$geography)) "block_group" else x$geography
fetch_acs <- function(county, geography, codes) {
  county_dir <- file.path(raw_dir, paste0("acs", cfg$acs_year, "_5year")); dir.create(county_dir, recursive = TRUE, showWarnings = FALSE)
  tables <- unique(sub("_.*$", "", codes))
  geo_code <- if (geography == "block_group") "150" else "140"
  geo_short <- if (geography == "block_group") "bg" else "tract"
  path <- file.path(county_dir, sprintf("acs%s_48%s_%s_censusreporter.json", cfg$acs_year, county, geo_short))
  if (!file.exists(path)) {
    url <- paste0("https://api.censusreporter.org/1.0/data/show/latest?table_ids=",
                  paste(tables, collapse = ","), "&geo_ids=", geo_code, "%7C05000US48", county)
    response <- request(url) |> req_timeout(180) |> req_perform()
    writeBin(resp_body_raw(response), path)
  }
  payload <- fromJSON(path, simplifyVector = FALSE)
  expected_release <- paste0("acs", cfg$acs_year, "_5yr")
  if (is.null(payload$release$id) || payload$release$id != expected_release) {
    stop("Census Reporter did not return the configured ACS release for county ", county)
  }
  rows <- lapply(names(payload$data), function(geoid) {
    estimate <- error <- setNames(rep(NA_real_, length(codes)), codes)
    for (table in tables) {
      table_data <- payload$data[[geoid]][[table]]
      table_codes <- codes[sub("_.*$", "", codes) == table]
      keys <- gsub("_", "", table_codes)
      estimate[table_codes] <- unlist(table_data$estimate[keys], use.names = FALSE)
      error[table_codes] <- unlist(table_data$error[keys], use.names = FALSE)
    }
    id <- sub(paste0("^", geo_code, "00US"), "", geoid)
    values <- c(as.list(setNames(estimate, paste0(names(estimate), "E"))),
                as.list(setNames(error, paste0(names(error), "M"))))
    c(list(NAME = payload$geography[[geoid]]$name, state = substr(id, 1, 2), county = substr(id, 3, 5),
           tract = substr(id, 6, 11), `block group` = if (geography == "block_group") substr(id, 12, 12) else NA_character_, GEOID = id), values)
  })
  bind_rows(rows)
}

component <- function(data, spec, suffix) {
  codes <- if (!is.null(spec$codes)) spec$codes else spec$subtract
  values <- data[paste0(codes, suffix)]
  if (!is.null(spec$subtract)) values[[2]] <- -values[[2]]
  if (suffix == "M") sqrt(rowSums(values^2, na.rm = FALSE)) else rowSums(values, na.rm = FALSE)
}
prepare_acs <- function(geography) {
  ids <- names(groups)[vapply(groups, group_geography, character(1)) == geography]
  codes <- unique(unlist(lapply(groups[ids], function(x) c(x$codes, x$subtract)), use.names = FALSE))
  raw <- bind_rows(lapply(unname(unlist(cfg$counties)), fetch_acs, geography = geography, codes = codes))
  for (field in setdiff(names(raw), c("NAME", "state", "county", "tract", "block group", "GEOID"))) {
    raw[[field]] <- suppressWarnings(as.numeric(raw[[field]])); raw[[field]][raw[[field]] < -1e7] <- NA_real_
  }
  result <- select(raw, GEOID, NAME, county)
  for (id in ids) {
    result[[id]] <- component(raw, groups[[id]], "E")
    result[[paste0(id, "_moe")]] <- component(raw, groups[[id]], "M")
  }
  result
}
acs_bg <- prepare_acs("block_group")
acs_tract <- prepare_acs("tract")

dictionary <- bind_rows(lapply(names(groups), function(id) {
  x <- groups[[id]]
  data.frame(group_id = id, label = x$label, unit = x$unit, denominator = x$denominator,
             display = if (is.null(x$display)) TRUE else x$display,
             source_geography = group_geography(x),
             acs_variables = paste(c(x$codes, x$subtract), collapse = ";"), acs_year = cfg$acs_year,
             stringsAsFactors = FALSE)
}))
write_csv(dictionary, file.path(processed_dir, "population_group_dictionary.csv"))

bg_zip <- file.path(raw_dir, sprintf("cb_%s_48_bg_500k.zip", cfg$boundary_year))
download_atomic(sprintf("https://www2.census.gov/geo/tiger/GENZ%s/shp/cb_%s_48_bg_500k.zip", cfg$boundary_year, cfg$boundary_year), bg_zip)
bg_dir <- sub("\\.zip$", "", bg_zip); if (!dir.exists(bg_dir)) unzip(bg_zip, exdir = bg_dir)
bg <- st_read(list.files(bg_dir, "\\.shp$", full.names = TRUE)[1], quiet = TRUE) |>
  filter(COUNTYFP %in% unname(unlist(cfg$counties))) |>
  select(GEOID, geometry) |>
  left_join(acs_bg, by = "GEOID") |>
  st_transform(4326)
if (any(is.na(bg$total_population))) stop("ACS records did not match all five-county block groups.")
st_write(bg, file.path(processed_dir, "block_group_demographics.gpkg"), delete_dsn = TRUE, quiet = TRUE)

tract_zip <- file.path(raw_dir, sprintf("cb_%s_48_tract_500k.zip", cfg$boundary_year))
download_atomic(sprintf("https://www2.census.gov/geo/tiger/GENZ%s/shp/cb_%s_48_tract_500k.zip", cfg$boundary_year, cfg$boundary_year), tract_zip)
tract_dir <- sub("\\.zip$", "", tract_zip); if (!dir.exists(tract_dir)) unzip(tract_zip, exdir = tract_dir)
tracts <- st_read(list.files(tract_dir, "\\.shp$", full.names = TRUE)[1], quiet = TRUE) |>
  filter(COUNTYFP %in% unname(unlist(cfg$counties))) |> select(GEOID, geometry) |>
  left_join(acs_tract, by = "GEOID") |> st_transform(4326)
if (any(is.na(tracts$disability_universe))) stop("ACS disability records did not match all five-county tracts.")
st_write(tracts, file.path(processed_dir, "tract_disability.gpkg"), delete_dsn = TRUE, quiet = TRUE)

block_list <- lapply(unname(unlist(cfg$counties)), function(county) {
  stem <- paste0("tl_2020_48", county, "_tabblock20")
  zip_path <- file.path(raw_dir, paste0(stem, ".zip"))
  download_atomic(sprintf("https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/%s.zip", stem), zip_path)
  directory <- file.path(raw_dir, stem); if (!dir.exists(directory)) unzip(zip_path, exdir = directory)
  x <- st_read(list.files(directory, "\\.shp$", full.names = TRUE)[1], quiet = TRUE)
  needed <- c("GEOID20", "geometry")
  if (!all(needed %in% names(x))) stop("Unexpected 2020 block schema for county ", county)
  select(x, all_of(needed)) |> mutate(bg_geoid = substr(GEOID20, 1, 12), tract_geoid = substr(GEOID20, 1, 11))
})
blocks <- bind_rows(block_list)
pl_zip <- file.path(raw_dir, "tx2020.pl.zip")
download_atomic("https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/Texas/tx2020.pl.zip", pl_zip)
pl_dir <- file.path(raw_dir, "tx2020_pl"); if (!dir.exists(pl_dir)) unzip(pl_zip, exdir = pl_dir)
geo <- data.table::fread(file.path(pl_dir, "txgeo2020.pl"), sep = "|", select = c(3, 8, 9),
                         col.names = c("SUMLEV", "LOGRECNO", "GEOID"), colClasses = "character", showProgress = FALSE)
geo <- geo[SUMLEV == "750", .(LOGRECNO, GEOID20 = sub("^7500000US", "", GEOID))]
geo[, LOGRECNO := as.character(as.integer(LOGRECNO))]
segment <- data.table::fread(file.path(pl_dir, "tx000012020.pl"), sep = "|", select = c(5, 6),
                             col.names = c("LOGRECNO", "POP20"), showProgress = FALSE)
segment[, LOGRECNO := as.character(LOGRECNO)]
block_population <- merge(geo, segment, by = "LOGRECNO", all.x = TRUE)[, .(GEOID20, POP20)]
blocks <- blocks |> left_join(as.data.frame(block_population), by = "GEOID20")
if (any(is.na(blocks$POP20))) stop("2020 PL population did not match every TIGER block.")
h8 <- st_read(at_root(cfg$paths$h8_grid), quiet = TRUE) |> select(h3_id, region) |> st_transform(cfg$geography$equal_area_crs)
block_points <- blocks |> st_transform(cfg$geography$equal_area_crs) |> st_point_on_surface()
crosswalk <- st_join(block_points, h8, left = FALSE) |> st_drop_geometry() |>
  group_by(bg_geoid, tract_geoid, h3_id, region) |>
  summarise(block_population = sum(POP20, na.rm = TRUE), .groups = "drop") |>
  group_by(bg_geoid) |>
  mutate(pop_weight = if (sum(block_population) > 0) block_population / sum(block_population) else rep(1 / n(), n()),
         housing_weight = pop_weight) |>
  ungroup()
write_csv(crosswalk, file.path(processed_dir, "block_group_h8_crosswalk.csv"))

bg_fields <- names(groups)[vapply(groups, group_geography, character(1)) == "block_group"]
tract_fields <- names(groups)[vapply(groups, group_geography, character(1)) == "tract"]
allocated <- crosswalk |> left_join(st_drop_geometry(bg) |> select(GEOID, all_of(bg_fields)), by = c("bg_geoid" = "GEOID"))
for (id in bg_fields) {
  weight <- if (groups[[id]]$unit == "household") allocated$housing_weight else allocated$pop_weight
  allocated[[id]] <- allocated[[id]] * weight
}
tract_crosswalk <- crosswalk |> group_by(tract_geoid, h3_id, region) |>
  summarise(block_population = sum(block_population), .groups = "drop") |> group_by(tract_geoid) |>
  mutate(tract_pop_weight = if (sum(block_population) > 0) block_population / sum(block_population) else rep(1 / n(), n())) |> ungroup() |>
  left_join(st_drop_geometry(tracts) |> select(GEOID, all_of(tract_fields)), by = c("tract_geoid" = "GEOID"))
for (id in tract_fields) tract_crosswalk[[id]] <- tract_crosswalk[[id]] * tract_crosswalk$tract_pop_weight
h8_bg <- allocated |> group_by(h3_id, region) |> summarise(across(all_of(bg_fields), ~sum(.x, na.rm = TRUE)), .groups = "drop")
h8_tract <- tract_crosswalk |> group_by(h3_id, region) |> summarise(across(all_of(tract_fields), ~sum(.x, na.rm = TRUE)), .groups = "drop")
h8_counts <- full_join(h8_bg, h8_tract, by = c("h3_id", "region"))
estimate_fields <- names(groups)
h8_index <- st_drop_geometry(h8) |> distinct(h3_id, region)
h8_counts <- h8_index |> left_join(h8_counts, by = c("h3_id", "region"))
h8_counts[estimate_fields] <- lapply(h8_counts[estimate_fields], function(x) replace(x, is.na(x), 0))
write_csv(h8_counts, file.path(processed_dir, "h8_population_counts.csv"))

qa <- bind_rows(lapply(estimate_fields, function(id) {
  source <- if (group_geography(groups[[id]]) == "tract") tracts else bg
  data.frame(group_id = id, acs_total = sum(source[[id]], na.rm = TRUE), allocated_total = sum(h8_counts[[id]], na.rm = TRUE),
  retained_share = ifelse(sum(source[[id]], na.rm = TRUE) > 0, sum(h8_counts[[id]], na.rm = TRUE) / sum(source[[id]], na.rm = TRUE), NA_real_)
  )
}))
write_csv(qa, file.path(processed_dir, "demographic_allocation_qa.csv"))
message("Prepared ", nrow(bg), " block groups and ", nrow(h8_counts), " H3 cells.")

