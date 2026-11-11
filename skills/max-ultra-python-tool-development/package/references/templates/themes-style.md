# Template: Palettes, theme manager and the style sheet

Palette JSON resolution (aliases, mixes, Max colorMan samples) and the derived shades of disabled coloured buttons (`themes.derived`), transactional theme switching for every registered window (fonts kept at the interface size after the new sheet re-polishes them), tinted icon files for QSS, and the canonical style sheet with `@role` tokens.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP, with the windows off screen.

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


def derived(colors):
    """Colours computed from the palette. A disabled coloured button (primary, danger) is a darker shade of its own
    colour with text and icon in a lighter shade of it: colour is never mixed with grey."""
    base = colors["tab_pane_background"]
    return {
        "accent_disabled": mix(base, colors["accent"], 0.30),
        "accent_disabled_border": mix(base, colors["accent"], 0.45),
        "accent_disabled_text": colors["accent"],
        "danger_disabled": mix(base, colors["danger"], 0.40),
        "danger_disabled_border": mix(base, colors["delete_border"], 0.40),
        "danger_disabled_text": colors["delete_border"],
    }


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
        colors.update(themes.derived(colors))  # Disabled coloured buttons: shades of their own colour
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
                inherit_fonts(window)  # The new sheet re-polished every widget: some got the default font back
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
QLabel#toolSection { color: @heading_text; font-weight: bold; }
QLabel#toolMuted { color: @muted_text; }
QLabel#toolCaption { color: @muted_text; font-size: 8pt; }
QLabel#toolRequired { color: @log_error; font-weight: bold; }  /* The * of a field that must be filled in */
QLabel#toolError { color: @log_error; }
QLabel a { color: @link; }

QFrame#toolVDivider { background: @border; border: none; margin: 4px 2px; }
/* A content block of the main window (options panel, list area): rounded, outlined. */
QFrame#toolPanel { background: @tab_pane_background; border: 1px solid @group_border; border-radius: 8px; }
QFrame#toolPanel QFrame#toolPanelSection { background: @surface; border: 1px solid @border; border-radius: 6px; }
/* About's hero: a gradient from the window colour (where the header shade ends) down to the recessed colour at the
   accent line, so the shade and the plate meet without a step. */
QFrame#toolAboutHero { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 @window, stop: 1 @recessed);
  border: none; }
QFrame#toolAccentDivider { background: @accent; border: none; }
QFrame#toolRule { background: @border; border: none; }
/* About: How to use in a card of its own (its numbered badges are painted: controls.NumberBadge). */
QFrame#toolHowTo { background: @tab_pane_background; border: 1px solid @group_border; border-radius: 8px; }
QLabel#toolAboutTitle { color: @heading_text; }
/* Warning boxes fade from the warning tint at the top to transparent at the bottom. */
QFrame#toolBanner { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 @log_warning_background,
                    stop: 1 transparent); border: 1px solid @log_warning; border-radius: 6px; }
QLabel#toolBannerTitle { color: @log_warning; font-weight: bold; }
QFrame#toolDanger { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 @log_error_background,
                    stop: 1 transparent); border: 1px solid @log_error; border-radius: 6px; }
QLabel#toolDangerTitle { color: @log_error; font-weight: bold; }

/* Qt's own tooltip: the help balloon's outline colour, so it shows on every side over dark panels; square corners and
   the system shadow stay. */
QToolTip { background: @tooltip_background; color: @tooltip_text; border: 1px solid @active_border; border-radius: 6px;
  padding: 4px 6px; }  /* Rounded by a window mask too (controls.round_tooltip) */

QPushButton { background: @surface; color: @text; border: 1px solid @border; border-radius: 6px;
  padding: 4px 12px; min-height: 18px; }
