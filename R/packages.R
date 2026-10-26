# Shared dependency loader. Package installation remains an explicit user step.
if (dir.exists(".R-library")) .libPaths(c(normalizePath(".R-library"), .libPaths()))

setup_project_packages <- function(packages, load_packages = TRUE) {
  packages <- unique(packages)
  missing <- setdiff(packages, rownames(utils::installed.packages()))
  if (length(missing)) {
    stop("Missing R packages: ", paste(missing, collapse = ", "),
         ". Install them before running this workflow.")
  }
  if (load_packages) {
    for (package in packages) {
      suppressPackageStartupMessages(
        library(package, character.only = TRUE, warn.conflicts = FALSE)
      )
    }
  }
  invisible(packages)
}
