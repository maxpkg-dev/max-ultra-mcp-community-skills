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
  `style().unpolish/polish`; `repolish(widget)` re-applies the widget's own style sheet instead.
- After `deleteLater`, a Python wrapper may outlive its C++ object: check `shiboken.isValid` (`is_valid`) before late
  callbacks touch widgets.

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
- Logs per Max version (`logs.set_host("max2027")`): two Max versions running at once must not share a log file.
- Max's bundled `python.exe` ignores `PYTHONPATH`: tests insert the package path themselves.
- Never `sys.exit()` / `raise SystemExit` in code that runs inside Max.
- Keep the Python 3.7 floor if Max 2022 is supported, and compile with the oldest and newest interpreters before every
  commit; unit tests that do not import the Qt modules will not catch a syntax error there.
- Before creating a module, check the name is free (a new `resources.py` once replaced an existing one).
- Paths over 260 characters fail for Windows programs: keep build and test scratch paths short.
- PowerShell `Set-Content -Encoding utf8` writes a BOM; `io.open(path, "w", newline=<bad>)` truncates the file before it
  raises. Edit source files with a proper editor or a script that writes a temporary file and replaces the target.
