# Materials & Reflections
Material readability combines base value/color, reflection, roughness, view angle, lighting, texture scale, bump/displacement and appropriate imperfections.

## Fresnel
Reflection changes with viewing angle; grazing angles generally show stronger reflection.

## ArchViz
Do not judge a shader only by maps. Inspect light and reflection context. Large facade planes need enough light/reflection variation to communicate orientation. Use roughness variation only when the intended material and scale justify it; uniform finishes may be correct. Correct texture scale before adding imperfections.

## Questions
What material is intended? Is value plausible? Does reflection describe the surface? Is roughness credible? Is texture scale architectural? Are bump/displacement frequencies appropriate? Is there useful environment content to reflect?


## Expanded book-grounded diagnosis

Source keys L, C and P and page-number conventions are defined in the [evidence register](book-evidence-register.md). ArchViz applications are production interpretations, not software instructions from the books.

### Reflections make off-camera context important

L 149-150 shows how the environment determines reflected appearance; L 158 illustrates how a specular response can become more conspicuous against a darker diffuse component.

**ArchViz application:** test the reflected environment before increasing reflectivity or changing IOR. A black surface showing a strong highlight does not by itself prove that its physical reflectance is unusually high. Keep reflection-relevant surroundings when optimizing a scene.

### Diagnose materials through light, scale and structure

L 193-196 connects visible texture with illumination, surface structure and directional highlights. L 202-204 extends this to material-specific observations.

**ArchViz application:** test a surface under broad and grazing illumination before strengthening bump or displacement. Establish large form, medium relief and microstructure separately. Directional scratches should affect highlight behavior coherently; wood grain, weave and weathering should follow construction and use.

**Diagnostic:** does the material fail because its geometry, texture scale, reflection response or illumination is wrong? Avoid a single "add roughness variation" answer.

### Transmission depends on more than surface color

L 161-162 and 173-174 connects transmitted color with the path through the material; L 177-180 distinguishes different light-penetration appearances.

**ArchViz application:** check thickness and transmission separately from reflection for glass and translucent materials. Do not use a painted color overlay as a general substitute for optical behavior.

For illustrated comparisons, use [book case studies](book-case-studies.md). For conditional troubleshooting, use the [artistic diagnostic workflow](artistic-diagnostic-workflow.md).
