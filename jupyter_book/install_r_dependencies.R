local_library <- file.path(getwd(), ".Rlib")
dir.create(local_library, recursive = TRUE, showWarnings = FALSE)
install.packages(
  c("ggplot2", "dplyr", "tidyr", "readr", "tibble", "stringr", "forcats", "purrr", "gridExtra", "cowplot"),
  lib = local_library,
  repos = "https://cloud.r-project.org",
  Ncpus = 2
)
