# Template: Main window example

The controls trainer: a main window built on the tool window that shows every shared control in one design, in eleven sections chosen from a list on the left (`SectionBook(side=True)`). **Fields**: panels with a required star and help balloons, required fields with the error bubble, Major / Minor / Patch steppers, the date picker, a date with a time and a time alone, the badge dropdown, a read-only ID with Copy and a menu, a folder field, collapsible groups, a drop zone. **Choices**: segments, switches, check boxes, dropdowns (plain, clearable, with icons, with groups, editable, with check boxes), scene picks, choice cards, every button variant, pills, warning blocks. **Sliders & Colours**, **Badges**, **Lists** (search with its empty state in place, a list with a menu, a multi-select list, the list editor, a table, a scene tree), **Cards & Gallery**, **Charts** (stat tiles, column, line and donut charts), **Feedback** (toasts, the busy overlay, result cards, empty states), **Loading** (spinners, a busy button, skeleton rows, a progress ring, wizard steps), **Windows** (messages, questions, prompts, Settings as tabs or a list, Welcome, Logs, About) and **Donations**. Below: the mini log with statuses only, View Logs, the state pill, the progress bar while working, the rotating link and the primary action with a background job that ends on the result card. It is a gallery: a real tool takes only the controls its task needs.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP, with the windows off screen.

## `python/mytool/ui/main_window.py`

```python
"""The tool's main window: ToolWindow (title bar, collapse, status bar) plus the tool's own content.

This demo content is the controls trainer: every shared control in one design, in sections chosen from a list on the
left (sections.SectionBook, the style for many sections):

* Fields: required fields checked while typing, error bubbles, version steppers, the date picker (months and years,
  a date with a time, a time alone), the badge dropdown, help balloons, collapsible groups, web addresses, a read-only
  ID with copy and a menu, a folder field, a place to drop files.
* Choices: segments, switches, check boxes, dropdowns (with icons, with groups, editable, with check boxes), a filter
  dropdown that can be cleared, scene picks, choices as cards, every button variant enabled and disabled, icon
  squares, pills, warning blocks.
* Sliders and colours: one-handle and two-handle sliders, colour pickers with presets and recent colours.
* Badges: count badges on buttons, status badges, removable tags, status dots.
* Lists: search with suggestions, a list with a menu and drag to reorder, a list to pick several items by
  dragging over them, the list editor, layer chips, a table, a scene tree.
* Cards and gallery: filter pills above a responsive card grid (with an empty state), a picture gallery with
  thumbnails and its lightbox.
* Charts: stat tiles with a change and a sparkline, a column chart, a line chart, a donut.
* Feedback: toasts, the busy overlay, result cards, empty states, the progress bar.
* Loading: spinners (inline, in a button, large), skeleton rows, a progress ring, wizard steps.
* Windows: the tool's own messages, questions and prompts, Settings as tabs or as a list, Welcome, Logs, About, and
  the tool without its window (api.py: the same operations for MAXScript, scripts and AI assistants).
* Donations: every place a donation can be offered (donation.py).
Below the sections: the mini log (statuses only); in the bottom strip View Logs, the state pill, the progress bar while
working and the primary action.

It is a gallery, not a layout to copy: a real tool takes only the controls its task needs (see "Choosing controls" in
the controls catalog). Replace the sections with the tool's own; keep the patterns.
"""

import datetime
import json
import time

from .. import DONATE_URL, TOOL_NAME, api
from ..qt_compat import QShortcut, QtCore, QtGui, QtWidgets, Qt, repolish
from ..ui_scale import pt, px, space
from . import controls, forms
from .badges import CountBadge, Dot, FilterPills, StatusBadge, Tag
from .cards import Card, CardGrid, demo_picture
from .charts import BarChart, DonutChart, LineChart, StatTile
from .colors import ColorButton
from .combos import GroupedComboBox, IconComboBox, MultiComboBox, RadioCards, editable_combo
from .gallery import Gallery, open_lightbox
from .dialogs import ConfirmDialog, SettingsDialog, ask, ask_text, how_to_card, inform
from .inputs import ClearableComboBox, CopyButton, ListEditor, MultiSelectList, PickButton, SearchBox
from .loading import ProgressRing, Skeleton, Spinner, Steps, busy
from .pickers import DateField, Stepper, TimeEdit
from .sections import SectionBook
from .sliders import RangeSlider, Slider
from .states import BusyOverlay, EmptyState, ResultCard, StateArea
from .statuslog import StatusLog, monospace
from .switch import Switch
from .tool_window import ToolWindow
from .tree import DropZone, SceneTree

SECTIONS = (("fields", "Fields", "pencil"), ("choices", "Choices", "sliders-horizontal"),
            ("sliders", "Sliders & Colours", "palette"), ("badges", "Badges", "tag"),
            ("lists", "Lists", "logs"), ("cards", "Cards & Gallery", "layout-grid"),
            ("charts", "Charts", "chart-column"), ("feedback", "Feedback", "circle-check"),
            ("loading", "Loading", "loader"), ("windows", "Windows", "copy"), ("donations", "Donations", "heart"))
BADGES = (("Added", "log_success"), ("Fixed", "log_warning"), ("Changed", "log_info"), ("Removed", "log_error"),
          ("Improved", "log_system"))
# Help texts (controls.help_html): one idea per block, few words; **term** at the start of a block, `code` for names.
HELP = {
    "dropdowns": ("Dropdowns", "**Icons** help when the items differ in kind.\n\n**Groups**: the headings cannot be "
                               "chosen.\n\n**Editable**: pick or type a new value.\n\n**Check boxes**: the list "
                               "stays open while you tick; the field sums it up."),
    "radio": ("Choices as cards", "For two to four choices whose difference needs a sentence. The arrow keys move the "
                                  "choice."),
    "tree": ("Scene tree", "**Click a chevron** or double-click a layer to open it.\n\nA layer's box ticks all of "
                           "its objects; it shows a dash when only some are ticked."),
    "drop": ("Files", "Drag files from Explorer onto the area, or click **Browse**. The area says at once whether it "
                      "takes them."),
    "charts": ("Charts", "Point at a column, a line or a part of the donut for its exact value.\n\nThe colours come "
                         "in a fixed order; a legend names them when there are two or more."),
    "api": ("Without the window", "Every operation of the tool is also an **API** call: MAXScript, Python and AI "
                                  "assistants (through Max Ultra MCP) use it with no window open.\n\n"
                                  "`describe` lists the operations; a call that changes the scene takes `dry_run`."),
    "loading": ("Loading", "**Spinner**: something short is on its way.\n\n**Skeleton**: the layout of what comes, "
                           "so nothing jumps.\n\n**Ring**: the share done, when it is known."),
    "result": ("Result", "**Name**: the public name of the result.\n\n"
                         "**Type**: a coloured badge, as in the changelog.\n\n"
                         "Names allow `A-Z a-z 0-9`, space, `-` and `_`."),
    "links": ("Links", "Shown in About and on the download page.\n\n"
                       "**Homepage** is optional. A site typed without `https://` gets it."),
    "channel": ("Release channel", "**Stable**: the release for everyone.\n\n"
                                   "**Beta** and **Alpha**: test versions, for testers only."),
    "options": ("Options", "What the tool does with the scene.\n\n"
                           "**Switches** turn one thing on or off. **Check boxes** pick items of a list.\n\n"
                           "Hover a control for details."),
    "buttons": ("Buttons and status", "**Primary**: the one main action of a panel.\n\n"
                                      "**Danger**: removes something.\n\n"
                                      "A disabled coloured button keeps a shade of its colour."),
    "results": ("Results", "Right-click a row for its menu: the arrow keys move in it, **Enter** runs an item, "
                           "**Esc** closes it. The keys at the right work without the menu too.\n\n"
                           "**Delete** is red and last; it asks first, it cannot be undone. Drag rows to reorder."),
    "sliders": ("Sliders", "**One handle** sets a value, **two handles** a range.\n\n"
                           "Drag, click the track, or use the arrow keys. The wheel scrolls the page."),
    "colors": ("Colours", "Click a colour to open the picker: the square, the hue strip, a hex value, the presets and "
                          "the recent colours.\n\n**Esc** puts the colour back."),
    "several": ("Pick several", "**Press and drag** over the rows to select a run, as in a MAXScript multiListBox.\n\n"
                                "**Ctrl+click** adds or removes one, **Shift+click** extends, **Ctrl+A** selects all.\n\n"
                                "The order never changes."),
    "picks": ("Scene picks", "Click the button, then click an object in a viewport: its name stands on the button.\n\n"
                             "**Esc** or a right click cancels; the **x** clears it.\n\n"
                             "**Camera** accepts cameras only."),
    "editor": ("List editor", "**Enter** adds the value; the paste button adds many lines at once.\n\n"
                              "Double-click a value to edit it. Duplicates are refused."),
    "feedback": ("Feedback", "**Toasts** tell the outcome of a small action.\n\n"
                             "**The result card** ends a main operation.\n\n"
                             "**The busy overlay** blocks the area while work runs."),
}
CARDS = (
    ("Interior Lighting", "Soft daylight with warm lamps for living rooms and kitchens.", "sparkles", "accent",
     ("New", "log_info"), "interior", "12 presets"),
    ("Exterior Dusk", "Low sun and blue hour for facades and gardens.", "globe", "log_warning", None, "exterior",
     "8 presets"),
    ("Product Studio", "Three-point light on a seamless background.", "box", "log_system", ("Pro", "log_system"),
     "studio", "5 presets"),
    ("Clay Render", "Neutral grey materials to judge the shapes.", "palette", "log_success", None, "studio",
     "3 presets"),
    ("Night Street", "Street lamps, wet asphalt, light from windows.", "star", "log_error", ("Beta", "log_warning"),
     "exterior", "6 presets"),
    ("Kitchen Close-up", "Shallow depth of field for details.", "zoom-in", "accent", None, "interior", "4 presets"),
)
CATEGORIES = (("", "All presets", "package", "#3280dd"), ("interior", "Interior", "sparkles", "#d38d50"),
              ("exterior", "Exterior", "globe", "#4aa37a"), ("studio", "Studio", "box", "#9b6bd6"))
