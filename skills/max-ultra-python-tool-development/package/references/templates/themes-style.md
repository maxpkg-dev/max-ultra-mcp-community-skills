# Template: Palettes, theme manager and the style sheet

Palette JSON resolution (aliases, mixes, Max colorMan samples), transactional theme switching for every registered window, tinted icon files for QSS, and the canonical style sheet with `@role` tokens.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `python/mytool/themes.py`

```python
"""Theme palettes: load, validate, resolve and render QSS.

Pure code. Palettes are editable JSON files in assets/themes. Values are "#rrggbb",
{"mix": [left, right, ratio]} or "$nativeRole" (a 3ds Max colorMan sample, with a fallback
stored in the file). Widgets never use literal colors; they use the role names below.
"""

import json
import math
import os
import re

DEFAULT_THEME = "graphite"
_HEX = re.compile(r"#[0-9a-fA-F]{6}$")
_TOKEN = re.compile(r"@([a-z][a-z0-9_]*)")

# Palette keys every theme must define (the skill's 83-role files define all of them).
REQUIRED_KEYS = (
    "window_background", "button_background", "field_background", "recessed_background",
    "dropdown_background", "header_background", "tab_pane_background", "active_tab_background",
    "tooltip_background", "text", "muted_text", "selected_text", "disabled_text", "field_text",
    "heading_text", "tooltip_text", "accent", "border", "field_border", "group_border",
    "active_border", "button_hover", "selection_background", "focus_border", "disabled_border",
    "log_info", "log_success", "log_warning", "log_error", "support_link", "scrollbar_thumb",
    "scrollbar_hover", "checkbox_border", "checkbox_hover_border", "delete_background",
    "delete_hover", "delete_pressed", "delete_text", "delete_border", "donate_background",
    "donate_hover", "donate_border",
)

# Semantic aliases used in QSS and code, mapped to palette keys.
ALIASES = {
    "window": "window_background",
    "surface": "button_background",
    "field": "field_background",
    "recessed": "recessed_background",
    "popup": "dropdown_background",
    "hover": "button_hover",
    "selected": "selection_background",
    "focus": "focus_border",
    "pressed": "selection_background",
    "link": "support_link",
    "link_hover": "accent",
    "success": "log_success",
    "warning": "log_warning",
    "danger_text_status": "log_error",
    "danger": "delete_background",
    "danger_hover": "delete_hover",
    "danger_pressed": "delete_pressed",
    "danger_text": "delete_text",
    "scroll_track": "recessed_background",
    "scroll_thumb": "scrollbar_thumb",
    "scroll_hover": "scrollbar_hover",
    "scroll_pressed": "text",
    "disabled_surface": "button_background",
}


class ThemeError(ValueError):
    pass


def theme_dir(root):
    return os.path.join(root, "assets", "themes")


def list_themes(root):
    """[(theme_id, display_name)] for every readable palette file, Warm Graphite first."""
    folder = theme_dir(root)
    found = []
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if not name.endswith(".json"):
            continue
        theme_id = name[:-5]
        try:
            with open(os.path.join(folder, name), "r", encoding="utf-8") as handle:
                display = json.load(handle).get("name") or theme_id
        except (OSError, ValueError):
            continue
        found.append((theme_id, display))
    found.sort(key=lambda item: (item[0] != DEFAULT_THEME, item[1].lower()))
    return found


def load_document(root, theme_id):
    """Read a palette file by id. Ids are plain names; paths are never accepted."""
    if not re.match(r"^[a-z0-9_-]+$", theme_id or ""):
        raise ThemeError("Invalid theme id: {!r}".format(theme_id))
    path = os.path.join(theme_dir(root), theme_id + ".json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
    except OSError as error:
        raise ThemeError("Cannot read theme '{}': {}".format(theme_id, error))
    except ValueError as error:
        raise ThemeError("Theme '{}' is not valid JSON: {}".format(theme_id, error))
    validate(document)
    return document


def validate(document):
    if not isinstance(document, dict) or not isinstance(document.get("colors"), dict):
        raise ThemeError("Theme must be an object with a 'colors' object.")
    if not isinstance(document.get("name"), str) or not document["name"].strip():
        raise ThemeError("Theme needs a non-empty 'name'.")
    missing = [key for key in REQUIRED_KEYS if key not in document["colors"]]
    if missing:
        raise ThemeError("Theme is missing colors: " + ", ".join(missing))
    fallbacks = document.get("colorMan", {})
    if not isinstance(fallbacks, dict) or any(not _HEX.match(str(v)) for v in fallbacks.values()):
        raise ThemeError("Theme 'colorMan' fallbacks must be #rrggbb values.")
    overrides = document.get("light_colors", {})
    if not isinstance(overrides, dict) or any(key not in document["colors"] for key in overrides):
        raise ThemeError("Theme 'light_colors' may only override existing colors.")


def _channels(value):
    return [int(value[i:i + 2], 16) for i in (1, 3, 5)]


def mix(left, right, ratio):
    a, b = _channels(left), _channels(right)
    # int(x + 0.5) rounds half up on both 3.7 and 3.13, unlike round() banker's rounding.
    return "#" + "".join("{:02x}".format(int(x * (1 - ratio) + y * ratio + 0.5)) for x, y in zip(a, b))


def resolve(document, native_colors=None):
    """Return {key: "#rrggbb"} for every palette key plus every alias."""
    validate(document)
    colors = document["colors"]
    fallbacks = document.get("colorMan", {})
    native_colors = native_colors or {}

    def value_of(value, depth=0):
        if depth > 8:
            raise ThemeError("Theme color expression is nested too deeply.")
        if isinstance(value, str):
            if _HEX.match(value):
                return value.lower()
            if value.startswith("$"):
                key = value[1:]
                if key not in fallbacks:
                    raise ThemeError("Unknown native color: " + key)
                return value_of(native_colors.get(key, fallbacks[key]), depth + 1)
        if isinstance(value, dict) and set(value) == {"mix"}:
            parts = value["mix"]
            if isinstance(parts, list) and len(parts) == 3:
                left, right, ratio = parts
                if type(ratio) in (int, float) and math.isfinite(ratio) and 0 <= ratio <= 1:
                    return mix(value_of(left, depth + 1), value_of(right, depth + 1), ratio)
        raise ThemeError("Invalid theme color expression: {!r}".format(value))

    result = {key: value_of(value) for key, value in colors.items()}
    if fallbacks:
        # Host-color themes switch status colors when Max uses a light UI.
        red, green, blue = _channels(result["field_background"])
        if 0.2126 * red + 0.7152 * green + 0.0722 * blue > 150:
            result.update({key: value_of(value) for key, value in document.get("light_colors", {}).items()})
    for alias, key in ALIASES.items():
        result.setdefault(alias, result[key])
    return result


def render(template, colors):
    """Replace @role tokens. Unknown roles raise KeyError on purpose."""
    return _TOKEN.sub(lambda match: colors[match.group(1)], template)
```

