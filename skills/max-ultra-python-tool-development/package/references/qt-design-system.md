# Shared Qt design system

Use this contract for tools created with this skill. Theme selection, Warm Graphite as the default, consistent control states, and the interaction rules below are **the requested design standard**, not universal Autodesk requirements. Exact breakpoints, optional opacity controls, and product-specific panels remain implementation choices; the window chrome, controls and dialogs follow the pages linked below. Do not add promotions, networking, or a skill browser to an unrelated tool.

Contents: theme pipeline; control states; the house rules; icons and sizing; responsive layout; loading and modality; host ownership. See [implementation recipes](qt-recipes.md) for a starter theme and code patterns, and [regression checks](regression-checks.md) for observable tests.

The concrete, proven look and behaviour of the standard window, every control, Settings / Logs / About / Donate and the interface size are in [windows](window-chrome.md), [controls catalog](controls-catalog.md), [Settings, Logs, About and Donate](settings-about-logs-donate.md) and [interface size](interface-size.md); the code is in the [starter templates](starter-templates.md). Where this general page and those pages differ, follow those pages.

## One theme pipeline for every window

Every tool must expose theme selection, inside Settings when Settings exists. If there is no Settings window, expose an Appearance control/menu on the tool. Ship Warm Graphite (`graphite`) as the default and at least one useful alternate theme. Start with the [bundled verified palette files](palettes.md), which work without the original checkout. Each palette is a separate editable `assets/themes/<id>.json` file in the generated tool. Colors belong in those files, geometry and spacing in shared UI code. Read the file again when selected; do not cache palettes indefinitely.

One theme manager loads, validates, resolves, and publishes a complete palette. Required roles:

| Family | Roles and behavior |
| --- | --- |
| Surfaces | `window`, `surface`, `field`, `recessed`, `popup`; popup must be distinct from the field |
| Text | `text`, `muted_text`, `selected_text`, `disabled_text`, `link`, `link_hover` |
| Interaction | `accent`, `hover`, `pressed`, `selected`, `focus`, `border`, `disabled_surface`, `disabled_border` |
| Meaning | `success`, `warning`, `danger`, `danger_hover`, `danger_pressed`, `danger_text`; distinguish pending from failed |
| Scrollbars | `scroll_track`, `scroll_thumb`, `scroll_hover`, `scroll_pressed` |

Aliases are acceptable if explicit and consistently resolved. The reference uses more specific names (for example `window_background`, `selection_background`, `focus_border`, `log_error`, `delete_background`); do not scatter literal hex values throughout widgets. For new tools, prefer semantic tokens directly to the reference's legacy literal-color substitution map. Include visible status text or icons as well as color.

Validate required keys, value types, color syntax and any alias/mix cycles before changing active state. On a bad palette, preserve the previous working theme and picker value, and show the error. Persist only a successfully applied selection to a user settings file, never the asset file. Restore it on launch; fall back to Warm Graphite with a diagnostic when the saved choice is missing or invalid. A settings-write error must be reported as an unsaved preference, not silently called success.

Keep canonical unthemed QSS and rich-text sources separate from rendered output. Register every tool-owned top-level window, popup, dialog, overlay and rich-content widget; newly opened windows inherit the current palette. On selection, apply styles to deduplicated live widgets first, then rerender rich content from canonical source. Preserve selection, scroll anchor, focus and active document. Do not recolor unrelated Max windows or globally replace code/prose containing hex colors.

Use one `link`/`link_hover` scheme in labels, help browsers, status HTML, tooltips where supported, and context menus. Apply it explicitly in generated HTML CSS; avoid platform-blue defaults or inherited paragraph colors overriding anchors. Escape user text, validate link destinations, and keep embedded document resource loading explicit rather than allowing unintended file/network fetches. This is especially relevant when a tool displays imported content.

## Shared controls and states

Implement each shared control once: buttons, status pills/badges, fields, dropdowns, spin controls, tabs, menus, progress bars, loading/Settings overlays, and requested About composition. Dialogs import or compose those implementations; they do not copy their paint events, QSS or interaction handlers. Use semantic variants (primary, secondary, danger, success, warning) and shared color/size/spacing tokens. A shared stylesheet alone does not justify duplicated behavior/painting. Prohibit drifting per-dialog overrides; put intentional exceptions in named documented variants such as About spacing. A control fix must propagate to every window. One small shared module is sufficient for small tools; do not introduce an unnecessary library/framework. Cover enabled, disabled, hover, pressed, selected, focused and busy states, including keyboard interaction.

