---
name: max-ultra-3d-floor-plan-from-drawing
description: Build an editable architectural shell in 3ds Max through Max Ultra MCP using the user's demonstrated workflow of compound wall splines, separate extruded storeys, spline-based slabs, and door openings with Edit Poly, Connect, Bridge or Extrude. Use for a bolvanka, wall shell, slabs, or door openings in this demonstrated style from an existing floor drawing. Excludes finished door leaves and frames, window assemblies, detailed facades, materials, and construction documentation.
---

# 3D Floor Plan from Drawing

By Mykhailo Svidryk. Adapted from the supplied max-ultra-wall-shell package. Demonstration notes are inherited source observations, not independent practical testing of this catalog package.

Reproduce the user's sequence: trace wall footprints in Top view, resolve curved portions, extrude each storey, align storeys, construct slabs, then form door openings and inspect the assembled shell. Keep the spline source editable beneath Extrude and add Edit Poly above it for openings.

## Before modeling

1. Discover and select the intended Max instance. Inspect the existing drawing, scene units, and relevant objects. Use stable node handles. Preserve the reference drawing.
2. Establish drawing scale from a known dimension. The demonstrated target wall height was **3 m**. The recording used raw Extrude 3000 while Max reported 1 system unit = 1 cm; that numerical convention is not a reusable physical conversion. Resolve the drawing's scale and convert intended dimensions to scene units before building. Do not change system units or rescale existing user work without agreement on that correction.
3. Identify storeys and their corresponding alignment landmarks. Derive thicknesses, gaps, setbacks, and curved walls from the actual drawing rather than from a generic house template.

## Resolve ambiguities before building

Expect imperfect drawings; separate layers and standardized symbols are helpful but are not prerequisites. Inspect the drawing visually together with its geometry before making construction decisions.

When a material detail is unclear (for example wall versus glazing, opening type, jamb location, thickness, conflicting lines, or missing dimensions), **ask the user instead of guessing**. Capture the actual relevant viewport, mark each uncertain location with a clearly visible numbered circle or arrow without obscuring the source lines, and show that annotated screenshot to the user. Pair each number with one short, concrete question; include a closer crop when the overview is insufficient. Batch related questions into one review. Keep the original screenshot for reference and distinguish annotations from source geometry. Do not present a redrawn or invented plan as the actual screenshot.

Record the user's answers against those numbered locations and reuse them throughout the task. Wait for answers before modeling the affected geometry; independent, unambiguous inspection or work may continue. Do not repeatedly ask for information already supplied. Do not silently resolve inconsistent dimensions or ambiguous architectural intent with arbitrary defaults.

Before modeling openings, obtain the following dimensions from the user unless already explicitly established for the current project:

- Door opening height, with separate values for exceptions.
- Height from the finished floor to the bottom of each window (sill level).
- Window opening height.
- Distance from the window top to the ceiling.

Ask in one concise batch, grouped by shared opening type or storey. Establish the intended units, finished-floor reference, and ceiling height. Check that sill height + window height + top-to-ceiling distance equals the floor-to-ceiling height within the drawing's stated precision. If it does not, ask which dimension governs before building. For confirmed floor-to-ceiling glazing, use zero sill and zero top gap and derive the opening height from the confirmed ceiling height; do not ask redundant questions. Previous demonstration values such as 2100/3000 are examples, not defaults for a new project.

## Check floor level changes before modeling

Inspect every plan for short runs of steps, ramps, thresholds, level annotations, and changes in slab or balcony outlines before constructing walls or slabs. Even three short parallel lines in a corridor may indicate a split level; do not assume one floor elevation across an entire storey. Mark unclear transitions on the review screenshot and ask before modeling the affected zones.

For each transition, establish the number of rises and their heights (do not infer the rise count from tread lines alone), ascent/descent direction, and the exact boundary of the raised or lowered zone. Confirm whether the ceiling stays at a shared absolute elevation or steps with the floor. Reuse these answers to create a zone schedule of finished-floor Z, finished-ceiling Z, and clear height. Keep clear room height distinct from floor-to-floor height, slab thickness, floor buildup, and ceiling allowance.

