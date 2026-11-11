# Template: Package identity, settings and resources

Name, version, developer, links, the donation destination and the donation offers in one place; JSON settings with session-only overrides for tests; when the tool offers a donation (`donation.py`, pure code: the Support window from Donate, the line on a result card, the start reminder; see [donations](../donations.md)); package-relative resource paths.

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
LINKS = (("3dground.net", "https://3dground.net"),)  # (label, https URL) pairs shown in About.
DONATE_URL = "https://3dground.net"  # Only a destination the owner gave; "" hides every Donate button.
# Where a donation is offered (see donation.py); ask the owner which ones they want. () = only the address in About.
DONATE_OFFERS = ("status", "about", "after_success", "reminder")
# The rotating link in the status bar (controls.PromotionLink): (long text, short text, https URL), the owner's own
# sites and tools and, when they want it, a donation request. () = no rotating link. Never a page the owner did not
# name.
PROMOTIONS = (
    ("Find practical 3ds Max scripts on 3dground.net.", "Scripts on 3dground.net", "https://3dground.net"),
    ("Discover useful 3ds Max tools on maxpkg.dev.", "Tools on maxpkg.dev", "https://maxpkg.dev"),
    ("Clean up unwanted scene data with Prune Scene.", "Explore Prune Scene", "https://maxpkg.dev/catalog/prune-scene"),
    ("Prepare models and assets for delivery with Model Packer.", "Explore Model Packer",
     "https://maxpkg.dev/catalog/model-packer"),
    ("{} is free. A small donation keeps it growing.".format(TOOL_NAME), "Support {}".format(TOOL_NAME), DONATE_URL),
)
# The update.json that tools/release.py writes, at its published address (for example the raw file in the main branch
# of the tool's repository). "" = no self-update: no checks, no Updates group in Settings (MaxPkg still updates the
# installed package).
UPDATE_URL = ""
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
    "auto_update": True,  # With an UPDATE_URL: check at start and install a newer version in the background.
    "ui_scale": "auto",  # Interface size: "auto" (screen and Windows / Max scaling) or a factor as text, "1.25".
    "window_geometry": "",  # saveGeometry() of the full window, base64.
    "mini_position": [],  # [x, y] of the collapsed bar when the user last moved it; [] = active viewport corner.
    "starts": 0,  # How many times the tool started (donation.py: the reminder).
    "successes": 0,  # Successful operations (donation.py: the line on the result card).
    "donate_reminders": True,  # Off after "I've already donated, don't remind me" or in Settings.
    "donate_reminded_at": 0,  # The start that last showed the reminder.
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

## `python/mytool/donation.py`

```python
"""When the tool offers a donation. Pure code (no Qt): the rules are tested without a window.

The owner chooses the offers in DONATE_OFFERS (package __init__); ask them which they want and never invent a
donation address. Nothing is offered without a DONATE_URL.

* "status": Donate at the right of the status bar. It opens the Support window (why a donation matters, Not now,
  a shimmering Donate), never the page straight away.
* "about": Donate at the bottom of About; it opens the Support window too.
* "after_success": after a successful operation the result card carries a line and a shimmering Donate. From the
  NOTE_FROM-th success on, at most once a session, never after a failure or a cancelled run.
* "reminder": the Support window by itself on the REMIND_AT-th start (after the window is up, never in safe mode),
  then every REMIND_EVERY starts (0 = only once). Its way out is "I've already donated, don't remind me" (the user's
  word, an honour system); Settings has the same switch.
Every offer can be closed with one click and none comes back in the same session.
"""

from . import DONATE_OFFERS, DONATE_URL

REMIND_AT = 5  # The start that shows the reminder first
REMIND_EVERY = 30  # Starts between reminders; 0 = only once
NOTE_FROM = 2  # The success that may first carry the donation line


class Donations(object):
    """`prefs` reads and writes the durable values (settings.Settings: get, set); `save()` writes them."""

    def __init__(self, prefs, save, url=None, offers=None):
        self.prefs = prefs
        self.save = save
        self.url = DONATE_URL if url is None else url
        self.offers = tuple(DONATE_OFFERS if offers is None else offers)
        self._noted = False
        self._reminded = False

    def offers_on(self, offer):
        return bool(self.url) and offer in self.offers

    def count_start(self):
        """Once per start of the tool. Returns the number of starts so far."""
        starts = int(self.prefs.get("starts") or 0) + 1
        self.prefs.set("starts", starts)
        self.save()
        return starts

    def reminder_due(self):
        if self._reminded or not self.offers_on("reminder") or not self.prefs.get("donate_reminders"):
            return False
        starts = int(self.prefs.get("starts") or 0)
        last = int(self.prefs.get("donate_reminded_at") or 0)
        if last <= 0:
            return starts >= REMIND_AT
        return REMIND_EVERY > 0 and starts - last >= REMIND_EVERY

    def mark_reminded(self):
        self._reminded = True
        self.prefs.set("donate_reminded_at", int(self.prefs.get("starts") or 0))
        self.save()

    def set_reminders(self, on):
        """"I've already donated, don't remind me" (off) and the Settings switch."""
        self.prefs.set("donate_reminders", bool(on))
        self.save()

    def after_success(self):
        """Count a successful operation; True when its result card may carry the donation line."""
        successes = int(self.prefs.get("successes") or 0) + 1
        self.prefs.set("successes", successes)
        self.save()
        if self._noted or not self.offers_on("after_success") or successes < NOTE_FROM:
            return False
        self._noted = True
        return True
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
