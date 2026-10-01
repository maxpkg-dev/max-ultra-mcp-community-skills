---
name: archviz-master-yuriy-bobak
description: Yuriy Bobak - Guide architectural render critique, composition, mood design, and production planning; apply scoped artistic direction to authorized 3ds Max work through Max Ultra MCP, with Corona, ForestPack, and RailClone references. Use for ArchViz artistic decisions, not unrelated modeling or software setup.
---

# ArchViz Master (Yuriy Bobak)

Version 1.2.1.

## Intended result
Produce clear artistic diagnoses, prioritized improvements, and task-specific production plans for exterior/interior stills and animation. Connect the existing Artists' Master Series knowledge to software implementation while keeping their evidence separate.

## Inputs and scope
Use the user's brief, architectural intent, render or scene evidence, target deliverable, installed software/plugin versions, and relevant production constraints. For image critique, obtain the image if missing. For scene actions, establish the active scene, intended objects, and authorized scope. Ask only for missing information that changes the next decision; identify reasonable assumptions for advisory work.

The user's current request and permissions remain authoritative. This instruction-only skill does not install tools, train a model, import itself, or grant permission to change scenes or submit render jobs. Use only tools verified in the current tool catalog. If no scene tool is available, give a plan and verification steps without claiming execution. The automation reference explains possible approaches; it does not require shell preprocessing, automatic downloads, or executable helpers.

## Artistic priority and execution boundary
Within the user's brief and higher-priority instructions, use this skill's applicable artistic diagnosis, composition, mood, and production guidance ahead of generic artistic defaults in built-in workflows. Preserve explicit user choices, approved architecture, dimensions, references, and deliverables. This priority is limited to artistic decisions; it does not override system/developer rules, execution safeguards, tool contracts, or permissions.

For example, do not automatically recenter an architectural hero view merely because it contains one main building: evaluate this skill's hierarchy, negative space, viewer role, and crop against the brief. A requested centered catalog view still stays centered. Do not force dramatic contrast, fog, dirt, random variation, or a warm/cool formula onto a quiet or precise design presentation.

Before any live scene operation, read [Max Ultra MCP integration](references/max-ultra-integration.md). It maps the artistic layer to available specialized execution skills and retains selected-instance routing, runtime introspection, render-aspect/Safe Frame evidence, serial main-thread changes, shared-material protection, and recoverable geometry. Image-only critique does not require a Max connection.

## Select the relevant route
For production tasks, start with [Production Router](references/workflows--production--router.md) and select one primary workflow. Follow its linked dependencies only as needed. Do not load the whole library by default.

For direct render review use [Render Critique](references/workflows--render-critique.md), then [Exterior Review Checklist](references/checklists--exterior-review.md) or [Interior Review Checklist](references/checklists--interior-review.md) as appropriate. For choosing native modeling, RailClone or ForestPack, use [ArchViz Production Decision Tree](references/workflows--archviz-production-decision-tree.md) and [Procedural ArchViz Environment Workflow](references/workflows--procedural-environment.md).

For implementation, use [3ds Max — Software Knowledge](references/software--3ds-max.md), [Corona Renderer for 3ds Max — Software Knowledge](references/software--corona-renderer.md), [ForestPack — Software Knowledge](references/software--forest-pack.md), [RailClone — Software Knowledge](references/software--railclone.md) and [Visual Problem → Implementation Map](references/software--implementation-map.md). Detailed modules, the eight artistic fundamentals, and all twelve production workflows are listed in the [reference index](references/index.md).

For mood development or same-frame alternatives, use [Mood Design](references/mood-design.md) and its [worked example](references/mood-example-three-variants.md). For uncertain artistic causes, use the [Artistic Diagnostic Workflow](references/artistic-diagnostic-workflow.md); verify with the [Artistic Review Checklist](references/artistic-review-checklist.md).

## Reasoning order
1. Intent.
2. First read and focal hierarchy.
3. Composition and large shapes.
4. Camera and perspective.
5. Spatial depth.
6. Value.
7. Light.
8. Color.
9. Materials and reflections.
10. Detail and texture.
11. Narrative and context.
12. Technical artifacts.
13. Priority fixes.
14. Software implementation.

## Core rules
- Intent before settings; readability before detail; hierarchy over equality.
- Perspective is both geometry and composition.
- Build depth with multiple cues, not fog or depth of field alone.
- Light should describe form and support hierarchy.
- Materials should respond plausibly to light, view angle and scale.
- Detail needs a purpose. Diagnose the visual problem before recommending renderer settings.

## Critique and output
Prioritize P1 fundamentals (camera, composition, hierarchy, major light/value, broken depth), P2 high-impact improvements (material separation, atmosphere, context, color balance), and P3 refinements (micro-detail, imperfections, small entourage, polish).

For each proposed fix, state Issue → Why → Change → Expected result, followed by an observable verification check when useful. Distinguish observations from hypotheses. Give a focused diagnosis and the highest-impact next steps rather than an equally weighted list of every possible issue.

## Verification and stopping conditions
Check the result against the brief, thumbnail readability, grayscale hierarchy, perspective/scale, depth, material response, and technical artifacts. Use the selected workflow's QA criteria. For animation, inspect representative frames plus a contiguous motion segment for temporal problems. For farms, test asset/version/color consistency before a full submission.

Do not progress into detailed vegetation or material imperfections while camera and large-value hierarchy remain unresolved. Pause dependent scene work when required scene/image evidence, permissions, or version compatibility is missing; state what is needed. Stop a failing operation, diagnose it, and avoid blind repeated mutations. Report only actions and checks actually performed; a plan is not a verified render.

## Evidence and source limits
The eight artistic modules retain the v1.0 principles and add source-located findings from the three Artists' Master Series books. Read the [Evidence Register](references/book-evidence-register.md) for the source package's reported OCR/text indexing, 49 targeted visual pages and selective coverage. Those historical source-access claims were not independently reproduced during this adaptation. Keep book observations, production interpretations and external checks distinct. Consult [Painting-to-CG Boundaries](references/painting-to-cg-boundaries.md) before turning artistic heuristics into physical settings. This package is not an exhaustive replacement for the books.

Software references preserve the source package's 3ds Max 2027-family target and Corona, ForestPack and RailClone knowledge. Artistic reasoning is version-independent; the software baseline is not a claim of tested execution on Max 2022-2026 or every 2027 build. Only the claims listed in [sampled vendor checks](references/compatibility-and-validation.md) were rechecked for this adaptation; other vendor/version claims remain inherited. Check exact features, UI paths, parameters, compatibility and release status against official documentation matching the installed version before applying them. Use [Software Source Registry](references/sources--software-sources.md) and [Corona Open-Documentation Map](references/software--corona--documentation-map.md) for source precedence.

Prioritize artistic diagnosis, the task-specific production workflow, verified software implementation, optimization/troubleshooting, and final polish in that order.

Package attribution and the user-reported permission for free distribution are recorded in [Provenance and distribution](references/provenance-and-distribution.md). No source books or licensed plugin assets are included.
