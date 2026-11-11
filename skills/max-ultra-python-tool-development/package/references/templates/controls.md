# Template: Shared controls

Lucide icon rendering and the brand icon; one height for every field, dropdown and button (`unify_heights`); themed buttons with variants (a disabled coloured button keeps a shade of its colour) and the round title-bar buttons (`WindowButton`); rounded popups (`round_popup`) and menus with Lucide icons, keys at the right, arrow-key navigation and red destructive items that take the red Delete fill as the current row (`Menu`, `MenuItem`); text fields' own menus in the same look (`text_menus`, `round_menu`); style properties applied at once (`set_style_property`); field frames for lists and text boxes (`boxed`); the step number (`NumberBadge`); the red error bubble that waits for real pointer movement (`ErrorTip`, `ErrorHints`); pills, the progress bar, the segmented control, the dropdown with a rounded list that the wheel changes only after a click; the View Logs status action
(`StatusAction`) and the field highlight after a jump (`Flash`); a flow layout; help balloons with markup (`help_html`, `Balloon`, `HelpButton`); completer rows, shimmer, marquee and the eliding label. Form helpers, switches and pickers are on the [forms](forms.md) page. `ui/toast.py` holds the toasts as MaxPkg Runtime
Manager shows them: animated status icons, a time bar, optional actions, stacked below the header
(`ToolWindow.notify`).

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP, with the windows off screen.

## `python/mytool/ui/controls.py`