Compute clear height as ceiling Z minus local finished-floor Z. A lower floor beneath an unchanged ceiling increases the room height. Measure door and window heights from each zone's own finished floor; floor-to-ceiling openings extend to that zone's confirmed ceiling. Do not automatically carry one opening height across differently leveled zones. At a doorway crossing the level boundary, clarify the threshold reference if ambiguous.

Build separate editable wall/slab regions where base elevations or heights differ, while preserving the demonstrated spline-and-Extrude workflow. Derive structural slab levels from confirmed finish layers; do not blindly translate an entire storey or its ceiling. Verify the step run, wall bases and tops, slab joins, and adjacent balcony levels in a section or side view as well as perspective. A broad user markup identifies a zone, but is not a precise structural slab boundary where the drawing remains ambiguous.

Confirmed example from the later plan review: three rises of 15 cm connect to a zone 45 cm below the main floor. With a common ceiling and 310 cm clear height in the main zone, the lowered zone has 355 cm clear height. These values are project-specific; confirm new projects independently.

## Trace the walls

1. Work in Top view, zooming into the active area. Trace the footprint of the wall material, including both sides and end returns. Doorway gaps are initially interruptions between wall footprints; the shell does not yet contain finished lintels, door leaves, frames, or window assemblies.
2. Keep multiple closed wall footprints in one Line/compound spline object for each storey or zone sharing the same base and top elevations. Split differently leveled zones as described above. Follow intersections, recesses, and opening jambs from the drawing. Use appropriate snaps after inspecting source geometry; the demonstration did not establish exact snap settings.
3. In the observed first storey the user progressed from the upper kitchen/exterior edge through the entrance and wet-room partitions, then the lower bedroom/stair area and perimeter. Preserve that progression when the same layout is supplied; on a different plan follow connected wall regions coherently.
4. Build rounded portions with Arc matched to the drawing, make it editable as needed, and Attach it to the main wall spline. The user explicitly confirmed this method for the first rounded corner. Remove replaced straight segments, join endpoints as needed, and verify that the resulting wall footprint is closed and has consistent thickness. Retain smooth tangency where appropriate rather than forcing every knot to Corner. See [demonstration notes](references/demonstration.md).
5. Check contour closure, wall thickness, crossings, and duplicate segments before extrusion. Open splines observed during editing are intermediate work, not a required final result.

## Extrude and assemble storeys

1. Add Extrude to the completed wall spline, retaining the Line/SplineShape base. The demonstrated straight-wall extrusion used one segment with both caps enabled. Use the physically intended wall height, normally 3 m for this demonstrated recipe unless the current brief differs.
2. Repeat for each storey as a separate editable object. A demonstrated curved lower-storey outline began as an Arc and was converted to SplineShape before extrusion.
3. Translate storeys in XY to align corresponding structural landmarks; verify multiple points rather than matching only pivots. Set Z from the intended level schedule. The example used a lower level, ground level, and upper level at working values -3000, 0, and +3000, with 3000-high walls. These are example-relative values, not universal coordinates or physical centimeters.
4. Inspect in perspective, temporarily hiding or isolating other assemblies as useful. Preserve and restore the user's visibility state when practical. Inspect curved walls, caps, junctions, and the alignment of stacked storeys.

## Slabs and final check

1. Derive each slab outline by editing a wall spline and removing everything unnecessary for the slab footprint, as the user explicitly demonstrated and confirmed. Retain the wall object: work on a separate copy/derived shape when constructing the slab. The exact copy/detach gesture was not observed. Remove internal wall loops and unwanted fragments, adjust and close the remaining perimeter, then use Extrude. Match recesses and intended voids; avoid accidentally capping required stair openings.
2. The demonstration used raw slab Extrude 300 compared with wall Extrude 3000. A physical slab thickness of 0.3 m is an inference from that ratio and should be confirmed for new work.
3. Adjust each slab outline and elevation independently. The example sampled slab bases at working Z values 0, 2700, and 6000; derive actual elevations from floor and ceiling intent instead of blindly copying those numbers.
4. Inspect the complete shell in Top and perspective. Check slab/wall contact, misalignment, unintended gaps, duplicate coplanar surfaces, and sufficient thickness. Keep separate storey wall objects and slabs editable.
5. Report what is complete and what remains at shell stage. Do not claim finished openings, resolved scale, watertight geometry, or exact command replay without checking them.