## `python/mytool/ui/theme_manager.py`

```python
"""Applies one palette to every MyTool-owned window and notifies painted controls.

Selection is transactional: a broken palette file leaves the previous theme active and is reported.
"""

import hashlib
import os

from .. import logs, resources, settings, themes, ui_scale
from ..qt_compat import QtWidgets, inherit_fonts, is_valid, scale_font

_log = logs.get("theme")
# Icons referenced from QSS must be files; tinted copies live in the user data folder.
_QSS_ICONS = {
    "icon_check": ("check", "log_badge_text"),
    "icon_check_disabled": ("check", "disabled_text"),
    "icon_minus": ("minus", "log_badge_text"),  # Partly checked groups.
    "icon_minus_disabled": ("minus", "disabled_text"),
    "icon_chevron_down": ("chevron-down", "text"),
    "icon_chevron_down_disabled": ("chevron-down", "disabled_text"),
}
_NATIVE_KEYS = ("background", "window", "text", "windowText", "shadow", "hilight", "itemHilight",
                "hilightText", "rollupTitleFace", "rollupTitleText")


def sample_max_colors():
    """Current 3ds Max UI colors from colorMan (main thread only); {} outside Max."""
    try:
        from pymxs import runtime as rt
    except ImportError:
        return {}
    sampled = {}
    for key in _NATIVE_KEYS:
        try:
            value = rt.colorMan.getColor(rt.Name(key))
            sampled[key] = "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, int(round(c * 255))))
                                                         for c in (value.x, value.y, value.z)))
        except Exception:
            continue  # Unknown key in this Max version: the palette fallback is used.
    return sampled


def tinted_svg(name, color):
    with open(resources.require(resources.icon_path(name)), "r", encoding="utf-8") as handle:
        return handle.read().replace("currentColor", color)


class ThemeManager(object):
    def __init__(self, root, prefs):
        self.root = root
        self.prefs = prefs
        self.theme_id = None
        self.colors = {}
        self.windows = []
        self.listeners = []
        with open(resources.require(resources.ui_file("style.qss")), "r", encoding="utf-8") as handle:
            self.template = handle.read()
        self.stylesheet = ""

    # Registration -------------------------------------------------------------------------------
    def register(self, window):
        if window not in self.windows:
            self.windows.append(window)
        window.setStyleSheet(self.stylesheet)
        scale_font(window)  # Top-level windows do not inherit the font: interface size per window.
        inherit_fonts(window)

    def unregister(self, window):
        if window in self.windows:
            self.windows.remove(window)

    def subscribe(self, callback):
        self.listeners.append(callback)

    def unsubscribe(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def color(self, role):
        return self.colors[role]

    # Loading ------------------------------------------------------------------------------------
    def _build(self, theme_id):
        document = themes.load_document(self.root, theme_id)
        native = sample_max_colors() if "colorMan" in document else {}
        colors = themes.resolve(document, native)
        colors.update(self._write_qss_icons(theme_id, colors))
        return colors, ui_scale.scale_sheet(themes.render(self.template, colors))  # Interface size.

    def _write_qss_icons(self, theme_id, colors):
        digest = hashlib.sha1(repr(sorted(colors.items())).encode("utf-8")).hexdigest()[:10]
        folder = os.path.join(settings.user_data_dir(), "runtime", "icons", theme_id + "-" + digest)
        os.makedirs(folder, exist_ok=True)
        paths = {}
        for token, (name, role) in _QSS_ICONS.items():
            path = os.path.join(folder, token + ".svg")
            if not os.path.isfile(path):
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(tinted_svg(name, colors[role]))
            paths[token] = path.replace("\\", "/")  # QSS url() needs forward slashes.
        return paths

    def load_initial(self):
        wanted = self.prefs.get("theme") or themes.DEFAULT_THEME
        try:
            self.colors, self.stylesheet = self._build(wanted)
            self.theme_id = wanted
        except (themes.ThemeError, OSError) as error:
            _log.warning("Saved theme %r unusable (%s); using %s", wanted, error, themes.DEFAULT_THEME)
            self.colors, self.stylesheet = self._build(themes.DEFAULT_THEME)
            self.theme_id = themes.DEFAULT_THEME

    def select(self, theme_id):
        """Apply a theme everywhere. Returns an error string, or None on success."""
        try:
            colors, stylesheet = self._build(theme_id)
        except (themes.ThemeError, OSError, KeyError) as error:
            _log.warning("Theme %s rejected: %s", theme_id, error)
            return "Theme could not be loaded: {}".format(error)
        previous = (self.theme_id, self.colors, self.stylesheet)
        self.theme_id, self.colors, self.stylesheet = theme_id, colors, stylesheet
        try:
            self._apply()
        except Exception as error:
            _log.exception("Applying theme %s failed", theme_id)
            self.theme_id, self.colors, self.stylesheet = previous
            self._apply()
            return "Theme could not be applied: {}".format(error)
        self.prefs.set("theme", theme_id)
        try:
            self.prefs.save()
        except OSError as error:
            return "Theme applied but not saved: {}".format(error)
        return None

    def _apply(self):
        live = [window for window in self.windows if is_valid(window)]
        self.windows = live
        for window in live:
            window.setUpdatesEnabled(False)
        try:
            for window in live:
                window.setStyleSheet(self.stylesheet)
            for callback in list(self.listeners):
                callback(self.colors)
        finally:
            for window in live:
                window.setUpdatesEnabled(True)
                QtWidgets.QWidget.update(window)

    def dispose(self):
        self.listeners = []
        self.windows = []
```

