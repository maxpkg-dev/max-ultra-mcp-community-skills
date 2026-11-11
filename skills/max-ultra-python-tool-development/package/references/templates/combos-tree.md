# Template: Dropdowns, choice cards, scene tree and drop zone

Dropdowns beyond the plain one (`combos.py`): with a Lucide icon per item, with group headings that cannot be chosen, editable (pick or type a new value, the completer owned by the window), and with check boxes that keep the list open and sum the ticks up in the field; choices as cards with an icon, a title and a line of text, moved with the arrow keys as radio buttons. A tree of the scene's parts as 3ds Max's Scene Explorer and a place to drop files (`tree.py`): layers with their objects, an icon per kind, check boxes that tick a whole layer, numbers on the right; a dashed area that takes files dragged from Explorer or chosen with Browse, and says at once whether it takes them.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP with the windows off screen (the controls trainer checks), and shown on screen in 3ds Max 2027.

## `python/mytool/ui/combos.py`

```python
"""Dropdowns beyond the plain one (controls.ComboBox), and choices shown as cards.

* IconComboBox: every item has a Lucide icon in the theme's colours, in the list and in the field; the icons are
  tinted again when the theme changes.
* GroupedComboBox: items under muted headings ("Renderers", "Exporters"); a heading cannot be chosen, the keys skip
  it, and the items under it are indented.
* editable_combo: a dropdown the user can also type into (a layer name that may be new). Its completer belongs to the
  window, never to the field (inputs.SearchBox explains why).
* MultiComboBox: a dropdown of check boxes for a few values that combine (object types to export). The list stays open
  while the user ticks; the field sums it up: "None", one name, "Box, Sphere", "3 selected" or "All".
* RadioCards: two to four exclusive choices whose difference needs a sentence (an export mode, a quality preset):
  cards with an icon, a title and a line of text; the chosen card has the accent border and a filled dot. The arrow
  keys move the choice, as radio buttons do.
Use a Segmented switch for two or three short words, a dropdown for a long list, and these where they read better.
"""

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, device_pixel_ratio, repolish
from ..ui_scale import px, space
from .controls import ComboBox, Themed, icon_pixmap, make_icon

HEADING = QtCore.Qt.UserRole + 41  # A heading row of GroupedComboBox


class IconComboBox(ComboBox, Themed):
    """See the module. `items`: (value, label, Lucide icon) triples."""

    def __init__(self, theme, items, parent=None):
        ComboBox.__init__(self, parent)
        self._icons = []
        for value, label, icon in items:
            self.addItem(label, value)
            self._icons.append(icon)
        self.setIconSize(QtCore.QSize(px(16), px(16)))
        self.bind_theme(theme)

    def _on_theme(self, colors):
        for index, name in enumerate(self._icons):
            self.setItemIcon(index, make_icon(name, colors, self))

    def value(self):
        return self.currentData()


class _GroupDelegate(QtWidgets.QStyledItemDelegate):
    """Headings in small muted bold text without a hover; items indented under them."""

    def __init__(self, combo):
        QtWidgets.QStyledItemDelegate.__init__(self, combo)
        self.combo = combo

    def sizeHint(self, option, index):
        hint = QtWidgets.QStyledItemDelegate.sizeHint(self, option, index)
        if index.data(HEADING):
            hint.setHeight(option.fontMetrics.height() + space(8))
        return hint

    def paint(self, painter, option, index):
        colors = self.combo._theme.colors
        if index.data(HEADING):
            painter.save()
            font = QtGui.QFont(option.font)
            font.setBold(True)
            font.setPointSizeF(option.font.pointSizeF() * 0.85)
            painter.setFont(font)
            painter.setPen(QtGui.QColor(colors["muted_text"]))
            painter.drawText(option.rect.adjusted(space(8), space(4), 0, 0), int(Qt.AlignLeft | Qt.AlignVCenter),
                             index.data(Qt.DisplayRole).upper())
            painter.restore()
            return
        text = index.data(Qt.DisplayRole)
        item = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(item, index)
        item.text = ""
        widget = option.widget
        style = widget.style() if widget is not None else QtWidgets.QApplication.style()
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, item, painter, widget)  # The rounded hover from the sheet
        active = bool(option.state & (QtWidgets.QStyle.State_Selected | QtWidgets.QStyle.State_MouseOver))
        painter.save()
        painter.setPen(QtGui.QColor(colors["selected_text" if active else "text"]))
        painter.drawText(option.rect.adjusted(space(8) + space(12), 0, -space(8), 0),
                         int(Qt.AlignLeft | Qt.AlignVCenter), text)
        painter.restore()


class GroupedComboBox(ComboBox, Themed):
    """See the module. `groups`: (heading, [(value, label), ...]) pairs."""

    def __init__(self, theme, groups, parent=None):
        ComboBox.__init__(self, parent)
        model = QtGui.QStandardItemModel(self)
        for heading, items in groups:
            row = QtGui.QStandardItem(heading)
            row.setData(True, HEADING)
            row.setFlags(Qt.NoItemFlags)  # Not chosen, skipped by the keys
            model.appendRow(row)
            for value, label in items:
                item = QtGui.QStandardItem(label)
                item.setData(value, Qt.UserRole)
                model.appendRow(item)
        self.setModel(model)
        self.bind_theme(theme)
        self.view().setItemDelegate(_GroupDelegate(self))
        first = next((row for row in range(model.rowCount()) if not model.item(row).data(HEADING)), 0)
        self.setCurrentIndex(first)

    def value(self):
        return self.currentData()

    def set_value(self, value):
        index = self.findData(value)
        if index >= 0 and not self.model().item(index).data(HEADING):
            self.setCurrentIndex(index)


def editable_combo(theme, items, owner, placeholder=""):
    """A dropdown with a text field: the user picks from `items` or types a new value. The completer (case
    insensitive, matching anywhere) belongs to `owner`, the window."""
    combo = ComboBox()
    combo.setEditable(True)
    combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)  # A typed value is a value, not a new list item
    combo.addItems(list(items))
    combo.setCurrentIndex(-1)
    if placeholder:
        combo.lineEdit().setPlaceholderText(placeholder)
    completer = QtWidgets.QCompleter(list(items), owner)
    completer.setCaseSensitivity(Qt.CaseInsensitive)
    completer.setFilterMode(Qt.MatchContains)
    combo.setCompleter(completer)
    return combo


class MultiComboBox(ComboBox, Themed):
    """See the module. `items`: (value, label) pairs; `checked`: the values ticked at the start."""

    changed = Signal(list)

    def __init__(self, theme, items, checked=(), parent=None):
        ComboBox.__init__(self, parent)
        model = QtGui.QStandardItemModel(self)
        for value, label in items:
            item = QtGui.QStandardItem(label)
            item.setData(value, Qt.UserRole)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setData(Qt.Checked if value in checked else Qt.Unchecked, Qt.CheckStateRole)
            model.appendRow(item)
        self.setModel(model)
        self.view().viewport().installEventFilter(self)
        self.bind_theme(theme)

    def items(self):
        model = self.model()
        return [model.item(row) for row in range(model.rowCount())]

    def values(self):
        return [item.data(Qt.UserRole) for item in self.items() if item.checkState() == Qt.Checked]

    def set_values(self, values):
        for item in self.items():
            item.setCheckState(Qt.Checked if item.data(Qt.UserRole) in values else Qt.Unchecked)
        self.update()
        self.changed.emit(self.values())

    def summary(self):
        chosen = [item.text() for item in self.items() if item.checkState() == Qt.Checked]
        if not chosen:
            return "None"
        if len(chosen) == len(self.items()):
            return "All"
        if len(chosen) <= 2:
            return ", ".join(chosen)
        return "{} selected".format(len(chosen))

    def eventFilter(self, watched, event):
        view = self.view()
        if view is not None and watched is view.viewport() and event.type() == QtCore.QEvent.MouseButtonRelease:
            position = event.position().toPoint() if hasattr(event, "position") else event.pos()
            index = view.indexAt(position)
            if index.isValid():  # Tick, and keep the list open for the next one
                item = self.model().itemFromIndex(index)
                item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
                self.update()
                self.changed.emit(self.values())
            return True
        return ComboBox.eventFilter(self, watched, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not self.view().isVisible():
            self.showPopup()
            return
        ComboBox.keyPressEvent(self, event)

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = self.summary()  # The field sums the ticks up
        option.currentIcon = QtGui.QIcon()
        painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, option)
        painter.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, option)


class RadioCard(QtWidgets.QFrame, Themed):
    """One card of RadioCards."""

    clicked = Signal()

    def __init__(self, theme, title, text, icon, parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setObjectName("toolRadioCard")
        self.setProperty("checked", "false")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self._icon = icon
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(space(12), space(12), space(12), space(12))
        layout.setSpacing(space(12))
        self.glyph = QtWidgets.QLabel()
        self.glyph.setFixedSize(px(20), px(20))
        layout.addWidget(self.glyph, 0, Qt.AlignTop)
        texts = QtWidgets.QVBoxLayout()
        texts.setSpacing(space(2))
        self.title = QtWidgets.QLabel(title)
        self.title.setObjectName("toolRadioTitle")
        self.text = QtWidgets.QLabel(text)
        self.text.setObjectName("toolMuted")
        self.text.setWordWrap(True)
        texts.addWidget(self.title)
        texts.addWidget(self.text)
        layout.addLayout(texts, 1)
        self.dot = _RadioDot(theme)
        layout.addWidget(self.dot, 0, Qt.AlignTop)
        for child in (self.glyph, self.title, self.text, self.dot):
            child.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.bind_theme(theme)

    def _on_theme(self, colors):
        role = "accent" if self.is_checked() else "muted_text"
        self.glyph.setPixmap(icon_pixmap(self._icon, colors[role], px(20), device_pixel_ratio(self)))

    def is_checked(self):
        return self.property("checked") == "true"

    def set_checked(self, on):
        self.setProperty("checked", "true" if on else "false")
        repolish(self)
        self.dot.set_checked(on)
        self._on_theme(self._theme.colors)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(
                event.position().toPoint() if hasattr(event, "position") else event.pos()):
            self.clicked.emit()
        QtWidgets.QFrame.mouseReleaseEvent(self, event)


class _RadioDot(QtWidgets.QWidget, Themed):
    """A radio circle: an empty ring, or the accent ring with a filled centre."""

    def __init__(self, theme, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setFixedSize(px(16), px(16))
        self._checked = False
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._colors = colors
        self.update()

    def set_checked(self, on):
        self._checked = on
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        ring = QtCore.QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.setPen(QtGui.QPen(QtGui.QColor(self._colors["accent" if self._checked else "checkbox_border"]), 1.5))
        painter.setBrush(QtGui.QColor(self._colors["recessed"]))
        painter.drawEllipse(ring)
        if self._checked:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QColor(self._colors["accent"]))
            inner = ring.width() * 0.27
            painter.drawEllipse(ring.adjusted(inner, inner, -inner, -inner))
        painter.end()


class RadioCards(QtWidgets.QWidget):
    """See the module. `choices`: (value, title, text, Lucide icon); `columns`: cards per row."""

    changed = Signal(object)

    def __init__(self, theme, choices, value=None, columns=None, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(space(8))
        columns = columns or len(choices)
        self.cards = []
        for index, (key, title, text, icon) in enumerate(choices):
            card = RadioCard(theme, title, text, icon)
            card.value = key
            card.clicked.connect(lambda card=card: self.choose(card.value, emit=True))
            card.installEventFilter(self)
            grid.addWidget(card, index // columns, index % columns)
            self.cards.append(card)
        for column in range(columns):
            grid.setColumnStretch(column, 1)
        self._value = None
        self.choose(value if value is not None else choices[0][0])

    def value(self):
        return self._value

    def choose(self, value, emit=False):
        for card in self.cards:
            card.set_checked(card.value == value)
        changed = value != self._value
        self._value = value
        if emit and changed:
            self.changed.emit(value)

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.KeyPress and watched in self.cards:
            key = event.key()
            index = self.cards.index(watched)
            if key in (Qt.Key_Right, Qt.Key_Down, Qt.Key_Left, Qt.Key_Up):
                step = 1 if key in (Qt.Key_Right, Qt.Key_Down) else -1
                card = self.cards[(index + step) % len(self.cards)]
                card.setFocus(Qt.TabFocusReason)
                self.choose(card.value, emit=True)  # As radio buttons: the arrow moves the choice
                return True
            if key in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
                self.choose(watched.value, emit=True)
                return True
        return QtWidgets.QWidget.eventFilter(self, watched, event)
```

