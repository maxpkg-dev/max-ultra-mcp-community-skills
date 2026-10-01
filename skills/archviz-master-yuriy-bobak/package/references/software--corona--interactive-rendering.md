# Corona Interactive Rendering

IR updates automatically as scene objects, materials, environment, lights and cameras change.

## Use
Use IR for look development, materials, lighting, camera and scene adjustments. Do not treat IR as the final-render mode.

## Performance
IR internally uses responsiveness-oriented settings and by default leaves one CPU thread available for other work. Thread override is under System Settings.

## Denoising
Interactive denoising can use supported NVIDIA/Intel GPU AI options. Use it as preview assistance; always inspect the underlying render quality.

## Workflow
Camera/composition → IR → broad light/value → materials → detail → final production render.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
