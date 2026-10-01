# Corona Physical Material

Corona Physical Material is the default starting point for physically based Corona shading and follows energy-conservation constraints.

## Build order
1 material identity / preset class;
2 base color/value;
3 metal/non-metal or relevant physical model;
4 reflection / IOR;
5 roughness;
6 refraction/transmission where applicable;
7 texture maps;
8 bump/normal;
9 displacement only when silhouette/parallax warrants it;
10 controlled imperfections.

## PBR maps
Use only maps that materially contribute. Typical inputs can include base color, roughness, metalness/specular workflow, opacity, normal/bump, height/displacement and emission.

## Glass example principle
Clear glass is based on low roughness, refraction enabled and physically plausible IOR; exact artistic requirements and geometry thickness still matter.

## Cosmos
Corona 15 removes the legacy toolbar Material Library; current ready-made materials are accessed through Chaos Cosmos.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.

For live material changes, apply the [shared-material and shared-map protection](workflows--production--materials.md#shared-materials-and-maps).
