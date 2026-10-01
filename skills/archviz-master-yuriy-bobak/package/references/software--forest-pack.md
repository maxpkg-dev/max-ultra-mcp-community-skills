# ForestPack — Software Knowledge

## Role
ForestPack is the high-density scene-assembly/scattering layer for ArchViz: vegetation, grass, rocks, people, cars, lights and repeated assets.

## Core system
A Forest object combines:
- Geometry items;
- Distribution;
- Areas;
- Surfaces;
- Transform variation;
- Items Editor;
- Camera controls;
- Material controls;
- Effects;
- Animation/display/render controls.

## Distribution modes
Use the mode that matches the design problem:
- Image mode: area-based scattering/patterns.
- Path mode: regular placement along splines.
- Reference mode: placement from markers/references.
- PFlow mode: particle-driven placement.
- RailClone integration: RailClone-exported segments can become ForestPack placement points.

## Areas
Areas can be built from splines, objects, Forest objects, paint and surfaces and can include/exclude scattering. Use boundaries deliberately to preserve architectural circulation, roads, facade visibility and designed landscape zones.

## Natural variation
Variation can be introduced through transforms such as translation, rotation and scale. Randomness must be art-directed: avoid both visible repetition and uncontrolled noise.

## ArchViz rules
- Art-direct density to the brief; preserve designed uniform planting when it is intentional.
- Protect the architectural focal hierarchy.
- Use foreground vegetation selectively for framing/depth.
- Reduce texture/contrast complexity in distant planting.
- Vary species, scale, rotation and clustering according to plausible landscape logic.
- Keep circulation and important facade features readable.
- Check intersections, floating items, boundary leaks and obvious repeated assets.
- Optimize viewport/display/camera behavior for large scenes rather than converting scatters to raw geometry without reason.

## ForestPack + RailClone
ForestPack can use exported RailClone segments as placement points. This allows procedural architecture/layout from RailClone to drive efficient ForestPack instancing while retaining Forest effects, animation, collision, camera clipping, color variation, LOD and related scatter controls.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