Use one shared spacing/radius scale, for example spacing units `4, 8, 12, 16, 24` logical pixels and radii `3, 4, 6, 8`. Give it semantic names: window inset, content inset, group inset, row gap, section gap, field radius, panel radius. Headers and content align to the same inset grid. Full-bleed hero backgrounds/dividers are explicit exceptions whose inner text still follows that grid. If responsive adaptation is chosen, select a complete density token set at each breakpoint rather than inventing per-control offsets. Otherwise keep the spacing scale stable. Values are starter design tokens, not copied product constants; verify against font metrics and hit targets.

- **Actions:** one height for every single-line control (30 px, `controls.unify_heights`), moderate rounded corners, clear focus outline, disabled contrast without an active hover treatment; a disabled primary or danger button keeps a darker shade of its own colour, never grey. Enabled clickable controls use a pointing-hand cursor; update it when enabled state changes. Editable text retains its text cursor. Use Title Case captions while keeping short connecting words such as `to`, `and`, `a`, `the` lowercase and preserving acronyms.
- **Status pills/badges:** use one measured capsule component with semantic status variants and shared insets/radius/type. Paint the rounded surface once and size from font metrics; do not make separate badge implementations for every dialog. In compact mode shorten the label while retaining meaningful numeric values (for example `Objects 1,234` to `Obj 1,234`), units where needed, and full accessible text/tooltips. Do not replace the entire value with an ellipsis. If it still cannot fit, wrap/reflow the row or provide usable scrolling rather than hiding the number. Decorative status badges use the normal cursor; only actionable pills get a pointing hand.
- **Copy:** share one helper. Copy the current value, display `Copied` and the Lucide check icon, then restore the original caption/icon after 2000 ms. Repeated copies restart one widget-owned timer. Restore accessible text too; destruction/restart cancels feedback.
- **Switches and checkboxes:** every on / off setting is a switch (`ui/switch.py`: rounded track, sliding knob, accent when on), in Settings and everywhere else. Checkboxes remain for picking items of a list or a partly selected group: one rounded indicator style with a visible check glyph, accent checked state, hover border, keyboard focus, and explicit disabled checked/unchecked states; handle partial state if tri-state is used. The reference Settings style is evidence, but its donate-specific color names are not a general dependency.
- **Groups and tabs:** subtle rounded groups with adequate title/content spacing. Joined tabs use a continuous active-color baseline across the heading except beneath the selected tab's face, which joins the content pane. Disable the native extra base, remove square backings, and give pages consistent padding. Keep tab selection, focus, surface, and adjoining pane consistent. Do not use a group border that cuts through its caption at high DPI. See the concrete tab recipe.
- **Fields and text areas:** rounded frames and coherent text/selection colors. A QSS border radius alone does not guarantee clipping of a native viewport. Mask/clip the actual owning surface or viewport on resize; clear square auto-filled backgrounds and verify both scrollbars and corners. Apply the shared treatment to plain text, rich text, search and log views as appropriate.
- **Dropdowns:** reserve trailing space and draw the original Lucide `chevron-down` vector in the current text/disabled color. Remove the native arrow and make the drop-down subcontrol borderless and transparent, eliminating its square button. Use a themed `QListView` popup with compact padding, rounded outer clipping, distinct popup background and selected/hover text contrast. Place it 4 logical pixels below the field, or above when space requires; clamp to the screen work area; round the popup window with a mask (`controls.round_popup`). The wheel never changes the value, focused or not; it scrolls the page. Preserve native keyboard selection and accessibility. A category value that is also shown as a badge uses the badge dropdown (`forms.BadgeComboBox`), sized to its content.
- **Spin/composite controls:** use the stepper (`pickers.Stepper`): one rounded field with small Lucide up/down chevrons stacked inside its right edge, step bounds, the arrows and the Up / Down keys; the wheel never steps it. A version is three steppers captioned Major / Minor / Patch. Dates use the date field and its themed calendar (`pickers.DateField`), never a native `QDateEdit` popup.
- **Context menus:** `controls.Menu`: rounded outer mask, comfortable item padding, theme hover/selection highlight, a Lucide icon on every item, the window's interface-size font. Separate destructive actions with a separator and show them in danger red; disabled actions use disabled roles. A right-click menu must operate on the intended target without invoking selection-driven document loading or refresh. Keyboard context menus use the current selection/cursor location.
- **Scrollbars:** thin (10 px bar), no visible track, a pill thumb (6 px, radius exactly half of it) in `scroll_thumb` with hover and pressed colours, minimum length 28 px. Keep the radius at half the thumb after scaling, or Qt draws it square (see [controls catalog](controls-catalog.md)). Clear native arrows, add/sub-line and add/sub-page backgrounds; make scroll-area backing containers and the corner transparent to remove blue/square native backing. Apply both axes and popup scrollbars.
- **Tables:** enable sorting only where meaningful and show a visible direction indicator. Use numerical values for counts/sizes, timestamps for dates, semantic version tuples for version ordering, and case-folded text for names. Retain display formatting separately in item data/model roles. Define missing-value ordering and a stable tie-breaker. Preserve selected records by identity across sort/reload. Disable sorting while batch populating and restore the previous column/direction afterward. Style selected, disabled, focus, header and empty states.
- **About:** part of every tool (status bar button); the composition in [Settings, Logs, About and Donate](settings-about-logs-donate.md) is the standard. In general terms: use a fixed-height title bar with Close X, a contrasting themed hero with larger script icon and closely grouped name/subtitle, a full-width accent divider, description/Version/Developer/Project and accent-colored website links. Hero/body use generous About-specific insets (reference 24px horizontal, 18px vertical, spacing 12); an optional How to use card with numbered steps; Donate/Close in a footer outside the scrolling body, always in view. Keep added height in the body, not header/hero; start at reference width 460 and adapt to content/DPI. See the full recipe and two-binding visual checks. Do not add About without a request or copy another product's branding/destination.

