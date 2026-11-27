# Observable regression checks

Run checks relevant to the generated tool, with pure/mocked and real-host results recorded separately. Use an authorized disposable scene for Max tests. This list is a test specification, not evidence that these checks have already passed.

| Scenario | Observable pass condition |
| --- | --- |
| Launch twice, rapidly, hidden, and after close | Exactly one active owner and intended main window; old timers/callback IDs/connections no longer fire |
| Relaunch during worker activity / active tick | New instance starts only after old work quiesces; old result cannot alter new UI or scene |
| Stop timeout or cleanup exception | No duplicate replacement; Max stays alive; retained owner enables later cleanup retry; diagnostic names the failure |
| Startup failure after each acquisition | Already-acquired resources released; unrelated Max callbacks/windows/processes remain intact |
| Theme selection with all dialogs open | Every owned window, popup, menu, painted control and rich text changes immediately; persisted ID restores on next launch |
| Shared controls reused in different dialogs | The same component fix affects each composition; named variants retain shared interaction/theme/DPI behavior without copied paint/style code |
| Compact status pills with large numbers | Short label retains meaningful numeric value/units and accessible full text; reflow avoids replacing all content with ellipsis |
| Edit a theme file and reselect it | Fresh values load without code edits; malformed file leaves the previous palette usable and picker consistent |
| Theme change with dropdown/QListView present | No `update()` overload exception; viewport and owning window repaint correctly in both binding families |
| Repeated resize while setting rich HTML and switching themes | One metadata block; no nested document duplication, infinite reflow, or source mutation; selected text and reading position remain useful |
| Right-click selected and unselected rows and document links | Menu opens on correct target; no document load, history change, busy overlay or network work until an explicit action requires it |
| Link rendering | Labels, HTML help, status and document links use the selected theme; displayed/copied example hex colors remain unchanged |
| Narrow/wide/narrow layout with long captions | No overlapping buttons, clipped close/cancel action or accumulating size constraints; help captions elide readably; icon-only controls retain accessible labels |
| Mixed action row at 200% and 250% or higher DPI | Icon-only and labeled buttons have matching height; original Lucide icons stay centered/crisp; text and group captions fit |
| Rounded field with both scrollbars visible | No square viewport corners, blue backing, native arrows or unthemed scroll-area corner |
| Dropdown at top/bottom/edge of each monitor | No square arrow button; distinct rounded popup; compact padding; 4px gap where space permits; popup stays within work area |
| Joined tabs, first/middle/last selection, scrolling and RTL | Continuous baseline outside selected face, no doubled native base/square backing, consistent page padding and keyboard focus |
| Requested About dialog in Qt5/PySide2 and Qt6/PySide6, short/tall/short and 200%+ DPI | Header/Close X and hero do not expand on vertical resize; body absorbs height; 24/18 hero/body insets, close subtitle grouping, full-width divider and combined 36px-plus-layout footer gap look intentional; metadata, links and actions stay usable |
| Integer/double spin controls at bounds, disabled/read-only, wheel and keyboard | Lucide arrows and themed transparent button areas, correct step enablement and values, no value change from the wheel, focused or not, clipped rounded outer surface at high DPI |
| Context menu states | Rounded boundary, aligned icon/text/shortcut, comfortable padding; danger action separated/red; disabled items do not look active |
| Keyboard interaction | Focus ring visible; Tab/Enter/Escape and dropdown navigation work; typing does not invoke Max accelerators; prior accelerator state restored on cleanup |
| Settings modality and opacity drag | Other tool windows veiled, Settings/child dialogs unobscured; preview veil hides during drag and restores on release/hide/cancel; unrelated Max windows unaffected |
| Progress unknown/known/zero/completed/cancelled | Correct mode and pill clipping; elapsed seconds reflect monotonic time; no fake progress; timers stop when hidden/idle/disposed |
| Loading overlay resize, failure and close | Spinner remains centered; content blocked but appropriate close/cancel available; busy state always clears; UI event loop responsive outside unavoidable host calls |
| Sort numerical/date/version/text columns both directions | Visible direction agrees with typed ordering; missing values deterministic; selected identity retained after repopulation |
| Status, selected and disabled states in every theme | Meaning readable beyond color; warning/error/success distinct; disabled actions neither clickable nor misleadingly hover-highlighted |
| Multi-monitor restore and optional native effects | Window remains reachable after monitor/DPI changes; unavailable shadows/rounding do not prevent startup |
| Title bar drag, double-click, edge resize | Moves; maximises and restores; dragging a maximised window restores it under the cursor; edges resize with the right cursor and never below the minimum |
| Rounded corners | Windows 11: DWM rounding and a theme-coloured border; elsewhere a rounded mask; maximised square; safe mode neither; startup never fails because of them |
| Collapse / restore ten times | Same place and size every time; bar 8 px inside the active viewport's bottom-left corner when never placed; a dragged bar comes back where it was put |
| Collapsed bar at screen edges and with taskbar changes | Never under the taskbar or off the monitors; confined again when a screen is added, removed or its work area changes |
| Max's window moved, maximised, sent to another display, minimised | Bar keeps its distance to Max's edges and follows; unplaced bar re-docks in the viewport corner after Max stops; a bar placed away from Max stays; after Max is minimised and restored the bar is where it was (no jump to -32000); no timer runs while Max stands still |
| Interface size on Full HD, 2K, 4K and with a Settings choice | Window, paddings, icons and fonts grow together (100 / 125 / 150 %); labels, checkboxes, fields and lists have the same font size; scroll thumbs stay pills at 100 / 125 / 150 / 200 % |
| Re-polish and dropdowns at 125 / 150 % | After a dropdown opens, a field's state property changes and a button's variant changes twice (each through `repolish`), no visible widget is at the application's or its class's default font size |
| Theme change at 125 / 150 % | Every field, list, label and button keeps the window's font size after switching the theme twice; open menus and About also match |
| One control height | Every field, dropdown, button, stepper and the date field in a window and its dialogs is 30 px (scaled); icon-only buttons are squares |
| Required fields and the error bubble | A required field has a red `*`; an invalid one a red outline; Enter alone (a dropdown closing over it) shows no bubble; a 3 px move of a faked pointer shows it above the field; Leave hides it; fixing the value removes outline and bubble |
| Mini log | Shows only current errors and warnings, or one green line; rebuilt on every check, never a growing history; a row with a target is clickable and opens its tab and group |
| Disabled coloured buttons | A disabled primary or danger button keeps a shade of its colour (never grey) in every theme |
| Collapsible groups | An optional group starts closed, opens when it holds data; a closed group's title is vertically centred; hover changes only the colour |
| Outlines of masked popups | Help balloon, error bubble, menu and calendar rendered through their own mask: the outermost pixel inside the mask is the border colour on the left and right of every row, at the top and bottom of the middle columns and down both sides of an arrow to its point |
| Self-update | From `file:///` releases made by `tools/release.py`: Check Now installs the newer version into the profile, `current.json` names it, the pill and toast appear; the launcher starts the newest copy; a failed start rolls back to the previous version or to the copy next to the launcher; a wrong checksum installs nothing; no Updates group without an `UPDATE_URL` |
| Checks while typing | Typing `dsf` in a URL field marks it at once (outline, bubble after a move, mini log row); `site.com` is no error while typing and becomes `https://site.com` when the field is left; clearing an optional field removes the error; a click on the row opens the closed group and focuses the field |
| Wheel over fields | A wheel turn over a dropdown (focused and not) and over a stepper leaves the value unchanged and scrolls the page; the open calendar still turns its month |
| Every window's chrome | Settings, About, Logs and questions are frameless with the tool's title bar, round close button and header shade; dragging the title bar moves them; Logs has a size grip; no QMessageBox is created anywhere |
| View Logs | First item on the left of the status bar; 12 px muted icon; own height; opens the modeless Logs window; no Logs button on the right |
| Toasts | Below the header at the right, stacked; an open key shows the same toast again instead of a second; the time waits under the pointer; a click closes it; none over the collapsed bar |
| Questions | Neutral button is the default; the destructive action is red; Esc keeps things as they are |
| Logs window | Not modal; days listed newest first (Today, Yesterday, dates); filter, search and summary agree; whole records selected; Copy / Export carry the selected records; Clear Logs asks, deletes every day and shows the empty state |
| Start after a crash at each start step | Report with the step, versions and crash-log tail in the Listener; safe mode and status line; a new version starts normally |
| Start after a crash marked "Garbage-collecting" and on PySide2 + Python 3.10 | Collector disabled while the tool runs; frozen and enabled on close; `gcprobe.run()` reports through the next start |
| Screen wrapper or style wrapper dead | Start succeeds with the screen lookup fallbacks and `repolish`; no `widget.screen()` call anywhere |
| Background job inside Max | Progress advances while Max is idle (GIL pump running only during jobs); cancel and close during the job ask first and stop it |
| Donate destination empty / set | No Donate button and no offer anywhere / Donate last in the status bar and left in About, both opening the Support window; the browser opens only from its Donate |
| Donation rules | Reminder on the 5th start and then every 30 (never in safe mode, during work or over another window); "I've already donated, don't remind me" and the Settings switch stop it; the result card's line from the 2nd success, once a session, never after a failure |
| Bubble shadows | The error bubble and the help balloon have no `NoDropShadowWindowHint`, `ErrorTip` inherits `QTipLabel` and is a `Qt.ToolTip`; on screen a soft shadow right and below follows the mask and the arrow, also during the fade; menus and dropdown lists stay without it |
| Colour formats | HEX, RGB and HSV show the same colour and follow each other, the square and the strip; the chosen format is remembered; fields, steppers, the switch and the pipette are one height after the first show |
| Confetti | `celebrate=True` on a success bursts from the card's round icon a moment after it shows; a warning or error never does. The layer is a `Qt.Tool` window of the tool's window with `WindowTransparentForInput`, `WA_TransparentForMouseEvents` and `WA_ShowWithoutActivating`: never active, never takes focus or clicks; its area is 0.55 of the window's width on each side, 0.45 of its height above and 110 px below, cut to the work area; 90 pieces in the theme's five roles, sized by the interface size; pieces thrown far to the side go sooner; it is deleted after 5 s. Safe mode, a hidden or minimized window: no burst |
| The veil | It goes with its dialog by every path (reject, hide, deleteLater); nothing is drawn on it to click |
| Harness isolation | A run inside the Max where the user runs the tool hides only its own windows and gives the user's copy its modules back; no window of the user's copy is hidden or replaced |
| Pick button | The picked name and handle stand on the button, the x clears it; the real pick mode never runs in an automated test |
| Links | A plain link opens its page or window; the rotating link shows one of the owner's messages, rotates without repeating, and stops while hidden |
| Standing sliders | The top of the track is the largest value; a standing range keeps its handles in order |
| Size grips | The main window and resizable dialogs show a grip in the bottom-right corner, never on the collapsed bar or a maximised window |
| Colour harmony | The harmony swatches follow the colour (a triad of red is red, green, blue); the format labels are never clipped; the wheel zooms the pipette's loupe |
| Colour picker | The card casts the light system shadow; the pipette freezes the screens with a loupe, a click brings the pixel's colour into the palette and the field, Esc keeps the colour and reopens the palette; Max's hotkeys stay off while picking |
| Count badges | The edge has the badge's hue and is darker than its fill (a quiet burgundy on red), never black or white |
| Multi-select list | Press and drag selects the run of rows under the pointer; Ctrl, Shift and Ctrl+A work; the order never changes; the footer counts the selection |
| Icons beside text | A message's, a toast's and a welcome point's icon is within 2 px of the vertical middle of its title and text; a status dot within 1 px of its label's capitals |
| Range slider | Each handle gets the same soft ring under the pointer |
| Before / After | The Before picture sets the size and is never enlarged; a wider one fits the width and keeps its shape; Before shows left of the divider and After right of it (in pixels); a press at 25 %, a drag to 75 % and past the edge (clamped at 100 %); Left / Right step 5 %, Home / End go to the edges; the wheel is not taken; a badge hides while the divider covers it; a failed picture shows its label on the muted fill; a picture on its way keeps a 16:9 place |
| Gallery and lightbox | Arrows and drags step with the slide; the counter, title and current thumbnail follow; the lightbox covers the content below the title bar, steps with the arrows, closes with Esc, a click beside and a throw up or down |
| Dialog placement | Every tool dialog opens centred over its window at 100 % and at 125 % or more |
| Welcome window | The icon centred on its glow without a cut edge, the name centred below; no hero plate and no accent line |
| Plain tooltips | The outline (`active_border`) is visible on all four sides over the darkest panel of every theme |
| Collapsed bar | The same window becomes the bar (nothing created or destroyed): size hint plus 2 x 4 px, margins 2 / 1 / 1 / 1, grip 14 x 22, brand icon 14, the name only (version in the tooltip), the 22 px round close button red on hover; a click on the name opens the window again at its exact geometry |
| A dialog's bottom row | Every footer button one height and one width (at least 92 px): About's Close equals Donate, Support's Not now equals Donate |
| Settings styles | Up to three sections as tabs with Close; four or more as a list on the left with icons, Reset in red, pages that scroll with soft edges |
| Search with suggestions | The window owns the completer (`owner`); the window shows, filters, closes and reopens with no native crash in each Max; the suggestions are rounded and themed |
| Scrolling edges | At the top only the bottom edge fades; in the middle both; at the end only the top |
| Section names with `&` | "Cards & Gallery" shows the `&` (`Button.setText` doubles it) |
| Filter pills | One chosen pill keeps its colour and glows, the rest turn neutral; an empty category shows its empty state; All brings every card back |
| Spacing scale | Every layout margin and gap goes through `space(n)` (except lines marked `# Not spacing:`); every style sheet padding and margin is on the scale; `space(10)` raises |
| Empty state in place | Typing a search that matches nothing leaves the search field at the same pixel; the empty state is as tall as the list it replaces |
| Menus | Rows show their keys; the arrow keys skip a disabled row; the current Delete row has the red Delete fill and another current row the `selected` fill (checked in pixels); a text field's own menu is frameless and rounded |
| Copy button | After a click the check and the outline are green (`done` property, checked in pixels) and both go back |
| Calendar | The title steps out to the months and to twelve years; the arrows page by the view; a year opens its months and a month its days; the keys move the day, Shift+Page a year, Esc steps back a view; days outside a range are grey and the keys stay inside it |
| Date and time | A click on a day only selects it; Done sends a `QDateTime` with the time; the time wraps (23:59 + 1 minute) and keeps two digits; the steppers and buttons in the popup are one height |
| Dropdowns | Every icon item has its icon; group headings cannot be chosen; the editable dropdown's completer belongs to the window; the check box dropdown keeps its list open on a tick and sums up as "Geometry, Materials", "3 selected", "All", "None" |
| Choice cards | The arrow keys move the chosen card; exactly one card is checked |
| Scene tree | A partly ticked layer shows a dash; ticking a layer ticks its objects; every row has its kind's icon |
| Drop zone | Only the allowed kinds are taken; dragging allowed files shows the accent state, other files the red state, and leaving puts it back |
| Charts | Clean ticks (0 / 200K / 400K / 600K), numbers in full under 10,000 and compact above, the palette's order, a change green when it is good either way, columns at most 24 px, tooltips with the exact value on a column, along a line (every series) and on a donut part; leaving clears the hover |
| API | `describe` lists every operation with parameters; unknown operations, missing, unknown or wrong parameters return clear error codes; `scene_summary` reads; `add_prefix` only with `dry_run` in checks; JSON in and out; `MyToolAPI.call` through MAXScript gives the same answer (and the owner's `MyToolAPI` is put back); `api_entry.py` loads without a window session; the window's panel calls the same API |
| Collapsed bars in a row | An unplaced bar sits at the active viewport's corner and is watched while collapsed; a bar collapsed later lines up after another tool's bar; the row closes the gap when a bar leaves; a dragged bar keeps its place; a double-click on the grip puts it back; an open window leaves the row and stops the check |
| Tooltips | A widget's tooltip text sits in `toolTipText` and Qt's is empty; Enter starts the delay; the Tip is rounded by its mask, outlined in `active_border`, has the light tooltip shadow and goes on Leave; a chart's value uses the same Tip; Qt's square tooltip never shows |
| One control height in rows | The Logs toolbar (day, levels, filter), the colour picker's format switch with its segments and pipette, and every segmented switch are one height (30 px at 100 %); a switch is never shorter than its segments |
| Logs window | It opens with no field lit up; its records fade at a clipped top and bottom |
| Tree selection in Qt 6 | The row's highlight leaves the indent unlit and runs across the column seam without a notch, in PySide2 and PySide6 |
| Loading | A visible spinner turns and a hidden one stops; a busy button shows a spinner, says what runs, refuses clicks and comes back as it was; the ring names its share; steps stop at the last |

Report exact Max build, Python, Qt/PySide versions, OS/DPI, scenarios exercised, observed result, and remaining failures. Screenshot evidence helps visual checks; resource counts or callbacks observed over multiple cycles help lifecycle checks. Standalone Qt fixtures cannot establish host ownership, Max focus, or scene safety. No design system can guarantee perfect rendering in every host and display configuration.
