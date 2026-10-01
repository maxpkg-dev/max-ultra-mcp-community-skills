# Interior Still — Production Workflow

## Load
composition, perspective-camera, depth, light, color-value, materials-reflections, narrative, visual-hierarchy; 3ds Max 2027; Corona materials, lighting/environment, LightMix, VFB/tone mapping.

## Pipeline
1. Define room experience and hero zone.
2. Select camera height/distance and lens character; avoid using extreme width simply to show everything.
3. Establish furniture/architecture scale and clean spatial layers.
4. Design daylight/artificial relationship.
5. Build value hierarchy; control window dominance.
6. Establish hero materials before props.
7. Use Corona Physical Material logic and physically coherent reflections/roughness.
8. Add styling selectively; avoid equal detail density everywhere.
9. Use LightMix for balancing/variants, then bake extreme final changes back to scene when appropriate.
10. IR lookdev → production render → denoise → VFB/post.
11. QA reflections, glazing, texture scale, clipping, repeated props, bright fixtures, noise and fireflies.

## Interior depth
Prefer overlap, value/light separation and material contrast before shallow DOF.

## Linked dependencies
Read the references needed for the selected branch; procedural modules apply only when those systems are used in the scene.

- [Materials & Reflections](knowledge--materials-reflections.md)
- [Narrative & Art Direction](knowledge--narrative.md)
- [Color & Value](knowledge--color-value.md)
- [Depth](knowledge--depth.md)
- [Composition](knowledge--composition.md)
- [Perspective & Camera](knowledge--perspective-camera.md)
- [Visual Hierarchy](knowledge--visual-hierarchy.md)
- [Light](knowledge--light.md)
- [3ds Max 2027 Core](software--3dsmax--2027-core.md)
- [Corona Physical Material](software--corona--materials.md)
- [Corona Lighting & Environment](software--corona--lighting-environment.md)
- [Corona LightMix](software--corona--lightmix.md)
- [VFB / Tone Mapping / Post](software--corona--tone-mapping-vfb.md)


## Artistic diagnosis and mood
For mood alternatives use [Mood Design](mood-design.md). For uncertain visual causes use the [Artistic Diagnostic Workflow](artistic-diagnostic-workflow.md), then the [Artistic Review Checklist](artistic-review-checklist.md). These extend the artistic layer without establishing new version-specific software settings.
