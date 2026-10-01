# Interior Animation — Production Workflow

## Load
Interior Still + Corona animation/network/denoising/displacement + procedural systems used by the scene.

## Pipeline
1. Define route, pacing and architectural story.
2. Check camera collision, height, speed, lens changes and doorway transitions.
3. Establish stable daylight/artificial lighting.
4. Preflight moving lights/objects separately from camera-only motion.
5. Test glossy materials, glass, mirrors, LED/light materials and dark indirect areas for temporal noise.
6. Use animation-safe GI workflow appropriate to scene motion.
7. Avoid temporally unstable denoising as a substitute for convergence.
8. Test displacement and procedural assets for flicker.
9. Render representative frames and a short contiguous test segment.
10. Farm frames across nodes.
11. QC full sequence for GI, noise, LightMix consistency, exposure, materials, geometry and post.

## Rule
A five-frame test is not enough for a long interior path; include a contiguous motion test.

## Linked dependencies
Read the references needed for the selected branch; procedural modules apply only when those systems are used in the scene.

- [Interior Still — Production Workflow](workflows--production--interior-still.md)
- [Render Farm — Production Workflow](workflows--production--render-farm.md)
- [Corona Animation](software--corona--animation.md)
- [Corona Network / Distributed Rendering](software--corona--network-rendering.md)
- [Corona Denoising](software--corona--denoising.md)
- [Corona Displacement](software--corona--displacement.md)
- [ForestPack Camera Optimization](software--forestpack--camera-optimization.md)
- [ForestPack Art Direction](software--forestpack--art-direction.md)
- [RailClone Core](software--railclone--core.md)
