# Production Troubleshooting Router

## Render looks wrong
Run Render Critique before technical debugging.

## Noise/fireflies
Load Corona troubleshooting + GI/performance + materials/lighting. Identify source class before changing global settings.

## Flicker
Load Corona animation + denoising + displacement + caustics; ForestPack camera/art direction; RailClone dependencies.

## Slow viewport
Load Scene Optimization + ForestPack display/camera + proxies + RailClone/native instancing.

## Slow render
Separate geometry/RAM, sampling/noise, displacement, volumetrics, caustics, lights, DOF/motion blur and render-element overhead.

## Missing farm content
Load Render Farm preflight.

## Vegetation issue
Load Vegetation + ForestPack modules.

## Repeated facade issue
Load Facade + RailClone modules.

## Camera feels wrong
Load Camera workflow before changing post or materials.

## Rule
Do not solve a visual-design problem with a technical optimization, and do not solve a technical bottleneck by degrading the image before identifying the bottleneck.

## Linked dependencies
Read the references needed for the selected branch; procedural modules apply only when those systems are used in the scene.

- [Render Critique](workflows--render-critique.md)
- [Corona Troubleshooting Decision Tree](software--corona--troubleshooting.md)
- [GI / Sampling / Performance](software--corona--gi-performance.md)
- [Corona Physical Material](software--corona--materials.md)
- [Corona Lighting & Environment](software--corona--lighting-environment.md)
- [Corona Animation](software--corona--animation.md)
- [Corona Denoising](software--corona--denoising.md)
- [Corona Displacement](software--corona--displacement.md)
- [Corona Caustics](software--corona--caustics.md)
- [Corona Proxies & Chaos Scatter](software--corona--proxies-scatter.md)
- [ForestPack Camera Optimization](software--forestpack--camera-optimization.md)
- [ForestPack Art Direction](software--forestpack--art-direction.md)
- [RailClone Core](software--railclone--core.md)
- [Scene Optimization — Production Workflow](workflows--production--scene-optimization.md)
- [Render Farm — Production Workflow](workflows--production--render-farm.md)
- [Vegetation — Production Workflow](workflows--production--vegetation.md)
- [Facade — Production Workflow](workflows--production--facade.md)
- [Camera — Production Workflow](workflows--production--camera.md)
