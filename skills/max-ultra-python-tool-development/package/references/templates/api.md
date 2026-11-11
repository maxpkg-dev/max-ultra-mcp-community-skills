# Template: The API (the tool without its window)

The tool's operations for MAXScript, Python and AI assistants through Max Ultra MCP, with no window open (see [the API](../api.md)). `MyToolAPI.ms` defines `MyToolAPI.call operation params:"{...}"`; `api_entry.py` loads the package the window starts, or the window's own modules; `api.py` holds the operations with checked parameters, `describe`, the envelope and the JSON and MAXScript entry points; `max_api.py` does the scene work on the main thread only, with `dry_run` and one undo record for changes. The window calls the same functions.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md); replace the example operations with the tool's own. Verified inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP (the trainer's checks, and `MyToolAPI.call "describe"` sent through `max_execute`).

## `MyToolAPI.ms`

```maxscript
-- MyTool API for MAXScript and AI assistants (through Max Ultra MCP): the tool's operations without its window.
-- StartMyTool.ms runs this file; a startup script may run it alone, so the API is there from the start of 3ds Max.
-- Every call returns JSON text: {"ok": true, "result": ...} or {"ok": false, "error": {"code": ..., "message": ...}}.
--   MyToolAPI.call "describe"                                                -- what the tool can do
--   MyToolAPI.call "scene_summary" params:"{\"selection_only\": true}"
--   MyToolAPI.call "add_prefix" params:"{\"prefix\": \"SM_\", \"dry_run\": true}"
global MyToolAPIRequest
global MyToolAPIResult
global MyToolAPI

struct MyToolAPIStruct
(
    loader,
    fn call operation params:"{}" =
    (
        python.ExecuteFile loader  -- Loads the package once; the window's own copy when it is open
        MyToolAPIRequest = "{\"operation\": \"" + operation + "\", \"params\": " + params + "}"
        MyToolAPIResult = undefined
        python.Execute "from mytool import api as _mytool_api\n_mytool_api.call_from_maxscript()"
        MyToolAPIResult
    )
)

(
    local loaderPath = (getFilenamePath (getThisScriptFileName())) + @"python\api_entry.py"
    if not doesFileExist loaderPath do
        throw "MyTool API loader is missing. Restore the complete tool folder."
    MyToolAPI = MyToolAPIStruct loader:loaderPath
)
```

## `python/api_entry.py`

```python
"""Loads MyTool's API without its window (MyToolAPI.ms runs this file before every call; after the first it does
nothing). It uses the same copy of the tool the window starts (bootstrap.pick_root: an installed update when it is
newer, else the copy next to the launcher), and when the window is open, the window's own modules. It opens no
window and touches no scene.
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE = "mytool"


def _bootstrap():
    """bootstrap.py as a library: pick_root only, without starting the window."""
    spec = importlib.util.spec_from_file_location("_mytool_bootstrap_lib", os.path.join(HERE, "bootstrap.py"))
    module = importlib.util.module_from_spec(spec)
    module._MYTOOL_IMPORT_ONLY = True  # bootstrap.py starts the window unless this is set
    spec.loader.exec_module(module)
    return module


def load():
    if PACKAGE in sys.modules:  # The window's session (or an earlier call) has it already
        return sys.modules[PACKAGE]
    root = _bootstrap().pick_root(os.path.dirname(HERE))
    folder = os.path.join(root, "python", PACKAGE)
    spec = importlib.util.spec_from_file_location(PACKAGE, os.path.join(folder, "__init__.py"),
                                                  submodule_search_locations=[folder])
    package = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE] = package
    try:
        spec.loader.exec_module(package)
    except Exception:
        del sys.modules[PACKAGE]  # Never leave a half-loaded package behind
        raise
    return package


load()
```

## `python/mytool/api.py`

