# RailClone — Software Knowledge

## Role
RailClone is a parametric modeling and spline-cloning system for repeated architectural and environmental systems.

## Mental model
RailClone builds objects from:
- Segments: reusable geometry building blocks.
- Generators: construction rules.
- Base objects: splines/surfaces/parameters.
- Operators: transformations, conditions, randomization, sequencing, composition and related logic.
- Styles: the complete procedural graph/rule system.

## Generators
### L1S
One-dimensional array for linear structures along a path/spline. Strong ArchViz uses:
- curbs;
- fences;
- railings;
- roads/edges;
- cornices;
- linear facade elements;
- repeated lights;
- street furniture sequences.

### A2S
Two-dimensional array controlled numerically and/or by splines. Strong ArchViz uses:
- facades;
- curtain walls;
- panels;
- cladding;
- floors/ceilings;
- tile systems;
- modular walls;
- repeated architectural grids.

## Segments
Segments are reusable source building blocks. Think modularly: default, start/end, corners, evenly spaced/special modules and variants where appropriate.

## Operators
Use operators to build rules instead of manual edits: transform, mirror, sequence, randomize, conditional selection, compose, arithmetic/parameter logic, UVW changes and related procedural operations.

## ArchViz decision rule
Use RailClone when a system is repeated, rule-based, likely to change, follows a spline/surface, or would be expensive to update manually. Avoid unnecessary procedural complexity for a unique object that is faster and clearer to model directly.

## Art-direction rule
Procedural does not mean visually uniform. Introduce controlled variation only where the real architectural system allows it. Preserve design intent and construction logic.

## ForestPack integration
RailClone segments can be exported to ForestPack and used as placement points, allowing procedural layout to drive high-density instancing.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
