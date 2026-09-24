args <- commandArgs(trailingOnly = TRUE)
input <- args[[1]]
output <- args[[2]]
data_dir <- args[[3]]
figure_prefix <- args[[4]]
dir.create(dirname(output), recursive = TRUE, showWarnings = FALSE)
dir.create(dirname(figure_prefix), recursive = TRUE, showWarnings = FALSE)
knitr::opts_knit$set(root.dir = normalizePath(data_dir))
knitr::opts_chunk$set(echo = TRUE, fig.path = figure_prefix)
knitr::knit(input, output = output, quiet = FALSE, envir = new.env(parent = globalenv()))
