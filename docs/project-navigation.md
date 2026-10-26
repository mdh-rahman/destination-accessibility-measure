# Repository navigation

DAM separates reusable code from place-specific implementation.

| Path | Responsibility |
| --- | --- |
| `R/` | Shared calculations, configuration validation, and matrix readers |
| `workflows/01_networks/` | Network acquisition and preparation |
| `workflows/03_accessibility/` | Common accessibility runner and summaries |
| `case-studies/<place>/` | Local configurations, POI preparation, data contract, outputs, and clearly labeled exploratory work |
| `gis/arcgis/` | ArcGIS delivery design and exporters |
| `docs/guide/` | Methods and replication documentation |
| `site/` | Public guide and example applications |
| `tests/` | Shared behavior and configuration tests |

The missing `02_travel_times/` number is intentional. A future workflow will provide a common interface across R5, prepared matrices, and additional routing engines.
