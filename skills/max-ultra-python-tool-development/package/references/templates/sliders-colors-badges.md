# Template: Sliders, colours and badges

One-handle and two-handle sliders in the tool's look, keyboard-driven and never changed by the wheel (`sliders.py`); a colour field that opens a rounded picker with a saturation square, a hue strip, a hex value, presets and recent colours (`colors.py`); count badges on the corner of a button, status badges, removable tags, status dots, and coloured filter pills with counts as in the MaxPkg Package Manager (`badges.py`).

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) through Max Ultra MCP with the windows off screen (the controls trainer checks), and shown on screen in 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3).

## `python/mytool/ui/sliders.py`

```python
"""Sliders in the tool's look: one handle (Slider) or two (RangeSlider), lying or standing (`vertical`).

A rounded track in `recessed` with a 1 px `border`, the chosen part filled in `accent`, round handles in `text` with
an accent edge, and the value in a small field-coloured label: on the right of a lying slider (30 px high like every
control), under a standing one (the smallest value at the bottom, like a mixer's fader). Drag a handle, click the
track to move the nearest handle there, or use the keyboard (arrows, Page Up / Down, Home / End; with two handles the
keys move the one clicked last). The mouse wheel never changes a value: it scrolls the page.
"""

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal
from ..ui_scale import px
from .controls import CONTROL_HEIGHT, Themed


def _event_point(event):
    position = getattr(event, "position", None)
    return position() if position else QtCore.QPointF(event.pos())


class _SliderBase(QtWidgets.QWidget, Themed):
    """Shared painting and value handling. `decimals` 0 gives whole numbers; `suffix` follows the value ("%")."""

    HANDLE = 16  # Logical px
    TRACK = 6
    LABEL = 22  # Height of the value label

    def __init__(self, theme, minimum, maximum, step=1.0, decimals=0, suffix="", label_chars=None, vertical=False,
                 parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._minimum, self._maximum = float(minimum), float(maximum)
        self._step = float(step)
        self._decimals = decimals
        self._suffix = suffix
        self._label_chars = label_chars
        self.vertical = vertical
        self._drag = None  # Index of the handle being dragged
        self._hover = None
        if vertical:
            self.setMinimumHeight(px(140))
            self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        else:
            self.setFixedHeight(px(CONTROL_HEIGHT))
            self.setMinimumWidth(px(140))
            self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.bind_theme(theme)

    def _fit_width(self):
        """A standing slider is as wide as its value label (at least a control's height)."""
        if self.vertical:
            self.setFixedWidth(max(px(CONTROL_HEIGHT) + px(14), self._label_width()))

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.FontChange:
            self._fit_width()  # The interface-size font arrived: the label is wider
        QtWidgets.QWidget.changeEvent(self, event)

    # ---- values ------------------------------------------------------------------------------------------------
    def _snap(self, value):
        value = max(self._minimum, min(self._maximum, float(value)))
        steps = round((value - self._minimum) / self._step)
        value = self._minimum + steps * self._step
        return round(value, self._decimals) if self._decimals else float(int(round(value)))

    def text_of(self, value):
        text = "{:.{}f}".format(value, self._decimals) if self._decimals else "{:,}".format(int(round(value)))
        return text + self._suffix

    def _label_text(self):
        raise NotImplementedError

    def _values(self):
        raise NotImplementedError

    def _set_handle(self, index, value):
        raise NotImplementedError

    # ---- geometry: positions are measured along the track (x when lying, y when standing) -------------------------
    def _label_width(self):
        metrics = self.fontMetrics()
        sample = self._label_chars or self._label_text()
        width = metrics.horizontalAdvance(sample) if hasattr(metrics, "horizontalAdvance") else metrics.width(sample)
        return width + px(16)

    def _track_rect(self):
        handle = px(self.HANDLE)
        if self.vertical:
            bottom = self.height() - px(self.LABEL) - px(10)
            return QtCore.QRectF((self.width() - px(self.TRACK)) / 2.0, handle / 2.0 + 1, px(self.TRACK),
                                 max(10.0, bottom - handle - 2))
        right = self.width() - self._label_width() - px(10)
        return QtCore.QRectF(handle / 2.0 + 1, (self.height() - px(self.TRACK)) / 2.0,
                             max(10.0, right - handle - 2), px(self.TRACK))

    def _share(self, value):
        return 0.0 if self._maximum == self._minimum else (value - self._minimum) / (self._maximum - self._minimum)

    def _x_of(self, value):
        """The position of `value` along the track (the smallest at the left, or at the bottom when standing)."""
        track = self._track_rect()
        if self.vertical:
            return track.bottom() - track.height() * self._share(value)
        return track.left() + track.width() * self._share(value)

    def _along(self, point):
        return point.y() if self.vertical else point.x()

    def _value_at(self, position):
        track = self._track_rect()
        if self.vertical:
            share = (track.bottom() - position) / max(1.0, track.height())
        else:
            share = (position - track.left()) / max(1.0, track.width())
        return self._snap(self._minimum + share * (self._maximum - self._minimum))

    def _nearest(self, position):
        positions = [abs(self._x_of(value) - position) for value in self._values()]
        best = min(range(len(positions)), key=lambda index: positions[index])
        if len(positions) == 2 and positions[0] == positions[1]:  # Both handles in one place: pick by direction
            upper = self._x_of(self._values()[1])
            best = 1 if (position < upper if self.vertical else position > upper) else 0
        return best

    def _centre(self, value):
        along = self._x_of(value)
        return QtCore.QPointF(self.width() / 2.0, along) if self.vertical else QtCore.QPointF(along, self.height() / 2.0)

    # ---- mouse and keys ----------------------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or not self.isEnabled():
            return
        position = self._along(_event_point(event))
        self._drag = self._nearest(position)
        self._active = self._drag
        self._set_handle(self._drag, self._value_at(position))
        self.update()

    def mouseMoveEvent(self, event):
        point = _event_point(event)
        position = self._along(point)
        if self._drag is not None:
            self._set_handle(self._drag, self._value_at(position))
        else:
            near = self._track_rect().adjusted(-px(10), -px(10), px(10), px(10)).contains(point)
            hover = self._nearest(position) if near else None
            if hover != self._hover:
                self._hover = hover
                self.update()

    def mouseReleaseEvent(self, event):
        self._drag = None
        self.update()

    def leaveEvent(self, event):
        self._hover = None
        self.update()
        QtWidgets.QWidget.leaveEvent(self, event)

    def wheelEvent(self, event):
        event.ignore()  # Scrolling never changes a value: the page under the slider scrolls

    def keyPressEvent(self, event):
        key = event.key()
        index = getattr(self, "_active", 0)
        value = self._values()[index]
        page = (self._maximum - self._minimum) / 10.0
        moves = {Qt.Key_Left: -self._step, Qt.Key_Down: -self._step, Qt.Key_Right: self._step, Qt.Key_Up: self._step,
                 Qt.Key_PageDown: -page, Qt.Key_PageUp: page}
        if key in moves:
            self._set_handle(index, self._snap(value + moves[key]))
        elif key == Qt.Key_Home:
            self._set_handle(index, self._minimum)
        elif key == Qt.Key_End:
            self._set_handle(index, self._maximum)
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)
            return
        self.update()

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    # ---- painting ----------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        colors = self._colors
        enabled = self.isEnabled()
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        track = self._track_rect()
        radius = px(self.TRACK) / 2.0
        painter.setPen(QtGui.QPen(QtGui.QColor(colors["border" if enabled else "disabled_border"]), 1))
        painter.setBrush(QtGui.QColor(colors["recessed" if enabled else "disabled_surface"]))
        painter.drawRoundedRect(track, radius, radius)
        values = self._values()
        if self.vertical:  # The chosen part: from the low handle (or the bottom) up to the high one
            low = self._x_of(values[0]) if len(values) == 2 else track.bottom()
            high = self._x_of(values[-1])
            chosen = QtCore.QRectF(track.left(), high, track.width(), max(0.0, low - high))
        else:
            start = self._x_of(values[0]) if len(values) == 2 else track.left()
            end = self._x_of(values[-1])
            chosen = QtCore.QRectF(start, track.top(), max(0.0, end - start), track.height())
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QColor(colors["accent" if enabled else "accent_disabled"]))
        painter.drawRoundedRect(chosen, radius, radius)
        handle = px(self.HANDLE)
        for index, value in enumerate(values):
            centre = self._centre(value)
            active = enabled and (self._drag == index or self._hover == index or
                                  (self.hasFocus() and getattr(self, "_active", 0) == index))
            size = handle + (px(2) if active else 0)
            if active:  # A soft accent ring around the handle under the pointer or with the focus
                ring = QtGui.QColor(colors["accent"])
                ring.setAlpha(60)
                painter.setPen(Qt.NoPen)  # Not the previous handle's edge: the same soft ring on both handles
                painter.setBrush(ring)
                painter.drawEllipse(centre, size / 2.0 + px(4), size / 2.0 + px(4))
            painter.setPen(QtGui.QPen(QtGui.QColor(colors["accent" if enabled else "disabled_border"]), px(2)))
            painter.setBrush(QtGui.QColor(colors["text" if enabled else "disabled_text"]))
            painter.drawEllipse(centre, size / 2.0 - 1, size / 2.0 - 1)
        width = min(self._label_width(), self.width())
        if self.vertical:
            label = QtCore.QRectF((self.width() - width) / 2.0, self.height() - px(self.LABEL), width, px(self.LABEL))
        else:
            label = QtCore.QRectF(self.width() - width, (self.height() - px(self.LABEL)) / 2.0, width, px(self.LABEL))
        painter.setPen(QtGui.QPen(QtGui.QColor(colors["field_border"]), 1))
        painter.setBrush(QtGui.QColor(colors["field"]))
        painter.drawRoundedRect(label.adjusted(0.5, 0.5, -0.5, -0.5), px(6), px(6))
        painter.setPen(QtGui.QColor(colors["field_text" if enabled else "disabled_text"]))
        painter.drawText(label, int(Qt.AlignCenter), self._label_text())
        painter.end()


class Slider(_SliderBase):
    """One handle: a value between `minimum` and `maximum` in steps of `step`; `vertical` stands it up."""

    valueChanged = Signal(float)

    def __init__(self, theme, minimum=0, maximum=100, value=0, step=1, decimals=0, suffix="", vertical=False,
                 parent=None):
        self._value = float(value)
        _SliderBase.__init__(self, theme, minimum, maximum, step, decimals, suffix, vertical=vertical, parent=parent)
        self._value = self._snap(value)
        self._label_chars = max(self.text_of(self._minimum), self.text_of(self._maximum), key=len)
        self.setAccessibleName("Slider")
        self._fit_width()

    def value(self):
        return self._value

    def setValue(self, value):
        self._set_handle(0, self._snap(value))

    def _values(self):
        return (self._value,)

    def _set_handle(self, index, value):
        if value != self._value:
            self._value = value
            self.update()
            self.valueChanged.emit(value)

    def _label_text(self):
        return self.text_of(self._value)


class RangeSlider(_SliderBase):
    """Two handles: a low and a high value; the handles never pass each other; `vertical` stands it up."""

    rangeChanged = Signal(float, float)

    def __init__(self, theme, minimum=0, maximum=100, low=20, high=80, step=1, decimals=0, suffix="", vertical=False,
                 parent=None):
        self._low, self._high = float(low), float(high)
        _SliderBase.__init__(self, theme, minimum, maximum, step, decimals, suffix, vertical=vertical, parent=parent)
        self._low, self._high = self._snap(min(low, high)), self._snap(max(low, high))
        widest = max(self.text_of(self._minimum), self.text_of(self._maximum), key=len)
        self._label_chars = widest + " - " + widest
        self.setAccessibleName("Range slider")
        self._fit_width()

    def values(self):
        return self._low, self._high

    def setValues(self, low, high):
        self._low, self._high = self._snap(min(low, high)), self._snap(max(low, high))
        self.update()
        self.rangeChanged.emit(self._low, self._high)

    def _values(self):
        return (self._low, self._high)

    def _set_handle(self, index, value):
        if index == 0:
            value = min(value, self._high)
            changed = value != self._low
            self._low = value
        else:
            value = max(value, self._low)
            changed = value != self._high
            self._high = value
        if changed:
            self.update()
            self.rangeChanged.emit(self._low, self._high)

    def _label_text(self):
        return "{} - {}".format(self.text_of(self._low), self.text_of(self._high))
```

