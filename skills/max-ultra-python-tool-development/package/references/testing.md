# Testing generated Python/Qt tools

Design tests around externally observable behavior and failure boundaries. A test that repeats a formula from the implementation or searches its source for a method name does not establish that the tool works. Keep tests in the generated tool's `tests/` folder; do not execute imported skill content automatically.

## Test layers

| Layer | Example and execution | Evidence / limit |
| --- | --- | --- |
| Smoke | In a fixture, launch the `.ms`, find one owned window, invoke a harmless action, stop and relaunch | Fast end-to-end readiness; not exhaustive behavior or visual review |
| Ordinary logic/unit | Run pure modules with `python -m unittest discover -s tests -v` in an isolated test environment; palette parsing, settings defaults, typed sorting, resource resolution | Deterministic input/output behavior without Max; cannot prove host APIs |
| Lifecycle regression | Fake workers and callback registries; inject failure after acquisition, cancellation refusal and late completion; assert counts and externally visible effects | Cleanup/retry contract under controlled failure; add real timers/host verification |
| Isolated Qt interface | Separate process for each installed PySide family; synthetic controller/data, no scene API; actual events, rendering and screenshots | Widget behavior in that runtime/platform; not Max's proxy style, parenting, accelerators or native modality |
| Real-Max integration through Max Ultra MCP | Explicitly select a dedicated disposable Max instance, run synthetic fixtures through the normal `.ms` launcher, inspect windows and capture visuals | Actual embedded runtime, main-thread behavior and host integration for recorded versions only |
| Visual review | Open rendered images at native resolution and inspect corner clipping, baseline, text, icons and states | Human/agent observation supplements assertions; saved screenshots alone are not reviewed evidence |

Never run a reference fixture unchanged just because it exists. Read it first: the reference `tests/run-qt-fixtures.py` requires a dedicated-process marker **and calls `rt.quitMax(noPrompt=True)` in its finalizer**. That runner is evidence of isolation design, not a safe reusable harness. Do not copy that exit behavior into this skill's generated fixtures; never terminate 3ds Max. Close only the fixture's owned widgets and resources.

## Fixtures and data isolation

Create synthetic names, rows, documents and long captions. Inject a temporary writable settings/log directory and fake I/O services. Keep production preferences, real asset paths, credentials, callbacks and scenes untouched. Disable autostart, update/install actions and external integrations in the fixture. No network is needed for control rendering. Record snapshots of relevant host state before and after a host test, and assert no unintended scene changes.

Use a fixture controller exposing only the public behavior needed by the view (settings read/write, operation requests, current status). Record operation requests so a right-click test can prove that no document load was requested. Exercise actual mouse/key events rather than directly invoking every handler. Use Qt's test support or event-loop conditions with deadlines; no unbounded sleeps. Tests may pump their isolated event loop for verification; production code must not use nested `processEvents()` loops to appear responsive.

For unit tests, assert known examples and boundary outcomes: malformed/missing theme roles leave the previous theme; a mix of black and white at 0.5 is `#808080`; version 1.10 sorts after 1.9; a timeout prevents the replacement constructor; a late result produces no UI write. For settings, simulate a write failure and assert an unsaved-state diagnostic. Pure tests should not import `pymxs` or Qt just to test numbers and paths.

## Runtime and matrix selection

Discover available Max installations/instances and record their actual Max build, `sys.version`, binding version and `QtCore.qVersion()`. Do not infer the embedded interpreter from a system Python. For every **available supported** runtime, run the relevant host fixtures; cover both PySide2/Qt5 and PySide6/Qt6 when available. Record unavailable combinations as not run, not passed. Do not install incompatible binary bindings into Max to manufacture coverage.

For standalone rendering, use a Python interpreter compatible with the selected PySide wheel in a separate environment. A test harness may create its own `QApplication` only outside Max. Use an offscreen platform only where that binding/platform supports it; use a visible isolated test process for focus, popups or native effects when offscreen cannot represent them. Set test-only scale variables before application creation, never mutate the running user's Max DPI configuration. Record the effective device pixel ratio and logical DPI because requested scale is not proof of applied scale.

Cover:

