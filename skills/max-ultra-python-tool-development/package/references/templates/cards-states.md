# Template: Cards, gallery and area states

Cards in a responsive grid (`cards.py`); the picture gallery and its lightbox as in the MaxPkg Package Manager (`gallery.py`: drag or step between pictures, thumbnails, a click opens the lightbox over the window's content with a blurred backdrop, Esc, arrows, a click beside or a throw up or down closes it; the Before / After slider `CompareSlider`: two pictures cut by a divider with a round knob, moved by a press, a drag or the keys); the states of a whole area (`states.py`): the busy overlay over a blurred snapshot with Cancel and the result (as the MaxPkg Package Manager), the result card of a finished operation with its countdown bar and, after a success, an optional donation line with a shimmering Donate (as MaxRewind), and the empty state with an icon, a hint and one action, which takes a list's own place (`StateArea`) so nothing around it moves; and the confetti burst that celebrates a rare, real success from the result card's round icon (`confetti.py`, as MaxPkg Packager's installer).

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) through Max Ultra MCP with the windows off screen (the controls trainer checks), and shown on screen in 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3).

## `python/mytool/ui/cards.py`

```python
"""Cards in a responsive grid, and neutral example pictures (the gallery and lightbox are in gallery.py).

* Card: a rounded block for one item of a collection (a preset, a scene, a package): an icon on a tinted disc, the
  name, an optional status badge, two lines of description, a muted detail and one action. The whole card is
  clickable (`clicked`); its outline brightens under the pointer.
* CardGrid: equal columns from the width (at least `min_width` each), as many as fit up to `max_columns`; the cards
  flow into rows and the grid's height follows.
* demo_picture: a neutral example picture painted in code for the showcase (no files, no metadata).
"""

import math

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, device_pixel_ratio
from ..ui_scale import px, space
from . import controls
from .badges import StatusBadge
from .controls import Button, Themed, icon_pixmap


class Card(QtWidgets.QFrame, Themed):
    """See the module. `badge`: (text, log role) or None; `action`: (label, Lucide icon, callback) or None."""

    clicked = Signal()

    def __init__(self, theme, title, text, icon="box", role="accent", badge=None, detail="", action=None,
                 parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setObjectName("toolCard")
        self.setAttribute(Qt.WA_Hover)
        self.setCursor(Qt.PointingHandCursor)
        self._icon, self._role = icon, role
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(space(12), space(12), space(12), space(12))
        layout.setSpacing(space(6))
        head = QtWidgets.QHBoxLayout()
        head.setSpacing(space(8))
        self.glyph = QtWidgets.QLabel()
        self.glyph.setFixedSize(px(30), px(30))
        head.addWidget(self.glyph, 0, Qt.AlignVCenter)
        name = QtWidgets.QLabel(title)
        name.setObjectName("toolSection")
        head.addWidget(name, 1, Qt.AlignVCenter)
        if badge:
            head.addWidget(StatusBadge(theme, badge[0], badge[1]), 0, Qt.AlignVCenter)
        layout.addLayout(head)
        self.text = controls.muted(text)
        layout.addWidget(self.text)
        layout.addStretch(1)
        if detail or action:
            foot = QtWidgets.QHBoxLayout()
            foot.setSpacing(space(6))
            if detail:
                small = QtWidgets.QLabel(detail)
                small.setObjectName("toolCaption")
                foot.addWidget(small, 1, Qt.AlignVCenter)
            else:
                foot.addStretch(1)
            if action:
                label, icon_name, callback = action
                self.action_button = Button(label, theme, icon=icon_name, variant="ghost")
                self.action_button.clicked.connect(callback)
                foot.addWidget(self.action_button)
            layout.addLayout(foot)
        self.bind_theme(theme)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(controls_point(event)):
            self.clicked.emit()
        QtWidgets.QFrame.mouseReleaseEvent(self, event)

    def _on_theme(self, colors):
        size = px(30)
        ratio = device_pixel_ratio(self)
        pixmap = QtGui.QPixmap(int(size * ratio), int(size * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        disc = QtGui.QColor(colors[self._role])
        disc.setAlphaF(0.16)
        painter.setPen(Qt.NoPen)
        painter.setBrush(disc)
        painter.drawEllipse(QtCore.QRectF(0, 0, size, size))
        icon = px(16)
        painter.drawPixmap((size - icon) // 2, (size - icon) // 2, icon_pixmap(self._icon, colors[self._role], icon,
                                                                               ratio))
        painter.end()
        self.glyph.setPixmap(pixmap)


def controls_point(event):
    position = getattr(event, "position", None)
    return position().toPoint() if position else event.pos()


class CardGrid(QtWidgets.QWidget):
    """See the module."""

    def __init__(self, min_width=220, spacing=10, max_columns=4, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._items = []
        self._min_width = px(min_width)
        self._spacing = px(spacing)
        self._max_columns = max_columns
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

    def set_items(self, widgets):
        for widget in self._items:
            if widget not in widgets:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self._items = list(widgets)
        for widget in self._items:
            widget.setParent(self)
            widget.show()
        self._relayout(self.width())

    def items(self):
        return list(self._items)

    def columns_for(self, width):
        columns = max(1, (width + self._spacing) // (self._min_width + self._spacing))
        return int(min(self._max_columns, columns))

    def relayout(self):
        """After cards were hidden or shown (a filter): only the shown ones take places."""
        self._relayout(self.width())

    def _relayout(self, width):
        if width <= 0:
            return
        columns = self.columns_for(width)
        column_width = (width - self._spacing * (columns - 1)) / float(columns)
        y = row_height = 0
        shown = [widget for widget in self._items if not widget.isHidden()]
        for index, widget in enumerate(shown):
            if index % columns == 0 and index:
                y += row_height + self._spacing
                row_height = 0
            # One row is as tall as its tallest card, so the cards of a row line up
            row = shown[index - index % columns:index - index % columns + columns]
            height = max(card.heightForWidth(int(column_width)) if card.hasHeightForWidth() else
                         card.sizeHint().height() for card in row)
            x = int(round((index % columns) * (column_width + self._spacing)))
            widget.setGeometry(x, y, int(column_width), height)
            row_height = max(row_height, height)
        total = y + row_height if shown else 0
        if self.minimumHeight() != total:
            self.setMinimumHeight(total)
            self.updateGeometry()

    def resizeEvent(self, event):
        QtWidgets.QWidget.resizeEvent(self, event)
        self._relayout(event.size().width())

    def sizeHint(self):
        return QtCore.QSize(self._min_width, self.minimumHeight())


def demo_picture(index, width=640, height=400, colors=None):
    """A neutral example picture for the showcase: a soft gradient with simple shapes (no files, no metadata)."""
    hues = (205, 28, 150, 265, 350, 95)
    hue = hues[index % len(hues)]
    image = QtGui.QImage(width, height, QtGui.QImage.Format_ARGB32_Premultiplied)
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    gradient = QtGui.QLinearGradient(0, 0, width, height)
    gradient.setColorAt(0.0, QtGui.QColor.fromHsl(hue, 120, 70))
    gradient.setColorAt(1.0, QtGui.QColor.fromHsl((hue + 40) % 360, 140, 30))
    painter.fillRect(image.rect(), gradient)
    painter.setPen(Qt.NoPen)
    for step in range(5):
        tone = QtGui.QColor.fromHsl((hue + step * 18) % 360, 160, 120 + step * 12)
        tone.setAlphaF(0.35)
        painter.setBrush(tone)
        radius = height * (0.18 + 0.05 * step)
        angle = index * 0.9 + step * 1.3
        centre = QtCore.QPointF(width * (0.5 + 0.32 * math.cos(angle)), height * (0.5 + 0.3 * math.sin(angle)))
        painter.drawEllipse(centre, radius, radius)
    horizon = QtGui.QColor(0, 0, 0, 70)
    painter.setBrush(horizon)
    painter.drawRect(QtCore.QRectF(0, height * 0.72, width, height * 0.28))
    painter.end()
    return QtGui.QPixmap.fromImage(image)
```

## `python/mytool/ui/gallery.py`