```python
"""The tool without its window: a small, stable API for scripts, MAXScript and AI assistants (through Max Ultra MCP).

Every operation of the tool is an operation here too, and the window calls the same functions (max_api.py for scene
work), so a fix reaches both. The rules:

* Plain data in, plain data out. Every call returns an envelope and never raises:
  {"ok": true, "operation": ..., "result": ..., "warnings": [...]} or
  {"ok": false, "operation": ..., "error": {"code": ..., "message": ...}}.
* describe() says what the tool can do: each operation's purpose, whether it changes the scene, its parameters with
  type, default, limits and text, and an example. An assistant reads it first and calls only what it lists.
* Parameters are checked here (type, required, choices, limits); an unknown parameter is refused, never ignored.
* An operation that changes the scene takes dry_run and says what it would change; the real run is one undo record
  and returns what it changed (handles, names, counts) for checks.
* No dialogs, no prompts, no windows: a missing answer is an error with a clear message.
* Main thread only for scene work (MAXScript, Max Ultra MCP's max_execute and the window all run there).
* API_VERSION grows only when an existing call changes meaning; a new operation does not change it.

From Python: `from mytool import api; api.call("scene_summary", selection_only=True)`.
From MAXScript (after MyToolAPI.ms ran, which the launcher does): `MyToolAPI.call "describe"` or
`MyToolAPI.call "add_prefix" params:"{\"prefix\": \"SM_\", \"dry_run\": true}"`; both return JSON text.
"""

import json
import logging
import re
import sys
import traceback

from . import TOOL_NAME, __version__
from . import max_api, settings

API_VERSION = 1
LOG = logging.getLogger("mytool.api")

# The settings an assistant may read and change; window positions and counters stay the tool's own.
PUBLIC_SETTINGS = {
    "theme": {"type": "string", "choices": ("graphite", "max", "burgundy", "coffee", "teal", "forest", "plum"),
              "text": "The colour theme of the tool's windows"},
    "ui_scale": {"type": "string", "choices": ("auto", "1.0", "1.25", "1.5", "1.75", "2.0"),
                 "text": "Interface size: auto, or a factor"},
    "auto_update": {"type": "boolean", "text": "Check for a newer version at start and install it"},
    "donate_reminders": {"type": "boolean", "text": "Show the donation reminder now and then"},
}


class ApiError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code


# The operations ------------------------------------------------------------------------------------------------------
def _describe():
    return {"tool": TOOL_NAME, "version": __version__, "api_version": API_VERSION,
            "operations": [dict(name=name, **{key: value for key, value in entry.items() if key != "function"})
                           for name, entry in sorted(OPERATIONS.items())]}


def _session_settings():
    """The running window's settings when it is open (so a change shows there at once), else the file's."""
    state = sys.modules.get("_mytool_session")
    owner = getattr(state, "owner", None)
    prefs = getattr(owner, "prefs", None)
    if prefs is not None and hasattr(prefs, "get") and hasattr(prefs, "set"):
        return prefs, owner
    return settings.Settings().load(), None


def _get_settings():
    prefs, _owner = _session_settings()
    return {key: prefs.get(key) for key in sorted(PUBLIC_SETTINGS)}


def _set_setting(key, value):
    spec = PUBLIC_SETTINGS.get(key)
    if spec is None:
        raise ApiError("INVALID_PARAMS", "Unknown setting {!r}; the settings are: {}".format(
            key, ", ".join(sorted(PUBLIC_SETTINGS))))
    _check_value("value", value, spec)
    prefs, owner = _session_settings()
    before = prefs.get(key)
    theme = getattr(owner, "theme", None)
    if key == "theme" and theme is not None and hasattr(theme, "select"):
        problem = theme.select(value)  # Every open window takes the theme at once, then it is saved
        if problem and "not saved" not in problem:
            raise ApiError("FAILED", problem)
        applied = True
    elif owner is not None and hasattr(owner, "set_preference"):
        owner.set_preference(key, value)  # Saved; a change of interface size shows at the next start
        applied = False
    else:
        prefs.set(key, value)
        prefs.save()
        applied = False
    return {"key": key, "from": before, "to": value, "applied_now": applied}


OPERATIONS = {
    "describe": {
        "function": _describe, "summary": "What this tool can do: every operation with its parameters.",
        "changes_scene": False, "params": {}, "example": {"operation": "describe"}},
    "scene_summary": {
        "function": max_api.scene_summary, "summary": "Count the objects of the scene or the selection by kind.",
        "changes_scene": False,
        "params": {"selection_only": {"type": "boolean", "default": False,
                                      "text": "Count only the selected objects"}},
        "example": {"operation": "scene_summary", "params": {"selection_only": True}}},
    "add_prefix": {
        "function": max_api.add_prefix,
        "summary": "Put a prefix in front of object names that lack it; one undo record. Try dry_run first.",
        "changes_scene": True,
        "params": {"prefix": {"type": "string", "required": True, "pattern": "^[A-Za-z0-9_-]{1,32}$",
                              "text": "Letters, digits, - and _ (1-32)"},
                   "selection_only": {"type": "boolean", "default": True,
                                      "text": "Only the selected objects; false renames every object"},
                   "dry_run": {"type": "boolean", "default": False, "text": "Only say what would change"}},
        "example": {"operation": "add_prefix", "params": {"prefix": "SM_", "dry_run": True}}},
    "get_settings": {
        "function": _get_settings, "summary": "The tool's settings an assistant may read.",
        "changes_scene": False, "params": {}, "example": {"operation": "get_settings"}},
    "set_setting": {
        "function": _set_setting, "summary": "Change one setting; an open window applies it at once.",
        "changes_scene": False,
        "params": {"key": {"type": "string", "required": True, "choices": tuple(sorted(PUBLIC_SETTINGS)),
                           "text": "The setting"},
                   "value": {"type": "any", "required": True, "text": "Its new value (see get_settings)"}},
        "example": {"operation": "set_setting", "params": {"key": "theme", "value": "max"}}},
}


# Checking and calling ------------------------------------------------------------------------------------------------
_TYPES = {"string": str, "boolean": bool, "integer": int, "number": (int, float)}


def _check_value(name, value, spec):
    kind = spec.get("type", "any")
    if kind != "any":
        wanted = _TYPES[kind]
        if kind in ("integer", "number") and isinstance(value, bool) or not isinstance(value, wanted):
            raise ApiError("INVALID_PARAMS", "{} must be a {}".format(name, kind))
    if "choices" in spec and value not in spec["choices"]:
        raise ApiError("INVALID_PARAMS", "{} must be one of: {}".format(name, ", ".join(map(str, spec["choices"]))))
    if "minimum" in spec and value < spec["minimum"] or "maximum" in spec and value > spec["maximum"]:
        raise ApiError("INVALID_PARAMS", "{} must be between {} and {}".format(
            name, spec.get("minimum", "-"), spec.get("maximum", "-")))
    if "pattern" in spec:
        if not re.match(spec["pattern"], value):
            raise ApiError("INVALID_PARAMS", "{}: {}".format(name, spec.get("text", "wrong form")))


def _arguments(entry, params):
    specs = entry["params"]
    unknown = sorted(set(params) - set(specs))
    if unknown:
        raise ApiError("INVALID_PARAMS", "Unknown parameter(s): {}; this operation takes: {}".format(
            ", ".join(unknown), ", ".join(sorted(specs)) or "nothing"))
    arguments = {}
    for name, spec in specs.items():
        if name in params:
            _check_value(name, params[name], spec)
            arguments[name] = params[name]
        elif spec.get("required"):
            raise ApiError("INVALID_PARAMS", "{} is required ({})".format(name, spec.get("text", "")))
        elif "default" in spec:
            arguments[name] = spec["default"]
    return arguments


def call(operation, **params):
    """Run one operation; returns the envelope (see the module), never raises."""
    envelope = {"ok": False, "operation": operation}
    try:
        entry = OPERATIONS.get(operation)
        if entry is None:
            raise ApiError("UNKNOWN_OPERATION", "No operation {!r}; describe lists them: {}".format(
                operation, ", ".join(sorted(OPERATIONS))))
        function = entry["function"]
        result = function(**_arguments(entry, params))
        envelope.update(ok=True, result=result, warnings=[])
    except ApiError as error:
        envelope["error"] = {"code": error.code, "message": str(error)}
    except max_api.NotInMax as error:
        envelope["error"] = {"code": "NOT_IN_MAX", "message": str(error)}
    except Exception as error:  # The caller gets a clear error; the log keeps the traceback
        LOG.error("API %s failed\n%s", operation, traceback.format_exc())
        envelope["error"] = {"code": "FAILED", "message": "{}: {}".format(type(error).__name__, error)}
    LOG.info("API %s: %s", operation, "ok" if envelope["ok"] else envelope["error"]["code"])
    return envelope


def call_json(text):
    """JSON in ({"operation": ..., "params": {...}}), JSON out (the envelope)."""
    try:
        request = json.loads(text or "{}")
        if not isinstance(request, dict) or not isinstance(request.get("params", {}), dict):
            raise ValueError("expected {\"operation\": ..., \"params\": {...}}")
    except ValueError as error:
        return json.dumps({"ok": False, "operation": None, "error": {"code": "INVALID_JSON", "message": str(error)}})
    return json.dumps(call(request.get("operation", "describe"), **request.get("params", {})), ensure_ascii=False)


def call_from_maxscript():
    """MyToolAPI.call in MyToolAPI.ms: the request waits in the MAXScript global MyToolAPIRequest (JSON text); the
    answer goes to MyToolAPIResult (JSON text)."""
    import pymxs
    runtime = pymxs.runtime
    runtime.MyToolAPIResult = call_json(str(runtime.MyToolAPIRequest))
```

