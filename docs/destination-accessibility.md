# Accessibility analysis contract

Every DAM result identifies its origin geography, opportunity inventory, mode, departure period, measure, routing constraints, and source dates.

The shared runner consumes a case-study YAML file and writes:

- `accessibility.csv`: one standardized value per origin and measure parameter;
- `qa_summary.csv`: coverage, reachability, exclusions, and distribution checks;
- `run_manifest.json`: configuration, input, routing, and execution provenance.

Austin currently demonstrates reachable opportunities and kth-nearest travel time for automobile and walking plus transit. Additional measures and modes should enter through the shared configuration and output contract rather than separate destination-specific analysis scripts.
