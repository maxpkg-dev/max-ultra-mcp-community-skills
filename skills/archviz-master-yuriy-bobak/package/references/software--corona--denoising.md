# Corona Denoising

## Types
Corona Denoiser: production, CPU, high-quality post-render denoising.
NVIDIA GPU AI: very fast preview/interactive-capable denoising.
Intel CPU/GPU AI: hybrid speed/quality option; GPU mode can support interactive workflows.

## Rules
Denoising reduces required convergence but cannot rescue an extremely noisy base image.
Inspect texture/detail loss and artifacts.
Denoising uses additional memory.

## Animation warning
Current Corona denoisers do not provide temporal consistency. They can introduce flicker/splotches in animation. Prefer sufficiently converged frames and animation-safe post workflows rather than relying on per-frame AI denoising.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