QPushButton:hover { background: @hover; border-color: @active_border; }
QPushButton:pressed { background: @pressed; }
QPushButton:focus { border-color: @focus; outline: none; }  /* The focus colour is the sign; no dotted frame */
QPushButton:disabled { background: @disabled_surface; color: @disabled_text; border-color: @disabled_border; }
QPushButton:checked { background: @selected; color: @selected_text; border-color: @accent; }
QPushButton[variant="primary"] { background: @accent; color: @log_badge_text; border-color: @accent; font-weight: bold; }
QPushButton[variant="primary"]:hover { background: @focus; }
QPushButton[variant="primary"]:disabled { background: @accent_disabled; color: @accent_disabled_text;
  border-color: @accent_disabled_border; }
QPushButton[variant="danger"] { background: @danger; color: @danger_text; border-color: @delete_border; }
QPushButton[variant="danger"]:hover { background: @danger_hover; }
QPushButton[variant="danger"]:pressed { background: @danger_pressed; }
/* Disabled coloured buttons stay in their colour (a darker shade, themes.derived), never grey. */
QPushButton[variant="danger"]:disabled { background: @danger_disabled; color: @danger_disabled_text;
  border-color: @danger_disabled_border; }
QPushButton[variant="ghost"] { background: transparent; border-color: transparent; padding: 4px 8px; }
QPushButton[variant="ghost"]:hover { background: @hover; border-color: @border; }
/* The title of a collapsible group: a panel title, not a button. Hover changes only the colour. */
QPushButton#toolGroupHeader { background: transparent; border: 1px solid transparent; color: @heading_text;
  font-weight: bold; padding: 2px 4px; text-align: left; }
QPushButton#toolGroupHeader:hover, QPushButton#toolGroupHeader:pressed, QPushButton#toolGroupHeader:checked {
  background: transparent; border-color: transparent; }
QPushButton#toolGroupHeader:hover { color: @text; }
QPushButton[variant="donate"] { background: @donate_background; color: @status_button_text; border-color: @donate_border; }
QPushButton[variant="donate"]:hover { background: @donate_hover; }
/* Title-bar buttons (controls.WindowButton): 28 px circles, transparent at rest, a soft circle on hover. Close turns
   red on hover with a light edge (the same red in every theme); its cross turns white. The collapsed bar's close is
   22 px through the "compact" property (never "size": a Qt property of every widget, so the rule would not match). */
QPushButton#toolIconButton { min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; padding: 0px;
  border: 1px solid transparent; border-radius: 14px; background: transparent; }
QPushButton#toolIconButton[compact="true"] { min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px;
  border-radius: 11px; }
QPushButton#toolIconButton:hover { background: @hover; border-color: @border; }
QPushButton#toolIconButton[role="close"]:hover { background: #9f3636; border-color: rgba(230, 120, 120, 150); }
QPushButton#toolIconButton[role="close"]:pressed { background: #842d2d; border-color: rgba(230, 120, 120, 110); }
/* A real button inside a field's right end (search): background and hover colour. */
QPushButton#toolFieldButton { padding: 0px; min-height: 0px; background: @surface; border: 1px solid @border;
  border-radius: 4px; }
QPushButton#toolFieldButton:hover { background: @hover; border-color: @active_border; }
QPushButton#toolFieldButton:pressed { background: @pressed; }
QPushButton#toolFieldClear { padding: 0px; min-height: 0px; background: transparent; border: none; border-radius: 4px; }
QPushButton#toolFieldClear:hover { background: @hover; }
QPushButton#toolSoftButton { background: @surface; border: 1px solid transparent; padding: 4px 8px; text-align: left; }
QPushButton#toolSoftButton:hover { background: @hover; border-color: @border; }
QPushButton#toolSmallAction { font-size: 8pt; padding: 2px 6px; min-height: 0px; }
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
QPushButton#toolMiniTitle { background: transparent; border: none; color: @text; font-size: 9pt; padding: 2px 6px;
                            text-align: left; }
QPushButton#toolMiniTitle:hover { background: @hover; border-radius: 4px; }

/* Settings: tabs and titled groups. The first tab sits on the pane's top-left corner: that corner is square, so the
   tab joins the pane. */
QTabWidget::pane { background: @tab_pane_background; border: 1px solid @tab_border; border-radius: 6px;
  border-top-left-radius: 0px; top: -1px; }
