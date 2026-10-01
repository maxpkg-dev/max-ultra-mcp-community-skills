# Corona Troubleshooting Decision Tree

## Noise
Locate it first: direct light / GI / glossy / refraction / DOF / motion blur / volume / caustics. Fix source before increasing global render cost.

## Fireflies
Inspect extreme light/material values, refractive paths, LightMix extremes and convergence. Denoising/firefly filtering is secondary to correcting pathological setup.

## Flicker
Check UHD Cache animation mode, denoising, screen-size displacement, caustics, VDB sequence naming, procedural/scatter randomness and moving light/object consistency.

## Memory
Audit high-resolution LightMix/render elements, denoising buffers, displacement density, huge textures, raw high-poly duplicates and scatter display/geometry strategy.

## Slow viewport
Use proxies/scatters/instances and display optimizations. Corona proxies help viewport/scene management but do not inherently accelerate ray tracing.

## Different farm result
Check exact software/plugin versions, assets, color management, system-wide Corona settings, paths and procedural dependencies.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
