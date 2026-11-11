# Template: Charts and loading

Simple statistics in the tool's look (`charts.py`): stat tiles with a change against a named period and a sparkline, a column chart, a line chart with a crosshair, a donut with its legend; every chart shows the exact value under the pointer. The data colours are one fixed categorical palette, assigned in order and validated on every theme's panel colour. Showing that something is on its way (`loading.py`): a spinner beside a line of text, in a button that started work (`busy`) and large in the middle of an area; skeleton rows that hold the place of content; a progress ring with a known share or spinning; the steps of a short wizard.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP with the windows off screen (the controls trainer checks), and shown on screen in 3ds Max 2027.

## `python/mytool/ui/charts.py`

```python
"""Simple statistics in the tool's look: stat tiles, a column chart, a line chart, a donut and a sparkline.

Painted with QPainter in the theme's ink colours; the data colours are one fixed categorical palette (SERIES, the
data-viz method's dark palette, checked with its validator on every theme's panel colour), assigned in order, never
cycled: a ninth series folds into "Other". The rules that keep them readable:

* One axis, never two. Thin marks: columns at most 24 px wide with a 4 px rounded top and a square base, 2 px lines,
  markers of at least 8 px with a ring in the panel colour, an area wash of about 10 %.
* Hairline gridlines one step off the panel; tick values rounded to clean numbers (1,000 / 10K).
* Text never wears a data colour: labels, values and legends use the text colours; a swatch beside them carries the
  colour. A legend for two series or more; a single series needs none (its title names it). Labels are selective:
  the hovered mark and the largest, never a number on every mark.
* Hover is part of the chart: a tooltip with the exact value on a column, a donut part, or along a line (with a
  crosshair). On the 3ds Max theme's grey panel several colours sit below 3:1: the legend, the labels and the tooltips
  carry the values, never the colour alone.
"""

import math

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt
from ..ui_scale import pt, px, space
from .controls import Themed, hide_tip, show_tip

# The data-viz method's dark categorical palette, in its fixed order (blue, orange, aqua, yellow, magenta, green,
# violet, red). Validated on every theme's panel: adjacent pairs CVD delta E >= 8.4, normal vision >= 19.3.
SERIES = ("#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767")


def compact(value):
    """1,284 / 12.9K / 4.2M: in full under 10,000, compact above."""
    value = float(value)
    if abs(value) < 10000:
        return "{:,.0f}".format(value) if value == int(value) else "{:,.1f}".format(value)
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= limit:
            text = "{:.1f}".format(value / limit).rstrip("0").rstrip(".")
            return text + suffix
    return str(value)


def nice_ticks(top, count=4):
    """Clean tick values from 0 to at least `top`: steps of 1, 2, 2.5 or 5 times a power of ten."""
    if top <= 0:
        return [0, 1]
    raw = top / float(count)
    power = 10 ** math.floor(math.log10(raw))
    step = next(power * factor for factor in (1, 2, 2.5, 5, 10) if power * factor >= raw)
    ticks = [0.0]
    while ticks[-1] < top:
        ticks.append(ticks[-1] + step)
    return ticks


def _text_width(metrics, text):
    return metrics.horizontalAdvance(text) if hasattr(metrics, "horizontalAdvance") else metrics.width(text)


class _Chart(QtWidgets.QWidget, Themed):
    """Shared: theme colours, the hover tooltip and the grid."""

    def __init__(self, theme, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover)
        self.hover = None
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def _ink(self, role):
        return QtGui.QColor(self._colors[role])

    def _grid(self):
        color = self._ink("border")
        color.setAlpha(110)  # Recessive: one step off the panel
        return color

    def _show_tip(self, event, text):
        position = getattr(event, "globalPosition", None)
        point = position().toPoint() if position else event.globalPos()
        show_tip(self, point, text)  # The tool's rounded Tip, under the pointer

    def leaveEvent(self, event):
        self.hover = None
        hide_tip(self)
        self.update()
        QtWidgets.QWidget.leaveEvent(self, event)

    def _legend(self, painter, names, top):
        """Swatches and names in one row from the left; returns the row's height."""
        metrics = self.fontMetrics()
        x, size = 0.0, px(10)
        for index, name in enumerate(names):
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QColor(SERIES[index % len(SERIES)]))
            painter.drawRoundedRect(QtCore.QRectF(x, top + (metrics.height() - size) / 2.0, size, size), px(2), px(2))
            painter.setPen(self._ink("text"))
            painter.drawText(QtCore.QPointF(x + size + px(6), top + metrics.ascent()), name)
            x += size + px(6) + _text_width(metrics, name) + px(16)
        return metrics.height() + px(8)


class StatTile(QtWidgets.QFrame, Themed):
    """A number that matters at a glance: the label (muted, sentence case), the value (large, semibold, compact), and an
    optional change against a named period with an arrow, green when the change is good (`up_is_good`) and red when it
    is not, plus an optional 12-point sparkline of the trend."""

    def __init__(self, theme, label, value, unit="", delta=None, period="vs last week", up_is_good=True, trend=None,
                 parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setObjectName("toolStatTile")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(space(12), space(12), space(12), space(12))
        layout.setSpacing(space(2))
        caption = QtWidgets.QLabel(label)
        caption.setObjectName("toolMuted")
        layout.addWidget(caption)
        self.value = QtWidgets.QLabel(compact(value) + unit)
        self.value.setObjectName("toolStatValue")  # The one label with its own, larger size
        font = self.value.font()
        font.setPointSizeF(pt(15))  # Its own size at the interface size (a set font is never reset to the window's)
        font.setBold(True)
        self.value.setFont(font)
        layout.addWidget(self.value)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(6))
        self.delta = None
        if delta is not None:
            good = (delta >= 0) == up_is_good
            self.delta = QtWidgets.QLabel("{} {:+.0%} {}".format("▲" if delta >= 0 else "▼", delta, period))
            self.delta.setObjectName("toolDeltaGood" if good else "toolDeltaBad")
            row.addWidget(self.delta)
        row.addStretch(1)
        if trend:
            row.addWidget(Sparkline(theme, trend))
        layout.addLayout(row)
        layout.addStretch(1)  # Tiles in a row share a height; the content stays at the top of each
        self.bind_theme(theme)

    def _on_theme(self, colors):
        if self.delta is not None:
            role = "log_success" if self.delta.objectName() == "toolDeltaGood" else "log_error"
            self.delta.setStyleSheet("color: {};".format(colors[role]))


class Sparkline(QtWidgets.QWidget, Themed):
    """A tiny trend line without axes: the series in the muted ink, the last point in the accent colour."""

    def __init__(self, theme, values, width=72, height=22, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.values = list(values)
        self.setFixedSize(px(width), px(height))
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        if len(self.values) < 2:
            return
        low, high = min(self.values), max(self.values)
        span = (high - low) or 1.0
        pad = px(3)
        width, height = self.width() - 2 * pad, self.height() - 2 * pad
        points = [QtCore.QPointF(pad + width * index / float(len(self.values) - 1),
                                 pad + height * (1.0 - (value - low) / span)) for index, value in enumerate(self.values)]
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor(self._colors["muted_text"]), px(1.5))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPolyline(QtGui.QPolygonF(points))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QColor(self._colors["accent"]))
        painter.drawEllipse(points[-1], px(2.5), px(2.5))
        painter.end()


class BarChart(_Chart):
    """Columns from one baseline: `items` [(label, value)], one series in the first data colour (no legend), the
    value of the hovered column and of the largest printed on its cap, a tooltip with the exact value."""

    def __init__(self, theme, items, unit="", parent=None):
        _Chart.__init__(self, theme, parent)
        self.items, self.unit = list(items), unit
        self.setMinimumHeight(px(190))

    def set_items(self, items):
        self.items = list(items)
        self.update()

    def _layout(self):
        metrics = self.fontMetrics()
        ticks = nice_ticks(max([value for _label, value in self.items] or [1]))
        left = max(_text_width(metrics, compact(tick)) for tick in ticks) + px(8)
        top, bottom = metrics.height() + px(4), self.height() - metrics.height() - px(8)
        plot = QtCore.QRectF(left, top, self.width() - left - px(4), max(10.0, bottom - top))
        return ticks, plot

    def bars(self):
        """[(rect, label, value)] in widget coordinates."""
        if not self.items:
            return []
        ticks, plot = self._layout()
        slot = plot.width() / len(self.items)
        width = min(px(24), slot * 0.6)  # Thin: never fill the slot
        result = []
        for index, (label, value) in enumerate(self.items):
            height = plot.height() * value / ticks[-1]
            x = plot.left() + slot * index + (slot - width) / 2.0
            result.append((QtCore.QRectF(x, plot.bottom() - height, width, height), label, value))
        return result

    def mouseMoveEvent(self, event):
        position = getattr(event, "position", None)
        point = position() if position else QtCore.QPointF(event.pos())
        hover = None
        _ticks, plot = self._layout()
        slot = plot.width() / max(1, len(self.items))
        for index, (rect, label, value) in enumerate(self.bars()):  # The whole slot is the target, not the thin bar
            if plot.left() + slot * index <= point.x() < plot.left() + slot * (index + 1):
                hover = index
                self._show_tip(event, "{}: {}{}".format(label, "{:,}".format(value), self.unit))
        if hover != self.hover:
            self.hover = hover
            self.update()

    def paintEvent(self, event):
        if not self.items:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        ticks, plot = self._layout()
        metrics = self.fontMetrics()
        for tick in ticks:  # Hairline grid and clean tick values
            y = plot.bottom() - plot.height() * tick / ticks[-1]
            painter.setPen(QtGui.QPen(self._grid(), 1))
            painter.drawLine(QtCore.QPointF(plot.left(), y), QtCore.QPointF(plot.right(), y))
            painter.setPen(self._ink("muted_text"))
            painter.drawText(QtCore.QRectF(0, y - metrics.height() / 2.0, plot.left() - px(6), metrics.height()),
                             int(Qt.AlignRight | Qt.AlignVCenter), compact(tick))
        largest = max(range(len(self.items)), key=lambda index: self.items[index][1])
        color = QtGui.QColor(SERIES[0])
        for index, (rect, label, value) in enumerate(self.bars()):
            path = QtGui.QPainterPath()  # A 4 px rounded cap, square at the baseline
            radius = min(px(4), rect.width() / 2.0, rect.height())
            path.moveTo(rect.left(), rect.bottom())
            path.lineTo(rect.left(), rect.top() + radius)
            path.quadTo(rect.left(), rect.top(), rect.left() + radius, rect.top())
            path.lineTo(rect.right() - radius, rect.top())
            path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + radius)
            path.lineTo(rect.right(), rect.bottom())
            path.closeSubpath()
            shade = QtGui.QColor(color)
            if self.hover is not None and index != self.hover:
                shade.setAlphaF(0.55)  # The hovered column stands out
            painter.fillPath(path, shade)
            if index in (largest, self.hover):
                painter.setPen(self._ink("text"))
                painter.drawText(QtCore.QRectF(rect.center().x() - px(40), rect.top() - metrics.height() - px(2),
                                               px(80), metrics.height()), int(Qt.AlignCenter), compact(value))
            painter.setPen(self._ink("muted_text"))
            slot = plot.width() / len(self.items)
            painter.drawText(QtCore.QRectF(rect.center().x() - slot / 2.0, plot.bottom() + px(4), slot,
                                           metrics.height()), int(Qt.AlignHCenter | Qt.AlignTop),
                             metrics.elidedText(label, Qt.ElideRight, int(slot - px(4))))
        painter.setPen(QtGui.QPen(self._ink("border"), 1))  # The baseline
        painter.drawLine(QtCore.QPointF(plot.left(), plot.bottom()), QtCore.QPointF(plot.right(), plot.bottom()))
        painter.end()


class LineChart(_Chart):
    """Values over time: `series` [(name, [values])] against `labels` (one per point). 2 px lines, an area wash under a
    single series, a legend for two or more; hovering shows a crosshair, the points of every series on it and a tooltip
    with their values."""

    def __init__(self, theme, labels, series, unit="", parent=None):
        _Chart.__init__(self, theme, parent)
        self.labels, self.series, self.unit = list(labels), list(series), unit
        self.setMinimumHeight(px(200))

    def _layout(self):
        metrics = self.fontMetrics()
        legend = metrics.height() + px(8) if len(self.series) > 1 else 0
        ticks = nice_ticks(max(max(values) for _name, values in self.series))
        left = max(_text_width(metrics, compact(tick)) for tick in ticks) + px(8)
        top, bottom = legend + metrics.height() / 2.0 + px(2), self.height() - metrics.height() - px(8)
        return legend, ticks, QtCore.QRectF(left, top, self.width() - left - px(10), max(10.0, bottom - top))

    def _point(self, plot, ticks, index, value):
        x = plot.left() + plot.width() * index / float(max(1, len(self.labels) - 1))
        return QtCore.QPointF(x, plot.bottom() - plot.height() * value / ticks[-1])

    def mouseMoveEvent(self, event):
        position = getattr(event, "position", None)
        point = position() if position else QtCore.QPointF(event.pos())
        _legend, _ticks, plot = self._layout()
        share = (point.x() - plot.left()) / max(1.0, plot.width())
        index = int(round(share * (len(self.labels) - 1)))
        hover = index if 0 <= index < len(self.labels) and plot.adjusted(-px(8), 0, px(8), 0).contains(point) else None
        if hover is not None:
            lines = [self.labels[hover]] + ["{}: {:,}{}".format(name, values[hover], self.unit)
                                            for name, values in self.series]
            self._show_tip(event, "\n".join(lines))
        if hover != self.hover:
            self.hover = hover
            self.update()

    def paintEvent(self, event):
        if not self.series or len(self.labels) < 2:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        legend, ticks, plot = self._layout()
        metrics = self.fontMetrics()
        if legend:
            self._legend(painter, [name for name, _values in self.series], 0)
        for tick in ticks:
            y = plot.bottom() - plot.height() * tick / ticks[-1]
            painter.setPen(QtGui.QPen(self._grid(), 1))
            painter.drawLine(QtCore.QPointF(plot.left(), y), QtCore.QPointF(plot.right(), y))
            painter.setPen(self._ink("muted_text"))
            painter.drawText(QtCore.QRectF(0, y - metrics.height() / 2.0, plot.left() - px(6), metrics.height()),
                             int(Qt.AlignRight | Qt.AlignVCenter), compact(tick))
        step = max(1, int(math.ceil(len(self.labels) * _text_width(metrics, "Mon 00") / max(1.0, plot.width()))))
        for index in range(0, len(self.labels), step):  # Labels that fit side by side
            x = plot.left() + plot.width() * index / float(len(self.labels) - 1)
            painter.drawText(QtCore.QRectF(x - px(40), plot.bottom() + px(4), px(80), metrics.height()),
                             int(Qt.AlignHCenter | Qt.AlignTop), self.labels[index])
        if self.hover is not None:  # The crosshair
            x = self._point(plot, ticks, self.hover, 0).x()
            painter.setPen(QtGui.QPen(self._ink("muted_text"), 1))
            painter.drawLine(QtCore.QPointF(x, plot.top()), QtCore.QPointF(x, plot.bottom()))
        for number, (name, values) in enumerate(self.series):
            color = QtGui.QColor(SERIES[number % len(SERIES)])
            points = [self._point(plot, ticks, index, value) for index, value in enumerate(values)]
            if len(self.series) == 1:  # A wash under a single series
                area = QtGui.QPolygonF(points + [QtCore.QPointF(points[-1].x(), plot.bottom()),
                                                 QtCore.QPointF(points[0].x(), plot.bottom())])
                wash = QtGui.QColor(color)
                wash.setAlphaF(0.12)
                painter.setPen(Qt.NoPen)
                painter.setBrush(wash)
                painter.drawPolygon(area)
            pen = QtGui.QPen(color, px(2))
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPolyline(QtGui.QPolygonF(points))
            marks = [len(values) - 1] + ([self.hover] if self.hover is not None else [])
            for index in marks:  # The end point and the hovered points, ringed in the panel colour
                painter.setPen(QtGui.QPen(QtGui.QColor(self._colors["tab_pane_background"]), px(2)))
                painter.setBrush(color)
                painter.drawEllipse(points[index], px(4.5), px(4.5))
        painter.setPen(QtGui.QPen(self._ink("border"), 1))
        painter.drawLine(QtCore.QPointF(plot.left(), plot.bottom()), QtCore.QPointF(plot.right(), plot.bottom()))
        painter.end()


class DonutChart(_Chart):
    """Parts of one whole: `parts` [(name, value)] around a ring with 2 px gaps in the panel colour, the total and its
    caption in the middle, a legend at the right with each share; hovering a part shows its name, value and share."""

    def __init__(self, theme, parts, caption="Total", unit="", parent=None):
        _Chart.__init__(self, theme, parent)
        self.parts, self.caption, self.unit = list(parts), caption, unit
        self.setMinimumHeight(px(170))

    def _ring(self):
        size = min(self.height(), self.width() * 0.45) - px(4)
        return QtCore.QRectF(px(2), (self.height() - size) / 2.0, size, size)

    def _angle_at(self, point):
        ring = self._ring()
        dx, dy = point.x() - ring.center().x(), ring.center().y() - point.y()
        distance = math.hypot(dx, dy)
        if not (ring.width() * 0.3 <= distance <= ring.width() / 2.0 + px(4)):
            return None
        return (90.0 - math.degrees(math.atan2(dy, dx))) % 360.0  # Clockwise from the top

    def mouseMoveEvent(self, event):
        position = getattr(event, "position", None)
        point = position() if position else QtCore.QPointF(event.pos())
        angle = self._angle_at(point)
        hover = None
        total = float(sum(value for _name, value in self.parts)) or 1.0
        if angle is not None:
            start = 0.0
            for index, (name, value) in enumerate(self.parts):
                sweep = 360.0 * value / total
                if start <= angle < start + sweep:
                    hover = index
                    self._show_tip(event, "{}: {:,}{} ({:.0%})".format(name, value, self.unit, value / total))
                start += sweep
        if hover != self.hover:
            self.hover = hover
            self.update()

    def paintEvent(self, event):
        if not self.parts:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        ring = self._ring()
        thickness = ring.width() * 0.2
        total = float(sum(value for _name, value in self.parts)) or 1.0
        start = 90.0  # Qt angles: counter-clockwise from 3 o'clock; parts run clockwise from the top
        for index, (name, value) in enumerate(self.parts):
            sweep = 360.0 * value / total
            pen = QtGui.QPen(QtGui.QColor(SERIES[index % len(SERIES)]),
                             thickness + (px(4) if index == self.hover else 0))
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            arc = ring.adjusted(thickness / 2.0, thickness / 2.0, -thickness / 2.0, -thickness / 2.0)
            painter.drawArc(arc, int(start * 16), int(-sweep * 16))
            start -= sweep
        start = 90.0  # The 2 px gaps in the panel colour between the parts
        painter.setPen(QtGui.QPen(QtGui.QColor(self._colors["tab_pane_background"]), px(2)))
        centre = ring.center()
        for _name, value in self.parts:
            radians = math.radians(start)
            outer = ring.width() / 2.0 + px(3)
            painter.drawLine(QtCore.QPointF(centre.x() + math.cos(radians) * (outer - thickness - px(6)),
                                            centre.y() - math.sin(radians) * (outer - thickness - px(6))),
                             QtCore.QPointF(centre.x() + math.cos(radians) * outer,
                                            centre.y() - math.sin(radians) * outer))
            start -= 360.0 * value / total
        metrics = self.fontMetrics()
        bold = QtGui.QFont(self.font())
        bold.setBold(True)
        bold.setPointSizeF(max(1.0, self.font().pointSizeF() * 1.4))
        painter.setFont(bold)
        painter.setPen(self._ink("text"))
        painter.drawText(QtCore.QRectF(ring.left(), centre.y() - metrics.height() * 1.1, ring.width(),
                                       metrics.height() * 1.3), int(Qt.AlignCenter), compact(total) + self.unit)
        painter.setFont(self.font())
        painter.setPen(self._ink("muted_text"))
        painter.drawText(QtCore.QRectF(ring.left(), centre.y() + px(2), ring.width(), metrics.height()),
                         int(Qt.AlignCenter), self.caption)
        x = ring.right() + px(18)  # The legend: swatch, name, share
        strong = QtGui.QFont(self.font())
        strong.setBold(True)
        y = centre.y() - (len(self.parts) * (metrics.height() + px(6))) / 2.0
        for index, (name, value) in enumerate(self.parts):
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QColor(SERIES[index % len(SERIES)]))
            painter.drawRoundedRect(QtCore.QRectF(x, y + (metrics.height() - px(10)) / 2.0, px(10), px(10)), px(2), px(2))
            painter.setFont(strong if index == self.hover else self.font())  # The hovered part's name in bold
            painter.setPen(self._ink("text"))
            painter.drawText(QtCore.QPointF(x + px(16), y + metrics.ascent()), name)
            painter.setPen(self._ink("muted_text"))
            painter.drawText(QtCore.QRectF(x, y, self.width() - x - px(4), metrics.height()),
                             int(Qt.AlignRight | Qt.AlignVCenter), "{:.0%}".format(value / total))
            y += metrics.height() + px(6)
        painter.end()
```