QTabBar::tab { background: @tab_background; color: @muted_text; border: 1px solid @tab_border; border-bottom: none;
  padding: 6px 16px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: @tab_pane_background; color: @text; }
QTabBar::tab:hover:!selected { background: @hover; }
QFrame#toolSettingsGroup { background: @active_tab_background; border: 1px solid @group_border; border-radius: 6px; }
QLabel#toolGroupTitle { color: @heading_text; font-weight: bold; font-size: 10pt; }

QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser { background: @field; color: @field_text; border: 1px solid @field_border;
  border-radius: 6px; padding: 4px 6px; selection-background-color: @selected; selection-color: @selected_text; }
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QTextBrowser:focus { border-color: @focus; }
QLineEdit:disabled { color: @disabled_text; border-color: @disabled_border; }
QAbstractSpinBox:disabled { color: @disabled_text; }
QLineEdit[readOnly="true"] { background: @recessed; }
/* A completer list continues its field: square bottom corners on the field while it is open. */
QLineEdit[open="true"] { border-color: @focus; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; }
QListView#toolSuggest { background: @field; color: @field_text; border: 1px solid @focus; border-top: 1px solid @field_border;
  border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; padding: 2px 0px 4px 0px; outline: 0; }
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
QTableWidget#toolTable::item { padding: 4px 8px; border: none; }
QHeaderView::section { background: @surface; color: @muted_text; border: none; border-bottom: 1px solid @border;
  padding: 4px 8px; }

QCheckBox { spacing: 8px; background: transparent; }
QCheckBox::indicator { width: 13px; height: 13px; border: 1px solid @checkbox_border; border-radius: 3px; background: @recessed; }
QCheckBox::indicator:hover { border-color: @checkbox_hover_border; }
QCheckBox::indicator:checked { background: @accent; border-color: @accent; image: url(@icon_check); }
QCheckBox::indicator:disabled { background: @disabled_surface; border-color: @disabled_border; }
QCheckBox::indicator:checked:disabled { image: url(@icon_check_disabled); }
QCheckBox::indicator:indeterminate { background: @accent; border-color: @accent; image: url(@icon_minus); }
QCheckBox::indicator:indeterminate:disabled { background: @disabled_surface; border-color: @disabled_border; image: url(@icon_minus_disabled); }
QCheckBox:disabled { color: @disabled_text; }

QComboBox { background: @field; color: @field_text; border: 1px solid @field_border; border-radius: 6px;
  padding: 4px 24px 4px 8px; }  /* Height: controls.unify_heights; the right padding is the arrow's room */
QComboBox:hover { border-color: @active_border; }
QComboBox:focus { border-color: @focus; }
QComboBox:disabled { color: @disabled_text; border-color: @disabled_border; }
QComboBox::drop-down { width: 24px; border: none; background: transparent; subcontrol-origin: padding; subcontrol-position: center right; }
QComboBox::down-arrow { image: url(@icon_chevron_down); width: 12px; height: 12px; }
QComboBox::down-arrow:disabled { image: url(@icon_chevron_down_disabled); }
QListView#toolPopup { background: @popup; color: @text; border: 1px solid @border; border-radius: 6px; padding: 4px;
  outline: 0; }  /* The popup window itself is rounded by a mask (controls.round_popup) */
QListView#toolPopup::item { padding: 4px 8px; border-radius: 4px; min-height: 20px; }
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

QGroupBox { border: 1px solid @group_border; border-radius: 6px; margin-top: 16px; padding: 12px 8px 8px 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: @heading_text; }

QPushButton::menu-indicator { image: none; width: 0px; }
QMenu { background: @popup; color: @text; border: 1px solid @border; border-radius: 6px; padding: 4px; }
QMenu::item { padding: 6px 16px 6px 8px; border-radius: 4px; }
QMenu::item:selected { background: @selected; color: @selected_text; }
QMenu::item:disabled { color: @disabled_text; }
QMenu::separator { height: 1px; background: @border; margin: 4px 6px; }
/* Menu items (controls.Menu.add_item): Lucide icon and text, a rounded highlight; destructive items are red. */
QPushButton#toolMenuItem { background: transparent; border: none; border-radius: 4px; text-align: left;
  padding: 6px 16px 6px 8px; min-width: 120px; }