LAYER_NAMES = ("Walls", "Floors", "Roofs", "Doors", "Windows", "Furniture", "Lights", "Cameras", "Helpers")
DONATION_NOTE = "If {} saved you time, a small donation keeps it going.".format(TOOL_NAME)


def _counter_text(text):
    return "{} / 300 characters".format(len(text))


class MainWindow(ToolWindow):
    def __init__(self, controller, parent=None):
        ToolWindow.__init__(self, controller, parent)
        theme = self.theme = controller.theme
        self.resize(px(1080), px(700))
        self.book = SectionBook(theme, side=True)  # Eleven sections: a list on the left, never eleven tabs
        self.pages = {}
        for key, title, icon in SECTIONS:
            page = self.book.add_page(key, title, icon)
            getattr(self, "_build_" + key)(page)
            page.addStretch(1)
            self.pages[key] = page
        self.body.addWidget(self.book, 1)
        self.fields_badge = CountBadge(self.book.buttons["fields"], theme)  # How many fields to fix
        self.busy = BusyOverlay(self.book, theme)  # Blocks the sections while work runs
        self.busy.cancelled.connect(self.cancel_busy)
        self.result_card = ResultCard(self.book, theme)  # The outcome of a main operation

        # The mini log: statuses only (errors and warnings, or one green line); the history is in the Logs window.
        self.log = StatusLog(theme)
        self.log.setFixedHeight(px(78))  # About three rows
        self.log.tab_requested.connect(self.go_to_field)
        self.body.addWidget(self.log)
        # The bottom strip: the state pill, the message (the progress bar takes its place while working), the primary
        # action pinned at the bottom, then Settings, About and Donate (View Logs is first on the left).
        self.state_pill = controls.Pill(theme, "Checking", "neutral")
        self.state_pill.set_clickable(True)  # Shows or hides the mini log
        self.state_pill.clicked.connect(lambda: self.log.setVisible(not self.log.isVisible()))
        self.status_row.insertWidget(1, self.state_pill)  # After View Logs
        self.progress = controls.ProgressBar(theme)
        self.progress.hide()
        after = self.status_row.indexOf(self.status_label) + 1  # Right of the message, which it replaces while working
        self.status_row.insertWidget(after, self.progress, 1)
        self.run_button = controls.Button("Run", theme, icon="box", variant="primary", tooltip="Run (Ctrl+Enter)")
        self.run_button.clicked.connect(self.run)
        self.status_row.insertWidget(after + 1, self.run_button)
        self.status_row.insertSpacing(after + 2, px(6))
        self.shimmer = controls.Shimmer(self.run_button)  # Draws the eye to Run once everything is filled in
        self._run_key = QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        self._run_key.activated.connect(self.run)

        controls.unify_heights(self)  # One height for every field, dropdown and button
        self.error_hints = controls.ErrorHints(theme, self)  # The red bubble on an invalid field
        for widget in self.field_widgets().values():
            self.error_hints.watch(widget)
        self.validate()
        self.set_status("Fill in the required fields and press Run.")

    # ---- small builders --------------------------------------------------------------------------------------------
    def _columns(self, page):
        holder = QtWidgets.QWidget()
        columns = QtWidgets.QHBoxLayout(holder)
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setSpacing(space(8))
        page.addWidget(holder)
        left, right = QtWidgets.QVBoxLayout(), QtWidgets.QVBoxLayout()
        for column in (left, right):
            column.setSpacing(space(6))
            columns.addLayout(column, 1)
        return left, right

    def _row(self, *widgets, stretch=True):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(6))
        for widget in widgets:
            row.addWidget(widget)
        if stretch:
            row.addStretch(1)
        return row

    def _button(self, text, icon, slot, variant="secondary", tooltip=""):
        button = controls.Button(text, self.theme, icon=icon, variant=variant, tooltip=tooltip)
        button.clicked.connect(slot)
        return button

    # ---- Fields ----------------------------------------------------------------------------------------------------
    def _build_fields(self, page):
        theme = self.theme
        left, right = self._columns(page)
        frame, lay = forms.panel("Result", theme, *HELP["result"], required=True)
        self.name = QtWidgets.QLineEdit()
        self.name.setPlaceholderText("Public name, e.g. Bitmap Collector")
        self.name.textChanged.connect(self.validate)
        self.kind = forms.BadgeComboBox(theme, BADGES)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(12))
        row.addLayout(forms.labeled("Name", self.name, required=True), 1)
        row.addLayout(forms.labeled("Type", self.kind))
        lay.addLayout(row)
        version = QtWidgets.QGridLayout()  # Each number with its own caption above it: Major . Minor . Patch
        version.setHorizontalSpacing(space(4))
        version.setVerticalSpacing(space(2))
        self.version = []
        for index, (name, value) in enumerate((("Major", 1), ("Minor", 0), ("Patch", 0))):
            stepper = Stepper(theme, 0, 999, value)
            stepper.valueChanged.connect(self.validate)
            self.version.append(stepper)
            version.addWidget(forms.caption(name), 0, index * 2)
            version.addWidget(stepper, 1, index * 2)
            if index < 2:
                dot = QtWidgets.QLabel(".")
                dot.setAlignment(Qt.AlignCenter)
                version.addWidget(dot, 1, index * 2 + 1)
        self.date = DateField(theme)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(12))
        row.addLayout(version)
        row.addStretch(1)
        row.addLayout(forms.labeled("Release date", self.date, required=True))
        lay.addLayout(row)
        row = QtWidgets.QHBoxLayout()  # A date with a time, and a time alone
        row.setSpacing(space(12))
        self.review = DateField(theme, with_time=True)  # The title switches to months and years; Done applies
        self.review.set_range(QtCore.QDate.currentDate().addYears(-10), QtCore.QDate.currentDate().addYears(10))
        self.review.changed.connect(lambda value: self.set_status("Review set to {}.".format(
            value.toString("yyyy-MM-dd HH:mm"))))
        self.reminder = TimeEdit(theme, QtCore.QTime(9, 30))
        row.addLayout(forms.labeled("Review at", self.review))
        row.addLayout(forms.labeled("Daily reminder", self.reminder))
        row.addStretch(1)
        lay.addLayout(row)
        self.description = QtWidgets.QPlainTextEdit()
        self.description.setFixedHeight(px(52))
        self.description.setPlainText("A short description of the result.")
        self.description.textChanged.connect(self.validate)
        self.description_box = controls.boxed(self.description)  # Lists and text boxes sit in a field frame
        self.counter = controls.muted("", wrap=False)
        lay.addLayout(forms.labeled("Description", self.description_box, required=True))
        lay.addWidget(self.counter)
        left.addWidget(frame)
        self.advanced = forms.Collapsible("Advanced options", theme)  # Holds data, so it starts open (below)
        self.advanced.inner.addWidget(controls.muted("Optional settings stay in a group that opens."))
        self.backup = QtWidgets.QLineEdit("Backup")
        self.advanced.inner.addLayout(forms.labeled("Backup layer", self.backup))
        self.folder = QtWidgets.QLineEdit("C:\\Projects\\Renders")  # A folder: read-only path, a button to choose
        self.folder.setReadOnly(True)
        choose = controls.Button("", theme, icon="folder-open", tooltip="Choose the output folder")
        choose.clicked.connect(self.choose_folder)
        self.advanced.inner.addLayout(forms.labeled("Output folder", forms.field_with_button(self.folder, choose)))
        left.addWidget(self.advanced)
        left.addStretch(1)

        frame, lay = forms.panel("Links", theme, *HELP["links"])
        self.channel = controls.ComboBox()
        for key, name in (("stable", "Stable"), ("beta", "Beta"), ("alpha", "Alpha")):
            self.channel.addItem(name, key)
        heading = QtWidgets.QHBoxLayout()  # A caption with its own "?" balloon
        heading.setSpacing(space(4))
        heading.addWidget(forms.caption("Channel"), 0, Qt.AlignVCenter)
        heading.addWidget(controls.HelpButton(theme, *HELP["channel"]), 0, Qt.AlignVCenter)
        heading.addStretch(1)
        channel = QtWidgets.QVBoxLayout()
        channel.setSpacing(space(2))
        channel.addLayout(heading)
        channel.addWidget(self.channel)
        self.homepage = QtWidgets.QLineEdit()
        self.homepage.setPlaceholderText("https://")
        self._check_url(self.homepage)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(12))
        row.addLayout(channel)
        row.addLayout(forms.labeled("Homepage URL", self.homepage), 1)
        lay.addLayout(row)
        self.guid = QtWidgets.QLineEdit("3f2a9c1e-7b4d-4e8a-9c21-5d6e7f8a9b0c")
        self.guid.setReadOnly(True)
        self.copy_button = CopyButton(theme, self.guid.text, "Copy the ID")  # The icon turns into a green check
        self.guid_menu = controls.Menu(theme, self)  # Rare actions in a menu keep the row short
        self.guid_menu.add_item("Paste ID from clipboard", "clipboard-paste", lambda: None)
        self.guid_menu.addSeparator()
        self.guid_menu.add_item("Generate a new ID", "refresh-cw", lambda: None, danger=True)
        more = controls.Button("", theme, icon="chevron-down", tooltip="Paste or generate an ID")
        more.clicked.connect(lambda: self.guid_menu.popup_at(more.mapToGlobal(QtCore.QPoint(0, more.height() + 2))))
        self.guid_more = more
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(6))
        row.addWidget(self.guid, 1)
        row.addWidget(self.copy_button)
        row.addWidget(more)
        lay.addLayout(forms.labeled("ID", row, hint="Read-only: copy it, or use the menu."))
        links = QtWidgets.QHBoxLayout()  # Plain links: a page outside the tool (with its icon), a window inside it
        links.setSpacing(space(16))
        links.addWidget(controls.Link(theme, "3dground.net", "https://3dground.net", external=True))
        links.addWidget(controls.Link(theme, "Show the logs", on_click=self.controller.show_logs))
        links.addStretch(1)
        lay.addLayout(links)
        right.addWidget(frame)
        self.purchase = forms.Collapsible("Purchase or support link", theme)  # Optional and empty: closed
        self.purchase.inner.addWidget(controls.muted("Optional: a page for a license, a donation or support."))
        self.purchase_url = QtWidgets.QLineEdit()
        self.purchase_url.setPlaceholderText("https://")
        self._check_url(self.purchase_url)
        self.purchase.inner.addLayout(forms.labeled("URL", self.purchase_url))
        right.addWidget(self.purchase)
        frame, lay = forms.panel("Files", theme, *HELP["drop"])
        self.drop = DropZone(theme, (".png", ".jpg", ".exr"))
        self.drop.dropped.connect(lambda paths: self.notify("{} file{} added.".format(
            len(paths), "" if len(paths) == 1 else "s"), "success"))
        lay.addWidget(self.drop)
        right.addWidget(frame)
        right.addStretch(1)
        if self.backup.text():
            self.advanced.set_open(True)  # An optional group opens when it holds data

    # ---- Choices ---------------------------------------------------------------------------------------------------
    def _build_choices(self, page):
        theme = self.theme
        left, right = self._columns(page)
        frame, lay = forms.panel("Options", theme, *HELP["options"])
        self.quality = controls.Segmented((("fast", "Fast", "Quick preview"), ("balanced", "Balanced", "Recommended"),
                                           ("max", "Max", "Slow and heavy")), theme, "balanced")
        lay.addWidget(self.quality)
        for text, checked, enabled in (("Selected objects only", True, True), ("Include hidden objects", False, True),
                                       ("Needs a selection", False, False)):
            switch = Switch(theme, text)  # On / off settings are switches
            switch.setChecked(checked)
            switch.setEnabled(enabled)
            lay.addWidget(switch)
        for text, state, enabled in (("Box", Qt.Checked, True), ("Sphere", Qt.Unchecked, True),
                                     ("All primitives", Qt.PartiallyChecked, True), ("Locked by the scene", Qt.Checked,
                                                                                    False)):
            box = QtWidgets.QCheckBox(text)  # Check boxes pick items of a list
            box.setTristate(state == Qt.PartiallyChecked)
            box.setCheckState(state)
            box.setEnabled(enabled)
            box.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
            lay.addWidget(box)
        self.target = controls.ComboBox()
        for label in ("New layer", "Current layer", "Selection's layer"):
            self.target.addItem(label)
        locked = controls.ComboBox()
        locked.addItem("Scene units")
        locked.setEnabled(False)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(12))
        row.addLayout(forms.labeled("Target layer", self.target), 1)
        row.addLayout(forms.labeled("Units", locked), 1)
        lay.addLayout(row)
        self.type_filter = ClearableComboBox(theme, (("any", "Any type"), ("mesh", "Meshes"), ("light", "Lights"),
                                                     ("camera", "Cameras")), "any", "Show only one type")
        lay.addLayout(forms.labeled("Filter", self.type_filter, hint="An x appears while a filter is on."))
        left.addWidget(frame)
        frame, lay = forms.panel("Scene picks", theme, *HELP["picks"])
        self.pick_object = PickButton(theme, "Pick an object")
        self.pick_camera = PickButton(theme, "Pick a camera", kind="camera")
        for button in (self.pick_object, self.pick_camera):
            button.picked.connect(lambda node: self.set_status("Picked {}.".format(node[1]) if node else "Cleared."))
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(12))
        row.addLayout(forms.labeled("Target object", self.pick_object), 1)
        row.addLayout(forms.labeled("Camera", self.pick_camera), 1)
        lay.addLayout(row)
        left.addWidget(frame)
        frame, lay = forms.panel("Dropdowns", theme, *HELP["dropdowns"])
        self.output = IconComboBox(theme, (("scene", "Scene file", "box"), ("image", "Rendered image", "camera"),
                                           ("report", "Report", "scroll-text"), ("package", "Package", "package")))
        self.preset = GroupedComboBox(theme, (("Interior", (("day", "Day"), ("night", "Night"), ("overcast", "Overcast"))),
                                              ("Exterior", (("sunny", "Sunny"), ("dusk", "Dusk"))),
                                              ("Studio", (("three", "Three-point"), ("soft", "Soft box")))))
        self.layer_combo = editable_combo(theme, LAYER_NAMES, self, "Pick or type")
        self.export_kinds = MultiComboBox(theme, (("geometry", "Geometry"), ("lights", "Lights"),
                                                  ("cameras", "Cameras"), ("helpers", "Helpers"),
                                                  ("materials", "Materials")), ("geometry", "materials"))
        self.export_kinds.changed.connect(lambda values: self.set_status("Export: {}.".format(
            self.export_kinds.summary())))
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(space(12))
        grid.setVerticalSpacing(space(8))
        grid.addLayout(forms.labeled("Output", self.output), 0, 0)
        grid.addLayout(forms.labeled("Light preset", self.preset), 0, 1)
        grid.addLayout(forms.labeled("Layer", self.layer_combo), 1, 0)
        grid.addLayout(forms.labeled("Export", self.export_kinds), 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        lay.addLayout(grid)
        left.addWidget(frame)
        left.addStretch(1)

        frame, lay = forms.panel("Buttons and status", theme, *HELP["buttons"])
        for enabled in (True, False):
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(space(6))
            for text, icon, variant in (("Primary", "box", "primary"), ("Secondary", "copy", "secondary"),
                                        ("Ghost", "eye", "ghost"), ("Danger", "trash-2", "danger")):
                button = controls.Button(text, theme, icon=icon, variant=variant)
                button.setEnabled(enabled)
                row.addWidget(button)
            row.addStretch(1)
            lay.addLayout(row)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(6))
        for icon, tip, variant in (("copy", "Copy", "secondary"), ("folder-open", "Open folder", "secondary"),
                                   ("refresh-cw", "Refresh", "secondary"), ("plus", "Add", "primary"),
                                   ("trash-2", "Remove", "danger")):
            row.addWidget(controls.Button("", theme, icon=icon, variant=variant, tooltip=tip))  # Squares
        row.addStretch(1)
        lay.addLayout(row)
        pills = controls.FlowLayout(spacing=px(6))
        for text, variant in (("Objects 1,234", "neutral"), ("Info", "info"), ("Done", "success"),
                              ("Cache: not set", "warning"), ("Failed", "error")):
            pills.addWidget(controls.Pill(theme, text, variant))
        holder = QtWidgets.QWidget()
        holder.setLayout(pills)
        lay.addWidget(holder)
        for name, title, text in (("toolBanner", "Large result", "About 2.4 million polygons. 3ds Max may become "
                                   "slow; choose a lower quality if this is too much."),
                                  ("toolDanger", "Not enough disk space", "The cache needs 1.2 GB; 300 MB are free.")):
            block = QtWidgets.QFrame()
            block.setObjectName(name)
            block_layout = QtWidgets.QVBoxLayout(block)
            block_layout.setContentsMargins(space(12), space(8), space(12), space(8))
            block_layout.setSpacing(space(2))
            heading = QtWidgets.QLabel(title)
            heading.setObjectName(name + "Title")
            block_layout.addWidget(heading)
            block_layout.addWidget(controls.muted(text))
            lay.addWidget(block)
        right.addWidget(frame)
        frame, lay = forms.panel("Quality", theme, *HELP["radio"])
        self.quality = RadioCards(theme, (("draft", "Draft", "Quick previews in a minute or two.", "gauge"),
                                          ("preview", "Client preview", "Clean enough to send; a few minutes.",
                                           "camera"),
                                          ("final", "Final", "Full quality for print; can take hours.", "sparkles")),
                                  "preview", columns=1)
        self.quality.changed.connect(lambda value: self.set_status("Quality: {}.".format(value)))
        lay.addWidget(self.quality)
        right.addWidget(frame)
        right.addStretch(1)

    # ---- Sliders and colours ---------------------------------------------------------------------------------------
    def _build_sliders(self, page):
        theme = self.theme
        left, right = self._columns(page)
        frame, lay = forms.panel("Sliders", theme, *HELP["sliders"])
        self.opacity = Slider(theme, 0, 100, 80, suffix=" %")
        lay.addLayout(forms.labeled("Opacity", self.opacity))
        self.strength = Slider(theme, 0, 1, 0.35, step=0.01, decimals=2)
        lay.addLayout(forms.labeled("Strength", self.strength))
        self.polygons = RangeSlider(theme, 0, 200000, 20000, 120000, step=1000)
        lay.addLayout(forms.labeled("Polygon range", self.polygons, hint="Objects between the two handles are kept."))
        self.distance = RangeSlider(theme, 0, 50, 5, 30, step=0.5, decimals=1, suffix=" m")
        lay.addLayout(forms.labeled("Camera distance", self.distance))
        locked = Slider(theme, 0, 100, 40, suffix=" %")
        locked.setEnabled(False)
        lay.addLayout(forms.labeled("Locked by the preset", locked))
        left.addWidget(frame)
        left.addStretch(1)

        frame, lay = forms.panel("Colours", theme, *HELP["colors"])
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(space(12))
        grid.setVerticalSpacing(space(6))
        self.colors = {}
        for index, (name, value) in enumerate((("Wire colour", "#e0a05a"), ("Background", "#2b2f36"),
                                                ("Highlight", "#4aa37a"), ("Warning", "#d9534f"))):
            button = ColorButton(theme, value)
            button.colorChanged.connect(lambda color, key=name: self.set_status("{}: {}".format(key, color)))
            self.colors[name] = button
            grid.addLayout(forms.labeled(name, button), index // 2, index % 2)
        lay.addLayout(grid)
        lay.addWidget(controls.muted("The picker opens under the button. Presets and the last colours you chose are "
                                     "one click away."))
        right.addWidget(frame)
        frame, lay = forms.panel("Standing sliders", theme)
        faders = QtWidgets.QHBoxLayout()  # Like a mixer: the smallest value at the bottom
        faders.setSpacing(space(16))
        self.faders = []
        for name, value in (("Key", 80), ("Fill", 45), ("Rim", 60)):
            fader = Slider(theme, 0, 100, value, suffix=" %", vertical=True)
            fader.setFixedHeight(px(170))
            self.faders.append(fader)
            column = QtWidgets.QVBoxLayout()
            column.setSpacing(space(2))
            label = forms.caption(name)
            label.setAlignment(Qt.AlignHCenter)
            column.addWidget(label)
            column.addWidget(fader, 0, Qt.AlignHCenter)
            faders.addLayout(column)
        self.height_range = RangeSlider(theme, 0, 30, 4, 18, step=0.5, decimals=1, suffix=" m", vertical=True)
        self.height_range.setFixedHeight(px(170))
        column = QtWidgets.QVBoxLayout()
        column.setSpacing(space(2))
        label = forms.caption("Height")
        label.setAlignment(Qt.AlignHCenter)
        column.addWidget(label)
        column.addWidget(self.height_range, 0, Qt.AlignHCenter)
        faders.addLayout(column)
        faders.addStretch(1)
        lay.addLayout(faders)
        right.addWidget(frame)
        right.addStretch(1)

    # ---- Badges ----------------------------------------------------------------------------------------------------
    def _build_badges(self, page):
        theme = self.theme
        left, right = self._columns(page)
        frame, lay = forms.panel("Count badges", theme)
        self.inbox = controls.Button("Messages", theme, icon="info")
        self.errors_button = controls.Button("Problems", theme, icon="circle-alert")
        lay.addLayout(self._row(self.inbox, self.errors_button))
        self.inbox_badge = CountBadge(self.inbox, theme, role="accent")
        self.inbox_badge.set_count(3)
        self.errors_badge = CountBadge(self.errors_button, theme)
        self.errors_badge.set_count(128)
        lay.addLayout(self._row(self._button("Add", "plus", lambda: self.inbox_badge.set_count(
            self.inbox_badge.count() + 1)), self._button("Clear", "x", lambda: self.inbox_badge.set_count(0))))
        lay.addWidget(controls.muted("A number on the corner of what it counts; hidden at zero, 99+ above 99."))
        left.addWidget(frame)
        frame, lay = forms.panel("Status badges and dots", theme)
        badges = controls.FlowLayout(spacing=px(6))
        for text, role in (("New", "log_info"), ("Beta", "log_warning"), ("Pro", "log_system"), ("Stable", "log_success"),
                           ("Deprecated", "log_error")):
            badges.addWidget(StatusBadge(theme, text, role))
        holder = QtWidgets.QWidget()
        holder.setLayout(badges)
        lay.addWidget(holder)
        dots = QtWidgets.QHBoxLayout()
        dots.setSpacing(space(16))
        for text, role, pulse in (("Online", "log_success", True), ("Busy", "log_warning", False),
                                  ("Offline", "muted_text", False)):
            dots.addWidget(Dot(theme, text, role, pulse))
        dots.addStretch(1)
        lay.addLayout(dots)
        left.addWidget(frame)
        left.addStretch(1)

        frame, lay = forms.panel("Tags", theme)
        self.tag_field = QtWidgets.QLineEdit()
        self.tag_field.setPlaceholderText("Add a layer tag and press Enter")
        self.tag_field.returnPressed.connect(self.add_tag)
        lay.addWidget(self.tag_field)
        self.tags = controls.FlowLayout(spacing=px(6))
        holder = QtWidgets.QWidget()
        holder.setLayout(self.tags)
        lay.addWidget(holder)
        for index, name in enumerate(("Walls", "Floors", "Furniture", "Lights")):
            self.add_tag(name, ("log_info", None, "log_success", "log_warning")[index])
        lay.addWidget(controls.muted("Removable chips for a set of values the user picked; the x removes one."))
        right.addWidget(frame)
        right.addStretch(1)

    def add_tag(self, name=None, role=None):
        name = (name or self.tag_field.text()).strip()
        existing = [self.tags.itemAt(index).widget().text() for index in range(self.tags.count())]
        if not name or name in existing:
            return
        tag = Tag(self.theme, name, role)
        tag.removed.connect(lambda _text, chip=tag: (self.tags.removeWidget(chip), chip.deleteLater()))
        self.tags.addWidget(tag)
        self.tag_field.clear()

    # ---- Lists -----------------------------------------------------------------------------------------------------
    def _build_lists(self, page):
        theme = self.theme
        left, right = self._columns(page)
        frame, lay = forms.panel("Results", theme, *HELP["results"])
        self.search = SearchBox(theme, "Search results", ["Result {:02d}".format(index) for index in range(1, 41)],
                                owner=self)  # The window owns the suggestions, never the field
        self.search.search.connect(self.filter_results)
        lay.addWidget(self.search)
        watching = controls.Marquee(theme)  # One line that scrolls when it does not fit
        watching.setText("Watching C:\\Projects\\Example\\Renders\\Interior\\Living room\\Final views for the client "
                         "presentation, version 3")
        lay.addWidget(watching)
        self.results = QtWidgets.QListWidget()  # Long lists scroll with the thin pill scroll bar
        for index in range(1, 41):
            self.results.addItem("Result {:02d}  ·  {:,} polygons".format(index, index * 1375))
        self.results.setCurrentRow(2)
        self.results.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)  # Drag rows to reorder
        self.results.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results.customContextMenuRequested.connect(self.results_menu)
        self.results.setMinimumHeight(px(220))
        controls.fade_edges(self.results, theme, "field")  # A list fades at its clipped edges too
        delete_key = QShortcut(QtGui.QKeySequence(Qt.Key_Delete), self.results)
        delete_key.setContext(Qt.WidgetShortcut)
        delete_key.activated.connect(self.remove_result)
        copy_key = QShortcut(QtGui.QKeySequence.Copy, self.results)  # The keys a menu shows work without it too
        copy_key.setContext(Qt.WidgetShortcut)
        copy_key.activated.connect(self.copy_result)
        self.no_results = EmptyState(theme, "search", "No results", "Nothing matches **this search**. Try a shorter "
                                     "word.", ("Clear Search", "x", lambda: self.search.clear()))
        self.results_area = StateArea(controls.boxed(self.results), self.no_results)  # The search field never moves
        lay.addWidget(self.results_area, 1)
        left.addWidget(frame, 1)
        frame, lay = forms.panel("Pick several", theme, *HELP["several"])
        self.objects = MultiSelectList(theme, ["{} {:02d}".format(kind, index) for index in range(1, 9)
                                               for kind in ("Box", "Sphere", "Light")])
        self.objects.setMinimumHeight(px(210))
        self.objects.changed.connect(lambda chosen: self.set_status("{} objects picked.".format(len(chosen))))
        lay.addWidget(self.objects)
        left.addWidget(frame)

        frame, lay = forms.panel("List editor", theme, *HELP["editor"])
        self.editor = ListEditor(theme, "Add a file extension, e.g. .png", (".jpg", ".png", ".exr"),
                                 check=lambda value: "" if value.startswith(".") and " " not in value
                                 else "An extension starts with a dot and has no spaces")
        self.editor.setMinimumHeight(px(200))
        lay.addWidget(self.editor)
        right.addWidget(frame)
        frame, lay = forms.panel("Layers", theme)
        chips = controls.FlowLayout(spacing=px(6))
        for index, name in enumerate(LAYER_NAMES[:7]):
            chip = controls.Button(name, theme, icon="eye" if index % 3 else "eye-off")
            chip.setCheckable(True)
            chip.setChecked(index % 3 != 0)
            chips.addWidget(chip)
        holder = QtWidgets.QWidget()
        holder.setLayout(chips)
        lay.addWidget(holder)
        right.addWidget(frame)
        frame, lay = forms.panel("Table", theme)
        table = QtWidgets.QTableWidget(5, 3)
        table.setObjectName("toolTable")
        table.setHorizontalHeaderLabels(("Name", "Polygons", "Date"))
        table.verticalHeader().hide()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.horizontalHeader().setStretchLastSection(True)
        today = datetime.date.today()
        for row, (name, polygons) in enumerate((("Chair", 1375), ("Table", 4210), ("Lamp", 980), ("Sofa", 12650),
                                                ("Shelf", 2210))):
            count = QtWidgets.QTableWidgetItem()
            count.setData(Qt.DisplayRole, polygons)  # Numbers sort as numbers
            for column, item in enumerate((QtWidgets.QTableWidgetItem(name), count,
                                           QtWidgets.QTableWidgetItem((today - datetime.timedelta(days=row))
                                                                      .isoformat()))):
                table.setItem(row, column, item)
        table.setSortingEnabled(True)
        table.sortByColumn(1, Qt.DescendingOrder)  # A visible direction indicator; numbers sort as numbers
        table.setMinimumHeight(px(150))
        lay.addWidget(table)
        right.addWidget(frame)
        frame, lay = forms.panel("Scene tree", theme, *HELP["tree"])
        self.tree = SceneTree(theme)
        for layer_name, rows, opened in (
                ("Walls", (("Wall 01", "geometry", 1375), ("Wall 02", "geometry", 2210), ("Window frame", "geometry",
                                                                                          980)), True),
                ("Lights", (("Sun", "light", 0), ("Fill light", "light", 0)), True),
                ("Cameras", (("Camera 01", "camera", 0), ("Camera 02", "camera", 0)), False)):
            layer = self.tree.add_layer(layer_name, opened)
            for name, kind, polygons in rows:
                self.tree.add_object(layer, name, kind, (polygons,) if polygons else ("",), checked=name != "Fill light")
        self.tree.setMinimumHeight(px(230))
        self.tree.checked_changed.connect(lambda names: self.set_status("{} objects ticked.".format(len(names))))
        lay.addWidget(self.tree)
        right.addWidget(frame)
        right.addStretch(1)

    def filter_results(self, text):
        shown = 0
        for row in range(self.results.count()):
            item = self.results.item(row)
            hidden = bool(text) and text.lower() not in item.text().lower()
            item.setHidden(hidden)
            shown += not hidden
        self.results_area.set_empty(shown == 0)  # In the list's own place: the field above stays where it was

    # ---- Cards and gallery -----------------------------------------------------------------------------------------
    def _build_cards(self, page):
        theme = self.theme
        self.filters = FilterPills(theme)  # Categories as coloured pills: a filter, not navigation
        for key, label, icon, color in CATEGORIES:
            count = len([card for card in CARDS if card[5] == key]) if key else None
            self.filters.add(key, label, icon, color, count)
        self.filters.add("lighting", "Lighting", "star", "#c9a227", 0)
        self.filters.changed.connect(self.filter_cards)
        page.addWidget(self.filters)
        self.grid = CardGrid(min_width=230, max_columns=3)
        self.cards = []
        for title, text, icon, role, badge, category, detail in CARDS:
            card = Card(theme, title, text, icon, role, badge, detail,
                        ("Apply", "play", lambda name=title: self.notify("{} applied.".format(name), "success")))
            card.category = category
            card.clicked.connect(lambda name=title: self.set_status("{} selected.".format(name)))
            self.cards.append(card)
        self.grid.set_items(self.cards)
        self.no_cards = EmptyState(theme, "package", "No presets in this category",
                                   "Presets you save into **Lighting** appear here.",
                                   ("Show All", "layout-grid", lambda: self.filters.choose("")))
        self.cards_area = StateArea(self.grid, self.no_cards)  # The gallery below does not jump up
        page.addWidget(self.cards_area)
        frame, lay = forms.panel("Gallery", theme)
        self.gallery = Gallery(theme)  # Drag or the arrows to step; a click opens the lightbox
        for index, (title, caption) in enumerate((
                ("Living room", "Morning light through the east windows."),
                ("Kitchen", "Noon, with the pendant lamps on."), ("Facade", "Blue hour, street lamps lit."),
                ("Studio", "Three-point light on a seamless background."), ("Street", "Night, wet asphalt."),
                ("Detail", "A close-up with a shallow depth of field."))):
            self.gallery.add(demo_picture(index), title, caption)
        self.gallery.preview_requested.connect(self.open_lightbox)
        lay.addWidget(self.gallery)
        page.addWidget(frame)

    def open_lightbox(self, index):
        """The gallery's pictures over the whole content of the window (gallery.Lightbox)."""
        self.lightbox = open_lightbox(self.full_view, self.theme, self.gallery.items, index)

    def filter_cards(self, key):
        shown = [card for card in self.cards if not key or card.category == key]
        for card in self.cards:
            card.setVisible(card in shown)
        self.grid.relayout()  # Only the shown cards take places
        self.cards_area.set_empty(not shown)

    # ---- Charts ----------------------------------------------------------------------------------------------------
    def _build_charts(self, page):
        theme = self.theme
        tiles = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(tiles)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(space(8))
        self.tiles = [StatTile(theme, "Objects", 12840, delta=0.08, trend=(9, 10, 10, 11, 11, 12, 11, 12, 12, 13, 12, 13)),
                      StatTile(theme, "Average render", 4.2, " min", delta=-0.12, up_is_good=False,
                               trend=(6, 5.8, 5.5, 5.6, 5.1, 5, 4.9, 4.7, 4.6, 4.4, 4.3, 4.2)),
                      StatTile(theme, "Materials", 342, delta=0.03),
                      StatTile(theme, "Errors", 3, delta=0.5, up_is_good=False, period="vs yesterday")]
        for tile in self.tiles:
            row.addWidget(tile, 1)
        page.addWidget(tiles)
        left, right = self._columns(page)
        frame, lay = forms.panel("Polygons by layer", theme, *HELP["charts"])
        self.bars = BarChart(theme, (("Walls", 182000), ("Floors", 64000), ("Furniture", 412000), ("Lights", 9000),
                                     ("Plants", 268000), ("Props", 131000)))
        lay.addWidget(self.bars)
        left.addWidget(frame)
        frame, lay = forms.panel("Scene memory", theme)
        self.donut = DonutChart(theme, (("Geometry", 1240), ("Textures", 2310), ("Lights", 120), ("Other", 330)),
                                caption="MB in use", unit="")
        lay.addWidget(self.donut)
        left.addWidget(frame)
        left.addStretch(1)
        days = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
        frame, lay = forms.panel("Render time this week, min", theme)
        self.lines = LineChart(theme, days, (("Draft", (12, 14, 11, 16, 13, 9, 8)),
                                             ("Final", (38, 42, 35, 51, 47, 30, 26))))
        lay.addWidget(self.lines)
        right.addWidget(frame)
        frame, lay = forms.panel("Frames rendered per day", theme)
        self.frames = LineChart(theme, days, (("Frames", (120, 180, 140, 260, 310, 90, 60)),))
        lay.addWidget(self.frames)
        right.addWidget(frame)
        right.addStretch(1)

    # ---- Feedback --------------------------------------------------------------------------------------------------
    def _build_feedback(self, page):
        theme = self.theme
        left, right = self._columns(page)
        frame, lay = forms.panel("Toasts", theme, *HELP["feedback"])
        lay.addLayout(self._row(
            self._button("Success", "check", lambda: self.notify("Settings saved.", "success")),
            self._button("Error", "x", lambda: self.notify(
                "Export failed.\nThe folder is read-only. Choose another output folder.", "error")),
            self._button("Warning", "circle-alert", lambda: self.notify(
                "12 textures are missing.\nThey render black until they are found.", "warning")),
            self._button("With action", "refresh-cw", lambda: self.notify(
                "A newer version is available.\nIt installs when the tool opens again.", "info",
                action=("Reopen Now", "refresh-cw", lambda: None), key="update"))))
        left.addWidget(frame)
        frame, lay = forms.panel("Busy overlay", theme)
        lay.addWidget(controls.muted("Blocks the sections while work runs, with what runs, a calm hint and Cancel; it "
                                     "ends on the result."))
        lay.addLayout(self._row(self._button("Start Work", "play", self.start_busy),
                                self._button("Work That Fails", "x", lambda: self.start_busy(fail=True))))
        left.addWidget(frame)
        frame, lay = forms.panel("Progress", theme)
        self.demo_progress = controls.ProgressBar(theme)
        self.demo_progress.start()
        self.demo_progress.set_progress("Copying textures", 7, 20)
        lay.addWidget(self.demo_progress)
        left.addWidget(frame)
        left.addStretch(1)

        frame, lay = forms.panel("Result cards", theme)
        lay.addWidget(controls.muted("The end of a main operation, in the middle over the blurred content. It closes "
                                     "by itself; the bar shows when, and waits under the pointer."))
        lay.addLayout(self._row(
            self._button("Success", "circle-check", lambda: self.result_card.show_message(
                "success", "Conversion finished", "24 objects converted in 3.2 s.")),
            self._button("Warning", "circle-alert", lambda: self.result_card.show_message(
                "warning", "Finished with warnings", "3 objects were skipped: see View Logs.")),
            self._button("Error", "x", lambda: self.result_card.show_message(
                "error", "Conversion failed", "The scene is read-only. Nothing was changed."))))
        right.addWidget(frame)
        frame, lay = forms.panel("Empty states", theme)
        lay.addWidget(EmptyState(theme, "cloud-off", "You are offline", "The catalog loads when the connection is "
                                 "back.", ("Retry", "refresh-cw", lambda: self.notify("Still offline.", "warning")),
                                 role="log_warning"))
        right.addWidget(frame)
        right.addStretch(1)

    def start_busy(self, fail=False):
        self.busy.start("Converting the scene" if not fail else "Exporting", "This usually takes a few seconds.")
        self._busy_timer = QtCore.QTimer(self)
        self._busy_timer.setSingleShot(True)
        self._busy_timer.timeout.connect(lambda: self.busy.finish(
            "error" if fail else "success", "Export failed\nThe folder is read-only. Nothing was changed." if fail
            else "Done\n24 objects converted."))
        self._busy_timer.start(2200)

    def cancel_busy(self):
        if getattr(self, "_busy_timer", None) is not None:
            self._busy_timer.stop()
        self.busy.finish("error", "Cancelled\nNothing was changed.")

    # ---- Loading ---------------------------------------------------------------------------------------------------
    def _build_loading(self, page):
        theme = self.theme
        left, right = self._columns(page)
        frame, lay = forms.panel("Spinners", theme, *HELP["loading"])
        line = QtWidgets.QHBoxLayout()
        line.setSpacing(space(8))
        self.small_spinner = Spinner(theme, 16)
        line.addWidget(self.small_spinner)
        line.addWidget(controls.muted("Loading presets…", wrap=False))
        line.addStretch(1)
        lay.addLayout(line)
        self.refresh = controls.Button("Refresh Catalog", theme, icon="refresh-cw")
        self.refresh.clicked.connect(self.refresh_demo)
        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._refresh_done)
        lay.addLayout(self._row(self.refresh, controls.muted("A button that started work shows a spinner and waits.")))
        big = QtWidgets.QVBoxLayout()
        big.setSpacing(space(8))
        self.large_spinner = Spinner(theme, 32)
        big.addWidget(self.large_spinner, 0, Qt.AlignHCenter)
        caption = controls.muted("Connecting to the catalog…", wrap=False)
        caption.setAlignment(Qt.AlignCenter)
        big.addWidget(caption)
        lay.addSpacing(space(8))
        lay.addLayout(big)
        left.addWidget(frame)
        frame, lay = forms.panel("Progress ring", theme)
        rings = QtWidgets.QHBoxLayout()
        rings.setSpacing(space(24))
        self.ring = ProgressRing(theme, 56)
        self.ring.set_value(0.35)
        self.spinning_ring = ProgressRing(theme, 56)
        self.spinning_ring.set_value(None)
        for ring, text in ((self.ring, "Known share"), (self.spinning_ring, "Not known yet")):
            column = QtWidgets.QVBoxLayout()
            column.setSpacing(space(6))
            column.addWidget(ring, 0, Qt.AlignHCenter)
            label = controls.muted(text, wrap=False)
            label.setAlignment(Qt.AlignCenter)
            column.addWidget(label)
            rings.addLayout(column)
        rings.addStretch(1)
        self.ring_button = controls.Button("Run", theme, icon="play")
        self.ring_button.clicked.connect(self.ring_demo)
        rings.addWidget(self.ring_button, 0, Qt.AlignVCenter)
        self._ring_timer = QtCore.QTimer(self)
        self._ring_timer.setInterval(40)
        self._ring_timer.timeout.connect(self._ring_step)
        lay.addLayout(rings)
        left.addWidget(frame)
        left.addStretch(1)
        frame, lay = forms.panel("Skeleton", theme)
        self.skeletons = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(self.skeletons)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(space(12))
        for _ in range(3):
            column.addWidget(Skeleton(theme, (0.5, 0.85), avatar=True))
        self.loaded = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(self.loaded)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(space(12))
        for index, (title, text) in enumerate((("Living room", "Morning light, 12 objects"),
                                               ("Kitchen", "Noon, 31 objects"), ("Facade", "Blue hour, 204 objects"))):
            column.addLayout(self._loaded_row(index, title, text))
        self.skeleton_area = StateArea(self.loaded, self.skeletons)
        self.skeleton_area.set_empty(True)
        lay.addWidget(self.skeleton_area)
        self.load_button = controls.Button("Load Again", theme, icon="rotate-ccw")
        self.load_button.clicked.connect(self.skeleton_demo)
        self._skeleton_timer = QtCore.QTimer(self)
        self._skeleton_timer.setSingleShot(True)
        self._skeleton_timer.timeout.connect(lambda: self.skeleton_area.set_empty(False))
        lay.addLayout(self._row(self.load_button, controls.muted("Grey rows hold the place until the content comes.")))
        right.addWidget(frame)
        frame, lay = forms.panel("Steps", theme)
        self.steps = Steps(theme, ("Scene", "Options", "Export", "Done"), 1)
        lay.addWidget(self.steps)
        back = controls.Button("Back", theme, icon="chevron-left")
        forward = controls.Button("Next", theme, icon="chevron-right", variant="primary")
        back.clicked.connect(lambda: self.steps.set_current(self.steps.current - 1))
        forward.clicked.connect(lambda: self.steps.set_current(self.steps.current + 1))
        controls.same_width(back, forward)
        lay.addLayout(self._row(back, forward))
        right.addWidget(frame)
        right.addStretch(1)
        self._skeleton_timer.start(1800)  # The demo content arrives a moment after the trainer opens

    def _loaded_row(self, index, title, text):
        # A row as the skeleton promised it: a round picture, a bold title, a muted line
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(12))
        picture = QtWidgets.QLabel()
        size = px(40)
        picture.setFixedSize(size, size)
        image = demo_picture(index).scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        rounded = QtGui.QPixmap(size, size)
        rounded.fill(Qt.transparent)
        painter = QtGui.QPainter(rounded)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        clip = QtGui.QPainterPath()
        clip.addEllipse(QtCore.QRectF(0, 0, size, size))
        painter.setClipPath(clip)
        painter.drawPixmap(0, 0, image)
        painter.end()
        picture.setPixmap(rounded)
        row.addWidget(picture)
        texts = QtWidgets.QVBoxLayout()
        texts.setSpacing(space(2))
        heading = QtWidgets.QLabel(title)
        heading.setObjectName("toolRadioTitle")
        texts.addWidget(heading)
        texts.addWidget(controls.muted(text, wrap=False))
        row.addLayout(texts, 1)
        return row

    def refresh_demo(self):
        busy(self.refresh, True, "Refreshing…")
        self._refresh_timer.start(2500)

    def _refresh_done(self):
        busy(self.refresh, False)
        self.notify("Catalog refreshed.", "success")

    def ring_demo(self):
        self.ring.set_value(0.0)
        self._ring_timer.start()

    def _ring_step(self):
        value = min(1.0, (self.ring.value() or 0.0) + 0.02)
        self.ring.set_value(value)
        if value >= 1.0:
            self._ring_timer.stop()

    def skeleton_demo(self):
        self.skeleton_area.set_empty(True)
        self._skeleton_timer.start(1800)

    # ---- Windows ---------------------------------------------------------------------------------------------------
    def _build_windows(self, page):
        theme = self.theme
        left, right = self._columns(page)
        frame, lay = forms.panel("Messages", theme)
        lay.addWidget(controls.muted("Every message is the tool's own window, never a Windows message box."))
        lay.addLayout(self._row(
            self._button("Info", "info", lambda: inform(self.controller, self, "Export", "The export is queued.",
                                                        "It starts when the current render ends.")),
            self._button("Success", "check", lambda: inform(self.controller, self, "Export", "Export finished.",
                                                            "**24** files written.", kind="success")),
            self._button("Warning", "circle-alert", lambda: inform(self.controller, self, "Textures",
                                                                   "12 textures are missing.",
                                                                   "They render black until they are found.",
                                                                   kind="warning")),
            self._button("Error", "x", lambda: inform(self.controller, self, "Save", "The file could not be saved.",
                                                      "The folder is read-only. Choose another folder.",
                                                      kind="error"))))
        lay.addLayout(self._row(self._button("Ask", "trash-2", self.ask_demo),
                                self._button("Text Prompt", "pencil", self.prompt_demo)))
        left.addWidget(frame)
        left.addStretch(1)
        frame, lay = forms.panel("Windows", theme)
        lay.addWidget(controls.muted("Settings as tabs suits up to three sections; a list on the left suits more."))
        lay.addLayout(self._row(
            self._button("Settings: Tabs", "settings", lambda: self.open_settings(False)),
            self._button("Settings: List", "settings", lambda: self.open_settings(True))))
        lay.addLayout(self._row(self._button("Welcome", "sparkles", self.controller.show_welcome),
                                self._button("Logs Window", "logs", self.controller.show_logs),
                                self._button("About", "info", self.controller.show_about)))
        right.addWidget(frame)
        frame, lay = forms.panel("Without the window (API)", theme, *HELP["api"])
        usage = QtWidgets.QPlainTextEdit()
        usage.setReadOnly(True)
        usage.setFont(monospace(pt(8.5)))
        usage.setPlainText('MyToolAPI.call "describe"\n'
                           'MyToolAPI.call "scene_summary" params:"{\\"selection_only\\": true}"\n'
                           'MyToolAPI.call "add_prefix" params:"{\\"prefix\\": \\"SM_\\", \\"dry_run\\": true}"')
        usage.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)  # One call per line; long ones scroll sideways
        usage.setFixedHeight(usage.fontMetrics().lineSpacing() * 3 + space(16))
        lay.addWidget(controls.boxed(usage))
        self.api_output = QtWidgets.QPlainTextEdit()
        self.api_output.setReadOnly(True)
        self.api_output.setFont(monospace(pt(8.5)))
        self.api_output.setPlaceholderText("The answer of a call shows here.")
        self.api_output.setMinimumHeight(px(140))
        lay.addLayout(self._row(self._button("Describe", "info", lambda: self.api_demo("describe")),
                                self._button("Scene Summary", "box", lambda: self.api_demo("scene_summary")),
                                self._button("Dry Run", "pencil", lambda: self.api_demo(
                                    "add_prefix", prefix="SM_", dry_run=True))))
        lay.addWidget(controls.boxed(self.api_output))
        right.addWidget(frame)
        right.addStretch(1)

    def api_demo(self, operation, **params):
        """The window calls the same API a script or an assistant calls (one code path)."""
        answer = api.call(operation, **params)
        self.api_output.setPlainText(json.dumps(answer, indent=2, ensure_ascii=False))
        self.set_status("{}: {}.".format(operation, "done" if answer["ok"] else answer["error"]["message"]))

    def open_settings(self, side):
        dialog = SettingsDialog(self.controller, self, side=side)
        dialog.finished.connect(lambda *_: dialog.dispose())
        dialog.show()

    def prompt_demo(self):
        address = ask_text(self.controller, self, "Homepage", "Web address of the tool's page",
                           self.homepage.text(), "https://3dground.net",
                           check=lambda text: forms.url_error(text, required=True), action="Save")
        if address is not None:
            self.homepage.setText(forms.complete_url(address))
            self.notify("Homepage saved.", "success")

    # ---- Donations -------------------------------------------------------------------------------------------------
    def _build_donations(self, page):
        theme = self.theme
        page.addWidget(how_to_card(theme, (
            "**Donate** in the status bar and in About opens the **Support** window: why a donation helps, Not now and "
            "a shimmering Donate.",
            "After a successful **Run** the result card can carry a line and Donate (from the second success, once a "
            "session).",
            "On the **5th start** the Support window comes by itself, with \"I've already donated, don't remind me\"; Settings > "
            "Support turns reminders on or off.",
        ), "The owner chooses which of these the tool uses (`DONATE_OFFERS`); none without a donation address.",
            title="Where a donation is offered"))
        left, right = self._columns(page)
        frame, lay = forms.panel("Try them", theme)
        enabled = bool(DONATE_URL)
        for button in (self._button("Support Window", "heart", lambda: self.controller.show_support()),
                       self._button("Start Reminder", "bell-off", lambda: self.controller.show_support(reminder=True)),
                       self._button("Result With Donate", "circle-check", lambda: self.result_card.show_message(
                           "success", "Conversion finished", "24 objects converted in 3.2 s.", 9000,
                           DONATION_NOTE))):
            button.setEnabled(enabled)
            lay.addLayout(self._row(button))
        if not enabled:
            lay.addWidget(controls.muted("No donation address: every offer is off."))
        left.addWidget(frame)
        left.addStretch(1)
        frame, lay = forms.panel("Shimmer", theme)
        lay.addWidget(controls.muted("A light band sweeps over a button every few seconds to draw the eye: Donate in "
                                     "the Support window and on the result card, Run once everything is filled in."))
        donate = controls.Button("Donate", theme, icon="heart", variant="donate")
        donate.clicked.connect(lambda: self.controller.show_support())
        donate.setEnabled(enabled)
        self.donate_shimmer = controls.Shimmer(donate)
        self.donate_shimmer.set_active(enabled)
        lay.addLayout(self._row(donate))
        right.addWidget(frame)
        right.addStretch(1)

    # ---- behaviour -------------------------------------------------------------------------------------------------
    def showEvent(self, event):
        ToolWindow.showEvent(self, event)
        controls.unify_heights(self)  # Again after polish: style sheet sizes apply when widgets first show

    def on_tab(self, key):  # The mini log's "go to" and older callers
        self.book.show_page(key)

    def _check_url(self, edit):
        """A web address field is checked on every edit; leaving it completes "site.com" to "https://site.com"."""
        edit.textChanged.connect(self.validate)

        def complete():
            completed = forms.complete_url(edit.text())
            if completed != edit.text():
                edit.setText(completed)
        edit.editingFinished.connect(complete)

    def field_widgets(self):
        """Validation key -> the widget that shows it (red outline, error bubble, go to field)."""
        return {"name": self.name, "description": self.description_box, "version": self.version[0],
                "homepage": self.homepage, "purchase": self.purchase_url}

    def validate(self, *_args):
        """Check the fields; the mini log shows the result as statuses (never a history)."""
        if not hasattr(self, "log"):
            return  # Still building
        description = self.description.toPlainText()
        self.counter.setText(_counter_text(description))
        problems = []
        if not self.name.text().strip():
            problems.append(("ERROR", "Name is required", "name"))
        if not description.strip():
            problems.append(("ERROR", "Description is required", "description"))
        for key, edit, label in (("homepage", self.homepage, "Homepage URL"), ("purchase", self.purchase_url,
                                                                               "Purchase URL")):
            error = forms.url_error(edit.text())
            if error:
                problems.append(("ERROR", "{}: {}".format(label, error), key))
        if all(stepper.value() == 0 for stepper in self.version):
            problems.append(("WARNING", "Version 0.0.0: raise it before a release", "version"))
        errors = [problem for problem in problems if problem[0] == "ERROR"]
        for key, widget in self.field_widgets().items():
            message = "\n".join(text for level, text, target in errors if target == key)
            invalid = "true" if message else "false"
            if widget.property("invalid") != invalid:
                widget.setProperty("invalid", invalid)
                repolish(widget)
            if (widget.property("invalidMessage") or "") != message:
                widget.setProperty("invalidMessage", message)  # Shown by the red bubble (controls.ErrorHints)
                self.error_hints.refresh(widget)
        self.fields_badge.set_count(len(errors))  # On the Fields section in the list
        if errors:
            self.state_pill.set_status("{} to fix".format(len(errors)), "error", "Click to show or hide the list")
        else:
            self.state_pill.set_status("Ready", "success", "Everything required is filled in")
        self.run_button.setEnabled(not errors and not self.progress.isVisible())
        self.shimmer.set_active(self.run_button.isEnabled())
        self.log.set_entries(problems if errors else problems + [("OK", "Ready to run", "")])

    def go_to_field(self, key):
        """A click on a mini log row: its section, the field in view and focused."""
        widget = self.field_widgets().get(key)
        if widget is None:
            return
        self.book.show_page("fields")
        group = widget.parentWidget()
        while group is not None and not isinstance(group, forms.Collapsible):
            group = group.parentWidget()
        if group is not None:
            group.set_open(True)  # A field in a closed group: open the group first
            QtWidgets.QApplication.processEvents()
        area = self.book.stack.currentWidget()
        if isinstance(area, QtWidgets.QScrollArea):
            area.ensureWidgetVisible(widget, px(20), px(40))
        widget.setFocus(Qt.OtherFocusReason)
        controls.Flash(widget, self.theme.colors["log_error"])  # Shows where to look

    def results_menu(self, position):
        item = self.results.itemAt(position)
        if item is None:
            return
        self.results.setCurrentItem(item)  # The menu acts on the row under the pointer
        self.result_menu(item).popup_at(self.results.viewport().mapToGlobal(position))

    def result_menu(self, item):
        """A row's menu: Lucide icons, a disabled item, a separator, the destructive item last and red."""
        menu = controls.Menu(self.theme, self)
        menu.add_item("Copy", "copy", self.copy_result, shortcut="Ctrl+C")
        menu.add_item("Rename", "pencil", lambda: self.results.editItem(item), enabled=False, shortcut="F2")
        menu.addSeparator()
        menu.add_item("Delete", "trash-2", self.remove_result, danger=True, shortcut="Del")
        return menu

    def copy_result(self):
        item = self.results.currentItem()
        if item is not None:
            QtWidgets.QApplication.clipboard().setText(item.text())
            self.set_status("Copied {}.".format(item.text().split("  ")[0]))

    def remove_result(self):
        item = self.results.currentItem()
        if item is None:
            return
        if ask(self.controller, self, "Delete Result", "Delete {}?".format(item.text().split("  ")[0]),
               "The result is removed from the list. This cannot be undone.", "Delete", "Cancel"):
            self.results.takeItem(self.results.row(item))
            self.notify("Result deleted.", "success")

    def ask_demo(self):
        """A question before something that cannot be undone (dialogs.ask); here only shown, nothing is deleted."""
        if ask(self.controller, self, "Clear Cache", "Clear the cache?",
               "**1.2 GB** of downloaded files are deleted. They download again when needed.", "Clear Cache"):
            self.notify("Cache cleared.", "success")

    def make_question(self):
        """The demo question without waiting for an answer (a test shows and closes it)."""
        return ConfirmDialog(self.controller, self, "Clear Cache", "Clear the cache?",
                             "**1.2 GB** of downloaded files are deleted. They download again when needed.",
                             "Clear Cache")

    def copy_id(self):
        self.copy_button.click()

    def choose_folder(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Output folder", self.folder.text())
        if path:
            self.folder.setText(path)

    def run(self):
        """A background job with progress: the worker gets plain data, results come back on the main thread."""
        if not self.run_button.isEnabled():
            return

        def work(cancel, report):
            for step in range(1, 21):
                if cancel.is_set():
                    return "cancelled"
                time.sleep(0.1)
                report("Processing", step, 20)
            return "done"

        self.run_button.setEnabled(False)
        self.status_label.hide()
        self.progress.start()
        self.state_pill.set_status("Working", "info")
        self.controller.run_job(work, self.progress.set_progress, self._finished)

    def _finished(self, result):
        self.progress.stop()
        self.status_label.show()
        failed = isinstance(result, Exception)
        self.set_status("Failed: {}".format(result) if failed else "Finished.")
        if failed:
            self.result_card.show_message("error", "Run failed", str(result))
        elif result == "cancelled":
            self.notify("Cancelled.\nNothing was changed.", "warning")
        else:  # The end of the main operation: the result card, with the donation line when donation.py allows it
            note = DONATION_NOTE if self.controller.donations.after_success() else ""
            self.result_card.show_message("success", "Finished", "20 objects processed.", 9000 if note else 4500, note)
        self.validate()
        if failed:
            self.state_pill.set_status("Failed", "error")
```
