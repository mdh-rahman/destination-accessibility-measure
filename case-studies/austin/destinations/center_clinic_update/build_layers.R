library(sf); library(dplyr); library(jsonlite)
args<-commandArgs(TRUE); root<-if(length(args)) args[1] else getwd(); out<-if(file.exists(file.path(root,'source/additions.json'))) root else file.path(root,'handoff/2026-11-17')
x<-st_read(file.path(out,'source/original_centers.gpkg'),layer='regional_centers',quiet=TRUE)
base<-x |> transmute(facility_id,facility_name,address,city,state,zip,county,facility_type,source_url,source_checked,programs,access_notes,review_notes,review_status,longitude,latitude,coordinate_source,h3_h8)
a<-fromJSON(file.path(out,'source/additions.json'))
a<-st_as_sf(a,coords=c('longitude','latitude'),crs=4326,remove=FALSE)
counties<-st_read(file.path(out,'source/county-boundaries.geojson'),quiet=TRUE) |> st_transform(4326)
a$county<-sub(" County$","",counties$name)[vapply(st_within(a,counties),function(z){stopifnot(length(z)==1);z},integer(1))]
a$h3_h8<-h3jsr::point_to_cell(a,res=8,simple=TRUE)
new<-a |> transmute(facility_id,facility_name,address,city,state='TX',zip,county,facility_type,source_url,source_checked='2026-11-17',programs=notes,access_notes='Service-specific eligibility / appointment requirements apply; see source',review_notes=notes,review_status=if_else(facility_id=='ch_northeast','temporary_service_changes','source_listed_user_included'),longitude,latitude,coordinate_source=paste0('ArcGIS address geocode; ',geocode_type,'; score ',geocode_score,'; entrance unverified'),h3_h8)
# Align geometry column names before row binding.
names(new)[names(new)==attr(new,'sf_column')]<-'geom'; st_geometry(new)<-'geom'
community<-bind_rows(base |> filter(facility_type %in% c('recreation_community_center','social_service_center')),new[a$community,])
senior<-base |> filter(facility_type %in% c('senior_center','senior_community_center'))
u<-st_read(file.path(out,'source/original_urgent_care.gpkg'),layer='urgent_care',quiet=TRUE) |> st_transform(4326)
u<-u |> transmute(facility_id=destination_id,facility_name=canonical_name,address,city,state,zip,county,facility_type='urgent_care',source_url=evidence_url,source_checked=NA_character_,programs='Urgent care; source-reviewed inventory',access_notes='Provider-specific eligibility and hours',review_notes=review_reason,review_status=review_decision,longitude,latitude,coordinate_source, h3_h8)
# Two Next Level records describe the same Wells Branch site at 14900 I-35.
dup<-grepl('Next Level',u$facility_name,ignore.case=TRUE)&grepl('^14900',u$address)
stopifnot(sum(dup)==2)
removed<-u[which(dup)[2],]; u<-u[-which(dup)[2],]
clinic<-bind_rows(u,new[a$clinic,])
sets<-list(community_social_recreation=community,senior_centers=senior,urgent_care_clinics=clinic)
for(n in names(sets)) {
 z<-sets[[n]]; stopifnot(!anyDuplicated(z$facility_id),all(st_is_valid(z)),!anyNA(z$h3_h8),!anyNA(z$county))
 st_write(z,file.path(out,paste0(n,'.gpkg')),layer=n,delete_dsn=TRUE,quiet=TRUE)
 write.csv(st_drop_geometry(z),file.path(out,paste0(n,'.csv')),row.names=FALSE,na='')
}
changes<-bind_rows(data.frame(facility_id=x$facility_id[x$facility_type=='civic_rental_venue'],action='excluded',reason='Luling Civic Center: rental-only venue; user decision'),data.frame(facility_id=removed$facility_id,action='deduplicated',reason='Next Level Wells Branch: duplicate 14900 I-35 facility; retain other record'),data.frame(facility_id=a$facility_id,action='added',reason=a$notes))
write.csv(changes,file.path(out,'change_log.csv'),row.names=FALSE)
write_json(lapply(sets,function(z)list(records=nrow(z),types=as.list(table(z$facility_type)),h3_resolution=8,crs='EPSG:4326')),file.path(out,'validation.json'),pretty=TRUE,auto_unbox=TRUE)
print(lapply(sets,function(z)table(z$facility_type)))