QPushButton#toolMenuItem[current="true"] { background: @selected; color: @selected_text; }
QPushButton#toolMenuItem:disabled { background: transparent; color: @disabled_text; }
QPushButton#toolMenuItem[danger="true"] { color: @log_error; }
QPushButton#toolMenuItem[danger="true"][current="true"] { background: @danger; color: @danger_text; }
QPushButton#toolMenuItem[danger="true"]:pressed { background: @danger_pressed; color: @danger_text; }
QLabel#toolMenuShortcut { color: @muted_text; background: transparent; }
QLabel#toolMenuShortcut[current="true"] { color: @selected_text; }
QLabel#toolMenuShortcut[danger="true"][current="true"] { color: @danger_text; }
/* A copy button that just copied: the green check and a green outline (inputs.CopyButton). */
QPushButton[done="true"], QPushButton[done="true"]:hover, QPushButton[done="true"]:focus { border-color: @log_success; }

/* Lists and multi-line text boxes sit in a field frame (controls.boxed): the frame draws border, focus and error. */
QFrame#toolBox { background: @field; border: 1px solid @field_border; border-radius: 6px; }
QFrame#toolBox[focused="true"] { border-color: @focus; }
QFrame#toolBox[invalid="true"] { border-color: @log_error; }
QFrame#toolBox QListWidget, QFrame#toolBox QPlainTextEdit, QFrame#toolBox QTextEdit, QFrame#toolBox QTableWidget {
  border: none; background: transparent; }
/* The mini log: no padding, so a row's tint reaches the box's border; the text keeps its inset (frame margins). */
QFrame#toolBox QTextEdit#toolStatusView { padding: 0px; }

/* A required field that is empty or wrong: red outline; controls.ErrorHints shows why in a red bubble. */
QLineEdit[invalid="true"], QPlainTextEdit[invalid="true"], QComboBox[invalid="true"], QListWidget[invalid="true"],
QPushButton[variant="field"][invalid="true"], QFrame#toolStepper[invalid="true"] { border-color: @log_error; }

/* Pickers (ui/pickers.py): a date field that looks like the other fields, calendar days, the number stepper. */
QPushButton[variant="field"] { background: @field; color: @field_text; border: 1px solid @field_border; border-radius: 6px;
  padding: 4px 8px; text-align: left; }
QPushButton[variant="field"]:hover { border-color: @active_border; }
QPushButton[variant="field"]:focus, QPushButton[variant="field"][open="true"] { border-color: @focus; }
QPushButton[variant="field"]:disabled { color: @disabled_text; border-color: @disabled_border; }
QWidget#toolCalendar { background: transparent; }
QFrame#toolCalendarFrame { background: @field; border: 1px solid @border; border-radius: 8px; }
QPushButton#toolCalendarTitle { background: transparent; border: 1px solid transparent; border-radius: 6px;
  color: @heading_text; font-weight: bold; padding: 0px 8px; }
QPushButton#toolCalendarTitle:hover { background: @hover; }
QPushButton#toolCalendarTitle:disabled { background: transparent; color: @heading_text; }
QLabel#toolCalendarWeekday { color: @muted_text; font-size: 8pt; }
QPushButton#toolDay { background: transparent; border: 1px solid transparent; border-radius: 6px; color: @text; padding: 0px;
  min-width: 28px; min-height: 26px; max-height: 26px; }
QPushButton#toolCalendarCell { background: transparent; border: 1px solid transparent; border-radius: 6px; color: @text;
  padding: 0px; min-width: 56px; min-height: 40px; max-height: 40px; }
