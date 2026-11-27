# Inspected source and limits

## MaxPkg Packager 2.0 (version 1.2.0 of this skill)

Version 1.2.0 (2026-11-11) carries the interface components the owner approved while MaxPkg Packager 2.0 was built:
a Python + Qt rewrite of the official MaxPkg packaging tool for 3ds Max 2022-2027 by the same author (repository
`maxpkg-dev/max-dev-tool`, branch `python-qt-rewrite`; its `maxpkg-src` folder was read as an uncommitted working tree on
2026-11-11). The owner asked for these components and rules to be captured in this skill.

| MaxPkg Packager source | Carried into the skill as |
| --- | --- |
| `ui/tool_window.py` `HEADER_SHADE`, `header_bottom`, `paintEvent`; `controls.WindowButton`; the compact collapsed bar | [tool-window](templates/tool-window.md), [windows](window-chrome.md) |
| `ui/pages.py` `required_mark`, `caption`, `labeled`, `panel`, `Collapsible`, `_GroupHeader`, `scroll_page` | `ui/forms.py` on the [forms](templates/forms.md) page |
| `ui/changelog.py` `KindComboBox`, `KindDelegate`, `draw_badge` | `forms.BadgeComboBox`, `BadgeDelegate`, `draw_badge`, generalized to any (name, log role) list |
| `ui/pickers.py` `Stepper`, `DateField`, `CalendarPopup`; `ui/switch.py` `Switch` | [forms](templates/forms.md) |
| `ui/controls.py` `help_html`, `Balloon`, `HelpButton`, `ComboBox`, `Menu`, `round_popup`, `boxed`, `unify_heights`, `NumberBadge`, `ErrorTip`, `ErrorHints`, coloured disabled buttons | [controls](templates/controls.md) |
| `logs.py` daily files; `ui/logwindow.py` `LogDialog`; `ui/statuslog.py` `StatusLog`, `paint_pills`, `pill_box`, `band_span` | [logs](templates/logs.md) |
| `ui/dialogs.py` `how_to_card`, modeless `ToolDialog`, the About footer; `themes.derived`; `ui/style.qss` rules | [dialogs](templates/dialogs.md), [themes-style](templates/themes-style.md) |
| The Lucide `logs` icon as used by MaxPkg Runtime Manager | Status bar and icon table |