## `python/mytool/ui/colors.py`

```python
"""Colour picking in the tool's look: a field with a swatch (ColorButton) that opens a palette (ColorPopup).

The palette: a saturation / brightness square and a hue strip (drag either), the value as HEX (#RRGGBB), RGB (0-255
each) or HSV (hue 0-359, saturation and value 0-100) with a switch between them (remembered), a pipette that picks
a colour anywhere on the screens (ScreenPicker), ready swatches, a colour harmony of the current colour
(complementary, analogous, triad, split complementary, tetrad or shades; remembered) and the colours picked recently in
this session. The
value changes live while dragging; Esc puts the colour the palette opened with back; Enter or a click outside keeps
the new one. The popup is a masked frameless window like every other popup of the tool (no translucent windows inside
Max) and casts Windows' light popup shadow along its mask.
"""

from ..qt_compat import (QtCore, QtGui, QtWidgets, Qt, Signal, inherit_fonts, live_screens, own_keyboard, scale_font,
                         work_area)
from ..ui_scale import px, space
from . import controls
from .controls import Button, Segmented, round_popup
from .pickers import Stepper

PRESETS = ("#e5e5e5", "#a3a3a3", "#525252", "#1f1f1f", "#e06c6c", "#e0a05a", "#e0d36a", "#7fbf6a", "#5ab8c4",
           "#6a8fe0", "#a07ae0", "#d07ab8")
_recent = []  # Colours picked in this session, newest first
ZOOMS = (4, 24)  # The loupe's enlargement, from far to close
_zoom = [10]  # The pipette's last enlargement
_mode = ["hex"]  # The value format chosen last (HEX, RGB or HSV), for every colour field of the tool
# Colour harmonies: hue offsets in degrees from the current colour; None = shades of it from dark to light
HARMONIES = (("complementary", "Complementary", (0, 180)), ("analogous", "Analogous", (-30, 0, 30)),
             ("triad", "Triad", (0, 120, 240)), ("split", "Split complementary", (0, 150, 210)),
             ("tetrad", "Tetrad", (0, 90, 180, 270)), ("shades", "Shades", None))
_harmony = ["analogous"]  # The harmony chosen last
MODES = (("hex", "HEX", "#RRGGBB"), ("rgb", "RGB", "Red, green and blue, 0-255 each"),
         ("hsv", "HSV", "Hue 0-359, saturation and value 0-100"))


def _point(event):
    position = getattr(event, "position", None)
    return position().toPoint() if position else event.pos()


class _SaturationValue(QtWidgets.QWidget):
    """The square: saturation left to right, brightness bottom to top, for the current hue."""

    changed = Signal()

    def __init__(self, popup):
        QtWidgets.QWidget.__init__(self)
        self.popup = popup
        self.setFixedSize(px(260), px(150))  # As wide as a row of 12 swatches
        self.setCursor(Qt.CrossCursor)

    def _pick(self, event):
        point = _point(event)
        saturation = max(0.0, min(1.0, point.x() / float(max(1, self.width() - 1))))
        value = max(0.0, min(1.0, 1.0 - point.y() / float(max(1, self.height() - 1))))
        self.popup.set_hsv(self.popup.hue, saturation, value)

    def mousePressEvent(self, event):
        self._pick(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._pick(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect())
        path = QtGui.QPainterPath()
        path.addRoundedRect(rect, px(6), px(6))
        painter.setClipPath(path)
        painter.fillRect(rect, QtGui.QColor.fromHsvF(self.popup.hue, 1.0, 1.0))
        white = QtGui.QLinearGradient(rect.topLeft(), rect.topRight())
        white.setColorAt(0.0, QtGui.QColor(255, 255, 255, 255))
        white.setColorAt(1.0, QtGui.QColor(255, 255, 255, 0))
        painter.fillRect(rect, QtGui.QBrush(white))
        black = QtGui.QLinearGradient(rect.topLeft(), rect.bottomLeft())
        black.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
        black.setColorAt(1.0, QtGui.QColor(0, 0, 0, 255))
        painter.fillRect(rect, QtGui.QBrush(black))
        centre = QtCore.QPointF(self.popup.saturation * (rect.width() - 1), (1.0 - self.popup.value) * (rect.height() - 1))
        painter.setClipping(False)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 160), px(3)))
        painter.drawEllipse(centre, px(6), px(6))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), px(2)))
        painter.drawEllipse(centre, px(6), px(6))
        painter.end()


class _HueStrip(QtWidgets.QWidget):
    """The hue strip under the square."""

    def __init__(self, popup):
        QtWidgets.QWidget.__init__(self)
        self.popup = popup
        self.setFixedSize(px(260), px(14))
        self.setCursor(Qt.PointingHandCursor)

    def _pick(self, event):
        hue = max(0.0, min(0.999, _point(event).x() / float(max(1, self.width() - 1))))
        self.popup.set_hsv(hue, self.popup.saturation, self.popup.value)

    def mousePressEvent(self, event):
        self._pick(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._pick(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0, px(2), 0, -px(2))
        gradient = QtGui.QLinearGradient(rect.topLeft(), rect.topRight())
        for step in range(7):
            gradient.setColorAt(step / 6.0, QtGui.QColor.fromHsvF(min(0.999, step / 6.0), 1.0, 1.0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QBrush(gradient))
        painter.drawRoundedRect(rect, rect.height() / 2.0, rect.height() / 2.0)
        x = self.popup.hue * (self.width() - 1)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 160), px(3)))
        painter.setBrush(QtGui.QColor.fromHsvF(self.popup.hue, 1.0, 1.0))
        handle = QtCore.QRectF(x - px(4), 0, px(8), self.height())
        painter.drawRoundedRect(handle, px(3), px(3))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), px(2)))
        painter.drawRoundedRect(handle, px(3), px(3))
        painter.end()


class _Swatch(QtWidgets.QAbstractButton):
    """One ready colour; a click picks it (and closes the palette, unless `keep_open`: the harmony row)."""

    SIZE = 18

    def __init__(self, color, popup, keep_open=False, size=None):
        QtWidgets.QAbstractButton.__init__(self)
        self.color = color
        self.popup = popup
        width, height = size or (self.SIZE, self.SIZE)
        self.setFixedSize(px(width), px(height))
        self.setCursor(Qt.PointingHandCursor)
        controls.set_tip(self, color)
        self.clicked.connect(lambda: popup.set_color(self.color, keep_open=keep_open))

    def set_color(self, color):
        self.color = color
        controls.set_tip(self, color)
        self.update()

    def paintEvent(self, event):
        colors = self.popup.theme.colors
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(1, 1, -1, -1)
        chosen = QtGui.QColor(self.color).name() == self.popup.color().name()
        painter.setPen(QtGui.QPen(QtGui.QColor(colors["accent" if (chosen or self.underMouse()) else "border"]),
                                  px(2) if chosen else 1))
        painter.setBrush(QtGui.QColor(self.color))
        painter.drawRoundedRect(rect, px(4), px(4))
        painter.end()

    def enterEvent(self, event):
        self.update()
        QtWidgets.QAbstractButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.update()
        QtWidgets.QAbstractButton.leaveEvent(self, event)


def grab_screens():
    """[(geometry, picture)] of every screen: its logical geometry and a picture of what it shows, in device pixels.
    Only kept in memory while the user picks; never saved."""
    shots = []
    for screen, _area, geometry in live_screens():
        try:
            picture = screen.grabWindow(0)
        except RuntimeError:  # A screen that went away while grabbing
            continue
        if not picture.isNull():
            shots.append((geometry, picture))
    return shots


class _PickerPane(QtWidgets.QWidget):
    """One screen shown frozen as it was (an opaque picture, never a translucent window), the cross cursor, and a
    loupe beside the pointer: the pixels around it enlarged with the centre one framed, and its #RRGGBB."""

    LOUPE = 110  # Logical px across the enlarged pixels; the wheel changes how many pixels fill it (ScreenPicker.zoom)

    def __init__(self, picker, geometry, picture):
        QtWidgets.QWidget.__init__(self, None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
                                   Qt.NoDropShadowWindowHint)
        self.setObjectName("toolScreenPicker")
        self.picker = picker
        self.image = picture.toImage()
        self.ratio = self.image.width() / float(max(1, geometry.width()))  # Device pixels per logical pixel
        self.setGeometry(geometry)
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.point = None
        scale_font(self)

    def color_at(self, point, dx=0, dy=0):
        x = min(max(0, int(point.x() * self.ratio) + dx), self.image.width() - 1)
        y = min(max(0, int(point.y() * self.ratio) + dy), self.image.height() - 1)
        return self.image.pixelColor(x, y)

    def mouseMoveEvent(self, event):
        self.point = _point(event)
        self.update()

    def leaveEvent(self, event):
        self.point = None
        self.update()
        QtWidgets.QWidget.leaveEvent(self, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.picker.finish(self.color_at(_point(event)).name())
        else:
            self.picker.finish(None)  # The right button cancels, as Esc

    def wheelEvent(self, event):
        """The wheel zooms the loupe: forward closer (fewer, larger pixels), back further."""
        delta = event.angleDelta().y()
        if delta:
            self.picker.set_zoom(self.picker.zoom + (2 if delta > 0 else -2))
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.picker.finish(None)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.point is not None:
            self.picker.finish(self.color_at(self.point).name())

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(QtCore.QRectF(self.rect()), self.image, QtCore.QRectF(self.image.rect()))
        if self.point is not None:
            self._paint_loupe(painter)
        painter.end()

    def _paint_loupe(self, painter):
        colors = self.picker.theme.colors
        cell = px(self.picker.zoom)
        cells = max(3, int(px(self.LOUPE) / cell))
        cells -= 0 if cells % 2 else 1  # Odd: one centre pixel
        half = cells // 2
        grid = cell * cells
        pad, line = px(6), self.fontMetrics().height() + px(8)
        width, height = grid + 2 * pad, grid + 2 * pad + line
        x, y = self.point.x() + px(18), self.point.y() + px(18)  # Below right of the pointer, flipped at the edges
        if x + width > self.width():
            x = self.point.x() - px(18) - width
        if y + height > self.height():
            y = self.point.y() - px(18) - height
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        card = QtCore.QRectF(x, y, width, height)
        painter.setPen(QtGui.QPen(QtGui.QColor(colors["active_border"]), 1))
        painter.setBrush(QtGui.QColor(colors["popup"]))
        painter.drawRoundedRect(card.adjusted(0.5, 0.5, -0.5, -0.5), px(8), px(8))
        area = QtCore.QRectF(x + pad, y + pad, grid, grid)
        clip = QtGui.QPainterPath()
        clip.addRoundedRect(area, px(4), px(4))
        painter.save()
        painter.setClipPath(clip)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        for row in range(cells):
            for column in range(cells):
                painter.fillRect(QtCore.QRectF(area.left() + column * cell, area.top() + row * cell, cell, cell),
                                 self.color_at(self.point, column - half, row - half))
        painter.restore()
        centre = QtCore.QRectF(area.left() + half * cell, area.top() + half * cell, cell, cell)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 200), 1))
        painter.drawRect(centre.adjusted(-1, -1, 1, 1))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1))
        painter.drawRect(centre)
        chosen = self.color_at(self.point)
        swatch = QtCore.QRectF(x + pad, area.bottom() + px(6), line - px(12), line - px(12))
        painter.setPen(QtGui.QPen(QtGui.QColor(colors["border"]), 1))
        painter.setBrush(chosen)
        painter.drawRoundedRect(swatch, px(3), px(3))
        painter.setPen(QtGui.QColor(colors["text"]))
        painter.drawText(QtCore.QRectF(swatch.right() + px(6), area.bottom() + px(2), grid, line - px(4)),
                         int(Qt.AlignVCenter | Qt.AlignLeft), chosen.name())
        painter.setPen(QtGui.QColor(colors["muted_text"]))
        painter.drawText(QtCore.QRectF(swatch.right() + px(6), area.bottom() + px(2), grid - swatch.width() - px(6),
                                       line - px(4)), int(Qt.AlignVCenter | Qt.AlignRight),
                         "{}x".format(self.picker.zoom))


class ScreenPicker(QtCore.QObject):
    """Pick a colour anywhere on the screens: every screen is shown frozen as it was with a loupe at the pointer; a
    click picks, Enter picks the pixel under the pointer, Esc or the right button cancels. `on_done(name)` gets
    "#rrggbb" or None. `shots`: [(geometry, picture)] instead of grabbing the screens (tests)."""

    def __init__(self, theme, on_done, shots=None, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.theme = theme
        self.on_done = on_done
        self.zoom = _zoom[0]  # Times each screen pixel is enlarged in the loupe (the wheel changes it)
        self.panes = [_PickerPane(self, geometry, picture)
                      for geometry, picture in (grab_screens() if shots is None else shots)]

    def start(self):
        if not self.panes:
            self.finish(None)
            return False
        for pane in self.panes:
            pane.show()
        own_keyboard(self.panes)  # Esc and Enter reach the picker, not 3ds Max
        pointer = QtGui.QCursor.pos()  # Read only: the pointer is never moved
        pane = next((p for p in self.panes if p.geometry().contains(pointer)), self.panes[0])
        pane.raise_()
        pane.activateWindow()
        pane.setFocus()
        return True

    def set_zoom(self, zoom):
        self.zoom = _zoom[0] = max(ZOOMS[0], min(ZOOMS[1], zoom))
        for pane in self.panes:
            pane.update()

    def finish(self, name):
        panes, self.panes = self.panes, []
        for pane in panes:
            pane.hide()
            pane.deleteLater()
        done, self.on_done = self.on_done, None
        if done is not None:
            done(name)


class ColorPopup(QtWidgets.QWidget):
    """The palette of a ColorButton (see the module)."""

    changed = Signal(str)  # Live while choosing
    closed = Signal(str)   # The colour it closed with

    def __init__(self, theme, parent):
        # A Qt.Popup without NoDropShadowWindowHint: Windows' light popup shadow follows the rounded mask
        QtWidgets.QWidget.__init__(self, parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("toolColorPopup")
        self.theme = theme
        self.hue, self.saturation, self.value = 0.0, 0.0, 0.0
        self._original = "#000000"
        self._field = None
        self.picker = None
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame = QtWidgets.QFrame()
        frame.setObjectName("toolPopupFrame")
        outer.addWidget(frame)
        body = QtWidgets.QVBoxLayout(frame)
        body.setContentsMargins(space(12), space(12), space(12), space(12))
        body.setSpacing(space(8))
        self.square = _SaturationValue(self)
        self.strip = _HueStrip(self)
        body.addWidget(self.square)
        body.addWidget(self.strip)
        modes = QtWidgets.QHBoxLayout()  # The value's format at the left, the pipette at the right
        modes.setSpacing(space(6))
        self.mode = Segmented(MODES, theme, _mode[0])
        self.mode.changed.connect(self.set_mode)
        modes.addWidget(self.mode, 1)  # The whole row up to the pipette: no clipped labels
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(6))
        self.preview = QtWidgets.QLabel()
        self.preview.setFixedSize(px(30), px(30))
        self.hex = QtWidgets.QLineEdit()
        self.hex.setObjectName("toolHexField")
        self.hex.setMaxLength(7)
        # Parented: a validator that only Python holds is deleted while the field still uses it
        self.hex.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"#?[0-9A-Fa-f]{0,6}"),
                                                                self.hex))
        self.hex.textEdited.connect(self._typed)
        self.hex.returnPressed.connect(self.close)
        self.pipette = Button("", theme, icon="pipette", tooltip="Pick a colour from the screen (Esc cancels)")
        self.pipette.clicked.connect(self.pick_from_screen)
        modes.addWidget(self.pipette)
        body.addLayout(modes)
        self._syncing = False
        self.rgb = [Stepper(theme, 0, 255, 0) for _part in range(3)]
        self.hsv = [Stepper(theme, 0, 359, 0), Stepper(theme, 0, 100, 0), Stepper(theme, 0, 100, 0)]
        for stepper in self.rgb:
            stepper.valueChanged.connect(self._from_rgb)
        for stepper in self.hsv:
            stepper.valueChanged.connect(self._from_hsv)
        self.pages = QtWidgets.QStackedWidget()
        self.pages.addWidget(self._page((("Hex", self.hex),)))
        self.pages.addWidget(self._page(zip(("R", "G", "B"), self.rgb)))
        self.pages.addWidget(self._page(zip(("H \u00b0", "S %", "V %"), self.hsv)))
        row.addWidget(self.preview, 0, Qt.AlignBottom)
        row.addWidget(self.pages, 1)
        body.addLayout(row)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(space(4))
        for index, color in enumerate(PRESETS):
            grid.addWidget(_Swatch(color, self), index // 12, index % 12)
        body.addLayout(grid)
        harmony_head = QtWidgets.QHBoxLayout()
        harmony_head.setSpacing(space(6))
        harmony_title = QtWidgets.QLabel("Harmony")
        harmony_title.setObjectName("toolCaption")
        self.harmony = controls.ComboBox()
        for key, label, _offsets in HARMONIES:
            self.harmony.addItem(label, key)
        self.harmony.setCurrentIndex(max(0, self.harmony.findData(_harmony[0])))
        self.harmony.currentIndexChanged.connect(self._harmony_chosen)
        harmony_head.addWidget(harmony_title)
        harmony_head.addStretch(1)
        harmony_head.addWidget(self.harmony)
        body.addLayout(harmony_head)
        harmony_row = QtWidgets.QHBoxLayout()
        harmony_row.setSpacing(space(4))
        self.harmony_swatches = [_Swatch("#000000", self, keep_open=True, size=(49, 22)) for _slot in range(5)]
        for swatch in self.harmony_swatches:
            harmony_row.addWidget(swatch)
        harmony_row.addStretch(1)
        body.addLayout(harmony_row)
        self.recent_title = QtWidgets.QLabel("Recent")
        self.recent_title.setObjectName("toolCaption")
        body.addWidget(self.recent_title)
        self.recent_row = QtWidgets.QHBoxLayout()
        self.recent_row.setSpacing(space(4))
        body.addLayout(self.recent_row)
        controls.unify_heights(self)  # The switch, the fields, the steppers and the pipette: one height

    def _page(self, fields):
        """One format: a small caption above each field."""
        page = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(page)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(space(6))
        grid.setVerticalSpacing(space(2))
        for column, (name, field) in enumerate(fields):
            caption = QtWidgets.QLabel(name)
            caption.setObjectName("toolCaption")
            grid.addWidget(caption, 0, column)
            grid.addWidget(field, 1, column)
        grid.setColumnStretch(grid.columnCount(), 1)
        return page

    def harmony_colors(self):
        """The current harmony of the current colour, as names."""
        offsets = dict((key, values) for key, _label, values in HARMONIES)[_harmony[0]]
        if offsets is None:  # Shades: the same hue and saturation, from dark to light
            return [QtGui.QColor.fromHsvF(self.hue, self.saturation, value).name() for value in (0.2, 0.4, 0.6, 0.8, 1.0)]
        return [QtGui.QColor.fromHsvF(((self.hue * 360.0 + offset) % 360.0) / 360.0, self.saturation, self.value).name()
                for offset in offsets]

    def _harmony_chosen(self, index):
        _harmony[0] = self.harmony.itemData(index)
        self._show_harmony()

    def _show_harmony(self):
        colors = self.harmony_colors()
        for slot, swatch in enumerate(self.harmony_swatches):
            swatch.setVisible(slot < len(colors))
            if slot < len(colors):
                swatch.set_color(colors[slot])

    def set_mode(self, mode):
        _mode[0] = mode
        self.mode.set_value(mode)
        self.pages.setCurrentIndex([key for key, _label, _tip in MODES].index(mode))

    def _from_rgb(self, _value=None):
        if self._syncing:
            return
        hue, saturation, value, _alpha = QtGui.QColor(*[stepper.value() for stepper in self.rgb]).getHsvF()
        self.hue = max(0.0, hue) if hue >= 0 else self.hue  # Greys have no hue: keep the strip where it is
        self.saturation, self.value = saturation, value
        self._show(source="rgb")

    def _from_hsv(self, _value=None):
        if self._syncing:
            return
        hue, saturation, value = [stepper.value() for stepper in self.hsv]
        self.hue, self.saturation, self.value = min(0.999, hue / 360.0), saturation / 100.0, value / 100.0
        self._show(source="hsv")

    def color(self):
        return QtGui.QColor.fromHsvF(self.hue, self.saturation, self.value)

    def set_hsv(self, hue, saturation, value):
        self.hue, self.saturation, self.value = hue, saturation, value
        self._show()

    def set_color(self, color, keep_open=True):
        hue, saturation, value, _alpha = QtGui.QColor(color).getHsvF()
        self.hue = max(0.0, hue) if hue >= 0 else self.hue  # Greys have no hue: keep the strip where it is
        self.saturation, self.value = saturation, value
        self._show()
        if not keep_open:
            self.close()

    def _typed(self, text):
        text = text if text.startswith("#") else "#" + text
        if len(text) == 7:
            hue, saturation, value, _alpha = QtGui.QColor(text).getHsvF()
            self.hue = max(0.0, hue) if hue >= 0 else self.hue
            self.saturation, self.value = saturation, value
            self._show(from_field=True)

    def _show(self, from_field=False, source=None):
        """Show the colour everywhere except in the format it was just typed in (`source`)."""
        color = self.color()
        name = color.name()
        source = "hex" if from_field else source
        self._syncing = True
        try:
            if source != "hex":
                self.hex.setText(name)
            if source != "rgb":
                for stepper, part in zip(self.rgb, (color.red(), color.green(), color.blue())):
                    stepper.setValue(part)
            if source != "hsv":
                for stepper, part in zip(self.hsv, (int(round(self.hue * 360)) % 360, int(round(self.saturation * 100)),
                                                    int(round(self.value * 100)))):
                    stepper.setValue(part)
        finally:
            self._syncing = False
        pixmap = QtGui.QPixmap(self.preview.size() * self.devicePixelRatioF())
        pixmap.setDevicePixelRatio(self.devicePixelRatioF())
        pixmap.fill(Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor(self.theme.colors["border"]), 1))
        painter.setBrush(QtGui.QColor(name))
        painter.drawRoundedRect(QtCore.QRectF(0.5, 0.5, self.preview.width() - 1, self.preview.height() - 1), px(6), px(6))
        painter.end()
        self.preview.setPixmap(pixmap)
        self._show_harmony()
        self.square.update()
        self.strip.update()
        for child in self.findChildren(_Swatch):
            child.update()
        self.changed.emit(name)

    def _fill_recent(self):
        while self.recent_row.count():
            item = self.recent_row.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for color in _recent[:12]:
            self.recent_row.addWidget(_Swatch(color, self))
        self.recent_row.addStretch(1)
        self.recent_title.setVisible(bool(_recent))

    def pick_from_screen(self):
        """The pipette: the palette steps aside (out of the screen's picture), the screens freeze with a loupe; the
        colour picked comes back into the palette, which opens again at its place."""
        field, before, original = self._field, self.color().name(), self._original
        self.hide()

        def done(name):
            if field is None:
                return
            self.show_for(field, name or before)
            self._original = original  # Esc in the palette still goes back to the colour it first opened with

        QtCore.QTimer.singleShot(150, lambda: self._start_picker(done))  # After the palette left the screen

    def _start_picker(self, done):
        self.picker = ScreenPicker(self.theme, done, parent=self)
        self.picker.start()

    def show_for(self, field, color):
        self._field = field
        self._original = QtGui.QColor(color).name()
        self.set_color(color)
        self._fill_recent()
        scale_font(self)
        for child in [self] + self.findChildren(QtWidgets.QWidget):
            child.ensurePolished()  # The style sheet's min-height lands at polish: level the heights after it
        inherit_fonts(self)
        controls.unify_heights(self)
        own_keyboard([self] + self.findChildren(QtWidgets.QWidget))  # Esc and typed values reach it, not 3ds Max
        self.adjustSize()
        below = field.mapToGlobal(QtCore.QPoint(0, field.height() + 4))
        area = work_area(field.mapToGlobal(QtCore.QPoint(0, 0)))
        x, y = below.x(), below.y()
        if area is not None:
            if y + self.height() > area.bottom():
                y = field.mapToGlobal(QtCore.QPoint(0, 0)).y() - self.height() - 4
            x = max(area.left(), min(x, area.right() - self.width()))
            y = max(area.top(), y)
        self.move(x, y)
        self.show()
        round_popup(self, 8)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.set_color(self._original)  # Esc: the colour it opened with
            self.close()
            return
        QtWidgets.QWidget.keyPressEvent(self, event)

    def hideEvent(self, event):
        name = self.color().name()
        if name in _recent:
            _recent.remove(name)
        _recent.insert(0, name)
        del _recent[16:]
        self.closed.emit(name)
        QtWidgets.QWidget.hideEvent(self, event)


class ColorButton(Button):
    """A field showing a colour swatch and its #RRGGBB; a click opens the palette."""

    colorChanged = Signal(str)

    def __init__(self, theme, color="#e0a05a", parent=None):
        Button.__init__(self, "", theme, variant="field", tooltip="Choose a colour", parent=parent)
        self._color = QtGui.QColor(color).name()
        self._popup = None
        self.clicked.connect(self._open)
        self._sync()

    def color(self):
        return self._color

    def setColor(self, color):
        name = QtGui.QColor(color).name()
        if name != self._color:
            self._color = name
            self._sync()
            self.colorChanged.emit(name)

    def _on_theme(self, colors):
        Button._on_theme(self, colors)
        if hasattr(self, "_color"):
            self._sync()

    def _sync(self):
        size = px(16)
        ratio = self.devicePixelRatioF() or 1.0
        pixmap = QtGui.QPixmap(int(size * ratio), int(size * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor(self._theme.colors["border"]), 1))
        painter.setBrush(QtGui.QColor(self._color if self.isEnabled() else self._theme.colors["disabled_surface"]))
        painter.drawRoundedRect(QtCore.QRectF(0.5, 0.5, size - 1, size - 1), px(4), px(4))
        painter.end()
        icon = QtGui.QIcon(pixmap)
        icon.addPixmap(pixmap, QtGui.QIcon.Disabled)
        self.setIcon(icon)
        self.setIconSize(QtCore.QSize(size, size))
        QtWidgets.QPushButton.setText(self, Button.ICON_GAP + self._color.upper())

    def changeEvent(self, event):
        Button.changeEvent(self, event)
        if event.type() == QtCore.QEvent.EnabledChange and hasattr(self, "_color"):
            self._sync()

    def _open(self):
        if self._popup is None:
            self._popup = ColorPopup(self._theme, self)
            self._popup.changed.connect(self.setColor)
            self._popup.closed.connect(self.setColor)
        self._popup.show_for(self, self._color)
```

