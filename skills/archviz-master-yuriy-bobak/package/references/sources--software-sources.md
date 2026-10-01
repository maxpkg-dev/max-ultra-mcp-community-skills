# Software Source Registry

## Autodesk
- User-supplied legacy 3ds Max 2012 Help URL.
- Current Autodesk 3ds Max 2027 Help should take precedence for version-specific behavior.
- Current MAXScript/Python documentation should be used for automation and pipeline questions.

## Chaos
- Official Corona for 3ds Max documentation: Chaos Documentation / CRMAX.
- Use for current Corona-specific UI, parameters, rendering, materials, lighting and troubleshooting.

## ITOOSOFT
- Official ForestPack documentation.
- Official RailClone documentation.
- Use for plugin-specific concepts, UI, distribution/generator systems, compatibility and integration.

## Source precedence
1. Current official documentation matching installed version.
2. Current official vendor documentation without exact version page.
3. User-supplied legacy documentation for historical/general concepts.
4. Model knowledge only when explicitly identified as such.

Do not overwrite the source-derived artistic core with software documentation; connect the two through implementation mappings.

For sampled direct vendor URLs and their exact verification limits, use [compatibility and validation](compatibility-and-validation.md). Runtime introspection establishes what the installed instance exposes; documentation establishes intended semantics. Both are required before version-sensitive edits.
