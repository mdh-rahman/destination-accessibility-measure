AUSTIN ACCESSIBILITY - TEAM DATA SNAPSHOT - 2026-11-03

START HERE
This dated snapshot supports additional statistics without rebuilding destinations
or rerunning routing. It contains the exact values exported for the DAM dashboard
at the source commit recorded in manifest.json. No new routing was performed.

CONTENTS (four data folders)
 destinations/ : eligible inventories in destinations.gpkg (one layer per type),
                full nongeometry attributes in CSV, and 2023 LODES jobs by H3.
 accessibility/: accessibility_results.csv is the main analysis table;
                measure_dictionary.csv explains each measure; group_comparisons.csv
                and dashboard_equity_summaries.json contain existing comparisons.
 demographics/ : h3_population_counts.csv reproduces the dashboard's 12 groups plus
                All residents and denominators. ACS2024 block-group/tract files
                are broader supporting demographic extracts; use the H3 table
                for matching dashboard outcomes. Dictionaries and crosswalk included.
 geography/    : H3 origins, Austin full-purpose boundary, counties, metro and
                block-group polygons. Retain H3 IDs as text.

HOW TO USE FROM EITHER REPOSITORY
Sync or download this whole dated folder from the team's SharePoint library.
Set the environment variable DAM_DATA_DIR to its local path; do not commit that
personal path or account credentials. Alternatively pass --data-dir explicitly.
Run from any directory with Python 3 (standard library only):
 python analyze_shared_data.py --data-dir "/your/local/snapshot" --verify
 python analyze_shared_data.py --data-dir "/your/local/snapshot" --region metro --mode walk_transit --group no_vehicle_households --threshold 30
The example validates every packaged file and calculates population-weighted
nearest-grocery coverage/median. It prints results without modifying the package.
Join accessibility_results.csv to demographics using h3_id, then to h8-grid.geojson.
Filter scenario, mode and measure_id before aggregating to avoid duplicate origins.
Austin is a subset of metro: filter in_austin=True. Do not append city rows to metro.

MEASUREMENT AND UNITS
Rows are H3 origin x scenario x mode x period x measure. Values retain their native
units (minutes, jobs, acres, or types). IDs such as facility_count__3 on a time
measure mean time to the third facility, not a count of three reachable facilities.
Use measure_dictionary.csv for labels/units; never infer units solely from an ID.
Empty value is not zero. result_status distinguishes modeled values, incomplete
baskets and no destination reached within the modeled routing constraints.
No modeled route does not establish that no real-world journey is possible.
Retain unreached origins in population denominators. Do not substitute 90 minutes
as their observed time or drop them silently. Medians can be beyond the model limit;
means excluding them must explicitly be labeled reachable-only means.
Household, family and person counts must be summarized separately. Groups overlap
and cannot be summed. ACS counts allocated to H3 are estimates, not direct H3 surveys.
The single-parent denominator is families with children; it differs from all families.

INVENTORY STATUS
Destinations were exported from the configured cleaned source layers and filtered
using accessibility.yml. inventory_manifest.json records the original layer,
source and retained counts. Extra NPPES review/pharmacy layers are not included.
Park eligibility and childcare OD eligibility filters are applied. Full source
snapshots remain outside this package; the GeoPackage is the eligible working set.
Dashboard destination display layers can differ from the scenario-eligible set.
Specifically, the displayed urgent-care layer has 64 features while the NPPES
analysis inventory has 73 records. These are not interchangeable inventories.
Childcare displays 1,281 operations but analysis retains 1,280 OD-eligible operations.
Park inventory contains 1,339 eligible polygons; the auto manifest reports one
additional matrix-edge exclusion. Use run manifests for mode-specific exclusions.
The supplied results are unchanged; these discrepancies require source review,
not silent alteration of results during this handoff.
The hospital/urgent-care source remains CMS NPPES; source verification is not final.
Licensed childcare capacity is not vacancies. Nearest does not imply eligibility,
affordability, opening hours, insurance acceptance or service quality.

ROUTING LIMITATIONS AND REPRODUCTION
Current auto input: project-provided ArcGIS matrices. Transit+walk: r5r/OSM/GTFS.
The configured AM period uses 2026-07-13 07:00 and a 120-minute window; consult
packaged run manifests for individual runs. The existing GTFS calendar/coverage
concern has not been corrected by this export. Treat transit outcomes as provisional.
The current modeled limits are 60 minutes auto and 90 minutes transit+walk.
A dated snapshot does not imply these are November service conditions.
Travel-time matrices, network caches, raw downloads and exploratory runs are omitted.
Use the DAM scripts and original inputs to reroute or reproduce cleaning from scratch.
This package supports downstream analysis, not a fully self-contained routing rebuild.

SHARING AND VERSIONING
For the existing UT/City project team. Some inventories include licensed-source
contributions and home-based childcare locations. This package is NOT cleared for
public redistribution. A separate public release should undergo source/field review.
Do not place the whole package in either public GitHub repository.
Record this dated folder and manifest's source commit in new analyses. Keep this
snapshot unchanged; put new statistics elsewhere and create a new dated snapshot
when source data or results change. manifest.json lists sizes and SHA-256 hashes.
Cloud sync and collaborator permissions are controlled by the existing shared library.
Source: https://github.com/mdh-rahman/destination-accessibility-measure
