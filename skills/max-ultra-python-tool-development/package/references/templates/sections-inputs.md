# Template: Sections and inputs

Pages with one chooser in two styles (`sections.py`: tabs on top for up to three sections, a list on the left with icons and a red destructive item from four, as the MaxPkg Package Manager's Settings; `choose_side` picks the style) and the input helpers beyond a plain field (`inputs.py`: `SearchBox` with the search glyph, a clear x and suggestions; `CopyButton` that turns into a green check; `ClearableComboBox` with an x while a filter is on; `ListEditor` to add, paste, edit, reorder and remove short values). The completer of `SearchBox` belongs to the window (`owner`), never to the field: see [max reliability](../max-reliability.md).

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) through Max Ultra MCP with the windows off screen (the controls trainer checks), and shown on screen in 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3).

## `python/mytool/ui/sections.py`

```python
"""Pages with one chooser, in two styles, for Settings and for any window with several sections.

* Tabs on top (`side=False`): for two or three short sections; the familiar look of the Settings window.
* A list on the left (`side=True`), as in the MaxPkg Package Manager's Settings: a narrow column of buttons with a
  Lucide icon and the name, the chosen one highlighted, a red one for a destructive section (Uninstall, Reset); the
  page shows its title on top and scrolls. For four sections or more, or names too long for tabs.
`choose_side(count)` gives the default: the list from four sections. Both styles take the same calls, so a tool
switches with one argument:

    book = SectionBook(theme, side=choose_side(len(PAGES)))
    layout = book.add_page("updates", "Updates", "refresh-cw")
    layout.addWidget(...)
"""

from ..qt_compat import QtCore, QtWidgets, Qt, Signal
from ..ui_scale import px, space
from .controls import Button, fade_edges

SIDE_FROM = 4  # Four sections or more: the list on the left


def choose_side(count):
    return count >= SIDE_FROM


class NavButton(Button):
    """A section in the list on the left: icon and name, muted until chosen; `danger` makes it red."""

    def __init__(self, text, theme, icon, danger=False):
        self._danger = danger
        Button.__init__(self, text, theme, icon=icon, variant="ghost")
        self.setObjectName("toolNavButton")
        self.setCheckable(True)
        self.setAutoExclusive(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setProperty("danger", "true" if danger else "false")
        self.icon_px = 15
        self.toggled.connect(lambda _on: self._on_theme(self._theme.colors))

    def _on_theme(self, colors):
        self.icon_role = "log_error" if self._danger else ("text" if self.isChecked() else "muted_text")
        Button._on_theme(self, colors)


class SectionBook(QtWidgets.QWidget):
    """See the module. `changed(key)` when another section is chosen."""

    changed = Signal(str)

    def __init__(self, theme, side=False, nav_width=168, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.theme = theme
        self.side = side
        self.keys = []
        self.buttons = {}
        self._current = ""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if side:
            self.nav = QtWidgets.QFrame()
            self.nav.setObjectName("toolNav")
            self.nav.setFixedWidth(px(nav_width))
            self.nav_layout = QtWidgets.QVBoxLayout(self.nav)
            self.nav_layout.setContentsMargins(space(12), space(12), space(12), space(12))
            self.nav_layout.setSpacing(space(2))
            self.nav_layout.addStretch(1)
            self.stack = QtWidgets.QStackedWidget()
            layout.addWidget(self.nav)
            layout.addWidget(self.stack, 1)
        else:
            self.tabs = QtWidgets.QTabWidget()
            self.tabs.setDocumentMode(False)
            self.tabs.currentChanged.connect(self._tab_changed)
            layout.addWidget(self.tabs)

    def add_page(self, key, title, icon="", danger=False):
        """A new section; returns the layout to fill (a scrolling page with the title on top in the list style)."""
        page = QtWidgets.QWidget()
        page.setObjectName("toolPage")
        inner = QtWidgets.QVBoxLayout(page)
        self.keys.append(key)
        if self.side:
            inner.setContentsMargins(space(16), space(16), space(16), space(16))
            inner.setSpacing(space(12))
            heading = QtWidgets.QLabel(title)
            heading.setObjectName("toolPageTitle")
            inner.addWidget(heading)
            area = QtWidgets.QScrollArea()
            area.setWidgetResizable(True)
            area.setFrameShape(QtWidgets.QFrame.NoFrame)
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            area.setWidget(page)
            fade_edges(area, self.theme)  # The page fades out at a clipped top or bottom edge
            self.stack.addWidget(area)
            button = NavButton(title, self.theme, icon, danger)
            button.clicked.connect(lambda _checked=False, name=key: self.show_page(name))
            self.nav_layout.insertWidget(self.nav_layout.count() - 1, button)
            self.buttons[key] = button
            if len(self.keys) == 1:
                self.show_page(key)
        else:
            inner.setContentsMargins(space(12), space(12), space(12), space(12))
            inner.setSpacing(space(12))
            self.tabs.addTab(page, title)
        return inner

    def show_page(self, key):
        if key not in self.keys:
            return
        index = self.keys.index(key)
        if self.side:
            for name, button in self.buttons.items():
                button.setChecked(name == key)
            self.stack.setCurrentIndex(index)
            changed = key != self._current
            self._current = key
            if changed:
                self.changed.emit(key)
        else:
            self.tabs.setCurrentIndex(index)

    def current(self):
        return self._current

    def set_page_visible(self, key, visible):
        """Hide a section that does not apply (Endpoint without developer mode); a hidden current section moves to
        the first one."""
        if key not in self.keys:
            return
        index = self.keys.index(key)
        if self.side:
            self.buttons[key].setVisible(visible)
        elif hasattr(self.tabs, "setTabVisible"):
            self.tabs.setTabVisible(index, visible)
        if not visible and self._current == key:
            self.show_page(self.keys[0])

    def _tab_changed(self, index):
        if 0 <= index < len(self.keys) and self.keys[index] != self._current:
            self._current = self.keys[index]
            self.changed.emit(self._current)


def page_row(*widgets):
    """Widgets side by side, left aligned (a button row on a page)."""
    row = QtWidgets.QHBoxLayout()
    row.setSpacing(space(8))
    for widget in widgets:
        row.addWidget(widget)
    row.addStretch(1)
    return row
```

