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
| MaxPkg build/archive | Run the original official packager API in the selected Max instance; inspect inner results and final inventory/manifests | Proves a verified local artifact, not installation or update behavior |
| MaxPkg install/update/uninstall | In an authorized isolated profile, test installed launcher/restart, prior-version update, settings retention and owned cleanup/reinstall | Separate actual installation evidence; never infer from build success |
| Visual review | Open rendered images at native resolution and inspect corner clipping, baseline, text, icons and states | Human/agent observation supplements assertions; saved screenshots alone are not reviewed evidence |

Never run a reference fixture unchanged just because it exists. Read it first: the reference `tests/run-qt-fixtures.py` requires a dedicated-process marker **and calls `rt.quitMax(noPrompt=True)` in its finalizer**. That runner is evidence of isolation design, not a safe reusable harness. Do not copy that exit behavior into this skill's generated fixtures; never terminate 3ds Max. Close only the fixture's owned widgets and resources.

## Fixtures and data isolation

Create synthetic names, rows, documents and long captions. Inject a temporary writable settings/log directory and fake I/O services. Keep production preferences, real asset paths, credentials, callbacks and scenes untouched. Disable autostart, update/install actions and external integrations in the fixture. No network is needed for control rendering. Record snapshots of relevant host state before and after a host test, and assert no unintended scene changes.

Use a fixture controller exposing only the public behavior needed by the view (settings read/write, operation requests, current status). Record operation requests so a right-click test can prove that no document load was requested. Exercise actual mouse/key events rather than directly invoking every handler. Use Qt's test support or event-loop conditions with deadlines; no unbounded sleeps. Tests may pump their isolated event loop for verification; production code must not use nested `processEvents()` loops to appear responsive.

Exercise shared components in at least two different dialog compositions, including a documented variant such as About spacing. A common button/menu/field fix must produce the corrected interaction and rendering in both windows; do not merely assert equal class names or copied stylesheet strings. Test pills with large numeric values and compact labels so numbers/units remain available rather than becoming ellipses. Verify semantic variants inherit theme, focus, disabled and DPI behavior without per-dialog drift.

For unit tests, assert known examples and boundary outcomes: malformed/missing theme roles leave the previous theme; a mix of black and white at 0.5 is `#808080`; version 1.10 sorts after 1.9; a timeout prevents the replacement constructor; a late result produces no UI write. For settings, simulate a write failure and assert an unsaved-state diagnostic. Pure tests should not import `pymxs` or Qt just to test numbers and paths.

## Runtime and matrix selection

Discover available Max installations/instances and record their actual Max build, `sys.version`, binding version and `QtCore.qVersion()`. Do not infer the embedded interpreter from a system Python. For every **available supported** runtime, run the relevant host fixtures; cover both PySide2/Qt5 and PySide6/Qt6 when available. Record unavailable combinations as not run, not passed. Do not install incompatible binary bindings into Max to manufacture coverage.

Run Qt checks inside 3ds Max through Max Ultra MCP (below). Do not start a `QApplication` in the `python.exe` that ships with Max, outside Max: Max ships only the `windows` platform plugin (no `offscreen`), so an offscreen attempt shows a fatal Qt message box on the user's desktop, and a visible run puts windows in front of the user's work. Pure logic tests that import no Qt may run outside Max. Never mutate the running user's Max DPI configuration; record the effective device pixel ratio and logical DPI because requested scale is not proof of applied scale.

Cover:

- Sizes: minimum, normal, large; both resize directions; just below/at/above each **user-approved** breakpoint. If adaptation was declined, assert stable font/control sizes and usable scroll/reflow instead.
- DPI: 100%, 200%, and an available greater-than-200% scale, plus mixed-DPI monitor movement when available.
- Themes: all shipped palettes; host palette dark/light samples; switch while Settings, dropdowns, menus, progress and HTML views exist.
- States: enabled/disabled, hover/pressed, selected/focused, checked/unchecked, loading/error/success, empty/long content; numeric bounds and read-only spin boxes if used.

Keep focused regression cases for [the documented bugs](regression-checks.md), not a combinatorial screenshot explosion. Expand combinations where failures reveal a dependency. Store unique artifact names containing runtime, theme, size, scale and state so one run cannot overwrite another's evidence.

## Interface harness inside 3ds Max

The real test of the UI runs the tool **inside 3ds Max through Max Ultra MCP**, on each available Max (PySide2 and
PySide6), without showing anything to the user:

- Start it with `max_execute` / `max_run_script` running `python.ExecuteFile @"...\harness.py"` in an explicitly selected
  instance. The harness reads its settings (tool root, report folder, interface size) from a JSON file, never from the
  user's settings.
- Before importing the tool: load it from the test copy, redirect `settings.user_data_dir` to a scratch folder (the
  user's own settings and logs are never touched), and install an application event filter that sets
  `Qt.WA_DontShowOnScreen` on every window of the tool at its first polish: Qt shows and lays out the windows, nothing
  appears on screen. Make `activateWindow` a no-op on the tool's window classes (never take Max's focus) and skip DWM
  calls on off-screen windows.
