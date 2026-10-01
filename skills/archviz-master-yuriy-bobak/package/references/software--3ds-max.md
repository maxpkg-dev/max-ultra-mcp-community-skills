# 3ds Max — Software Knowledge

## Role in ArchViz
3ds Max is the scene-authoring and integration layer: modeling, modifiers, splines, cameras, materials, animation, rendering, scripting, asset assembly, and plugin hosting.

## Current workflow knowledge
### Modeling / scene construction
Use native geometry, splines, modifiers, instances/references, compound/procedural workflows and non-destructive stacks where they make revisions easier. Prefer procedural construction for repeated architectural systems.

### Camera / composition implementation
Translate the artistic camera diagnosis into:
- camera position and height;
- target/orientation;
- focal length / field of view;
- intentional tilt or corrected verticals;
- clipping where needed;
- camera-to-subject distance;
- framing/crop.

Always solve the visual intent first; do not choose focal length only to fit more content.

### Scripting / automation
MAXScript is 3ds Max's built-in scripting language and can automate modeling, animation, materials, rendering, UI tools, import/export and batch workflows. Python can interoperate with MAXScript and the 3ds Max runtime, making it useful for pipeline tools.

Potential ArchViz automation:
- scene cleanup and naming;
- batch texture checks/resizing;
- asset relinking;
- material audits;
- camera creation/validation;
- batch render setup;
- object/instance management;
- render-node preparation;
- repetitive modeling operations.

### 2027 awareness
Keep version-specific recommendations aligned with current Autodesk 3ds Max 2027 documentation. Newer features should not be inferred from the legacy 2012 help supplied by the user.

## Decision rule
When asked how to do something in 3ds Max:
1. diagnose the desired visual/production result;
2. choose native vs plugin/procedural method;
3. prefer non-destructive/reusable construction for recurring ArchViz tasks;
4. give exact UI/script steps only when supported by current documentation.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
