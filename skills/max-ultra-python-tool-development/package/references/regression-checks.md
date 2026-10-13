# Observable regression checks

Run checks relevant to the generated tool, with pure/mocked and real-host results recorded separately. Use an authorized disposable scene for Max tests. This list is a test specification, not evidence that these checks have already passed.

| Scenario | Observable pass condition |
| --- | --- |
| Launch twice, rapidly, hidden, and after close | Exactly one active owner and intended main window; old timers/callback IDs/connections no longer fire |
| Relaunch during worker activity / active tick | New instance starts only after old work quiesces; old result cannot alter new UI or scene |
| Stop timeout or cleanup exception | No duplicate replacement; Max stays alive; retained owner enables later cleanup retry; diagnostic names the failure |
| Startup failure after each acquisition | Already-acquired resources released; unrelated Max callbacks/windows/processes remain intact |
| Theme selection with all dialogs open | Every owned window, popup, menu, painted control and rich text changes immediately; persisted ID restores on next launch |
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

Report exact Max build, Python, Qt/PySide versions, OS/DPI, scenarios exercised, observed result, and remaining failures. Screenshot evidence helps visual checks; resource counts or callbacks observed over multiple cycles help lifecycle checks. Standalone Qt fixtures cannot establish host ownership, Max focus, or scene safety. No design system can guarantee perfect rendering in every host and display configuration.
