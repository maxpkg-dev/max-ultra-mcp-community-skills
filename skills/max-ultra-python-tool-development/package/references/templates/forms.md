# Template: Forms, switches and pickers

The building blocks of a tool's pages: rounded panels with a title, a red star when the content is required and a "?" balloon (`panel`); the caption above a field with its own red star (`caption`, `labeled`, `required_mark`); collapsible groups whose title looks like a panel title (`Collapsible`, `GroupHeader`); the dropdown whose items are coloured badges, closed and open, sized to its content (`BadgeComboBox`, `BadgeDelegate`, `draw_badge`); the switch that replaces check boxes for on / off options (`Switch`); the number stepper in one rounded field, with leading zeros and wrapping when asked (`Stepper`); the time field (`TimeEdit`); and the date field with its themed calendar: the title steps out to the months and to twelve years, the keys work as in Windows' calendar, a range greys out the rest, and with a time a click selects and Done applies the date and the time (`DateField`, `CalendarPopup`).

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP, with the windows off screen.

## `python/mytool/ui/forms.py`

```python
"""Form building blocks shared by every page of the tool: rounded panels with a title, a red * for what is required
and a "?" help balloon; captions above fields; collapsible groups that look like panels; a dropdown whose items are
coloured badges.

Panels and collapsible groups share one inset, so a panel's title, a group's arrow and the fields below both start at
the same x.
"""

import math
import re

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal
from ..ui_scale import px, space
from . import controls


def scroll_page(widget, theme=None, role="window"):
    """A page that scrolls vertically when the window is shorter than its panels (never sideways). With `theme` its
    clipped top and bottom edges fade out (controls.EdgeFade) into `role`, the colour behind it."""
    area = QtWidgets.QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QtWidgets.QFrame.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    area.setWidget(widget)
    if theme is not None:
        controls.fade_edges(area, theme, role)
    return area


def required_mark():
    """The red * after the name of something that must be filled in (theme colour log_error, tooltip "Required")."""
    star = QtWidgets.QLabel("*")
    star.setObjectName("toolRequired")
    star.setToolTip("Required")
    return star


def panel(title, theme, help_title=None, help_text=None, required=False):
    """A rounded panel with a section title (a red * when its content is required, and a "?" balloon when there is
    help). Returns (frame, content layout). The help text uses controls.help_html markup."""
    frame = QtWidgets.QFrame()
    frame.setObjectName("toolPanel")
    outer = QtWidgets.QVBoxLayout(frame)
    outer.setContentsMargins(space(12), space(6), space(12), space(8))
    outer.setSpacing(space(6))
    head = QtWidgets.QHBoxLayout()
    head.setSpacing(space(6))
    name = QtWidgets.QHBoxLayout()
    name.setSpacing(space(2))  # The * as close to the title as to a field's name
    name.addWidget(controls.section(title), 0, Qt.AlignVCenter)  # The "?" sits on the title's centre line
    if required:
        name.addWidget(required_mark(), 0, Qt.AlignVCenter)
    head.addLayout(name)
    if help_text:
        head.addWidget(controls.HelpButton(theme, help_title or title, help_text), 0, Qt.AlignVCenter)
    head.addStretch(1)
    outer.addLayout(head)
    return frame, outer


def caption(text, required=False):
    """The name above a field; a field that must be filled in gets a red * after it."""
    label = QtWidgets.QLabel(text)
    label.setObjectName("toolCaption")
    if not required:
        return label
    row = QtWidgets.QWidget()
    line = QtWidgets.QHBoxLayout(row)
    line.setContentsMargins(0, 0, 0, 0)
    line.setSpacing(space(2))
    line.addWidget(label)
    line.addWidget(required_mark())
    line.addStretch(1)
    return row


def labeled(text, widget, hint=None, required=False):
    """A caption above a widget or layout, and an optional muted hint below it. Returns a layout."""
    box = QtWidgets.QVBoxLayout()
    box.setSpacing(space(2))
    box.addWidget(caption(text, required))
    if isinstance(widget, QtWidgets.QWidget):
        box.addWidget(widget)
    else:
        box.addLayout(widget)
    if hint:
        box.addWidget(controls.muted(hint))
    return box


def field_with_button(edit, button):
    row = QtWidgets.QHBoxLayout()
    row.setSpacing(space(6))
    row.addWidget(edit, 1)
    row.addWidget(button)
    return row


# ---- Checks while typing ----------------------------------------------------------------------------------------
_HOST = re.compile(r"^(?:[A-Za-z0-9]{1}(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$|^localhost$")


def complete_url(text):
    """A site typed without its scheme gets https:// when the field is left: "3dground.net" -> "https://3dground.net".
    Anything else is returned unchanged (url_error then says what is wrong)."""
    text = (text or "").strip()
    if text and "://" not in text and " " not in text and "." in text.split("/")[0]:
        return "https://" + text
    return text


def url_error(text, required=False):
    """What is wrong with a web address, in a few words; "" when it is fine (or empty and not required). Checked on
    every edit, so the field shows its error at once."""
    text = (text or "").strip()
    if not text:
        return "Required" if required else ""
    if " " in text:
        return "A web address has no spaces"
    completed = complete_url(text)
    if completed != text:  # "site.com": fine while typing, https:// is added when the field is left
        text = completed
    match = re.match(r"^(https?)://([^/?#:]+)(?::\d{1,5})?(?:[/?#].*)?$", text, re.I)
    if not match:
        if "://" in text:
            return "Use an address that starts with https://"
        return "Not a web address: type it as https://3dground.net"
    if not _HOST.match(match.group(2)):
        return "The site name is not valid: {}".format(match.group(2))
    return ""


# ---- Collapsible groups ----------------------------------------------------------------------------------------
class GroupHeader(controls.Button):
    """The title of a Collapsible. It looks like the title of any other panel, not like a button: on hover only the
    colour of the text and the arrow changes (no background, no frame)."""

    GAP = 1  # Between the arrow's icon and the title; the arrow's picture adds about 6 px of air of its own

    def __init__(self, title, theme):
        controls.Button.__init__(self, title, theme, icon="chevron-right", variant="ghost", icon_role="heading_text")
        self.setObjectName("toolGroupHeader")
        self.setCursor(Qt.PointingHandCursor)

    def _tint(self, role):
        self.icon_role = role
        self._on_theme(self._theme.colors)

    def paintEvent(self, event):
        """The arrow, a small gap and the title, both centred on the button's height. No background or frame."""
        painter = QtGui.QPainter(self)
        size = self.iconSize()
        left = px(4)
        self.icon().paint(painter, QtCore.QRect(left, (self.height() - size.height()) // 2, size.width(), size.height()))
        painter.setFont(self.font())
        painter.setPen(QtGui.QColor(self._theme.colors[self.icon_role or "heading_text"]))
        title = QtCore.QRect(left + size.width() + px(self.GAP), 0, self.width(), self.height())
        painter.drawText(title, int(Qt.AlignVCenter | Qt.AlignLeft), self.text())
        painter.end()

    def enterEvent(self, event):
        self._tint("text")
        controls.Button.enterEvent(self, event)

    def leaveEvent(self, event):
        self._tint("heading_text")
        controls.Button.leaveEvent(self, event)


class Collapsible(QtWidgets.QFrame):
    """A titled group that opens and closes, drawn as a panel like every other group of the window. Put its widgets
    into `inner`. An optional group starts closed; open it (`header.setChecked(True)`) when it holds data."""

    toggled = Signal(bool)

    def __init__(self, title, theme, parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setObjectName("toolPanel")
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(space(6), space(4), space(12), space(4))  # Same room above and below: a closed group is centred
        lay.setSpacing(space(6))
        self.header = GroupHeader(title, theme)
        self.header.setCheckable(True)
        self.header.setFocusPolicy(Qt.NoFocus)
        self.header.toggled.connect(self.set_open)
        lay.addWidget(self.header, 0, Qt.AlignLeft)
        self.content = QtWidgets.QWidget()
        self.inner = QtWidgets.QVBoxLayout(self.content)
        self.inner.setContentsMargins(space(6), 0, 0, 0)  # 6 + 6: the content starts where a panel's content starts (12)
        self.inner.setSpacing(space(8))
        self.content.setVisible(False)
        lay.addWidget(self.content)

    def is_open(self):
        return self.header.isChecked()

    def set_open(self, on):
        if self.header.isChecked() != bool(on):
            self.header.setChecked(bool(on))  # Comes back here through `toggled`
            return
        self.content.setVisible(bool(on))
        self.header.icon_name = "chevron-down" if on else "chevron-right"
        self.header._on_theme(self.header._theme.colors)  # Re-tint the new icon
        self.toggled.emit(bool(on))


# ---- Badge dropdown --------------------------------------------------------------------------------------------
def _badge_font(base):
    font = QtGui.QFont(base)
    font.setBold(True)
    font.setPointSizeF(font.pointSizeF() * 0.85)
    return font


def badge_width(base, names):
    """Every badge is as wide as the longest name, so texts after the badges start in one column."""
    metrics = QtGui.QFontMetricsF(_badge_font(base))
    return max(metrics.horizontalAdvance(name) for name in names) + px(12)


def draw_badge(painter, left, center_y, name, role, colors, base, width):
    """A coloured capsule (fill `<role>_background`, text `<role>`) with its name in the middle, centred on the
    capital letters. `role` is a log colour role (log_success, log_warning, log_info, log_error, log_system,
    log_debug). Returns its rectangle."""
    font = _badge_font(base)
    metrics = QtGui.QFontMetricsF(font)
    height = metrics.capHeight() + px(9)
    badge = QtCore.QRectF(left, center_y - height / 2.0, width, height)
    painter.save()
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QtGui.QColor(colors[role + "_background"]))
    painter.drawRoundedRect(badge, height / 2.0, height / 2.0)
    painter.setFont(font)
    painter.setPen(QtGui.QColor(colors[role]))
    painter.drawText(QtCore.QPointF(math.floor(badge.center().x() - metrics.horizontalAdvance(name) / 2.0),
                                    round(badge.center().y() + metrics.capHeight() / 2.0)), name)
    painter.restore()
    return badge


class BadgeDelegate(QtWidgets.QStyledItemDelegate):
    """The rows of a BadgeComboBox's list: each item's badge, as it looks in the closed field."""

    def __init__(self, theme, combo):
        QtWidgets.QStyledItemDelegate.__init__(self, combo)
        self.theme = theme
        self.combo = combo

    def sizeHint(self, option, index):
        return QtCore.QSize(int(self.combo.badge_width(option.font)) + px(18), option.fontMetrics.height() + px(12))

    def paint(self, painter, option, index):
        colors = self.theme.colors
        rect = QtCore.QRectF(option.rect).adjusted(px(3), px(1), -px(3), -px(1))
        if option.state & (QtWidgets.QStyle.State_Selected | QtWidgets.QStyle.State_MouseOver):
            painter.save()
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QColor(colors["hover"]))
            painter.drawRoundedRect(rect, px(5), px(5))
            painter.restore()
        name = index.data(Qt.UserRole)
        draw_badge(painter, rect.left() + px(6), rect.center().y(), name, self.combo.role(name), colors, option.font,
                   self.combo.badge_width(option.font))


class BadgeComboBox(controls.ComboBox):
    """A dropdown that shows its value as a coloured badge, closed and open. `badges`: ((name, log role), ...),
    for example (("Added", "log_success"), ("Fixed", "log_warning")). Sized to its content: exactly the badge, a small
    gap and the arrow; the open list takes the same width."""

    def __init__(self, theme, badges, parent=None):
        controls.ComboBox.__init__(self, parent)
        self.theme = theme
        self._roles = dict(badges)
        self._names = tuple(name for name, _role in badges)
        for name in self._names:
            self.addItem(name, name)
        self.view().setItemDelegate(BadgeDelegate(theme, self))
        self.fit_width()

    def role(self, name):
        return self._roles.get(name, "log_info")

    def badge_width(self, base):
        return badge_width(base, self._names)

    def fit_width(self):
        """The badge plus the style sheet's 8 px left and 26 px right padding and 1 px borders."""
        self.setFixedWidth(int(self.badge_width(self.font())) + px(40))

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.FontChange:  # The window's interface-size font arrives after construction
            self.fit_width()
        controls.ComboBox.changeEvent(self, event)

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = ""  # The badge takes the place of the text
        painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, option)
        field = self.style().subControlRect(QtWidgets.QStyle.CC_ComboBox, option,
                                            QtWidgets.QStyle.SC_ComboBoxEditField, self)
        name = self.currentData()
        if name:
            draw_badge(painter, field.left() + px(2), QtCore.QRectF(field).center().y(), name, self.role(name),
                       self.theme.colors, self.font(), self.badge_width(self.font()))
```