## `python/mytool/ui/style.qss`

```css
/* Canonical tool stylesheet. Theme tokens (at-sign + role name) are replaced by the active theme and every pixel
   size is multiplied by the interface size (ui_scale.scale_sheet); never write an at-sign in comments here.
   Spacing scale: 4 8 12 16 24. Radii: 3 4 6 8. */

QWidget#toolWindow, QDialog#toolDialog { background: @window; color: @text; }
/* Default text colour with the lowest specificity (this sheet is set on the tool's windows only): an id-based
   descendant rule here would beat every variant / object-name colour (primary, danger, muted). */
QWidget { color: @text; }
QLabel { background: transparent; }
QLabel#toolSection { color: @heading_text; font-weight: bold; padding-top: 4px; }
QLabel#toolMuted { color: @muted_text; }
QLabel#toolCaption { color: @muted_text; font-size: 8pt; }
QLabel#toolError { color: @log_error; }
QLabel a { color: @link; }

QFrame#toolVDivider { background: @border; border: none; margin: 4px 2px; }
/* A content block of the main window (options panel, list area): rounded, outlined. */
QFrame#toolPanel { background: @tab_pane_background; border: 1px solid @group_border; border-radius: 8px; }
QFrame#toolPanel QFrame#toolPanelSection { background: @surface; border: 1px solid @border; border-radius: 6px; }
QFrame#toolAboutHero { background: @recessed; border: none; }
QFrame#toolAccentDivider { background: @accent; border: none; }
QLabel#toolAboutTitle { color: @heading_text; }
/* Warning boxes fade from the warning tint at the top to transparent at the bottom. */
QFrame#toolBanner { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 @log_warning_background,
                    stop: 1 transparent); border: 1px solid @log_warning; border-radius: 6px; }
QLabel#toolBannerTitle { color: @log_warning; font-weight: bold; }
QFrame#toolDanger { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 @log_error_background,
                    stop: 1 transparent); border: 1px solid @log_error; border-radius: 6px; }
QLabel#toolDangerTitle { color: @log_error; font-weight: bold; }

QToolTip { background: @tooltip_background; color: @tooltip_text; border: 1px solid @border; padding: 4px 6px; }

QPushButton { background: @surface; color: @text; border: 1px solid @border; border-radius: 6px;
  padding: 5px 12px; min-height: 18px; }
QPushButton:hover { background: @hover; border-color: @active_border; }
QPushButton:pressed { background: @pressed; }
QPushButton:focus { border-color: @focus; }
QPushButton:disabled { background: @disabled_surface; color: @disabled_text; border-color: @disabled_border; }
QPushButton:checked { background: @selected; color: @selected_text; border-color: @accent; }
QPushButton[variant="primary"] { background: @accent; color: @log_badge_text; border-color: @accent; font-weight: bold; }
QPushButton[variant="primary"]:hover { background: @focus; }
QPushButton[variant="primary"]:disabled { background: @disabled_surface; color: @disabled_text; border-color: @disabled_border; }
QPushButton[variant="danger"] { background: @danger; color: @danger_text; border-color: @delete_border; }
QPushButton[variant="danger"]:hover { background: @danger_hover; }
QPushButton[variant="danger"]:pressed { background: @danger_pressed; }
QPushButton[variant="ghost"] { background: transparent; border-color: transparent; padding: 5px 8px; }
QPushButton[variant="ghost"]:hover { background: @hover; border-color: @border; }
QPushButton[variant="donate"] { background: @donate_background; color: @status_button_text; border-color: @donate_border; }
QPushButton[variant="donate"]:hover { background: @donate_hover; }
/* Square icon-only buttons (title bar minimise / close, small row actions). */
QPushButton#toolIconButton { padding: 2px; min-height: 0px; background: @surface; border: 1px solid transparent;
  border-radius: 4px; }
QPushButton#toolIconButton:hover { background: @hover; border-color: @border; }
/* A real button inside a field's right end (search): background and hover colour. */
QPushButton#toolFieldButton { padding: 0px; min-height: 0px; background: @surface; border: 1px solid @border;
  border-radius: 4px; }
QPushButton#toolFieldButton:hover { background: @hover; border-color: @active_border; }
QPushButton#toolFieldButton:pressed { background: @pressed; }
QPushButton#toolFieldClear { padding: 0px; min-height: 0px; background: transparent; border: none; border-radius: 4px; }
QPushButton#toolFieldClear:hover { background: @hover; }
QPushButton#toolSoftButton { background: @surface; border: 1px solid transparent; padding: 3px 8px; text-align: left; }
QPushButton#toolSoftButton:hover { background: @hover; border-color: @border; }
QPushButton#toolSmallAction { font-size: 8pt; padding: 1px 6px; min-height: 0px; }
QPushButton#toolChevron { background: transparent; border: none; padding: 2px; min-height: 0px; }
QPushButton#toolChevron:hover { background: transparent; border: none; }
/* Segments keep full borders and overlap by 1 px (placed by hand); the checked one is raised so its accent border
   shows on every side. */
QPushButton[segment="first"] { border-top-right-radius: 0px; border-bottom-right-radius: 0px; }
QPushButton[segment="middle"] { border-radius: 0px; }
QPushButton[segment="last"] { border-top-left-radius: 0px; border-bottom-left-radius: 0px; }

/* Own title bar and the collapsed bar. */
QFrame#toolTitleBar { background: transparent; border: none; }
QLabel#toolWindowTitle { color: @accent; font-weight: bold; font-size: 10pt; }
QFrame#toolMiniBar { background: transparent; border: none; }
QPushButton#toolMiniTitle { background: transparent; border: none; color: @accent; font-weight: bold;
                            font-size: 10pt; padding: 3px 10px; text-align: left; }
QPushButton#toolMiniTitle:hover { background: @hover; border-radius: 4px; }

/* Settings: tabs and titled groups. The first tab sits on the pane's top-left corner: that corner is square, so the
   tab joins the pane. */
QTabWidget::pane { background: @tab_pane_background; border: 1px solid @tab_border; border-radius: 6px;
  border-top-left-radius: 0px; top: -1px; }
QTabBar::tab { background: @tab_background; color: @muted_text; border: 1px solid @tab_border; border-bottom: none;
  padding: 6px 18px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: @tab_pane_background; color: @text; }
QTabBar::tab:hover:!selected { background: @hover; }
QFrame#toolSettingsGroup { background: @active_tab_background; border: 1px solid @group_border; border-radius: 6px; }
QLabel#toolGroupTitle { color: @heading_text; font-weight: bold; font-size: 10pt; }

QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser { background: @field; color: @field_text; border: 1px solid @field_border;
  border-radius: 6px; padding: 4px 6px; selection-background-color: @selected; selection-color: @selected_text; }
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QTextBrowser:focus { border-color: @focus; }
QTextEdit#toolLogView { background: @recessed; border-color: @group_border; padding: 2px; }
QLineEdit:disabled { color: @disabled_text; border-color: @disabled_border; }
QAbstractSpinBox:disabled { color: @disabled_text; }
QLineEdit[readOnly="true"] { background: @recessed; }
/* A completer list continues its field: square bottom corners on the field while it is open. */
QLineEdit[open="true"] { border-color: @focus; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; }
QListView#toolSuggest { background: @field; color: @field_text; border: 1px solid @focus; border-top: 1px solid @field_border;
  border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; padding: 2px 0px 5px 0px; outline: 0; }
/* A dropdown panel (rows highlight by background only). */
QFrame#toolDropdown { background: @field; border: 1px solid @border; border-radius: 6px; }
QFrame#toolPopupRow { background: transparent; border: none; }
QFrame#toolPopupRow:hover { background: @selected; }
QFrame#toolPopupDivider { background: @border; border: none; margin: 2px 8px; }
/* Lists: a rounded field; rows highlight by background (rounded) without a focus rectangle. */
QListWidget { background: @field; color: @field_text; border: 1px solid @field_border; border-radius: 6px;
  padding: 4px; outline: 0; }
QListWidget::item { padding: 4px 8px; border-radius: 4px; }
QListWidget::item:hover { background: @hover; }
QListWidget::item:selected { background: @selected; color: @selected_text; }
QTableWidget#toolTable { background: @field; alternate-background-color: @surface; color: @field_text;
  border: 1px solid @field_border; border-radius: 6px; selection-background-color: @selected;
  selection-color: @selected_text; outline: 0; }
QTableWidget#toolTable::item { padding: 3px 8px; border: none; }
QHeaderView::section { background: @surface; color: @muted_text; border: none; border-bottom: 1px solid @border;
  padding: 4px 8px; }

QCheckBox { spacing: 7px; background: transparent; }
QCheckBox::indicator { width: 13px; height: 13px; border: 1px solid @checkbox_border; border-radius: 3px; background: @recessed; }
QCheckBox::indicator:hover { border-color: @checkbox_hover_border; }
QCheckBox::indicator:checked { background: @accent; border-color: @accent; image: url(@icon_check); }
QCheckBox::indicator:disabled { background: @disabled_surface; border-color: @disabled_border; }
QCheckBox::indicator:checked:disabled { image: url(@icon_check_disabled); }
QCheckBox::indicator:indeterminate { background: @accent; border-color: @accent; image: url(@icon_minus); }
QCheckBox::indicator:indeterminate:disabled { background: @disabled_surface; border-color: @disabled_border; image: url(@icon_minus_disabled); }
QCheckBox:disabled { color: @disabled_text; }

QComboBox { background: @field; color: @field_text; border: 1px solid @field_border; border-radius: 6px;
  padding: 4px 26px 4px 8px; min-height: 18px; }
QComboBox:hover { border-color: @active_border; }
QComboBox:focus { border-color: @focus; }
QComboBox:disabled { color: @disabled_text; border-color: @disabled_border; }
QComboBox::drop-down { width: 24px; border: none; background: transparent; subcontrol-origin: padding; subcontrol-position: center right; }
QComboBox::down-arrow { image: url(@icon_chevron_down); width: 12px; height: 12px; }
QComboBox::down-arrow:disabled { image: url(@icon_chevron_down_disabled); }
QListView#toolPopup { background: @popup; color: @text; border: 1px solid @border; padding: 4px; outline: 0; }
QListView#toolPopup::item { padding: 4px 10px; border-radius: 4px; min-height: 20px; }
QListView#toolPopup::item:selected, QListView#toolPopup::item:hover { background: @selected; color: @selected_text; }

/* Scroll bars: thin, no visible track, a pill thumb rounded over its whole width. Bar 10 px, thumb margin 2 px, so the
   thumb is 6 px and its radius 3 px is exactly half of it. Keep that ratio: every px here is scaled and rounded on
   its own (ui_scale), and Qt draws a square thumb when the radius is more than half its width. Hover and press only
   change the thumb's colour. */
QScrollBar:vertical { width: 10px; background: transparent; border: none; margin: 0px; }
QScrollBar:horizontal { height: 10px; background: transparent; border: none; margin: 0px; }
QScrollBar::handle:vertical { background: @scroll_thumb; min-height: 28px; border-radius: 3px; margin: 2px; }
QScrollBar::handle:horizontal { background: @scroll_thumb; min-width: 28px; border-radius: 3px; margin: 2px; }
QScrollBar::handle:hover { background: @scroll_hover; }
QScrollBar::handle:pressed { background: @scroll_pressed; }
QScrollBar::add-page, QScrollBar::sub-page { background: none; border: none; }
QScrollBar::add-line, QScrollBar::sub-line { background: none; border: none; width: 0; height: 0; }
QScrollBar::up-arrow, QScrollBar::down-arrow, QScrollBar::left-arrow, QScrollBar::right-arrow { image: none; width: 0; height: 0; }
QAbstractScrollArea::corner { background: transparent; border: none; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }

QGroupBox { border: 1px solid @group_border; border-radius: 6px; margin-top: 14px; padding: 10px 8px 8px 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: @heading_text; }

QPushButton::menu-indicator { image: none; width: 0px; }
QMenu { background: @popup; color: @text; border: 1px solid @border; padding: 4px; }
QMenu::item { padding: 5px 18px 5px 10px; border-radius: 4px; }
QMenu::item:selected { background: @selected; color: @selected_text; }
QMenu::item:disabled { color: @disabled_text; }
QMenu::separator { height: 1px; background: @border; margin: 4px 6px; }
```
