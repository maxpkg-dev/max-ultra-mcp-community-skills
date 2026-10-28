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
| Integer/double spin controls at bounds, disabled/read-only, wheel and keyboard | Lucide arrows and themed transparent button areas, correct step enablement and values, no accidental unfocused wheel changes, clipped rounded outer surface at high DPI |
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
| Start after a crash at each start step | Report with the step, versions and crash-log tail in the Listener; safe mode and status line; a new version starts normally |
| Start after a crash marked "Garbage-collecting" and on PySide2 + Python 3.10 | Collector disabled while the tool runs; frozen and enabled on close; `gcprobe.run()` reports through the next start |
| Screen wrapper or style wrapper dead | Start succeeds with the screen lookup fallbacks and `repolish`; no `widget.screen()` call anywhere |
| Background job inside Max | Progress advances while Max is idle (GIL pump running only during jobs); cancel and close during the job ask first and stop it |
| Donate destination empty / set | No Donate button anywhere / last in the status bar and left in About, opening the browser only on click |

Report exact Max build, Python, Qt/PySide versions, OS/DPI, scenarios exercised, observed result, and remaining failures. Screenshot evidence helps visual checks; resource counts or callbacks observed over multiple cycles help lifecycle checks. Standalone Qt fixtures cannot establish host ownership, Max focus, or scene safety. No design system can guarantee perfect rendering in every host and display configuration.