## House rules

These rules were set by the owner while building MaxPkg Packager 2.0 and apply to every tool made with this skill:

- **Consistent and rounded.** Every control has rounded corners and the same 30 px height in a row; a button is never
  taller than the field beside it. No grey on coloured controls: a coloured button, pill or badge keeps its colour
  (a darker shade when disabled).
- **One spacing scale.** Margins, gaps and paddings are steps of 0, 2, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48 px
  (`ui_scale.space(n)` refuses anything else); see the rule in the [controls catalog](controls-catalog.md).
- **Narrow by default, like the Command Panel.** A tool's main window is one column about as wide as 3ds Max's
  Command Panel (300-360 px at 100 %): panels stacked, rare options in closed groups, the primary action at the
  bottom, so it covers as little of the viewports as possible. Autodesk builds its own tools as Command Panel
  rollouts for this reason. Go wider only when the content needs the width (a table with several columns, a gallery,
  logs, a node view, a side-by-side comparison), and even then open at the smallest size that shows it and let the
  user widen it. The controls trainer is wide because it is a gallery of every control, not a model for a tool's
  window.
- **Compact windows, never resized by the tool.** Small insets (panels 12 / 6 / 12 / 8), a compact collapsed bar.
  Only the user resizes a window; showing or hiding a part takes room from the page, which scrolls if it must. A
  one-time fit when a window first opens is allowed.
- **Header shade.** The main window's title bar (and tab row) sit on a dark gradient (black at 0.7 alpha to
  transparent) that ends where the first panel starts (`ToolWindow.HEADER_SHADE`, `header_bottom`).
- **Required means marked.** Every field the validation requires has a red `*` after its name; a panel whose content
  is required has one after its title. An invalid field gets a red outline and the red error bubble, which appears
  only after the pointer really moves on the field (Qt sends Enter when a dropdown above it closes).
- **Help is scanned, not read.** "?" balloons: a title, a thin line, then short blocks; one idea per block, few
  words, a bold term at the start, `code` chips for names and characters.
- **An outlined popup is outlined on every side, the arrow included.** Masked popups (help balloon, error bubble,
  anything with an arrow) stroke their outline along the inside of the mask's own path (`controls.paint_bubble`).
- **Light shadows under bubbles.** The error bubble and the help balloon cast Windows' own small popup shadow along
  their mask, arrow included: soft, a few pixels right and below, never a painted or translucent shadow. Plain
  tooltips have an outline in `active_border` that shows on every side.
