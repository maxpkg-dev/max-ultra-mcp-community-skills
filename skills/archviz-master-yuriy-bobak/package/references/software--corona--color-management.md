# Corona + 3ds Max Color Management

For 3ds Max 2024+ Chaos generally advises that default color-management/gamma settings do not need manual changes.

## Gamma workflow
When using legacy Gamma Workflow, Display Gamma 2.2 is the documented requirement.

## OCIO
Use OCIO when the production pipeline is standardized around OCIO; 3ds Max and Corona handle the color-management settings through that workflow.

## Skill rule
Never recommend changing gamma casually to fix an image. Diagnose lighting, exposure, tone mapping, texture color space and pipeline configuration separately.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
