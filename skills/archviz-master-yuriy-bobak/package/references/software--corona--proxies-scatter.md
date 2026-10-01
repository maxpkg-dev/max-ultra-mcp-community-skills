# Corona Proxies & Chaos Scatter

## Corona Proxy
Proxies primarily improve scene/viewport manageability and scene-file weight; they do not inherently make the final render faster or higher quality. Geometry is stored externally and loaded for rendering.

## Chaos Scatter
Chaos Scatter supports dense scattering over surfaces/splines/volumes, presets, per-instance editing, paint/erase, slope/altitude limits, edge trimming, include/exclude areas, surface-color mapping, camera clipping and adaptive viewport preview.

## ForestPack relationship
ForestPack remains a powerful dedicated scattering/art-direction system. Choose based on project pipeline and required controls; do not convert a working procedural scatter to raw geometry merely for perceived render speed.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.

For conversion, use the [recoverable optimization workflow](workflows--production--scene-optimization.md#recoverability-before-applying); verify the proxy before moving originals to a backup layer, and never delete them as part of conversion.
