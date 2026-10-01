# Mood Design for Architectural Visualization

ArchViz Master v1.2 reference. Use the [worked three-variant brief](mood-example-three-variants.md) when developing alternatives and [illustrated mood evidence](mood-evidence.md) when source reasoning is needed.

## When to use

Use when developing mood alternatives, directing atmosphere or diagnosing why a technically plausible image communicates the wrong experience. Apply to the user's chosen scene and deliverable. A request for a neutral design presentation does not imply a dramatic treatment.

## Establish the intended experience

Extract from the brief, or state provisional assumptions for:

- Situation: what is happening, and what might happen next?
- Viewer role: resident, arriving visitor, passerby or detached observer.
- Intended feeling: a specific phrase such as quiet anticipation before opening.
- Primary visible cues: the few relationships that should convey the situation at delivery size.
- Architectural obligations: geometry, access, finishes and design features that must remain legible and accurate.
- Unwanted interpretation: for example, quiet becoming deserted, shelter looking damp, or dignity becoming inaccessibility.

Ask for clarification only when an unknown materially changes the work. Otherwise label assumptions and proceed with a useful concept. Do not claim to have seen an image or inspected a scene that was not provided.

## Design mood through relationships

### Lighting and weather

Treat weather as a set of visual conditions, not a guaranteed emotion. Overcast light can support clarity, calm or foreboding; context and activity determine which reading is plausible. Identify source direction, softness, visible practical lights and environmental contributions before proposing a grade. [L: PDF 219, 241, 251, 255]

For rain, coordinate wet surfaces, shelter, runoff and activity. Do not prescribe rain streaks, puddles or haze independently of the setting. For an evening welcome, make the destination and route readable rather than tinting the whole image warm.

### Color and material identity

Use relative warm/cool relationships where useful, without requiring orange-blue contrast. Preserve finishes that the brief requires viewers to recognize. Separate changes to illumination, material properties and post-processing in the proposal. A stronger global grade can create unwanted color in regions that should respond differently. [L: PDF 274-275]

### Viewpoint and involvement

Describe the viewer's relationship to the space before choosing camera changes. Framing, occlusion and scale can suggest observation, participation, shelter or exposure, but none has a fixed emotional meaning. Check whether prominent people address the viewer or remain absorbed in their activity. [C: PDF 197, 203]

When asked for alternatives of one frame, preserve camera position, orientation, field of view, projection and crop unless the user asks to explore cameras. Propose camera alternatives separately if the existing view materially prevents the brief from being communicated.

### Action and narrative

Give prominent figures an intelligible action and relationship to architecture. Direction of travel can reverse arrival into departure. Pose, gaze and nearby objects should agree, without relying on details too small to survive the output size. Additional assets are useful only if they explain the situation or spatial use. [C: PDF 219]

### Value structure and spatial reading

Inspect whether value grouping suggests proximity or separation from the main event. Grayscale studies can reveal this before color development, but do not establish a universal value-to-emotion mapping. Stronger depth is not always preferable: a restrained editorial view may intentionally use quieter spatial contrast. [C: PDF 254; P: PDF 170-171]

## Develop and compare alternatives

For a same-frame comparison, record the invariants: camera, architecture, base finishes, planting, primary furniture, output dimensions and color pipeline. Record allowed variables: light, weather, occupancy, small props and surface condition. Wetness may change material response while preserving the specified base material.

Distinguish two modes:

- **Art-direction comparison:** combine several cues into coherent alternatives. Do not claim the result isolates the cause of an emotional response.
- **Diagnostic comparison:** change one suspected contributor while holding relevant others steady. Recheck both the local issue and the whole frame.

Keep output presentation consistent. Exposure and white balance may differ when required for finished alternatives; record those differences rather than enforcing identical numerical settings across different lighting conditions.

For each alternative provide: a short situation, intended reading, lighting/color decisions, activity and props, attention order, likely failure, and a practical check. State whether it is a written concept, paintover, generated illustration, scene edit or rendered result.

## Example briefs for one residential terrace frame

| Alternative | Cue combination | Failure to test |
|---|---|---|
| Quiet morning | Soft illumination, restrained palette, one resident with a cup, readable connection to the garden | Deserted or closed property |
| Shared late afternoon | Localized warm illumination, three people engaged in a conversation, clear circulation | Crowding, staged poses, distracting clothing |
| Shelter in rain | Coherent wet exterior, protected seating, restrained local light, calm occupants | Leaks, exposure, implausible wetness, excessive effects |

These are production interpretations of the sources, not depicted book examples or presets. Adapt them to the actual climate, orientation, design, brief and available scene information. Do not invent verified sun positions or numerical renderer settings.

## Diagnose unintended readings

| Symptom | Competing explanations | Small useful test |
|---|---|---|
| Quiet scene feels abandoned | No readable use; dark destination; poorly visible access | Clarify one plausible activity or the destination, then compare without changing global saturation |
| Welcoming scene feels staged | Unrelated poses; excessive prop symmetry; everyone addresses the camera | Test one coherent interaction and review circulation |
| Atmospheric treatment conceals the design | Compressed values; heavy grade; excessive haze or foreground obstruction | Compare with the suspected treatment reduced while preserving camera and geometry |
| Rain feels like a pasted effect | Dry exposed materials; missing shelter logic; inconsistent water behavior | Hide visible streaks and test whether surface/environment cues still communicate rain |
| Warm treatment loses material identity | Global color shift overwhelms local colors; exposure hides distinctions | Compare required finishes with an ungraded view at matched exposure |
| Scene is dramatic but emotionally unclear | Lighting dominates while action and viewer role conflict | Describe the action without adjectives; revise the inconsistent cue |

These tests suggest causes; none proves all other scene parameters correct. Restore diagnostic substitutions before final delivery unless they are adopted intentionally within the brief.

## Review and stopping criteria

Review the image at intended delivery size and as a small full-frame view. Check intended first read, apparent activity, scale/access legibility, material identity and the most plausible unwanted reading. Use grayscale alongside color; grayscale alone cannot diagnose hue, recognition or narrative.

If useful, ask a reviewer to describe the situation without seeing its title. Record ambiguity instead of asserting that all viewers will feel the intended emotion. Mood evaluation is qualitative and context dependent.

Stop iterating when the requested comparison is delivered, the intended reading is adequately supported and required design information remains clear. Identify unresolved tradeoffs instead of endlessly increasing contrast, saturation, detail or atmosphere. A preview request authorizes a preview; do not silently integrate or install a module when the user has reserved that decision.

## Source register and interpretation limits

All page locators are one-based PDF page indices in the copies examined during development; they may differ in other editions or files. The module is self-contained: the source books are attribution, not runtime dependencies, and should not be bundled.

| Key | Book | Relevant examined pages | Contribution |
|---|---|---|---|
| L | Artists' Master Series: Color and Light | 219, 241, 251, 255, 274-275 | Weather and emotional context; restrained lighting palette and local color |
| C | Artists' Master Series: Composition & Narrative | 197, 203, 219, 254 | Setting, viewer involvement, action direction and tonal proximity |
| P | Artists' Master Series: Perspective and Depth | 170-171 | Alternative color/value treatments and deliberate spatial emphasis |

Book examples support artistic reasoning. Diagnostic tables, terrace briefs and production workflow are synthesized applications, not quotations or validated perceptual models. Do not convert simplified painting statements into universal physical claims: early-morning scenes do not justify disabling indirect illumination, and an unusual warm/cool relationship alone does not establish physical impossibility. Version-specific software controls require separate verification when used; this module specifies none.
