# Exterior Animation — Production Workflow

## Load
Exterior Still + Corona animation, denoising, displacement, network-rendering; ForestPack camera optimization/art direction; RailClone procedural modules.

## Pipeline
1. Lock story beats and shot purpose.
2. Build stable procedural scene systems.
3. Design camera path and test at low quality.
4. Validate ForestPack camera clipping/expansion over the entire path.
5. Validate RailClone systems and animated/procedural dependencies.
6. Establish lighting and material consistency.
7. Test representative frames: start, middle, end, difficult lighting, close vegetation, reflective/refractive areas.
8. GI strategy: use documented animation-safe UHD Cache workflow when applicable.
9. Avoid relying on temporally inconsistent per-frame denoising.
10. Audit displacement; prefer animation-stable strategy when screen-size tessellation flickers.
11. Render-farm preflight.
12. Distribute separate frames across nodes via render manager.
13. Sequence QC for flicker, popping, texture changes, scatter changes, GI, caustics, exposure and color.
14. Composite/grade as a sequence, not independent stills.

## Rule
Temporal consistency outranks the quality of any single isolated frame.

## Linked dependencies
Read the references needed for the selected branch; procedural modules apply only when those systems are used in the scene.

- [Exterior Still — Production Workflow](workflows--production--exterior-still.md)
- [Render Farm — Production Workflow](workflows--production--render-farm.md)
- [Corona Animation](software--corona--animation.md)
- [Corona Denoising](software--corona--denoising.md)
- [Corona Displacement](software--corona--displacement.md)
- [Corona Network / Distributed Rendering](software--corona--network-rendering.md)
- [ForestPack Camera Optimization](software--forestpack--camera-optimization.md)
- [ForestPack Art Direction](software--forestpack--art-direction.md)
- [RailClone Core](software--railclone--core.md)
- [RailClone L1S](software--railclone--l1s.md)
- [RailClone A2S](software--railclone--a2s.md)
- [RailClone Operators & Macros](software--railclone--operators-macros.md)
