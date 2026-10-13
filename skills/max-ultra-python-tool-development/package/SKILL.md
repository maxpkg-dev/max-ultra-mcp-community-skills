---
name: max-ultra-python-tool-development
description: Build or refactor Python and Qt tools for Autodesk 3ds Max with a MaxScript launcher, clean restart, editable themes, shared controls, bundled-runtime compatibility, and official MaxPkg MZP delivery for newly created tools. Use for standalone tool development, not scene modeling or MCP server implementation.
---

# Python Tool Development for 3ds Max

Deliver a maintainable in-Max tool whose normal entry point is a `.ms` launcher. Running it again must dispose of the previous instance and start one replacement, including when its window is hidden. Creating a script/tool with this skill includes a package-ready project and a locally built installable MZP from the official MaxPkg Packager as the normal final delivery stage. This user-defined default authorizes in-scope local packaging without a redundant permission question; it does not authorize publication, push, or unrelated installation changes. A narrow edit, review or audit does not require an unrelated packaging migration/build unless requested or necessary to its stated deliverable. Do not add a separate custom installer or service: standard MaxPkg packaging is sufficient.

## Establish the tool contract

Inspect existing code and identify the requested behavior, minimum Max release, UI needs, scene effects, and long-running operations. Separate supported targets from versions actually tested. For unknown runtime details, inspect the intended host or current Autodesk documentation before choosing APIs or dependencies.

Before adding responsive breakpoint adaptation, ask the tool's user whether they want it unless they have already explicitly chosen: narrow windows reduce text/control sizes and may use icon-only actions; wider windows enlarge fonts, controls and icons. Do not silently enable those changes. While awaiting the choice, implement ordinary layouts, fit, scrolling and DPI correctness without breakpoint-driven scaling. Record the choice in the generated tool's documentation.

Use these references by task:

- [Architecture and compatibility](references/architecture.md): project folders, runtime APIs, version targeting.
- [Lifecycle and restart examples](references/lifecycle.md): launcher, ownership, cleanup and workers.
- [Qt design system](references/qt-design-system.md): required theme selection, shared controls, states, modality and optional responsive tiers.
- [UI implementation recipes](references/qt-recipes.md): theme/reflow pipeline, clipping, dropdowns, scrollbars, copy feedback and concrete Settings veils.
- [Editable reference palettes](references/palettes.md): actual verified Max Ultra MCP theme files, semantic mappings, provenance and standalone reuse.
- [Regression checks](references/regression-checks.md): lifecycle and polished UI acceptance scenarios.
- [Testing workflow](references/testing.md): smoke, unit, regression, isolated Qt rendering and real-Max MCP fixtures with honest versioned evidence.
- [MaxPkg delivery](references/maxpkg-delivery.md): live official tooling, authoring files, runtime allowlist, real API build, archive verification and installation-test boundaries.
- [Source evidence](references/evidence.md): inspected implementation and limits; the source checkout is not required to use the installed skill.

## Required behavior

- Keep the `.ms` entry point small: resolve its own directory, check the Python bootstrap exists, and execute that file in Max's embedded Python. Do not require users to start a system Python interpreter.
- Keep one stable, tool-specific session owner outside the reloadable package. It owns every window, timer, callback, signal connection, event filter, and background task. A repeated launch requests shutdown and waits for quiescence before replacement; module reload alone is not disposal.
- Make cleanup idempotent and safe after partial initialization. Stop new work, invalidate stale results, unregister only owned callbacks, stop owned timers, disconnect owned connections, and release owned UI objects on the main thread. Record cleanup failures and block a replacement while ownership or worker state remains uncertain.
- Cancel workers cooperatively and use bounded asynchronous shutdown polling. Never terminate 3ds Max, call application-wide quit, kill threads, or kill unrelated processes. An external helper may be stopped only with verified ownership; a shared service needs an explicit shared-lifecycle design.
- Keep `pymxs`, scene/viewport/renderer calls, and Qt UI operations on Max's main thread. Workers receive plain data and return plain results. Reject completion from an old lifecycle or stale scene before applying it.
- Resolve read-only assets from the package location, not the working directory or a developer's machine. Keep durable user preferences/data in an appropriate writable user location; explicitly disposable package-owned settings may live under the dynamically resolved installed package root. Preserve existing settings on update and document uninstall retention. Separate UI, lifecycle, scene operations, domain logic, resources, and documentation as the tool's size warrants.
- Use the Python and Qt bindings shipped with the supported Max release. Reuse Max's Qt application and parent windows to Max. Do not install another Qt binding into its runtime as a compatibility fix.
- Give every tool theme selection, in Settings when available, with Warm Graphite as the default starting theme. Load separate editable semantic-color files on selection, persist the choice, and update every open owned window and rich HTML view immediately. Use original Lucide button icons exclusively unless the user requests another icon set. Follow the shared design-system controls and regression checks; optional breakpoint adaptation still requires the user's choice above.
- Implement shared UI controls once and compose/import them into dialogs: buttons, status pills/badges, fields, dropdowns, spin controls, tabs, menus, progress/overlays and requested About composition. Use semantic variants and shared color/size/spacing tokens; do not copy paint/style implementations per dialog or add drifting local overrides. Named documented variants such as About insets are allowed. Keep compact status labels and numeric values meaningful. A small tool needs only a shared module, not an extra framework.

## Implement and verify

Use an explicit `start` / `request_stop` / `is_stopped` contract when asynchronous work exists. A small synchronous tool may use a simpler equivalent. Document what closing versus hiding the UI does. Keep import-time behavior passive so importing modules does not create windows or mutate scenes.

Follow the testing workflow: smoke, ordinary logic/unit, regression and interface tests, including isolated Qt rendering and screenshots reviewed visually. Test generated tools through Max Ultra MCP in an authorized isolated/synthetic Max fixture when available. Verify each available supported runtime, particularly PySide2/Qt5 and PySide6/Qt6, using actual bundled version probes. If isolation or a runtime is unavailable, record the missing coverage instead of claiming success. Test first launch, repeated launch, rapid double launch, close then relaunch, hidden-window relaunch, startup failure, rerun during work, late worker results, and shutdown timeout. Inspect owned resources to confirm only one active lifecycle remains. Do not open, modify, or save a user's scene merely to validate startup.

For Qt UI, verify targeted binding families, theme switching, keyboard focus, resize in both directions, 200% and higher DPI, dialogs, and missing resources. A standalone Qt test cannot establish Max parenting or callback behavior. Deliver the project layout, launch instructions, supported-runtime assumptions, responsive-layout choice, actual test evidence, and remaining limitations. This is one independently installable community/custom skill, not a built-in product skill. Importing it neither installs a Python tool nor authorizes scene changes.

## Package and deliver

For tool creation, finish the [MaxPkg delivery workflow](references/maxpkg-delivery.md): refresh official guidance, preserve the original packager and both standard hooks, configure the actual project, and build through `MaxPkgPackerApi` in the selected Max instance. The entry remains the `.ms` launcher that starts Python. Inspect inner API responses and final archive contents/version; never rename a ZIP to claim an MZP. Include the source project and exact local MZP result, distinguishing build/archive checks from real install, launch, update and uninstall tests. If official tooling, required facts or a suitable Max connection are unavailable, report the precise blocker and leave the fullest verified ready-to-build project possible; do not claim the MZP was built. Recipes are adaptable instruction examples, not a drop-in library or a guarantee of pixel-identical UI output.
