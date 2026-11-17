args <- commandArgs(trailingOnly=TRUE)
root <- normalizePath(args[1]); out <- normalizePath(args[2]); setwd(root)
suppressPackageStartupMessages(library(sf))
cfg <- yaml::read_yaml('case-studies/austin/config/accessibility.yml')
counts <- list()
for (name in names(cfg$inventories)) {
 spec <- cfg$inventories[[name]]
 if (identical(spec$format, 'h8_csv')) {
   file.copy(spec$path,file.path(out,'destinations','jobs_h3_r8.csv'))
   next
 }
 x <- st_read(spec$path,layer=spec$layer,quiet=TRUE); before <- nrow(x)
 for (field in names(spec$filters)) {
   rule <- spec$filters[[field]]; keep <- rep(TRUE,nrow(x))
   if (!is.null(rule$include)) keep <- keep & x[[field]] %in% rule$include
   if (!is.null(rule$exclude)) keep <- keep & !(x[[field]] %in% rule$exclude)
   if (isTRUE(rule$not_missing)) keep <- keep & !is.na(x[[field]])
   if (!is.null(rule$greater_than)) keep <- keep & !is.na(x[[field]]) & x[[field]] > rule$greater_than
   x <- x[which(keep),]
 }
 x <- x[!st_is_empty(x),]
 stopifnot(!anyNA(x[[spec$id]]),!anyDuplicated(x[[spec$id]]))
 st_write(x,file.path(out,'destinations','destinations.gpkg'),layer=name,quiet=TRUE)
 write.csv(st_drop_geometry(x),file.path(out,'destinations',paste0(name,'.csv')),row.names=FALSE,na='')
 counts[[name]] <- list(source_path=spec$path,source_layer=spec$layer,source_records=before,eligible_records=nrow(x),id=spec$id,source=spec$source,filters=spec$filters)
}
jsonlite::write_json(counts,file.path(out,'destinations','inventory_manifest.json'),pretty=TRUE,auto_unbox=TRUE,null='null')
