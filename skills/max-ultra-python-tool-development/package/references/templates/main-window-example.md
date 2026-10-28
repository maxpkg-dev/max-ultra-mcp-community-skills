# Template: Main window example

A main window built on the tool window that shows every shared control once: options panel with help, field button, segmented choice, checkboxes, dropdown, primary action pinned at the bottom, pills, progress, warning block, list, background job.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `python/mytool/ui/main_window.py`

```python
"""The tool's main window: ToolWindow (title bar, collapse, status bar) plus the tool's own content.

This demo content shows every shared control once; replace it with the tool's panels and keep the patterns: a rounded
panel (#toolPanel) with section titles and "?" help, segmented choices, checkboxes, a dropdown, a field with its
button inside, status pills, a progress bar and the primary action pinned at the bottom.
"""

import time

from ..qt_compat import QtCore, QtWidgets, Qt
from ..ui_scale import px
from . import controls
from .tool_window import ToolWindow

HELP = {
    "options": ("Options", "What the tool does with the scene. Hover a control for details."),
    "status": ("Status", "Pills summarise state at a glance; the progress bar shows real progress or a sweep."),
}


def _section(title, theme, help_key):
    row = QtWidgets.QHBoxLayout()
    row.setSpacing(px(6))
    row.addWidget(controls.section(title))
    row.addWidget(controls.HelpButton(theme, *HELP[help_key]))
    row.addStretch(1)
    return row


class MainWindow(ToolWindow):
    def __init__(self, controller, parent=None):
        ToolWindow.__init__(self, controller, parent)
        theme = controller.theme
        columns = QtWidgets.QHBoxLayout()
        columns.setSpacing(px(12))
        self.body.addLayout(columns, 1)

        # Left: an options panel.
        panel = QtWidgets.QFrame()
        panel.setObjectName("toolPanel")
        options = QtWidgets.QVBoxLayout(panel)
        options.setContentsMargins(px(12), px(10), px(12), px(12))
        options.setSpacing(px(8))
        options.addLayout(_section("Options", theme, "options"))
        search = QtWidgets.QLineEdit()
        search.setPlaceholderText("Search objects by name")
        search_button = controls.Button("", theme, icon="search", tooltip="Search (Enter)", parent=search)
        search_button.setObjectName("toolFieldButton")
        search.setTextMargins(0, 0, px(30), 0)
        self._search, self._search_button = search, search_button
        search.installEventFilter(self)
        options.addWidget(search)
        self.quality = controls.Segmented((("fast", "Fast", "Quick preview"), ("balanced", "Balanced", "Recommended"),
                                           ("max", "Max", "Slow and heavy")), theme, "balanced")
        options.addWidget(self.quality)
        for text, checked, enabled in (("Selected objects only", True, True), ("Include hidden objects", False, True),
                                       ("Needs a selection", False, False)):
            box = QtWidgets.QCheckBox(text)
            box.setChecked(checked)
            box.setEnabled(enabled)
            box.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
            options.addWidget(box)
        target = controls.ComboBox()
        for label in ("New layer", "Current layer", "Selection's layer"):
            target.addItem(label)
        options.addWidget(target)
        options.addStretch(1)
        actions = QtWidgets.QHBoxLayout()  # The primary action stays pinned at the bottom of the panel.
        actions.setSpacing(px(6))
        remove = controls.Button("Remove", theme, icon="trash-2", variant="danger", tooltip="Delete the last result")
        actions.addWidget(remove)
        actions.addStretch(1)
        self.run_button = controls.Button("Run", theme, icon="box", variant="primary", tooltip="Run (Ctrl+Enter)")
        self.run_button.clicked.connect(self.run)
        actions.addWidget(self.run_button)
        options.addLayout(actions)
        panel.setFixedWidth(px(300))
        columns.addWidget(panel)

        # Right: status, progress, a warning block.
        right = QtWidgets.QVBoxLayout()
        right.setSpacing(px(10))
        right.addLayout(_section("Status", theme, "status"))
        pills = QtWidgets.QHBoxLayout()
        pills.setSpacing(px(6))
        for text, variant in (("Objects 1,234", "neutral"), ("Info", "info"), ("Done", "success"),
                              ("Cache: not set", "warning"), ("Failed", "error")):
            pills.addWidget(controls.Pill(theme, text, variant))
        pills.addStretch(1)
        right.addLayout(pills)
        self.progress = controls.ProgressBar(theme)
        self.progress.hide()
        right.addWidget(self.progress)
        banner = QtWidgets.QFrame()
        banner.setObjectName("toolBanner")
        banner_layout = QtWidgets.QVBoxLayout(banner)
        banner_layout.setContentsMargins(px(12), px(10), px(12), px(10))
        banner_layout.setSpacing(px(4))
        title = QtWidgets.QLabel("Large result")
        title.setObjectName("toolBannerTitle")
        banner_layout.addWidget(title)
        banner_layout.addWidget(controls.muted("About 2.4 million polygons. 3ds Max may become slow; choose a lower "
                                               "quality if this is too much."))
        right.addWidget(banner)
        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(px(6))
        for text, icon, variant in (("Secondary", "copy", "secondary"), ("Ghost", "eye", "ghost")):
            buttons.addWidget(controls.Button(text, theme, icon=icon, variant=variant))
        disabled = controls.Button("Disabled", theme, icon="download")
        disabled.setEnabled(False)
        buttons.addWidget(disabled)
        buttons.addStretch(1)
        right.addLayout(buttons)
        right.addWidget(controls.section("Recent results"))
        results = QtWidgets.QListWidget()  # Long lists scroll with the thin pill scroll bar.
        for index in range(1, 41):
            results.addItem("Result {:02d}  ·  {:,} polygons".format(index, index * 1375))
        results.setCurrentRow(2)
        right.addWidget(results, 1)
        columns.addLayout(right, 1)
        self.status_pill = controls.Pill(theme, "Ready", "success")
        self.status_row.insertWidget(0, self.status_pill)
        self.set_status("Select objects and press Run.")

    def eventFilter(self, watched, event):
        if watched is getattr(self, "_search", None) and event.type() in (QtCore.QEvent.Resize, QtCore.QEvent.Show):
            size = watched.height() - px(6)  # A real button inside the field's right end.
            self._search_button.setGeometry(watched.width() - size - px(3), px(3), size, size)
            return False
        return ToolWindow.eventFilter(self, watched, event)

    def run(self):
        """A background job with progress: the worker gets plain data, results come back on the main thread."""
        def work(cancel, report):
            for step in range(1, 21):
                if cancel.is_set():
                    return "cancelled"
                time.sleep(0.1)
                report("Processing", step, 20)
            return "done"

        self.run_button.setEnabled(False)
        self.progress.start()
        self.status_pill.set_status("Working", "info")
        self.controller.run_job(work, self.progress.set_progress, self._finished)

    def _finished(self, result):
        self.progress.stop()
        self.run_button.setEnabled(True)
        failed = isinstance(result, Exception)
        self.status_pill.set_status("Failed" if failed else "Done", "error" if failed else "success")
        self.set_status("Failed: {}".format(result) if failed else "Finished.")
```