## `python/mytool/ui/switch.py`

```python
"""A toggle switch in the tool's look: a rounded track, a sliding knob and the label to its right.

It replaces check boxes everywhere. It behaves like a check box (`toggled`, `isChecked`, `setChecked`, `setEnabled`).
"""

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt
from ..ui_scale import px
from .controls import Themed


def _mix(first, second, amount):
    return QtGui.QColor(int(first.red() + (second.red() - first.red()) * amount),
                        int(first.green() + (second.green() - first.green()) * amount),
                        int(first.blue() + (second.blue() - first.blue()) * amount))


class Switch(QtWidgets.QAbstractButton, Themed):
    TRACK_W, TRACK_H, GAP = 32, 18, 9  # Logical pixels at 100 %

    def __init__(self, theme, text="", parent=None):
        QtWidgets.QAbstractButton.__init__(self, parent)
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self._position = 0.0  # 0 = off (knob left), 1 = on (knob right)
        self._animation = QtCore.QVariantAnimation(self)
        self._animation.setDuration(120)
        self._animation.valueChanged.connect(self._move)
        self.toggled.connect(self._slide)
        self._colors = theme.colors
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def setChecked(self, checked):
        QtWidgets.QAbstractButton.setChecked(self, checked)
        self._animation.stop()
        self._position = 1.0 if self.isChecked() else 0.0  # No animation for programmatic changes
        self.update()

    def _slide(self, checked):
        self._animation.stop()
        self._animation.setStartValue(self._position)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def _move(self, value):
        self._position = float(value)
        self.update()

    def sizeHint(self):
        text = self.text()
        width = px(self.TRACK_W) + (px(self.GAP) + self.fontMetrics().horizontalAdvance(text) if text else 0)
        return QtCore.QSize(width + px(2), max(px(self.TRACK_H), self.fontMetrics().height()) + px(6))

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, event):
        colors = self._colors
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        enabled = self.isEnabled()
        track_w, track_h = px(self.TRACK_W), px(self.TRACK_H)
        top = (self.height() - track_h) / 2.0
        track = QtCore.QRectF(1, top, track_w, track_h)
        off_fill, on_fill = QtGui.QColor(colors["recessed"]), QtGui.QColor(colors["accent"])
        if not enabled:
            off_fill = on_fill = QtGui.QColor(colors["disabled_surface"])
            border = QtGui.QColor(colors["disabled_border"])
        elif self.hasFocus():
            border = QtGui.QColor(colors["focus"])
        elif self.underMouse():
            border = QtGui.QColor(colors["active_border"])
        else:
            border = _mix(QtGui.QColor(colors["checkbox_border"]), on_fill, self._position)
        painter.setPen(QtGui.QPen(border, 1))
        painter.setBrush(_mix(off_fill, on_fill, self._position))
        painter.drawRoundedRect(track, track_h / 2.0, track_h / 2.0)
        margin = px(3)
        knob = track_h - 2 * margin
        x = track.left() + margin + (track_w - 2 * margin - knob) * self._position
        knob_color = QtGui.QColor(colors["disabled_text"] if not enabled else colors["muted_text"])
        if enabled:
            knob_color = _mix(knob_color, QtGui.QColor(colors["log_badge_text"]), self._position)
        painter.setPen(Qt.NoPen)
        painter.setBrush(knob_color)
        painter.drawEllipse(QtCore.QRectF(x, top + margin, knob, knob))
        if self.text():
            painter.setPen(QtGui.QColor(colors["text"] if enabled else colors["disabled_text"]))
            painter.setFont(self.font())
            area = QtCore.QRectF(track.right() + px(self.GAP), 0, self.width() - track.right() - px(self.GAP), self.height())
            painter.drawText(area, int(Qt.AlignVCenter | Qt.AlignLeft), self.text())
        painter.end()

    def enterEvent(self, event):
        self.update()
        QtWidgets.QAbstractButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.update()
        QtWidgets.QAbstractButton.leaveEvent(self, event)
```