```python
"""Shared controls. Every dialog composes these; none re-implements their painting or behavior."""

import html
import math
import re
import time

from ..qt_compat import (QtCore, QtGui, QtSvg, QtWidgets, Qt, Signal, device_pixel_ratio, inherit_fonts, own_keyboard,
                         repolish, work_area)
from ..ui_scale import pt, px, space
from .theme_manager import tinted_svg


_icon_cache = {}
_URL = re.compile(r"(?:https?://|www\.)[^\s,;)]+[^\s,;.)]")
_WORD_JOINER = "\u2060"  # Zero width, forbids a line break between the characters it joins


def keep_urls_whole(text):
    """Web addresses never break across lines (Qt would break after "/" or "."): a wrap moves the whole address to
    the next line. For text shown with word wrap; copy the original text, not this."""
    return _URL.sub(lambda match: _WORD_JOINER.join(match.group(0)), text or "")


_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
PARAGRAPH_GAP = 7  # Logical px between the blocks of a help text
LINE_HEIGHT = 120  # Percent: wrapped lines of a help text get air between them


def _plain_html(text, colors):
    text = html.escape(keep_urls_whole(text), quote=False)
    return _BOLD.sub(lambda match: '<b style="color:{}">{}</b>'.format(colors["heading_text"], match.group(1)), text)


def _inline_html(text, colors):
    """**bold** and [label](https://...) in text without code; the address itself never gets the word joiners."""
    result, last = "", 0
    for match in _LINK.finditer(text):
        result += _plain_html(text[last:match.start()], colors)
        result += '<a href="{}" style="color:{}; text-decoration:none">{}</a>'.format(
            html.escape(match.group(2)), colors["link"], _plain_html(match.group(1), colors))
        last = match.end()
    return result + _plain_html(text[last:], colors)


def help_html(text, colors, text_role="tooltip_text"):
    """Help text with a little markup, as rich text that is quick to scan: blocks split by a blank line get room
    between them, **term** is bold, `code` (file names, characters) is a small monospaced chip, [label](https://...) is
    a link, a single line break stays a line break."""
    blocks = [block.strip() for block in re.split(r"\n\s*\n", (text or "").strip()) if block.strip()]
    result = []
    for index, block in enumerate(blocks):
        body = ""
        for number, piece in enumerate(_CODE.split(block)):  # Odd pieces are code
            if number % 2:  # A chip never breaks inside (StartMyTool.ms stays on one line)
                body += ('<span style="font-family:Consolas,\'Courier New\'; background-color:{}; color:{}">'
                         '&nbsp;{}&nbsp;</span>').format(colors["field"], colors["heading_text"],
                                                          html.escape(_WORD_JOINER.join(piece), quote=False))
            else:
                body += _inline_html(piece, colors)
        result.append('<p style="margin-top:{}px; margin-bottom:0px; line-height:{}%; color:{}">{}</p>'.format(
            0 if index == 0 else px(PARAGRAPH_GAP), LINE_HEIGHT, colors[text_role], body.replace("\n", "<br>")))
    return "".join(result)


CONTROL_HEIGHT = 30  # One height (logical px) for every single-line control: fields, dropdowns, buttons, steppers.
FOOTER_WIDTH = 92  # The least width (logical px) of the buttons of a dialog's bottom row (same_width).
# Parts and small special buttons that keep their own size.
_OWN_SIZE = {"toolMenuItem", "toolDay", "toolCalendarCell", "toolStepArrow", "toolStepValue", "toolIconButton", "toolFieldButton", "toolFieldClear",
             "toolSmallAction", "toolChevron", "toolMiniTitle", "toolSoftButton", "toolStatusAction", "toolToastClose",
             "toolNavButton", "toolThumb"}


class _BoxFocus(QtCore.QObject):
    """Outlines a box in the focus colour while the field inside it has the keyboard focus."""

    def __init__(self, box):
        QtCore.QObject.__init__(self, box)
        self.box = box

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.FocusIn, QtCore.QEvent.FocusOut):
            self.box.setProperty("focused", event.type() == QtCore.QEvent.FocusIn)
            repolish(self.box)
        return False


def boxed(inner, margin=1):
    """A list or multi-line text box inside a rounded field frame.

    In the tool's frameless window inside 3ds Max, Qt does not paint the style sheet border of scroll areas (lists,
    text boxes), while plain frames are painted. The frame therefore draws the field's border, focus and invalid
    outline; the widget inside has none. `margin` 0 puts the widget right against the border (rows highlighted from
    edge to edge)."""
    box = QtWidgets.QFrame()
    box.setObjectName("toolBox")
    layout = QtWidgets.QVBoxLayout(box)
    layout.setContentsMargins(px(margin), px(margin), px(margin), px(margin))  # Not spacing: the frame's 1 px border
    layout.setSpacing(0)
    inner.setFrameShape(QtWidgets.QFrame.NoFrame)
    layout.addWidget(inner)
    box.setFocusProxy(inner)
    inner.installEventFilter(_BoxFocus(box))
    return box


def round_popup(widget, radius=6):
    """Rounded corners for a popup window by a window mask (no translucent windows inside 3ds Max)."""
    path = QtGui.QPainterPath()
    path.addRoundedRect(QtCore.QRectF(widget.rect()), px(radius), px(radius))
    widget.setMask(QtGui.QRegion(path.toFillPolygon().toPolygon()))


def paint_bubble(painter, shape, fill, border, width=1.0):
    """Fills a masked popup's shape (a bubble with its arrow) and outlines it on the whole perimeter. The outline is
    drawn twice as wide and clipped to the shape, so it runs along the inside: a stroke centred on the edge loses its
    outer half to the window mask (and to the widget's right and bottom edges), and the bubble looks open there."""
    painter.save()
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setClipPath(shape)
    painter.fillPath(shape, QtGui.QColor(fill))
    pen = QtGui.QPen(QtGui.QColor(border), 2.0 * width)
    pen.setJoinStyle(Qt.MiterJoin)  # The arrow's point keeps its outline too
    painter.strokePath(shape, pen)
    painter.restore()


def set_style_property(widget, name, value):
    """Set a property that a style sheet rule matches on (current, done, picking) and apply the rule now: Qt reads
    the rules again only when the widget is polished. The widget keeps its interface-size font."""
    if widget.property(name) == value:
        return
    font = widget.font()
    widget.setProperty(name, value)
    repolish(widget)
    widget.setFont(font)
    widget.update()


class Menu(QtWidgets.QMenu):
    """A context or button menu with rounded corners like every other popup of the tool (see MenuItem for the rows).
    The arrow keys move the current row over the enabled rows, Enter or Space runs it, Esc closes the menu."""

    def __init__(self, theme, parent=None):
        QtWidgets.QMenu.__init__(self, parent)
        self.theme = theme
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        if parent is not None:
            self.setFont(parent.window().font())  # A popup does not inherit its window's interface-size font

    def add_item(self, text, icon, slot, danger=False, enabled=True, shortcut=""):
        """`shortcut`: the key that does the same outside the menu ("Ctrl+C", "Del"), shown at the right. The menu
        only shows it; the window's own QShortcut does the work."""
        button = MenuItem(text, self.theme, icon, danger, shortcut)
        button.menu = self
        button.setEnabled(enabled)
        action = QtWidgets.QWidgetAction(self)
        action.setDefaultWidget(button)
        action.setEnabled(enabled)
        button.clicked.connect(lambda: (self.close(), slot()))
        self.addAction(action)
        return action

    def rows(self):
        return [action.defaultWidget() for action in self.actions() if isinstance(action, QtWidgets.QWidgetAction)
                and isinstance(action.defaultWidget(), MenuItem)]

    def current(self):
        return next((row for row in self.rows() if row.is_current()), None)

    def set_current(self, row):
        for item in self.rows():
            item.set_current(item is row)

    def keyPressEvent(self, event):
        rows = [row for row in self.rows() if row.isEnabled()]
        key = event.key()
        if rows and key in (Qt.Key_Down, Qt.Key_Up, Qt.Key_Home, Qt.Key_End):
            current = self.current()
            index = rows.index(current) if current in rows else -1
            if key == Qt.Key_Down:
                index = (index + 1) % len(rows)
            elif key == Qt.Key_Up:
                index = (index - 1) % len(rows) if index >= 0 else len(rows) - 1
            else:
                index = 0 if key == Qt.Key_Home else len(rows) - 1
            self.set_current(rows[index])
            return
        if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space) and self.current() is not None:
            self.current().click()
            return
        QtWidgets.QMenu.keyPressEvent(self, event)

    def showEvent(self, event):
        QtWidgets.QMenu.showEvent(self, event)
        round_popup(self)

    def resizeEvent(self, event):
        QtWidgets.QMenu.resizeEvent(self, event)
        round_popup(self)

    def fit_fonts(self):
        """The items keep the menu's interface-size font after their style sheet polish; before the menu is
        measured."""
        for child in [self] + self.findChildren(QtWidgets.QWidget):
            child.ensurePolished()
        inherit_fonts(self)

    def popup_at(self, point):
        self.fit_fonts()
        own_keyboard([self] + self.findChildren(QtWidgets.QWidget))  # Esc and the arrows reach the menu, not 3ds Max
        (getattr(self, "exec_", None) or getattr(self, "exec"))(point)


class _RoundMenu(QtCore.QObject):
    def eventFilter(self, menu, event):
        if event.type() in (QtCore.QEvent.Show, QtCore.QEvent.Resize):
            round_popup(menu)
        return False


def round_menu(menu, owner=None):
    """A menu that Qt builds itself (a text field's Undo / Cut / Copy / Paste / Select All) in the tool's look: no
    frame, no system shadow, rounded by a mask, the window's interface-size font; the style sheet colours it."""
    menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
    menu.installEventFilter(_RoundMenu(menu))
    if owner is not None:
        menu.setFont(owner.window().font())
    return menu


class _TextMenus(QtCore.QObject):
    """Opens a text field's standard menu through round_menu instead of Qt's square one."""

    def eventFilter(self, watched, event):
        if event.type() != QtCore.QEvent.ContextMenu:
            return False
        field = owner = watched
        parent = watched.parentWidget()
        if isinstance(parent, (QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit)) and watched is parent.viewport():
            field = owner = parent  # A text box gets the event on its viewport
        elif isinstance(watched, QtWidgets.QAbstractSpinBox):
            field = watched.findChild(QtWidgets.QLineEdit)  # A stepper or the date field: its own line edit's menu
        if field is None or owner.contextMenuPolicy() != Qt.DefaultContextMenu:
            return False
        menu = round_menu(field.createStandardContextMenu(), field)
        (getattr(menu, "exec_", None) or getattr(menu, "exec"))(event.globalPos())
        menu.deleteLater()
        return True


def text_menus(root):
    """Every text field, text box and stepper under `root` opens its right-click menu in the tool's look. Called by
    unify_heights, so new fields of a window get it too."""
    keeper = root.findChild(_TextMenus, "toolTextMenus")
    if keeper is None:
        keeper = _TextMenus(root)
        keeper.setObjectName("toolTextMenus")
    targets = root.findChildren(QtWidgets.QLineEdit) + root.findChildren(QtWidgets.QAbstractSpinBox)
    for box in root.findChildren(QtWidgets.QPlainTextEdit) + root.findChildren(QtWidgets.QTextEdit):
        targets.append(box.viewport())
    for widget in targets:
        if not widget.property("toolTextMenu"):
            widget.setProperty("toolTextMenu", True)
            widget.installEventFilter(keeper)


class _Tips(QtCore.QObject):
    """The widgets' tooltips in the tool's own rounded Tip. 3ds Max takes every widget's ToolTip event at the
    application level (it never reaches the widget), so the Tip follows the pointer itself: it opens 700 ms after the
    pointer enters a widget, at once while another tip has just closed (moving along a row of buttons), and goes when
    the pointer leaves, clicks, scrolls or types. The text lives in the widget's "toolTipText" property and Qt's own
    tooltip stays empty, so Max never shows its square tooltip over ours. It never touches Qt's tooltip window:
    rounding that window by a mask took 3ds Max 2022 down."""

    WAKE_MS = 700
    AWAKE_S = 0.4  # After a tip closed, the next one opens at once for this long
    HIDE_ON = (QtCore.QEvent.Leave, QtCore.QEvent.MouseButtonPress, QtCore.QEvent.Wheel, QtCore.QEvent.KeyPress,
               QtCore.QEvent.Hide)

    def __init__(self, root):
        QtCore.QObject.__init__(self, root)
        self.root = root
        self.tip = None
        self.pending = None
        self._closed_at = 0.0
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._wake)

    def show(self, widget, point, text):
        if self.tip is None:
            self.tip = Tip(_theme_of(widget), self.root)
        self.tip.show_text(point, text, widget)
        return self.tip

    def show_for(self, widget, point=None):
        """Show `widget`'s tip now, at `point` or under the widget (what the hover does after its delay)."""
        text = tip_text(widget)
        if not text:
            return None
        if point is None:
            point = widget.mapToGlobal(QtCore.QPoint(widget.width() // 2, widget.height() // 2))
        return self.show(widget, point, text)

    def hide(self, widget=None):
        if self.tip is not None and self.tip.isVisible() and (widget is None or self.tip.owner is widget):
            self.tip.hide()
            self._closed_at = time.monotonic()

    def _wake(self):
        widget, self.pending = self.pending, None
        if widget is None or not widget.isVisible():
            return
        point = QtGui.QCursor.pos()
        if widget.rect().contains(widget.mapFromGlobal(point)):  # Still under the pointer
            self.show_for(widget, point)

    def eventFilter(self, widget, event):
        kind = event.type()
        if kind == QtCore.QEvent.Enter and isinstance(widget, QtWidgets.QWidget) and tip_text(widget):
            self.pending = widget
            awake = time.monotonic() - self._closed_at < self.AWAKE_S or (self.tip is not None and
                                                                          self.tip.isVisible())
            self.timer.start(30 if awake else self.WAKE_MS)
        elif kind == QtCore.QEvent.ToolTip:
            return True  # Never Qt's square tooltip, when Max lets the event through
        elif kind in self.HIDE_ON:
            if self.pending is widget:
                self.timer.stop()
                self.pending = None
            self.hide(widget)
        return False


def tip_text(widget):
    """The text of `widget`'s tooltip in the tool's Tip ("" for none)."""
    return widget.property("toolTipText") or ""


def set_tip(widget, text):
    """Give `widget` a tooltip in the tool's Tip. Use it instead of setToolTip for a widget whose tooltip changes after
    its window is built (a swatch's colour, a calendar cell); the tool's buttons do it themselves through setToolTip.
    A widget not yet in a window gets its Tip when unify_heights reaches it."""
    widget.setProperty("toolTipText", text or "")
    QtWidgets.QWidget.setToolTip(widget, "")
    if text and not widget.accessibleDescription():
        widget.setAccessibleDescription(text)  # What a screen reader would have read from the tooltip
    if not widget.property("toolOwnTip") and widget.window() is not widget:
        widget.setProperty("toolOwnTip", True)
        widget.installEventFilter(tips_of(widget))


def _theme_of(widget):
    """The theme of the window `widget` sits in (every themed control keeps it as `_theme`)."""
    for candidate in (widget, widget.window()):
        theme = getattr(candidate, "_theme", None) or getattr(candidate, "theme", None) or getattr(
            getattr(candidate, "controller", None), "theme", None)
        if theme is not None and hasattr(theme, "colors"):
            return theme
    for child in widget.window().findChildren(QtWidgets.QWidget):
        theme = getattr(child, "_theme", None)
        if theme is not None and hasattr(theme, "colors"):
            return theme
    raise RuntimeError("No theme found for the tooltip")


def tips_of(widget):
    """The tooltip keeper of `widget`'s window (made on first use)."""
    root = widget.window()
    keeper = root.findChild(_Tips, "toolTips")
    if keeper is None:
        keeper = _Tips(root)
        keeper.setObjectName("toolTips")
    return keeper


def show_tip(widget, point, text):
    """Show `text` in the tool's Tip at the global `point` for `widget` (a chart's value under the pointer)."""
    return tips_of(widget).show(widget, point, text)


def hide_tip(widget):
    tips_of(widget).hide(widget)


def own_tooltips(root):
    """Every widget under `root` with a tooltip, and every button (buttons often get one later), shows it in the
    tool's Tip instead of Qt's: the text moves into the "toolTipText" property. Called by unify_heights, so widgets
    added later get it too."""
    tips_of(root)
    for widget in [root] + root.findChildren(QtWidgets.QWidget):
        if isinstance(widget, QTipLabel):
            continue
        text = QtWidgets.QWidget.toolTip(widget) or tip_text(widget)  # Qt's own text, or one set_tip kept
        if text:
            set_tip(widget, text)
        elif isinstance(widget, QtWidgets.QAbstractButton) and not widget.property("toolOwnTip"):
            widget.setProperty("toolOwnTip", True)
            widget.installEventFilter(tips_of(widget))


def same_width(*buttons):
    """Mark the buttons of one bottom row of a dialog (Donate and Close, Cancel and OK, Not now and Donate):
    unify_heights also gives them one width, the widest one's and at least FOOTER_WIDTH. A short "Close" beside an
    icon button ("Donate" with its heart) otherwise looks smaller although both are 30 px high. One button alone
    still gets FOOTER_WIDTH."""
    group = "w{}".format(id(buttons[0]))
    for button in buttons:
        button.setProperty("sameWidth", group)


def _match_widths(root):
    groups = {}
    for button in root.findChildren(QtWidgets.QPushButton):
        group = button.property("sameWidth")
        if group:
            groups.setdefault(group, []).append(button)
    for buttons in groups.values():
        width = max([px(FOOTER_WIDTH)] + [button.sizeHint().width() for button in buttons])
        for button in buttons:
            button.setMinimumWidth(width)


def unify_heights(root):
    """Give every field, dropdown and button under `root` the same height; a button without text becomes a square;
    the buttons marked with same_width get one width.

    One rule in one place: a button can never be taller than the field next to it. Call it after a window or dialog
    has built its widgets (and again after adding widgets later)."""
    _match_widths(root)
    height = px(CONTROL_HEIGHT)
    for widget in root.findChildren(QtWidgets.QWidget):
        name = widget.objectName()
        if name in _OWN_SIZE:
            continue
        if isinstance(widget, QtWidgets.QPushButton):
            widget.setFixedHeight(height)
            if not widget.text().strip() and widget.property("segment") is None:
                widget.setFixedWidth(height)  # Icon-only: a square
        elif isinstance(widget, (QtWidgets.QComboBox, QtWidgets.QLineEdit)):
            if isinstance(widget.parentWidget(), (QtWidgets.QAbstractSpinBox, QtWidgets.QComboBox)):
                continue  # The text part of a spin box or an editable dropdown: its frame has the height
            widget.setFixedHeight(height)
        elif name == "toolStepper":
            widget.setFixedHeight(height)
    text_menus(root)  # The fields' own right-click menus in the tool's look, for fields added later too
    own_tooltips(root)  # Tooltips in the tool's rounded Tip, as every popup


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


class NumberBadge(QtWidgets.QWidget, Themed):
    """A step number in a round accent outline. Painted here: the digits are centred on their own ink, so they sit
    exactly in the middle of the circle (a label centres the font's line box, which puts digits off centre)."""

    def __init__(self, number, theme, size=20, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._text = str(number)
        self.setFixedSize(px(size), px(size))
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        color = QtGui.QColor(self._colors["accent"])
        painter.setPen(QtGui.QPen(color, 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QtCore.QRectF(self.rect()).adjusted(0.6, 0.6, -0.6, -0.6))
        font = QtGui.QFont(self.font())
        font.setBold(True)
        font.setPointSizeF(pt(8))
        metrics = QtGui.QFontMetricsF(font)
        ink = metrics.tightBoundingRect(self._text)  # Relative to the baseline origin
        ratio = device_pixel_ratio(self) or 1.0
        # Across: by the advance width. Digits have one width and sit in the middle of it; the ink box differs
        # between Qt 5 and Qt 6 by a pixel. Down, never up: round() goes to the even pixel.
        x = math.floor((self.width() - metrics.horizontalAdvance(self._text)) / 2.0 * ratio) / ratio
        # Up and down: by the ink, so the digit's own height is centred
        y = round((self.height() / 2.0 - ink.top() - ink.height() / 2.0) * ratio) / ratio
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(QtCore.QPointF(x, y), self._text)
        painter.end()


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

    ICON_GAP = " "  # En space before the text of icon buttons.

    def setToolTip(self, text):
        if self.property("toolOwnTip"):  # The tool's Tip shows it (controls.own_tooltips), never Qt's square one
            set_tip(self, text)
        else:
            QtWidgets.QPushButton.setToolTip(self, text)

    def toolTip(self):
        return tip_text(self) or QtWidgets.QPushButton.toolTip(self)

    def setText(self, text):
        text = text.replace("&", "&&")  # A plain "&" ("Cards & Gallery"), never a hidden shortcut letter
        QtWidgets.QPushButton.setText(self, (self.ICON_GAP + text) if text and self.icon_name else text)

    def text(self):
        return QtWidgets.QPushButton.text(self).lstrip(self.ICON_GAP).replace("&&", "&")

    def _on_theme(self, colors):
        if self.icon_name:
            # Same colour as the variant's text in style.qss.
            role = self.icon_role or {"primary": "log_badge_text", "danger": "danger_text",
                                      "donate": "status_button_text"}.get(self.property("variant"), "text")
            local = dict(colors, text=colors[role])
            disabled = {"primary": "accent_disabled_text", "danger": "danger_disabled_text"}.get(
                self.property("variant"))
            if disabled:  # A coloured button keeps a shade of its colour when disabled, never a grey icon
                local["disabled_text"] = colors[disabled]
            self.setIcon(make_icon(self.icon_name, local, self))
            size = getattr(self, "icon_px", 16)  # Small arrow buttons set a smaller icon
            self.setIconSize(QtCore.QSize(px(size), px(size)))

    def _sync_cursor(self):
        self.setCursor(Qt.PointingHandCursor if self.isEnabled() else Qt.ArrowCursor)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.EnabledChange:
            self._sync_cursor()
        QtWidgets.QPushButton.changeEvent(self, event)


class MenuItem(Button):
    """One row of a Menu: a 16 px Lucide icon, the text, and an optional shortcut at the right in muted text. The
    current row (under the pointer, or chosen with the arrow keys) has the rounded `selected` fill. A destructive row
    (Delete, Remove, Clear) has red text and a red icon; as the current row it takes the red fill of a Delete button
    with light text and icon, so the user sees what the click does before it."""

    def __init__(self, text, theme, icon, danger=False, shortcut=""):
        Button.__init__(self, text, theme, icon=icon, variant="menu", icon_role="log_error" if danger else None)
        self.danger = danger
        self.menu = None
        self.setObjectName("toolMenuItem")
        self.setProperty("danger", "true" if danger else "false")
        self.setProperty("current", "false")
        self.setFocusPolicy(Qt.NoFocus)
        self.shortcut_label = None
        if shortcut:
            self.shortcut_label = QtWidgets.QLabel(shortcut, self)
            self.shortcut_label.setObjectName("toolMenuShortcut")
            self.shortcut_label.setProperty("danger", "true" if danger else "false")
            self.shortcut_label.setProperty("current", "false")
            self.shortcut_label.setAttribute(Qt.WA_TransparentForMouseEvents)

    def sizeHint(self):
        hint = Button.sizeHint(self)
        if self.shortcut_label is not None:  # Room for the shortcut and a gap before it
            hint.setWidth(hint.width() + self.shortcut_label.sizeHint().width() + px(24))
        return hint

    def resizeEvent(self, event):
        Button.resizeEvent(self, event)
        if self.shortcut_label is not None:
            hint = self.shortcut_label.sizeHint()
            self.shortcut_label.setGeometry(self.width() - hint.width() - px(12), (self.height() - hint.height()) // 2,
                                            hint.width(), hint.height())

    def is_current(self):
        return self.property("current") == "true"

    def set_current(self, on):
        value = "true" if on and self.isEnabled() else "false"
        set_style_property(self, "current", value)
        if self.shortcut_label is not None:
            set_style_property(self.shortcut_label, "current", value)
        if self.danger and self.icon_name:  # Light icon on the red fill, red icon on the menu
            role = "danger_text" if value == "true" else "log_error"
            self.setIcon(make_icon(self.icon_name, dict(self._theme.colors, text=self._theme.colors[role]), self))

    def enterEvent(self, event):
        if self.menu is not None:
            self.menu.set_current(self if self.isEnabled() else None)
        Button.enterEvent(self, event)

    def leaveEvent(self, event):
        if self.menu is not None and self.is_current():
            self.menu.set_current(None)
        Button.leaveEvent(self, event)


class WindowButton(Button):
    """A round 28 px title-bar button: transparent at rest, a soft circle on hover; the close button turns red with a
    white cross. `small` gives the 22 px button of the collapsed bar through the "compact" property (not "size":
    that is a Qt property of every widget, and a style rule on it silently never matches)."""

    def __init__(self, icon, theme, tooltip, close=False, parent=None, small=False):
        Button.__init__(self, "", theme, icon=icon, variant="ghost", tooltip=tooltip, parent=parent)
        self._close = close
        self.setObjectName("toolIconButton")
        self.setProperty("role", "close" if close else "")
        self.setProperty("compact", "true" if small else "false")  # 22 px: the collapsed bar ("size" is Qt's own)
        self.setFixedSize(px(22 if small else 28), px(22 if small else 28))
        if small:
            self.icon_px = 14
            self._on_theme(theme.colors)  # Again, with the smaller icon
        self.setFocusPolicy(Qt.NoFocus)  # No focus frame on a round button

    def enterEvent(self, event):
        if self._close and self.isEnabled():
            self.setIcon(make_icon(self.icon_name, dict(self._theme.colors, text="#ffffff"), self))
        Button.enterEvent(self, event)

    def leaveEvent(self, event):
        if self._close:
            self._on_theme(self._theme.colors)
        Button.leaveEvent(self, event)


class StatusAction(Button):
    """A text action in the status bar, as MaxPkg Runtime Manager's "View Logs": muted 11 px text after a 12 px Lucide
    icon in the muted colour, no background and no frame; on hover only the text colour changes. It opens something
    (the Logs window); it is not a command that changes the scene."""

    def __init__(self, text, theme, icon, tooltip=""):
        Button.__init__(self, text, theme, icon=icon, variant="ghost", tooltip=tooltip, icon_role="muted_text")
        self.setObjectName("toolStatusAction")
        self.icon_px = 12
        self._on_theme(theme.colors)  # Again, at 12 px
        self.setFocusPolicy(Qt.NoFocus)


class Flash(QtWidgets.QWidget):
    """A coloured highlight over a widget that fades out: shows where to look after a jump to a field (a click on a
    mini log row)."""

    def __init__(self, target, color, duration=2000):
        QtWidgets.QWidget.__init__(self, target.parentWidget())
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._color = QtGui.QColor(color)
        self._alpha = 0.0
        self.setGeometry(target.geometry().adjusted(-px(2), -px(2), px(2), px(2)))
        self.animation = QtCore.QVariantAnimation(self)
        self.animation.setDuration(duration)
        self.animation.setKeyValueAt(0.0, 0.0)
        self.animation.setKeyValueAt(0.15, 1.0)  # Lights up smoothly (0.3 s)
        self.animation.setKeyValueAt(0.35, 1.0)  # stays a moment
        self.animation.setKeyValueAt(1.0, 0.0)  # and fades out slowly
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        self.animation.valueChanged.connect(self._step)
        self.animation.finished.connect(self.deleteLater)
        self.show()
        self.raise_()
        self.animation.start()

    def _step(self, value):
        self._alpha = float(value)
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        fill = QtGui.QColor(self._color)
        fill.setAlphaF(0.6 * self._alpha)  # The whole field lights up, not only its outline
        edge = QtGui.QColor(self._color)
        edge.setAlphaF(self._alpha)
        painter.setPen(QtGui.QPen(edge, px(2)))
        painter.setBrush(fill)
        painter.drawRoundedRect(QtCore.QRectF(self.rect()).adjusted(1, 1, -1, -1), px(7), px(7))
        painter.end()


class QTipLabel(QtWidgets.QWidget):
    """Base of the tool's own tooltip windows (Qt.ToolTip). The name is on purpose: Qt for Windows gives Windows' small
    soft popup shadow (CS_DROPSHADOW) only to tooltip windows whose class inherits "QTipLabel" (its own tooltip label),
    so the red error bubble gets the same light shadow as every Qt tooltip. The shadow follows the window mask, arrow
    included. Style sheets still match the subclass's own name, never the QToolTip rule: never name the bubble itself
    QTipLabel."""


class ErrorTip(QTipLabel, Themed):
    """What is wrong with a field, in a red bubble that floats up just above it as soon as the pointer is on the
    field (no system tooltip delay). A small arrow points at the field; it goes away when the pointer leaves. It has
    the light system shadow of tooltips (QTipLabel; no NoDropShadowWindowHint)."""

    WIDTH = 300
    PAD = 9
    ARROW = 6
    RADIUS = 7

    def __init__(self, theme, parent=None):
        QTipLabel.__init__(self, parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        if parent is not None:
            self.setFont(parent.font())  # A popup does not inherit its window's interface-size font
        self._text, self._below, self._tip = "", False, 0
        self._colors = theme.colors
        self.target = None
        self.fade = QtCore.QVariantAnimation(self)
        self.fade.setDuration(140)
        self.fade.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.fade.valueChanged.connect(self._step)
        self._end = QtCore.QPoint()
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def show_for(self, widget, text):
        self.target = widget
        self._text = text = keep_urls_whole(text)
        inner = px(self.WIDTH) - 2 * px(self.PAD)
        metrics = QtGui.QFontMetrics(self.font())
        text_rect = metrics.boundingRect(0, 0, inner, 10000, int(Qt.TextWordWrap), text)
        width = min(px(self.WIDTH), text_rect.width() + 2 * px(self.PAD) + 2)
        height = text_rect.height() + 2 * px(self.PAD) + px(self.ARROW)
        corner = widget.mapToGlobal(QtCore.QPoint(0, 0))
        area = work_area(corner) or QtCore.QRect(corner.x() - 2000, corner.y() - 2000, 4000, 4000)
        self._below = corner.y() - height - px(2) < area.top()  # No room above: under the field
        x = max(area.left(), min(corner.x(), area.right() - width))
        y = corner.y() + widget.height() + px(2) if self._below else corner.y() - height - px(2)
        self._tip = max(px(self.RADIUS) + px(self.ARROW), min(corner.x() + px(18) - x, width - px(self.RADIUS) - px(self.ARROW)))
        self.setFixedSize(width, height)
        self._end = QtCore.QPoint(x, y)
        shape = self._shape()
        self.setMask(QtGui.QRegion(shape.toFillPolygon().toPolygon()))
        self.fade.stop()
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)
        self._step(0.0)
        self.show()
        self.raise_()
        self.fade.start()

    def _step(self, value):
        value = float(value)
        self.setWindowOpacity(value)
        lift = int(round((1.0 - value) * px(6)))  # Floats up into place (down into place when under the field)
        self.move(self._end.x(), self._end.y() + (-lift if self._below else lift))

    def hide_tip(self, widget=None):
        if widget is None or widget is self.target:
            self.fade.stop()
            self.hide()
            self.target = None

    def _shape(self):
        body_h = self.height() - px(self.ARROW)
        top = px(self.ARROW) if self._below else 0
        body = QtGui.QPainterPath()
        body.addRoundedRect(QtCore.QRectF(0, top, self.width(), body_h), px(self.RADIUS), px(self.RADIUS))
        edge = top if self._below else body_h
        point = 0 if self._below else self.height()
        arrow = QtGui.QPainterPath()
        arrow.addPolygon(QtGui.QPolygonF([QtCore.QPointF(self._tip - px(self.ARROW), edge + (1 if self._below else -1)),
                                          QtCore.QPointF(self._tip, point),
                                          QtCore.QPointF(self._tip + px(self.ARROW), edge + (1 if self._below else -1))]))
        return body.united(arrow)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        paint_bubble(painter, self._shape(), self._colors["danger"], self._colors["log_error"], 1.0)
        painter.setPen(QtGui.QColor(self._colors["danger_text"]))
        top = px(self.ARROW) if self._below else 0
        painter.drawText(QtCore.QRectF(px(self.PAD), top + px(self.PAD), self.width() - 2 * px(self.PAD),
                                       self.height() - px(self.ARROW) - 2 * px(self.PAD)),
                         int(Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignVCenter), self._text)
        painter.end()


class Tip(QTipLabel, Themed):
    """The tool's plain tooltip: the text on `tooltip_background` in `tooltip_text`, a 1 px `active_border` outline,
    radius 6 by a window mask (outlined on every side with paint_bubble), Windows' light tooltip shadow (QTipLabel),
    at most 360 px wide with word wrap. It opens under the pointer (above it when there is no room), stays inside the
    screen's work area, and goes when the pointer leaves, clicks, scrolls or types, or after 10 s plus 40 ms a
    character. One Tip per window (`tips_of`)."""

    WIDTH = 360
    RADIUS = 6

    def __init__(self, theme, parent=None):
        QTipLabel.__init__(self, parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        if parent is not None:
            self.setFont(parent.font())  # A popup does not inherit its window's interface-size font
        self._text = ""
        self.owner = None
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def text(self):
        return self._text

    def _layout(self, text):
        pad_x, pad_y = space(8), space(4)
        metrics = QtGui.QFontMetrics(self.font())
        box = metrics.boundingRect(0, 0, px(self.WIDTH) - 2 * pad_x, 10000, int(Qt.TextWordWrap), text)
        return QtCore.QSize(box.width() + 2 * pad_x + 2, box.height() + 2 * pad_y + 2)

    def show_text(self, point, text, owner=None):
        self.owner = owner
        self._text = text
        size = self._layout(text)
        area = work_area(point) or QtCore.QRect(point.x() - 2000, point.y() - 2000, 4000, 4000)
        x = max(area.left(), min(point.x() + px(2), area.right() - size.width()))
        y = point.y() + px(18)  # Under the pointer, clear of the cursor
        if y + size.height() > area.bottom():
            y = point.y() - size.height() - px(4)
        self.setFixedSize(size)
        self.move(x, max(area.top(), y))
        round_popup(self, self.RADIUS)
        self.show()
        self.raise_()
        self.update()
        self._timer.start(10000 + 40 * len(text))

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(self.rect()), px(self.RADIUS), px(self.RADIUS))
        paint_bubble(painter, path, self._colors["tooltip_background"], self._colors["active_border"])
        painter.setPen(QtGui.QColor(self._colors["tooltip_text"]))
        painter.setFont(self.font())
        painter.drawText(self.rect().adjusted(space(8) + 1, space(4) + 1, -space(8) - 1, -space(4) - 1),
                         int(Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignVCenter), self._text)
        painter.end()


class ErrorHints(QtCore.QObject):
    """Shows a field's error in an ErrorTip while the pointer is on it. A field has an error while its
    "invalidMessage" property holds text."""

    MOVE = 3  # Pixels the pointer moves on the field before its bubble shows

    def __init__(self, theme, window):
        QtCore.QObject.__init__(self, window)
        self.tip = ErrorTip(theme, window)
        self.cursor_pos = QtGui.QCursor.pos  # Where the pointer is (a test gives its own)
        self._pending, self._origin = None, None
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._check)

    def watch(self, widget):
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QtCore.QEvent.Enter:
            if watched.property("invalidMessage"):
                # Not at once: Qt also sends Enter when a dropdown or a menu above the field closes and the pointer
                # simply is there. The bubble waits until the pointer moves on the field.
                self._pending, self._origin = watched, self.cursor_pos()
                self._timer.start()
        elif kind in (QtCore.QEvent.Leave, QtCore.QEvent.Hide, QtCore.QEvent.MouseButtonPress):
            if self._pending is watched:
                self._stop_waiting()
            self.tip.hide_tip(watched)
        return False

    def _stop_waiting(self):
        self._timer.stop()
        self._pending = None

    def _check(self):
        widget = self._pending
        try:
            position = self.cursor_pos()
            inside = widget is not None and widget.isVisible() and widget.rect().contains(widget.mapFromGlobal(position))
        except RuntimeError:  # The field is gone
            inside = False
        if not inside:
            self._stop_waiting()
            return
        if (position - self._origin).manhattanLength() >= self.MOVE:
            self._stop_waiting()
            message = widget.property("invalidMessage")
            if message:
                self.tip.show_for(widget, message)

    def refresh(self, widget):
        """The field's error changed while the pointer is on it: update or remove the bubble."""
        if self.tip.target is widget:
            message = widget.property("invalidMessage")
            if message:
                self.tip.show_for(widget, message)
            else:
                self.tip.hide_tip(widget)

    def dispose(self):
        self._stop_waiting()
        self.tip.hide()
        self.tip.deleteLater()


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
            button.setFocusPolicy(Qt.NoFocus)  # No dotted focus frame on a segment
            position = "first" if index == 0 else ("last" if index == len(options) - 1 else "middle")
            button.setProperty("segment", position)
            button.setParent(self)
            self.group.addButton(button)
            self.buttons[key] = button
            self._order.append(button)
            button.toggled.connect(lambda on, k=key: self._on_toggled(k, on))
        self.set_value(current or options[0][0])

    def _height(self):
        # The one control height, like the fields beside it: never the buttons' padded size hint, which is shorter
        # (unify_heights makes the buttons 30 px; a shorter row cut their bottom border off).
        return max([px(CONTROL_HEIGHT)] + [button.minimumHeight() for button in self._order])

    def sizeHint(self):
        hints = [button.sizeHint() for button in self._order]
        return QtCore.QSize(sum(h.width() for h in hints) - self.OVERLAP * (len(hints) - 1), self._height())

    def minimumSizeHint(self):
        # Text width plus a small margin only: the buttons' own (padded) minimum made the row wider than a
        # panel with a scroll bar, which cut off the last segment.
        metrics = self.fontMetrics()
        width = sum(metrics.horizontalAdvance(button.text()) + 14 for button in self._order)
        return QtCore.QSize(width, self._height())

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
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):
        """The wheel never changes a dropdown's value, focused or not: it scrolls the page under it (scrolling must
        never change a field by accident). The value is chosen in the open list or with the keyboard."""
        event.ignore()

    def showPopup(self):
        # The list is polished by its style sheet rule at its first show (Qt 5: 9 pt item view font). Polish it now and
        # give it the interface size first, so the popup is measured with the right rows.
        self.view().ensurePolished()
        inherit_fonts(self.view().window())
        QtWidgets.QComboBox.showPopup(self)
        popup = self.view().window()
        area = work_area(self.mapToGlobal(QtCore.QPoint(0, 0))) or popup.geometry()
        below = self.mapToGlobal(QtCore.QPoint(0, self.height() + 4))
        y = below.y()
        if y + popup.height() > area.bottom():
            y = self.mapToGlobal(QtCore.QPoint(0, 0)).y() - popup.height() - 4
        x = max(area.left(), min(below.x(), area.right() - popup.width()))
        popup.move(x, max(area.top(), y))
        round_popup(popup)  # Same rounded corners as the field it opens from


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
    """A help bubble with an arrow pointing at its HelpButton: a bold title, a thin line, then the help in short
    blocks (help_html: blank lines, **terms**, `code`). A click elsewhere or Esc closes it. Painted here and shaped
    with a window mask (translucent popups are risky inside Max). Windows' own small popup shadow (CS_DROPSHADOW: a
    Qt.Popup without NoDropShadowWindowHint) follows the mask: a light shadow right and below, arrow included."""

    WIDTH = 300
    PAD = 10
    ARROW = 7
    RADIUS = 6

    def __init__(self, theme, parent=None):
        QtWidgets.QWidget.__init__(self, parent, Qt.Popup | Qt.FramelessWindowHint)
        if parent is not None:
            self.setFont(parent.font())  # A popup does not inherit its window's (interface-size) font.
        self._title, self._text = "", ""
        self._document = QtGui.QTextDocument(self)
        self._document.setDocumentMargin(0)
        self._shape = QtGui.QPainterPath()
        self.closed_at = 0.0
        self.bind_theme(theme)

    def _fonts(self):
        title = QtGui.QFont(self.font())
        title.setBold(True)
        return title, self.font()

    def _layout_text(self):
        """The help as rich text at the balloon's inner width; returns its height."""
        _title_font, text_font = self._fonts()
        self._document.setDefaultFont(text_font)
        self._document.setHtml(help_html(self._text, self._colors))
        self._document.setTextWidth(px(self.WIDTH) - 2 * px(self.PAD))
        return int(self._document.size().height() + 0.999)

    def _rule_gap(self):
        return px(6)  # Above and below the thin line under the title

    def show_for(self, anchor, title, text):
        self._title, self._text = title, text
        title_font, _text_font = self._fonts()
        inner = px(self.WIDTH) - 2 * px(self.PAD)
        title_h = QtGui.QFontMetrics(title_font).boundingRect(0, 0, inner, 10000, int(Qt.TextWordWrap), title).height()
        text_h = self._layout_text()
        body_h = px(self.PAD) + title_h + 2 * self._rule_gap() + 1 + text_h + px(self.PAD)
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
        if self._text:
            self._layout_text()
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        paint_bubble(painter, self._shape, self._colors["tooltip_background"], self._colors["active_border"], 1.5)
        title_font, text_font = self._fonts()
        inner = px(self.WIDTH) - 2 * px(self.PAD)
        top = self._body_top + px(self.PAD)
        painter.setFont(title_font)
        painter.setPen(QtGui.QColor(self._colors["heading_text"]))
        painter.drawText(QtCore.QRect(px(self.PAD), top, inner, self._title_h), int(Qt.TextWordWrap), self._title)
        rule = top + self._title_h + self._rule_gap()
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        painter.setPen(QtGui.QPen(QtGui.QColor(self._colors["border"]), 1))
        painter.drawLine(px(self.PAD), rule, px(self.PAD) + inner, rule)  # Separates the title from the help
        painter.translate(px(self.PAD), rule + 1 + self._rule_gap())
        self._document.drawContents(painter)
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


class EdgeFade(QtWidgets.QWidget, Themed):
    """A soft edge of a scroll area, as in the MaxPkg Package Manager: the colour behind the area drawn over the
    content with an alpha ramp, so the content fades out instead of being cut off. The top edge shows once the area
    is scrolled, the bottom edge while more is below. `role`: the theme colour behind the area (window for a page,
    tab_pane_background inside a panel, field inside a list box). Mouse events pass through. See fade_edges."""

    SIZE = 22  # Logical px

    def __init__(self, area, theme, edge="top", role="window"):
        QtWidgets.QWidget.__init__(self, area.viewport())
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.area = area
        self.edge = edge
        self.role = role
        bar = area.verticalScrollBar()
        bar.valueChanged.connect(self._follow)
        bar.rangeChanged.connect(lambda _low, _high: self._follow())
        area.viewport().installEventFilter(self)
        self.bind_theme(theme)
        self._follow()

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.Resize, QtCore.QEvent.Show):
            self._follow()
        return False

    def _follow(self, *_args):
        viewport = self.area.viewport()
        bar = self.area.verticalScrollBar()
        needed = bar.value() > bar.minimum() if self.edge == "top" else bar.value() < bar.maximum()
        size = px(self.SIZE)
        self.setGeometry(0, 0 if self.edge == "top" else viewport.height() - size, viewport.width(), size)
        self.setVisible(needed)
        if needed:
            self.raise_()
            self.update()

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        solid = QtGui.QColor(self._colors[self.role])
        clear = QtGui.QColor(solid)
        clear.setAlpha(0)
        ramp = QtGui.QLinearGradient(0, 0, 0, self.height())
        ramp.setColorAt(0.0, solid if self.edge == "top" else clear)
        ramp.setColorAt(1.0, clear if self.edge == "top" else solid)
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QBrush(ramp))
        painter.end()


def fade_edges(area, theme, role="window"):
    """Soft top and bottom edges on a scroll area (EdgeFade); returns both."""
    return EdgeFade(area, theme, "top", role), EdgeFade(area, theme, "bottom", role)


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


class PromotionLink(QtWidgets.QLabel, Themed):
    """The rotating link in the status bar, as in MaxRewind, TerraScoop and Max Ultra MCP (same author): a new
    message every ROTATE_MS in shuffled order (never the same one twice in a row), the long text when it fits and the
    short one otherwise, underlined in the `support_link` colour; a click opens the page in the browser. The messages
    are `(long text, short text, URL)` (package PROMOTIONS); one without a URL is left out."""

    ROTATE_MS = 30000

    def __init__(self, theme, promotions, parent=None):
        QtWidgets.QLabel.__init__(self, parent)
        self.promotions = [promotion for promotion in promotions if promotion[2]]
        self.setMinimumWidth(0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
        self.setTextFormat(Qt.RichText)
        self.setOpenExternalLinks(False)
        self.linkActivated.connect(lambda url: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url)))
        self._color = "#efa35c"
        self._remaining, self.current = [], None
        self.timer = QtCore.QTimer(self)  # Runs only while the link is shown
        self.timer.setInterval(self.ROTATE_MS)
        self.timer.timeout.connect(self.rotate)
        self.rotate()
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._color = colors.get("support_link", colors.get("link", self._color))
        self.update_text()

    def rotate(self):
        import random
        if not self.promotions:
            return
        if not self._remaining:
            self._remaining = list(self.promotions)
            random.shuffle(self._remaining)
            if len(self._remaining) > 1 and self._remaining[-1] == self.current:
                self._remaining[0], self._remaining[-1] = self._remaining[-1], self._remaining[0]
        self.current = self._remaining.pop()
        self.update_text()

    def update_text(self):
        import html
        if self.current is None:
            return
        full, short, url = self.current
        metrics = self.fontMetrics()
        width = metrics.horizontalAdvance if hasattr(metrics, "horizontalAdvance") else metrics.width
        available = max(0, self.contentsRect().width() - 2)
        label = full if width(full) <= available else short
        label = metrics.elidedText(label, Qt.ElideRight, available)
        self.setText('<a href="{}" style="color:{}; text-decoration:underline">{}</a>'.format(
            html.escape(url, quote=True), self._color, html.escape(label)))
        self.setToolTip(full + "\n" + url)
        self.setAccessibleName(full)

    def resizeEvent(self, event):
        QtWidgets.QLabel.resizeEvent(self, event)
        self.update_text()

    def showEvent(self, event):
        QtWidgets.QLabel.showEvent(self, event)
        self.timer.start()

    def hideEvent(self, event):
        self.timer.stop()
        QtWidgets.QLabel.hideEvent(self, event)


class Link(QtWidgets.QWidget, Themed):
    """A plain hyperlink: the text in the `link` colour, underlined under the pointer or with the keyboard focus, the
    pointing hand. A click (or Enter / Space) opens `url` in the browser, or calls `on_click` for a link that opens
    something inside the tool. `external` adds the small Lucide external-link icon after the text (a page outside the
    tool). The address is the tooltip. Use it in running text and help; actions that change something are buttons."""

    clicked = Signal()

    def __init__(self, theme, text, url="", on_click=None, external=False, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._text, self.url, self._on_click, self._external = text, url, on_click, external
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self.setAttribute(Qt.WA_Hover)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setToolTip(url or text)
        self.setAccessibleName(text)
        self.bind_theme(theme)

    def text(self):
        return self._text

    def sizeHint(self):
        metrics = self.fontMetrics()
        width = metrics.horizontalAdvance(self._text) if hasattr(metrics, "horizontalAdvance") else \
            metrics.width(self._text)
        return QtCore.QSize(width + (px(4) + px(12) if self._external else 0) + 2, metrics.height() + 2)

    def _open(self):
        if self._on_click is not None:
            self._on_click()
        elif self.url:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.url))
        self.clicked.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self._open()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._open()
            return
        QtWidgets.QWidget.keyPressEvent(self, event)

    def enterEvent(self, event):
        self.update()
        QtWidgets.QWidget.enterEvent(self, event)

    def leaveEvent(self, event):
        self.update()
        QtWidgets.QWidget.leaveEvent(self, event)

    def focusInEvent(self, event):
        self.update()
        QtWidgets.QWidget.focusInEvent(self, event)

    def focusOutEvent(self, event):
        self.update()
        QtWidgets.QWidget.focusOutEvent(self, event)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        color = self._colors.get("link", self._colors["accent"])
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        font = QtGui.QFont(self.font())
        font.setUnderline(self.underMouse() or self.hasFocus())
        painter.setFont(font)
        painter.setPen(QtGui.QColor(color))
        metrics = QtGui.QFontMetrics(font)
        width = metrics.horizontalAdvance(self._text) if hasattr(metrics, "horizontalAdvance") else \
            metrics.width(self._text)
        painter.drawText(QtCore.QRect(0, 0, width + 2, self.height()), int(Qt.AlignVCenter | Qt.AlignLeft), self._text)
        if self._external:
            size = px(12)
            painter.drawPixmap(width + px(4), (self.height() - size) // 2,
                               icon_pixmap("external-link", color, size, device_pixel_ratio(self)))
        painter.end()
```