## `python/mytool/ui/loading.py`

```python
"""Showing that something is on its way.

* Spinner: a faint ring with an accent arc that turns and breathes in length (as the gallery's preloader); 16 px next
  to a line of text, 24-40 px in the middle of an area. Its timer runs only while it is visible.
* busy(button, on, text): a button that started work shows a spinner in place of its icon, says what runs
  ("Loading..."), and cannot be clicked again until the work ends; then it is itself again.
* Skeleton: grey rounded bars where content will appear (a list, a card), with a soft light sweeping over them, so the
  layout does not jump when the content arrives.
* ProgressRing: a ring that fills with the share done and prints it in the middle; without a share it spins.
* Steps: the steps of a short wizard in a row. The current step is the loudest mark (a solid accent disc with its
  number and a soft halo, its name in bold); done steps step back to an accent tint with a check; steps to come are a
  grey ring with a muted number. The joining line is accent up to the current step.
Use the progress bar (controls.ProgressBar) for long work in the status bar, the busy overlay (states.BusyOverlay) when
work blocks a whole area, and these for the small cases.
"""

import math
import time

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, device_pixel_ratio
from ..ui_scale import px, space
from .controls import Themed, icon_pixmap


class Spinner(QtWidgets.QWidget, Themed):
    """See the module. `size`: logical px."""

    def __init__(self, theme, size=16, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setFixedSize(px(size), px(size))
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._started = time.monotonic()
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.update)
        self.bind_theme(theme)

    def showEvent(self, event):
        self._timer.start()
        QtWidgets.QWidget.showEvent(self, event)

    def hideEvent(self, event):
        self._timer.stop()
        QtWidgets.QWidget.hideEvent(self, event)

    def is_turning(self):
        return self._timer.isActive()

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        seconds = time.monotonic() - self._started
        width = max(1.5, self.width() / 8.0)
        ring = QtCore.QRectF(self.rect()).adjusted(width, width, -width, -width)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        track = QtGui.QColor(self._colors["border"])
        painter.setPen(QtGui.QPen(track, width))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(ring)
        pen = QtGui.QPen(QtGui.QColor(self._colors["accent"]), width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        span = 60.0 + 120.0 * (0.5 + 0.5 * math.sin(seconds * 3.2))
        painter.drawArc(ring, int(-seconds * 300.0 * 16), int(-span * 16))
        painter.end()


def busy(button, on, text=None):
    """Show `button` working: a spinner where its icon was, `text` ("Loading...") and no clicks until busy(button,
    False) gives it back its own icon, text and state."""
    if on:
        if getattr(button, "_busy", None) is not None:
            return
        theme = button._theme
        button._busy = (button.text(), button.icon(), button.isEnabled())
        size = button.iconSize()
        empty = QtGui.QPixmap(size)
        empty.fill(Qt.transparent)
        button.setIcon(QtGui.QIcon(empty))  # Keeps the room of the icon for the spinner
        if text:
            button.setText(text)
        button.setEnabled(False)
        spinner = Spinner(theme, max(10, int(size.width() / max(0.01, px(1)))), button)
        spinner.setFixedSize(size)
        spinner.move(px(12), (button.height() - size.height()) // 2)
        spinner.show()
        button._spinner = spinner
    else:
        state = getattr(button, "_busy", None)
        if state is None:
            return
        text_before, _icon, enabled = state
        button._busy = None
        if getattr(button, "_spinner", None) is not None:
            button._spinner.hide()
            button._spinner.deleteLater()
            button._spinner = None
        button.setText(text_before)
        button._on_theme(button._theme.colors)  # Its own icon again, in the theme's colour
        button.setEnabled(enabled)


class Skeleton(QtWidgets.QWidget, Themed):
    """See the module. `lines`: the widths of the bars as shares of the width (a title then text lines); `avatar` puts
    a round placeholder at the left (a list row with a picture)."""

    SWEEP_MS = 1300

    def __init__(self, theme, lines=(0.45, 0.9, 0.75), avatar=False, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.lines, self.avatar = lines, avatar
        self.setMinimumHeight(px(14) * len(lines) + px(8) * (len(lines) - 1) + px(4))
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._started = time.monotonic()
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self.update)
        self.bind_theme(theme)

    def showEvent(self, event):
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
        base = QtGui.QColor(self._colors["surface"])
        path = QtGui.QPainterPath()
        left = 0.0
        if self.avatar:
            size = min(self.height(), px(40))
            path.addEllipse(QtCore.QRectF(0, (self.height() - size) / 2.0, size, size))
            left = size + px(12)
        bar, gap = px(14), px(8)
        top = (self.height() - (bar * len(self.lines) + gap * (len(self.lines) - 1))) / 2.0
        for index, share in enumerate(self.lines):
            path.addRoundedRect(QtCore.QRectF(left, top + index * (bar + gap), (self.width() - left) * share, bar),
                                bar / 2.0, bar / 2.0)
        painter.fillPath(path, base)
        phase = ((time.monotonic() - self._started) * 1000.0 % self.SWEEP_MS) / self.SWEEP_MS
        x = -self.width() * 0.4 + phase * self.width() * 1.8
        light = QtGui.QLinearGradient(x - px(60), 0, x + px(60), 0)
        glow = QtGui.QColor(self._colors["hover"])
        glow.setAlpha(0)
        light.setColorAt(0.0, glow)
        glow.setAlpha(255)
        light.setColorAt(0.5, glow)
        glow.setAlpha(0)
        light.setColorAt(1.0, glow)
        painter.setClipPath(path)
        painter.fillRect(self.rect(), QtGui.QBrush(light))
        painter.end()


class ProgressRing(QtWidgets.QWidget, Themed):
    """See the module. `set_value(share)` with 0..1, or None for a spinning ring."""

    def __init__(self, theme, size=56, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setFixedSize(px(size), px(size))
        self._value = None
        self._started = time.monotonic()
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.update)
        self.bind_theme(theme)

    def set_value(self, share):
        self._value = None if share is None else max(0.0, min(1.0, float(share)))
        self.setAccessibleName("Working" if self._value is None else "{:.0%} done".format(self._value))
        self._sync_timer()
        self.update()

    def value(self):
        return self._value

    def _sync_timer(self):
        if self._value is None and self.isVisible():
            self._timer.start()
        else:
            self._timer.stop()

    def showEvent(self, event):
        QtWidgets.QWidget.showEvent(self, event)
        self._sync_timer()

    def hideEvent(self, event):
        self._timer.stop()
        QtWidgets.QWidget.hideEvent(self, event)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        colors = self._colors
        width = max(3.0, self.width() / 11.0)
        ring = QtCore.QRectF(self.rect()).adjusted(width, width, -width, -width)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor(colors["recessed"]), width))
        painter.drawEllipse(ring)
        pen = QtGui.QPen(QtGui.QColor(colors["accent"]), width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        if self._value is None:
            seconds = time.monotonic() - self._started
            painter.drawArc(ring, int(-seconds * 260.0 * 16), int(-100 * 16))
        else:
            if self._value > 0:
                painter.drawArc(ring, 90 * 16, int(-self._value * 360 * 16))
            font = QtGui.QFont(self.font())
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QtGui.QColor(colors["text"]))
            painter.drawText(self.rect(), int(Qt.AlignCenter), "{:.0%}".format(self._value))
        painter.end()


class Steps(QtWidgets.QWidget, Themed):
    """See the module. `set_current(index)`; the steps before it are done."""

    DISC, HALO = 24, 4  # The step disc and the soft ring around the current one, logical px

    def __init__(self, theme, names, current=0, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.names, self.current = list(names), current
        self.setMinimumHeight(px(self.DISC + 2 * self.HALO) + space(4) + self.fontMetrics().height() + space(2))
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.bind_theme(theme)

    def set_current(self, index):
        self.current = max(0, min(len(self.names), index))
        self.update()

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def state(self, index):
        """"done", "current" or "next": what the step at `index` shows."""
        if index < self.current:
            return "done"
        return "current" if index == self.current else "next"

    def paintEvent(self, event):
        # The current step is the loudest mark: a solid accent disc with its number and a soft accent halo. Done steps
        # step back to an accent tint with an accent check; steps to come are a grey ring with a muted number. The line
        # is accent up to the current step.
        colors = self._colors
        accent = QtGui.QColor(colors["accent"])
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        count = len(self.names)
        disc, halo = px(self.DISC), px(self.HALO)
        slot = self.width() / float(max(1, count))
        centres = [slot * (index + 0.5) for index in range(count)]
        middle = halo + disc / 2.0
        for index in range(count - 1):
            line = QtGui.QPen(QtGui.QColor(colors["accent" if index < self.current else "border"]), px(2))
            line.setCapStyle(Qt.RoundCap)
            painter.setPen(line)
            painter.drawLine(QtCore.QPointF(centres[index] + disc / 2.0 + halo + px(2), middle),
                             QtCore.QPointF(centres[index + 1] - disc / 2.0 - halo - px(2), middle))
        bold = QtGui.QFont(self.font())
        bold.setBold(True)
        for index, (centre, name) in enumerate(zip(centres, self.names)):
            rect = QtCore.QRectF(centre - disc / 2.0, halo, disc, disc)
            state = self.state(index)
            if state == "current":
                glow = QtGui.QColor(accent)
                glow.setAlphaF(0.28)
                painter.setPen(Qt.NoPen)
                painter.setBrush(glow)
                painter.drawEllipse(rect.adjusted(-halo, -halo, halo, halo))
                painter.setBrush(accent)
                painter.drawEllipse(rect)
                painter.setFont(bold)
                painter.setPen(QtGui.QColor(colors["log_badge_text"]))
                painter.drawText(rect, int(Qt.AlignCenter), str(index + 1))
            elif state == "done":
                tint = QtGui.QColor(accent)
                tint.setAlphaF(0.22)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QtGui.QColor(colors["window"]))
                painter.drawEllipse(rect)
                painter.setBrush(tint)
                painter.drawEllipse(rect)
                size = px(14)
                painter.drawPixmap(QtCore.QPointF(centre - size / 2.0, middle - size / 2.0),
                                   icon_pixmap("check", colors["accent"], size, device_pixel_ratio(self)))
            else:
                width = px(1.5)
                painter.setPen(QtGui.QPen(QtGui.QColor(colors["border"]), width))
                painter.setBrush(QtGui.QColor(colors["window"]))
                painter.drawEllipse(rect.adjusted(width / 2.0, width / 2.0, -width / 2.0, -width / 2.0))
                painter.setFont(self.font())
                painter.setPen(QtGui.QColor(colors["muted_text"]))
                painter.drawText(rect, int(Qt.AlignCenter), str(index + 1))
            painter.setFont(bold if state == "current" else self.font())
            painter.setPen(QtGui.QColor(colors["muted_text" if state == "next" else "text"]))
            painter.drawText(QtCore.QRectF(centre - slot / 2.0, disc + 2 * halo + space(4), slot,
                                           self.fontMetrics().height() + 2), int(Qt.AlignHCenter | Qt.AlignTop), name)
        painter.end()
```
