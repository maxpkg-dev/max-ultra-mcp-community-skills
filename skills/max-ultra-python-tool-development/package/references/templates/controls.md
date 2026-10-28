# Template: Shared controls

Lucide icon rendering, the brand icon, themed buttons with variants, pills, the progress bar, the segmented control, the dropdown, a flow layout, help balloons, completer rows, shimmer, marquee and the eliding label.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `python/mytool/ui/controls.py`

```python
"""Shared controls. Every dialog composes these; none re-implements their painting or behavior."""

import time

from ..qt_compat import QtCore, QtGui, QtSvg, QtWidgets, Qt, Signal, device_pixel_ratio, work_area
from ..ui_scale import pt, px
from .theme_manager import tinted_svg


_icon_cache = {}


def icon_pixmap(name, color, size, ratio):
    key = (name, color, size, round(ratio, 2))
    pixmap = _icon_cache.get(key)
    if pixmap is None:
        renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(tinted_svg(name, color).encode("utf-8")))
        physical = max(1, int(round(size * ratio)))
        image = QtGui.QImage(physical, physical, QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        painter = QtGui.QPainter(image)
        renderer.render(painter)
        painter.end()
        pixmap = QtGui.QPixmap.fromImage(image)
        pixmap.setDevicePixelRatio(ratio)
        _icon_cache[key] = pixmap
    return pixmap


def brand_pixmap(size, ratio):
    """The MyTool brand icon (not a button icon) rendered sharply at the device pixel ratio."""
    from .. import resources
    physical = max(1, int(round(size * ratio)))
    image = QtGui.QImage(physical, physical, QtGui.QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    renderer = QtSvg.QSvgRenderer(resources.asset("mytool.svg"))
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    pixmap = QtGui.QPixmap.fromImage(image)
    pixmap.setDevicePixelRatio(ratio)
    return pixmap


class BrandIcon(QtWidgets.QLabel):
    """The MyTool icon beside the tool's name in title bars; rendered when shown (the screen's pixel
    ratio is known then)."""

    def __init__(self, size=18, parent=None):
        QtWidgets.QLabel.__init__(self, parent)
        self._size = px(size)  # Interface size.
        self.setFixedSize(self._size, self._size)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Drags on the bar pass through.

    def showEvent(self, event):
        self.setPixmap(brand_pixmap(self._size, device_pixel_ratio(self)))
        QtWidgets.QLabel.showEvent(self, event)


def make_icon(name, colors, widget, size=16):
    ratio = device_pixel_ratio(widget)
    size = px(size)  # Rendered at the interface size, so it stays sharp at the button's scaled icon size.
    icon = QtGui.QIcon()
    icon.addPixmap(icon_pixmap(name, colors["text"], size, ratio), QtGui.QIcon.Normal)
    icon.addPixmap(icon_pixmap(name, colors["disabled_text"], size, ratio), QtGui.QIcon.Disabled)
    return icon


class Themed(object):
    """Mixin: re-tint icons and repaint when the theme changes."""

    def bind_theme(self, theme):
        self._theme = theme
        theme.subscribe(self._on_theme)
        self.destroyed.connect(lambda *_: theme.unsubscribe(self._on_theme))
        self._on_theme(theme.colors)

    def _on_theme(self, colors):
        pass


class Button(QtWidgets.QPushButton, Themed):
    """Push button with semantic variant (primary, secondary, danger, ghost, donate) and Lucide icon."""

    def __init__(self, text="", theme=None, icon=None, variant="secondary", tooltip="", parent=None,
                 icon_role=None):
        QtWidgets.QPushButton.__init__(self, "", parent)
        self.icon_name = icon
        self.icon_role = icon_role  # A theme colour for the icon instead of the variant's text colour.
        self.setText(text)
        self.setProperty("variant", variant)
        if tooltip:
            self.setToolTip(tooltip)
        if not text and tooltip:
            self.setAccessibleName(tooltip)
        self._sync_cursor()
        if theme is not None:
            self.bind_theme(theme)

    ICON_GAP = "\u2002"  # En space before the text of icon buttons.

    def setText(self, text):
        QtWidgets.QPushButton.setText(self, (self.ICON_GAP + text) if text and self.icon_name else text)

    def text(self):
        return QtWidgets.QPushButton.text(self).lstrip(self.ICON_GAP)

    def _on_theme(self, colors):
        if self.icon_name:
            # Same colour as the variant's text in style.qss.
            role = self.icon_role or {"primary": "log_badge_text", "danger": "danger_text",
                                      "donate": "status_button_text"}.get(self.property("variant"), "text")
            local = dict(colors, text=colors[role])
            self.setIcon(make_icon(self.icon_name, local, self))
            self.setIconSize(QtCore.QSize(px(16), px(16)))

    def _sync_cursor(self):
        self.setCursor(Qt.PointingHandCursor if self.isEnabled() else Qt.ArrowCursor)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.EnabledChange:
            self._sync_cursor()
        QtWidgets.QPushButton.changeEvent(self, event)


class Pill(QtWidgets.QWidget, Themed):
    """Rounded status capsule. Variants: neutral, info, success, warning, error.

    set_clickable(True) turns it into a button-like control that emits `clicked`.
    """

    clicked = Signal()

    _ROLES = {"neutral": "muted_text", "info": "log_info", "success": "log_success",
              "warning": "log_warning", "error": "log_error"}

    def __init__(self, theme, text="", variant="neutral", parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._text = text
        self._variant = variant
        self._colors = theme.colors
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        self.bind_theme(theme)

    def set_status(self, text, variant=None, tooltip=None):
        self._text = text
        if variant:
            self._variant = variant
        self.setToolTip(tooltip or text)
        self.setAccessibleName(tooltip or text)
        self.updateGeometry()
        self.update()

    def text(self):
        return self._text

    def set_clickable(self, on):
        self._clickable = bool(on)
        self.setCursor(Qt.PointingHandCursor if on else Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if getattr(self, "_clickable", False) and event.button() == Qt.LeftButton \
                and self.rect().contains(event.pos()):
            self.clicked.emit()
        QtWidgets.QWidget.mouseReleaseEvent(self, event)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def sizeHint(self):
        metrics = self.fontMetrics()
        width = metrics.horizontalAdvance(self._text) if hasattr(metrics, "horizontalAdvance") \
            else metrics.width(self._text)
        return QtCore.QSize(width + px(20), metrics.height() + px(8))

    def minimumSizeHint(self):
        # Never force the parent wider than it is: a pill may shrink, and its text then elides in the
        # middle while the full text stays in the tooltip (callers keep long details out of pills).
        hint = self.sizeHint()
        return QtCore.QSize(min(hint.width(), px(64)), hint.height())

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2
        tone = QtGui.QColor(self._colors[self._ROLES.get(self._variant, "muted_text")])
        fill = QtGui.QColor(tone)
        fill.setAlpha(40)
        painter.setPen(QtGui.QPen(tone, 1))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, radius, radius)
        painter.setPen(QtGui.QColor(self._colors["text"]))
        inner = self.rect().adjusted(10, 0, -10, 0)
        painter.drawText(inner, Qt.AlignCenter, self.fontMetrics().elidedText(self._text, Qt.ElideMiddle,
                                                                              inner.width()))
        painter.end()


class ProgressBar(QtWidgets.QWidget, Themed):
    """Pill progress bar with a clipped rounded fill, a caption and elapsed seconds.

    Known work shows real progress; total=None shows an indeterminate sweep. Timers run only while busy.
    `clicked` is emitted on a left click.
    """

    clicked = Signal()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
        QtWidgets.QWidget.mouseReleaseEvent(self, event)

    def __init__(self, theme, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._colors = theme.colors
        self._label = ""
        self._done = 0
        self._total = None
        self._started = None
        self._phase = 0.0
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._tick)
        self.setMinimumHeight(px(22))
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.bind_theme(theme)

    def start(self):
        import time
        self._started = time.monotonic()
        self._done, self._total, self._label = 0, None, "Starting..."
        self._timer.start()
        self.show()
        self.update()

    def set_progress(self, label, done, total):
        self._label, self._done, self._total = label, done, total
        self.update()

    def stop(self):
        self._timer.stop()
        self._started = None
        self.hide()

    def elapsed(self):
        import time
        return 0.0 if self._started is None else time.monotonic() - self._started

    def _tick(self):
        self._phase = (self._phase + 0.02) % 1.0
        self.update()

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def hideEvent(self, event):
        self._timer.stop()
        QtWidgets.QWidget.hideEvent(self, event)

    def sizeHint(self):
        return QtCore.QSize(px(200), max(px(22), self.fontMetrics().height() + px(8)))

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2
        track = QtGui.QPainterPath()
        track.addRoundedRect(rect, radius, radius)
        painter.fillPath(track, QtGui.QColor(self._colors["recessed"]))
        painter.setClipPath(track)
        fill = QtGui.QColor(self._colors["accent"])
        fill.setAlpha(150)
        if self._total:
            fraction = max(0.0, min(1.0, float(self._done) / self._total))
            painter.fillRect(QtCore.QRectF(rect.left(), rect.top(), rect.width() * fraction, rect.height()), fill)
        else:
            span = rect.width() * 0.3
            x = rect.left() - span + (rect.width() + span) * self._phase
            painter.fillRect(QtCore.QRectF(x, rect.top(), span, rect.height()), fill)
        painter.setClipping(False)
        painter.setPen(QtGui.QPen(QtGui.QColor(self._colors["border"]), 1))
        painter.drawPath(track)
        painter.setPen(QtGui.QColor(self._colors["text"]))
        caption = self._label
        if self._total:
            caption = "{} {}/{}".format(caption, self._done, self._total)
        caption = "{}  {:.0f}s".format(caption, self.elapsed())
        text_rect = self.rect().adjusted(10, 0, -10, 0)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft,
                         self.fontMetrics().elidedText(caption, Qt.ElideMiddle, text_rect.width()))
        painter.end()


class Segmented(QtWidgets.QWidget):
    """Exclusive row of checkable buttons, e.g. quality presets."""

    changed = Signal(str)

    OVERLAP = 1  # Neighbouring segments share one border line.

    def __init__(self, options, theme, current=None, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        # No layout: QBoxLayout treats a negative spacing as "style default" (a visible gap), so the
        # buttons are placed by hand, each overlapping its left neighbour by OVERLAP px.
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.group = QtWidgets.QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = {}
        self._order = []
        for index, (key, label, tip) in enumerate(options):
            button = Button(label, theme, tooltip=tip)
            button.setCheckable(True)
            position = "first" if index == 0 else ("last" if index == len(options) - 1 else "middle")
            button.setProperty("segment", position)
            button.setParent(self)
            self.group.addButton(button)
            self.buttons[key] = button
            self._order.append(button)
            button.toggled.connect(lambda on, k=key: self._on_toggled(k, on))
        self.set_value(current or options[0][0])

    def sizeHint(self):
        hints = [button.sizeHint() for button in self._order]
        return QtCore.QSize(sum(h.width() for h in hints) - self.OVERLAP * (len(hints) - 1),
                            max(h.height() for h in hints))

    def minimumSizeHint(self):
        # Text width plus a small margin only: the buttons' own (padded) minimum made the row wider than a
        # panel with a scroll bar, which cut off the last segment.
        metrics = self.fontMetrics()
        width = sum(metrics.horizontalAdvance(button.text()) + 14 for button in self._order)
        return QtCore.QSize(width, max(button.minimumSizeHint().height() for button in self._order))

    def resizeEvent(self, event):
        QtWidgets.QWidget.resizeEvent(self, event)
        count = len(self._order)
        total = self.width() + self.OVERLAP * (count - 1)
        x = 0
        for index, button in enumerate(self._order):
            # Each segment's right edge, minus the overlaps so far: the last one ends exactly at width().
            right = int(round(total * (index + 1) / float(count))) - index * self.OVERLAP
            button.setGeometry(x, 0, right - x, self.height())
            x = right - self.OVERLAP

    def _on_toggled(self, key, on):
        if on:
            self.buttons[key].raise_()  # Keep the checked segment's border above its neighbours.
            self.changed.emit(key)

    def set_value(self, key):
        self.buttons[key].setChecked(True)
        self.buttons[key].raise_()

    def value(self):
        for key, button in self.buttons.items():
            if button.isChecked():
                return key
        return None


class ComboBox(QtWidgets.QComboBox):
    """Themed dropdown whose popup is a styled list placed 4px below (or above) the field."""

    def __init__(self, parent=None):
        QtWidgets.QComboBox.__init__(self, parent)
        view = QtWidgets.QListView(self)
        view.setObjectName("toolPopup")
        self.setView(view)
        self.setCursor(Qt.PointingHandCursor)

    def showPopup(self):
        QtWidgets.QComboBox.showPopup(self)
        popup = self.view().window()
        area = work_area(self.mapToGlobal(QtCore.QPoint(0, 0))) or popup.geometry()
        below = self.mapToGlobal(QtCore.QPoint(0, self.height() + 4))
        y = below.y()
        if y + popup.height() > area.bottom():
            y = self.mapToGlobal(QtCore.QPoint(0, 0)).y() - popup.height() - 4
        x = max(area.left(), min(below.x(), area.right() - popup.width()))
        popup.move(x, max(area.top(), y))


class FlowLayout(QtWidgets.QLayout):
    """Left-to-right layout that wraps to new rows (for chips such as the scene layer toggles)."""

    def __init__(self, parent=None, spacing=6, row_spacing=None):
        QtWidgets.QLayout.__init__(self, parent)
        self._items = []
        self._gap = spacing
        self._row_gap = spacing if row_spacing is None else row_spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._arrange(QtCore.QRect(0, 0, width, 0), apply=False)

    def setGeometry(self, rect):
        QtWidgets.QLayout.setGeometry(self, rect)
        self._arrange(rect, apply=True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QtCore.QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def _arrange(self, rect, apply):
        margins = self.contentsMargins()
        left, top = rect.x() + margins.left(), rect.y() + margins.top()
        right = rect.right() - margins.right()
        x, y, row_height = left, top, 0
        for item in self._items:
            hint = item.sizeHint()
            if x > left and x + hint.width() > right + 1:
                x, y, row_height = left, y + row_height + self._row_gap, 0
            if apply:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), hint))
            x += hint.width() + self._gap
            row_height = max(row_height, hint.height())
        return y + row_height - rect.y() + margins.bottom()


def section(text):
    label = QtWidgets.QLabel(text)
    label.setObjectName("toolSection")
    return label


class Balloon(QtWidgets.QWidget, Themed):
    """A help bubble with an arrow pointing at its HelpButton: a bold title and a short description. A click
    elsewhere or Esc closes it. Painted here and shaped with a window mask (translucent popups are risky inside
    Max, pitfalls.md)."""

    WIDTH = 280
    PAD = 10
    ARROW = 7
    RADIUS = 6

    def __init__(self, theme, parent=None):
        QtWidgets.QWidget.__init__(self, parent, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        if parent is not None:
            self.setFont(parent.font())  # A popup does not inherit its window's (interface-size) font.
        self._title, self._text = "", ""
        self._shape = QtGui.QPainterPath()
        self.closed_at = 0.0
        self.bind_theme(theme)

    def _fonts(self):
        title = QtGui.QFont(self.font())
        title.setBold(True)
        return title, self.font()

    def show_for(self, anchor, title, text):
        self._title, self._text = title, text
        title_font, text_font = self._fonts()
        inner = px(self.WIDTH) - 2 * px(self.PAD)
        flags = int(Qt.TextWordWrap)
        title_h = QtGui.QFontMetrics(title_font).boundingRect(0, 0, inner, 10000, flags, title).height()
        text_h = QtGui.QFontMetrics(text_font).boundingRect(0, 0, inner, 10000, flags, text).height()
        body_h = px(self.PAD) + title_h + 4 + text_h + px(self.PAD)
        height = body_h + px(self.ARROW)
        # Below the button when it fits on the screen, else above; the arrow points at the button's centre.
        centre = anchor.mapToGlobal(QtCore.QPoint(anchor.width() // 2, anchor.height() // 2))
        area = work_area(centre) or QtCore.QRect(centre.x() - 2000, centre.y() - 2000, 4000, 4000)
        below = centre.y() + anchor.height() // 2 + height <= area.bottom()
        x = max(area.left() + 4, min(centre.x() - px(self.WIDTH) // 2, area.right() - px(self.WIDTH) - 4))
        y = centre.y() + anchor.height() // 2 + 2 if below else centre.y() - anchor.height() // 2 - 2 - height
        tip = max(px(self.RADIUS) + px(self.ARROW), min(centre.x() - x, px(self.WIDTH) - px(self.RADIUS) - px(self.ARROW)))
        top = px(self.ARROW) if below else 0
        body = QtGui.QPainterPath()
        body.addRoundedRect(QtCore.QRectF(0, top, px(self.WIDTH), body_h), px(self.RADIUS), px(self.RADIUS))
        edge = top if below else body_h
        point = 0 if below else height
        arrow = QtGui.QPainterPath()
        arrow.addPolygon(QtGui.QPolygonF([QtCore.QPointF(tip - px(self.ARROW), edge + (1 if below else -1)),
                                          QtCore.QPointF(tip, point), QtCore.QPointF(tip + px(self.ARROW),
                                                                                     edge + (1 if below else -1))]))
        self._shape = body.united(arrow)
        self._body_top = top
        self._title_h = title_h
        self.setFixedSize(px(self.WIDTH), height)
        self.setMask(QtGui.QRegion(self._shape.toFillPolygon().toPolygon()))
        self.move(x, y)
        self.show()

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillPath(self._shape, QtGui.QColor(self._colors["tooltip_background"]))
        painter.setPen(QtGui.QPen(QtGui.QColor(self._colors["active_border"]), 1.5))
        painter.drawPath(self._shape)
        title_font, text_font = self._fonts()
        inner = px(self.WIDTH) - 2 * px(self.PAD)
        top = self._body_top + px(self.PAD)
        painter.setFont(title_font)
        painter.setPen(QtGui.QColor(self._colors["heading_text"]))
        painter.drawText(QtCore.QRect(px(self.PAD), top, inner, self._title_h), int(Qt.TextWordWrap), self._title)
        painter.setFont(text_font)
        painter.setPen(QtGui.QColor(self._colors["tooltip_text"]))
        painter.drawText(QtCore.QRect(px(self.PAD), top + self._title_h + 4, inner, 10000),
                         int(Qt.TextWordWrap | Qt.AlignTop | Qt.AlignLeft), self._text)
        painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        QtWidgets.QWidget.keyPressEvent(self, event)

    def hideEvent(self, event):
        self.closed_at = time.monotonic()
        QtWidgets.QWidget.hideEvent(self, event)


class HelpButton(QtWidgets.QAbstractButton, Themed):
    """A small round "?" beside a title; a click opens a Balloon with a short description of that part of the
    panel, a second click (or one elsewhere) closes it."""

    SIZE = 16

    def __init__(self, theme, title, text, parent=None):
        QtWidgets.QAbstractButton.__init__(self, parent)
        self._title, self._text, self._balloon_theme = title, text, theme
        self.balloon = None
        self.setFixedSize(px(self.SIZE), px(self.SIZE))
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAccessibleName("Help: " + title)
        self.clicked.connect(self.toggle)
        self.bind_theme(theme)

    def toggle(self):
        balloon = self.balloon
        if balloon is not None and balloon.isVisible():
            balloon.close()
            return
        if balloon is not None and time.monotonic() - balloon.closed_at < 0.3:
            return  # This click's press closed the open balloon (a popup closes on any press outside it).
        if balloon is None:
            self.balloon = balloon = Balloon(self._balloon_theme, self.window())
            balloon.destroyed.connect(lambda *_: setattr(self, "balloon", None))
        balloon.show_for(self, self._title, self._text)
        self.update()

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def enterEvent(self, event):
        self.update()
        QtWidgets.QAbstractButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.update()
        QtWidgets.QAbstractButton.leaveEvent(self, event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        active = self.underMouse() or (self.balloon is not None and self.balloon.isVisible())
        tone = QtGui.QColor(self._colors["accent" if active else "muted_text"])
        rect = QtCore.QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.setPen(QtGui.QPen(tone, 1.2))
        fill = QtGui.QColor(tone)
        fill.setAlpha(45 if active else 0)
        painter.setBrush(fill)
        painter.drawEllipse(rect)
        font = QtGui.QFont(self.font())
        font.setBold(True)
        font.setPixelSize(px(10))
        painter.setFont(font)
        painter.drawText(self.rect(), int(Qt.AlignCenter), "?")
        painter.end()


class SuggestionDelegate(QtWidgets.QStyledItemDelegate):
    """Rows of the search suggestions: the text starts exactly where the search field's text does (no stair
    step), and hover / selection only colour the background."""

    def __init__(self, field, colors, parent=None):
        QtWidgets.QStyledItemDelegate.__init__(self, parent)
        self.field = field
        self.colors = colors  # A callable returning the theme colours.

    def text_left(self, view):
        """Where the field's text begins, in the list's viewport coordinates."""
        option = QtWidgets.QStyleOptionFrame()
        self.field.initStyleOption(option)
        try:
            contents = self.field.style().subElementRect(QtWidgets.QStyle.SE_LineEditContents, option, self.field)
        except RuntimeError:  # The style's wrapper outlived it (qt_compat.repolish): near enough without it.
            contents = self.field.contentsRect()
        start = self.field.mapToGlobal(QtCore.QPoint(contents.left() + 2, 0))  # Qt's own 2 px inner margin.
        return view.viewport().mapFromGlobal(start).x()

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), option.fontMetrics.height() + px(10))

    def paint(self, painter, option, index):
        colors = self.colors()
        painter.save()
        selected = option.state & QtWidgets.QStyle.State_Selected or option.state & QtWidgets.QStyle.State_MouseOver
        if selected:
            painter.fillRect(option.rect, QtGui.QColor(colors["selected"]))
        painter.setPen(QtGui.QColor(colors["selected_text"] if selected else colors["field_text"]))
        view = self.parent()
        left = max(4, self.text_left(view)) if view is not None else 8
        rect = option.rect.adjusted(left - option.rect.left(), 0, -left, 0)
        text = option.fontMetrics.elidedText(index.data() or "", Qt.ElideRight, rect.width())
        painter.drawText(rect, int(Qt.AlignLeft | Qt.AlignVCenter), text)
        painter.restore()


class Shimmer(QtWidgets.QWidget):
    """A light diagonal band that sweeps across `target` every few seconds to draw the eye. Painted here over the button, clipped to its rounded corners; mouse events pass through."""

    SWEEP_MS = 900
    PAUSE_MS = 2600
    SLANT = 0.45  # The band leans this much (horizontal per vertical).

    def __init__(self, target):
        QtWidgets.QWidget.__init__(self, target)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._active = False
        self._started = time.monotonic()
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.update)
        target.installEventFilter(self)
        self.hide()

    def set_active(self, on):
        self._active = bool(on)
        self._started = time.monotonic()
        self._follow()

    def _follow(self):
        target = self.parentWidget()
        running = self._active and target.isVisible()
        if running:
            self.setGeometry(target.rect())
            self.raise_()
            self.show()
            self._timer.start()
        else:
            self._timer.stop()
            self.hide()

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.Show, QtCore.QEvent.Hide, QtCore.QEvent.Resize):
            self._follow()
        return False

    def phase(self):
        """0..1 while the band sweeps, None in the pause."""
        elapsed = (time.monotonic() - self._started) * 1000.0 % (self.SWEEP_MS + self.PAUSE_MS)
        return elapsed / self.SWEEP_MS if elapsed < self.SWEEP_MS else None

    def paintEvent(self, event):
        f = self.phase()
        if f is None:
            return
        f = f * f * (3.0 - 2.0 * f)  # Ease in and out.
        width, height = float(self.width()), float(self.height())
        band = max(px(28), width * 0.35)
        x = -band - self.SLANT * height + f * (width + 2.0 * band + 2.0 * self.SLANT * height)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        clip = QtGui.QPainterPath()
        clip.addRoundedRect(QtCore.QRectF(self.rect()), px(6), px(6))
        painter.setClipPath(clip)
        # Across the band (perpendicular to its slant): clear, a soft light middle, clear.
        gradient = QtGui.QLinearGradient(x - band / 2.0, 0.0, x + band / 2.0, self.SLANT * band)
        for stop, alpha in ((0.0, 0), (0.42, 46), (0.5, 80), (0.58, 46), (1.0, 0)):
            gradient.setColorAt(stop, QtGui.QColor(255, 255, 255, alpha))
        painter.fillRect(self.rect(), QtGui.QBrush(gradient))
        painter.end()


class Marquee(QtWidgets.QWidget, Themed):
    """One line of text in the normal text colour; when it does not fit it runs from right to left in a loop
   , pausing a moment each time it comes round."""

    GAP = 60       # Pixels between the end of the text and its next start.
    STEP_MS = 30   # One pixel per step.
    PAUSE_MS = 1500

    def __init__(self, theme, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._text, self._offset, self._color = "", 0, QtGui.QColor("#d0d0d0")
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(self.STEP_MS)
        self.timer.timeout.connect(self._step)
        self._pause = QtCore.QTimer(self)
        self._pause.setSingleShot(True)
        self._pause.timeout.connect(self._restart)
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._color = QtGui.QColor(colors.get("text", "#d0d0d0"))
        self.update()

    def setText(self, text):
        self._text = text or ""
        self.setToolTip(self._text)
        self._offset = 0
        self._sync()
        self.update()

    def text(self):
        return self._text

    def sizeHint(self):
        return QtCore.QSize(px(100), self.fontMetrics().height() + px(2))

    def _width(self):
        metrics = self.fontMetrics()
        width = getattr(metrics, "horizontalAdvance", None) or metrics.width
        return width(self._text)

    def _running(self):
        return self.isVisible() and self._width() > self.width()

    def _sync(self):
        if self._running():
            if not self.timer.isActive() and not self._pause.isActive():
                self._pause.start(self.PAUSE_MS)
        else:
            self.timer.stop()
            self._pause.stop()
            self._offset = 0

    def _restart(self):
        if self._running():
            self.timer.start()

    def _step(self):
        self._offset += 1
        if self._offset >= self._width() + px(self.GAP):
            self._offset = 0
            self.timer.stop()
            self._pause.start(self.PAUSE_MS)
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(self._color)
        rect = self.rect()
        flags = int(Qt.AlignLeft | Qt.AlignVCenter)
        if self._running():
            width = self._width()
            painter.drawText(QtCore.QRect(-self._offset, 0, width, rect.height()), flags, self._text)
            painter.drawText(QtCore.QRect(width + px(self.GAP) - self._offset, 0, width, rect.height()), flags,
                             self._text)
        else:
            painter.drawText(rect, flags, self._text)
        painter.end()

    def resizeEvent(self, event):
        QtWidgets.QWidget.resizeEvent(self, event)
        self._sync()

    def showEvent(self, event):
        QtWidgets.QWidget.showEvent(self, event)
        self._sync()

    def hideEvent(self, event):
        self.timer.stop()
        self._pause.stop()
        QtWidgets.QWidget.hideEvent(self, event)


class ElidedLabel(QtWidgets.QLabel):
    """One line of text that shortens itself with "..." instead of widening its layout; the full text is the
    tooltip."""

    def __init__(self, text="", parent=None):
        QtWidgets.QLabel.__init__(self, parent)
        self._full = ""
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
        self.setMinimumWidth(0)
        self.setText(text)

    def setText(self, text):
        self._full = text or ""
        self.setToolTip(self._full)
        self._elide()

    def text(self):
        return self._full

    def _elide(self):
        width = max(0, self.contentsRect().width())
        QtWidgets.QLabel.setText(self, self.fontMetrics().elidedText(self._full, Qt.ElideMiddle, width)
                                 if width > 0 else self._full)

    def resizeEvent(self, event):
        QtWidgets.QLabel.resizeEvent(self, event)
        self._elide()


def muted(text, wrap=True):
    label = QtWidgets.QLabel(text)
    label.setObjectName("toolMuted")
    label.setWordWrap(wrap)
    return label
```