## `python/mytool/max_api.py`

```python
"""Scene work, on 3ds Max's main thread only: pymxs lives here and nowhere else in the tool.

The window and the API (api.py) both call these functions, so the tool has one code path for every operation. Each
function takes plain values and returns plain data: what it found or what it changed (handles, names, counts), never
a Qt object. A function that changes the scene takes dry_run and does its changes inside one undo record, so Ctrl+Z
takes back the whole operation.

Never call these from a worker thread; a job that needs scene data gets it here first and passes plain data on.
"""


class NotInMax(RuntimeError):
    """pymxs is missing: the code runs outside 3ds Max (a unit test, a plain Python)."""


def _runtime():
    try:
        import pymxs
    except ImportError:
        raise NotInMax("This needs 3ds Max (pymxs is not available)")
    return pymxs, pymxs.runtime


def _nodes(rt, selection_only):
    return list(rt.selection) if selection_only else list(rt.objects)


def scene_summary(selection_only=False):
    """How many objects the scene (or the selection) holds, by kind. Read-only."""
    _pymxs, rt = _runtime()
    nodes = _nodes(rt, selection_only)
    kinds = {}
    for node in nodes:
        kind = str(rt.superClassOf(node))
        kinds[kind] = kinds.get(kind, 0) + 1
    return {"objects": len(nodes), "by_kind": kinds, "selected": int(rt.selection.count),
            "scene": str(rt.maxFilePath) + str(rt.maxFileName) or ""}


def add_prefix(prefix, selection_only=True, dry_run=False):
    """Put `prefix` in front of the names of the selected objects (or of every object) that do not start with it
    yet. With dry_run nothing changes and the result says what would. One undo record for the whole operation."""
    pymxs, rt = _runtime()
    planned = []
    for node in _nodes(rt, selection_only):
        name = str(node.name)
        if not name.startswith(prefix):
            planned.append((int(rt.getHandleByAnim(node)), name, prefix + name))
    if planned and not dry_run:
        with pymxs.undo(True, "Add prefix"):
            for handle, _old, new in planned:
                node = rt.maxOps.getNodeByHandle(handle)
                if node is not None:
                    node.name = new
    return {"dry_run": bool(dry_run), "count": len(planned),
            "changed": [{"handle": handle, "from": old, "to": new} for handle, old, new in planned]}
```
