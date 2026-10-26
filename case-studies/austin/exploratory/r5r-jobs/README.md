# Exploratory r5r job analysis

These scripts preserve the Austin case study's earlier standalone job-accessibility experiments. They generated travel times and job measures together with `r5r` and are retained only for methodological comparison and provenance.

They are not part of the authoritative Austin workflow. Current analyses separate the two tasks:

1. Automobile travel times are ingested from the project team's ArcGIS-generated H8 matrices.
2. Transit plus walk travel times are generated with `r5r`, GTFS, and OpenStreetMap.
3. The R `accessibility` package calculates job and destination accessibility from either matrix through `workflows/03_accessibility/run_accessibility.R`.

Do not publish outputs from these scripts as current DAM results.
