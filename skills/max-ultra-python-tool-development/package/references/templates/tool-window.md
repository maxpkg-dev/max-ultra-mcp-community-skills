# Template: Tool window: title bar, edges, collapsed bar, status bar

The frameless main window base with its own title bar (round 28 px buttons, close red on hover), the dark header shade that fades out where the content starts (`HEADER_SHADE`, `header_bottom`), edge resizing, rounded corners, the compact collapsed bar that docks in the active viewport and follows 3ds Max's window, and the status bar with View Logs first on the left (a muted text action with the Lucide `logs` icon) and Settings / About / Donate on the right; `notify()` shows toasts below the header.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP, with the windows off screen.

## `python/mytool/ui/tool_window.py`

```python
"""The tool's main window: own title bar, resizable edges, collapse to a small bar, status bar with Settings / Logs /
About / Donate. Subclass it or put the tool's content into `self.body` (a QVBoxLayout).

Window rules (proven in TerraScoop on Max 2022-2027):
* No Windows frame: the title bar moves the window (drag), double-click maximises, minus collapses to a bar, X closes.
  The 4 px edges resize it. Windows 11 rounds the corners through DWM (qt_compat.round_window_corners).
* The status bar: View Logs first on the left, then pills and the message; Settings, About and Donate on the right.
  Toasts (`notify`) appear below the header at the right.
* Place and size come back on the next start; a saved place off every screen falls back to centring on 3ds Max's
  screen. Screens are looked up by position (qt_compat.live_screens), never through widget.screen().
* A dark shade behind the title bar (and any tabs) fades out where the content starts (HEADER_SHADE, header_bottom).
* The collapsed bar: compact grip (drag), icon, name (click opens again), small X. Unplaced, it sits 8 px inside the active
  viewport's bottom-left corner, on whichever monitor that viewport is, and the bars of every tool built from this
  starter line up there in one row (in the order they were collapsed; ROW_PROPERTY finds them, no shared file). A light
  check every 500 ms while collapsed keeps the row on the corner when the viewport layout, the active viewport or the
  monitor changes. Dragged, a bar leaves the row and keeps its place; a double-click on its grip puts it back. It never
  goes under the taskbar or off the monitors, and it follows 3ds Max's window through Qt's own move signals.
"""

import time

from .. import DONATE_OFFERS, DONATE_URL, PROMOTIONS, TOOL_NAME, UPDATE_URL, __version__
from .. import qt_compat
from ..qt_compat import (QtCore, QtGui, QtWidgets, Qt, bounded_window_position, inherit_fonts, is_valid, live_screens,
                         own_keyboard, primary_work_area, round_window_corners, scale_font, work_area)
from ..ui_scale import px, space
from . import controls
from .toast import ToastStack


def _global_pos(event):
    """Global cursor position of a mouse event (PySide6 globalPosition, PySide2 globalPos)."""
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()


def _on_screen(rect):
    """True when the top strip of `rect` (where its title bar is) is on some screen."""
    top = QtCore.QRect(rect.x(), rect.y(), rect.width(), 30)
    return any(area.intersected(top).width() >= 120 for _screen, area, _geometry in live_screens())


class ToolWindow(QtWidgets.QWidget):
    EDGE = 4  # Logical pixels around the window that resize it.
    MINI_GAP = 8  # Logical pixels between the collapsed bar and the viewport's corner.
    SETTLE_MS = 250  # After 3ds Max's window stops moving, the bar takes its final place once.
    PARKED = -30000  # Windows puts a minimised window at (-32000, -32000).
    ROW_PROPERTY = "maxToolCollapsedBar"  # On a collapsed bar of any tool built from this starter: the shared row
    ROW_GAP = 4  # Logical pixels between bars in the row.
    WATCH_MS = 500  # While collapsed: how often the bar checks the viewport corner and the row.

    def __init__(self, controller, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.controller = controller
        theme = controller.theme
        scale_font(self)  # Interface size, before any child exists (polished children keep their font).
        self.setObjectName("toolWindow")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)  # The window background comes from the style sheet.
        self.setMouseTracking(True)
        self.setWindowTitle("{} {}".format(TOOL_NAME, __version__))
        self.setMinimumSize(px(560), px(360))
        self.resize(px(900), px(600))
        self.geometry_restored = False  # True when restore_geometry_state brought back the user's place and size
        self._resizing = None
        self._drag = None

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(px(self.EDGE), px(self.EDGE), px(self.EDGE), px(self.EDGE))  # Not spacing: the free resize edges
        outer.setSpacing(0)

        # Title bar: icon, "Name version", optional pills, stretch, minimise (collapse), close.
        self.title_bar = QtWidgets.QFrame()
        self.title_bar.setObjectName("toolTitleBar")
        bar = QtWidgets.QHBoxLayout(self.title_bar)
        bar.setContentsMargins(space(8), space(4), space(4), space(2))
        bar.setSpacing(space(4))
        bar.addWidget(controls.BrandIcon(18))
        bar.addSpacing(space(4))
        title = QtWidgets.QLabel("{} {}".format(TOOL_NAME, __version__))
        title.setObjectName("toolWindowTitle")
        bar.addWidget(title)
        self.title_row = bar  # Status pills can join it, right of the name.
        bar.addStretch(1)
        for icon, tip, slot in (("minus", "Collapse to a small bar (click its name to open again)", self.minimise),
                                ("x", "Close " + TOOL_NAME, self.close)):
            button = controls.WindowButton(icon, theme, tip, close=(icon == "x"))  # Round; close turns red on hover
            button.clicked.connect(slot)
            bar.addWidget(button)
        self.title_bar.installEventFilter(self)
        outer.addWidget(self.title_bar)

        # Collapsed bar: grip (drag), icon, name (click opens again), close.
        self.mini_bar = QtWidgets.QFrame()
        self.mini_bar.setObjectName("toolMiniBar")
        mini = QtWidgets.QHBoxLayout(self.mini_bar)
        mini.setContentsMargins(px(2), px(1), px(1), px(1))  # Not spacing: the packager's bar, 1 px inside its border
        mini.setSpacing(space(2))
        self.mini_grip = QtWidgets.QLabel()
        self.mini_grip.setFixedSize(px(14), px(22))
        self.mini_grip.setAlignment(Qt.AlignCenter)
        self.mini_grip.setCursor(Qt.SizeAllCursor)
        self.mini_grip.setToolTip("Drag to move; double-click to put the bar back in the row")
        self.mini_grip.installEventFilter(self)
        mini.addWidget(self.mini_grip)
        mini.addWidget(controls.BrandIcon(14))
        self.mini_title = QtWidgets.QPushButton(TOOL_NAME)  # The name only; the version is in its tooltip
        self.mini_title.setObjectName("toolMiniTitle")
        self.mini_title.setCursor(Qt.PointingHandCursor)
        self.mini_title.setToolTip("Open {} {} again".format(TOOL_NAME, __version__))
        self.mini_title.installEventFilter(self)  # A click opens the window, a drag moves the bar.
        mini.addWidget(self.mini_title, 1)
        mini_close = controls.WindowButton("x", theme, "Close " + TOOL_NAME, close=True, small=True)  # 22 px
        mini_close.clicked.connect(self.close)
        mini.addWidget(mini_close)
        self.mini_bar.hide()
        self.mini_bar.installEventFilter(self)  # Enter clears the edge cursor (eventFilter)
        outer.addWidget(self.mini_bar)
        self._mini = None  # While collapsed: (geometry, minimum size, visible parts) to come back to.
        self._host_window = None  # While collapsed: 3ds Max's window (QWindow) whose moves the bar follows.
        self._host_widget = None
        self._host_rect = None
        self._followed = False
        self._settle_timer = None
        self._watch_timer = None  # The light check while collapsed (watch_mini)

        # Content and status bar.
        self.full_view = QtWidgets.QWidget()
        outer.addWidget(self.full_view, 1)
        self.full_view.installEventFilter(self)  # Enter clears the edge cursor (eventFilter)
        root = QtWidgets.QVBoxLayout(self.full_view)
        root.setContentsMargins(space(12), space(12), space(12), space(8))
        root.setSpacing(space(8))
        self.body = QtWidgets.QVBoxLayout()
        self.body.setSpacing(space(8))
        root.addLayout(self.body, 1)
        status = QtWidgets.QHBoxLayout()
        status.setSpacing(space(6))
        # View Logs comes first on the left, as in MaxPkg Runtime Manager: a muted text action, not a button.
        self.logs_action = controls.StatusAction(
            "View Logs", theme, "logs", "See what {} did: steps, warnings and errors".format(TOOL_NAME))
        self.logs_action.clicked.connect(controller.show_logs)
        status.addWidget(self.logs_action)
        self.update_pill = controls.Pill(theme, "", "info")  # "Version 1.2.0 installed · Reopen" after an update
        self.update_pill.set_clickable(True)
        self.update_pill.clicked.connect(self._update_clicked)
        self.update_pill.hide()
        status.addWidget(self.update_pill)
        self.status_label = controls.ElidedLabel("")  # Long messages end with an ellipsis instead of being cut
        self.status_label.setObjectName("toolMuted")
        status.addWidget(self.status_label, 1)
        self.promotion = None
        if PROMOTIONS:  # The rotating link, between the message and the buttons on the right
            self.promotion = controls.PromotionLink(theme, PROMOTIONS)
            status.addWidget(self.promotion, 1)
        self.status_row = status  # Pills go after View Logs (index 1), more buttons before Settings.
        for text, icon, tip, slot in (("Settings", "settings", "Theme, interface size and options",
                                       controller.show_settings),
                                      ("About", "info", "About " + TOOL_NAME, controller.show_about)):
            button = controls.Button(text, theme, icon=icon, variant="ghost", tooltip=tip)
            button.clicked.connect(slot)
            status.addWidget(button)
        if DONATE_URL and "status" in DONATE_OFFERS:  # Only with a destination the owner gave; the last on the right
            self.donate_button = controls.Button("Donate", theme, icon="heart", variant="donate",
                                                 tooltip="Why a donation helps {}".format(TOOL_NAME))
            self.donate_button.clicked.connect(lambda: controller.show_support())  # Explains first (SupportDialog)
            status.addWidget(self.donate_button)
        root.addLayout(status)
        self.toasts = ToastStack(self, theme)  # Notices about the outcome of an action (notify)
        # The size grip of every resizable window (dialogs: ToolDialog(resizable=True)): in the bottom-right corner,
        # clear of the last button; hidden while collapsed or maximised. The edges resize the window too.
        self.grip = QtWidgets.QSizeGrip(self)
        self.grip.setFixedSize(px(12), px(12))
        self.grip.setToolTip("Drag to resize")

    # Header shade ------------------------------------------------------------------------------------
    HEADER_SHADE = 0.7  # Opacity of the black at the very top; it fades to nothing where the content starts

    def header_bottom(self):
        """Where the header ends, in window coordinates: the shade fades out there. Here the content (the first panel)
        starts below the title bar; a window with more header (a tab row) returns where its tabs end."""
        return self.title_bar.geometry().bottom() + 1 + self.full_view.layout().contentsMargins().top()

    def paintEvent(self, event):
        """A dark shade from the top of the window to the start of the content sets the header apart. It is painted
        on the window's own background, under the title bar (and the tabs)."""
        QtWidgets.QWidget.paintEvent(self, event)
        if self._mini is not None or not self.title_bar.isVisible():
            return
        bottom = self.header_bottom()
        shade = QtGui.QLinearGradient(0, 0, 0, bottom)
        dark = QtGui.QColor(0, 0, 0)
        dark.setAlphaF(self.HEADER_SHADE)
        shade.setColorAt(0.0, dark)
        shade.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(self)
        painter.fillRect(QtCore.QRect(0, 0, self.width(), bottom), shade)
        painter.end()

    # Status ---------------------------------------------------------------------------------------
    def set_status(self, text):
        self.status_label.setText(text)

    def on_update_result(self, result, automatic):
        """An update check finished (controller.check_updates): a pill and a toast for a new version; failures of an
        automatic check stay quiet (they are in the log)."""
        version = result.get("version")
        if result.get("error") or not version:
            return
        reopen = self.controller.can_reopen()
        if result.get("installed"):
            self.update_pill.set_status("Version {} installed".format(version) + (" · Reopen" if reopen else ""),
                                        "success", "Reopen {} to start the new version".format(TOOL_NAME))
            self.notify("Version {} is installed.\nIt starts when {} opens again.".format(version, TOOL_NAME), "success",
                        action=("Reopen Now", "refresh-cw", self.controller.reopen) if reopen else None, key="update")
        else:
            self.update_pill.set_status("Version {} available".format(version), "info")
        self.update_pill.show()

    def _update_clicked(self):
        if "installed" in self.update_pill.text() and self.controller.can_reopen() and \
                self.controller.confirm_stop("relaunch"):
            self.controller.reopen()

    def notify(self, text, kind="info", action=None, key=""):
        """A toast below the header at the right: "First line\nmuted rest". `kind`: success, error, warning or info;
        `action`: (label, Lucide icon, callback) or a list of them; `key`: shown again instead of a second one."""
        return self.toasts.notify(text, kind, action, key)

    # Title bar drag, collapsed bar drag / click ------------------------------------------------------
    def eventFilter(self, watched, event):
        # The resize arrows belong to the free edge only. Children inherit the window's cursor, and the window gets no
        # event when the pointer moves from the edge onto a child (title bar, content), so entering one clears it:
        # inside the window the pointer is the ordinary arrow.
        if event.type() == QtCore.QEvent.Enter and self._resizing is None and \
                watched in (getattr(self, "title_bar", None), getattr(self, "full_view", None),
                            getattr(self, "mini_bar", None)):
            self.unsetCursor()
        if watched in (getattr(self, "mini_grip", None), getattr(self, "mini_title", None)):
            kind = event.type()
            if kind == QtCore.QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._drag = _global_pos(event) - self.frameGeometry().topLeft()
                self._drag_from = _global_pos(event)
                self._dragged = False
                return True
            if kind == QtCore.QEvent.MouseMove and self._drag is not None:
                if (_global_pos(event) - self._drag_from).manhattanLength() > 4:
                    self._dragged = True
                if self._dragged:  # Never below the taskbar or off the screens.
                    self.move(bounded_window_position(_global_pos(event) - self._drag, self.frameGeometry().size(),
                                                      _global_pos(event)))
                return True
            if kind == QtCore.QEvent.MouseButtonDblClick and watched is self.mini_grip:
                self.back_to_row()
                return True
            if kind == QtCore.QEvent.MouseButtonRelease and self._drag is not None:
                self._drag = None
                if self._dragged:
                    self.controller.set_preference("mini_position", [self.x(), self.y()])
                    self.setProperty("maxToolBarPlaced", True)  # Out of the row; the others close the gap
                elif watched is self.mini_title:
                    QtCore.QTimer.singleShot(0, self.restore_from_mini)
                return True
        if watched is getattr(self, "title_bar", None):
            kind = event.type()
            if kind == QtCore.QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton:
                self.showNormal() if self.isMaximized() else self.showMaximized()
                return True
            if kind == QtCore.QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._drag = _global_pos(event) - self.frameGeometry().topLeft()
                return True
            if kind == QtCore.QEvent.MouseMove and self._drag is not None:
                if self.isMaximized():  # Dragging a maximised window restores it under the cursor.
                    ratio = float(self._drag.x()) / max(1, self.width())
                    self.showNormal()
                    self._drag = QtCore.QPoint(int(self.width() * ratio), self._drag.y())
                self.move(_global_pos(event) - self._drag)
                return True
            if kind == QtCore.QEvent.MouseButtonRelease:
                self._drag = None
        return QtWidgets.QWidget.eventFilter(self, watched, event)

    # Resizing by the edges ---------------------------------------------------------------------------
    def _edges(self, pos):
        if self._mini is not None or self.isMaximized():
            return 0
        x, y, w, h, e = pos.x(), pos.y(), self.width(), self.height(), px(self.EDGE) + 2
        return (1 if x <= e else 0) | (2 if x >= w - e else 0) | (4 if y <= e else 0) | (8 if y >= h - e else 0)

    _CURSORS = {1: Qt.SizeHorCursor, 2: Qt.SizeHorCursor, 4: Qt.SizeVerCursor, 8: Qt.SizeVerCursor,
                5: Qt.SizeFDiagCursor, 10: Qt.SizeFDiagCursor, 6: Qt.SizeBDiagCursor, 9: Qt.SizeBDiagCursor}

    def mousePressEvent(self, event):
        edges = self._edges(event.pos())
        if edges and event.button() == Qt.LeftButton:
            self._resizing = (edges, _global_pos(event), self.geometry())
            return
        QtWidgets.QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self._resizing is not None:
            edges, start, geometry = self._resizing
            delta = _global_pos(event) - start
            rect = QtCore.QRect(geometry)
            minimum = self.minimumSize()
            if edges & 1:
                rect.setLeft(min(rect.left() + delta.x(), rect.right() - minimum.width()))
            if edges & 2:
                rect.setRight(max(rect.right() + delta.x(), rect.left() + minimum.width()))
            if edges & 4:
                rect.setTop(min(rect.top() + delta.y(), rect.bottom() - minimum.height()))
            if edges & 8:
                rect.setBottom(max(rect.bottom() + delta.y(), rect.top() + minimum.height()))
            self.setGeometry(rect)
            return
        cursor = self._CURSORS.get(self._edges(event.pos()))
        if cursor is not None:
            self.setCursor(cursor)
        else:
            self.unsetCursor()
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        self._resizing = None
        QtWidgets.QWidget.mouseReleaseEvent(self, event)

    def leaveEvent(self, event):
        if self._resizing is None:
            self.unsetCursor()
        QtWidgets.QWidget.leaveEvent(self, event)

    # Window position and size ----------------------------------------------------------------------
    def geometry_state(self):
        state = self._mini[0] if self._mini is not None else self.saveGeometry()  # Collapsed: the full window's.
        return bytes(state.toBase64()).decode("ascii")

    def restore_geometry_state(self, encoded):
        """Restore the saved position/size; fall back to centred on 3ds Max's screen when it is off every screen."""
        restored = False
        if encoded:
            try:
                restored = bool(self.restoreGeometry(QtCore.QByteArray.fromBase64(encoded.encode("ascii"))))
            except (ValueError, TypeError):
                restored = False
        frame = self.geometry()
        visible = any(area.intersected(frame).width() >= 160 and area.intersected(frame).height() >= 120
                      for _screen, area, _geometry in live_screens())
        if restored and visible:
            self.geometry_restored = True
            return
        area = None
        if self.parentWidget() is not None:  # By position: never parentWidget().screen() (a dead QScreen in Max 2024).
            area = work_area(self.parentWidget().frameGeometry().center())
        area = area or primary_work_area()
        width, height = min(self.width(), area.width()), min(self.height(), area.height())
        self.setGeometry(area.x() + (area.width() - width) // 2, area.y() + (area.height() - height) // 2,
                         width, height)

    # Collapsed bar -----------------------------------------------------------------------------------
    def minimise(self):
        """Collapse to the small bar; restore_from_mini() brings back the same place and size."""
        if self._mini is not None:
            return
        if self.isMaximized():
            self.showNormal()
        self.toasts.clear()  # No notices over the small bar
        parts = [part for part in (self.title_bar, self.full_view) if part.isVisible()]
        self._mini = (self.saveGeometry(), self.minimumSize(), parts)
        for part in parts:
            part.hide()
        self.mini_grip.setPixmap(controls.icon_pixmap("grip-vertical", self.controller.theme.color("muted_text"),
                                                      px(14), controls.device_pixel_ratio(self)))
        self.mini_bar.show()
        self.grip.hide()
        self.setMinimumSize(0, 0)
        size = QtCore.QSize(self.mini_bar.sizeHint().width() + 2 * px(self.EDGE),
                            self.mini_bar.sizeHint().height() + 2 * px(self.EDGE))
        self.resize(size)
        saved = self.controller.prefs.get("mini_position") or []
        placed = len(saved) == 2 and _on_screen(QtCore.QRect(int(saved[0]), int(saved[1]), size.width(),
                                                             size.height()))
        self.setProperty(self.ROW_PROPERTY, True)
        self.setProperty("maxToolBarSince", time.time())
        self.setProperty("maxToolBarPlaced", placed)
        if placed:
            self.move(int(saved[0]), int(saved[1]))  # Where the user last put it.
        else:
            self.move(self.row_slot(size))
        self.confine_mini()
        self.follow_host(True)
        if self._watch_timer is None:
            self._watch_timer = QtCore.QTimer(self)
            self._watch_timer.setInterval(self.WATCH_MS)
            self._watch_timer.timeout.connect(self.watch_mini)
        self._watch_timer.start()
        if not getattr(self, "_watching_screens", False):  # Taskbar moved, screen added or removed.
            self._watching_screens = True
            application = QtGui.QGuiApplication.instance()
            application.screenAdded.connect(self._watch_screen)
            application.screenRemoved.connect(lambda *_: self.confine_mini())
            for screen, _area, _geometry in live_screens():
                self._watch_screen(screen)

    def row_slot(self, size):
        """Top-left of this bar in the shared row: the viewport corner, after the unplaced bars (of any tool) that
        collapsed earlier."""
        home = self._mini_home(size)
        since = self.property("maxToolBarSince") or 0.0
        earlier = []
        for widget in QtWidgets.QApplication.topLevelWidgets():
            try:
                if widget is self or not widget.property(self.ROW_PROPERTY) or widget.property("maxToolBarPlaced") \
                        or not widget.isVisible():
                    continue
                if (widget.property("maxToolBarSince") or 0.0) < since:
                    earlier.append(widget.frameGeometry().width())
            except RuntimeError:  # A bar of a tool that is closing
                continue
        return QtCore.QPoint(home.x() + sum(width + px(self.ROW_GAP) for width in earlier), home.y())

    def watch_mini(self):
        """The light check while collapsed: an unplaced bar keeps its slot in the row at the viewport corner when
        the viewport layout, the active viewport, the monitor or the row changes. Never while being dragged."""
        if self._mini is None or not is_valid(self):
            if self._watch_timer is not None:
                self._watch_timer.stop()
            return
        if self.property("maxToolBarPlaced") or self._drag is not None:
            return
        target = self.row_slot(self.size())
        if target != self.pos():
            self.move(target)
            self.confine_mini()

    def back_to_row(self):
        """A double-click on the grip: the bar forgets the place it was dragged to and joins the row again."""
        self.controller.set_preference("mini_position", [])
        self.setProperty("maxToolBarPlaced", False)
        self.watch_mini()

    def _mini_home(self, size):
        """Top-left for an unplaced bar: inside the active viewport's bottom-left corner; without a viewport (outside
        Max), bottom-left of the host window above its time slider."""
        viewport = qt_compat.active_viewport_rect()
        if viewport is not None and viewport.width() > size.width() and viewport.height() > size.height():
            gap = px(self.MINI_GAP)
            return QtCore.QPoint(viewport.left() + gap, viewport.top() + viewport.height() - gap - size.height())
        widget = self._host_widget if self._host_widget is not None else self.parentWidget()
        host = widget.frameGeometry() if widget is not None else None
        if host is None or host.width() < size.width():
            host = primary_work_area()
        return QtCore.QPoint(host.left() + 12, host.bottom() - size.height() - 110)

    def _watch_screen(self, screen):
        try:
            screen.availableGeometryChanged.connect(lambda *_: self.confine_mini())
        except RuntimeError:  # A screen whose wrapper is already dead (qt_compat.live_screens).
            pass
        self.confine_mini()

    def confine_mini(self):
        """The collapsed bar stays inside a screen's work area (above the taskbar)."""
        if self._mini is None or not is_valid(self):
            return
        bounded = bounded_window_position(self.pos(), self.frameGeometry().size())
        if bounded != self.pos():
            self.move(bounded)

    def follow_host(self, on, host=None):
        """While collapsed, the bar moves with 3ds Max's main window (also to another display).

        Driven only by Qt's own "window moved / resized" signals of Max's window: nothing polls and nothing runs while
        Max stands still. Connected on collapse, disconnected on restore and close. `host` replaces Max's window in a
        standalone test. In safe mode, or when Max's window cannot be reached, the bar simply stays.
        """
        handle, self._host_window = self._host_window, None
        if handle is not None:
            for signal in (handle.xChanged, handle.yChanged, handle.widthChanged, handle.heightChanged):
                try:
                    signal.disconnect(self._host_moved)
                except (RuntimeError, TypeError):  # Max's window or its wrapper is gone.
                    pass
        if self._settle_timer is not None:
            self._settle_timer.stop()
        self._host_widget, self._followed = None, False
        widget = host if host is not None else self.parentWidget()
        if not on or widget is None or qt_compat.SAFE["on"]:
            return
        try:
            handle = widget.windowHandle()
            if handle is None:
                return
            self._host_rect = QtCore.QRect(handle.frameGeometry())
            for signal in (handle.xChanged, handle.yChanged, handle.widthChanged, handle.heightChanged):
                signal.connect(self._host_moved)
        except (RuntimeError, AttributeError):
            return
        self._host_window, self._host_widget = handle, widget

    def _host_moved(self, *_args):
        """3ds Max's window moved or changed size: the bar keeps its distance to Max's nearest edges."""
        handle = self._host_window
        if self._mini is None or handle is None or not is_valid(self):
            return
        try:
            new = QtCore.QRect(handle.frameGeometry())
            # Windows hides the bar with its owner and brings it back where it was. A minimised window is parked at
            # -32000 before (or without) its state saying so: never follow it there.
            if handle.visibility() == QtGui.QWindow.Minimized or new.left() <= self.PARKED or new.top() <= self.PARKED:
                return
        except RuntimeError:
            self.follow_host(False)
            return
        old, self._host_rect = self._host_rect, new
        bar = self.frameGeometry()
        if old is None or new == old or not old.intersects(bar):
            return  # The user put the bar away from 3ds Max: it stays there.
        left, right = bar.left() - old.left(), old.right() - bar.right()
        top, bottom = bar.top() - old.top(), old.bottom() - bar.bottom()
        x = new.left() + left if left <= right else new.right() - right - bar.width() + 1
        y = new.top() + top if top <= bottom else new.bottom() - bottom - bar.height() + 1
        self.move(x, y)
        self._followed = True
        if self._settle_timer is None:
            self._settle_timer = QtCore.QTimer(self)
            self._settle_timer.setSingleShot(True)  # Started by a move only; never runs on its own.
            self._settle_timer.timeout.connect(self._host_settled)
        self._settle_timer.start(self.SETTLE_MS)

    def _host_settled(self):
        if self._mini is None or not self._followed or not is_valid(self):
            return
        self._followed = False
        if self.controller.prefs.get("mini_position"):
            self.confine_mini()
            self.controller.set_preference("mini_position", [self.x(), self.y()])  # Placed by the user: its new place.
        else:
            self.move(self.row_slot(self.size()))  # Its slot at the active viewport's corner on the new display.
            self.confine_mini()

    def restore_from_mini(self):
        if self._mini is None:
            return
        self.follow_host(False)
        if self._watch_timer is not None:
            self._watch_timer.stop()
        self.setProperty(self.ROW_PROPERTY, False)  # The other bars close the gap
        geometry, minimum, parts = self._mini
        self._mini = None
        self.mini_bar.hide()
        for part in parts:
            part.show()
        self.setMinimumSize(minimum)
        self.restoreGeometry(geometry)  # Its own place and size, wherever the bar was.
        self._place_grip()

    # Showing, corners, keys, closing ----------------------------------------------------------------
    RADIUS = 8  # Corner radius of the fallback mask; Windows 11's own rounding is 8 px too.

    def showEvent(self, event):
        QtWidgets.QWidget.showEvent(self, event)
        # Children are polished now: a widget matched by a style sheet rule (lists, tables) got the application's font
        # back at polish time, not the window's interface-size font. Give it the window's size again.
        inherit_fonts(self)
        # Rounded corners: Windows 11 DWM rounds them smoothly and draws the thin border in the theme's border
        # colour. Where DWM cannot (Windows 10, remote sessions), a rounded window mask does it (hard edges).
        self._dwm_round = round_window_corners(self, self.controller.theme.colors.get("border"))
        self._mask_corners()
        self.own_keyboard()

    def _place_grip(self):
        grip = getattr(self, "grip", None)
        if grip is None:
            return
        grip.setVisible(self._mini is None and not self.isMaximized() and not self.isFullScreen())
        grip.move(self.width() - grip.width() - 1, self.height() - grip.height() - 1)
        grip.raise_()

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.WindowStateChange:
            self._place_grip()  # No grip on a maximised window
        QtWidgets.QWidget.changeEvent(self, event)

    def resizeEvent(self, event):
        QtWidgets.QWidget.resizeEvent(self, event)
        self._place_grip()
        self._mask_corners()
        stack = getattr(self, "toasts", None)  # resize() in __init__ comes before the stack exists
        if stack is not None and stack.toasts:
            stack.place()

    def _mask_corners(self):
        if getattr(self, "_dwm_round", True) or qt_compat.SAFE["on"]:
            return  # DWM rounds them, or safe mode keeps native extras off.
        if self.isMaximized() or self.isFullScreen():
            self.clearMask()  # A maximised window has square corners, as everywhere in Windows.
            return
        radius = px(self.RADIUS)
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(self.rect()), radius, radius)
        self.setMask(QtGui.QRegion(path.toFillPolygon().toPolygon()))

    def own_keyboard(self):
        """Max's hotkeys stay off while any of the tool's widgets has the focus, so Esc, Delete and letters reach it.
        Run again when widgets are created later (a web page's focus proxy, rebuilt rows)."""
        own_keyboard([self] + self.findChildren(QtWidgets.QWidget))

    def closeEvent(self, event):
        # Closing the window ends the session (the controller asks first while work runs).
        if not self.controller.confirm_stop("close"):
            event.ignore()
            return
        QtWidgets.QWidget.closeEvent(self, event)
        if event.isAccepted():
            self.controller.request_stop()

    def dispose(self):
        self.follow_host(False)
```
