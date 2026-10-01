# ForestPack ↔ RailClone Integration

Requires ForestPack 9.4.1+ and RailClone 7.3.2+.

RailClone segments marked Export to Forest can become ForestPack placement points. In ForestPack use Reference distribution and enable Use RailClone Items.

ForestPack creates one item per exported segment and receives position, rotation, scale and wireframe color. Segment deformation is not transferred.

RailClone Tags can map segment types to Forest geometry by using fpgeom=<geometry name>.

Compatible ForestPack behavior includes Effects, animation, collision detection, camera clipping, distance falloff, Look At, color variation, Items Editor, LOD, altitude/slope, surface projection and map-driven transforms.

Use this when architectural procedural logic should drive efficiently instanced environmental/asset placement.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
