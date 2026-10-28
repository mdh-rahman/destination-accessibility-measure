#!/usr/bin/env Rscript
# Export only public aggregate demographics and peak group outcomes.
suppressPackageStartupMessages({library(sf);library(readr);library(dplyr);library(jsonlite);library(yaml)})
script <- sub('--file=', '', commandArgs()[grep('--file=', commandArgs())])
root <- normalizePath(file.path(dirname(script), '../..'))
cfg <- read_yaml(file.path(root,'population-access/config.yml'))
p <- file.path(root,cfg$paths$processed)
out <- file.path(root,cfg$paths$output,'web');dir.create(out,recursive=TRUE,showWarnings=FALSE)
d <- read_csv(file.path(p,'population_group_dictionary.csv'),show_col_types=FALSE) |> filter(display)
for (geo in c('block_group','tract')) {
 x <- st_read(file.path(p,if(geo=='tract') 'tract_disability.gpkg' else 'block_group_demographics.gpkg'),quiet=TRUE)
 keep <- d |> filter(source_geography==geo, !group_id %in% c('total_population','children_household_universe'))
 cols <- unique(c('GEOID',keep$group_id,keep$denominator,paste0(keep$group_id,'_moe')))
 x <- x[, intersect(cols,names(x))]
 x <- st_transform(x,5070) |> st_simplify(dTolerance=30,preserveTopology=TRUE) |> st_transform(4326)
 st_write(x,file.path(out,paste0(geo,'.geojson')),delete_dsn=TRUE,quiet=TRUE,layer_options='COORDINATE_PRECISION=5')
}
s <- read_csv(file.path(root,cfg$paths$output,'tables/group_access_summary.csv'),show_col_types=FALSE)
write_json(list(groups=d,outcomes=s,acs_year=cfg$acs_year),file.path(out,'population.json'),dataframe='rows',auto_unbox=TRUE,na='null',digits=5)
file.copy(file.path(root,cfg$paths$output,'tables/group_access_summary.csv'),out,overwrite=TRUE)
