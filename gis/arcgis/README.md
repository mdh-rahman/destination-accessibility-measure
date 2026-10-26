# ArcGIS delivery roadmap

DAM calculations remain independent of ArcGIS. ArcGIS is a delivery target for analysts and agencies that need editable maps, hosted layers, or a project package.

A future export command will create a dated delivery folder containing:

- one origin feature class with standardized accessibility fields;
- reviewed opportunity layers;
- study, county, municipal, and optional demographic boundaries;
- a field dictionary and source manifest;
- QA summaries and run metadata;
- layer files with consistent symbology;
- an ArcGIS Pro project and, when appropriate, a project package.

The package should be derived from validated DAM outputs. It should not contain licensed raw data, routing caches, or undocumented intermediate files. The current Austin export script is a bridge toward this contract and still needs conversion into a general configuration-driven exporter.