- **Scrolling never changes a field.** The mouse wheel over a dropdown or a stepper scrolls the page, focused or
  not; values change only through the open list, the arrows or the keyboard. An open popup (the calendar) may use the
  wheel for itself.
- **Check while typing.** Fields with a format (web address, e-mail, path, number range) are validated on every edit
  and show their error at once (outline, bubble, mini log); what can be completed for the user is completed when the
  field is left (`https://`). A jump from the mini log opens a closed group to show its field.
- **Optional groups are closed** until they hold data (`forms.Collapsible`); their titles look like panel titles.
- **The mini log shows statuses, not history.** Errors and warnings, or one green line; the Logs window keeps the
  history (one file per day, not modal, whole-record selection, Clear Logs with confirmation).
- **One chrome for every window.** Settings, About, Logs, questions, small edit windows and an installer window use
  the main window's own title bar, round close button, header shade and rounded corners; no native Windows title bar
  anywhere, no `QMessageBox` (questions: `dialogs.ask`). Dialog buttons stay at the bottom, outside any scroll area.
- **View Logs** is the status bar's first item on the left, a muted text action with the 12 px Lucide `logs` icon, as
  in MaxPkg Runtime Manager; it opens the modeless Logs window.
- **Toasts for outcomes, questions before destruction.** A toast (MaxPkg Runtime Manager's style: animated status
  icon, time bar, optional action) tells the result of an action; `dialogs.ask` comes before anything that cannot be
  undone; neither replaces the mini log or the field's error bubble.
- **Lucide icons only**; round title-bar buttons, the close button red on hover; no dotted focus frame on buttons.
- **Every message is ours.** Questions, information, warnings, errors, one-line prompts, the welcome window and the
  donation request are tool windows (`ask`, `inform`, `ask_text`, `WelcomeDialog`, `SupportDialog`); never a
  `QMessageBox`, `QInputDialog`, `QErrorMessage` or `QProgressDialog`. Only the system's file and folder pickers stay
  native.
- **A dialog's bottom row is one size.** Its buttons share one width (the widest, at least 92 px) and one height
  (`controls.same_width`): Close is never smaller than the Donate beside it.
- **Settings in sections.** Tabs on top for up to three sections; a list on the left with icons from four, the chosen
  section highlighted and a destructive section (Reset) in red, as in the MaxPkg Package Manager (`SectionBook`). The
  same list holds a main window with many sections.
- **Soft edges.** A scrolling page or list fades into its background where its content is cut (`EdgeFade`), as in the
  MaxPkg Package Manager.
- **Aligned by the eye.** An icon beside a short text block sits on the block's vertical middle; a status dot on the
  middle of its label's capitals; checked in pixels, not assumed.
- **Ends are shown.** The end of the main operation is a result card in the middle that closes by itself; work that
  blocks the area runs under the busy overlay with Cancel; an empty list says why and offers one action.
- **Donations, politely.** Only where the owner wants them ([donations](donations.md)); one click closes an offer and
  nothing comes back in the same session.
