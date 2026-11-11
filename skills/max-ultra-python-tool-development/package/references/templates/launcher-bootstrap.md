# Template: Launcher and bootstrap

The thin `.ms` entry point and the Python bootstrap that starts one session, or stops the previous one on a Qt timer and then starts a fresh one. The anchor module in `sys.modules` lives outside the reloadable package. The bootstrap starts the newest copy of the tool (next to the launcher, or a self-update in the user profile) and rolls back a freshly updated version that cannot start.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `StartMyTool.ms`

```maxscript
-- MyTool launcher. Starts (or cleanly restarts) the Python tool inside 3ds Max, and defines MyToolAPI (MyToolAPI.ms)
-- so scripts and AI assistants can use the tool's operations without its window.
(
    local entryPath = getThisScriptFileName()
    local folder = getFilenamePath entryPath
    local bootstrapPath = folder + @"python\bootstrap.py"
    if not doesFileExist bootstrapPath do
        throw "MyTool bootstrap is missing. Restore the complete tool folder."
    if doesFileExist (folder + "MyToolAPI.ms") do
        fileIn (folder + "MyToolAPI.ms")  -- Only defines MyToolAPI; loads nothing until its first call
    python.ExecuteFile bootstrapPath
)
```

## `python/bootstrap.py`

```python
"""Executed by StartMyTool.ms inside 3ds Max's Python. Starts or restarts the MyTool session.

The session anchor lives in sys.modules["_mytool_session"], outside the reloadable package, so a
relaunch can find the previous owner, ask it to stop, wait for it on a Qt timer (never sleeping on the
main thread), then import fresh code and start exactly one replacement.

It starts the newest copy of the tool: the one next to the launcher (installed by MaxPkg) or one installed by a
self-update in %LOCALAPPDATA%/MyTool/app (updater.py). A freshly updated version that cannot start rolls back to
the previous one, or to the copy next to the launcher. This file itself is not updated by a self-update: keep it
compatible with newer packages.
"""

import importlib
import importlib.util
import json
import os
import re
import sys
import time
import traceback
import types

PACKAGE = "mytool"
ANCHOR = "_mytool_session"
STOP_TIMEOUT = 15.0
TOOL_FOLDER = "MyTool"  # settings.user_data_dir(): %LOCALAPPDATA%\MyTool
LAUNCHER_ROOT_VARIABLE = "MYTOOL_LAUNCHER_ROOT"  # Tells the controller where the launcher is (Reopen)


def app_home():
    return os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), TOOL_FOLDER, "app")


def _version_of(root):
    """The package version of a copy of the tool, read from its __init__.py without importing it."""
    try:
        with open(os.path.join(root, "python", PACKAGE, "__init__.py"), "r", encoding="utf-8") as handle:
            match = re.search(r"^__version__\s*=\s*['\"]{1}([^'\"]+)['\"]", handle.read(), re.M)
    except OSError:
        return (0, 0, 0)
    parts = re.findall(r"\d+", match.group(1))[:3] if match else []
    return tuple(int(part) for part in parts) + (0,) * (3 - len(parts))


def pick_root(bundled, home=None):
    """The copy to start: the installed update when it is newer than the copy next to the launcher, else that copy
    (MaxPkg may have installed a newer one there since)."""
    home = home or app_home()
    try:
        with open(os.path.join(home, "current.json"), "r", encoding="utf-8") as handle:
            state = json.load(handle)
        installed = os.path.join(home, state["dir"])
        if os.path.isfile(os.path.join(installed, "python", "bootstrap.py")) and \
                _version_of(installed) > _version_of(bundled):
            return installed
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return bundled


def _roll_back(root, bundled, home=None):
    """A freshly updated version that cannot start: the previous installed version becomes current (or none, so the
    copy next to the launcher starts). Returns the folder to start instead, or None."""
    home = home or app_home()
    if os.path.normcase(os.path.abspath(root)) == os.path.normcase(os.path.abspath(bundled)):
        return None  # The copy next to the launcher failed: nothing to roll back to.
    try:
        spec = importlib.util.spec_from_file_location("_mytool_rollback",
                                                      os.path.join(root, "python", PACKAGE, "updater.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        state = module.read_current(home)
        if not state or state.get("dir") != os.path.basename(root) or not module.rollback(home):
            return None
        _report("this version could not start; going back to the previous version.")
        return pick_root(bundled, home)
    except Exception:
        _report("rollback failed:\n" + traceback.format_exc())
        return None


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


def _start_new(state, bundled, retry=True):
    root = pick_root(bundled)
    os.environ[LAUNCHER_ROOT_VARIABLE] = bundled
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
        if retry and _roll_back(root, bundled) is not None:
            _start_new(state, bundled, retry=False)  # Once: the previous version, or the copy next to the launcher


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


if not globals().get("_MYTOOL_IMPORT_ONLY"):  # api_entry.py loads this file for pick_root only, without a window
    launch(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```