## `python/mytool/ui/toast.py`

```python
"""Toasts: short notices about the result of an action, as MaxPkg Runtime Manager shows them.

A toast is an opaque rounded card inside the tool's window (a child widget, never a translucent window inside Max):
an animated status icon on a tinted disc, a bold first line and a muted rest, optional action buttons, a close button
and a thin bar along the bottom that shows the time left. It slides in from the right and fades in; the time waits
while the pointer is over it; a click anywhere on it closes it. Toasts stack below the window's header, newest at the
bottom. A toast with a key that is still open is shown again for its full time instead of a second one.

Use a toast for the outcome of an action the user started (copied, saved, built, failed). Keep problems that block
work in the mini log and on the fields; ask before destroying something (dialogs.ask).
"""

import math
import re

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, is_valid
from ..ui_scale import px, space
from . import controls

_LINK = re.compile(r"(?:https?://|www\.)\S+")
# The Lucide "box" on its 24-unit grid: the outline (a hexagon) and the inner edges.
BOX_OUTLINE = ((12, 2), (21, 7), (21, 17), (12, 22), (3, 17), (3, 7), (12, 2))
BOX_INNER = (((3, 7), (12, 12), (21, 7)), ((12, 12), (12, 22)))


def without_links(text):
    """`text` with every http(s):// or www. address removed and lines left empty dropped: a notification never
    shows a raw web address."""
    lines = []
    for line in str(text or "").split("\n"):
        if not _LINK.search(line):
            lines.append(line)
            continue
        cleaned = " ".join(_LINK.sub("", line).split())
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines).strip()


def ease_out(progress):
    """Cubic ease-out of a 0..1 progress (the animated icons)."""
    return 1.0 - (1.0 - progress) ** 3


def round_pen(color, width):
    pen = QtGui.QPen(color, width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def partial_line(points, fraction):
    """The first `fraction` (0..1) of a polyline, by length."""
    if fraction <= 0:
        return []
    lengths = [math.hypot(end[0] - start[0], end[1] - start[1]) for start, end in zip(points, points[1:])]
    left = sum(lengths) * min(1.0, fraction)
    drawn = [points[0]]
    for (start, end), length in zip(zip(points, points[1:]), lengths):
        if left >= length:
            drawn.append(end)
            left -= length
        else:
            share = left / length if length else 0.0
            drawn.append((start[0] + (end[0] - start[0]) * share, start[1] + (end[1] - start[1]) * share))
            break
    return drawn


class StatusIcon(QtWidgets.QWidget):
    """An animated status icon painted with QPainter (QtSvg plays almost no SVG animation). running: the Lucide box
    draws itself in a loop; done: a circle and then a tick draw in with a small spring; error: the alert icon draws in
    and shakes; warning: the same with a small hop; info: the circle, the dot and the stem of an "i". The timer runs
    only while something moves."""

    SIZE = 44  # Drawn on a 44 px grid, scaled to the widget
    FPS = 30
    DONE_SECONDS = 0.9
    ERROR_SECONDS = 0.9
    LOOP = 2.4  # Seconds per drawing loop of the box

    def __init__(self, theme, size=SIZE, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.theme = theme
        self._state = "running"
        self._clock = QtCore.QElapsedTimer()
        self._clock.start()
        self.setFixedSize(px(size), px(size))
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(int(1000 / self.FPS))
        self._timer.timeout.connect(self._tick)

    def set_state(self, state):
        """'running', 'done', 'error', 'warning' or 'info'."""
        self._state = state
        self._clock.restart()
        if self.isVisible():
            self._timer.start()
        self.update()

    def state(self):
        return self._state

    def _elapsed(self):
        return self._clock.elapsed() / 1000.0

    def _tick(self):
        finished = self.DONE_SECONDS if self._state == "done" else self.ERROR_SECONDS
        if self._state != "running" and self._elapsed() > finished + 0.2:
            self._timer.stop()
        self.update()

    def showEvent(self, event):
        QtWidgets.QWidget.showEvent(self, event)
        self._timer.start()

    def hideEvent(self, event):
        self._timer.stop()
        QtWidgets.QWidget.hideEvent(self, event)

    def paintEvent(self, _event):
        colors = self.theme.colors
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.scale(self.width() / float(self.SIZE), self.height() / float(self.SIZE))
        elapsed = self._elapsed()
        progress = min(1.0, elapsed / self.ERROR_SECONDS)
        if self._state == "running":
            self._paint_running(painter, elapsed, QtGui.QColor(colors["accent"]))
        elif self._state == "done":
            self._paint_done(painter, min(1.0, elapsed / self.DONE_SECONDS), QtGui.QColor(colors["log_success"]))
        elif self._state == "info":
            self._paint_info(painter, progress, QtGui.QColor(colors["accent"]))
        elif self._state == "warning":
            self._paint_error(painter, progress, QtGui.QColor(colors["log_warning"]), hop=True)
        else:
            self._paint_error(painter, progress, QtGui.QColor(colors["log_error"]))
        painter.end()

    def _paint_running(self, painter, elapsed, accent):
        phase = (elapsed % self.LOOP) / self.LOOP
        outline = ease_out(min(1.0, phase / 0.45))
        inner = ease_out(max(0.0, min(1.0, (phase - 0.35) / 0.3)))
        pulse = 1.0 + 0.06 * math.sin(max(0.0, min(1.0, (phase - 0.7) / 0.15)) * math.pi) if phase > 0.7 else 1.0
        alpha = 1.0 if phase < 0.88 else max(0.0, 1.0 - (phase - 0.88) / 0.12)
        painter.translate(self.SIZE / 2.0, self.SIZE / 2.0)
        painter.scale(pulse * self.SIZE / 26.0, pulse * self.SIZE / 26.0)
        painter.translate(-12.0, -12.0)
        faint = QtGui.QColor(accent)
        faint.setAlpha(40)
        painter.setPen(round_pen(faint, 1.6))
        for line in self._box_paths(1.0, 1.0):
            painter.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in line]))
        color = QtGui.QColor(accent)
        color.setAlphaF(alpha)
        painter.setPen(round_pen(color, 1.9))
        for line in self._box_paths(outline, inner):
            if len(line) > 1:
                painter.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in line]))

    def _box_paths(self, outline, inner):
        """The box's lines, each cut to the drawn fraction."""
        paths = [partial_line(BOX_OUTLINE, outline)]
        paths.extend(partial_line(line, inner) for line in BOX_INNER)
        return paths

    def _paint_done(self, painter, progress, color):
        eased = ease_out(progress)
        spring = 1.0 + 0.07 * math.sin(max(0.0, (progress - 0.66) / 0.34) * math.pi) if progress > 0.66 else 1.0
        painter.translate(self.SIZE / 2.0, self.SIZE / 2.0)
        painter.scale(spring, spring)
        painter.translate(-self.SIZE / 2.0, -self.SIZE / 2.0)
        ring = QtCore.QRectF(4, 4, self.SIZE - 8, self.SIZE - 8)  # Room for the spring
        painter.setPen(round_pen(color, 2.6))
        painter.drawArc(ring, 90 * 16, int(-360.0 * min(1.0, eased / 0.6) * 16))
        tick = max(0.0, min(1.0, (eased - 0.45) / 0.45))
        if tick > 0:
            # The tick of Lucide circle-check on its 24 grid, scaled to the icon.
            scale = (self.SIZE - 8) / 20.0
            points = [QtCore.QPointF(4 + (x - 2) * scale, 4 + (y - 2) * scale)
                      for x, y in ((8.5, 12.0), (11.0, 14.5), (15.5, 9.5))]
            first = math.hypot(points[1].x() - points[0].x(), points[1].y() - points[0].y())
            second = math.hypot(points[2].x() - points[1].x(), points[2].y() - points[1].y())
            length = (first + second) * tick
            path = QtGui.QPainterPath(points[0])
            if length <= first:
                path.lineTo(points[0] + (points[1] - points[0]) * (length / first))
            else:
                path.lineTo(points[1])
                path.lineTo(points[1] + (points[2] - points[1]) * ((length - first) / second))
            painter.setPen(round_pen(color, 3.0))
            painter.drawPath(path)

    def _paint_info(self, painter, progress, color):
        """The circle draws in, the dot of the "i" pops in, then its stem grows downwards."""
        ring_part = ease_out(min(1.0, progress / 0.45))
        stem_part = ease_out(max(0.0, min(1.0, (progress - 0.5) / 0.35)))
        ring = QtCore.QRectF(4, 4, self.SIZE - 8, self.SIZE - 8)
        painter.setPen(round_pen(color, 2.6))
        painter.drawArc(ring, 90 * 16, int(-360.0 * ring_part * 16))
        middle = self.SIZE / 2.0
        if progress > 0.38:
            pop = min(1.0, (progress - 0.38) / 0.12)
            painter.setPen(round_pen(color, 3.0 + 1.2 * math.sin(pop * math.pi)))
            painter.drawPoint(QtCore.QPointF(middle, 14.5))
        if stem_part > 0:
            painter.setPen(round_pen(color, 3.0))
            painter.drawLine(QtCore.QPointF(middle, 20.5), QtCore.QPointF(middle, 20.5 + 9.5 * stem_part))

    def _paint_error(self, painter, progress, color, hop=False):
        """The circle draws in, the "!" is drawn from the top, its dot pops in, and the icon shakes (an error) or
        makes a small hop (a warning)."""
        ring_part = ease_out(min(1.0, progress / 0.45))
        bar_part = ease_out(max(0.0, min(1.0, (progress - 0.35) / 0.3)))
        if hop:
            lift = -math.sin(max(0.0, min(1.0, (progress - 0.6) / 0.3)) * math.pi) * 3.0 if progress > 0.6 else 0.0
            painter.translate(0, lift)
        else:
            shake = math.sin((progress - 0.45) * math.pi * 8) * 4.5 * (1.0 - progress) if progress > 0.45 else 0.0
            painter.translate(shake, 0)
        ring = QtCore.QRectF(4, 4, self.SIZE - 8, self.SIZE - 8)
        painter.setPen(round_pen(color, 2.6))
        painter.drawArc(ring, 90 * 16, int(-360.0 * ring_part * 16))
        middle = self.SIZE / 2.0
        painter.setPen(round_pen(color, 3.0))
        if bar_part > 0:
            painter.drawLine(QtCore.QPointF(middle, 13.5), QtCore.QPointF(middle, 13.5 + 11.0 * bar_part))
        if progress > 0.68:
            painter.drawPoint(QtCore.QPointF(middle, 31.0))


class Toast(QtWidgets.QFrame):
    """One notice (see the module). `kind`: success, error, warning or info. `action`: one (label, Lucide icon,
    callback) or a list of them; the first is the primary button, and an offer stays 3 s longer."""

    expired = Signal()

    STATES = {"success": ("done", "log_success"), "error": ("error", "log_error"),
              "warning": ("warning", "log_warning")}
    LIFETIME_MS = {"error": 8000, "warning": 6500}
    DEFAULT_LIFETIME_MS = 5200
    WIDTH = 340
    RADIUS = 14

    def __init__(self, text, kind, theme, parent, action=None, key=""):
        QtWidgets.QFrame.__init__(self, parent)
        self.setObjectName("toolToast")
        self.theme = theme
        self.kind = kind
        self.key = key
        state, self._role = self.STATES.get(kind, ("info", "accent"))
        self.icon = StatusIcon(theme, size=28)
        self.icon.set_state(state)
        disc = QtWidgets.QWidget()
        disc.setFixedSize(px(40), px(40))
        disc_layout = QtWidgets.QHBoxLayout(disc)
        disc_layout.setContentsMargins(space(6), space(6), space(6), space(6))
        disc_layout.addWidget(self.icon)
        self._disc = disc
        lines = without_links(text).split("\n", 1)  # Never a raw web address in a notification
        # Wrapped labels get an exact width, or the nested layout sizes them for a narrower one (gaps).
        text_width = px(self.WIDTH) - px(12) - px(40) - px(12) - px(12) - px(22) - px(10)
        texts = QtWidgets.QVBoxLayout()  # The title and the text, centred beside the icon
        texts.setSpacing(space(2))
        title = QtWidgets.QLabel(lines[0])
        title.setObjectName("toolToastTitle")
        title.setWordWrap(True)
        title.setFixedWidth(text_width)
        texts.addWidget(title)
        if len(lines) > 1 and lines[1].strip():
            body = QtWidgets.QLabel(lines[1].strip())
            body.setObjectName("toolToastBody")
            body.setWordWrap(True)
            body.setFixedWidth(text_width)
            texts.addWidget(body)
        actions = [action] if isinstance(action, tuple) else list(action or [])
        buttons = None
        if actions:  # Under the text, not beside the icon: the icon stays on the middle of the words
            buttons = QtWidgets.QHBoxLayout()
            buttons.setContentsMargins(space(40) + space(12), 0, 0, 0)
            buttons.setSpacing(space(8))
            for position, (action_text, action_icon, callback) in enumerate(actions):
                button = controls.Button(action_text, theme, icon=action_icon,
                                         variant="primary" if position == 0 else "secondary")
                button.setFixedHeight(px(controls.CONTROL_HEIGHT))
                button.clicked.connect(lambda _checked=False, run=callback: (self._expire(), run()))
                buttons.addWidget(button)
            buttons.addStretch(1)
        close = controls.Button("", theme, icon="x", variant="ghost", tooltip="Close", icon_role="muted_text")
        close.setObjectName("toolToastClose")
        close.icon_px = 14
        close._on_theme(theme.colors)
        close.setFixedSize(px(22), px(22))
        close.setFocusPolicy(Qt.NoFocus)
        close.clicked.connect(self._expire)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(space(12), space(12), space(12), space(16))
        outer.setSpacing(space(8))
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(12))
        row.addWidget(disc, 0, Qt.AlignVCenter)  # The icon on the vertical middle of the title and the text
        row.addLayout(texts, 1)
        row.setAlignment(texts, Qt.AlignVCenter)
        row.addWidget(close, 0, Qt.AlignTop)
        outer.addLayout(row)
        if buttons is not None:
            outer.addLayout(buttons)
        self.setFixedWidth(px(self.WIDTH))
        self.setAttribute(Qt.WA_Hover)
        self.setCursor(Qt.PointingHandCursor)
        self._lifetime = self.LIFETIME_MS.get(kind, self.DEFAULT_LIFETIME_MS) + (3000 if actions else 0)
        self._left = float(self._lifetime)
        self._clock = QtCore.QElapsedTimer()
        self._clock.start()
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self._slide = QtCore.QPropertyAnimation(self, b"pos", self)
        self._slide.setDuration(260)
        self._slide.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._entered = False
        self._opacity = QtWidgets.QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)
        self._fade = QtCore.QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade.setDuration(220)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        # Drop the effect once visible: it renders through an offscreen buffer that let the page show through.
        self._fade.finished.connect(lambda: self.setGraphicsEffect(None))

    def place(self, point):
        """Move to `point`; the first time it slides in from the right and fades in."""
        if not self._entered:
            self._entered = True
            self.move(point + QtCore.QPoint(px(28), 0))
            self._slide.setStartValue(self.pos())
            self._slide.setEndValue(point)
            self._slide.start()
            self._fade.start()
        elif self._slide.state() == QtCore.QAbstractAnimation.Running:
            self._slide.setEndValue(point)
        else:
            self.move(point)

    def restart(self):
        """Full time again, and the icon draws itself once more."""
        self._left = float(self._lifetime)
        self._clock.restart()
        self.icon.set_state(self.icon.state())
        self.update()

    def _tick(self):
        elapsed = self._clock.restart()
        if not self.underMouse():  # Reading a toast keeps it open
            self._left -= elapsed
        if self._left <= 0:
            self._expire()
            return
        self.update()

    def _expire(self):
        if is_valid(self):
            self._timer.stop()
            self.hide()
            self.expired.emit()
            self.deleteLater()

    def mousePressEvent(self, event):
        self._expire()

    def paintEvent(self, _event):
        colors = self.theme.colors
        accent = QtGui.QColor(colors[self._role])
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = px(self.RADIUS)
        # Opaque: toasts sit over busy pages, any see-through lets the controls below show.
        gradient = QtGui.QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0.0, QtGui.QColor(colors["popup"]))
        gradient.setColorAt(1.0, QtGui.QColor(colors["tab_pane_background"]))
        shape = QtGui.QPainterPath()
        shape.addRoundedRect(rect, radius, radius)
        painter.fillPath(shape, QtGui.QBrush(gradient))
        # A faint wash of the toast's colour from the left, under the icon.
        wash = QtGui.QLinearGradient(rect.topLeft(), QtCore.QPointF(rect.left() + px(140), rect.top()))
        tint = QtGui.QColor(accent)
        tint.setAlphaF(0.10)
        wash.setColorAt(0.0, tint)
        tint.setAlphaF(0.0)
        wash.setColorAt(1.0, tint)
        painter.fillPath(shape, QtGui.QBrush(wash))
        painter.setPen(QtGui.QPen(QtGui.QColor(colors["active_border"]), 1))
        painter.drawPath(shape)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 26), 1))  # The bright top edge of the glass
        painter.drawLine(QtCore.QPointF(rect.left() + radius, rect.top() + 1),
                         QtCore.QPointF(rect.right() - radius, rect.top() + 1))
        disc = QtCore.QRectF(self._disc.geometry())  # A tinted disc behind the icon
        fill = QtGui.QColor(accent)
        fill.setAlphaF(0.14)
        painter.setPen(Qt.NoPen)
        painter.setBrush(fill)
        painter.drawEllipse(disc)
        # Time left: a thin bar along the bottom, clipped to the rounded card.
        share = max(0.0, min(1.0, self._left / float(self._lifetime)))
        painter.setClipPath(shape)
        bar = QtGui.QColor(accent)
        bar.setAlphaF(0.75)
        painter.fillRect(QtCore.QRectF(rect.left(), rect.bottom() - 2.5, rect.width() * share, 2.5), bar)
        painter.end()


class ToastStack(QtCore.QObject):
    """The toasts of one window: below its header at the right, newest at the bottom, 8 px apart."""

    GAP = 8
    MARGIN = 14

    def __init__(self, window, theme):
        QtCore.QObject.__init__(self, window)
        self.window = window
        self.theme = theme
        self.toasts = []

    def notify(self, text, kind="info", action=None, key=""):
        """Show a toast (see Toast); returns it, or the open toast with the same key, shown again for its time."""
        if key:
            for toast in self.toasts:
                if is_valid(toast) and toast.isVisible() and toast.key == key:
                    toast.restart()
                    return toast
        toast = Toast(text, kind, self.theme, self.window, action=action, key=key)
        toast.expired.connect(lambda: QtCore.QTimer.singleShot(0, self.place))
        toast.show()
        self.toasts = [item for item in self.toasts if is_valid(item) and item.isVisible()] + [toast]
        self.place()
        return toast

    def place(self):
        window = self.window
        if not is_valid(window):
            return
        top = window.header_bottom() + px(self.GAP) if hasattr(window, "header_bottom") else px(self.MARGIN)
        alive = []
        for toast in self.toasts:
            if not is_valid(toast) or not toast.isVisible():
                continue
            toast.adjustSize()
            toast.place(QtCore.QPoint(window.width() - toast.width() - px(self.MARGIN), top))
            toast.raise_()
            top += toast.height() + px(self.GAP)
            alive.append(toast)
        self.toasts = alive

    def clear(self):
        for toast in list(self.toasts):
            if is_valid(toast):
                toast._expire()
        self.toasts = []
```
