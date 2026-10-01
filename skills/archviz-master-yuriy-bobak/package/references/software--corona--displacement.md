# Corona Displacement

Displacement changes actual rendered surface geometry and should be reserved for detail that needs silhouette/parallax/depth rather than details better handled by bump/normal.

## Animation
Screen-size displacement may change tessellation with camera position and can flicker. World-size displacement keeps tessellation spatially consistent but can use more memory.

## Optimization
Use the largest displacement size that still resolves required detail. Autobump can preserve fine appearance while allowing coarser displacement tessellation.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