## `python/mytool/ui/pickers.py`

```python
"""Shared pickers in the tool's own look: a number stepper, a time field, and a date field with a themed calendar.

* Stepper: a whole number with stacked arrows; `pad` shows leading zeros ("05"), `wrap` turns 59 into 0 and back.
* TimeEdit: hours and minutes as two wrapping steppers ("14 : 30").
* DateField / CalendarPopup: a field that opens a month calendar. The title ("November 2026") is a button: it switches
  to the twelve months of the year, and from there to twelve years, so a date years away is three clicks off, never
  dozens of arrow clicks. The arrows and the wheel step a month, a year or twelve years, by the view. The keys work
  as in Windows' own calendar: arrows move the day, Page Up / Down the month (with Shift the year), Home goes to
  today, Enter picks, Esc steps back a view and then closes. `with_time=True` adds the time under the days: a click
  on a day then only selects it, and Done (or Enter) applies the date and the time together. `set_range` greys out
  the days, months and years outside it.

They are built from the shared Button and the style sheet rules in style.qss (rounded fields, accent for the
selection), so they sit next to the other controls without looking different.
"""

from ..qt_compat import (QtCore, QtGui, QtWidgets, Qt, Signal, inherit_fonts, own_keyboard, repolish, scale_font,
                         work_area)
from ..ui_scale import px, space
from . import controls
from .controls import Button, round_popup


class Stepper(QtWidgets.QFrame):
    """A whole-number field in one rounded frame: the value, and small up / down arrows stacked at the right edge.
    The arrow keys step it too; the wheel does not (it scrolls the page)."""

    valueChanged = Signal(int)

    def __init__(self, theme, minimum=0, maximum=999, value=0, parent=None, pad=0, wrap=False):
        QtWidgets.QFrame.__init__(self, parent)
        self.setObjectName("toolStepper")
        self._minimum, self._maximum, self._value = minimum, maximum, value
        self._pad, self._wrap = pad, wrap
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, space(2), 0)
        layout.setSpacing(0)
        self.edit = QtWidgets.QLineEdit(str(value).zfill(pad))
        self.edit.setObjectName("toolStepValue")
        self.edit.setAlignment(Qt.AlignCenter)
        self.edit.setFixedWidth(px(40))
        self.edit.setValidator(QtGui.QIntValidator(minimum, maximum, self))
        self.edit.editingFinished.connect(self._from_text)
        self.edit.installEventFilter(self)
        arrows = QtWidgets.QVBoxLayout()
        arrows.setContentsMargins(0, space(2), 0, space(2))
        arrows.setSpacing(0)
        self.up = Button("", theme, icon="chevron-up", tooltip="Increase")
        self.down = Button("", theme, icon="chevron-down", tooltip="Decrease")
        for button, delta in ((self.up, 1), (self.down, -1)):
            button.setObjectName("toolStepArrow")
            button.icon_px = 10
            button._on_theme(theme.colors)
            button.setFocusPolicy(Qt.NoFocus)
            button.setAutoRepeat(True)
            button.clicked.connect(lambda _=False, d=delta: self.step(d))
            arrows.addWidget(button)
        layout.addWidget(self.edit)
        layout.addLayout(arrows)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def value(self):
        return self._value

    def setValue(self, value):
        value = max(self._minimum, min(self._maximum, int(value)))
        self.edit.setText(str(value).zfill(self._pad))
        if value != self._value:
            self._value = value
            self.valueChanged.emit(value)

    def step(self, delta):
        value = self._value + delta
        if self._wrap:  # 59 + 1 is 0, 0 - 1 is 59
            value = self._minimum + (value - self._minimum) % (self._maximum - self._minimum + 1)
        self.setValue(value)

    def _from_text(self):
        try:
            self.setValue(int(self.edit.text()))
        except ValueError:
            self.edit.setText(str(self._value))

    def eventFilter(self, watched, event):
        if watched is self.edit:
            kind = event.type()
            if kind in (QtCore.QEvent.FocusIn, QtCore.QEvent.FocusOut):
                self.setProperty("focused", kind == QtCore.QEvent.FocusIn)
                repolish(self)
            elif kind == QtCore.QEvent.KeyPress and event.key() in (Qt.Key_Up, Qt.Key_Down):
                self.step(1 if event.key() == Qt.Key_Up else -1)
                return True
            # The wheel is left to the page: scrolling never changes the number
        return QtWidgets.QFrame.eventFilter(self, watched, event)


class TimeEdit(QtWidgets.QWidget):
    """Hours and minutes: two wrapping steppers with leading zeros and a colon between them. The arrow keys and the
    small arrows step them; typing a number works too."""

    changed = Signal(object)  # QTime

    def __init__(self, theme, time=None, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        time = QtCore.QTime(time) if time is not None else QtCore.QTime.currentTime()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(space(4))
        self.hours = Stepper(theme, 0, 23, time.hour(), pad=2, wrap=True)
        self.minutes = Stepper(theme, 0, 59, time.minute(), pad=2, wrap=True)
        self.hours.setToolTip("Hours")
        self.minutes.setToolTip("Minutes")
        colon = QtWidgets.QLabel(":")
        colon.setObjectName("toolTimeColon")
        layout.addWidget(self.hours)
        layout.addWidget(colon)
        layout.addWidget(self.minutes)
        self.hours.valueChanged.connect(lambda _value: self.changed.emit(self.time()))
        self.minutes.valueChanged.connect(lambda _value: self.changed.emit(self.time()))
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def time(self):
        return QtCore.QTime(self.hours.value(), self.minutes.value())

    def setTime(self, time):
        self.hours.setValue(time.hour())
        self.minutes.setValue(time.minute())


MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December")
WEEKDAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")


def _cell_state(button, state):
    """A calendar cell's look (selected, today, other month) through its style sheet property."""
    if button.property("state") != state:
        button.setProperty("state", state)
        repolish(button)


class CalendarPopup(QtWidgets.QWidget):
    """See the module. Three views in one frame: the days of a month, the months of a year, twelve years."""

    picked = Signal(object)  # QDate, or QDateTime with_time

    DAYS, MONTHS, YEARS = 0, 1, 2
    YEARS_SHOWN = 12

    def __init__(self, theme, parent, with_time=False):
        QtWidgets.QWidget.__init__(self, parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("toolCalendar")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.with_time = with_time
        self.minimum = self.maximum = None
        self._month = QtCore.QDate.currentDate()  # Any day of the month, year or years shown
        self._selected = QtCore.QDate.currentDate()
        self._view = self.DAYS
        self._dates = []
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame = QtWidgets.QFrame()
        frame.setObjectName("toolCalendarFrame")
        outer.addWidget(frame)
        body = QtWidgets.QVBoxLayout(frame)
        body.setContentsMargins(space(8), space(8), space(8), space(8))
        body.setSpacing(space(8))
        head = QtWidgets.QHBoxLayout()
        head.setSpacing(space(4))
        self.previous = Button("", theme, icon="chevron-left", variant="ghost", tooltip="Previous month")
        self.following = Button("", theme, icon="chevron-right", variant="ghost", tooltip="Next month")
        self.previous.clicked.connect(lambda: self.step(-1))
        self.following.clicked.connect(lambda: self.step(1))
        self.title = Button("", theme, variant="ghost", tooltip="Choose a month and a year")
        self.title.setObjectName("toolCalendarTitle")
        self.title.clicked.connect(self.zoom_out)
        head.addWidget(self.previous)
        head.addWidget(self.title, 1)
        head.addWidget(self.following)
        body.addLayout(head)
        self.views = QtWidgets.QStackedWidget()
        body.addWidget(self.views)

        days = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(days)
        grid.setSpacing(space(2))
        grid.setContentsMargins(0, 0, 0, 0)
        for column, name in enumerate(WEEKDAYS):
            label = QtWidgets.QLabel(name)
            label.setObjectName("toolCalendarWeekday")
            label.setAlignment(Qt.AlignCenter)
            grid.addWidget(label, 0, column)
        self.days = []
        for index in range(42):
            button = self._cell("toolDay", lambda _=False, i=index: self._pick_day(i))
            grid.addWidget(button, 1 + index // 7, index % 7)
            self.days.append(button)
        self.views.addWidget(days)

        self.months = self._cell_grid(12, 3, self._pick_month)
        self.years = self._cell_grid(self.YEARS_SHOWN, 3, self._pick_year)

        self.time = None
        if with_time:
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(space(8))
            caption = QtWidgets.QLabel("Time")
            caption.setObjectName("toolMuted")
            self.time = TimeEdit(theme)
            now = Button("Now", theme, icon="clock", variant="ghost", tooltip="Today and the current time")
            now.clicked.connect(self._now)
            row.addWidget(caption)
            row.addWidget(self.time)
            row.addStretch(1)
            row.addWidget(now)
            body.addLayout(row)
        foot = QtWidgets.QHBoxLayout()
        foot.setSpacing(space(8))
        self.today_button = Button("Today", theme, icon="calendar", variant="ghost", tooltip="Go to today (Home)")
        self.today_button.clicked.connect(self._today)
        self.done = None
        if with_time:
            foot.addWidget(self.today_button)
            foot.addStretch(1)
            self.done = Button("Done", theme, icon="check", variant="primary", tooltip="Apply the date and time (Enter)")
            self.done.clicked.connect(self.apply)
            foot.addWidget(self.done)
        else:
            foot.addStretch(1)
            foot.addWidget(self.today_button)
            foot.addStretch(1)
        body.addLayout(foot)

    def _cell(self, name, slot):
        button = QtWidgets.QPushButton("")
        button.setObjectName(name)
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)
        button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        button.clicked.connect(slot)
        return button

    def _cell_grid(self, count, columns, pick):
        page = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(page)
        grid.setSpacing(space(4))
        grid.setContentsMargins(0, 0, 0, 0)
        cells = []
        for index in range(count):
            button = self._cell("toolCalendarCell", lambda _=False, i=index: pick(i))
            grid.addWidget(button, index // columns, index % columns)
            cells.append(button)
        grid.setRowStretch(count // columns, 1)
        self.views.addWidget(page)
        return cells

    # The range -------------------------------------------------------------------------------------------------------
    def set_range(self, minimum=None, maximum=None):
        self.minimum = QtCore.QDate(minimum) if minimum is not None else None
        self.maximum = QtCore.QDate(maximum) if maximum is not None else None
        self._fill()

    def _allowed(self, first, last):
        """Whether any day from `first` to `last` is inside the range."""
        return not ((self.minimum is not None and last < self.minimum) or
                    (self.maximum is not None and first > self.maximum))

    def _clamp(self, date):
        if self.minimum is not None and date < self.minimum:
            return QtCore.QDate(self.minimum)
        if self.maximum is not None and date > self.maximum:
            return QtCore.QDate(self.maximum)
        return date

    # Views ------------------------------------------------------------------------------------------------------------
    def view(self):
        return self._view

    def set_view(self, view):
        self._view = view
        self.views.setCurrentIndex(view)
        self._fill()

    def zoom_out(self):
        """Days -> the months of the year -> twelve years."""
        if self._view < self.YEARS:
            self.set_view(self._view + 1)

    def step(self, delta):
        """The arrows and the wheel: a month, a year or twelve years, by the view."""
        if self._view == self.DAYS:
            self._month = self._month.addMonths(delta)
        elif self._view == self.MONTHS:
            self._month = self._month.addYears(delta)
        else:
            self._month = self._month.addYears(delta * self.YEARS_SHOWN)
        self._fill()

    def move_month(self, delta):
        self._month = self._month.addMonths(delta)
        self._fill()

    def wheelEvent(self, event):
        self.step(-1 if event.angleDelta().y() > 0 else 1)

    def _first_year(self):
        return self._month.year() - 4  # The shown year in the second row, a few years back and ahead around it

    def _fill(self):
        today = QtCore.QDate.currentDate()
        year = self._month.year()
        tips = {self.DAYS: ("Previous month", "Next month"), self.MONTHS: ("Previous year", "Next year"),
                self.YEARS: ("Previous years", "Next years")}[self._view]
        self.previous.setToolTip(tips[0])
        self.following.setToolTip(tips[1])
        self.title.setEnabled(self._view < self.YEARS)
        if self._view == self.DAYS:
            first = QtCore.QDate(year, self._month.month(), 1)
            start = first.addDays(-(first.dayOfWeek() - 1))
            self.title.setText("{} {}".format(MONTH_NAMES[first.month() - 1], year))
            self._dates = []
            for index, button in enumerate(self.days):
                date = start.addDays(index)
                self._dates.append(date)
                button.setText(str(date.day()))
                button.setEnabled(self._allowed(date, date))
                if date == self._selected:
                    state = "selected"
                elif date == today:
                    state = "today"
                elif date.month() != first.month():
                    state = "other"
                else:
                    state = ""
                _cell_state(button, state)
        elif self._view == self.MONTHS:
            self.title.setText(str(year))
            for index, button in enumerate(self.months):
                first = QtCore.QDate(year, index + 1, 1)
                button.setText(MONTH_NAMES[index][:3])
                controls.set_tip(button, "{} {}".format(MONTH_NAMES[index], year))
                button.setEnabled(self._allowed(first, first.addMonths(1).addDays(-1)))
                if (year, index + 1) == (self._selected.year(), self._selected.month()):
                    state = "selected"
                elif (year, index + 1) == (today.year(), today.month()):
                    state = "today"
                else:
                    state = ""
                _cell_state(button, state)
        else:
            first_year = self._first_year()
            self.title.setText("{} \u2013 {}".format(first_year, first_year + self.YEARS_SHOWN - 1))
            for index, button in enumerate(self.years):
                shown = first_year + index
                button.setText(str(shown))
                button.setEnabled(self._allowed(QtCore.QDate(shown, 1, 1), QtCore.QDate(shown, 12, 31)))
                if shown == self._selected.year():
                    state = "selected"
                elif shown == today.year():
                    state = "today"
                else:
                    state = ""
                _cell_state(button, state)

    # Picking ----------------------------------------------------------------------------------------------------------
    def selected(self):
        return QtCore.QDate(self._selected)

    def _select(self, date):
        date = self._clamp(date)
        self._selected = QtCore.QDate(date)
        self._month = QtCore.QDate(date)
        self._fill()

    def _pick_day(self, index):
        date = self._dates[index]
        if self.with_time:
            self._select(date)  # With a time to set, a click selects; Done applies
            return
        self.picked.emit(date)
        self.close()

    def _pick_month(self, index):
        self._month = QtCore.QDate(self._month.year(), index + 1, 1)
        self.set_view(self.DAYS)

    def _pick_year(self, index):
        self._month = QtCore.QDate(self._first_year() + index, self._month.month(), 1)
        self.set_view(self.MONTHS)

    def apply(self):
        """Done / Enter: the selected day (and the time) to the field."""
        if self.with_time:
            self.picked.emit(QtCore.QDateTime(self._selected, self.time.time()))
        else:
            self.picked.emit(QtCore.QDate(self._selected))
        self.close()

    def _today(self):
        today = self._clamp(QtCore.QDate.currentDate())
        if self.with_time:
            self._select(today)
            self.set_view(self.DAYS)
            return
        self.picked.emit(today)
        self.close()

    def _now(self):
        self.time.setTime(QtCore.QTime.currentTime())
        self._today()

    def keyPressEvent(self, event):
        key, shift = event.key(), bool(event.modifiers() & Qt.ShiftModifier)
        if key == Qt.Key_Escape:
            if self._view != self.DAYS:
                self.set_view(self._view - 1)  # Back to the days first; Esc again closes
            else:
                self.close()
            return
        if self._view != self.DAYS:
            if key in (Qt.Key_Left, Qt.Key_Up, Qt.Key_PageUp):
                self.step(-1)
            elif key in (Qt.Key_Right, Qt.Key_Down, Qt.Key_PageDown):
                self.step(1)
            return
        moves = {Qt.Key_Left: -1, Qt.Key_Right: 1, Qt.Key_Up: -7, Qt.Key_Down: 7}
        if key in moves:
            self._select(self._selected.addDays(moves[key]))
        elif key in (Qt.Key_PageUp, Qt.Key_PageDown):
            sign = -1 if key == Qt.Key_PageUp else 1
            self._select(self._selected.addYears(sign) if shift else self._selected.addMonths(sign))
        elif key == Qt.Key_Home:
            self._select(QtCore.QDate.currentDate())
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self.apply()
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)

    def show_for(self, field, value):
        date = value.date() if isinstance(value, QtCore.QDateTime) else value
        self._selected = QtCore.QDate(date)
        self._month = QtCore.QDate(date)
        if self.time is not None and isinstance(value, QtCore.QDateTime):
            self.time.setTime(value.time())
        self._view = self.DAYS
        self.views.setCurrentIndex(self.DAYS)
        self._fill()
        scale_font(self)
        inherit_fonts(self)
        for child in [self] + self.findChildren(QtWidgets.QWidget):
            child.ensurePolished()  # The style sheet's sizes land at polish: level the heights after it
        controls.unify_heights(self)  # The buttons and the time steppers: the tool's one control height
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
        self.setFocus(Qt.PopupFocusReason)  # The keys work at once
        own_keyboard([self] + self.findChildren(QtWidgets.QWidget))  # Esc and the arrows reach it, not 3ds Max
        round_popup(self, 8)  # The frame's own radius; corners are cut by a mask, not a translucent window


class DateField(Button):
    """A field showing a date (2026-11-11) or a date and a time (2026-11-11  14:30); clicking it opens the calendar.
    `changed` sends a QDate, or a QDateTime with_time."""

    changed = Signal(object)

    def __init__(self, theme, date=None, parent=None, with_time=False):
        Button.__init__(self, "", theme, icon="calendar-clock" if with_time else "calendar", variant="field",
                        parent=parent)
        self.with_time = with_time
        now = QtCore.QDateTime.currentDateTime()
        if date is None:
            date = now
        if isinstance(date, QtCore.QDateTime):
            self._value = QtCore.QDateTime(date)
        else:
            self._value = QtCore.QDateTime(QtCore.QDate(date), now.time())
        if not with_time:
            self._value.setTime(QtCore.QTime(0, 0))
        else:  # Whole minutes
            self._value.setTime(QtCore.QTime(self._value.time().hour(), self._value.time().minute()))
        self._popup = None
        self.minimum = self.maximum = None
        self.clicked.connect(self._open)
        self._sync()

    def date(self):
        return self._value.date()

    def setDate(self, date):
        self._value.setDate(QtCore.QDate(date))
        self._sync()

    def date_time(self):
        return QtCore.QDateTime(self._value)

    def set_date_time(self, value):
        self._value = QtCore.QDateTime(value)
        self._sync()

    def set_range(self, minimum=None, maximum=None):
        self.minimum, self.maximum = minimum, maximum
        if self._popup is not None:
            self._popup.set_range(minimum, maximum)

    def _sync(self):
        self.setText(self._value.toString("yyyy-MM-dd  HH:mm" if self.with_time else "yyyy-MM-dd"))

    def _open(self):
        if self._popup is None:
            self._popup = CalendarPopup(self._theme, self, self.with_time)
            self._popup.set_range(self.minimum, self.maximum)
            self._popup.picked.connect(self._picked)
        self._popup.show_for(self, self._value if self.with_time else self._value.date())

    def _picked(self, value):
        new = QtCore.QDateTime(value) if isinstance(value, QtCore.QDateTime) else QtCore.QDateTime(value, QtCore.QTime(0, 0))
        if new != self._value:
            self._value = new
            self._sync()
            self.changed.emit(QtCore.QDateTime(new) if self.with_time else new.date())
```
