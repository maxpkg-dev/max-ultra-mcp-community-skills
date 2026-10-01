# Max Ultra MCP Integration

Read before executing any scene operation. For critique of a supplied image or an advisory brief, work from that evidence without connecting to or changing Max.

## Scoped precedence

The user's intent, explicit constraints and higher-priority instructions govern. Within that scope, ArchViz Master's applicable artistic reasoning takes priority over generic artistic defaults: diagnosis, framing, mood, light/value hierarchy, material readability, context, and the order of production refinement. Built-in Max Ultra skills supply execution and verification mechanics. Never interpret this division as permission to ignore a whole skill or system rule.

| Potential conflict | Resolution |
|---|---|
| Built-in single-object centered framing versus an architectural hero composition | When this skill applies, choose framing from the brief, hierarchy, viewer role and negative space. Intentional asymmetry or crop is allowed when the deliverable permits it. Preserve a user's complete-object/centered requirement; never use artistic priority to hide missing required geometry. |
| Built-in full-object acceptance screenshot versus an intentional architectural crop | Judge the intended final crop inside Safe Frame. If complete geometry must also be proved, capture a separate overview or query its bounds; do not mislabel the cropped beauty view as complete-object evidence. |
| Generic dramatic depth, strong contrast or random variation versus quiet mood or designed repetition | Use the relevant artistic diagnosis and mood module. Preserve intentional symmetry, repetition, low contrast and material identity when they support the brief. |
| Artistic camera advice versus locked same-frame alternatives | Preserve the agreed camera, projection, lens and crop. Propose camera alternatives separately; do not silently change comparison invariants. |
| A production route recommends Corona, ForestPack or RailClone but the scene uses another setup | Preserve the chosen renderer and working systems. Plugin references are conditional implementation candidates, not authority to install, switch or convert them. |
| An artistic effect suggests fog, DOF, clipping, animation or new assets | Recommend it only when justified by the brief. Apply only within the authorized task and available capabilities; do not treat artistic priority as permission for extra effects. |
| A book heuristic conflicts with physical behavior or installed software | Use the book for visual intent and the verified physical/runtime model for implementation. Do not invent numeric recipes or APIs. |

## Discover and route

For Max work, use the available `max-ultra-mcp` skill. Discover instances with `max_list_instances` and select the only or uniquely identified target with `max_select_instance`. If several targets remain ambiguous, resolve that ambiguity before operations; if none is connected, explain how to connect. Read scene information and `max_capabilities`; acquire current NodeRefs and scene revisions. Never reuse historical handles or select by an assumed global default.

Load a specialized skill by its available client name or discover it through `max_skills_list` and `max_skill_read`, retaining the returned revision. These names are discovery hints, not filesystem dependencies or proof of installed tools:

- `max-ultra-camera-composition`: camera transforms, render aspect, Safe Frame, camera basis, and visual evidence; apply the scoped artistic choices above.
- `max-ultra-renderer-settings`: active renderer/class/property introspection, exact setting semantics, before/after readback and unsupported results.
- `max-ultra-floor-plan`: dimensioned shell/openings/floor with validation tokens and preserved source geometry.
- `max-ultra-small-house-detailing`: editable roofs, facades, joinery, finishes and fitted architectural assemblies.
- `max-ultra-spline-modeling`: editable paths and profiles. Use the focused armchair or character/object modeling skill only for the corresponding reference-driven reconstruction.

If a skill or tool is absent, use the live catalog to select a verified alternative and preserve the safeguards below. If execution cannot be established, deliver an explicit plan or limitation. Never invoke a tool solely because it appears in documentation or a backlog.

## Execution and evidence that artistic priority never overrides

1. Prefer available semantic tools, then registered operations, then bounded reviewed MaxScript; use unrestricted `max_execute` only when no narrower tool fits. Never turn raw prose into executable code. Do not guess plugin classes, property names, enum values or UI selectors.
2. Serialize mutations through Max Ultra's selected-instance main-thread queue. Do not run scene, viewport, renderer, SDK or UI calls on background threads. Respect validation tokens, NodeRefs, stale-state errors and existing approval boundaries. Preserve system units and convert dimensional inputs.
3. For live camera judgments, record output size/aspect, activate the actual camera and deterministically enable Safe Frame. Keep it enabled in comparisons. Compare the rendered area rather than the viewport rectangle. Capture and inspect tool-returned images with the appropriate clean preset; use explicit camera transforms, not perspective orbit commands in a camera view. An already supplied render can be critiqued directly without changing viewport state.
4. Query the active renderer and its runtime properties before renderer-specific edits. Use official documentation matching the installed build to interpret values. Read back applied changes and report applied, unchanged, unsupported and warnings accurately. Property discovery alone does not establish writability or correct semantics.
5. Before material edits, find shared materials and shared map branches. Clone for matched objects by default if an edit would affect unmatched nodes. Preserve original maps and assignments for recovery; a shallow material copy may still share maps. Verify affected and unaffected assignments after the edit.
6. For optimization/proxies, preserve source geometry, modifier stacks, procedural graphs and assets. Verify proxy output, transforms, bounds, materials and dependencies before placing originals on a recoverable backup layer. Do not delete originals as part of conversion. Simplification, collapsing stacks, deleting nodes or removing required render elements needs an explicit scoped plan and authorization.
7. Render or run other long operations only within the request, using available cancellable job tools. Never claim arbitrary synchronous MaxScript is safely cancellable; bound it and stop on failure. Do not automatically replay a timed-out mutation. Inspect post-state first.
8. UI fallback may affect only HWNDs belonging to the selected `3dsmax.exe` PID, with ownership revalidated immediately before mutation. Coordinate clicks or transport success alone are not semantic proof.
9. Saving, replacing scenes, exporting, copying assets, farm submission, software installation and uploads remain governed by the user's scope. Separate scan roots from write destinations, resolve filename collisions, verify copies before repathing, and retain a manifest for asset/export/proxy work. Do not replace an unsaved scene for a batch job; use a dedicated worker where applicable.
10. Verify changed properties and visual results. A viewport proves framing/geometry evidence, not final Corona shading. Report only actual queries, edits, renders and checks. Restore temporary diagnostic substitutions unless intentionally adopted.

## Compatibility

The artistic layer can guide supported Max Ultra environments across 3ds Max 2022-2027, but this package's software notes target the 2027 family and selected plugins. This is not real-version validation. On an older build, keep the artistic goal and find a verified implementation; do not claim a 2027 feature exists there. See [compatibility and validation](compatibility-and-validation.md).
