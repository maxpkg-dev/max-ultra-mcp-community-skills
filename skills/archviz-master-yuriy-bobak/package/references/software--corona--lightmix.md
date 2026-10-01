# Corona LightMix

LightMix allows intensity/color changes to lights and emissive sources during or after rendering.

## Setup
Automatic setup creates the LightMix/LightSelect render-element structure. Manual setup uses CShading_LightMix plus CShading_LightSelect elements.

## Workflow
Develop physically sensible lights first → use LightMix for balancing/look variants → when changes become extreme, bake them back to scene lights and re-render.

## Important limits
LightMix color filters the original source color rather than replacing it. Highly saturated original lights reduce later color flexibility.
Extreme LightMix intensity changes can create persistent noise/fireflies.
Large numbers of LightSelect elements at high resolution increase RAM use.

## High-resolution strategy
Tune LightMix at lower resolution → bake final choices to scene → disable unnecessary LightMix elements → final high-resolution render when memory matters.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
