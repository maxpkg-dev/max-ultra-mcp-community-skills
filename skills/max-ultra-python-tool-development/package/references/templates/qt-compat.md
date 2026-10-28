# Template: PySide2 / PySide6 compatibility and Max integration helpers

The only module that picks the Qt binding. Also: live screens by position (never `widget.screen()`), work areas, the active viewport rectangle, bounded window positions, safe re-polish, interface-size fonts, DWM rounded corners, Max hotkey ownership and the safe-mode switch.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `python/mytool/qt_compat.py`

```python
"""The single place that chooses the Qt binding and hides PySide2/PySide6 differences.

PySide6 is used when it is installed (Max 2025+), otherwise PySide2 (Max 2022-2024). Only the absence of
PySide6 triggers the fallback: a broken PySide6 raises instead of silently mixing binding families.
"""

import importlib.util

if importlib.util.find_spec("PySide6") is not None:
    from PySide6 import QtCore, QtGui, QtWidgets, QtSvg  # noqa: F401
    from PySide6.QtWebChannel import QWebChannel  # noqa: F401
    from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings  # noqa: F401
    from PySide6.QtGui import QAction, QShortcut  # noqa: F401
    import shiboken6 as _shiboken
    BINDING = "PySide6"
else:
    from PySide2 import QtCore, QtGui, QtWidgets, QtSvg  # noqa: F401
    from PySide2.QtWebChannel import QWebChannel  # noqa: F401
    from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings  # noqa: F401
    from PySide2.QtWidgets import QAction, QShortcut  # noqa: F401
    import shiboken2 as _shiboken
    BINDING = "PySide2"

Qt = QtCore.Qt
Signal = QtCore.Signal
Slot = QtCore.Slot


def qt_version():
    return QtCore.qVersion()


def is_valid(obj):
    """False when the C++ object behind a Python wrapper was deleted."""
    try:
        return obj is not None and _shiboken.isValid(obj)
    except Exception:
        return False


def exec_dialog(dialog):
    method = getattr(dialog, "exec", None) or getattr(dialog, "exec_")
    return method()


def max_main_window():
    """Max's main window for parenting, or None outside Max (standalone tests)."""
    try:
        import qtmax
    except ImportError:
        return None
    getter = getattr(qtmax, "GetQMaxMainWindow", None)
    return getter() if getter else None


# Safe start (startguard): after a start that took 3ds Max down, the optional extras that call into Max or Windows
# for our windows (own hotkey handling, DWM corners) are left out.
SAFE = {"on": False}


def own_keyboard(widgets):
    """Inside Max: while one of these widgets has the keyboard focus, Max's own hotkeys are off, so keys such
    as Esc, Delete or R reach MyTool instead of 3ds Max. No-op
    outside Max, where qtmax lacks the call, or in safe mode."""
    if SAFE["on"]:
        return 0
    try:
        import qtmax
    except ImportError:
        return 0
    disable = getattr(qtmax, "DisableMaxAcceleratorsOnFocus", None)
    if disable is None:
        return 0
    count = 0
    for widget in widgets:
        try:
            disable(widget, True)
            count += 1
        except Exception:  # A widget being destroyed; the rest still get it.
            pass
    return count


def live_screens():
    """[(screen, work area, geometry)] of every screen in Qt's current list; screens whose wrapper is dead are left out.

    Never ask a widget for its screen(): 3ds Max 2024's main window handed back a QScreen that was already gone
    ("Internal C++ object (PySide2.QtGui.QScreen) already deleted" at a user's MyTool start, 2026-10-26), and the
    next start crashed Max with an access violation, most likely through the same stale screen. Qt's own list of
    screens is current: look positions up in it.
    """
    result = []
    try:
        screens = QtGui.QGuiApplication.screens()
    except RuntimeError:
        return result
    for screen in screens:
        try:
            result.append((screen, QtCore.QRect(screen.availableGeometry()), QtCore.QRect(screen.geometry())))
        except RuntimeError:
            continue
    return result


def screen_at(point):
    """(screen, work area, geometry) of the live screen nearest to the global `point`; (None, None, None) without
    screens."""
    def distance(entry):
        geometry = entry[2]
        x = max(geometry.left(), min(point.x(), geometry.right()))
        y = max(geometry.top(), min(point.y(), geometry.bottom()))
        return (point.x() - x) ** 2 + (point.y() - y) ** 2

    screens = live_screens()
    return min(screens, key=distance) if screens else (None, None, None)


def work_area(point):
    """The work area (screen without the taskbar) of the screen nearest to the global `point`, or None."""
    return screen_at(point)[1]


def active_viewport_rect():
    """The active 3ds Max viewport on screen in Qt pixels, or None outside Max or when Windows cannot tell.

    Windows reports device pixels; Max turns Qt's high-DPI scaling off, so they are Qt pixels there, but the ratio of
    the live screen under the viewport is applied anyway (never a window's screen(), see live_screens).
    """
    try:
        import ctypes
        from ctypes import wintypes
        from pymxs import runtime as rt
        hwnd = int(rt.viewport.getHWnd())
        rect = wintypes.RECT()
        if not hwnd or not ctypes.windll.user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
            return None
    except Exception:  # Outside Max (no pymxs), or a Max without the call.
        return None
    if rect.right <= rect.left or rect.bottom <= rect.top:
        return None
    ratio = 1.0
    screen = screen_at(QtCore.QPoint((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2))[0]
    if screen is not None:
        try:
            ratio = float(screen.devicePixelRatio()) or 1.0
        except RuntimeError:
            ratio = 1.0
    return QtCore.QRect(int(rect.left / ratio), int(rect.top / ratio), int((rect.right - rect.left) / ratio),
                        int((rect.bottom - rect.top) / ratio))


def primary_work_area():
    """The primary screen's work area; any live screen's, or a Full HD guess, when Qt cannot tell."""
    try:
        return QtCore.QRect(QtGui.QGuiApplication.primaryScreen().availableGeometry())
    except (RuntimeError, AttributeError):
        screens = live_screens()
        return screens[0][1] if screens else QtCore.QRect(0, 0, 1920, 1040)


def bounded_window_position(position, size, anchor=None):
    """`position` moved so a window of `size` stays inside the work area (the screen without the taskbar) of
    the screen nearest to `anchor` (default: the window's centre). As in Max Ultra MCP's collapsed panel."""
    target = anchor if anchor is not None else position + QtCore.QPoint(size.width() // 2, size.height() // 2)
    area = work_area(target)
    if area is None:
        return position
    return QtCore.QPoint(max(area.left(), min(position.x(), area.right() - size.width() + 1)),
                         max(area.top(), min(position.y(), area.bottom() - size.height() + 1)))


def repolish(widget):
    """Re-apply the style sheet rules to `widget` after its object name or a property changed.

    `widget.style()` can hand back a wrapper whose C++ style is already gone ("Internal C++ object
    (PySide6.QtWidgets.QCommonStyle) already deleted": a user's Max 2026 at MyTool's start, 2026-10-26, probably
    after another tool replaced the application style). Then setting the widget's own style sheet makes Qt re-polish
    it through its live style, without that wrapper.
    """
    try:
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
    except RuntimeError:
        own = widget.styleSheet()
        widget.setStyleSheet(own + " ")  # A different, non-empty sheet: Qt re-polishes the widget.
        widget.setStyleSheet(own)
    widget.update()


def scale_font(widget):
    """Give a top-level window of ours the interface-size font (ui_scale); its children inherit it. Top-level
    windows do not inherit fonts from a parent window, so every one of ours needs this once."""
    from . import ui_scale
    factor = ui_scale.current["font"]
    if factor == 1.0 or widget.property("toolFontScaled"):
        return
    font = QtGui.QFont(widget.font())
    if font.pointSizeF() > 0:
        font.setPointSizeF(font.pointSizeF() * factor)
    elif font.pixelSize() > 0:
        font.setPixelSize(ui_scale.px(font.pixelSize()))
    widget.setFont(font)
    widget.setProperty("toolFontScaled", True)


def inherit_fonts(root):
    """Widgets polished before they were placed in an interface-size window keep the application's font of that
    moment; give each its parent's size (bold and family stay). Runs once a window is built (ThemeManager.register).
    """
    from . import ui_scale
    if ui_scale.current["font"] == 1.0:
        return
    for _ in range(3):  # Parents first is usual, but not promised by findChildren.
        changed = False
        for child in root.findChildren(QtWidgets.QWidget):
            parent = child.parentWidget()
            if parent is None or child.isWindow() or child.testAttribute(Qt.WA_SetFont):
                continue
            size, wanted = child.font().pointSizeF(), parent.font().pointSizeF()
            base = QtWidgets.QApplication.font(child).pointSizeF()  # Its class default (item views differ).
            if abs(size - base) < 0.01 and abs(wanted - base) > 0.01:
                font = QtGui.QFont(child.font())
                font.setPointSizeF(wanted)
                child.setFont(font)
                changed = True
        if not changed:
            return


def measure_scale(anchor=None, choice="auto"):
    """Set the interface size (ui_scale.apply) for the screen of `anchor` (a widget, e.g. Max's main window) or
    the primary screen; 3ds Max's own UI scale counts when it is larger. Returns the factors."""
    from . import ui_scale
    screen = None
    if anchor is not None:  # By position in Qt's screen list, never anchor.screen() (live_screens).
        try:
            screen = screen_at(anchor.frameGeometry().center())[0]
        except RuntimeError:
            screen = None
    if screen is None:
        try:
            screen = QtGui.QGuiApplication.primaryScreen()
        except RuntimeError:
            screen = None
    host = None
    try:
        from pymxs import runtime as rt
        host = float(rt.GetUIScaleFactor())
    except Exception:
        pass  # Outside Max, or a Max without it.
    try:
        geometry = screen.geometry()
        return ui_scale.apply(geometry.width(), geometry.height(), screen.devicePixelRatio(),
                              screen.logicalDotsPerInch() / 96.0, host, choice)
    except (RuntimeError, AttributeError):  # No screen, or its wrapper died meanwhile.
        return ui_scale.apply(1920, 1080, host_scale=host, choice=choice)


def device_pixel_ratio(widget):
    getter = getattr(widget, "devicePixelRatioF", None)
    return getter() if getter else widget.devicePixelRatio()


def round_window_corners(widget, border_color=None):
    """Windows 11: rounded corners (and the system shadow) for a frameless top-level window via DWM.

    `border_color` "#rrggbb" tints the thin system border. Does nothing elsewhere or on older Windows.
    Returns True when DWM accepted the corner preference.
    """
    import sys
    if sys.platform != "win32" or SAFE["on"]:
        return False
    try:
        import ctypes
        from ctypes import wintypes
        hwnd = wintypes.HWND(int(widget.winId()))
        dwm = ctypes.windll.dwmapi
        preference = ctypes.c_int(2)  # DWMWCP_ROUND
        ok = dwm.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)) == 0
        if ok and border_color:
            red, green, blue = (int(border_color[k:k + 2], 16) for k in (1, 3, 5))
            colorref = ctypes.c_uint(red | (green << 8) | (blue << 16))  # DWMWA_BORDER_COLOR, 0x00BBGGRR
            dwm.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(colorref), ctypes.sizeof(colorref))
        return ok
    except (AttributeError, OSError, ValueError):
        return False
```
