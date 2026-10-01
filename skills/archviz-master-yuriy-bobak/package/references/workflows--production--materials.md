# Materials — Production Workflow

## Load
materials-reflections, color-value, light; Corona materials, displacement, color-management.

## Build order
Identity → base value/color → physical model → IOR/reflection → roughness → transmission/refraction → texture scale → bump/normal → displacement → imperfections.

## Decision tree
Needs silhouette/parallax? yes → displacement candidate.
Only micro-surface response? → bump/normal.
Reflective material looks flat? → inspect environment/light/view angle before random roughness changes.
Glass weak? → geometry + IOR/reflection/roughness + interior/environment content + camera angle.
Material looks fake? → check scale before adding dirt.

## QA
Real-world scale, UVs, repetition, roughness variation, Fresnel, edge behavior, displacement memory, color-space correctness.

## Linked dependencies
Read the references needed for the selected branch; procedural modules apply only when those systems are used in the scene.

- [Materials & Reflections](knowledge--materials-reflections.md)
- [Color & Value](knowledge--color-value.md)
- [Light](knowledge--light.md)
- [Corona Physical Material](software--corona--materials.md)
- [Corona Displacement](software--corona--displacement.md)
- [Corona + 3ds Max Color Management](software--corona--color-management.md)


## Book-grounded visual checks
Use [Illustrated Case Studies](book-case-studies.md) to evaluate projected clusters, repeated scale cues, material response and detail hierarchy. These are production interpretations; preserve design intent and verify software controls separately.

## Shared materials and maps
Before editing, inspect assignments and graph sharing across matched and unmatched objects. Clone materials and affected shared map branches for matched objects by default when the change could affect unmatched nodes. Preserve original maps/assignments for recovery and verify both target and unaffected assignments afterward. Use [Max Ultra MCP Integration](max-ultra-integration.md) for runtime property checks and serial execution; a natural-language request becomes an explicit edit plan, never executable prose.
