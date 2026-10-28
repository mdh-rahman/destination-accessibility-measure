#!/usr/bin/env Rscript

suppressPackageStartupMessages({library(dplyr); library(jsonlite); library(readr); library(tidyr); library(yaml)})
script <- sub("--file=", "", commandArgs()[grep("--file=", commandArgs())])
root <- normalizePath(file.path(dirname(script), "../.."), mustWork = TRUE)
cfg <- yaml::read_yaml(file.path(root, "population-access/config.yml"))
at_root <- function(path) file.path(root, path)
processed <- at_root(cfg$paths$processed); output <- at_root(cfg$paths$output)
dir.create(file.path(output, "tables"), recursive = TRUE, showWarnings = FALSE)

dictionary <- read_csv(file.path(processed, "population_group_dictionary.csv"), show_col_types = FALSE) |> filter(display)
demographics <- read_csv(file.path(processed, "h8_population_counts.csv"), show_col_types = FALSE)
groups <- dictionary$group_id

weighted_quantile <- function(x, w, p) {
  ok <- is.finite(x) & is.finite(w) & w > 0
  if (!any(ok)) return(NA_real_)
  x <- x[ok]; w <- w[ok]; o <- order(x); x <- x[o]; w <- w[o]
  x[which(cumsum(w) / sum(w) >= p)[1]]
}
weighted_mean <- function(x, w) {
  ok <- is.finite(x) & is.finite(w) & w > 0
  if (!any(ok)) NA_real_ else sum(x[ok] * w[ok]) / sum(w[ok])
}

scenario_root <- at_root(cfg$paths$scenario_root)
files <- list.files(scenario_root, pattern = "accessibility\\.csv$", recursive = TRUE, full.names = TRUE)
files <- files[grepl(paste0("/(", paste(cfg$analysis$modes, collapse = "|"), ")/", cfg$analysis$period, "/accessibility\\.csv$"), files)]
if (!length(files)) stop("No peak-period accessibility files found.")

summaries <- list(); index <- 1L
for (path in files) {
  access <- read_csv(path, show_col_types = FALSE)
  manifest <- fromJSON(file.path(dirname(path), "run_manifest.json"))
  access$maximum_trip_minutes <- manifest$maximum_trip_minutes
  access <- left_join(access, demographics, by = c("geography_id" = "h3_id"), relationship = "many-to-one")
  series <- access |> distinct(opportunity_field, parameter_name, parameter_value)
  for (k in seq_len(nrow(series))) {
    x <- access |> filter(opportunity_field == series$opportunity_field[k], parameter_name == series$parameter_name[k], parameter_value == series$parameter_value[k])
    for (region_name in cfg$analysis$regions) {
      z <- if (region_name == "metro") x else filter(x, region == region_name)
      for (group in groups) {
        w <- z[[group]]
        reachable <- !is.na(z$access_value) & z$is_reachable
        if (unique(z$measure) == "cumulative_opportunities") reachable <- reachable & z$access_value > 0
        is_time <- unique(z$measure) == "kth_nearest_time"
        value <- z$access_value
        if (is_time) value[!reachable] <- unique(z$maximum_trip_minutes)
        total_weight <- sum(w[is.finite(w) & w > 0], na.rm = TRUE)
        summaries[[index]] <- data.frame(
          region = region_name, group_id = group, scenario = unique(z$scenario), destination = unique(z$destination),
          mode = unique(z$mode), period = unique(z$period), measure = unique(z$measure),
          opportunity_field = series$opportunity_field[k], parameter_name = series$parameter_name[k],
          parameter_value = series$parameter_value[k], maximum_trip_minutes = unique(z$maximum_trip_minutes),
          population_or_households = total_weight,
          reachable_share = if (total_weight > 0) sum(w[reachable], na.rm = TRUE) / total_weight else NA_real_,
          mean_access = weighted_mean(value, w), mean_reachable_access = weighted_mean(z$access_value[reachable], w[reachable]),
          p10_access = weighted_quantile(value, w, .10), p50_access = weighted_quantile(value, w, .50),
          p90_access = weighted_quantile(value, w, .90), stringsAsFactors = FALSE)
        index <- index + 1L
      }
    }
  }
}
summary <- bind_rows(summaries) |> left_join(select(dictionary, group_id, group_label = label, unit), by = "group_id")
keys <- c("region","scenario","destination","mode","period","measure","opportunity_field","parameter_name","parameter_value")
reference <- summary |> filter(group_id %in% c(cfg$analysis$reference_group, "children_household_universe")) |>
  select(all_of(keys), unit, reference_mean = mean_access, reference_p50 = p50_access, reference_reachable_share = reachable_share)
summary <- summary |> left_join(reference, by = c(keys, "unit")) |>
  mutate(mean_difference_from_reference = mean_access - reference_mean,
         mean_ratio_to_reference = ifelse(reference_mean != 0, mean_access / reference_mean, NA_real_),
         reachable_share_difference = reachable_share - reference_reachable_share)
write_csv(summary, file.path(output, "tables", "group_access_summary.csv"))

inventory <- tibble(path = files) |> mutate(
  scenario = sub(paste0("^", scenario_root, "/([^/]+)/.*$"), "\\1", path),
  mode = sub("^.*/(drive|walk_transit)/am_peak/accessibility.csv$", "\\1", path), period = cfg$analysis$period)
write_csv(inventory, file.path(output, "tables", "peak_scenario_inventory.csv"))
message("Summarized ", length(files), " peak scenario-mode files into ", nrow(summary), " group rows.")

