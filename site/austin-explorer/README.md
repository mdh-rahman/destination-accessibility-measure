# Accessibility dashboard

This folder is the static GitHub Pages build of the Austin Metro Accessibility
Explorer. Open `index.html` through a local web server for review; browsers
cannot load the data files correctly from a `file://` URL.

The dashboard reads compact files under `data/` that were exported from the
validated scenario results. To refresh it:

1. Run all required scenarios with `workflows/03_accessibility/run_accessibility.R`.
2. Run `site/austin-explorer/scripts/export_dashboard_data.py` from the repository root.
3. Validate the export with `validate_dashboard_data.py`.
4. Review the changed compact data files before committing them.

GitHub Actions publishes this directory through
`.github/workflows/dashboard-pages.yml`. The dashboard contains derived,
compact outputs; raw downloads and routing matrices stay outside Git.

## Essential-destination basket

The combined selector uses the nearest grocery, childcare, pharmacy, urgent care, hospital, park, library and public center, with equal category weights. An origin mean is calculated only if all eight have a modeled route; incomplete origins remain unavailable, not zero. Category counts within 15, 30 or 60 minutes retain zeros and range from 0 to 8. Click an origin to inspect all component times. Population-weighted area means are unavailable if any weighted origins have incomplete values; complete-data coverage is reported separately. Map median/range for basket travel time describe only complete origins.

Rebuild using `python site/austin-explorer/scripts/export_dashboard_data.py`; this also runs `workflows/03_accessibility/build_destination_basket.py`. The latter can be run independently to refresh only the combined measure. Its CSVs and input hashes are saved under `case-studies/austin/outputs/working/essential_destinations/<mode>/am_peak/`. The basket is a prototype equal-category summary, not a validated minimum-service standard or a multi-stop itinerary.

## Integrated equity view

The Map / Equity analysis tabs share destination, mode, study area and population selectors. The equity tab includes weighted box plots (10th–90th percentile whiskers), cumulative distributions, area-specific low-access shares and a low-access map. It uses the 12 reviewed groups plus All residents for map summaries. Selecting the equity tab from All residents highlights the poverty group initially; all 12 remain visible in comparison charts. The selected area determines the percentile benchmark, with identical Austin membership in the map and equity data.

After exporting dashboard measures, run `python population-access/scripts/build_equity_review.py --root .` and then `python site/austin-explorer/scripts/publish_population.py`. The latter only packages local assets; it does not deploy. It replaces legacy capped population summaries with reviewed, censored statistics and packages all downloadable comparison tables. The combined basket offers equity charts for reachable-type counts; its mean remains incomplete when any category cannot be reached. Mode-ratio equity distributions are not offered; select Auto or Transit + walk.

### Simplified explorer controls

The sidebar now presents Destination, Mode, Accessibility measure and Population group, followed by Study area. Definitions, statistics and review downloads are available through Chart rather than repeated in the map sidebar. Reference-layer switches are in the map's collapsed Layers menu. Population selection changes chart weighting and popup demographic information; it does not change map colors or opacity. The Map / Chart tabs retain the existing `view=equity` URL for compatibility.
