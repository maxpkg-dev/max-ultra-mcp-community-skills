# Template: Package identity, settings and resources

Name, version, developer, links and the donation destination in one place; JSON settings with session-only overrides for tests; package-relative resource paths.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `python/mytool/__init__.py`

```python
"""MyTool: a Python + Qt tool for 3ds Max. Importing this package is passive: it creates no windows and touches no scene.

Identity and links live here once; the title bar, About, Settings and Donate buttons read them.
"""

__version__ = "1.0.0"
TOOL_NAME = "MyTool"
SUBTITLE = "One line about what the tool does"
DEVELOPER = "Developer Name"  # Public name; About leaves out empty values (never invent them).
LINKS = (("example.com", "https://example.com"),)  # (label, https URL) pairs shown in About.
DONATE_URL = "https://example.com/donate"  # Only a destination the owner gave; "" hides every Donate button.
```

## `python/mytool/settings.py`

```python
"""Durable user preferences stored as JSON outside the (possibly read-only) install folder.

Pure code. Unknown keys from newer versions are preserved; a value whose type differs from its default falls back to
the default (store an interface size as text, "1.25", like the default "auto").
"""

import json
import os
import tempfile

from . import TOOL_NAME

DEFAULTS = {
    "theme": "graphite",
    "ui_scale": "auto",  # Interface size: "auto" (screen and Windows / Max scaling) or a factor as text, "1.25".
    "window_geometry": "",  # saveGeometry() of the full window, base64.
    "mini_position": [],  # [x, y] of the collapsed bar when the user last moved it; [] = active viewport corner.
}


def user_data_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, TOOL_NAME)


class Settings(object):
    def __init__(self, path=None):
        self.path = path or os.path.join(user_data_dir(), "settings.json")
        self.values = dict(DEFAULTS)
        self.overrides = {}  # Session-only values (tests, fixtures); never written by save().
        self.load_error = None

    def load(self):
        self.values = dict(DEFAULTS)
        self.load_error = None
        if not os.path.isfile(self.path):
            return self
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                stored = json.load(handle)
            if not isinstance(stored, dict):
                raise ValueError("settings root is not an object")
        except (OSError, ValueError) as error:
            self.load_error = str(error)
            return self
        for key, value in stored.items():
            default = DEFAULTS.get(key)
            if key in DEFAULTS and default is not None and type(value) is not type(default):
                continue  # Wrong type: keep the default instead of crashing later.
            self.values[key] = value
        return self

    def get(self, key):
        if key in self.overrides:
            return self.overrides[key]
        return self.values.get(key, DEFAULTS.get(key))

    def override(self, key, value):
        """Use a value for this session only; save() keeps writing the user's own value."""
        self.overrides[key] = value

    def set(self, key, value):
        if key in self.overrides:
            self.overrides[key] = value  # Session-only (tests, fixtures): never reaches the settings file.
        else:
            self.values[key] = value

    def save(self):
        """Write atomically. Raises OSError so callers can report an unsaved preference."""
        folder = os.path.dirname(self.path)
        os.makedirs(folder, exist_ok=True)
        handle, temporary = tempfile.mkstemp(prefix=".settings-", suffix=".json", dir=folder)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump(self.values, stream, indent=2, sort_keys=True)
            os.replace(temporary, self.path)
        except BaseException:
            try:
                os.remove(temporary)
            except OSError:
                pass
            raise
```

## `python/mytool/resources.py`

```python
"""Package-relative resource paths. Never depends on the working directory or a developer checkout."""

import os

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
# Layout: <root>/python/<package>/resources.py; assets in <root>/assets.
ROOT = os.path.dirname(os.path.dirname(PACKAGE_DIR))


def asset(*parts):
    return os.path.join(ROOT, "assets", *parts)


def icon_path(name):
    return asset("icons", name + ".svg")


def ui_file(*parts):
    return os.path.join(PACKAGE_DIR, "ui", *parts)


def require(path):
    if not os.path.exists(path):
        raise IOError("Resource is missing: {}. Reinstall the tool.".format(path))
    return path
```