```python
"""Picture gallery and lightbox, as in the MaxPkg Package Manager.

* Gallery: the current picture in a rounded frame that follows a sideways drag with its neighbour sliding in beside it
  (SlideView); round previous / next buttons over its sides and a "2 / 6" counter in its corner; its title and caption
  below; a row of thumbnails (or, `compact`, one strip that scrolls by dragging). The arrow keys step it. A click on the
  picture asks for the lightbox (`preview_requested(index)`; `open_lightbox` shows it).
* Lightbox: the pictures over the whole content of the window, on a blurred, tinted copy of it that fades in; large
  round previous / next buttons, the round close button (red on hover), the title and caption at the bottom. Esc,
  a click beside the picture or dragging the picture up or down (the backdrop fades as it goes, Fancybox style)
  closes it; Left / Right and drags step through the pictures.
* CompareSlider: two pictures of one thing (before / after a render setting, a clay and a final render) on top of each
  other, cut by a vertical divider with a round knob; press or drag anywhere to move it, Left / Right step it, Home /
  End go to the edges. As in the MaxPkg Package Manager.
All of them are child widgets of the window, never translucent windows. Pictures are QPixmaps the tool owns (renders,
previews); `pixmap_for` may return None while one is still loading (a spinning ring) and `failed_for` say that one will
not come (an icon and a short message).
"""

import math

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, device_pixel_ratio, is_valid, own_keyboard
from ..ui_scale import px, space
from . import controls
from .controls import Themed, icon_pixmap
from .states import blurred

DRAG_THRESHOLD = 6  # Logical px of movement before a press becomes a drag instead of a click
SWIPE_DISTANCE = 40  # Logical px of sideways drag that goes to the neighbour picture


def _global_xy(event):
    position = event.globalPosition() if hasattr(event, "globalPosition") else event.globalPos()
    return position.x(), position.y()


class Swipe(QtCore.QObject):
    """Drags on a widget: `dragged(dx)` / `released(dx)` sideways, `dragged_vertical(dy)` / `released_vertical(dy)`
    up or down (with `vertical`; the first pixels decide), `clicked()` for a press and release without a drag."""

    dragged = Signal(int)
    released = Signal(int)
    dragged_vertical = Signal(int)
    released_vertical = Signal(int)
    clicked = Signal()

    def __init__(self, widget, vertical=False):
        QtCore.QObject.__init__(self, widget)
        self.vertical = vertical
        self._start = None
        self._axis = None
        self._cursor = None
        widget.installEventFilter(self)

    def _deltas(self, event):
        x, y = _global_xy(event)
        return x - self._start[0], y - self._start[1]

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QtCore.QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self._start = _global_xy(event)
            self._axis = None
            return True
        if kind == QtCore.QEvent.MouseMove and self._start is not None:
            dx, dy = self._deltas(event)
            if self._axis is None and max(abs(dx), abs(dy)) > px(DRAG_THRESHOLD):
                self._axis = "y" if self.vertical and abs(dy) > abs(dx) else "x"
                self._cursor = watched.cursor()
                watched.setCursor(Qt.ClosedHandCursor)
            if self._axis == "x":
                self.dragged.emit(int(dx))
            elif self._axis == "y":
                self.dragged_vertical.emit(int(dy))
            return self._axis is not None
        if kind == QtCore.QEvent.MouseButtonRelease and self._start is not None and event.button() == Qt.LeftButton:
            dx, dy = self._deltas(event)
            axis, self._start, self._axis = self._axis, None, None
            if axis is not None:
                watched.setCursor(self._cursor)
            if axis == "x":
                self.released.emit(int(dx))
            elif axis == "y":
                self.released_vertical.emit(int(dy))
            else:
                self.clicked.emit()
            return True
        return False


class DragScroll(QtCore.QObject):
    """Drag a horizontal scroll area (and the buttons inside it) with the mouse; a plain click still clicks."""

    def __init__(self, area):
        QtCore.QObject.__init__(self, area)
        self.area = area
        self._start = None
        self._dragging = False
        area.viewport().installEventFilter(self)
        area.viewport().setCursor(Qt.OpenHandCursor)

    def watch(self, widget):
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QtCore.QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self._start = (_global_xy(event)[0], self.area.horizontalScrollBar().value(), watched)
            self._dragging = False
        elif kind == QtCore.QEvent.MouseMove and self._start is not None and event.buttons() & Qt.LeftButton:
            delta = _global_xy(event)[0] - self._start[0]
            if not self._dragging and abs(delta) > px(DRAG_THRESHOLD):
                self._dragging = True
                self.area.viewport().setCursor(Qt.ClosedHandCursor)
                if isinstance(self._start[2], QtWidgets.QAbstractButton):
                    self._start[2].setDown(False)  # The drag must not end as a click
            if self._dragging:
                self.area.horizontalScrollBar().setValue(int(self._start[1] - delta))
                return True
        elif kind == QtCore.QEvent.MouseButtonRelease and self._start is not None:
            dragged, self._start, self._dragging = self._dragging, None, False
            if dragged:
                self.area.viewport().setCursor(Qt.OpenHandCursor)
                return True
        return False


class SlideView(QtWidgets.QWidget, Themed):
    """The picture carousel: the current picture follows a sideways drag with its neighbour sliding in beside it; a
    drag past SWIPE_DISTANCE (or `slide(step)`) animates to that neighbour, a shorter one springs back. `framed` draws
    the rounded recessed frame of the gallery; `inset` is the side margin each picture is fitted into (slides still
    cross the whole widget); `dismissible` lets a drag up or down throw the picture off (the lightbox). Pictures are
    never enlarged: a small one keeps its size, a large one shrinks to fit."""

    index_changed = Signal(int)
    clicked = Signal()
    clicked_outside = Signal()  # A click beside the current picture (the lightbox closes on it)
    dismiss_progress = Signal(float)  # 0..1 while the picture is dragged up or down
    dismissed = Signal()
    GAP = 24
    DISMISS_DISTANCE = 110
    FAILED_TEXT = "This picture could not be loaded."

    def __init__(self, theme, count, pixmap_for, framed=False, inset=2, dismissible=False, failed_for=None,
                 loop=True, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.count, self.pixmap_for, self.failed_for = count, pixmap_for, failed_for
        self.framed, self.inset, self.loop = framed, px(inset), loop
        self.index, self.offset, self.lift = 0, 0.0, 0.0
        self._current_rect = QtCore.QRectF()
        self._scaled = {}
        self._target_step = 0
        self._dismissing = False
        self._animation = QtCore.QVariantAnimation(self)
        self._animation.setDuration(240)
        self._animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._animation.valueChanged.connect(self._set_offset)
        self._animation.finished.connect(self._settle)
        self._lift_animation = QtCore.QVariantAnimation(self)
        self._lift_animation.valueChanged.connect(self._set_lift)
        self._lift_animation.finished.connect(self._lift_settled)
        self._spin = QtCore.QElapsedTimer()
        self._spin.start()
        self._spin_timer = QtCore.QTimer(self)  # Runs only while a picture is still loading
        self._spin_timer.setInterval(33)
        self._spin_timer.timeout.connect(self.update)
        self.swipe = Swipe(self, vertical=dismissible)
        self.swipe.dragged.connect(self._on_drag)
        self.swipe.released.connect(self._on_release)
        self.swipe.dragged_vertical.connect(self._on_lift)
        self.swipe.released_vertical.connect(self._on_lift_release)
        self.swipe.clicked.connect(self._on_click)
        self.bind_theme(theme)

    # ---- index and sliding ------------------------------------------------------------------------------------
    def set_count(self, count):
        self.count = count
        self._scaled = {}
        self.set_index(min(self.index, max(0, count - 1)))

    def set_index(self, index):
        self._animation.stop()
        self.index = index % self.count if self.count else 0
        self.offset = 0.0
        self.update()
        self.index_changed.emit(self.index)

    def reachable(self, step):
        return self.loop or 0 <= self.index + step < self.count

    def slide(self, step):
        """Animate to the next (+1) or the previous (-1) picture."""
        if self.count < 2 or not self.reachable(step):
            return
        if self._animation.state() == QtCore.QAbstractAnimation.Running:
            self._animation.stop()
            self._settle()
        self._animate_to(step)

    def _span(self):
        return self.width() + px(self.GAP)

    def _set_offset(self, value):
        self.offset = float(value)
        self.update()

    def _animate_to(self, step):
        self._target_step = step
        self._animation.setStartValue(float(self.offset))
        self._animation.setEndValue(float(-step * self._span()))
        self._animation.start()

    def _on_drag(self, delta):
        if self.count < 2:
            return
        self._animation.stop()
        if not self.reachable(-1 if delta > 0 else 1):
            delta *= 0.25  # Past the first or last picture: it only stretches a little and springs back
        self._set_offset(max(-self._span(), min(self._span(), delta)))

    def _on_release(self, delta):
        if self.count < 2:
            return
        step = 0 if abs(delta) < px(SWIPE_DISTANCE) else (1 if delta < 0 else -1)
        self._animate_to(step if self.reachable(step) else 0)

    def _settle(self):
        step, self._target_step = self._target_step, 0
        if step:
            self.index = (self.index + step) % self.count
            self.index_changed.emit(self.index)
        self.offset = 0.0
        self.update()

    def _on_click(self):
        self.clicked.emit()
        point = QtCore.QPointF(self.mapFromGlobal(QtGui.QCursor.pos()))  # Read only: the pointer is never moved
        if not self._current_rect.isEmpty() and not self._current_rect.contains(point):
            self.clicked_outside.emit()

    # ---- drag up or down to dismiss -----------------------------------------------------------------------------
    def progress(self):
        return min(1.0, abs(self.lift) / max(1.0, self.height() * 0.45))

    def _set_lift(self, value):
        self.lift = float(value)
        self.update()
        self.dismiss_progress.emit(self.progress())

    def _on_lift(self, delta):
        self._lift_animation.stop()
        self._set_lift(delta)

    def _on_lift_release(self, delta):
        self._dismissing = abs(delta) >= px(self.DISMISS_DISTANCE)
        end = (self.height() if delta > 0 else -self.height()) if self._dismissing else 0.0
        self._lift_animation.setDuration(220 if self._dismissing else 320)
        self._lift_animation.setEasingCurve(QtCore.QEasingCurve.InCubic if self._dismissing
                                            else QtCore.QEasingCurve.OutBack)
        self._lift_animation.setStartValue(float(self.lift))
        self._lift_animation.setEndValue(float(end))
        self._lift_animation.start()

    def _lift_settled(self):
        if self._dismissing:
            self._dismissing = False
            self.dismissed.emit()
        else:
            self._set_lift(0.0)

    # ---- painting -------------------------------------------------------------------------------------------------
    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def resizeEvent(self, event):
        QtWidgets.QWidget.resizeEvent(self, event)
        self._scaled = {}

    def _scaled_pixmap(self, index, size):
        source = self.pixmap_for(index)
        if source is None or source.isNull():
            return None
        cached = self._scaled.get(index)
        if cached is not None and cached[0] == source.cacheKey() and cached[1] == size:
            return cached[2]
        ratio = device_pixel_ratio(self)
        natural = source.size() / max(1.0, source.devicePixelRatio())
        fitted = natural if natural.width() <= size.width() and natural.height() <= size.height() else \
            natural.scaled(size, Qt.KeepAspectRatio)
        scaled = source.scaled(int(fitted.width() * ratio), int(fitted.height() * ratio), Qt.KeepAspectRatio,
                               Qt.SmoothTransformation)
        scaled.setDevicePixelRatio(ratio)
        self._scaled[index] = (source.cacheKey(), size, scaled)
        return scaled

    def paintEvent(self, event):
        colors = self._colors
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        frame = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self.framed:
            painter.setPen(QtGui.QPen(QtGui.QColor(colors["border"]), 1))
            painter.setBrush(QtGui.QColor(colors["recessed"]))
            painter.drawRoundedRect(frame, px(8), px(8))
            clip = QtGui.QPainterPath()
            clip.addRoundedRect(frame.adjusted(1, 1, -1, -1), px(7), px(7))
            painter.setClipPath(clip)
        if not self.count:
            painter.end()
            return
        area = QtCore.QRectF(self.rect()).adjusted(self.inset, px(2), -self.inset, -px(2))
        size = QtCore.QSize(int(area.width()), int(area.height()))
        if self.lift:  # Dragged up or down: the picture follows and shrinks a little around its centre
            scale = 1.0 - 0.15 * self.progress()
            middle = area.center()
            painter.translate(middle.x(), middle.y() + self.lift)
            painter.scale(scale, scale)
            painter.translate(-middle.x(), -middle.y())
        loading = False
        for step in ((-1, 0, 1) if self.count > 1 and not self.lift else (0,)):
            left = area.left() + step * self._span() + self.offset
            if left - self.inset >= self.width() or left + area.width() + self.inset <= 0 or not self.reachable(step):
                continue
            position = (self.index + step) % self.count
            pixmap = self._scaled_pixmap(position, size)
            centre = QtCore.QPointF(left + area.width() / 2.0, area.center().y())
            if pixmap is None:
                if self.failed_for is not None and self.failed_for(position):
                    target = self._paint_failed(painter, centre)
                else:
                    loading = True
                    target = self._paint_preloader(painter, centre)
            else:
                logical = QtCore.QSizeF(pixmap.size()) / pixmap.devicePixelRatio()
                target = QtCore.QRectF(left + (area.width() - logical.width()) / 2.0,
                                       area.top() + (area.height() - logical.height()) / 2.0,
                                       logical.width(), logical.height())
                painter.drawPixmap(target, pixmap, QtCore.QRectF(pixmap.rect()))
            if step == 0:
                self._current_rect = target
        painter.end()
        if loading and not self._spin_timer.isActive():
            self._spin_timer.start()
        elif not loading and self._spin_timer.isActive():
            self._spin_timer.stop()

    def _paint_failed(self, painter, centre):
        size = px(32)
        painter.drawPixmap(QtCore.QPointF(centre.x() - size / 2.0, centre.y() - size),
                           icon_pixmap("image-off", self._colors["muted_text"], size, device_pixel_ratio(self)))
        painter.setPen(QtGui.QColor(self._colors["muted_text"]))
        text = QtCore.QRectF(centre.x() - px(160), centre.y() + px(8), px(320), px(22))
        painter.drawText(text, int(Qt.AlignCenter), self.FAILED_TEXT)
        return QtCore.QRectF(text.left(), centre.y() - size, text.width(), size + px(30))

    def _paint_preloader(self, painter, centre):
        """A faint ring with an accent arc that turns and breathes in length."""
        seconds = self._spin.elapsed() / 1000.0
        radius = px(14)
        ring = QtCore.QRectF(centre.x() - radius, centre.y() - radius, 2 * radius, 2 * radius)
        pen = QtGui.QPen(QtGui.QColor(self._colors["border"]), px(3))
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(ring)
        pen.setColor(QtGui.QColor(self._colors["accent"]))
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        span = 60.0 + 120.0 * (0.5 + 0.5 * math.sin(seconds * 3.2))
        painter.drawArc(ring, int(-seconds * 300.0 * 16), int(-span * 16))
        return ring

    def hideEvent(self, event):
        self._spin_timer.stop()
        QtWidgets.QWidget.hideEvent(self, event)


class RoundButton(QtWidgets.QAbstractButton, Themed):
    """A round button over a picture: a dark see-through disc with a light edge and a white Lucide icon; the edge turns
    accent on hover. Painted, so it reads on any picture and in every theme."""

    def __init__(self, theme, icon, size, tooltip, parent=None):
        QtWidgets.QAbstractButton.__init__(self, parent)
        self._icon = icon
        self.setFixedSize(px(size), px(size))
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)  # The keyboard stays on the gallery or the lightbox
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip)
        self.setAttribute(Qt.WA_Hover)
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QtGui.QPen(QtGui.QColor(self._colors["accent"]) if self.underMouse() else
                                  QtGui.QColor(255, 255, 255, 90), 1))
        painter.setBrush(QtGui.QColor(0, 0, 0, 150 if self.isDown() else 115))
        painter.drawEllipse(rect)
        icon = int(self.width() * 0.5)
        painter.drawPixmap((self.width() - icon) // 2, (self.height() - icon) // 2,
                           icon_pixmap(self._icon, "#ffffff", icon, device_pixel_ratio(self)))
        painter.end()


class _Counter(QtWidgets.QWidget, Themed):
    """"2 / 6" in a dark capsule in the picture's corner."""

    def __init__(self, theme, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._text = ""
        self.bind_theme(theme)

    def set_text(self, text):
        self._text = text
        metrics = self.fontMetrics()
        width = metrics.horizontalAdvance(text) if hasattr(metrics, "horizontalAdvance") else metrics.width(text)
        self.setFixedSize(width + px(16), metrics.height() + px(6))
        self.update()

    def _on_theme(self, colors):
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 90), 1))
        painter.setBrush(QtGui.QColor(0, 0, 0, 125))
        painter.drawRoundedRect(rect, rect.height() / 2.0, rect.height() / 2.0)
        painter.setPen(QtGui.QColor("#ffffff"))
        painter.drawText(self.rect(), int(Qt.AlignCenter), self._text)
        painter.end()


class Gallery(QtWidgets.QWidget, Themed):
    """See the module. `add(pixmap, title, caption)`; `preview_requested(index)` on a click on the picture."""

    preview_requested = Signal(int)
    current_changed = Signal(int)

    def __init__(self, theme, compact=False, loop=True, heights=(220, 420), parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.items = []
        self.compact, self.heights = compact, heights
        self.main = SlideView(theme, 0, self.pixmap_for, framed=True, loop=loop)
        self.main.setCursor(Qt.PointingHandCursor)
        self.main.setToolTip("Click to open, drag sideways for the next picture")
        self.main.clicked.connect(lambda: self.preview_requested.emit(self.main.index))
        self.main.index_changed.connect(self._show_index)
        self.previous = RoundButton(theme, "chevron-left", 32, "Previous picture (Left)", self.main)
        self.next = RoundButton(theme, "chevron-right", 32, "Next picture (Right)", self.main)
        self.previous.clicked.connect(lambda: self.main.slide(-1))
        self.next.clicked.connect(lambda: self.main.slide(1))
        self.counter = _Counter(theme, self.main)
        self.title = QtWidgets.QLabel("")
        self.title.setObjectName("toolSection")
        self.title.setWordWrap(True)
        self.caption = controls.muted("")
        self.thumb_size = QtCore.QSize(px(88), px(54)) if compact else QtCore.QSize(px(104), px(62))
        self.thumbs = []
        strip = QtWidgets.QWidget()
        strip.setObjectName("toolThumbStrip")
        self.strip_layout = QtWidgets.QHBoxLayout(strip)
        self.strip_layout.setContentsMargins(0, 0, 0, 0)
        self.strip_layout.setSpacing(space(8))
        self.strip_layout.addStretch(1)
        self.strip = QtWidgets.QScrollArea()  # One row that scrolls by dragging when it does not fit
        self.strip.setObjectName("toolThumbArea")
        self.strip.setWidget(strip)
        self.strip.setWidgetResizable(True)
        self.strip.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.strip.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.strip.setFixedHeight(self.thumb_size.height() + px(14))
        self.drag = DragScroll(self.strip)
        self.drag.watch(strip)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(space(6))
        layout.addWidget(self.main)
        layout.addWidget(self.title)
        layout.addWidget(self.caption)
        layout.addWidget(self.strip)
        self.bind_theme(theme)
        self._sync_controls()

    def pixmap_for(self, index):
        return self.items[index][0] if 0 <= index < len(self.items) else None

    def add(self, pixmap, title="", caption=""):
        self.items.append((pixmap, title, caption))
        position = len(self.items) - 1
        button = QtWidgets.QPushButton()
        button.setObjectName("toolThumb")
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedSize(self.thumb_size)
        button.setIconSize(self.thumb_size - QtCore.QSize(px(6), px(6)))
        controls.set_tip(button, title)
        button.setIcon(QtGui.QIcon(self._thumb(pixmap)))
        button.clicked.connect(lambda _checked=False, value=position: self.main.set_index(value))
        self.drag.watch(button)
        self.strip_layout.insertWidget(self.strip_layout.count() - 1, button)
        self.thumbs.append(button)
        self.main.set_count(len(self.items))
        self._sync_controls()

    def _thumb(self, pixmap):
        """A thumbnail cut to fill its button, with rounded corners."""
        size = self.thumb_size - QtCore.QSize(px(6), px(6))
        ratio = device_pixel_ratio(self)
        target = QtGui.QPixmap(int(size.width() * ratio), int(size.height() * ratio))
        target.setDevicePixelRatio(ratio)
        target.fill(Qt.transparent)
        cover = pixmap.scaled(target.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        painter = QtGui.QPainter(target)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        clip = QtGui.QPainterPath()
        clip.addRoundedRect(QtCore.QRectF(0, 0, size.width(), size.height()), px(4), px(4))
        painter.setClipPath(clip)
        x = (cover.width() - target.width()) // 2
        y = (cover.height() - target.height()) // 2
        painter.drawPixmap(QtCore.QRectF(0, 0, size.width(), size.height()), cover,
                           QtCore.QRectF(x, y, target.width(), target.height()))
        painter.end()
        return target

    def count(self):
        return len(self.items)

    def current(self):
        return self.main.index

    def show_index(self, index):
        self.main.set_index(index)

    def _show_index(self, index):
        if not self.items:
            return
        _pixmap, title, caption = self.items[index]
        self.title.setText(title)
        self.title.setVisible(bool(title))
        self.caption.setText(caption)
        self.caption.setVisible(bool(caption))
        self.counter.set_text("{} / {}".format(index + 1, len(self.items)))
        for position, button in enumerate(self.thumbs):
            button.setChecked(position == index)
        if self.thumbs:
            self.strip.ensureWidgetVisible(self.thumbs[index], px(24), 0)
        self._sync_controls()
        self.current_changed.emit(index)

    def _sync_controls(self):
        several = len(self.items) > 1
        for widget in (self.previous, self.next, self.counter):
            widget.setVisible(several)
        self._place()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            self.main.slide(1 if event.key() == Qt.Key_Right else -1)
            return
        QtWidgets.QWidget.keyPressEvent(self, event)

    def _on_theme(self, colors):
        self.update()

    def resizeEvent(self, event):
        QtWidgets.QWidget.resizeEvent(self, event)
        self._place()

    def _place(self):
        height = max(px(self.heights[0]), min(px(self.heights[1]), int(self.width() * 0.56)))
        if self.main.height() != height:
            self.main.setFixedHeight(height)
        middle = height // 2 - self.previous.height() // 2
        self.previous.move(px(10), middle)
        self.next.move(self.width() - self.next.width() - px(10), middle)
        self.counter.move(self.width() - self.counter.width() - px(10), height - self.counter.height() - px(10))


class Lightbox(QtWidgets.QWidget, Themed):
    """See the module. `host`: the widget it covers (the window's content below its title bar); `items`: (pixmap,
    title, caption) tuples."""

    TINT = 0.6  # Share of the recessed colour over the blurred content

    def __init__(self, host, theme, items, index=0):
        backdrop = blurred(host.grab())  # Before this widget exists, so it is not in the picture
        QtWidgets.QWidget.__init__(self, host)
        self._built = False
        self.setObjectName("toolLightbox")
        self.host = host
        self.items = list(items)
        self._backdrop = backdrop
        self._shade = 0.0
        self.image = SlideView(theme, len(self.items), self.pixmap_for, inset=70, dismissible=True, parent=self)
        self.image.set_index(index)
        self.image.index_changed.connect(lambda _index: self._place())
        self.image.dismiss_progress.connect(self._on_dismiss_progress)
        self.image.dismissed.connect(self.close_lightbox)
        self.image.clicked_outside.connect(self.close_lightbox)  # A click beside the picture closes it
        self._fade = QtCore.QVariantAnimation(self)
        self._fade.setDuration(200)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.valueChanged.connect(self._set_shade)
        self.caption = QtWidgets.QLabel("", self)
        self.caption.setAlignment(Qt.AlignCenter)
        self.caption.setWordWrap(True)
        self.caption.setTextFormat(Qt.RichText)
        self.previous = RoundButton(theme, "chevron-left", 40, "Previous picture (Left)", self)
        self.next = RoundButton(theme, "chevron-right", 40, "Next picture (Right)", self)
        self.previous.clicked.connect(lambda: self.image.slide(-1))
        self.next.clicked.connect(lambda: self.image.slide(1))
        self.close_button = controls.WindowButton("x", theme, "Close (Esc)", close=True, parent=self)
        self.close_button.setFocusPolicy(Qt.NoFocus)
        self.close_button.clicked.connect(self.close_lightbox)
        for button in (self.previous, self.next):
            button.setVisible(len(self.items) > 1)
        self.setFocusPolicy(Qt.StrongFocus)
        host.installEventFilter(self)
        self.bind_theme(theme)
        self._built = True
        self.setGeometry(host.rect())
        self.show()
        self.raise_()
        own_keyboard([self])  # Esc and the arrows reach the lightbox, not 3ds Max
        self.setFocus(Qt.OtherFocusReason)
        self._place()
        self._fade.start()

    def pixmap_for(self, index):
        return self.items[index][0] if 0 <= index < len(self.items) else None

    def current(self):
        return self.image.index

    def _set_shade(self, value):
        self._shade = float(value)
        self.update()

    def _on_dismiss_progress(self, progress):
        """The picture is dragged up or down: the backdrop fades and the controls step aside until it comes back."""
        self._fade.stop()
        self._set_shade(1.0 - 0.85 * progress)
        resting = progress < 0.01
        for widget in (self.previous, self.next, self.close_button, self.caption):
            widget.setVisible(resting and (widget is self.close_button or widget is self.caption or
                                           len(self.items) > 1))

    def _on_theme(self, colors):
        self._colors = colors
        self._place()
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        painter.setOpacity(self._shade)
        if self._backdrop is not None:
            painter.drawPixmap(self.rect(), self._backdrop)
        painter.setOpacity(1.0)
        tint = QtGui.QColor(self._colors["recessed"])
        tint.setAlphaF(min(1.0, self.TINT * self._shade + (0.25 if self._backdrop is None else 0.0)))
        painter.fillRect(self.rect(), tint)
        painter.end()

    def eventFilter(self, watched, event):
        if watched is self.host and event.type() == QtCore.QEvent.Resize:
            self.setGeometry(self.host.rect())
        return False

    def resizeEvent(self, event):
        QtWidgets.QWidget.resizeEvent(self, event)
        self._place()

    def mousePressEvent(self, event):
        event.accept()  # Clicks on the backdrop stay in the lightbox ...

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.close_lightbox()  # ... and close it, like a click beside the picture

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close_lightbox()
        elif key in (Qt.Key_Left, Qt.Key_Right):
            self.image.slide(1 if key == Qt.Key_Right else -1)
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)

    def close_lightbox(self):
        if is_valid(self):
            self.host.removeEventFilter(self)
            self.hide()
            self.deleteLater()

    def _place(self):
        if not self._built or not is_valid(self):
            return
        self.image.setGeometry(self.rect().adjusted(0, px(48), 0, -px(84)))
        self.image.update()
        _pixmap, title, caption = self.items[self.image.index] if self.items else (None, "", "")
        colors = self._colors
        self.caption.setText('<span style="color:{0}"><b>{1}</b></span><br><span style="color:{2}">{3}</span>'.format(
            colors["text"], title, colors["muted_text"], caption) if title or caption else "")
        self.caption.setGeometry(px(70), self.height() - px(80), self.width() - px(140), px(64))
        middle = self.image.geometry().center().y() - self.previous.height() // 2
        self.previous.move(px(18), middle)
        self.next.move(self.width() - self.next.width() - px(18), middle)
        self.close_button.move(self.width() - self.close_button.width() - px(14), px(12))


def open_lightbox(host, theme, items, index=0):
    """Show the lightbox over `host` at picture `index`; returns it."""
    return Lightbox(host, theme, items, index)


class CompareSlider(QtWidgets.QWidget, Themed):
    """Before / After: two pictures on top of each other, cut by a vertical divider (as in the MaxPkg Package Manager).

    * The Before picture sets the size: its own size, or the available width when it is wider; never enlarged, its
      aspect kept. The After picture lies exactly over it and shows only right of the divider; a different shape is
      cropped to fit, centred, never stretched. Corners rounded 8 px.
    * The divider starts at the middle: a 2 px white line with a 40 px round knob (a white 2 px ring, a dark see-through
      fill, the Lucide chevrons-left-right). A press anywhere moves it there and a drag follows the pointer; with the
      focus, Left / Right step it by 5 %, Home / End go to the edges, and an outline in the focus colour rings the knob.
    * Small dark badges name the sides in the top corners (Before left, After right); a badge hides while the divider
      covers it.
    * The wheel is left to the page. While a picture is on its way (None) the place is 16:9; a picture that failed (a
      path that does not load) shows its label on a muted fill.
    `before` / `after`: (label, picture) with a QPixmap, a file path or None; `set_picture` when one arrives later.
    `changed(float)` sends the divider's place (0..1).
    """

    changed = Signal(float)
    LOADING_RATIO = 9 / 16.0
    STEP = 0.05

    def __init__(self, theme, before, after, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.position = 0.5
        self._sides = {}
        self.setCursor(Qt.SizeHorCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self.set_picture("before", *before)
        self.set_picture("after", *after)
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def set_picture(self, side, label, picture):
        """`side` "before" or "after"; `picture` a QPixmap, a file path or None (still on its way)."""
        failed = False
        if isinstance(picture, str):
            loaded = QtGui.QPixmap(picture)
            failed, picture = loaded.isNull(), (None if loaded.isNull() else loaded)
        elif picture is not None and picture.isNull():
            failed, picture = True, None
        self._sides[side] = (label, picture, failed)
        names = [self._sides.get(key, ("", None, False))[0] for key in ("before", "after")]
        self.setAccessibleName("{} / {} comparison".format(*names))
        self.updateGeometry()
        self.update()

    def label(self, side):
        return self._sides[side][0]

    def failed(self, side):
        return self._sides[side][2]

    def picture_rect(self, width=None):
        width = self.width() if width is None else width
        picture = self._sides["before"][1]
        if picture is None:
            return QtCore.QRectF(0, 0, width, width * self.LOADING_RATIO)
        ratio = picture.devicePixelRatioF() if hasattr(picture, "devicePixelRatioF") else picture.devicePixelRatio()
        natural = QtCore.QSizeF(picture.width() / max(1.0, ratio), picture.height() / max(1.0, ratio))
        shown = natural.scaled(min(float(width), natural.width()), 100000.0, Qt.KeepAspectRatio)
        return QtCore.QRectF((width - shown.width()) / 2.0, 0, shown.width(), shown.height())

    def set_position(self, position):
        position = max(0.0, min(1.0, float(position)))
        if position != self.position:
            self.position = position
            self.update()
            self.changed.emit(position)

    def _follow(self, event):
        target = self.picture_rect()
        point = event.position() if hasattr(event, "position") else event.pos()
        if target.width() > 0:
            self.set_position((point.x() - target.left()) / target.width())

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return int(round(self.picture_rect(width).height()))

    def sizeHint(self):
        return QtCore.QSize(px(400), self.heightForWidth(px(400)))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setFocus(Qt.MouseFocusReason)
            self._follow(event)
            event.accept()
            return
        QtWidgets.QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._follow(event)
            event.accept()
            return
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Left:
            self.set_position(self.position - self.STEP)
        elif key == Qt.Key_Right:
            self.set_position(self.position + self.STEP)
        elif key == Qt.Key_Home:
            self.set_position(0.0)
        elif key == Qt.Key_End:
            self.set_position(1.0)
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)
            return
        event.accept()

    def _badge_font(self):
        font = QtGui.QFont(self.font())
        font.setPointSizeF(max(7.0, font.pointSizeF() * 0.85))
        font.setBold(True)
        return font

    def badge_rects(self):
        target = self.picture_rect()
        metrics = QtGui.QFontMetricsF(self._badge_font())
        rects = []
        for index, side in enumerate(("before", "after")):
            text = self.label(side)
            advance = metrics.horizontalAdvance(text) if hasattr(metrics, "horizontalAdvance") else metrics.width(text)
            width, height = advance + space(16), metrics.height() + space(6)
            left = target.left() + space(8) if index == 0 else target.right() - space(8) - width
            rects.append(QtCore.QRectF(left, target.top() + space(8), width, height))
        return rects

    def badge_visible(self, index):
        """False while the divider covers the badge (0: Before, 1: After)."""
        target = self.picture_rect()
        split = target.left() + target.width() * self.position
        rect = self.badge_rects()[index]
        return split > rect.right() if index == 0 else split < rect.left()

    def _draw_side(self, painter, side, target, clip):
        label, picture, failed = self._sides[side]
        painter.save()
        painter.setClipRect(clip, Qt.IntersectClip)
        if picture is not None:
            source = QtCore.QRectF(picture.rect())
            if target.height() > 0 and source.height() > 0:  # Cropped to the Before shape, centred, never stretched
                wanted = target.width() / target.height()
                if source.width() / source.height() > wanted:
                    width = source.height() * wanted
                    source = QtCore.QRectF(source.left() + (source.width() - width) / 2.0, source.top(), width,
                                           source.height())
                else:
                    height = source.width() / wanted
                    source = QtCore.QRectF(source.left(), source.top() + (source.height() - height) / 2.0,
                                           source.width(), height)
            painter.drawPixmap(target, picture, source)
        else:
            painter.fillRect(target, QtGui.QColor(self._colors["recessed"]))
            if failed:
                painter.setPen(QtGui.QColor(self._colors["muted_text"]))
                painter.drawText(clip.intersected(target), int(Qt.AlignCenter), label)
        painter.restore()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        target = self.picture_rect()
        split = target.left() + target.width() * self.position
        shape = QtGui.QPainterPath()
        shape.addRoundedRect(target, px(8), px(8))
        painter.setClipPath(shape)
        self._draw_side(painter, "before", target,
                        QtCore.QRectF(target.left(), target.top(), split - target.left(), target.height()))
        self._draw_side(painter, "after", target,
                        QtCore.QRectF(split, target.top(), target.right() - split, target.height()))
        white = QtGui.QColor("#ffffff")
        line = px(2)
        painter.fillRect(QtCore.QRectF(split - line / 2.0, target.top(), line, target.height()), white)
        painter.setFont(self._badge_font())
        for index, (rect, side) in enumerate(zip(self.badge_rects(), ("before", "after"))):
            if not self.badge_visible(index):
                continue
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QColor(0, 0, 0, 165))
            painter.drawRoundedRect(rect, px(5), px(5))
            painter.setPen(white)
            painter.drawText(rect, int(Qt.AlignCenter), self.label(side))
        painter.setClipping(False)
        size = px(40)
        knob = QtCore.QRectF(split - size / 2.0, target.center().y() - size / 2.0, size, size)
        painter.setPen(QtGui.QPen(white, px(2)))
        painter.setBrush(QtGui.QColor(0, 0, 0, 115))
        painter.drawEllipse(knob.adjusted(1, 1, -1, -1))
        glyph = px(20)
        painter.drawPixmap(QtCore.QPointF(knob.center().x() - glyph / 2.0, knob.center().y() - glyph / 2.0),
                           icon_pixmap("chevrons-left-right", "#ffffff", glyph, device_pixel_ratio(self)))
        if self.hasFocus():
            painter.setPen(QtGui.QPen(QtGui.QColor(self._colors["focus"]), px(2)))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(knob.adjusted(-px(2), -px(2), px(2), px(2)))
        painter.end()
```

