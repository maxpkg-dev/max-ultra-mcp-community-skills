# ForestPack Camera Optimization

ForestPack can limit items to the active camera visibility to reduce unnecessary scatter load.

## Workflow
Use visibility limiting for very large vegetation/environment scatters. Add expansion margin for animated cameras to prevent items popping at frame edges.

## ArchViz rule
Optimize after composition/camera is stable enough to avoid hiding required context. For animation, test the full camera path for popping and reflections/shadows that may need off-camera geometry.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
