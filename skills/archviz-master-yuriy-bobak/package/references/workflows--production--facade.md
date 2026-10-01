# Facade — Production Workflow

## Load
composition, perspective-camera, materials-reflections; 3ds Max core; RailClone core/L1S/A2S/operators-macros; Corona materials.

## Tool choice
Unique sculptural facade → native modeling.
Repeated linear trim/cornice/rail → RailClone L1S.
Panel/curtain-wall/cladding grid → RailClone A2S.
Reusable studio facade logic → RailClone Macro.

## Pipeline
1. Read module/grid logic.
2. Create clean base splines/dimensions.
3. Build minimal reusable segment kit.
4. Assign default/edge/corner/special modules.
5. Expose parameters that architects are likely to revise.
6. Add conditional/random variation only when construction/design permits.
7. Validate corners, openings, end conditions and UV/material IDs.
8. Evaluate facade at hero camera and distance.
9. Light/material test before micro-detail.

## Linked dependencies
Read the references needed for the selected branch; procedural modules apply only when those systems are used in the scene.

- [Composition](knowledge--composition.md)
- [Perspective & Camera](knowledge--perspective-camera.md)
- [Materials & Reflections](knowledge--materials-reflections.md)
- [3ds Max 2027 Core](software--3dsmax--2027-core.md)
- [RailClone Core](software--railclone--core.md)
- [RailClone L1S](software--railclone--l1s.md)
- [RailClone A2S](software--railclone--a2s.md)
- [RailClone Operators & Macros](software--railclone--operators-macros.md)
- [Corona Physical Material](software--corona--materials.md)


## Book-grounded visual checks
Use [Illustrated Case Studies](book-case-studies.md) to evaluate projected clusters, repeated scale cues, material response and detail hierarchy. These are production interpretations; preserve design intent and verify software controls separately.