QPushButton#toolDay:hover, QPushButton#toolCalendarCell:hover { background: @hover; }
QPushButton#toolDay[state="other"] { color: @disabled_text; }
QPushButton#toolDay[state="today"], QPushButton#toolCalendarCell[state="today"] { border-color: @accent; }
QPushButton#toolDay[state="selected"], QPushButton#toolCalendarCell[state="selected"] { background: @accent;
  color: @log_badge_text; border-color: @accent; }
QPushButton#toolDay:disabled, QPushButton#toolCalendarCell:disabled { background: transparent; color: @disabled_text;
  border-color: transparent; }
QLabel#toolTimeColon { color: @muted_text; font-weight: bold; }
/* Number stepper: one rounded field, the arrows stacked inside its right edge. */
QFrame#toolStepper { background: @field; border: 1px solid @field_border; border-radius: 6px; }
QFrame#toolStepper:hover { border-color: @active_border; }
QFrame#toolStepper[focused="true"] { border-color: @focus; }
QLineEdit#toolStepValue { background: transparent; border: none; padding: 4px 2px 4px 6px; min-height: 20px; }
QPushButton#toolStepArrow { background: transparent; border: none; border-radius: 3px; padding: 0px;
  min-width: 18px; max-width: 18px; min-height: 12px; max-height: 12px; }
QPushButton#toolStepArrow:hover { background: @hover; }
QPushButton#toolStepArrow:pressed { background: @pressed; }

/* The status bar's text action (controls.StatusAction, "View Logs"), as in MaxPkg Runtime Manager: muted 11 px text,
   no background or frame; on hover only the colour changes. Its 12 px icon stays muted. */
QPushButton#toolStatusAction { color: @muted_text; font-size: 11px; border: none; background: transparent;
  padding: 0px 2px; }
QPushButton#toolStatusAction:hover, QPushButton#toolStatusAction:pressed { color: @text; background: transparent;
  border: none; }

/* Toasts (ui/toast.py) paint their own card; only the texts and the close button are styled here. */
QFrame#toolToast { background: transparent; border: none; }
QLabel#toolToastTitle { color: @text; font-size: 13px; font-weight: bold; }
QLabel#toolToastBody { color: @muted_text; font-size: 12px; }
QPushButton#toolToastClose { border: none; border-radius: 11px; background: transparent; padding: 0px;
  min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px; }
QPushButton#toolToastClose:hover { background: @hover; }

/* Sections as a list on the left (ui/sections.py), as the MaxPkg Package Manager's Settings: a recessed column, the
   chosen section on a soft highlight, a destructive one in red. The page title sits above each page. */
QFrame#toolNav { background: @recessed; border: none; border-right: 1px solid @border; border-bottom-left-radius: 8px; }
QPushButton#toolNavButton { background: transparent; color: @muted_text; border: 1px solid transparent;
  border-radius: 6px; padding: 8px 12px; text-align: left; }
QPushButton#toolNavButton:hover { background: @surface; color: @text; border-color: transparent; }
QPushButton#toolNavButton:checked { background: @hover; color: @text; border-color: @border; }
QPushButton#toolNavButton[danger="true"] { color: @log_error; }
QPushButton#toolNavButton[danger="true"]:checked { background: @log_error_background; color: @log_error;
  border-color: @log_error; }
QLabel#toolPageTitle { color: @heading_text; font-weight: bold; font-size: 11pt; }

/* The colour popup (ui/colors.py): a rounded card; the window around it is masked (controls.round_popup). */
QWidget#toolColorPopup { background: transparent; }
QFrame#toolPopupFrame { background: @popup; border: 1px solid @border; border-radius: 8px; }

/* Whole-area states (ui/states.py) paint their own cards. */
QFrame#toolBusyCard, QFrame#toolEmptyState { background: transparent; border: none; }

/* Cards (ui/cards.py): the outline brightens under the pointer; the whole card is clickable. */
QFrame#toolCard { background: @tab_pane_background; border: 1px solid @group_border; border-radius: 8px; }
QFrame#toolCard:hover { border-color: @accent; }
/* The gallery's thumbnails (ui/gallery.py): rounded, the current one framed in the accent colour; the strip scrolls
   by dragging. Its picture, buttons, counter and the lightbox are painted. */
