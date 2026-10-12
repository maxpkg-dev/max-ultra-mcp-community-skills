# Demonstration evidence

Observed on 2026-10-03 through periodic Max Ultra MCP viewport snapshots and read-only scene queries, not a continuous video or complete command log.

## Confirmed sequence

- Trace a compound Line for the first floor drawing. An intermediate read found seven closed spline elements. Door gaps and wall end returns were built into the traced footprints.
- Create the rounded perimeter portion with Arc and attach it to the main wall spline; this method was explicitly confirmed by the user after observation.
- Apply Extrude and retain the Line base; repeat with a separate Line for the next floor drawing.
- Build another curved outline beginning as Arc, convert to SplineShape, and apply Extrude.
- Increase working wall extrusion from 300 to 3000, align plans horizontally, and place storeys at working levels -3000, 0, +3000.
- Inspect in perspective with selective visibility.
- Derive slab outlines by editing the wall spline and deleting unwanted parts, explicitly confirmed by the user. Separate Line-based slabs had Extrude 300; edit their contours and elevations, then inspect the assembled shell.

The user explicitly confirmed the intended wall height was 3 metres. Runtime units nevertheless remained centimeters at scale 1. The skill therefore preserves physical intent and requires a scale check; it does not label raw 3000 as 3 metres in an arbitrary scene.

## Door-opening demonstration and spoken explanation

The user subsequently explained the sequence explicitly while modeling on the reference walls:

- Add Edit Poly to preserve the existing history above Extrude.
- Select opposing edges at a door, use Connect, and position the new cut with snaps at the required height.
- Use an intended default head height of 2.1 m; the demonstrated raw coordinate is 2100 with wall extrusion 3000. The verbal unit label was inconsistent with the known drawing/system-unit mismatch, so preserve physical intent and verify scale.
- Select opposing elements and Bridge to make the wall above an ordinary door. The user described edges, while a sampled state showed polygon sub-object mode; exact selection level and indices must be inspected during implementation.
- At sliding doors where Bridge is unsuitable, make the same height cut at the door-travel wall portion and Extrude toward the wall the door travels to.
- Repeat across doors. The user stated the general approach also applies to windows, but this project's windows run floor to ceiling and need no such opening infill.

Read-only evidence on reference Line001 (handle 136): Edit Poly above Extrude, edge mode initially and polygon mode later; new vertex elevations near 2100 alongside 0 and 3000; visible lintels formed across former full-height gaps. Sampled settings were Connect segments 1, pinch 0, slide 0 and Bridge segments 1, taper/bias/twists 0. These sampled values do not establish every operation's settings. The user aimed for a clean mesh; final manifold topology was not established by observation alone.

## Confirmed split-level correction in the later drawing

The initial review missed a short stair run in plan C. The user identified three steps, confirmed 15 cm per rise, and outlined the right-hand zone as 45 cm lower than the main large-bedroom zone. The user then confirmed 355 cm clear height below a common ceiling, compared with 310 cm in the main zone. This establishes a lowered floor rather than a lowered ceiling. The user explicitly requested that future plan reviews check steps and level differences before modeling. The outlined zone and its dimensions belong to this project, not to all subsequent plans.

## Not established by snapshots

Later explicit user requirements: inspect imperfect drawings and present numbered annotations on actual screenshots for ambiguous details before guessing; obtain door heights and window sill, opening, and top-gap heights before opening construction; set every modeled object's pivot at its horizontal bounding-box center and bottom Z. These are requested workflow rules, not claims that the earlier scene already passed those checks. Reuse prior answers and batch work to reduce unnecessary calls and tokens.

- Exact snaps, hotkeys, or menu actions used during tracing.
- Exact Arc construction parameters and endpoint joining settings.
- Exact copy/detach gesture used to obtain a separate slab object. Editing the wall spline and deleting unwanted portions is confirmed.
- Whether all final wall contours were closed, all floors aligned precisely, and all overlapping surfaces resolved. The last visual check showed an assembled preliminary shell, not a construction-ready model.

When exact reproduction of an unobserved gesture matters, obtain the user's explanation; otherwise use a suitable editable implementation and identify it as an implementation choice.

