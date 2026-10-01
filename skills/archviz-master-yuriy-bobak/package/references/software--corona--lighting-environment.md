# Corona Lighting & Environment

## Exterior choices
Corona Sun + Corona Sky: physically coherent daylight system where sky responds to sun position.
HDRI: image-based lighting for complex real-world light/reflection character.

## HDRI setup
HDRI can be assigned through the native 3ds Max Environment or Corona Scene Environment Single Map. CoronaBitmap supports environment mapping modes. The two main assignment routes do not inherently differ in quality/performance.

## Overrides
Corona supports environment override workflows, including reflection/refraction use cases and per-camera environment overrides.

## Native Max lights
Native Standard/Photometric lights can work with Corona when configured correctly, but Chaos recommends Corona Lights for more physically coherent/efficient Corona workflows.

## Light material
Corona Light Material turns arbitrary geometry into an emitter and is useful for custom-shaped luminous objects such as bulbs and LED strips. It can also be configured as visible/self-illuminated content without emitting scene light when emission is disabled.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
