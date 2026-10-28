# Population-specific accessibility

Start here to inspect demographic context and group outcomes before publishing them in the Austin explorer. Routing and destination inventories remain in their existing workflows; this folder adds origin-side population weights, not a new composite accessibility score.

## Run and review

From the DAM repository root, run `Rscript population-access/run_all.R`. Inputs and paths are in `config.yml`. Review `output/review.html`; the complete results are in `output/tables/group_access_summary.csv`. Both the five-county metro and Austin are included. Only morning-peak auto and transit-plus-walk scenarios are selected. Generated outputs are ignored by Git.

Run `Rscript population-access/scripts/export_web.R` to create compact public exports in `output/web/`. The website packaging script `site/austin-explorer/scripts/publish_population.py` copies those aggregates and review figures into the dashboard. Rebuild accessibility data with `python3 site/austin-explorer/scripts/export_dashboard_data.py` and validate with `python3 site/austin-explorer/scripts/validate_dashboard_data.py` before publishing.

## Sources and groups

The workflow uses ACS 2024 five-year estimates retrieved through Census Reporter, with the release explicitly checked. Most variables use block groups; disability uses tracts. The dictionary records Census table cells, denominators, units and source geography. Raw API responses remain cached locally. The public accessibility map uses modeled H3 allocations only to vary opacity and show where a selected group is concentrated; accessibility remains the cell color and does not change among residents of the same origin. Original Census geography remains available in the review outputs.

Groups include age, poverty, disability, vehicle availability, limited-English-speaking households and households with children. The four displayed racial/ethnic categories are Hispanic/Latino, non-Hispanic Black, non-Hispanic White and other non-Hispanic residents. The last category combines Asian, American Indian/Alaska Native, Native Hawaiian/Pacific Islander, other race and multiracial residents. Detailed counts remain in the source preparation. The optional people-of-color summary overlaps the four categories and is not an additional mutually exclusive category. These are descriptive groups, not assumptions about individual needs.

## Calculation and limitations

Group means are `sum(accessibility * group_count) / sum(group_count)`. Resident groups are compared with all residents; household groups with all households. Population weighting is separate from any future destination-importance weighting. Job outcomes here describe residents' exposure to job access, not a worker-weighted LEHD employment metric.

ACS counts are allocated to H3 resolution 8 using 2020 Census block population and representative block points. Weights are normalized within each source geography over matched H3 origins, preserving source totals. Household counts currently use population as a proxy for their within-area distribution. Conservation of totals does not validate the allocation. Census and H3 boundaries, population changes since 2020 and within-block locations introduce uncertainty. Austin summaries select H3 cells whose centers are inside its full-purpose boundary, rather than estimating an exact city population.

For required-destination travel times, unreachable origins are assigned the analysis ceiling (auto 60 minutes; transit 90 minutes) in capped means and percentiles. These values are censored summaries, not actual unreachable travel times. The reachable share and mean among reachable origins are also exported. For cumulative supply, zeros remain zeros and the reached share requires positive supply. No minimum service standard or composite equity index is imposed.

The public job selector retains 15- and 30-minute auto thresholds and 30- and 60-minute transit-plus-walk thresholds. The public parks selector retains acreage within 10, 15, and 30 minutes; park counts remain outside the published interface.

ACS count margins of error are retained and shown where available. There is no blanket reliability suppression; small-area estimates require caution. H3 allocation uncertainty is not included in ACS margins of error.

## Peak park update — 2026-10-28

Both modes now include eligible park counts and whole-park acreage within 10, 15 and 30 minutes. Auto uses Karner's prepared AM matrix; transit uses the existing pinned r5r/OSM/CapMetro network for July 13, 2026, 07:00–08:59, with the 50th-percentile travel time, 90-minute trip limit and 20-minute walk limit. The retained service-calendar warning remains in the run log; the snapshot does not represent all regional operators.

The existing park eligibility filters were retained. Polygon representative points are routing proxies, not verified entrances; whole-park acreage is counted once when its representative destination is reachable. One park lies outside the auto matrix grid and is excluded from that mode. Manifests and QA tables are next to each scenario's results in `case-studies/austin/outputs/working/park_reachable_supply/`.
