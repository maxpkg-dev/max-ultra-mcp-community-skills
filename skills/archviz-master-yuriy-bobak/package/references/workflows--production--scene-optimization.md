# Scene Optimization — Production Workflow

## Diagnose first
Viewport slow? render slow? RAM high? file huge? network transfer slow? identify which.

## Geometry
Use instances/procedural systems/scatters/proxies where appropriate. Avoid unnecessary raw duplication. Simplify unseen detail.

## Vegetation
Use ForestPack/Chaos Scatter rather than converting dense scatters to geometry without reason. Optimize display and camera behavior.

## Repeated architecture
Use RailClone or native instancing for rule-based repeated systems.

## Proxies
Corona Proxy primarily helps scene/viewport/file management; do not claim it inherently accelerates final ray tracing.

## Textures
Audit resolution, missing maps, duplicated assets and unnecessary high-resolution sources.

## Displacement
Use only where visual payoff justifies memory/tessellation; coarsen while preserving required detail, use autobump where appropriate.

## Render elements
Remove unnecessary high-resolution LightMix/render elements when RAM is constrained.

## QA
Test representative final camera, not only viewport statistics.

## Linked dependencies
Read the references needed for the selected branch; procedural modules apply only when those systems are used in the scene.

- [ForestPack Camera Optimization](software--forestpack--camera-optimization.md)
- [ForestPack Art Direction](software--forestpack--art-direction.md)
- [RailClone Core](software--railclone--core.md)
- [Corona Proxies & Chaos Scatter](software--corona--proxies-scatter.md)
- [Corona Displacement](software--corona--displacement.md)
- [Corona LightMix](software--corona--lightmix.md)
- [GI / Sampling / Performance](software--corona--gi-performance.md)

## Recoverability before applying
Treat the recommendations above as candidates in a measured, scoped plan. Preserve original geometry, modifier stacks, procedural sources and required render elements. Do not collapse or delete originals to obtain a proxy: write and verify the proxy, compare transforms/bounds/materials, then move originals to a recoverable backup layer. Deletion is a separate authorized operation. Keep off-camera reflection, shadow and GI contributors, and check every required view or animation path before adopting culling or simplification. See [Max Ultra MCP Integration](max-ultra-integration.md).
