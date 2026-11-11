# Reliability inside 3ds Max

Lessons from building and supporting TerraScoop on 3ds Max 2022-2027 (PySide2 and PySide6), each one a real failure.
They apply to any Python + Qt tool in Max. The starter templates already follow them.

## Start safety: crashes users can report

Users whose Max crashes when a tool starts can usually send only MaxPkg's log, which mirrors the MAXScript Listener.

- **Start guard** (`startguard.py`): before every start step (settings, scale, theme, window, geometry, show) write the
  step to `logs/start-<host>.json`; write `ready` once the window works (and `stopped` / `failed` on close or a Python
  error). A start that finds an unfinished step knows Max died during it.
- That start prints a short report to the Listener: the step, the tool version, facts about that start (Max / Qt /
  Python versions, settings that matter) and the end of the faulthandler crash log of the dead session. MaxPkg's log
  shows it, so the user's screenshot carries the evidence. It also shows a status line "Safe start: ... please send the
  logs".
- **Safe mode** for the rest of that tool version: optional native extras off (DWM corners and masks, `qtmax` hotkey
  hooks, following Max's window), the window centred instead of restored. A new version tries the normal start again.
- **faulthandler** writes `logs/crash-<host>.log` with a session mark at each start, all threads. Enable it after the
  guard has read the previous session's tail.
- **Read the crash log before designing a fix.** A dump whose top frame is `Garbage-collecting` means Python's garbage
  collector met a broken object; the frames below are only where the collection happened to run (an import, a
  `findChildren`), and disabling features just moves the crash.

## Python's garbage collector in 3ds Max 2024

Max 2024 (PySide2 5.15.1 on Python 3.10) died at the first full collection after a large tool window was built; the same
Python and PySide2 outside Max did not, even with a collection every 300 ms. The broken object comes from inside Max.

- Hold automatic collection while the tool runs on PySide2 + Python 3.10+ (and on any host after a crash marked
  `Garbage-collecting`): `gc.disable()` at the very start of `start()`; on close `gc.freeze()` then `gc.enable()`, so no
  later collection walks the objects that existed (including the broken one). Reference counting still frees almost
  everything; only cyclic garbage made meanwhile stays.
- `gcprobe.run()` from the Listener (`python.execute "from mytool import gcprobe; gcprobe.run()"`, tool open) walks every
  tracked object and its references like a collection does, and writes the type it is at into an mmap'd file first, so a
  crash still names the object; the next start's report includes it.

## Dead Qt wrappers

- **Never ask a widget for its screen.** Max 2024's main window returned a QScreen that Qt had already deleted ("Internal
  C++ object (PySide2.QtGui.QScreen) already deleted"); when PySide did not notice, the next start read freed memory and
  crashed Max. Look screens up by position in `QGuiApplication.screens()` (`live_screens`, `screen_at`, `work_area`,
  `primary_work_area`), skip wrappers that raise, keep no QScreen objects, and fall back to a Full HD area.
- **`widget.style()` can be dead** (another tool replaced the application style, Max 2026): never call
  `style().unpolish/polish`; `repolish(widget)` re-applies the widget's own style sheet instead, and puts back the
  interface-size font that polishing takes away ([interface size](interface-size.md)).
- After `deleteLater`, a Python wrapper may outlive its C++ object: check `shiboken.isValid` (`is_valid`) before late
  callbacks touch widgets.

## Events 3ds Max takes first

3ds Max filters events for the whole application, before a widget's own event filters:

- **ToolTip** events never reach a tool's widgets (both Max 2022 and 2027): a tool cannot restyle the tooltip from
  that event. The tool's Tip follows Enter and Leave instead, and the text lives outside Qt's tooltip property so Max
  shows nothing over it.
- **Esc** (and other hotkeys) are taken unless the widget with the keyboard focus has Max's accelerators off. Every
  window, dialog, popup and menu of the tool calls `qt_compat.own_keyboard` on itself and its children when it shows
  (`DisableMaxAcceleratorsOnFocus`): the main window, dialogs, the calendar, the colour picker and its pipette, the
  lightbox and menus. A popup created later than its window needs its own call.

## Qt objects that took Max down

- **Qt's own tooltip window, rounded by a mask.** To round the plain tooltips, a first try set a window mask on Qt's
  tooltip label (`qtooltip_label`, a private `QTipLabel`) and installed an event filter object on it. 3ds Max 2022
  died with an access violation in the next `QToolTip.showText` (the faulthandler dump named that line): Qt deletes
  and recreates that label on its own schedule. Never touch Qt's tooltip window; the tool shows its own Tip
  (`controls.Tip`, see the [controls catalog](controls-catalog.md#tooltips)).

- **A completer owned by its own line edit.** The trainer's search field created `QCompleter(model, field)`, asked it
  for its default popup and set it on the field. 3ds Max 2022 (PySide2 5.15.1) died with a heap corruption
  (`0xc0000374` in `ntdll.dll`, no Python traceback, no faulthandler dump) in the first event-loop pass after the window
  showed, or a moment after the window closed. Every widget built alone in a hidden window was fine; only the whole
  window failed. The fix is TerraScoop's proven pattern: the completer and its model belong to the window
  (`SearchBox(..., owner=window)`), the list view is created in Python and handed over with `setPopup`, the delegate
  is set after it, and the popup gets the style sheet and font when it opens. The trainer then passed every check in
  Max 2022 and stayed up after closing.
- **An event filter called before `__init__` ends.** PySide6 (3ds Max 2027) runs a dialog's `eventFilter` while the
  base class constructor is still building the title bar, before the subclass has created its own widgets: the
  Support and message windows failed to open with "object has no attribute". In an `eventFilter`, read the subclass's
  widgets with `getattr(self, "name", None)`, and assign a watched widget to its attribute before
  `installEventFilter`. PySide2 (3ds Max 2022) never showed it, so a check in one Max version is not enough.
- **How it was found:** build each new widget in its own hidden window inside Max with a marker written and flushed
  (`os.fsync`) before and after each step; then build the whole window with sections switched off by halves; then
  swap the suspect for a stand-in and switch its parts on one by one. The last marker names the step. Use a Max that
  holds no user work for this; a native crash cannot be caught.

## Threads, the GIL and heavy work

- 3ds Max keeps Python's GIL on its main thread while idle, so worker threads only advance while main-thread Python runs:
  a 0.7 s job took 45 s. While any job runs, a 16 ms Qt timer sleeps 10 ms on the main thread (`_GilPump`), and stops
  when the runner is idle. Start every job through `JobRunner.submit` so the pump starts. No nested `processEvents()`.
- `pymxs`, scene, viewport and Qt widget calls stay on the main thread. Workers get plain data; results and progress come
  back through a queued signal (`_Poster`) and are dropped when the session stops or the job was cancelled.
- Heavy CPU work (big meshes, images, external programs) belongs in a **child process**: Max's own `python.exe -B -m
  package.worker job.pickle` with the working directory `python/`. Not `multiprocessing` (inside Max `sys.executable` is
  3dsmax.exe and spawn re-imports `__main__`). Not `python.exe package/worker.py` by path (the package folder shadows the
  standard library: a module named `http.py` replaced `http`). Pass the Qt DLL folder and plugin path if the worker uses
  Qt; end it with `taskkill /F /T` on cancel so its own children die too; fall back to threads if no process starts.
- Max 2027's in-process Python is markedly slower for long pure-Python loops than the same interpreter standalone; another
  reason for the child process.
- Bundled OpenMP programs run in parallel spin their idle threads: set `OMP_WAIT_POLICY=PASSIVE` and a thread count per job.

## Keyboard

- Max's accelerators take Esc, Delete and letters before a Qt tool window sees them. Call
  `qtmax.DisableMaxAcceleratorsOnFocus(widget, True)` for the window and every child (again for widgets created later).
- Never send keystrokes to a user's Max to test a tool: they go to Max's focused window and trigger Max hotkeys. Test
  keys with QTest in a standalone window.

## Web views (only if the tool embeds one)

- The object registered with `QWebChannel` must have **slots only with `str` arguments and no signals**: a published
  `Signal(dict)` / `Signal(list)` made the channel convert PyObjects recursively until the native stack overflowed and
  Max died. Python-facing signals live on a separate, unpublished QObject without a widget parent.
- Max 2022's QtWebEngine is Chromium 80: plain ES2017 JavaScript and conservative CSS (no `inset`, no `?.` / `??`).
- PySide2 `runJavaScript(code, callback)` does not exist: use `runJavaScript(code, 0, callback)` in both bindings.
- Chromium flags and the Qt Quick backend are read once per process, at the first web view; later settings do nothing.
- Pages do not repaint while covered: verify DOM state with `runJavaScript`, not a window grab.

## Scene work

- **Create large meshes in one call**: `mesh vertices: faces: materialIDs:` (triangles), hide triangulation diagonals
  with `setEdgeVis`, then `convertToPoly` (it keeps the hidden diagonals and rebuilds the polygons). `polyop.createPolygon`
  per face is quadratic in Max 2022 (minutes for 30k vertices). Set smoothing groups explicitly (the mesh constructor
  defaults to group 1; give sharp parts their own groups).
- `mesh tverts:` is silently ignored: apply UVs explicitly (`setNumTVerts`, `setTVert`, `buildTVFaces`, `setTVFace`).
- MAXScript snippets run through `python.execute` / MCP are top-level code: wrap them in `( ... )` before using `local`.
  `python.execute` returns nothing: put results on a known module attribute and read it back.
- **Undo and failures**: run large builds with undo off and delete everything created if a step fails. Never call a full
  MAXScript `gc()` in a user's scene (it clears the undo history); use `gc light:true`.
- **Memory**: MAXScript values made during one Python call stay alive until it returns; after a big build or removal
  run a light gc on `QTimer.singleShot(0)`, and `updateSceneMaterialLib()` after deleting materials. Running out of
  commit memory is an access violation, not a `MemoryError`: estimate the memory of what will be created and check free
  commit plus page-file room before creating millions of triangles; include every generated mesh in the estimate.
- **Bookkeeping**: tag created objects with a user property (import name, parameters) instead of helper Dummies (users
  delete them). Remove by exact name; never fall back to "the newest" when a name is missing.
- Never open, reset or modify a user's scene to test; use a temporary object and remove exactly it.

## Windows, files, environment

- Tool windows are owned by Max's main window: they hide while Max is minimised and come back with it. Minimised windows
  are parked at (-32000, -32000).
- One log file per day, each record appended and the file closed again at once: two Max versions running at once can
  share a day's file and Clear Logs can delete every file. The crash log stays per Max version
  (`logs.set_host("max2027")`), because faulthandler keeps its file open.
- Max's bundled `python.exe` ignores `PYTHONPATH`: tests insert the package path themselves.
- Never `sys.exit()` / `raise SystemExit` in code that runs inside Max.
- Keep the Python 3.7 floor if Max 2022 is supported, and compile with the oldest and newest interpreters before every
  commit; unit tests that do not import the Qt modules will not catch a syntax error there.
- Before creating a module, check the name is free (a new `resources.py` once replaced an existing one).
- Paths over 260 characters fail for Windows programs: keep build and test scratch paths short.
- PowerShell `Set-Content -Encoding utf8` writes a BOM; `io.open(path, "w", newline=<bad>)` truncates the file before it
  raises. Edit source files with a proper editor or a script that writes a temporary file and replaces the target.