- Sizes: minimum, normal, large; both resize directions; just below/at/above each **user-approved** breakpoint. If adaptation was declined, assert stable font/control sizes and usable scroll/reflow instead.
- DPI: 100%, 200%, and an available greater-than-200% scale, plus mixed-DPI monitor movement when available.
- Themes: all shipped palettes; host palette dark/light samples; switch while Settings, dropdowns, menus, progress and HTML views exist.
- States: enabled/disabled, hover/pressed, selected/focused, checked/unchecked, loading/error/success, empty/long content; numeric bounds and read-only spin boxes if used.

Keep focused regression cases for [the documented bugs](regression-checks.md), not a combinatorial screenshot explosion. Expand combinations where failures reveal a dependency. Store unique artifact names containing runtime, theme, size, scale and state so one run cannot overwrite another's evidence.

## Real-Max testing with MCP

For generated tools, real-Max verification is required when an authorized isolated host is available. Use Max Ultra MCP: list instances first, explicitly select the only instance or the uniquely identified disposable fixture instance, and resolve ambiguity before actions. Inspect capabilities and runtime versions with read-only calls. Use available MaxScript execution/file execution tools to run the generated `.ms` entry point on the main thread; do not assume a tool name or argument schema without discovering it.

Verify launch/relaunch while visible, hidden, working and stopping. Count owned windows/timers/callbacks and prove old callbacks stop firing. Open Settings and other tool dialogs, apply themes, interact with menus, and obtain screenshots of the **tool windows**, not merely an unrelated viewport. Use Max-owned UI capture or an approved capture capability; a `QWidget.grab()` fixture image is useful but may omit native chrome/shadows. Review actual pixels for modal stacking and focus if capture cannot show them reliably. Test operation failures and cleanup without real scene data.

If only a user's working scene is available and isolation cannot be established, do not alter/reset it to run a fixture. Complete pure and standalone tests and report the host-test blocker. Do not claim PySide2/Qt5 coverage from a PySide6 run, or future-version compatibility from import fallback alone.

When adding a new Max/Qt combination, first record versions and probe capabilities (parent-window helper, enum forms, event APIs, overloads, shiboken validity and widget style behavior). Add a narrow compatibility adapter and rerun lifecycle and UI matrices. Keep unsupported/unavailable environments explicit. Do not add a guessed release-number branch or market a future release as supported without evidence.

## Reference fixture lessons

These files were inspected read-only as patterns, not executed or bundled:

| Reference fixture | Useful behavior to reproduce in the generated tool's own tests |
| --- | --- |
| `tests/qt-ui-fixture.py` | Synthetic status and temporary data, exact button geometry, log viewport/mask, bounds and screenshots; hide stops overflow timer and unchanged text does not reset it |
| `tests/qt-dialog-fixture.py` | Fake controller operations, narrow row fitting, modal veils, elapsed progress, copy feedback, document navigation and resize reentrancy; latest document case checks one metadata occurrence/frame |
| `tests/qt-theme-fixture.py` | Multiple windows and real combo popup; deliberately rejects item-view no-argument update calls; repeated palette changes preserve literal hex text in documents |
| `tests/qt-copy-fixture.py` | Shared copy controls restore captions/icons after feedback and use restartable owned timers |
| `tests/qt-progress-fixture.py` | Actual rendered pixels at track corners, determinate/indeterminate values and animation stop/start on hide/show |
| `tests/run-qt-fixtures.py` | Records host/Python/Qt/DPI results in a dedicated process; its application-exit finalizer must not be reused |

A geometry assertion can test non-overlap and containment; a pixel check can detect an opaque corner or wrong track color. Neither alone proves readability. Review screenshots at native scale, especially high-DPI icons, compact controls, popup masks and tab seams. For native shadows or modality, include host capture and interaction observations.

## Evidence report

For each run record fixture name/revision, environment, command or MCP action, expected invariant, actual outcome, artifact path and limitations. Separate syntax/static, mocked, standalone Qt, and real-Max results. Report skipped fixtures and reasons. Do not call a package importer check a smoke test of the generated tool. Do not claim visual verification just because PNG files were saved.
