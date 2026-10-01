# Corona Renderer for 3ds Max — Software Knowledge

## Role
Corona is the rendering/material/lighting layer used to turn the 3ds Max scene into physically coherent ArchViz imagery.

## Skill domains
Maintain knowledge for:
- render setup and performance;
- interactive rendering;
- Corona Camera/exposure;
- Sun/Sky and environment workflows;
- artificial lights;
- LightMix;
- Corona Physical Material;
- reflection / roughness / IOR / Fresnel behavior;
- bump and displacement;
- proxies/scattered geometry interoperability;
- volumetrics/atmosphere when visually justified;
- tone mapping and VFB workflow;
- denoising;
- animation/flicker-aware workflows;
- render elements and compositing;
- troubleshooting.

## Artistic mapping
Camera problem → solve camera/framing before tone mapping.
Flat lighting → inspect source direction/size/environment before increasing contrast.
Weak material → inspect scale, roughness/reflection/IOR and illumination before adding imperfections.
Weak depth → solve spatial cues first; atmosphere/DOF are supporting tools.
Distracting background → control light/value/color/detail before relying on blur.
Overprocessed image → preserve believable value relationships and material response.

## Documentation rule
Corona-specific numeric settings and UI paths are version-sensitive. Use current Chaos Corona for 3ds Max documentation for exact controls rather than deriving them from the art books.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
