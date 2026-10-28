#!/usr/bin/env Rscript

suppressPackageStartupMessages({library(dplyr); library(ggplot2); library(readr); library(sf); library(yaml)})
script <- sub("--file=", "", commandArgs()[grep("--file=", commandArgs())])
root <- normalizePath(file.path(dirname(script), "../.."), mustWork = TRUE)
cfg <- yaml::read_yaml(file.path(root, "population-access/config.yml")); at_root <- function(x) file.path(root, x)
processed <- at_root(cfg$paths$processed); output <- at_root(cfg$paths$output)
dir.create(file.path(output, "figures"), recursive = TRUE, showWarnings = FALSE)
summary <- read_csv(file.path(output, "tables", "group_access_summary.csv"), show_col_types = FALSE)
dictionary <- read_csv(file.path(processed, "population_group_dictionary.csv"), show_col_types = FALSE) |> filter(display)
qa <- read_csv(file.path(processed, "demographic_allocation_qa.csv"), show_col_types = FALSE)
bg <- st_read(file.path(processed, "block_group_demographics.gpkg"), quiet = TRUE)
tracts <- st_read(file.path(processed, "tract_disability.gpkg"), quiet = TRUE)

core <- c("below_poverty","no_vehicle_households","children_under_18","adults_65_plus","people_with_disability","limited_english_households")
denom <- setNames(dictionary$denominator, dictionary$group_id)
map_data <- bind_rows(lapply(core, function(g) {
  x <- if (g == "people_with_disability") tracts else bg
  x$share <- ifelse(x[[denom[[g]]]] > 0, x[[g]] / x[[denom[[g]]]], NA_real_); x$group_id <- g
  select(x, group_id, share)
})) |> left_join(select(dictionary, group_id, group_label = label), by = "group_id")
map <- ggplot(map_data) + geom_sf(aes(fill = share), color = NA) + facet_wrap(~group_label, ncol = 3) +
  scale_fill_viridis_c(labels = scales::percent, option = "C", na.value = "grey90") +
  coord_sf(datum = NA) + labs(title = "Five-county demographic context", fill = "Share") +
  theme_void(base_size = 10) + theme(plot.title = element_text(face = "bold", size = 16), strip.text = element_text(face = "bold"), legend.position = "bottom")
ggsave(file.path(output, "figures", "demographic_overview.png"), map, width = 12, height = 8, dpi = 160, bg = "white")

selected <- summary |> filter(region == "metro", !group_id %in% c("total_population", "children_household_universe", "people_of_color")) |>
  filter((measure == "kth_nearest_time") | (scenario == "jobs_cumulative" & opportunity_field == "total_jobs" & parameter_value == 45) | (scenario == "park_reachable_supply" & opportunity_field == "acreage" & parameter_value == 15)) |>
  mutate(relative_disadvantage = ifelse(measure == "kth_nearest_time", mean_ratio_to_reference,
                                        ifelse(mean_ratio_to_reference > 0, 1 / mean_ratio_to_reference, NA_real_)),
         mode_label = recode(mode, drive = "Auto", walk_transit = "Transit + walk"))
gap <- ggplot(selected, aes(relative_disadvantage, reorder(group_label, relative_disadvantage), color = mode_label)) +
  geom_vline(xintercept = 1, color = "grey45", linetype = 2) + geom_point(size = 2, alpha = .85) +
  facet_wrap(~destination, scales = "free_y") +
  scale_color_manual(values = c("Auto" = "#d95f02", "Transit + walk" = "#1b9e77")) +
  labs(title = "Population-specific access relative to the metro population", subtitle = "Values above 1 indicate comparatively worse access; peak period only", x = "Relative disadvantage", y = NULL, color = NULL) +
  theme_minimal(base_size = 10) + theme(plot.title = element_text(face = "bold", size = 15), legend.position = "bottom", panel.grid.minor = element_blank())
ggsave(file.path(output, "figures", "group_access_comparison.png"), gap, width = 13, height = 12, dpi = 160, bg = "white")

table_rows <- summary |> filter(region == "metro", group_id %in% c("total_population","below_poverty","no_vehicle_households","adults_65_plus","people_with_disability")) |>
  filter(measure == "kth_nearest_time") |>
  select(destination, mode, group_label, reachable_share, mean_access, p50_access, p90_access, mean_difference_from_reference) |>
  mutate(mode = recode(mode, drive = "Auto", walk_transit = "Transit + walk"),
         reachable_share = scales::percent(reachable_share, accuracy = .1), across(where(is.numeric), ~round(.x, 1)))