## `python/mytool/ui/states.py`

```python
"""States of a whole area: work running, a result, nothing to show.

* BusyOverlay (as MaxPkg Runtime Manager's work shade and busy card): the area under a blurred, tinted snapshot of
  itself and a card with the animated box, what runs, a calm hint and Cancel; it ends on the result (the tick or the
  alert) and fades away. Everything under it is blocked while it shows.
* ResultCard (as MaxRewind's notice): the outcome of a finished operation in the middle of the area over its blurred,
  dimmed content: a round icon in the result's colour, a bold line, a muted line, a bar that runs down to the card
  closing (it waits while the pointer is on the card), and, after a success, an optional note with a shimmering Donate
  (only when the owner gave a donation destination). A click elsewhere closes it. `celebrate=True` adds the confetti
  burst from its round icon (confetti.py) for a rare, real milestone.
* EmptyState (as Runtime Manager's state panel): an icon on a tinted disc, a title, a hint in help markup and an
  optional action ("No results" with Clear Search, "Offline" with Retry).
* StateArea: a list (or a grid) and its empty state in one place. The empty state takes the content's own room, centred,
  so nothing around it moves: the search field above a list stays where it was while the user types.
All three are child widgets of the area they cover, never translucent windows (risky inside Max). The confetti of a
celebrated result is its own short-lived layer (see confetti.py).
"""

import time

from .. import DONATE_URL
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, device_pixel_ratio
from ..ui_scale import px, space
from . import controls
from .confetti import burst
from .controls import Button, Shimmer, Themed, icon_pixmap
from .toast import StatusIcon

BLUR = 10  # The snapshot is shrunk this many times and smoothly scaled back: a soft, cheap blur


def blurred(pixmap):
    if pixmap.isNull():
        return None
    image = pixmap.toImage()
    small = image.scaled(max(1, image.width() // BLUR), max(1, image.height() // BLUR), Qt.IgnoreAspectRatio,
                         Qt.SmoothTransformation)
    return QtGui.QPixmap.fromImage(small.scaled(image.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))


class BusyOverlay(QtWidgets.QWidget, Themed):
    """See the module. `start(title, hint, on_cancel)`; `finish(kind, text)` with kind success / error shows the
    result for a moment, then the overlay goes."""

    cancelled = Signal()
    RESULT_MS = {"success": 1200, "error": 2600}

    def __init__(self, target, theme):
        QtWidgets.QWidget.__init__(self, target)
        self.target = target
        self._backdrop = None
        self.card = QtWidgets.QFrame(self)
        self.card.setObjectName("toolBusyCard")
        layout = QtWidgets.QVBoxLayout(self.card)
        layout.setContentsMargins(space(24), space(24), space(24), space(20))
        layout.setSpacing(space(6))
        self.icon = StatusIcon(theme, size=44)
        self.title = QtWidgets.QLabel("Working...")
        self.title.setObjectName("toolSection")
        self.hint = controls.muted("")
        for label in (self.title, self.hint):
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
        self.cancel_button = Button("Cancel", theme, icon="x")
        self.cancel_button.clicked.connect(self.cancelled.emit)
        layout.addWidget(self.icon, 0, Qt.AlignHCenter)
        layout.addSpacing(space(6))
        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        layout.addSpacing(space(6))
        layout.addWidget(self.cancel_button, 0, Qt.AlignHCenter)
        self.card.setFixedWidth(px(300))
        self._done = QtCore.QTimer(self)
        self._done.setSingleShot(True)
        self._done.timeout.connect(self.hide)
        target.installEventFilter(self)
        self.hide()
        self.bind_theme(theme)

    def start(self, title, hint="This usually takes a few seconds.", cancellable=True):
        self._done.stop()
        self.hide()  # Out of the snapshot of the area behind it
        self._backdrop = blurred(self.target.grab())
        self.setGeometry(self.target.rect())
        self.icon.set_state("running")
        self.title.setText(title)
        self.hint.setText(hint)
        self.hint.setVisible(bool(hint))
        self.cancel_button.setVisible(cancellable)
        self._place()
        self.raise_()
        self.show()
        self.setFocus()

    def finish(self, kind, text):
        """The work ended: "First line\\nmuted rest"; success draws the tick, anything else the alert."""
        lines = (text or "").split("\n", 1)
        self.icon.set_state("done" if kind == "success" else "error")
        self.title.setText(lines[0])
        self.hint.setText(lines[1] if len(lines) > 1 else ("" if kind == "success" else "Nothing was changed."))
        self.hint.setVisible(bool(self.hint.text()))
        self.cancel_button.hide()
        self._place()
        self._done.start(self.RESULT_MS.get(kind, 2600))

    def is_busy(self):
        return self.isVisible() and not self._done.isActive()

    def _place(self):
        self.card.adjustSize()
        self.card.move((self.width() - self.card.width()) // 2, (self.height() - self.card.height()) // 2)

    def eventFilter(self, watched, event):
        if watched is self.target and event.type() == QtCore.QEvent.Resize and self.isVisible():
            self.setGeometry(watched.rect())
            self._place()
        return False

    def mousePressEvent(self, event):
        event.accept()  # The area under it is blocked while work runs

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.cancel_button.isVisible():
            self.cancelled.emit()
            return
        event.accept()

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        colors = self._colors
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if self._backdrop is not None:
            painter.drawPixmap(self.rect(), self._backdrop)
        shade = QtGui.QColor(colors["recessed"])
        shade.setAlpha(140 if self._backdrop is not None else 190)
        painter.fillRect(self.rect(), shade)
        rect = QtCore.QRectF(self.card.geometry()).adjusted(0.5, 0.5, -0.5, -0.5)
        gradient = QtGui.QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0.0, QtGui.QColor(colors["popup"]))
        gradient.setColorAt(1.0, QtGui.QColor(colors["tab_pane_background"]))
        painter.setPen(QtGui.QPen(QtGui.QColor(colors["active_border"]), 1))
        painter.setBrush(QtGui.QBrush(gradient))
        painter.drawRoundedRect(rect, px(14), px(14))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 30), 1))  # The bright top edge of the glass
        painter.drawLine(QtCore.QPointF(rect.left() + px(14), rect.top() + 1),
                         QtCore.QPointF(rect.right() - px(14), rect.top() + 1))
        painter.end()


class ResultCard(QtWidgets.QWidget, Themed):
    """See the module. `show_message(kind, title, text, ms, donate_note)`; kind success / warning / error."""

    WIDTH = 320
    TICK_MS = 16
    ICONS = {"success": ("circle-check", "log_success"), "warning": ("circle-alert", "log_warning"),
             "error": ("circle-alert", "log_error")}

    def __init__(self, target, theme):
        QtWidgets.QWidget.__init__(self, target)
        self.target = target
        self._icon, self._role, self._title, self._text, self._note = "circle-check", "log_success", "", "", ""
        self._duration = self._left = 0.0
        self._last = None
        self._paused = False
        self._card = QtCore.QRectF()
        self._heights = (0, 0, 0)
        self._backdrop = None
        self._tick = QtCore.QTimer(self)
        self._tick.setInterval(self.TICK_MS)
        self._tick.timeout.connect(self._advance)
        self.donate_button = None
        if DONATE_URL:  # Only with a destination the owner gave
            self.donate_button = Button("Donate", theme, icon="heart", variant="donate", parent=self,
                                        tooltip="Opens the donation page in your browser")
            self.donate_button.setFocusPolicy(Qt.NoFocus)
            self.donate_button.setMinimumWidth(px(110))
            self.donate_button.clicked.connect(self._donate)
            self.donate_button.installEventFilter(self)
            self.donate_shimmer = Shimmer(self.donate_button)  # A light band sweeps over it every few seconds
            self.donate_shimmer.set_active(True)
            self.donate_button.hide()
        self.setMouseTracking(True)
        target.installEventFilter(self)
        self.hide()
        self.bind_theme(theme)

    def show_message(self, kind, title, text="", ms=4500, donate_note="", celebrate=False):
        """`donate_note`: a line above a Donate button after a success, or "" for no button. `celebrate`: confetti
        bursts from the round icon of a success (confetti.py); only for a rare, real milestone."""
        self._icon, self._role = self.ICONS.get(kind, self.ICONS["success"])
        self._title, self._text = title, text
        self._note = donate_note if self.donate_button is not None else ""
        self.hide()  # Out of the snapshot of the area behind it
        self.setGeometry(self.target.rect())
        self._backdrop = blurred(self.target.grab())
        self._duration = self._left = float(ms)
        self._last = time.monotonic()
        self._paused = False
        self._arrange()
        self.raise_()
        self.show()
        self.update()
        self._tick.start()
        if celebrate and kind == "success":  # A moment after the card is up, from the centre of its round icon
            QtCore.QTimer.singleShot(80, self._celebrate)

    def _celebrate(self):
        if not self.isVisible():
            return
        centre = QtCore.QPoint(int(self._card.center().x()), int(self._card.top() + px(22) + px(34) / 2))
        self.confetti = burst(self.window(), self._theme, self.mapToGlobal(centre))

    def _donate(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(DONATE_URL))
        self.hide()

    def _arrange(self):
        width = min(px(self.WIDTH), self.width() - px(24))
        bold = QtGui.QFont(self.font())
        bold.setBold(True)
        flags = int(Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap)
        title_h = QtGui.QFontMetrics(bold).boundingRect(0, 0, width - px(32), 1000, flags, self._title).height()
        text_h, note_h = (self.fontMetrics().boundingRect(0, 0, width - px(32), 1000, flags, line).height()
                          if line else 0 for line in (self._text, self._note))
        button = self.donate_button.sizeHint() if note_h else QtCore.QSize()
        height = px(22) + px(34) + px(12) + title_h + (px(4) + text_h if text_h else 0) \
            + (px(14) + note_h + px(8) + button.height() if note_h else 0) + px(26)
        card = QtCore.QRectF((self.width() - width) / 2.0, (self.height() - height) / 2.0, width, height)
        self._card, self._heights = card, (title_h, text_h, note_h)
        if self.donate_button is not None:
            if note_h:
                self.donate_button.setGeometry(int(card.center().x() - button.width() / 2.0),
                                               int(card.bottom() - px(26) - button.height()),
                                               button.width(), button.height())
            self.donate_button.setVisible(bool(note_h))

    def hideEvent(self, event):
        self._tick.stop()
        self._backdrop = None
        QtWidgets.QWidget.hideEvent(self, event)

    def _advance(self):
        now = time.monotonic()
        if not self._paused:
            self._left -= (now - self._last) * 1000.0
        self._last = now
        if self._left <= 0:
            self.hide()
            return
        self.update(self._card.toAlignedRect().adjusted(-2, -2, 2, 2))

    def _set_paused(self, paused):
        if paused != self._paused:
            self._paused = paused
            self._last = time.monotonic()

    def eventFilter(self, watched, event):
        if watched is self.target and event.type() == QtCore.QEvent.Resize:
            self.setGeometry(watched.rect())
            self._arrange()
        elif watched is self.donate_button and event.type() == QtCore.QEvent.Enter:
            self._set_paused(True)  # The card can come up under the pointer right on the button
        return False

    def mouseMoveEvent(self, event):
        position = getattr(event, "position", None)
        point = position() if position else QtCore.QPointF(event.pos())
        self._set_paused(self._card.contains(point))

    def leaveEvent(self, event):
        self._set_paused(False)
        QtWidgets.QWidget.leaveEvent(self, event)

    def mousePressEvent(self, event):
        self.hide()

    def _on_theme(self, colors):
        self._colors = colors
        if self.isVisible():
            self._arrange()
        self.update()

    def paintEvent(self, event):
        c = self._colors
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if self._backdrop is not None:
            painter.drawPixmap(self.rect(), self._backdrop)
        shade = QtGui.QColor(c["recessed"])
        shade.setAlpha(120 if self._backdrop is not None else 170)
        painter.fillRect(self.rect(), shade)
        card = self._card
        width = card.width()
        title_h, text_h, note_h = self._heights
        bold = QtGui.QFont(self.font())
        bold.setBold(True)
        flags = int(Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap)
        icon = px(34)
        painter.setPen(QtGui.QPen(QtGui.QColor(c["border"]), 1))
        painter.setBrush(QtGui.QColor(c["popup"]))
        painter.drawRoundedRect(card, px(10), px(10))
        y = card.top() + px(22)
        tone = QtGui.QColor(c[self._role])
        painter.drawPixmap(int(card.center().x() - icon / 2), int(y),
                           icon_pixmap(self._icon, c[self._role], icon, device_pixel_ratio(self)))
        y += icon + px(12)
        painter.setFont(bold)
        painter.setPen(QtGui.QColor(c["text"]))
        painter.drawText(QtCore.QRectF(card.left() + px(16), y, width - px(32), title_h), flags, self._title)
        if text_h:
            painter.setFont(self.font())
            painter.setPen(QtGui.QColor(c["muted_text"]))
            painter.drawText(QtCore.QRectF(card.left() + px(16), y + title_h + px(4), width - px(32), text_h), flags,
                             self._text)
        if note_h:
            y += title_h + (px(4) + text_h if text_h else 0) + px(14)
            painter.setFont(self.font())
            painter.setPen(QtGui.QColor(c["text"]))
            painter.drawText(QtCore.QRectF(card.left() + px(16), y, width - px(32), note_h), flags, self._note)
        bar_h = px(3)  # The countdown: a thin track along the bottom, the result's colour running down to the close
        track = QtCore.QRectF(card.left() + px(16), card.bottom() - px(12) - bar_h, width - px(32), bar_h)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QColor(c["border"]))
        painter.drawRoundedRect(track, bar_h / 2.0, bar_h / 2.0)
        share = max(0.0, min(1.0, self._left / self._duration)) if self._duration else 0.0
        if share > 0:
            if self._paused:
                tone.setAlpha(150)  # Held while the pointer is over the card
            painter.setBrush(tone)
            painter.drawRoundedRect(QtCore.QRectF(track.left(), track.top(), track.width() * share, bar_h),
                                    bar_h / 2.0, bar_h / 2.0)
        painter.end()


class EmptyState(QtWidgets.QFrame, Themed):
    """See the module. `action`: (label, Lucide icon, callback) or None."""

    def __init__(self, theme, icon, title, text, action=None, role="muted_text", parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setObjectName("toolEmptyState")
        self._icon_name, self._role = icon, role
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(space(24), space(24), space(24), space(24))
        layout.setSpacing(space(8))
        layout.addStretch(1)  # Centred in whatever room it gets (StateArea gives it the list's room)
        self.glyph = QtWidgets.QLabel()
        self.glyph.setFixedSize(px(56), px(56))
        self.glyph.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.glyph, 0, Qt.AlignHCenter)
        heading = QtWidgets.QLabel(title)
        heading.setObjectName("toolSection")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)
        self.text = QtWidgets.QLabel()
        self.text.setWordWrap(True)
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setTextFormat(Qt.RichText)
        self._raw_text = text
        layout.addWidget(self.text)
        self.action = None
        if action:
            label, icon_name, callback = action
            self.action = Button(label, theme, icon=icon_name)
            self.action.clicked.connect(callback)
            layout.addSpacing(space(4))
            layout.addWidget(self.action, 0, Qt.AlignHCenter)
        layout.addStretch(1)
        self.bind_theme(theme)

    def _on_theme(self, colors):
        size = px(56)
        ratio = device_pixel_ratio(self)
        pixmap = QtGui.QPixmap(int(size * ratio), int(size * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        disc = QtGui.QColor(colors[self._role])
        disc.setAlphaF(0.12)
        painter.setPen(Qt.NoPen)
        painter.setBrush(disc)
        painter.drawEllipse(QtCore.QRectF(0, 0, size, size))
        icon = px(26)
        painter.drawPixmap(int((size - icon) / 2), int((size - icon) / 2),
                           icon_pixmap(self._icon_name, colors[self._role], icon, ratio))
        painter.end()
        self.glyph.setPixmap(pixmap)
        self.text.setText(controls.help_html(self._raw_text, colors, "muted_text"))


class StateArea(QtWidgets.QWidget):
    """See the module. `content`: the list's frame or the grid; `empty`: its EmptyState. The area is as tall as the
    taller of the two, so showing the empty state never moves the controls above or below it."""

    def __init__(self, content, empty, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.content, self.empty = content, empty
        self.stack = QtWidgets.QStackedLayout(self)
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(content)
        self.stack.addWidget(empty)

    def set_empty(self, empty):
        self.stack.setCurrentWidget(self.empty if empty else self.content)

    def is_empty(self):
        return self.stack.currentWidget() is self.empty
```