QPushButton#toolThumb { border: 1px solid @border; border-radius: 6px; background: @surface; padding: 2px; }
QPushButton#toolThumb:hover { border-color: @active_border; }
QPushButton#toolThumb:checked { border-color: @accent; background: @surface; }
QScrollArea#toolThumbArea, QWidget#toolThumbStrip { background: transparent; border: none; }
/* A filter that differs from its default (inputs.ClearableComboBox): an accent outline. */
QComboBox[active="true"] { border-color: @accent; }
/* A pick button while 3ds Max's pick mode runs (inputs.PickButton). */
QPushButton[picking="true"] { border-color: @accent; color: @accent; }
/* A scene tree (tree.SceneTree): a list's field frame, theme chevrons for the layers, check boxes as everywhere. */
QTreeWidget#toolTree { background: @field; color: @field_text; border: 1px solid @field_border; border-radius: 6px;
  padding: 4px; outline: 0; selection-background-color: transparent; selection-color: @selected_text; }
/* A row's highlight is one rounded bar from its check box to the right edge, drawn by tree.SceneTree.drawRow: the
   indent stays unlit and the column seam shows no notch. The style sheet's own item fills stay transparent. */
QTreeWidget#toolTree { show-decoration-selected: 0; }
QTreeWidget#toolTree::item { padding: 2px 4px; border-radius: 0px; min-height: 22px; background: transparent; }
QTreeWidget#toolTree::item:hover { background: transparent; }
QTreeWidget#toolTree::item:selected { background: transparent; color: @selected_text; }
QTreeWidget#toolTree::branch, QTreeWidget#toolTree::branch:hover, QTreeWidget#toolTree::branch:selected {
  background: transparent; }
QFrame#toolBox QTreeWidget#toolTree { border: none; background: transparent; }
/* Check boxes inside lists, trees and dropdown lists look like the tool's check boxes. */
QTreeWidget::indicator, QListWidget::indicator, QListView#toolPopup::indicator { width: 13px; height: 13px;
  border: 1px solid @checkbox_border; border-radius: 3px; background: @recessed; }
QTreeWidget::indicator:checked, QListWidget::indicator:checked, QListView#toolPopup::indicator:checked {
  background: @accent; border-color: @accent; image: url(@icon_check); }
QTreeWidget::indicator:indeterminate, QListWidget::indicator:indeterminate { background: @accent;
  border-color: @accent; image: url(@icon_minus); }
/* Choices as cards (combos.RadioCards): the chosen card has the accent border. */
QFrame#toolRadioCard { background: @field; border: 1px solid @field_border; border-radius: 8px; }
QFrame#toolRadioCard:hover { border-color: @active_border; }
QFrame#toolRadioCard:focus { border-color: @focus; }
QFrame#toolRadioCard[checked="true"] { background: @surface; border-color: @accent; }
QLabel#toolRadioTitle { color: @text; font-weight: bold; background: transparent; }
/* A place to drop files (tree.DropZone): dashed while waiting, accent for files it takes, red for files it does not. */
QFrame#toolDropZone { background: @recessed; border: 1px dashed @border; border-radius: 8px; }
QFrame#toolDropZone[state="over"] { background: @surface; border: 1px solid @accent; }
QFrame#toolDropZone[state="reject"] { border: 1px solid @log_error; }
QLabel#toolDropTitle { color: @text; font-weight: bold; background: transparent; }
/* Stat tiles (charts.StatTile): a quiet panel; the number is the loud part. */
QFrame#toolStatTile { background: @field; border: 1px solid @field_border; border-radius: 8px; }
/* The text field inside an editable dropdown (combos.editable_combo): the dropdown's frame is the field. */
QComboBox QLineEdit { background: transparent; border: none; padding: 0px; }
QComboBox:editable { padding-left: 4px; }  /* The text field adds its own inset: the text starts where a dropdown's does */
```