## Door openings and lintels

1. Work on the requested wall objects only. When a user's reference shell and an assistant-built shell coexist, preserve the reference and modify only the assistant-built walls. Identify doors and their widths from the drawing, distinguishing ordinary hinged doors, sliding doors, and glazing. Do not bridge every gap indiscriminately.
2. Add an **Edit Poly modifier above Extrude** to retain construction history; do not collapse the stack or replace the spline base. The initial wall footprints already contain full-height gaps at door locations. This step forms the wall material above those gaps, leaving the opening beneath.
3. At a door, select the opposing wall edges and use **Connect** to create the required cut. Position the resulting edges precisely at the user-confirmed door-head height using snaps, as the user demonstrated. Measure height from the relevant finished-floor level, accounting for storey transforms and slab elevation. The original demonstration used **2.1 m intended height**, represented by **2100 drawing units** with walls of 3000 drawing units in that scene. Although the user verbally called 2100 centimeters, that scene has a known scale mismatch: do not interpret that as a 21 m door or apply 2100 blindly to another scene.
4. For an ordinary door, select the opposing elements above the new cut and use **Bridge** to form the lintel. The user called these opposing edges; snapshots also showed polygon sub-object mode during the demonstration. Inspect the actual topology and active component level before choosing the appropriate Edit Poly Bridge operation. Do not guess indices or bridge the lower opening. Preserve consistent wall thickness and connect the lintel cleanly to both jambs.
5. For a **sliding door** where that opposing Bridge construction is unsuitable, select the edges at the wall portion along which the door travels, establish the same head-height cut, and **Extrude toward the receiving wall**. Derive the direction and distance from the actual jambs and destination wall, not from a fixed world axis. Inspect the face/edge selection needed for the actual topology; the demonstration did not establish a universal component index or Extrude dialog setting. Ensure the resulting wall material joins the receiving wall without an overlapping internal cap, duplicate face, or open seam; weld or clean the junction when needed. Do not add a door leaf or track unless requested.
6. Repeat for all intended doors. The user described the same general approach for window openings when needed, but this demonstrated project has **floor-to-ceiling windows**, so leave those glazing gaps full height. Do not add window lintels or sills here. A different window design requires its own sill and head dimensions.
7. Verify in close perspective and against the plan: correct opening locations and widths, head heights relative to each floor, intact space beneath lintels, wall thickness, and clean junctions. Check boundary edges, duplicate/internal faces, and normals before claiming a clean closed mesh. Preserve the editable modifier stack and separate slabs. Report any unresolved topology rather than claiming watertightness from a screenshot alone.

## Pivots

For every modeled wall object, slab, and other newly created model, place the pivot at the center of its evaluated world-space bounding box in X and Y and at its lowest point in Z: `[(minX+maxX)/2, (minY+maxY)/2, minZ]`. This means the object's horizontal center, not world X=0/Y=0. Set the pivot after geometry and placement are finalized, and recheck it after edits that change the bounds. Move only the pivot; preserve the model's visible world-space geometry, alignment, and editable stack. Read back the pivot and bounds to verify the result. Apply this to the objects being modeled, without changing unrelated reference drawings or the user's comparison model.

## MCP execution and efficiency

Use available semantic tools when they preserve this spline-and-Extrude workflow. Do not substitute a monolithic mesh-building pipeline that loses the editable construction. If the semantic surface lacks spline or modifier operations, use small reviewed MaxScript operations under the applicable Max Ultra MCP script rules. Run mutations serially and read back real parameters. During live human demonstration, observe only; do not repair or remodel the scene without a request.

Reuse verified operations and batch compatible work by storey when practical. Inspect shared scene data once, retain confirmed dimensions and classifications, and return compact validation summaries. Capture views at useful review milestones and inspect further when a failure or ambiguity warrants it. Speed must not come from guessing missing information or skipping geometry verification.

