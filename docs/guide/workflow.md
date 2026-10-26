# End-to-end workflow

## 1 Define the analysis frame

Choose a study boundary, origin geography, coordinate system, modes, departure periods, and the population represented by each origin. Preserve all origins, including those with no reachable opportunity.

## 2 Prepare opportunity inventories

Prefer authoritative program or licensing data when available. Retain raw snapshots, standardize fields, geocode missing coordinates, identify duplicates, screen eligibility, record manual decisions, and create one reviewed spatial layer per opportunity type.

## 3 Prepare or ingest travel times

Use mode-appropriate inputs and document them independently from the accessibility measure.

- **Austin automobile:** ingest the project team's ArcGIS-generated time-of-day H8 matrices.
- **Austin transit plus walk:** use `r5r` with the pinned GTFS and OpenStreetMap snapshots. Record the service date, departure window, percentile, walk limit, and maximum trip duration.

GTFS and OpenStreetMap are required to reproduce the r5r transit matrix. They are not required merely to calculate accessibility from an already prepared matrix.

## 4 Declare the analysis

A case-study YAML file identifies the origin grid, inventories, modes, periods, and measures. Common measures include reachable opportunities within a threshold, travel time to the kth-nearest opportunity, gravity-weighted access, and supply-sensitive access.

## 5 Calculate accessibility

The shared runner passes the selected travel matrix and opportunity table to the R `accessibility` package. It produces the same output schema across modes and destinations. Large matrices can be processed in origin batches without creating another full copy.

## 6 Validate

Check origin and destination coverage, excluded destinations, duplicate identifiers, missing coordinates, transit service-calendar validity, travel-time distributions, implausible values, and the share of origins marked unreachable.

## 7 Deliver

Publish a tidy table, spatial layer, QA summary, and run manifest. Web maps and ArcGIS packages are presentation layers derived from these validated outputs.
