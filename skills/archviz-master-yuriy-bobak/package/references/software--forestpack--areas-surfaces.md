# ForestPack Areas & Surfaces

Area types include Splines, Objects, Forests, Paint and Surfaces. Areas can be combined and processed as include/exclude regions according to supported area behavior.

## ArchViz uses
- exclude buildings, roads, paths, pools and entrances;
- include planting beds and landscape zones;
- project scatters onto terrain/surfaces;
- paint art-directed local density;
- use other Forest objects to create exclusions/relationships.

## Boundary control
For Corona workflows, official docs recommend Edge boundary checking plus Forest Edge map in material opacity/cutout to prevent visible scatter leakage at borders; Material Optimiser can automate setup.

## Rules
Avoid overlapping include areas where they create coplanar issues. Check curbs, paths, facade bases and camera-near boundaries carefully.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
