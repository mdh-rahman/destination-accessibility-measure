# Methods and design principles

DAM treats accessibility as a relationship among origins, opportunities, travel conditions, and a stated measure. A result is incomplete unless all four are documented.

## Separate routing from measurement

Routing creates or supplies an origin-destination travel-time matrix. Accessibility measurement combines that matrix with opportunity data to answer a stated question. DAM keeps these stages separate so different modes can use appropriate routing inputs while sharing consistent measure definitions.

For the Austin case study:

- Automobile travel times come from time-of-day H8 matrices prepared by the Austin Opportunity Index project team in ArcGIS.
- Transit plus walk travel times are generated with `r5r` from documented GTFS and OpenStreetMap snapshots.
- The R `accessibility` package is the common calculator for jobs and all destination measures.

The earlier standalone r5r job scripts are preserved under `case-studies/austin/exploratory/r5r-jobs/`. They are exploratory provenance, not the current automobile method.

## Routing realism

- Transit routing includes walking access and egress, waiting, transfers, and in-vehicle time.
- Automobile analysis ingests modeled time-of-day matrices.
- Routing parameters and source dates are stored with every run.
- Unreachable origins remain explicit rather than silently disappearing.

## Opportunity quality

A large POI list is not automatically a valid destination layer. Each inventory needs an eligibility definition, source hierarchy, duplicate policy, geographic screen, coordinate QA, and a record of manual decisions.

## Measures

Names describe the calculation directly. Examples include "jobs reachable within 45 minutes," "travel time to the third-nearest grocery," and "park acreage reachable within 30 minutes." The appropriate measure depends on how the destination functions and should be reviewed with subject-matter experts.

## Packages used

| Package or tool | Role |
| --- | --- |
| `accessibility` | Common calculator for cumulative opportunities, kth-nearest time, gravity, and supply-sensitive measures |
| `r5r` | Transit plus walk travel-time matrix generation for the Austin case study |
| GTFS | Scheduled routes, stops, trips, and service calendars used by r5r |
| OpenStreetMap | Walk and street network used by r5r |
| ArcGIS matrices | Current Austin automobile travel-time input |
| `sf` and `h3jsr` | Spatial processing and H3 conversion |
| `dplyr` and `readr` | Tabular transformation and input-output |
| `yaml` and `jsonlite` | Scenario configuration and run manifests |

## Relation to TrACKIT

TrACKIT provides a clear ordered ArcGIS workflow for networks, POIs, origin-destination matrices, accessibility metrics, reports, and spatial outputs. DAM adopts the clarity of that sequence while focusing on baseline and comparative accessibility rather than infrastructure scenario testing. DAM also emphasizes schedule-based transit, time-specific automobile inputs, curated administrative POIs, coverage QA, standardized manifests, and portable case-study configuration.
