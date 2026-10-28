# Template: Launcher and bootstrap

The thin `.ms` entry point and the Python bootstrap that starts one session, or stops the previous one on a Qt timer and then starts a fresh one. The anchor module in `sys.modules` lives outside the reloadable package.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `StartMyTool.ms`

```maxscript
-- MyTool launcher. Starts (or cleanly restarts) the Python tool inside 3ds Max.
(
    local entryPath = getThisScriptFileName()
    local bootstrapPath = (getFilenamePath entryPath) + @"python\bootstrap.py"
    if not doesFileExist bootstrapPath do
        throw "MyTool bootstrap is missing. Restore the complete tool folder."
    python.ExecuteFile bootstrapPath
)
```

## `python/bootstrap.py`

```python
"""Executed by StartMyTool.ms inside 3ds Max's Python. Starts or restarts the MyTool session.

The session anchor lives in sys.modules["_mytool_session"], outside the reloadable package, so a
relaunch can find the previous owner, ask it to stop, wait for it on a Qt timer (never sleeping on the
main thread), then import fresh code and start exactly one replacement.
"""

import importlib
import importlib.util
import os
import sys
import time
import traceback
import types

PACKAGE = "mytool"
ANCHOR = "_mytool_session"
STOP_TIMEOUT = 15.0


def _qtcore():
    if importlib.util.find_spec("PySide6") is not None:
        from PySide6 import QtCore
    else:
        from PySide2 import QtCore
    return QtCore


def _report(message):
    print("MyTool: " + message)


def _import_fresh(root):
    for name in list(sys.modules):
        if name == PACKAGE or name.startswith(PACKAGE + "."):
            del sys.modules[name]
    importlib.invalidate_caches()
    folder = os.path.join(root, "python", PACKAGE)
    spec = importlib.util.spec_from_file_location(PACKAGE, os.path.join(folder, "__init__.py"),
                                                  submodule_search_locations=[folder])
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the MyTool package from " + folder)
    package = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE] = package
    spec.loader.exec_module(package)
    return importlib.import_module(PACKAGE + ".controller")


def _start_new(state, root):
    candidate = None
    try:
        controller = _import_fresh(root)
        candidate = controller.Controller(root)
        state.owner = candidate
        candidate.start()
    except Exception:
        _report("start failed:\n" + traceback.format_exc())
        if candidate is not None:
            try:
                candidate.request_stop()
                candidate.poll_stop()
            except Exception:
                _report("cleanup after failed start also failed:\n" + traceback.format_exc())


def launch(root):
    state = sys.modules.get(ANCHOR)
    if state is None:
        state = types.ModuleType(ANCHOR)
        sys.modules[ANCHOR] = state
    if getattr(state, "transitioning", False):
        return  # A relaunch is already in progress; repeated clicks coalesce.
    old = getattr(state, "owner", None)
    if old is not None:
        try:
            old.poll_stop()  # Finish a cleanup left over from an earlier close, if any.
        except Exception:
            pass
    if old is None or old.is_stopped():
        state.transitioning = True
        try:
            _start_new(state, root)
        finally:
            state.transitioning = False
        return

    # A running build is not interrupted silently: the old session asks first (older versions have no
    # confirm_stop and stop as before).
    confirm = getattr(old, "confirm_stop", None)
    if confirm is not None:
        try:
            if not confirm("relaunch"):
                return
        except Exception:
            _report("could not ask the previous session:\n" + traceback.format_exc())

    state.transitioning = True
    try:
        old.request_stop()
    except Exception:
        state.transitioning = False
        _report("could not stop the previous session:\n" + traceback.format_exc())
        return

    QtCore = _qtcore()
    timer = QtCore.QTimer()
    state.poll_timer = timer  # Strong reference on the anchor, outside the reloadable package.
    deadline = time.monotonic() + STOP_TIMEOUT

    def tick():
        try:
            old.poll_stop()
            if old.is_stopped():
                timer.stop()
                state.poll_timer = None
                try:
                    _start_new(state, root)
                finally:
                    state.transitioning = False
            elif time.monotonic() > deadline:
                timer.stop()
                state.poll_timer = None
                state.transitioning = False
                _report("the previous session did not stop in time. Run MyTool again to retry.")
        except Exception:
            timer.stop()
            state.poll_timer = None
            state.transitioning = False
            _report("restart failed:\n" + traceback.format_exc())

    timer.timeout.connect(tick)
    timer.start(50)


launch(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```
