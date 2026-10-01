# Corona ArchViz Decision Tree

## Image is flat
First inspect camera/composition/value hierarchy. Then inspect key-light direction, sky/environment balance, facade plane separation and reflections. Do not start with contrast sliders.

## Image is noisy
Identify noise type/location first: glossy/refraction, dark indirect regions, DOF/motion blur, displacement/detail, volumetrics, lights. Then choose sampling/render-time/denoising changes. Avoid universal magic settings.

## Glass is weak
Check geometry/normals, material type, IOR/reflection/roughness, environment/interior content and camera angle.

## Exterior lacks depth
Use geometry overlap, scale, value/color/detail falloff first; add atmospheric/volumetric effects only when physically/art-directorially justified.

## Interior windows dominate
Balance exposure/light hierarchy rather than simply crushing highlights. Preserve plausible exterior/interior relationship.

## Animation
Prioritize temporal consistency, stable assets/materials/lighting, deterministic procedural systems and tested camera paths. Treat denoising/flicker and distributed rendering as production decisions, not still-image defaults.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