## `python/mytool/ui/inputs.py`

```python
"""Input helpers beyond the plain field: search with suggestions, copy with a visible "copied", a dropdown that can go
back to its default, and an editor for a list of short values.

* SearchBox: the search glyph at the left, a clear x at the right while there is text (Esc clears too), suggestions
  in the tool's rounded popup as you type (SuggestionDelegate), `search(text)` after a short pause or on Enter.
* CopyButton: a square copy button; after a click its icon turns into a green check for a moment and the tooltip says
  "Copied". Pair it with a toast only when the copy happens out of sight.
* ClearableComboBox: a dropdown with a small x that appears while a filter differs from its default ("Any type"); the
  field's outline shows that a filter is on.
* MultiSelectList: pick several items by pressing and dragging over them (as a MAXScript multiListBox), Ctrl and
  Shift clicks, Ctrl+A; the order never changes.
* ListEditor: add values one by one (Enter) or paste many lines, edit with a double click, drag to reorder, Delete or
  the row menu to remove; duplicates and invalid values are refused with the reason under the field.
"""

from ..qt_compat import (QShortcut, QtCore, QtGui, QtWidgets, Qt, Signal, device_pixel_ratio, inherit_fonts, is_valid,
                         repolish, scale_font)
from ..ui_scale import px, space
from . import controls
from .controls import Button, ComboBox, SuggestionDelegate, Themed, icon_pixmap, round_popup


class SearchBox(QtWidgets.QLineEdit, Themed):
    """See the module. `suggestions`: the values offered while typing (contains, case-insensitive). `owner`: the
    window that owns the suggestions.

    The completer, its model and its list belong to `owner`, never to the field itself, and the list is created
    here and handed over with setPopup (TerraScoop's pattern, proven inside 3ds Max). A completer that was a child of
    its own line edit took 3ds Max 2022 down with a heap corruption once the window showed."""

    search = Signal(str)
    PAUSE_MS = 300

    def __init__(self, theme, placeholder="Search", suggestions=(), owner=None, parent=None):
        QtWidgets.QLineEdit.__init__(self, parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(False)
        self.glyph = QtWidgets.QLabel(self)
        self.glyph.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.clear_button = Button("", theme, icon="x", variant="ghost", tooltip="Clear (Esc)", parent=self)
        self.clear_button.setObjectName("toolFieldClear")
        self.clear_button.icon_px = 14
        self.clear_button.setFocusPolicy(Qt.NoFocus)
        self.clear_button.clicked.connect(self.clear)
        self.clear_button.hide()
        self._pause = QtCore.QTimer(self)
        self._pause.setSingleShot(True)
        self._pause.setInterval(self.PAUSE_MS)
        self._pause.timeout.connect(lambda: self.search.emit(self.text().strip()))
        self.textChanged.connect(self._changed)
        self.returnPressed.connect(lambda: (self._pause.stop(), self.search.emit(self.text().strip())))
        self.model = QtCore.QStringListModel(list(suggestions), owner)
        self.completer = QtWidgets.QCompleter(self.model, owner)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setMaxVisibleItems(8)
        view = QtWidgets.QListView()  # The list continues the field: the tool's rounded popup
        view.setObjectName("toolPopup")
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setUniformItemSizes(True)
        view.setMouseTracking(True)
        self.completer.setPopup(view)
        # After setPopup, which installs QCompleter's own delegate
        self._delegate = SuggestionDelegate(self, lambda: self._theme.colors, view)
        view.setItemDelegate(self._delegate)
        view.setWindowFlags(view.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.popup_view = view  # Before the filter: PySide6 may call it at once
        view.installEventFilter(self)  # Style, font and rounded corners when it opens
        self.setCompleter(self.completer)
        self.bind_theme(theme)

    def set_suggestions(self, values):
        self.model.setStringList(list(values))

    def _changed(self, text):
        self.clear_button.setVisible(bool(text))
        self._pause.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.text() and not self.completer.popup().isVisible():
            self.clear()
            return
        QtWidgets.QLineEdit.keyPressEvent(self, event)

    def eventFilter(self, watched, event):
        if watched is self.popup_view and event.type() == QtCore.QEvent.Show:
            # A popup window of its own: the tool window's style sheet and interface-size font do not reach it
            watched.setStyleSheet(self._theme.stylesheet)
            scale_font(watched)
            inherit_fonts(watched)
            QtCore.QTimer.singleShot(0, lambda: round_popup(watched) if is_valid(watched) and watched.isVisible()
                                     else None)
        return False

    def _on_theme(self, colors):
        size = px(16)
        self.glyph.setPixmap(icon_pixmap("search", colors["muted_text"], size, device_pixel_ratio(self)))
        self.glyph.setFixedSize(size, size)
        self.setTextMargins(px(22), 0, px(22), 0)
        self._place()

    def resizeEvent(self, event):
        QtWidgets.QLineEdit.resizeEvent(self, event)
        self._place()

    def _place(self):
        self.glyph.move(px(8), (self.height() - self.glyph.height()) // 2)
        size = self.height() - px(8)
        self.clear_button.setGeometry(self.width() - size - px(4), px(4), size, size)


class CopyButton(Button):
    """See the module. `text`: the value to copy, or a callable that returns it."""

    copied = Signal(str)
    DONE_MS = 1400

    def __init__(self, theme, text, tooltip="Copy", parent=None):
        Button.__init__(self, "", theme, icon="copy", tooltip=tooltip, parent=parent)
        self._text = text
        self._tooltip = tooltip
        self._done = QtCore.QTimer(self)
        self._done.setSingleShot(True)
        self._done.setInterval(self.DONE_MS)
        self._done.timeout.connect(self._reset)
        self.clicked.connect(self._copy)

    def _copy(self):
        value = self._text() if callable(self._text) else self._text
        QtWidgets.QApplication.clipboard().setText(value)
        self.icon_name, self.icon_role = "check", "log_success"
        self._on_theme(self._theme.colors)
        controls.set_style_property(self, "done", "true")  # The outline turns green with the check
        self.setToolTip("Copied")
        self._done.start()
        self.copied.emit(value)

    def _reset(self):
        self.icon_name, self.icon_role = "copy", None
        self._on_theme(self._theme.colors)
        controls.set_style_property(self, "done", "false")
        self.setToolTip(self._tooltip)

    def is_showing_done(self):
        return self._done.isActive()


class ClearableComboBox(QtWidgets.QWidget):
    """See the module. `choices`: (value, label) pairs; `default`: the value that means "no filter"."""

    changed = Signal(object)

    def __init__(self, theme, choices, default, tooltip="", parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.default = default
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(space(4))
        self.combo = ComboBox()
        for value, label in choices:
            self.combo.addItem(label, value)
        self.combo.setCurrentIndex(max(0, self.combo.findData(default)))
        if tooltip:
            self.combo.setToolTip(tooltip)
        self.clear_button = Button("", theme, icon="x", tooltip="Back to {}".format(self.combo.currentText()))
        self.clear_button.clicked.connect(lambda: self.set_value(self.default, emit=True))
        layout.addWidget(self.combo, 1)
        layout.addWidget(self.clear_button)
        self.combo.currentIndexChanged.connect(lambda _index: (self._sync(), self.changed.emit(self.value())))
        self._sync()

    def value(self):
        return self.combo.currentData()

    def set_value(self, value, emit=False):
        self.combo.blockSignals(True)
        self.combo.setCurrentIndex(max(0, self.combo.findData(value)))
        self.combo.blockSignals(False)
        self._sync()
        if emit:
            self.changed.emit(self.value())

    def _sync(self):
        active = self.value() != self.default
        self.clear_button.setVisible(active)
        if (self.combo.property("active") == "true") != active:
            self.combo.setProperty("active", "true" if active else "false")  # An accent outline: a filter is on
            repolish(self.combo)


class ListEditor(QtWidgets.QWidget, Themed):
    """See the module. `check(value)` returns "" or why the value is refused (beside the duplicate rule)."""

    changed = Signal(list)

    def __init__(self, theme, placeholder="Add a value", values=(), check=None, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._check = check or (lambda value: "")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(space(4))
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(6))
        self.field = QtWidgets.QLineEdit()
        self.field.setPlaceholderText(placeholder)
        self.field.returnPressed.connect(self.add_from_field)
        self.field.textChanged.connect(lambda _text: self._show_error(""))
        self.add_button = Button("Add", theme, icon="plus", tooltip="Add the value (Enter)")
        self.add_button.clicked.connect(self.add_from_field)
        paste = Button("", theme, icon="clipboard-paste", tooltip="Paste many values, one per line")
        paste.clicked.connect(self.paste_lines)
        row.addWidget(self.field, 1)
        row.addWidget(self.add_button)
        row.addWidget(paste)
        layout.addLayout(row)
        self.error = QtWidgets.QLabel("")
        self.error.setObjectName("toolError")
        self.error.setWordWrap(True)
        self.error.hide()
        layout.addWidget(self.error)
        self.list = QtWidgets.QListWidget()
        self.list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.list.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._menu)
        self.list.model().rowsMoved.connect(lambda *_: self._emit())
        self.list.itemChanged.connect(self._edited)
        delete = QShortcut(QtGui.QKeySequence(Qt.Key_Delete), self.list)
        delete.setContext(Qt.WidgetShortcut)
        delete.activated.connect(self.remove_current)
        layout.addWidget(controls.boxed(self.list), 1)
        foot = QtWidgets.QHBoxLayout()
        self.count = controls.muted("", wrap=False)
        foot.addWidget(self.count, 1)
        clear = controls.StatusAction("Remove All", theme, "trash-2", tooltip="Remove every value")
        clear.clicked.connect(self.clear_all)
        foot.addWidget(clear)
        layout.addLayout(foot)
        self._editing = False
        for value in values:
            self._append(value)
        self._emit()
        self.bind_theme(theme)

    def values(self):
        return [self.list.item(row).text() for row in range(self.list.count())]

    def _append(self, value):
        item = QtWidgets.QListWidgetItem(value)
        item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled)
        self._editing = True
        self.list.addItem(item)
        self._editing = False
        return item

    def _problem(self, value, ignore_row=-1):
        if not value:
            return "Type a value first"
        lowered = value.lower()
        for row in range(self.list.count()):
            if row != ignore_row and self.list.item(row).text().lower() == lowered:
                return "{} is already in the list".format(value)
        return self._check(value)

    def _show_error(self, text):
        self.error.setText(text)
        self.error.setVisible(bool(text))
        invalid = "true" if text else "false"
        if self.field.property("invalid") != invalid:
            self.field.setProperty("invalid", invalid)
            repolish(self.field)

    def add_from_field(self):
        value = self.field.text().strip()
        problem = self._problem(value)
        if problem:
            self._show_error(problem)
            return False
        self.list.setCurrentItem(self._append(value))
        self.field.clear()
        self._emit()
        return True

    def paste_lines(self, text=None):
        """Add every new, valid line of the clipboard (or `text`); says how many were skipped."""
        text = QtWidgets.QApplication.clipboard().text() if text is None else text
        added, skipped = 0, 0
        for line in text.splitlines():
            value = line.strip()
            if not value:
                continue
            if self._problem(value):
                skipped += 1
            else:
                self._append(value)
                added += 1
        self._emit()
        self._show_error("" if not skipped else "{} line{} skipped: duplicates or not valid".format(
            skipped, "" if skipped == 1 else "s"))
        return added, skipped

    def _edited(self, item):
        if self._editing:
            return
        value = item.text().strip()
        problem = self._problem(value, self.list.row(item))
        if problem:
            self._show_error(problem)
            self._editing = True
            item.setText(item.data(Qt.UserRole) or "")
            self._editing = False
            return
        self._editing = True
        item.setText(value)
        item.setData(Qt.UserRole, value)
        self._editing = False
        self._emit()

    def remove_current(self):
        item = self.list.currentItem()
        if item is not None:
            self.list.takeItem(self.list.row(item))
            self._emit()

    def clear_all(self):
        if self.list.count():
            self.list.clear()
            self._emit()

    def _menu(self, position):
        item = self.list.itemAt(position)
        if item is None:
            return
        self.list.setCurrentItem(item)
        menu = controls.Menu(self._theme, self)
        menu.add_item("Edit", "pencil", lambda: self.list.editItem(item))
        menu.add_item("Copy", "copy", lambda: QtWidgets.QApplication.clipboard().setText(item.text()))
        menu.addSeparator()
        menu.add_item("Remove", "trash-2", self.remove_current, danger=True)
        menu.popup_at(self.list.viewport().mapToGlobal(position))

    def _emit(self):
        for row in range(self.list.count()):
            item = self.list.item(row)
            self._editing = True
            item.setData(Qt.UserRole, item.text())  # What an invalid edit falls back to
            self._editing = False
        count = self.list.count()
        self.count.setText("No values yet" if not count else "{} value{}".format(count, "" if count == 1 else "s"))
        self.changed.emit(self.values())


class MultiSelectList(QtWidgets.QWidget, Themed):
    """A list where several items are picked, as 3ds Max's multiListBox: press on an item and drag up or down to
    select the run of items under the pointer (the list scrolls by itself at its edges), Ctrl+click adds or removes
    one, Shift+click extends to it, Ctrl+A selects all. The items keep their order: nothing can be dragged to another
    place. Below it: how many are selected, Select All and Select None. `changed(texts)` with the selected texts in
    list order."""

    changed = Signal(list)

    def __init__(self, theme, items=(), parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(space(4))
        self.list = QtWidgets.QListWidget()
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)  # Press and drag selects a run
        self.list.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)  # Never reordered by a drag
        self.list.setDragEnabled(False)
        self.list.setAutoScroll(True)
        self.list.itemSelectionChanged.connect(self._changed)
        controls.fade_edges(self.list, theme, "field")
        layout.addWidget(controls.boxed(self.list), 1)
        foot = QtWidgets.QHBoxLayout()
        foot.setSpacing(space(8))
        self.count = controls.muted("", wrap=False)
        foot.addWidget(self.count, 1)
        self.all_button = controls.StatusAction("Select All", theme, "check", tooltip="Select every item (Ctrl+A)")
        self.all_button.clicked.connect(self.list.selectAll)
        self.none_button = controls.StatusAction("Select None", theme, "x", tooltip="Clear the selection")
        self.none_button.clicked.connect(self.list.clearSelection)
        foot.addWidget(self.all_button)
        foot.addWidget(self.none_button)
        layout.addLayout(foot)
        self.set_items(items)
        self.bind_theme(theme)

    def set_items(self, items):
        self.list.clear()
        self.list.addItems(list(items))
        self._changed()

    def selected(self):
        return [self.list.item(row).text() for row in range(self.list.count()) if self.list.item(row).isSelected()]

    def select(self, texts):
        wanted = set(texts)
        for row in range(self.list.count()):
            item = self.list.item(row)
            item.setSelected(item.text() in wanted)

    def _changed(self):
        chosen = self.selected()
        total = self.list.count()
        self.count.setText("{} of {} selected".format(len(chosen), total) if chosen else "{} items".format(total))
        self.none_button.setEnabled(bool(chosen))
        self.all_button.setEnabled(len(chosen) < total)
        self.changed.emit(chosen)


PICK_KINDS = {"camera": "camera", "light": "light", "geometry": "GeometryClass", "shape": "shape"}


def pick_in_viewport(kind=None, message="Pick an object"):
    """3ds Max's own pick mode (MAXScript pickObject, on the main thread): the pointer becomes the pick cursor over the
    viewports and the message shows in Max's prompt line; a click on an object picks it, Esc or a right click cancels.
    Returns (anim handle, name) of the picked node, or None (cancelled, the wrong kind, or outside Max)."""
    try:
        from pymxs import runtime as rt
    except ImportError:
        return None
    node = rt.pickObject(message=message)
    if node is None:
        return None
    wanted = PICK_KINDS.get(kind)
    if wanted is not None and rt.superClassOf(node) != getattr(rt, wanted):
        return None
    return int(rt.getHandleByAnim(node)), str(node.name)


class PickButton(Button):
    """Pick an object in a viewport, as MAXScript's pickbutton: a field-look button with the Lucide crosshair. A click
    shows "Click an object in a viewport" in the accent colour and starts 3ds Max's own pick mode; the picked object's
    name then stands on the button and a small x clears it. `kind`: None, "camera", "light", "geometry" or "shape".
    `picked((handle, name) or None)`. Keep the anim handle, never the node: the scene may change before it is used.
    `pick` replaces the pick mode in tests (it must never wait for a click there)."""

    picked = Signal(object)

    def __init__(self, theme, prompt="Pick an object", kind=None, pick=None, parent=None):
        Button.__init__(self, prompt, theme, icon="crosshair", variant="field",
                        tooltip="Click, then click an object in a viewport (Esc cancels)", parent=parent)
        self._prompt, self._kind = prompt, kind
        self._pick = pick or (lambda which: pick_in_viewport(which, prompt))
        self.node = None
        self.clear_button = Button("", theme, icon="x", variant="ghost", tooltip="Clear", parent=self)
        self.clear_button.setObjectName("toolFieldClear")
        self.clear_button.icon_px = 14
        self.clear_button.setFocusPolicy(Qt.NoFocus)
        self.clear_button.clicked.connect(self.clear)
        self.clear_button.hide()
        self.clicked.connect(self.start)

    def start(self):
        self.setProperty("picking", "true")
        repolish(self)
        Button.setText(self, "Click an object in a viewport")
        QtCore.QTimer.singleShot(30, self._run)  # The button shows it is picking before Max's pick mode starts

    def _run(self):
        try:
            result = self._pick(self._kind)
        finally:
            self.setProperty("picking", "false")
            repolish(self)
        if result:
            self.node = result
            self.picked.emit(result)
        self._sync()

    def clear(self):
        self.node = None
        self._sync()
        self.picked.emit(None)

    def _sync(self):
        Button.setText(self, self.node[1] if self.node else self._prompt)
        self.clear_button.setVisible(self.node is not None)
        self._place()

    def resizeEvent(self, event):
        Button.resizeEvent(self, event)
        self._place()

    def _place(self):
        size = self.height() - px(8)
        self.clear_button.setGeometry(self.width() - size - px(4), px(4), size, size)
```