- **Use with judgment.** The catalog is a toolbox: pick the control that fits each need ([choosing
  controls](controls-catalog.md#choosing-controls)) and leave out what the task does not need. A red star only where the
  validation requires a value, a "?" only where the labels are not enough, groups only for rare options, tabs only for
  several large pages, a mini log only when there is validation or a build.
- **Tests never move the user's mouse** (`QCursor.setPos`) or send keys to the user's windows; give the code a fake
  pointer position instead (`ErrorHints.cursor_pos`).

## Icons, typography, and responsive layout

Use original Lucide SVG geometry exclusively for button icons unless the user requests another icon set, with its license in the generated tool's distribution. Do not substitute emoji, font symbols, or approximated paths. Brand logos, if actually required, remain separate assets with their own rights. Tint action vectors using the active/disabled text roles. Rasterize at `logical_size * devicePixelRatioF()`, then set the pixmap device pixel ratio; avoid repeatedly scaling an already small bitmap. The reference copies a `QIcon` before clearing a borrowed style-option icon under PySide2.

The interface size for 2K / 4K screens (one factor per session from the screen and Windows / Max scaling, [interface size](interface-size.md)) is part of DPI correctness inside Max, which turns Qt's own scaling off; it is on by default and needs no question. First ask whether the user wants responsive breakpoint adaptation unless an explicit choice already exists. Explain that narrow windows reduce text/control sizes and may show icon-only actions, while wider windows enlarge fonts, controls and icons. If declined or unanswered, retain stable typography/control sizes and use ordinary layout reflow, scrolling and minimum sizes to fit. DPI-aware rendering is required either way. The tiered scaling and compact icon-only recipes below apply only after opt-in.

Use layouts and the actual row's available width, including margins, stretch items, icon widths, font metrics and spacing. Reset previous compact constraints before computing a new fit. In the opted-in compact mode, collapse lower-priority actions to icon-only when needed; retain tooltips and accessible names. Keep help captions readable with `fontMetrics().elidedText`, full-text tooltips and a sensible minimum; reflow into rows/columns or scroll if controls still cannot fit. Do not let button rectangles overlap or clip destructive labels ambiguously.

Use common control-height tokens. An icon-only button may need as much height as a labeled button because point fonts scale independently of logical icon pixels; use style metrics and font height in `sizeHint()`. Coordinate typography, margins, spacing, icon size and scrollbar density, and restore every property when growing after shrinking. Avoid cumulative scaling or blindly inheriting the main panel's breakpoints in auxiliary dialogs. Keep minimum UI text readable rather than shrinking indefinitely to fit.

The reference main panel currently uses `<350` logical pixels for its smallest tier, with 24-pixel actions, 14-pixel icons and 7-pixel scrollbars, and larger tiers above 1250 and at 1800. These are observations, not universal defaults; fit the actual tool's content. Validate 100%, 200%, and greater-than-200% display scaling and mixed-DPI monitor transitions. Keep all Qt layout geometry logical; multiply only raster/native coordinate operations that actually require physical pixels.

## Progress, loading, and Settings modality

For long operations, use a pill progress bar with a clipped rounded fill. Known work uses real progress values; unknown work uses an indeterminate animation, never invented percentages. Show elapsed seconds from `time.monotonic()` next to it. Stop animation and elapsed timers when no longer needed; restarting an operation resets elapsed time. At low fill values, keep the fill inside the rounded track. Report completion/failure/cancellation in text.

A Skills-style loading overlay is a child over the content area: translucent recessed surface, centered faint circular track and accent arc, updated by an owned Qt timer (the reference uses 40 ms). Leave title/close/cancel controls usable as appropriate, disable underlying interactions, resize the overlay with its parent, and stop animation while hidden. Clear busy state on every completion and error path. Neither sleep nor nested event loops make loading nonblocking; long Max calls still block the UI, so chunk supported work or explain that limit.

Settings is modal, parented to the tool/Max ownership chain and shown above the tool's other windows. Dim other **tool-owned** windows with full-window translucent child veils, not by reducing their opacity. Veils track resizing and newly shown owned windows; Settings and dialogs it opens must remain visible and interactive. Keep this modality controller separate from content-loading overlays.

If an opacity slider is included, apply the chosen base opacity to the target window. On slider press, temporarily hide that target's Settings veil so the user can preview it; on release restore the veil and persist the value. Restore on hide, close, cancellation, loss of the drag, and errors too. Keyboard changes should persist without leaving a stale preview state. Do not change opacity on unrelated Max windows.

## Window integration

Parent to Max, keep strong lifecycle ownership, and avoid global always-on-top flags. The Logs window is the one modeless tool dialog (watched while working); Settings, About and questions are modal. Every tool window, dialogs included, has the main window's frameless chrome ([windows](window-chrome.md#dialogs)); no native title bars. Preserve focus while updating status, themes, or documents. Use available monitor geometry (excluding taskbars) to restore and constrain window positions; handle disconnected monitors and windows larger than a work area. The standard main window is frameless with its own title bar, edge resizing and a collapsed bar ([windows](window-chrome.md)); it must retain close, drag, resize and modal stacking. Dialogs keep the native frame.

Round the main window's corners: Windows 11 DWM (corner preference and a border tinted with the theme's border colour), and a rounded window mask where DWM refuses. Gate native code by platform and capability, use correct native handle types, and fail gracefully without preventing the tool opening. Do not promise identical corners on all Windows/Qt/remote-session combinations. Cleanup must remove global focus hooks, event filters, timers, veils, popups, window registries and deferred theme/reflow work as described in [lifecycle](lifecycle.md).