Generalized while assembling: names (`mytool`, `MyTool`, `tool` object names), the badge dropdown, the example
content (a showcase of every control on three tabs instead of the packager's pages), and the log file prefix. Fixed
while assembling, each found by the standalone harness: the mini log and the Logs window stored their monospaced font
in `self.font`, which hides `QWidget.font()` and made `inherit_fonts` fail at any interface size other than 100 %
(renamed `mono_font`); a theme change left fields at the default 9 pt (`ThemeManager._apply` now runs `inherit_fonts`
after `setStyleSheet`; the 1.1.x starter had the same gap); menus opened at the default font (`Menu` takes its
window's font and `fit_fonts` before it is measured); the badge dropdown re-fits its width when the interface-size
font arrives; About grows once after its first layout pass so its body does not scroll. Not carried: the packager's
own toast messages (Runtime Manager's are used instead), its project model, updater and setup window, and the frameless dialog redesign that
was still in progress in that working tree.

Later the same day the owner added four requests, carried as well: the status bar's **View Logs** text action exactly
as MaxPkg Runtime Manager Qt has it (`ui/manager_window.py`, `assets/manager.qss` `#StatusAction`); **toasts** as
Runtime Manager Qt shows them (`Toast`, `StatusIcon`, its stacking and lifetimes; only toasts inside the window, not its
translucent screen-corner toasts); **every window in the main window's chrome** and questions instead of
`QMessageBox` (MaxPkg Packager's frameless `ToolDialog`, `ConfirmDialog`, `ask`, the size grip, no dotted focus frame);
the rule to use the catalog with judgment ("Choosing controls"); and the rule that scrolling never changes a field (the
wheel over a dropdown or a stepper scrolls the page, focused or not; MaxPkg Packager's `ComboBox.wheelEvent` and `Stepper`); and the
rule that an outlined popup is outlined on every side, the arrow included (MaxPkg Packager's `controls.paint_bubble`). The owner also asked to stop running Qt in Max's
`python.exe` outside Max: the early standalone runs showed windows on the desktop, and an attempt with the
`offscreen` platform, which Max does not ship, raised a Qt error box. Checks now run only inside 3ds Max.

Verification: the starter was regenerated from the template pages (the extracted files were compared with the tested
project: identical), compiled with Python 3.7.9 and 3.13.9, and run as one project **inside 3ds Max 2022** (Python 3.7.9
/ PySide2 5.15.1) **and 3ds Max 2027** (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP (`python.ExecuteFile` of a
harness; the tool's windows created with `WA_DontShowOnScreen`, settings and logs in a scratch folder, the pointer
faked, every patch undone and the session stopped at the end; empty scenes, not modified) at 125 % interface size: 46
checks passed in each (one control height; the help balloon, error bubble, menu and calendar rendered through
their own masks show the border colour on every side and down both sides of an arrow to its point; the wheel over a dropdown (with focus claimed) and a stepper changes
nothing while the open calendar still turns its month; one font size at start, in a menu, in Settings, in About and after a theme
change; View Logs first in the status bar with a 12 px icon and no Logs button on the right; the badge dropdown and its
list fit the badge; optional groups closed or open by data; a click on a mini log row reaches its field and flashes
it; the error bubble absent after Enter alone and shown after a 3 px move of the faked pointer; toasts below the header,
stacked, a repeated key shown again instead of twice; a question in the tool's frame with the neutral default and a red
action; a rounded menu at the window's font; the compact collapsed bar; Settings frameless with its title bar and veil;
About without scrolling; Logs frameless, not modal, with a size grip, two days with Today first, a click selecting a
whole record, the summary and Clear Logs; the Max theme; the mini log's green line; Run with its shimmer; a background
job with the progress bar in place of the message, ending with a toast). Earlier in the preparation the same checks
(38, before these additions) passed outside Max on both bindings. The reference pictures in `assets/` come from the run
inside 3ds Max 2027 (graphite and Max themes; `widget.grab()` of the off-screen windows, composed at their places; log
records synthetic). Native effects (Windows 11 corner rounding, real window activation, system moves) and the launcher's
restart path were not exercised by these runs. No practical skill test or reviewer is recorded.

### The controls trainer, self-update and donations (later on 2026-11-11)

The owner then asked for a "controls trainer" that shows everything in one design, and for more parts, each carried
from the author's own tools: self-update and Settings > Updates (MaxPkg Packager's `core/updater.py`, generalized as
`updater.py`, `tools/release.py` and the launcher's `pick_root` / rollback); the tool's own message and prompt windows;
instant checks of web addresses; the Settings window as tabs or as a list on the left, coloured filter pills, soft
edges of scrolling areas, the busy overlay, empty states, search with suggestions, the clearable filter and the copy
button (MaxPkg Runtime Manager Qt: `settings_panel.py`, `pages.py` `CollectionPill`, `widgets.py` `EdgeFade`,
`StatePanel`, `SearchBox`, `ClearableDropdown`, `CopyButton`, `manager_window.py` `WorkShade` / `BusyCard`); the
Support window with its shimmering Donate (Runtime Manager's `dialogs.SupportDialog`); the result card with a donation
line (MaxRewind's `controls.Notice`, same author; its `Shimmer` equals the skill's); footers of one size (the owner's
observation that About's Close looked smaller than Donate: both were 30 px high, Close was narrow with a faint edge);
and the whole donation story with the owner choosing the offers ([donations](donations.md)). Sliders, the colour
picker, badges, tags, status dots, the list editor, cards, the gallery and the welcome window were written for the
trainer in the same style.

Found and fixed inside Max while the trainer was checked:

- **A native crash in 3ds Max 2022.** The first run took Max 2022 down (`0xc0000374`, heap corruption, no traceback).
  Bisection inside Max (each widget alone, then the window with sections switched off by halves, then the search field
  part by part) named the search field's completer, which was a child of its own line edit. With TerraScoop's pattern
  (the window owns the completer, the list is created and set with `setPopup`) the window shows, filters and closes
  with Max staying up. See [Max reliability](max-reliability.md#qt-objects-that-took-max-down).
- **PySide6 calls an event filter from the base constructor.** In 3ds Max 2027 the Support and message windows failed
  to open: `ToolDialog.__init__` already ran their `eventFilter`, before their own attributes existed. They now read
  them with `getattr`; Max 2022 never showed it.
- A plain `&` in a section name ("Cards & Gallery") vanished: `Button.setText` now doubles it.

Verification of the final code: the template pages were regenerated from the starter and compared (identical);
compiled with Python 3.7.9 and 3.13.9; the trainer harness (the 1.2.0 checks above plus the trainer's) ran **inside
3ds Max 2022** (PySide2 5.15.1) **and 3ds Max 2027** (PySide6 6.8.3) at 125 %, windows off screen, settings in a
scratch folder, empty scenes: **145 checks passed in each** (206, then 235 after the rounds below), including nine sections in a list with a count badge, a
plain `&`, no sideways scrolling in any section, the wheel never changing a slider, arrow keys on a slider, a range
keeping its order, the colour picker as a rounded card, search suggestions, the empty state of a search and its way
back, the list editor refusing a duplicate and counting pasted lines, the copy button's check, soft edges at the top
and bottom of a list, filter pills dimming the others and an empty category, the gallery's arrow keys, the busy
overlay over the sections ending on its tick, the result card with Donate and its shimmer, the Support window as the
reminder (Not now and Donate one size, Donate shimmering, "Don't remind me again"), the welcome window's buttons one
size, Settings as tabs (Close at least 92 px) and as a list (five sections, Reset in red), About's Donate and Close one
size, an error message in the tool's frame, the donation rules (reminder on the 5th start and then every 30, the line
from the second success and once a session, off after "Don't remind me again", nothing without an address), and the
self-update checks: an update found and installed from a `file:///` release, `current.json`, the pill and toast, the
launcher starting the newer copy, a second version keeping the first as previous, rollback twice, and a checksum
mismatch installing nothing. Last, at the parent session's request with the owner's results from MaxPkg Packager 2.0: the error bubble and the
help balloon cast Windows' own small popup shadow (`ErrorTip` inherits an empty `QTipLabel`, no
`NoDropShadowWindowHint`; checked through the native window class, `GetClassLongPtrW(hwnd, GCL_STYLE) & 0x20000`, set
for both and not for a menu, in 3ds Max 2022 and 2027), plain tooltips have an `active_border` outline (checked in the
applied style sheet), and the collapsed bar matches the packager's (the bar's size hint plus 2 x 4 px, margins
2 / 1 / 1 / 1, a 14 x 22 grip, the name only with the version in its tooltip, the compact round close button smaller
than the title bar's). The shadow itself is drawn by Windows and does not appear in `widget.grab()` pictures; the
packager's screen grabs showed it. Then, from the owner's review of the running trainer: the second handle of a range slider got the
first one's edge on its hover ring (the painter's pen was not cleared; both rings are now checked to match); the
colour picker got the light shadow and a pipette that picks from frozen pictures of the screens (checked with a
neutral picture in place of the screens: a click brings its pixel back into the palette and the field, Esc keeps the
colour); count badges are edged in a more vivid shade of their own colour instead of a dark ring; the gallery and
lightbox of the MaxPkg Package Manager (`widgets.SlideView`, `Swipe`, `DragScroll`, `details.ScreenshotViewer`,
`manager_window.ScreenshotPreview`, same author) replace the simple gallery (checked: sliding with the keys, the
lightbox over the content, stepping, Esc and a throw down); the welcome window was redesigned (centred icon on a glow,
no hero plate or line); and dialogs now open centred over their window (they sat below the middle at 125 %). The
owner's further review added: count badges with a quiet darker edge of their own colour; status dots on the middle of
their label's capitals and icons on the vertical middle of their text in messages, toasts and welcome points (both
checked in pixels); a multi-select list picked by dragging over the rows, as MAXScript's multiListBox; the colour value
as HEX, RGB or HSV, colour harmonies and a pipette loupe that zooms with the wheel; a pick button for scene objects
(checked with a stand-in for Max's pick mode, which waits for a person); plain links and the rotating link of the
author's tools (MaxRewind's `PromotionLink`), with 3dground.net in place of example addresses; standing sliders; a size
grip on every resizable window; About's hero as a gradient that meets the header shade without a step. One mistake was
found by the owner, not by the checks: a close button painted on the veil could never be clicked, because a
window-modal dialog blocks every input to its owner window; it was removed and the veil now goes with its dialog by
any path. The owner also met a dialog that stayed invisible behind its veil: the harness, run in the same Max as the
owner's copy of the trainer, had hidden the owner's new windows and left its own modules loaded. It now hides only its
own windows and restores the owner's modules (checked: after a run the owner's copy still uses its own modules and its
window is not hidden). The trainer was also started on screen in 3ds Max 2027 through its launcher several
times; each start stopped the previous session and reached the start guard's "ready" step. The reference pictures in
`assets/` now come from the 3ds Max 2022 run. Native effects (Windows 11 corners, activation, system moves) remain
unchecked; no practical skill test or reviewer is recorded.

The owner then asked for the components still missing and for a design-system spacing: spinners (inline, in a busy
button, large), skeleton rows, a progress ring and wizard steps; dropdowns with icons, with groups, editable and with
check boxes; choice cards; a scene tree; a drop zone; stat tiles and simple charts (columns, lines, a donut) with
values under the pointer; context menus with keys at the right, arrow keys and a red Delete that takes the Delete
button's fill as the current row, and text fields' own menus in the same look; a calendar that steps out to the months
and to twelve years, with a time, Now and Done; a green outline on the copy button with its check; a list's empty
state that keeps the search field in place; and one spacing scale (0, 2, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48) with
`space(n)` refusing anything else, applied to every layout call and style sheet padding of the starter (about 200
values; the in-between ones such as 10, 14 and 18 moved to the nearest step by role). The chart colours are the
data-viz method's dark categorical palette in its fixed order, run through its colour-vision validator against every
theme's panel colour (adjacent pairs clear; on the 3ds Max theme's grey several sit below 3:1 contrast, so legends,
labels and tooltips carry the values). The checks grew to **206, passed in 3ds Max 2022 and 3ds Max 2027**: among
them the search field at the same pixel with no results, the menu's keys, the arrow keys skipping a disabled row and
the red fill in pixels, the copy button's green outline in pixels, every calendar view, the keys, Shift+Page, Esc
stepping back, a range greying out days, Done sending the date with the time, the time wrapping, the dropdowns'
icons, headings, the window-owned completer and the check box list staying open, choice cards with the arrow keys,
the tree's partial and full ticks, the drop zone's accept and refuse states, clean chart ticks and compact numbers,
the good / bad colour of a change either way, tooltips on a column, along a line and on a donut part, spinners that
stop when hidden, the busy button coming back, and a static read of every layout call and style sheet padding against
the scale. The runs found five faults that were fixed: a drop zone that stayed red after a refused drag (Qt sends no
leave to a widget that ignored the enter; it now accepts the enter without a drop action), the time steppers 4 px
short in the calendar (the popup now levels heights after its style sheet polish), the stat values reset by the
font check (they are now named and keep their own size), PySide2 refusing `list.append` as a slot, and the collapsed
bar's packager margins (2 / 1 / 1 / 1) moved by the scale (they are now marked as not spacing). One fault was in the
checks themselves: Max 2022 read the test script in the system code page, so a literal ellipsis in a check became
"â€¦" and the check passed against its own garbled text (the picture showed it); test scripts now write such
characters as escapes. The trainer was started on screen in 3ds Max 2027 after every change and reached "ready" each
time; the reference pictures were regenerated from the 3ds Max 2022 run (49 now).

A further round from the owner's testing: the wizard steps made the current step the loudest mark (it had been
quieter than the done ones); the tree's highlight no longer lights the indent (in Qt 6 only a highlight drawn by the
tree itself kept it out) and has no notch at the column seam; the Logs window opens without a lit field and its
records fade at the edges; segmented switches had become 2 px shorter than their segments after the spacing round
(their height now follows the one control height); every tooltip became the tool's own rounded Tip; the menus,
dialogs, calendar and colour picker switch Max's hotkeys off while they have the focus. The owner asked for narrow
Command Panel-style windows as the default and for an API in every tool: `api.py`, `max_api.py`, `api_entry.py` and
`MyToolAPI.ms` (describe, envelopes, checked parameters, dry runs, one undo record), and for the collapsed bars of
several tools to share one row at the active viewport's corner. What the runs taught: 3ds Max takes every widget's
ToolTip event at the application level (both versions) and, in a fresh session, an Esc sent to a widget without the
focus; a first attempt to round Qt's own tooltip window by a mask took 3ds Max 2022 down (access violation in
`QToolTip.showText`, named by the faulthandler dump), so the tool never touches that window; the update check's own
test cut `bootstrap.py` at its last `launch(` and broke on the new import-only guard. The owner's 3ds Max 2027 also
went down once while they clicked through the trainer before these fixes (a minidump, no Python trace; the faulthandler
log of that session was not written); what was clicked is not known. Final runs: **235 checks passed in 3ds Max
2022 and in 3ds Max 2027**. Earlier 2022 runs lost one or two popup checks each (a calendar view, the check box list),
different each time, while the owner was clicking in that same Max (a popup closes on any click outside it); the run
after the owner stopped was clean.
`MyToolAPI.call "describe"` was also sent through Max Ultra MCP's `max_execute` to the running trainer in 3ds Max
2027 and answered with the operations in JSON. Last, the owner made the reminder's way out an honour system: "I've already
donated, don't remind me" replaces "Don't remind me again" (checked by its text in the Support window). The
reference pictures in `assets/` now come from the clean 3ds Max 2027 run (51).

## Version 1.3.0

Two controls from the owner's other tools, approved there: the confetti burst of MaxPkg Packager's installer
(`ui/confetti.py`, `ResultCard.show_message(..., celebrate=True)`, the trainer's Celebration panel; prepared in this
repository by an earlier session and left uncommitted) and the Before / After compare slider of the MaxPkg Package
Manager (`gallery.CompareSlider`, adapted to plain QPixmaps or file paths, the theme roles `recessed`, `muted_text`
and `focus`, the interface size and the spacing scale; the trainer's Cards & Gallery section shows a clay and a
rendered version of one picture). The starter was regenerated from the template pages (45 code files identical),
compiled with Python 3.7.9 and 3.13.9, and run inside 3ds Max 2022 (PySide2 5.15.1) and 3ds Max 2027 (PySide6 6.8.3)
through Max Ultra MCP with the windows off screen, settings in a scratch folder and empty scenes, at 125 %: **35
release checks passed in each**. They cover the trainer starting with its eleven sections and none scrolling sideways;
the compare slider's size from Before (never enlarged, a wider one fitted), Before left and After right of the divider
in pixels, a press at 25 %, a drag to 75 % and a clamp at 100 %, the keys, the wheel left to the page, a badge hidden
while covered, a failed picture's label on the muted fill and the 16:9 place of a picture on its way (the Package
Manager's own unit tests, adapted); the confetti: no burst over a hidden window or in safe mode, none after a warning
even with `celebrate`, a burst from a celebrated success, a layer that is a `Qt.Tool` window of the tool's window
taking no clicks, keys or focus, its area around the window cut to the work area, 90 pieces in the theme's five
roles, pieces thrown far to the side going sooner, and the layer gone after 5 s; the API still answering (a scene
change only as a dry run); a clean stop. The 235-check harness of 1.2.0 lived in a scratch folder that was cleared
before this version and was not run again; the new release checks are kept with the maintainer's working files. The
reference pictures `compare-slider.png` and `confetti.png` come from the 3ds Max 2027 run. No practical skill test or
reviewer is recorded.

## TerraScoop (version 1.1.0 of this skill)

The window, controls, dialogs, interface size, Max reliability lessons and starter templates added in 1.1.0 come from
TerraScoop, a free Python + Qt tool for 3ds Max 2022-2027 by the same author (repository `maxpkg-dev/terra-scoop`):
release 1.3.7 at commit `9a64463` and the collapsed bar's following at commit `1b58c6b` (2026-10-28). The owner
authorized moving its UI and mechanics into this skill and publishing it on 2026-10-28.

| TerraScoop source | Carried into the skill as |
| --- | --- |
| `ui/main_window.py` title bar, edges, collapsed bar, `follow_host`, status bar | [tool-window template](templates/tool-window.md), [windows](window-chrome.md) |
| `ui/controls.py`, `ui/style.qss`, `ui/theme_manager.py`, `themes.py` | [controls](templates/controls.md), [themes-style](templates/themes-style.md), [controls catalog](controls-catalog.md) |
| `ui/dialogs.py` Settings, Logs, About; donate placement | [dialogs](templates/dialogs.md), [Settings, Logs, About and Donate](settings-about-logs-donate.md) |
| `ui_scale.py`, `qt_compat.measure_scale / scale_font / inherit_fonts` | [ui-scale](templates/ui-scale.md), [interface size](interface-size.md) |
| `startguard.py`, `gcprobe.py`, `controller.py` (GIL pump, GC hold), `workers.py`, `logs.py`, `bootstrap.py` | [startguard-gcprobe](templates/startguard-gcprobe.md), [controller-workers](templates/controller-workers.md), [logs](templates/logs.md), [launcher-bootstrap](templates/launcher-bootstrap.md) |
| `.agents/pitfalls.md` (failures in Max 2022-2027 and users' Max 2024 / 2026 reports) | [Max reliability](max-reliability.md), testing and MaxPkg lessons |

The starter was assembled from those modules with TerraScoop-specific parts removed (map, build card, promotion link,
domain settings), generalized names (`mytool`, `MyTool`, `tool` object names), the window and controller rewritten as
reusable bases, and three improvements found while assembling it: a corner mask where DWM rounding is unavailable,
`inherit_fonts` after polish in the main window and against each widget's class default font (lists kept 9 pt
otherwise), and thin pill scroll bars whose radius stays half the thumb after scaling. It was run as one project outside
Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3 (window, help
balloon, background job with progress, Settings, About, Logs, collapse and restore, stop), and the reference pictures in
`assets/` were taken from those runs (graphite and Max themes, 125 % interface size). The assembled starter was not run
inside Max during preparation; its parts were host-tested inside Max 2022 and 2027 as TerraScoop. No TerraScoop
domain code, icons, map data or brand assets are included.

Version 1.1.1 (2026-10-28) carries TerraScoop commit `119baa5`: `repolish` gives a widget its interface-size font back
after polishing it (TerraScoop's search field and Build button fell to 9 pt at 125 / 150 %), and `ComboBox.showPopup`
fixes its list's font before Qt measures it. The starter was regenerated from those modules (only `qt-compat` and
`controls` changed) and run again outside Max on both bindings with a font scan after a dropdown and two variant
changes: 0 widgets at a default size (the 1.1.0 starter left the repolished button at 8.25 / 9 pt). The same fix was
checked inside 3ds Max 2022 and 2027 as TerraScoop (every dialog, a dropdown and the search suggestions at 125 %).

## Max Ultra MCP (version 1.0)

Read-only source inspection on 2026-10-13 used the Max Ultra MCP checkout at commit `8c364294e1b5f9cb0aed778ba8aaac91f3015070` with a clean working tree. Paths below identify reference files. The inspected source credits Lukianenko Vasyl / 3DGROUND. Instructions and examples are a newly written synthesis; seven theme JSON files are byte-preserved snapshots included at the user's explicit request. See [palette provenance](palettes.md). No general product sublicense is asserted. A user does not need that checkout to follow this skill.

The source was being developed concurrently: follow-up reads saw HEAD `513662305ad8ea6758f721e85cdcc6b73858902f` and uncommitted UI/fixture changes. The About recipe reflects the inspected `AboutWindow` working-tree implementation, not a claim that it belongs to the initial commit or a released build. No changes were made to that checkout by this preparation. Palette hashes identify the exact included snapshot independently of later source changes.

| Reference file / symbol | Observed behavior | Reusable lesson / boundary |
| --- | --- | --- |
| `01_START_MAX_ULTRA_MCP_FIRST.ms` | Derives the adjacent bootstrap path, checks existence, calls `python.ExecuteFile` | Thin, location-independent normal entry point |
| `python/bootstrap.py` | Separate `sys.modules` session anchor, loading guard, Qt timer polling, timeout, exact package namespace eviction, explicit import spec | Dispose old resources before replacing code; bind imports to this launch location |
| `python/max_ultra/client.py`: `Client.__init__`, `initialize`, `close` | Initializes cleanup fields, cleans up on failure, owns a panel timer, unregisters named callbacks, disconnects shutdown signal, disposes helpers and windows | Central ownership and partial-start cleanup; actual cleanup coverage still needs host tests |
| `python/max_ultra/transport.py`: `Transport.stop`, `_run` | Stop event, socket shutdown, worker without UI/pymxs calls | Cancellation and plain-data handoff; TCP protocol and server discovery are not general tool requirements |
| `python/max_ultra/tasks.py`: `BackgroundTasks` | Bounded submission, caller-thread completion polling, future cancellation, `shutdown(wait=False)` | Useful I/O boundary; cancellation does not stop an already-running future, and nonwaiting shutdown is not proof of quiescence |
| `python/max_ultra/qt.py` | PySide6/PySide2 imports, Max parent, native accelerator helper or focus guard, guard release | Centralize compatibility and undo application-level hooks |
| `python/max_ultra/helpers.py`, `processes.py` | Managed helper jobs, cancellation files, timeouts, process ownership confinement | Ownership matters; Windows job objects are an optional advanced implementation, not a blanket kill policy |
| `python/max_ultra/themes.py` | Assets located from `__file__` | Package-relative immutable resources |
| `docs/UI_DESIGN.md` | Layout, DPI, focus, reusable controls, busy UI and test expectations | Adapt principles; do not impose product branding, exact breakpoints, or custom chrome |
| `python/max_ultra/widgets.py`: `ActionButton`, `copy_action`, `RoundedTextEdit`, `ThemedComboBox`, `PillProgressBar`, `LoadingOverlay`, `SettingsVeil`, `Window` | DPI-aware icon painting, restartable copy timer, native clipping, popup gap, progress, content loading and modal veils | Shared controls and explicit lifecycle ownership; generated tools need host validation |
| `python/max_ultra/themes.py`: `apply_all`, `html` | Deduplicates widgets, styles before HTML, explicitly calls QWidget repaint, transforms CSS rather than prose | Avoid item-view update overload errors and unintended source recoloring |
| `python/max_ultra/dialogs.py`: `ResponsiveSkillBrowser`, `SkillsMenu`, `SkillTableItem`, `SkillsWindow` | Defers reflow while rendering, rounds menus, compares stored date keys, shows sort indicator, fits rows | Regression coverage for reentrancy, context actions, typed sorting and compact rows |
| `python/max_ultra/community_dialog.py`: `MetadataBadge`, `MetadataRow`, `CommunityWindow` | Measured metadata sizing, row-direction adaptation, progress plus monotonic elapsed seconds | Plain data, independent layout decisions and truthful progress |
| `assets/themes/*.json` (seven palettes, excluding legacy `bindings.json`) | Named semantic colors, mixes, native colorMan fallback and light-mode overrides | Editable standalone palette references with exact bytes retained |
| Follow-up `python/max_ultra/dialogs.py`: `AboutWindow` | Final approved working-tree recipe: fixed vertical header/hero policies; 24/18 hero/body margins, spacing 12, body stretch, extra 36 footer spacer, 460 default width; larger DPI-aware icon, title/subtitle, accent separator and metadata/links/actions | Conditional About composition, generous aligned hero/body grid and compact chrome exception; numbers are reference tokens, not host-tested guarantees; product branding and destinations are not reusable defaults |
| `tests/qt-ui-fixture.py`, `qt-dialog-fixture.py`, `qt-theme-fixture.py`, `qt-copy-fixture.py`, `qt-progress-fixture.py`, `run-qt-fixtures.py` | Synthetic fixtures, temp settings, geometry/pixel assertions, screenshots, overload/reflow cases, runtime evidence | See testing reference; source runner's application-exit finalizer is deliberately excluded |

The reference bootstrap specifically waits on transport and active tick state; it is not proof that every helper/future has finished. The lifecycle contract here deliberately strengthens that boundary: track every owned worker and fail closed if it cannot quiesce. Likewise, aggregate cleanup errors and preserve retry handles instead of assuming each cleanup step succeeds. These are recommendations for generated tools, not claims about the reference implementation.

The theme transaction's apply-before-persist and rollback guidance is a proposed improvement; the inspected controller persists its selection before applying. The general typed-sort guidance goes beyond the reference's text/date comparator. Required theme selection and user opt-in to breakpoint scaling are this skill's user-specified policy, not claims that Autodesk requires them.

No shared QSpinBox/QDoubleSpinBox implementation was found in the inspected UI modules. Their recipe is a new design recommendation, with mandatory behavioral/visual tests and no claim of existing product or host validation.

The [MaxPkg delivery reference](maxpkg-delivery.md) was checked against the live official maxpkg-dev/max-dev-tool repository at commit `1281d283b30d885382c12804ca12da3f092d888b` on 2026-10-13: README, coding rules, adaptation prompt and automation API documentation were read from that same immutable revision. The installed Max Ultra MaxPkg Packaging skill supplied additional tooling/hook guidance. Local MZP delivery by default, retaining both hooks and preserving existing authorization are explicit user requirements for this skill. No generated-tool MZP was built or installed while updating this instruction package; only its community-skill ZIP was built.

The example lifecycle is conceptual guidance with a concrete synchronous implementation and an asynchronous extension contract. No example was run inside 3ds Max during preparation. Package validation, syntax checks, or mocked lifecycle tests do not demonstrate host integration or practical skill quality. No transport, server, installer, private paths, executable reference-product code, or icon assets are distributed in this package.