## `python/mytool/ui/confetti.py`

```python
"""Confetti (as MaxPkg Packager's installer): a short burst from the success sign when a rare, real milestone succeeds
(a package installed, the first export of a project). The pieces fly up and out to both sides a little past the
window, flutter down and are gone by 100 px below its bottom edge; each one goes at its own moment, and most end in a
small four-pointed star in their colour with a white heart. The pieces thrown far to the side go soonest, so the middle
of the burst lingers. The layer lives 5 s.

The one translucent window of a tool, and only for those 5 s: it rounds nothing (that is what goes wrong with Max's
windows), takes no clicks, no keys and no focus (WindowTransparentForInput, WA_TransparentForMouseEvents,
WA_ShowWithoutActivating), belongs to the tool's window (a Qt.Tool window it owns: it closes with it) and deletes
itself. Safe mode leaves it out, like every other native extra. Use it once per real success, never for routine
results: the result card says the outcome, the confetti only celebrates it (ResultCard.show_message with
celebrate=True).
"""

import math
import random

from .. import qt_compat, ui_scale
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt
from ..ui_scale import px

LIFE_MS = 5000  # The layer's whole life
PIECES = 90
ROLES = ("accent", "log_success", "log_info", "log_system", "log_warning")  # The pieces' colours, in turn


def burst(window, theme, origin):
    """A burst from `origin` (a global point: the centre of the success sign) over `window`. Returns the layer, or
    None in safe mode or while the window is hidden or minimized. Keep the layer on the caller; it deletes itself."""
    if qt_compat.SAFE["on"] or window is None or not window.isVisible() or window.isMinimized():
        return None
    return Confetti(window, theme, origin)


def twinkle(painter, piece, flash, fade):
    """A four-pointed star in the piece's colour, white at its heart: it grows, turns a little and is gone.
    `flash` runs from 0 to 1 over the star's life; `fade` is the opacity below the window's bottom edge."""
    size = (3.0 + 9.0 * (1.0 - (1.0 - flash) ** 2)) * ui_scale.current["px"]
    waist = size * 0.18
    star = QtGui.QPainterPath()
    star.moveTo(0, -size)
    for x, y in ((waist, -waist), (size, 0), (waist, waist), (0, size), (-waist, waist), (-size, 0),
                 (-waist, -waist)):
        star.lineTo(x, y)
    star.closeSubpath()
    painter.save()
    painter.translate(piece["x"], piece["y"])
    painter.rotate(45 * flash)
    painter.setOpacity(fade * (1.0 - flash) ** 1.5)
    painter.setBrush(piece["color"].lighter(135))
    painter.drawPath(star)
    painter.setBrush(QtGui.QColor(255, 255, 255, 230))
    painter.drawEllipse(QtCore.QPointF(0, 0), waist * 0.9, waist * 0.9)
    painter.restore()


class Confetti(QtWidgets.QWidget):
    """See the module. A see-through layer over the screen around `window`: 0.55 of its width on each side, 0.45 of
    its height above and 110 px below, cut to the work area of its screen."""

    def __init__(self, window, theme, origin):
        flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint
        if hasattr(Qt, "WindowTransparentForInput"):
            flags |= Qt.WindowTransparentForInput
        QtWidgets.QWidget.__init__(self, window, flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose)
        frame = window.frameGeometry()
        area = frame.adjusted(-int(frame.width() * 0.55), -int(frame.height() * 0.45),
                              int(frame.width() * 0.55), px(110))
        screen = qt_compat.work_area(frame.center())
        if screen is not None:
            area = area.intersected(screen)
        self.setGeometry(area)
        self.floor = frame.bottom() - area.top()  # Below the window's bottom edge the pieces fade out
        start = origin - area.topLeft()
        colors = theme.colors
        scale = ui_scale.current["px"]
        self.pieces = []
        for index in range(PIECES):
            angle = math.radians(random.uniform(-160, -20))  # A fan up and out to both sides
            speed = random.uniform(460, 860) * scale
            self.pieces.append({
                "x": start.x() + random.uniform(-14, 14) * scale, "y": start.y(),
                "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed,
                "tilt": random.uniform(-30, 30), "flip": random.uniform(0, 6.28), "rate": random.uniform(4, 7),
                "w": 8 * scale, "h": 4.5 * scale, "color": QtGui.QColor(colors[ROLES[index % len(ROLES)]]),
                # Each piece goes at its own moment: thrown far to the side, sooner; the middle lingers
                "life": max(0.6, (1.3 + 3.3 * random.random() ** 0.7) *
                            (1.0 - 0.75 * min(1.0, abs(math.cos(angle)) * speed / (700 * scale)) ** 1.4)),
                "fade": random.uniform(0.12, 0.5),  # Its last moments: it shrinks away
                "sparkle": random.random() < 0.7})  # Most end in a little star
        self.clock = QtCore.QElapsedTimer()
        self.clock.start()
        self.last = 0
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.show()

    def tick(self):
        now = self.clock.elapsed()
        step = (now - self.last) / 1000.0
        self.last = now
        if now > LIFE_MS:
            self.timer.stop()
            self.close()  # WA_DeleteOnClose: gone with the burst
            return
        scale = ui_scale.current["px"]
        gravity = 650 * scale
        air = 0.985 ** (step * 60)
        for piece in self.pieces:
            piece["vx"] *= 0.963 ** (step * 60)  # The burst opens, then the pieces only fall
            piece["vy"] = min(piece["vy"] * air + gravity * step, 140 * scale)  # A gentle fall
            piece["x"] += piece["vx"] * step
            piece["y"] += piece["vy"] * step
            piece["flip"] += piece["rate"] * step
        self.update()

    def paintEvent(self, event):
        seconds = self.clock.elapsed() / 1000.0
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        reach = 100.0 * ui_scale.current["px"]  # Gone 100 px below the window
        for piece in self.pieces:
            below = (piece["y"] - self.floor) / reach
            if below >= 1.0:
                continue
            fade = 1.0 if below <= 0 else 1.0 - below
            left = (piece["life"] - seconds) / piece["fade"]
            if left <= 0:
                flash = -left * piece["fade"] / 0.32  # Then, for most, a little star flashes where it was
                if piece["sparkle"] and flash < 1.0:
                    twinkle(painter, piece, flash, fade)
                continue
            own = min(1.0, left)
            painter.setOpacity(own * fade)
            painter.save()
            painter.translate(piece["x"], piece["y"])
            painter.scale(0.4 + 0.6 * own, 0.4 + 0.6 * own)
            painter.rotate(piece["tilt"] + 15 * math.sin(piece["flip"] * 0.5))
            painter.scale(1.0, max(0.2, abs(math.cos(piece["flip"]))))  # It turns over as it flutters
            painter.setBrush(piece["color"])
            painter.drawRoundedRect(QtCore.QRectF(-piece["w"] / 2, -piece["h"] / 2, piece["w"], piece["h"]), 1, 1)
            painter.restore()
        painter.end()
```