- Drive it with timed steps (`QTimer.singleShot`, Max's own event loop; nothing blocks): open each dialog, show
  questions with `show()` instead of the blocking `exec`, run a job, collapse and restore, switch theme, then
  `request_stop()`. Write a report line per step and "END" last; wait for that line from outside.
- At the end undo every patch, remove the event filter and the path entry: the user's Max keeps nothing of the test
  but a few unloaded modules.
- Pass flags for special starts: a pre-written start guard file and crash log for a "crashed last time" start, a stand-in
  host window for the collapsed bar's following, a dead screen object for the screen lookup fallbacks.
- **Screenshots: grab the tool's own windows** (`widget.grab()` works on off-screen windows; several windows painted
  at their places on a neutral backdrop). Never capture the screen: it takes whatever else the user has open. Round the frameless main window's
  corners in the picture as Windows 11 shows them. Review the pictures at native size and zoom into details (scroll
  thumbs, 1 px borders, corners).
- Record per run: interpreter, binding and Qt versions, interface size, fonts of a few widget kinds (they must match),
  again after a theme change, inside an open menu and in About.
- **Never move the user's mouse** (`QCursor.setPos`) and never send keys or clicks to the user's windows. Code that
  reads the pointer takes the position from a replaceable function (`ErrorHints.cursor_pos`); the test gives its own
  and sends the event itself (`QEvent.Enter`). Open popups through their methods (`HelpButton.toggle`,
  `DateField._open`, `ComboBox.showPopup`, `QMenu.popup` instead of the blocking `exec`).
- Keep the run's own paths out of pictures and logs: a log record or traceback shown in a screenshot must not carry a
  real user folder (write synthetic records, rewrite the install path in the test's log handler).

The harness cannot show Max parenting, Max hotkeys, viewport rectangles or host crashes; repeat the essential steps in
Max through MCP.

### Running checks in the Max the user works in

The interface harness installs an application-wide event filter that keeps windows off screen and replaces the
tool's modules while it runs. In a Max where the user runs a copy of the same tool (a demo, the trainer), it must
hide only the windows of its own classes (compare the class with the one its module now holds) and put the user's
modules back in `sys.modules` at the end; otherwise a dialog the user opens during or after the run is invisible and
its veil locks the window. Prefer a second Max for checks while the user tests by hand, and relaunch the user's copy
afterwards.

### Keys and tooltips in a fresh Max

A fresh 3ds Max session takes an Esc sent with `sendEvent` to a widget that does not have the keyboard focus (the
off-screen test windows have none), and every ToolTip event, at the application level: the widget never sees them.
Checks of an Esc handler call the widget's `keyPressEvent` directly; checks of a tooltip send Enter and call the
keeper's `show_for` (what the hover delay does). A run in a Max where a tool window had the focus may pass either way,
so a check that passes there proves nothing about a fresh session.

### Keep test scripts ASCII

`python.ExecuteFile` in 3ds Max 2022 read a UTF-8 test script in the system code page: a literal "…" in a check became
"â€¦", and the check passed against its own garbled text while the picture showed it. Write non-ASCII characters in
test scripts as escapes (`"Refreshing\u2026"`); the tool's own modules are imported as UTF-8 and may keep them.

### When Max dies without a traceback

A native crash (Windows event log: `3dsmax.exe`, exception `0xc0000374` or `0xc0000005`) leaves no Python traceback
and often no faulthandler dump. Find it by bisection inside a Max that holds no user work: build each new widget in
its own hidden window with flushed markers, then the whole window with parts switched off by halves, then the suspect
part by part (see [Max reliability](max-reliability.md#qt-objects-that-took-max-down)). Never bisect in the user's own
Max session or with their tool window open.

## Real-Max testing with MCP

For generated tools, real-Max verification is required when an authorized isolated host is available. Use Max Ultra MCP: list instances first, explicitly select the only instance or the uniquely identified disposable fixture instance, and resolve ambiguity before actions. Inspect capabilities and runtime versions with read-only calls. Use available MaxScript execution/file execution tools to run the generated `.ms` entry point on the main thread; do not assume a tool name or argument schema without discovering it.

Verify launch/relaunch while visible, hidden, working and stopping. Count owned windows/timers/callbacks and prove old callbacks stop firing. Open Settings and other tool dialogs, apply themes, interact with menus, and obtain screenshots of the **tool windows**, not merely an unrelated viewport. Use Max-owned UI capture or an approved capture capability; a `QWidget.grab()` fixture image is useful but may omit native chrome/shadows. Review actual pixels for modal stacking and focus if capture cannot show them reliably. Test operation failures and cleanup without real scene data.

Host fixtures that cannot avoid the user's Max: back up the tool's settings file first and diff it after; use the settings object's session-only overrides for every key a fixture changes (never write test values to the user's file); block signals or restore values on controls the fixture changes; before touching the window, check that no job runs; stop the tool before writing a start-guard file (a stopping session writes "stopped" over it); put each window action in its own timer step (pymxs calls inside one step can run other pending timers); afterwards put back what was changed (window places, Max's window state, frozen collector objects with `gc.unfreeze()`). While a build or other heavy work runs in a host, do not run UI Automation walks or grab windows (a Max 2022 crash coincided with both). Never send keystrokes to a user's Max.

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
