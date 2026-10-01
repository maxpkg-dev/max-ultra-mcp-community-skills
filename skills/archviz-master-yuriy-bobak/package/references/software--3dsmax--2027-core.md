# 3ds Max 2027 Core

Use 3ds Max 2027/2027.x documentation as the version authority.

## Current 2027 family features relevant to ArchViz
- Smart Bevel and subsequent enhancements: cleaner post-Boolean intersection bevel workflows.
- Extrude modifier custom direction: spline extrusion can use a gizmo/custom direction rather than only local Z.
- Spline Chamfer improvements.
- Noise Plus: modern procedural noise with fractal types, animation and tiling controls.
- Boolean improvements including recursive welding/cleanup.
- Field Helper for component-selection workflows.
- OCIO/color-management updates.
- USD workflow improvements.
- 2027.2: 3D Gaussian Splat support and Point objects/modifiers.
- 2027.2: Point Instance modifier for true render-time instancing from point datasets.

## ArchViz use
Model architecture non-destructively where revisions are expected. Prefer clean splines, modifier stacks, instances and procedural systems. Use Booleans/Smart Bevel for controlled hard-surface detail; use custom-direction Extrude for non-axis-aligned spline forms; use Noise Plus for controlled natural variation only where physically appropriate.

## Camera
Solve intent, eye level, camera-to-subject distance and perspective before focal-length fine tuning. Check vertical behavior and edge distortion.

## Color management
Treat color management as a pipeline concern. Do not mix display-space and scene-space assumptions casually. Keep render/VFB/post pipeline consistent.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
