# Corona Animation

## Core rule
Animation requires temporal consistency, not merely clean individual frames.

## UHD Cache
For camera fly-throughs without moving lights/objects, Chaos documents the Animation (flicker-free) workflow and permits reuse/precomputation of cache data.
For moving lights/objects, calculating animation-safe cache data per frame is the safest documented approach; slower movement may allow incremental cache strategies.

## Denoising
Do not assume still-image denoising is animation-safe; Corona denoisers lack temporal consistency.

## Displacement
Screen-size displacement can retessellate differently by camera/frame and may flicker. World-size displacement can improve temporal stability at increased memory cost. Keep displacement size as coarse as visual requirements allow and use autobump where appropriate.

## Network rendering
For sequences, prefer a render manager where machines render different frames. Corona native DR is primarily designed for multiple machines contributing to one image.

## Preflight
Test representative frames for GI, displacement, procedural assets, vegetation, moving lights, motion blur, DOF, denoising artifacts and texture/asset availability before launching the sequence.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