## `python/mytool/ui/tree.py`

```python
"""A tree of the scene's parts, and a place to drop files.

* SceneTree (as 3ds Max's Scene Explorer): layers with their objects, a Lucide icon per kind (geometry, light,
  camera), a check box on every row (a layer's box shows "some" when only part of it is ticked and ticks all of it in
  one click), a second column right-aligned for numbers, theme chevrons to open and close a layer, the selection in
  the `selected` colour. Open a layer with a click on its chevron, a double-click or the Right key.
* DropZone: a dashed rounded area that takes files dragged from Explorer, and a Browse button for the same through
  the system file picker. While files are dragged over it, it says whether it takes them: the accent for files it
  takes, red with the reason for files it does not ("Only PNG, JPG or EXR"). It sends the paths it took.
"""

import os

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, device_pixel_ratio, repolish
from ..ui_scale import px, space
from .controls import Button, Themed, icon_pixmap, make_icon

KINDS = {"layer": "layers", "geometry": "box", "light": "lightbulb", "camera": "camera"}
KIND = Qt.UserRole + 7  # The row's kind, for its icon


class SceneTree(QtWidgets.QTreeWidget, Themed):
    """See the module. `columns`: the headings; add rows with add_layer / add_object."""

    checked_changed = Signal(list)  # The names of the ticked objects

    def __init__(self, theme, columns=("Name", "Polygons"), parent=None):
        QtWidgets.QTreeWidget.__init__(self, parent)
        self.setObjectName("toolTree")
        self.setColumnCount(len(columns))
        self.setHeaderLabels(list(columns))
        self.setUniformRowHeights(True)
        self.setAnimated(False)  # Rows appear at once, as in Max
        self.setIndentation(px(18))
        self.setIconSize(QtCore.QSize(px(16), px(16)))
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for column in range(1, len(columns)):
            self.header().setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeToContents)
            self.headerItem().setTextAlignment(column, int(Qt.AlignRight | Qt.AlignVCenter))
        self.itemChanged.connect(self._item_changed)
        self.bind_theme(theme)

    def _on_theme(self, colors):
        self._colors = colors
        iterator = QtWidgets.QTreeWidgetItemIterator(self)
        while iterator.value() is not None:
            item = iterator.value()
            kind = item.data(0, KIND)
            if kind:
                self._tint(item, kind)
            iterator += 1

    def _tint(self, item, kind):
        item.setData(0, KIND, kind)
        colors = self._colors
        item.setIcon(0, make_icon(KINDS[kind], dict(colors, text=colors["accent" if kind == "layer" else "muted_text"]),
                                  self))

    def add_layer(self, name, opened=True):
        item = QtWidgets.QTreeWidgetItem(self, [name])
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
        item.setCheckState(0, Qt.Checked)
        self._tint(item, "layer")
        item.setExpanded(opened)
        return item

    def add_object(self, layer, name, kind="geometry", numbers=(), checked=True):
        item = QtWidgets.QTreeWidgetItem(layer, [name] + ["{:,}".format(n) if isinstance(n, int) else str(n)
                                                          for n in numbers])
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        for column in range(1, self.columnCount()):
            item.setTextAlignment(column, int(Qt.AlignRight | Qt.AlignVCenter))  # Numbers line up on the right
        self._tint(item, kind)
        return item

    def checked_names(self):
        names = []
        iterator = QtWidgets.QTreeWidgetItemIterator(self)
        while iterator.value() is not None:
            item = iterator.value()
            if item.parent() is not None and item.checkState(0) == Qt.Checked:
                names.append(item.text(0))
            iterator += 1
        return names

    def _item_changed(self, item, column):
        if column == 0:
            self.checked_changed.emit(self.checked_names())

    def drawRow(self, painter, option, index):
        # The row's highlight is drawn here: one rounded bar from the check box to the right edge, the indent unlit and
        # no seam between the columns. The style sheet's item fills are transparent: Qt 6 also lit the indent of a
        # selected row, whatever show-decoration-selected said.
        selected = self.selectionModel() is not None and self.selectionModel().isSelected(index)
        hovered = bool(option.state & QtWidgets.QStyle.State_MouseOver)
        if selected or hovered:
            left = self.visualRect(index).left()
            bar = QtCore.QRectF(left, option.rect.top(), option.rect.right() - left + 1, option.rect.height())
            painter.save()
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QColor(self._colors["selected" if selected else "hover"]))
            painter.drawRoundedRect(bar, px(4), px(4))
            painter.restore()
        QtWidgets.QTreeWidget.drawRow(self, painter, option, index)

    def drawBranches(self, painter, rect, index):
        # The indent is drawn here: only a layer's chevron, never the row's selection or hover. Qt 6 paints the
        # selection into the indent whatever the style sheet says (show-decoration-selected), so a selected child row
        # had a lit piece at its left.
        item = self.itemFromIndex(index)
        if item is None or item.childCount() == 0:
            return
        size = px(12)
        indent = self.indentation()
        x = rect.right() - indent + (indent - size) / 2.0 + 1
        y = rect.top() + (rect.height() - size) / 2.0
        name = "chevron-down" if item.isExpanded() else "chevron-right"
        painter.drawPixmap(QtCore.QPointF(x, y), icon_pixmap(name, self._colors["muted_text"], size,
                                                             device_pixel_ratio(self)))


class DropZone(QtWidgets.QFrame, Themed):
    """See the module. `extensions`: the endings it takes (".png"); `title`: what to drop."""

    dropped = Signal(list)

    def __init__(self, theme, extensions, title="Drop images here", parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setObjectName("toolDropZone")
        self.setProperty("state", "")
        self.setAcceptDrops(True)
        self.extensions = tuple(extension.lower() for extension in extensions)
        names = [extension.lstrip(".").upper() for extension in self.extensions]
        self.kinds = names[0] if len(names) == 1 else "{} or {}".format(", ".join(names[:-1]), names[-1])
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(space(16), space(16), space(16), space(16))
        layout.setSpacing(space(6))
        self.glyph = QtWidgets.QLabel()
        self.glyph.setFixedSize(px(28), px(28))
        layout.addWidget(self.glyph, 0, Qt.AlignHCenter)
        self.title = QtWidgets.QLabel(title)
        self.title.setObjectName("toolDropTitle")
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)
        self.hint = QtWidgets.QLabel("{}, or choose them".format(self.kinds))
        self.hint.setObjectName("toolMuted")
        self.hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint)
        self.browse = Button("Browse…", theme, icon="folder-open")
        self.browse.clicked.connect(self._browse)
        layout.addSpacing(space(4))
        layout.addWidget(self.browse, 0, Qt.AlignHCenter)
        self._default = (title, self.hint.text())
        self.bind_theme(theme)

    def _on_theme(self, colors):
        state = self.property("state")
        role = {"over": "accent", "reject": "log_error"}.get(state, "muted_text")
        self.glyph.setPixmap(icon_pixmap("upload", colors[role], px(28), device_pixel_ratio(self)))

    def _set_state(self, state, title=None, hint=None):
        self.setProperty("state", state)
        repolish(self)
        self.title.setText(title or self._default[0])
        self.hint.setText(hint or self._default[1])
        self._on_theme(self._theme.colors)

    def _paths(self, event):
        data = event.mimeData()
        if not data.hasUrls():
            return [], []
        local = [url.toLocalFile() for url in data.urls() if url.isLocalFile()]
        good = [path for path in local if os.path.splitext(path)[1].lower() in self.extensions]
        return good, [path for path in local if path not in good]

    def dragEnterEvent(self, event):
        good, bad = self._paths(event)
        if good:
            count = len(good)
            self._set_state("over", "Drop {} file{}".format(count, "" if count == 1 else "s"),
                            "{} other file{} will be skipped".format(len(bad), "" if len(bad) == 1 else "s")
                            if bad else self._default[1])
            event.acceptProposedAction()
        else:
            self._set_state("reject", "These files cannot be used", "Only {}".format(self.kinds))
            # Taken without a drop action: Qt then sends the leave (and the move, which shows "not allowed"); a drag
            # ignored here would never tell the zone it left, and the red state would stay
            event.setDropAction(Qt.IgnoreAction)
            event.accept()

    def dragMoveEvent(self, event):
        good, _bad = self._paths(event)
        if good:
            event.acceptProposedAction()
        else:
            event.ignore()  # The "not allowed" pointer

    def dragLeaveEvent(self, event):
        self._set_state("")
        QtWidgets.QFrame.dragLeaveEvent(self, event)

    def dropEvent(self, event):
        good, _bad = self._paths(event)
        self._set_state("")
        if good:
            event.acceptProposedAction()
            self.dropped.emit(good)

    def take(self, paths):
        """The same as a drop, from code (a test, or a list the user pasted)."""
        good = [path for path in paths if os.path.splitext(path)[1].lower() in self.extensions]
        if good:
            self.dropped.emit(good)
        return good

    def _browse(self):
        patterns = " ".join("*" + extension for extension in self.extensions)
        paths, _filter = QtWidgets.QFileDialog.getOpenFileNames(self.window(), "Choose files", "",
                                                                "{} ({})".format(self.kinds, patterns))
        if paths:
            self.take(paths)
```
