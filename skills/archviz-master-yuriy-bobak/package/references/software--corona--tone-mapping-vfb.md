# VFB / Tone Mapping / Post

Corona VFB supports real-time post-processing during and after rendering. Corona 8+ uses stackable tone-mapping operators applied in order.

## Discipline
Use tone mapping to finish a coherent render, not repair unresolved lighting/material/composition.
Preserve highlight hierarchy and believable material response.
Use white balance as chromatic adaptation rather than a substitute for correct source colors.

## Bloom & Glare
Bloom/Glare can be adjusted during/after rendering and can optionally compute after render to save render resources. In Corona it is independent from DOF aperture-blade behavior, so art-direct it deliberately.

## CIE
Corona Image Editor can load CXR and perform VFB-like post, LightMix and denoising without opening 3ds Max.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
