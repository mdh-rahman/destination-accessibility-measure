# Destination Accessibility Measure (DAM)

**Realistic multimodal accessibility from networks to opportunities**

Destination Accessibility Measure (DAM) is an open-source workflow for measuring how people reach jobs and essential destinations by different travel modes and at different times of day. It emphasizes realistic routing inputs, carefully reviewed points of interest, transparent accessibility measures, and reproducible GIS-ready outputs.

**Current version:** `2026.10.26`
**Guide:** https://mdh-rahman.github.io/destination-accessibility-measure/
**Austin example explorer:** https://mdh-rahman.github.io/destination-accessibility-measure/austin-explorer/

DAM is not a transportation-project scenario editor. It establishes a defensible baseline of accessibility conditions and supports comparison across modes, times, destinations, places, and population groups. Future releases can add walking, bicycling, paratransit, and additional routing backends without changing the output contract.

## Austin routing and measurement

The Austin case study separates travel-time estimation from accessibility measurement:

- Automobile analyses ingest time-of-day H8 matrices prepared by the Austin Opportunity Index project team in ArcGIS.
- Transit plus walk matrices are generated with `r5r`, a pinned CapMetro GTFS feed, and OpenStreetMap.
- The R `accessibility` package calculates the declared job and destination measures from either matrix.

Earlier standalone r5r job-measure scripts are retained under `case-studies/austin/exploratory/r5r-jobs/` as provenance and are not part of the authoritative Austin workflow.

## Workflow

1. Prepare origins and geographic boundaries.
2. Build or ingest mode-specific travel networks and travel-time matrices.
3. Assemble, screen, geocode, and document opportunity inventories.
4. Declare measures, modes, departure periods, and thresholds in a case-study configuration.
5. Run the shared accessibility engine.
6. Validate spatial coverage, unreachable origins, source provenance, and result distributions.
7. Export tables, spatial layers, manifests, and web or ArcGIS delivery packages.

## Repository map

| Path | Purpose |
| --- | --- |
| `R/` | Reusable measure, scenario, and travel-matrix functions |
| `workflows/01_networks/` | Network and schedule preparation |
| `workflows/03_accessibility/` | Shared scenario runner and result summaries |
| `case-studies/austin/` | Austin configuration, POI processing, and example outputs |
| `gis/arcgis/` | GIS delivery contract and ArcGIS packaging roadmap |
| `docs/guide/` | Methods and replication documentation |
| `site/` | Public guide and Austin example explorer |
| `tests/` | Configuration and measure validation |

The numbering leaves room for a future `02_travel_times/` workflow that can support additional routing engines and modes.

## Run the Austin example

Large and restricted inputs remain local. Follow `case-studies/austin/DATA.md`, then run:

```sh
Rscript workflows/03_accessibility/run_accessibility.R \
  --config case-studies/austin/config/accessibility.yml \
  --scenario grocery_third_nearest \
  --mode drive \
  --period am_peak
```

Outputs follow one contract:

```text
case-studies/austin/outputs/working/
└── <scenario>/<mode>/<period>/
    ├── accessibility.csv
    ├── qa_summary.csv
    └── run_manifest.json
```

## Versioning

DAM uses calendar versions in `YYYY.MM.DD` form. A release records the code and documentation available on that date. Every analytical run also records its own timestamp, configuration, source metadata, and routing parameters in a manifest.

## Relationship to the Austin Opportunity Index

Austin is the first case study and was developed within the Austin Opportunity Index research collaboration. DAM is maintained independently so the workflow can mature before selected outputs or interfaces are proposed to the team repository.

## License

MIT. See `LICENSE` and `NOTICE.md`.

## Population-specific outcomes

See [population-access](population-access/README.md) for the Austin demographic review workflow, group-weighted peak outcomes, and website export steps. The public explorer includes peak park counts and acreage, demographic maps, and downloadable group summaries.
