# Austin case study

This folder implements DAM for the Austin-Round Rock-Georgetown five-county region: Bastrop, Caldwell, Hays, Travis, and Williamson counties.

## Routing and measurement split

The case study deliberately separates travel-time estimation from accessibility measurement.

- **Automobile:** time-of-day H8 travel-time matrices prepared by the Austin Opportunity Index project team in ArcGIS are ingested as the current authoritative automobile input.
- **Transit plus walk:** `r5r` builds travel-time matrices from a pinned CapMetro GTFS feed and OpenStreetMap network. The routing includes walking access and egress, waiting, transfers, and in-vehicle time.
- **Accessibility measurement:** the R `accessibility` package applies the same declared measures to either mode-specific matrix. It calculates the indicators; it does not perform routing.

This separation lets a routing source change without changing the definition of a destination accessibility measure.

## Folder map

- `config/accessibility.yml` declares origins, inventories, modes, periods, and measures.
- `config/network.R` pins the GTFS, OpenStreetMap, LODES, routing, and boundary settings used for transit plus walk and employment preparation.
- `destinations/` prepares and documents opportunity inventories.
- `workflows/jobs/preparation/` prepares LODES employment opportunities used by the shared runner.
- `exploratory/r5r-jobs/` preserves superseded standalone r5r job experiments and is not an authoritative workflow.
- `data/` is local and ignored; see `DATA.md`.
- `outputs/` is generated and ignored.
- Public results are presented under `site/austin-explorer/`.

Austin is an example implementation. Shared functions and runners remain at the repository root so another region can add a case-study configuration without copying the analytical engine.
