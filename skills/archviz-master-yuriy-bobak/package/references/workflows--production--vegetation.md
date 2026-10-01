# Vegetation — Production Workflow

## Load
depth, composition, visual-hierarchy, narrative; ForestPack distribution, areas-surfaces, art-direction, camera-optimization; Corona proxies/scatter where relevant.

## Tool choice
Large art-directed ArchViz scatter → ForestPack candidate.
Native Chaos Scatter pipeline → Chaos Scatter candidate.
Manual hero plant → direct object/instance.
RailClone-driven positions → ForestPack Reference + RailClone Items.

## ForestPack decision
Area field → Image.
Street/tree line → Path.
Exact design positions → Reference.
Particle-driven → PFlow.

## Art direction
Design species mix, scale range, clusters, density, clear zones and depth hierarchy.
Foreground can frame but must not obscure architecture.
Background should generally carry lower texture/contrast frequency.
Use Areas to protect roads, paths, buildings, entrances and sightlines.
Use camera optimization carefully for huge scenes/animation.

## QA
Floating plants, intersections, repeated assets, impossible species/slope, border leaks, camera popping, shadow/reflection dependencies.

## Linked dependencies
Read the references needed for the selected branch; procedural modules apply only when those systems are used in the scene.

- [Depth](knowledge--depth.md)
- [Composition](knowledge--composition.md)
- [Visual Hierarchy](knowledge--visual-hierarchy.md)
- [Narrative & Art Direction](knowledge--narrative.md)
- [ForestPack Distribution](software--forestpack--distribution.md)
- [ForestPack Areas & Surfaces](software--forestpack--areas-surfaces.md)
- [ForestPack Art Direction](software--forestpack--art-direction.md)
- [ForestPack Camera Optimization](software--forestpack--camera-optimization.md)
- [ForestPack ↔ RailClone Integration](software--forestpack--railclone-integration.md)
- [Corona Proxies & Chaos Scatter](software--corona--proxies-scatter.md)
