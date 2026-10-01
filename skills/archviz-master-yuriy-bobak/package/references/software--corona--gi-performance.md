# GI / Sampling / Performance

## General
Start with defaults. Change performance controls only after identifying the actual bottleneck/noise source.

## GI
Path Tracing is the unbiased primary GI solution. UHD Cache is a secondary cached GI solution particularly useful where indirect illumination dominates, such as interiors.

## Noise diagnosis
Direct-light noise → investigate light sampling/source setup before arbitrary global changes.
Indirect/GI or glossy noise → GI/AA balance may be relevant.
Strong DOF/motion blur → AA demand changes; do not use one universal GI/AA value.
Bright refractive spots/fireflies → diagnose refraction/light/material setup and sampling before simply increasing render time.

## Render limits
Choose Time, Pass or Noise limit according to production predictability. For farms/animation, fixed time or controlled quality targets can be easier to budget, but test representative frames.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