html_escape <- function(x) gsub("&", "&amp;", gsub("<", "&lt;", gsub(">", "&gt;", as.character(x), fixed = TRUE), fixed = TRUE), fixed = TRUE)
html_table <- function(x) {
  header <- paste0("<tr>", paste0("<th>", html_escape(names(x)), "</th>", collapse = ""), "</tr>")
  rows <- apply(x, 1, function(r) paste0("<tr>", paste0("<td>", html_escape(r), "</td>", collapse = ""), "</tr>"))
  paste0("<table><thead>", header, "</thead><tbody>", paste(rows, collapse = ""), "</tbody></table>")
}
qa_display <- qa |> filter(group_id %in% dictionary$group_id) |> left_join(select(dictionary, group_id, label), by = "group_id") |>
  transmute(Group = label, `ACS total` = round(acs_total), `Allocated total` = round(allocated_total), `Retained share` = scales::percent(retained_share, accuracy = .1))

html <- paste0('<!doctype html><html><head><meta charset="utf-8"><title>Population-specific accessibility review</title><style>',
  'body{font-family:Arial,sans-serif;color:#163047;max-width:1240px;margin:36px auto;padding:0 24px;line-height:1.5}h1,h2{color:#12344d}h1{font-size:34px} .note{background:#eef7f5;border-left:5px solid #178c82;padding:14px 18px}img{max-width:100%;border:1px solid #d9e1e6}table{border-collapse:collapse;width:100%;font-size:13px}th{background:#163b56;color:white;position:sticky;top:0}th,td{padding:7px;border:1px solid #d5dde2;text-align:right}th:first-child,td:first-child{text-align:left}.scroll{max-height:620px;overflow:auto}code{background:#edf1f3;padding:2px 5px}</style></head><body>',
  '<h1>Population-specific accessibility review</h1><p><strong>Scope:</strong> five-county Austin metro and City of Austin; AM peak auto and transit + walk only.</p>',
  '<div class="note"><strong>Interpretation.</strong> Accessibility is calculated once for each H3 origin. Demographic counts are origin-side weights used to describe who experiences those conditions. The analysis does not multiply local access by demographic concentration and does not create a single equity score. For travel-time measures, unreachable origins are assigned the documented mode-specific analysis limit in the capped summary; reachability is reported separately.</div>',
  '<h2>Demographic context</h2><p>ACS 2024 five-year block-group estimates. The maps show published block-group geography; H3 counts are modeled allocations used for summaries.</p><img src="figures/demographic_overview.png" alt="Demographic overview">',
  '<h2>Access comparisons</h2><p>Relative disadvantage compares each group with the metro population (or all households for household groups). Travel-time ratios above one mean longer capped travel time. For jobs and park acreage, the ratio is inverted so values above one consistently indicate worse access.</p><img src="figures/group_access_comparison.png" alt="Population access comparison">',
  '<h2>Peak-period destination results</h2><p>Minutes are capped at 60 for auto and 90 for transit + walk when the required destination is unreachable. Park counts and acreage now include peak results for both modes at 10, 15, and 30 minutes; see the downloadable summary table.</p><div class="scroll">', html_table(table_rows), '</div>',
  '<h2>Allocation QA</h2><p>Retained share compares the five-county ACS total with the amount allocated to H3 origins in the metro grid. Allocation weights are normalized within each source geography across matched H3 origins, preserving source totals; this does not establish within-cell accuracy.</p>', html_table(qa_display),
  '<h2>Files</h2><ul><li><code>tables/group_access_summary.csv</code></li><li><code>tables/peak_scenario_inventory.csv</code></li><li><code>spatial/block_group_demographics.gpkg</code></li><li><code>spatial/h8_population_counts.csv</code></li></ul>',
  '</body></html>')
writeLines(html, file.path(output, "review.html"), useBytes = TRUE)
dir.create(file.path(output, "spatial"), recursive = TRUE, showWarnings = FALSE)
file.copy(file.path(processed, "block_group_demographics.gpkg"), file.path(output, "spatial", "block_group_demographics.gpkg"), overwrite = TRUE)
file.copy(file.path(processed, "tract_disability.gpkg"), file.path(output, "spatial", "tract_disability.gpkg"), overwrite = TRUE)
file.copy(file.path(processed, "h8_population_counts.csv"), file.path(output, "spatial", "h8_population_counts.csv"), overwrite = TRUE)
file.copy(file.path(processed, "population_group_dictionary.csv"), file.path(output, "tables", "population_group_dictionary.csv"), overwrite = TRUE)
message("Wrote ", file.path(output, "review.html"))