## `python/mytool/ui/badges.py`

```python
"""Badges: small marks that carry one piece of information.

* CountBadge: a number in a round bubble on the corner of a button or a tab ("3", "99+"); hidden at 0.
* StatusBadge: a short word in a tinted capsule (NEW, BETA, PRO, DEPRECATED) beside a name.
* Tag: a removable chip ("Walls  x") for a set of values the user picked; a click on the x removes it.
* Dot: a coloured status dot with a label (Online, Busy, Offline).
Pills (controls.Pill) show a state in a sentence; badge dropdowns (forms.BadgeComboBox) pick a category. Use a badge
only where the information is worth the space.
"""

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal
from ..ui_scale import pt, px
from . import controls
from .controls import Themed, icon_pixmap
from ..qt_compat import device_pixel_ratio


def _text_width(metrics, text):
    return metrics.horizontalAdvance(text) if hasattr(metrics, "horizontalAdvance") else metrics.width(text)


class CountBadge(QtWidgets.QWidget, Themed):
    """A number in the top-right corner of `target` (a button, a segment). It follows the target's place and size and
    paints over it; mouse events pass through. `role`: the bubble's colour (log_error for problems, accent for news)."""

    def __init__(self, target, theme, role="log_error", parent=None):
        QtWidgets.QWidget.__init__(self, parent or target.parentWidget())
        self.target = target
        self._role = role
        self._count = 0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        target.installEventFilter(self)
        self.hide()
        self.bind_theme(theme)

    def set_count(self, count):
        self._count = max(0, int(count))
        self.setVisible(self._count > 0 and self.target.isVisible())
        self._place()
        self.update()

    def count(self):
        return self._count

    def _label(self):
        return "99+" if self._count > 99 else str(self._count)

    def _font(self):
        font = QtGui.QFont(self.font())
        font.setBold(True)
        font.setPointSizeF(pt(7.5))
        return font

    def _place(self):
        metrics = QtGui.QFontMetrics(self._font())
        height = px(16)
        width = max(height, _text_width(metrics, self._label()) + px(8))
        rect = self.target.geometry()
        # Inside the target's top-right corner: a parent clips anything outside it (a segment row, a panel)
        self.setGeometry(rect.right() - width - px(2), rect.top() + px(2), width, height)
        self.raise_()

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.Move, QtCore.QEvent.Resize, QtCore.QEvent.Show):
            self._place()
            self.setVisible(self._count > 0)
        elif event.type() == QtCore.QEvent.Hide:
            self.hide()
        return False

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        tone = QtGui.QColor(self._colors[self._role])
        hue, saturation, value, _alpha = tone.getHsvF()
        # The edge: the same hue, darker and a little deeper (a dark burgundy on a red badge), quiet, never black
        edge = QtGui.QColor.fromHsvF(max(0.0, hue), min(1.0, saturation * 1.15), value * 0.62)
        painter.setPen(QtGui.QPen(edge, px(1.2)))
        painter.setBrush(tone)
        painter.drawRoundedRect(rect, rect.height() / 2.0, rect.height() / 2.0)
        painter.setFont(self._font())
        painter.setPen(QtGui.QColor(self._colors["log_badge_text"]))
        painter.drawText(self.rect(), int(Qt.AlignCenter), self._label())
        painter.end()


class StatusBadge(QtWidgets.QWidget, Themed):
    """A short word in a tinted capsule: text and edge in `role`, fill `<role>_background` (log_info, log_success,
    log_warning, log_error, log_system, log_debug). Upper case, bold, a little smaller than the text around it."""

    def __init__(self, theme, text, role="log_info", parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._text = text.upper()
        self._role = role
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        controls.set_tip(self, text)
        self.bind_theme(theme)

    def _font(self):
        font = QtGui.QFont(self.font())
        font.setBold(True)
        font.setPointSizeF(font.pointSizeF() * 0.8)
        return font

    def sizeHint(self):
        metrics = QtGui.QFontMetrics(self._font())
        return QtCore.QSize(_text_width(metrics, self._text) + px(12), metrics.height() + px(4))

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        tone = QtGui.QColor(self._colors[self._role])
        painter.setPen(QtGui.QPen(tone, 1))
        painter.setBrush(QtGui.QColor(self._colors[self._role + "_background"]))
        painter.drawRoundedRect(rect, px(4), px(4))
        painter.setFont(self._font())
        painter.setPen(tone)
        painter.drawText(self.rect(), int(Qt.AlignCenter), self._text)
        painter.end()


class Tag(QtWidgets.QWidget, Themed):
    """A chip with a value and a small x: `removed(text)` when the x is clicked. `role` tints it (a log role), or
    None for the neutral surface."""

    removed = Signal(str)

    def __init__(self, theme, text, role=None, removable=True, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._text = text
        self._role = role
        self._removable = removable
        self._hover_x = False
        self.setMouseTracking(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setAccessibleName(text)
        self.bind_theme(theme)

    def text(self):
        return self._text

    def sizeHint(self):
        metrics = self.fontMetrics()
        extra = px(18) if self._removable else 0
        return QtCore.QSize(_text_width(metrics, self._text) + px(20) + extra, metrics.height() + px(10))

    def _x_rect(self):
        size = px(14)
        return QtCore.QRect(self.width() - size - px(7), (self.height() - size) // 2, size, size)

    def mouseMoveEvent(self, event):
        position = getattr(event, "position", None)
        point = position().toPoint() if position else event.pos()
        hover = self._removable and self._x_rect().adjusted(-3, -3, 3, 3).contains(point)
        if hover != self._hover_x:
            self._hover_x = hover
            self.setCursor(Qt.PointingHandCursor if hover else Qt.ArrowCursor)
            self.update()

    def leaveEvent(self, event):
        self._hover_x = False
        self.update()
        QtWidgets.QWidget.leaveEvent(self, event)

    def mouseReleaseEvent(self, event):
        position = getattr(event, "position", None)
        point = position().toPoint() if position else event.pos()
        if self._removable and event.button() == Qt.LeftButton and self._x_rect().adjusted(-3, -3, 3, 3).contains(point):
            self.removed.emit(self._text)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        colors = self._colors
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self._role:
            edge, fill, text = colors[self._role], colors[self._role + "_background"], colors["text"]
        else:
            edge, fill, text = colors["border"], colors["surface"], colors["text"]
        painter.setPen(QtGui.QPen(QtGui.QColor(edge), 1))
        painter.setBrush(QtGui.QColor(fill))
        painter.drawRoundedRect(rect, rect.height() / 2.0, rect.height() / 2.0)
        painter.setPen(QtGui.QColor(text))
        text_rect = self.rect().adjusted(px(10), 0, -(px(24) if self._removable else px(10)), 0)
        painter.drawText(text_rect, int(Qt.AlignVCenter | Qt.AlignLeft), self._text)
        if self._removable:
            box = self._x_rect()
            if self._hover_x:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QtGui.QColor(colors["hover"]))
                painter.drawEllipse(QtCore.QRectF(box).adjusted(-2, -2, 2, 2))
            ratio = device_pixel_ratio(self)
            painter.drawPixmap(box, icon_pixmap("x", colors["text" if self._hover_x else "muted_text"], box.width(),
                                                ratio))
        painter.end()


class Dot(QtWidgets.QWidget, Themed):
    """A status dot and its label: `role` gives the colour (log_success Online, log_warning Busy, muted_text Offline).
    `pulse` makes a soft ring breathe around it while something is live (its timer runs only while visible)."""

    def __init__(self, theme, text, role="log_success", pulse=False, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._text = text
        self._role = role
        self._phase = 0.0
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._pulse = pulse
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.bind_theme(theme)

    def set_status(self, text, role):
        self._text, self._role = text, role
        self.updateGeometry()
        self.update()

    def sizeHint(self):
        return QtCore.QSize(px(18) + _text_width(self.fontMetrics(), self._text), max(px(16), self.fontMetrics().height()))

    def _tick(self):
        self._phase = (self._phase + 0.05) % 1.0
        self.update()

    def showEvent(self, event):
        if self._pulse:
            self._timer.start()
        QtWidgets.QWidget.showEvent(self, event)

    def hideEvent(self, event):
        self._timer.stop()
        QtWidgets.QWidget.hideEvent(self, event)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        tone = QtGui.QColor(self._colors[self._role])
        # On the middle of the label's capitals, not of its line box: the font's ascent holds extra room above the
        # letters, so a dot on the box's middle sits a few pixels high next to the text
        metrics = self.fontMetrics()
        baseline = (self.height() - metrics.height()) / 2.0 + metrics.ascent()
        capitals = metrics.capHeight() if hasattr(metrics, "capHeight") else metrics.xHeight()
        centre = QtCore.QPointF(px(6), baseline - capitals / 2.0)
        if self._pulse:
            ring = QtGui.QColor(tone)
            ring.setAlphaF(0.35 * (1.0 - self._phase))
            painter.setPen(Qt.NoPen)
            painter.setBrush(ring)
            radius = px(4) + px(3) * self._phase
            painter.drawEllipse(centre, radius, radius)
        painter.setPen(Qt.NoPen)
        painter.setBrush(tone)
        painter.drawEllipse(centre, px(4), px(4))
        painter.setPen(QtGui.QColor(self._colors["text"]))
        painter.drawText(QtCore.QRect(px(16), 0, self.width() - px(16), self.height()),
                         int(Qt.AlignVCenter | Qt.AlignLeft), self._text)
        painter.end()


def _is_light(colors):
    return QtGui.QColor(colors["window"]).lightnessF() > 0.6


class FilterPill(QtWidgets.QAbstractButton, Themed):
    """A category chip, as the MaxPkg Package Manager's collections: a capsule tinted with its own `color`, a Lucide
    icon, the name and a count in a soft bubble (None for no count). `dimmed` (set by FilterPills) turns it neutral
    while another pill is chosen; the chosen one glows. Painted, so the count can never overlap the name."""

    def __init__(self, theme, text, icon, color, count=None, parent=None):
        QtWidgets.QAbstractButton.__init__(self, parent)
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAttribute(Qt.WA_Hover)
        self._icon_name = icon
        self._color = QtGui.QColor(color)
        self._count = count
        self.dimmed = False
        self.bind_theme(theme)

    def set_count(self, count):
        self._count = count
        self.updateGeometry()
        self.update()

    def _small(self):
        font = QtGui.QFont(self.font())
        font.setPointSizeF(font.pointSizeF() * 0.82)
        return font

    def _count_width(self):
        if self._count is None:
            return 0
        return max(px(18), _text_width(QtGui.QFontMetrics(self._small()), str(self._count)) + px(10))

    def sizeHint(self):
        count = self._count_width()
        width = px(10) + px(14) + px(6) + _text_width(self.fontMetrics(), self.text()) + \
            (px(6) + count if count else 0) + px(11)
        return QtCore.QSize(width, px(30))

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        colors = self._colors
        light = _is_light(colors)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        radius = rect.height() / 2.0
        hover = self.underMouse()
        if self.dimmed:
            border = QtGui.QColor(colors["text" if hover else "border"])
            fill = QtGui.QColor(colors["surface"])
            text = QtGui.QColor(colors["text" if hover else "muted_text"])
        else:
            border = QtGui.QColor(self._color)
            fill = QtGui.QColor(self._color)
            fill.setAlphaF(0.42 if hover else 0.30)
            text = QtGui.QColor(colors["text"] if light else "#ffffff")
        if self.isChecked() and not self.dimmed:  # A soft glow around the chosen pill
            glow = QtGui.QColor(self._color)
            glow.setAlphaF(0.28)
            painter.setPen(QtGui.QPen(glow, 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(-0.5, -0.5, 0.5, 0.5), radius, radius)
        painter.setPen(QtGui.QPen(border, 1))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, radius, radius)
        icon = px(14)
        x = px(10)
        painter.drawPixmap(x, (self.height() - icon) // 2,
                           icon_pixmap(self._icon_name, text.name(), icon, device_pixel_ratio(self)))
        x += icon + px(6)
        width = _text_width(self.fontMetrics(), self.text())
        painter.setPen(text)
        painter.setFont(self.font())
        painter.drawText(QtCore.QRect(x, 0, width + 2, self.height()), int(Qt.AlignVCenter | Qt.AlignLeft), self.text())
        count = self._count_width()
        if count:
            bubble = QtCore.QRectF(x + width + px(6), (self.height() - px(16)) / 2.0, count, px(16))
            tone = QtGui.QColor(text)
            tone.setAlphaF(0.18)
            edge = QtGui.QColor(text)
            edge.setAlphaF(0.28)
            painter.setPen(QtGui.QPen(edge, 1))
            painter.setBrush(tone)
            painter.drawRoundedRect(bubble, bubble.height() / 2.0, bubble.height() / 2.0)
            painter.setFont(self._small())
            painter.setPen(text)
            painter.drawText(bubble, int(Qt.AlignCenter), str(self._count))
        painter.end()


class FilterPills(QtWidgets.QWidget):
    """A wrapping row of FilterPills that picks one category: `changed(key)`. The first pill is usually "All" (key
    ""): while it is chosen every pill keeps its colour; choosing another dims the rest; a click on the chosen pill
    goes back to the first one."""

    changed = Signal(str)

    def __init__(self, theme, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        from .controls import FlowLayout
        self.theme = theme
        self.pills = {}
        self.keys = []
        self._current = None
        self.setLayout(FlowLayout(spacing=px(6)))

    def add(self, key, text, icon, color, count=None):
        pill = FilterPill(self.theme, text, icon, color, count)
        pill.clicked.connect(lambda _checked=False, name=key: self.choose(name))
        self.layout().addWidget(pill)
        self.pills[key] = pill
        self.keys.append(key)
        if self._current is None:
            self.choose(key, quiet=True)
        else:
            self._paint_states()
        return pill

    def choose(self, key, quiet=False):
        if key == self._current and key != self.keys[0]:
            key = self.keys[0]  # A click on the chosen pill: back to All
        self._current = key
        self._paint_states()
        if not quiet:
            self.changed.emit(key)

    def current(self):
        return self._current

    def _paint_states(self):
        first = self.keys[0] if self.keys else None
        for name, pill in self.pills.items():
            pill.setChecked(name == self._current)
            pill.dimmed = self._current != first and name != self._current
            pill.update()
```
