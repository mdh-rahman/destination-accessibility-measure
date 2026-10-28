#!/usr/bin/env Rscript

script <- sub("--file=", "", commandArgs()[grep("--file=", commandArgs())])
root <- normalizePath(file.path(dirname(script), ".."), mustWork = TRUE)
steps <- file.path(root, "population-access/scripts", c("prepare_demographics.R", "summarize_group_access.R", "build_review.R"))
for (step in steps) {
  message("Running ", basename(step))
  status <- system2(file.path(R.home("bin"), "Rscript"), step)
  if (status != 0) stop("Population-access step failed: ", basename(step), call. = FALSE)
}

