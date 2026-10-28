# Template: Settings, Logs and About

Modal tool dialogs with a veil over the owner window: Settings with tabs and titled groups (Appearance first), the Logs window, and About.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `python/mytool/ui/dialogs.py`

```python
"""Settings, Logs and About. All compose the shared controls and the shared stylesheet."""

import os
import platform
import sys

from .. import DEVELOPER, DONATE_URL, LINKS, SUBTITLE, TOOL_NAME, __version__, logs, settings, themes, ui_scale
from ..qt_compat import BINDING, QtCore, QtGui, QtWidgets, Qt, inherit_fonts, qt_version, work_area
from ..ui_scale import pt, px
from . import controls

DESCRIPTION = "What the tool does in two or three sentences: the input, the result in the scene, the main options."
DISCLAIMER = ""  # A warning block in About (third-party data, unofficial sources); "" leaves it out.
CREDITS = "Lucide icons (ISC)."


class Veil(QtWidgets.QWidget):
    """Translucent cover over a tool window while a modal tool dialog is open."""

    def __init__(self, target, theme):
        QtWidgets.QWidget.__init__(self, target)
        self.target = target
        self.theme = theme
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.NoFocus)
        target.installEventFilter(self)
        self.setGeometry(target.rect())
        self.raise_()
        self.show()

    def eventFilter(self, watched, event):
        if watched is self.target and event.type() == QtCore.QEvent.Resize:
            self.setGeometry(watched.rect())
        return False

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        shade = QtGui.QColor(self.theme.color("recessed"))
        shade.setAlpha(150)
        painter.fillRect(self.rect(), shade)
        painter.end()

    def dispose(self):
        self.target.removeEventFilter(self)
        self.hide()
        self.deleteLater()


class ToolDialog(QtWidgets.QDialog):
    """Base for modal tool dialogs: themed, veils the owner window while visible."""

    def __init__(self, controller, title, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.controller = controller
        self.setObjectName("toolDialog")
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModal)
        # Explicit hints: before the first show windowFlags() is a bare Qt.Dialog, and masking it alone left Windows
        # drawing a greyed-out close button. No "?" button.
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint)
        self.veil = None
        controller.theme.register(self)

    def showEvent(self, event):
        QtWidgets.QDialog.showEvent(self, event)
        inherit_fonts(self)  # Interface size for what the dialog built after its font was set.
        if self.veil is None and self.parentWidget() is not None:
            self.veil = Veil(self.parentWidget(), self.controller.theme)

    def hideEvent(self, event):
        self._drop_veil()
        QtWidgets.QDialog.hideEvent(self, event)

    def _drop_veil(self):
        if self.veil is not None:
            self.veil.dispose()
            self.veil = None

    def dispose(self):
        self._drop_veil()
        self.controller.theme.unregister(self)
        self.hide()
        self.deleteLater()


def settings_group(layout, title):
    """A titled block of the Settings window (grouped, named controls). Returns its form layout."""
    frame = QtWidgets.QFrame()
    frame.setObjectName("toolSettingsGroup")
    inner = QtWidgets.QVBoxLayout(frame)
    inner.setContentsMargins(px(12), px(8), px(12), px(10))
    inner.setSpacing(px(6))
    caption = QtWidgets.QLabel(title)
    caption.setObjectName("toolGroupTitle")
    inner.addWidget(caption)
    form = QtWidgets.QFormLayout()
    form.setContentsMargins(0, 0, 0, 0)
    form.setHorizontalSpacing(px(12))
    form.setVerticalSpacing(px(6))
    form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
    form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    inner.addLayout(form)
    layout.addWidget(frame)
    return form


def settings_page(tabs, title):
    page = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(page)
    layout.setContentsMargins(px(10), px(12), px(10), px(10))
    layout.setSpacing(px(10))
    tabs.addTab(page, title)
    return layout


class SettingsDialog(ToolDialog):
    """Tabs; the General tab starts with Appearance (theme, interface size). The tool adds its own groups below and
    its own tabs after it."""

    def __init__(self, controller, parent):
        ToolDialog.__init__(self, controller, "{} Settings".format(TOOL_NAME), parent)
        theme = controller.theme
        self.resize(px(520), px(460))
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(px(16), px(16), px(16), px(16))
        layout.setSpacing(px(8))
        tabs = QtWidgets.QTabWidget()
        tabs.setDocumentMode(False)
        layout.addWidget(tabs, 1)
        general = settings_page(tabs, "General")

        form = settings_group(general, "Appearance")
        self.theme_combo = controls.ComboBox()
        for theme_id, name in themes.list_themes(controller.root):
            self.theme_combo.addItem(name, theme_id)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(theme.theme_id)))
        self.theme_combo.currentIndexChanged.connect(self.on_theme_selected)
        form.addRow("Theme", self.theme_combo)
        # Interface size applies while windows are built, so on reopening.
        self.scale_combo = controls.ComboBox()
        self.scale_combo.addItem("Auto ({})".format(ui_scale.percent(ui_scale.current["auto"])), "auto")
        for value in ui_scale.CHOICES:
            self.scale_combo.addItem(ui_scale.percent(value), str(value))
        chosen = str(controller.prefs.get("ui_scale") or "auto")
        self.scale_combo.setCurrentIndex(max(0, self.scale_combo.findData(chosen)))
        self.scale_combo.setToolTip("The size of {}'s text, buttons and windows. Auto follows the screen (larger on "
                                    "2K and 4K) and Windows scaling.".format(TOOL_NAME))
        self.scale_combo.currentIndexChanged.connect(self.on_scale_selected)
        form.addRow("Interface size", self.scale_combo)
        note = QtWidgets.QHBoxLayout()
        note.setSpacing(px(8))
        note.addWidget(controls.muted("Applies when {} opens again.".format(TOOL_NAME)), 1)
        self.reopen_button = controls.Button("Reopen Now", theme, icon="refresh-cw",
                                             tooltip="Close {} and open it again with the new size".format(TOOL_NAME))
        self.reopen_button.clicked.connect(self.on_reopen)
        note.addWidget(self.reopen_button)
        self.scale_note_row = QtWidgets.QWidget()
        self.scale_note_row.setLayout(note)
        self.scale_note_row.hide()
        form.addRow(self.scale_note_row)
        self.theme_error = QtWidgets.QLabel("")
        self.theme_error.setObjectName("toolError")
        self.theme_error.setWordWrap(True)
        self.theme_error.hide()
        form.addRow(self.theme_error)

        form = settings_group(general, "Example options")
        box = QtWidgets.QCheckBox("An option the tool remembers")
        box.setCursor(Qt.PointingHandCursor)
        box.setChecked(True)
        form.addRow(box)
        combo = controls.ComboBox()
        for label in ("Balanced", "Fast", "Best"):
            combo.addItem(label)
        form.addRow("Quality", combo)
        general.addStretch(1)

        footer = QtWidgets.QHBoxLayout()
        footer.addStretch(1)
        close = controls.Button("Close", theme)
        close.clicked.connect(self.close)
        footer.addWidget(close)
        layout.addLayout(footer)

    def on_theme_selected(self, index):
        theme_id = self.theme_combo.itemData(index)
        error = self.controller.theme.select(theme_id)
        self.theme_error.setVisible(bool(error))
        self.theme_error.setText(error or "")
        if error and "not saved" not in error:  # The previous theme stays: show it in the picker again.
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(self.controller.theme.theme_id)))
            self.theme_combo.blockSignals(False)

    def on_scale_selected(self, index):
        self.controller.set_preference("ui_scale", self.scale_combo.itemData(index))
        self.reopen_button.setVisible(self.controller.can_reopen())
        self.scale_note_row.setVisible(True)

    def on_reopen(self):
        self.close()
        self.controller.reopen()


class LogDialog(ToolDialog):
    """Readable log: filter by level, search, live updates; records drawn with the theme's log colours.

    The file stays plain text (Copy Diagnostics, Open Folder); only the view is formatted.
    """

    FILTERS = (("all", "All", "Every record"), ("warnings", "Warnings", "Warnings and errors"),
               ("errors", "Errors", "Errors only"))

    def __init__(self, controller, parent):
        ToolDialog.__init__(self, controller, "{} Log".format(TOOL_NAME), parent)
        theme = controller.theme
        self.resize(px(900), px(520))
        self.records = []
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(px(14), px(14), px(14), px(12))
        layout.setSpacing(px(10))

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(px(10))
        self.level_filter = controls.Segmented(self.FILTERS, theme, "all")
        self.level_filter.setFixedWidth(px(270))
        self.level_filter.changed.connect(lambda *_: self.render())
        top.addWidget(self.level_filter)
        self.query = QtWidgets.QLineEdit()
        self.query.setPlaceholderText("Filter messages")
        self.query.setClearButtonEnabled(True)
        self.query.textChanged.connect(lambda *_: self.render())
        top.addWidget(self.query, 1)
        self.summary = controls.muted("", wrap=False)
        top.addWidget(self.summary)
        layout.addLayout(top)

        self.text = QtWidgets.QTextEdit()
        self.text.setObjectName("toolLogView")
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.text.setUndoRedoEnabled(False)
        font = QtGui.QFont("Cascadia Mono")
        if not QtGui.QFontInfo(font).fixedPitch():
            font = QtGui.QFont("Consolas")
        if not QtGui.QFontInfo(font).fixedPitch():
            font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        font.setPointSizeF(pt(9.0))
        self.text.setFont(font)
        self.text.document().setDocumentMargin(10)
        layout.addWidget(self.text, 1)

        row = QtWidgets.QHBoxLayout()
        refresh = controls.Button("Refresh", theme, icon="refresh-cw")
        refresh.clicked.connect(self.reload)
        self.live = QtWidgets.QCheckBox("Live")
        self.live.setToolTip("Refresh every 2 seconds while this window is open")
        self.live.setCursor(Qt.PointingHandCursor)
        self.copy_button = controls.Button("Copy Diagnostics", theme, icon="copy",
                                           tooltip="Copy versions and the recent log for a bug report")
        self.copy_button.clicked.connect(self.copy_diagnostics)
        folder = controls.Button("Open Folder", theme, icon="folder-open")
        folder.clicked.connect(lambda: open_folder(os.path.dirname(logs.log_path(settings.user_data_dir()))))
        close = controls.Button("Close", theme)
        close.clicked.connect(self.close)
        for widget in (refresh, self.live, self.copy_button, folder):
            row.addWidget(widget)
        row.addStretch(1)
        row.addWidget(close)
        layout.addLayout(row)

        self.copy_timer = QtCore.QTimer(self)  # "Copied" for 2 s, then the caption comes back.
        self.copy_timer.setSingleShot(True)
        self.copy_timer.setInterval(2000)
        self.copy_timer.timeout.connect(lambda: self.copy_button.setText("Copy Diagnostics"))
        self.live_timer = QtCore.QTimer(self)
        self.live_timer.setInterval(2000)
        self.live_timer.timeout.connect(self.reload)
        self.live.toggled.connect(lambda on: self.live_timer.start() if on else self.live_timer.stop())
        theme.subscribe(self._on_theme)
        self.reload()

    def _on_theme(self, _colors):
        self.render()

    def reload(self):
        records = logs.parse_records(logs.tail(settings.user_data_dir()))
        if records != self.records or not self.text.document().characterCount() > 1:
            self.records = records
            self.render()

    def _formats(self):
        colors = self.controller.theme.colors

        def fmt(color, background=None, bold=False, italic=False):
            text_format = QtGui.QTextCharFormat()
            text_format.setForeground(QtGui.QColor(color))
            if background:
                text_format.setBackground(QtGui.QColor(background))
            if bold:
                text_format.setFontWeight(QtGui.QFont.Bold)
            text_format.setFontItalic(italic)
            return text_format

        return {
            "text": fmt(colors["field_text"]),
            "gap": fmt(colors["field_text"]),
            "time": fmt(colors["muted_text"]),
            "source": fmt(colors["log_system"]),
            "day": fmt(colors["muted_text"], colors["log_support_background"], bold=True),
            "session": fmt(colors["accent"], bold=True),
            "level-debug": fmt(colors["log_debug"], colors["log_debug_background"], bold=True),
            "level-info": fmt(colors["log_info"], colors["log_info_background"], bold=True),
            "level-warning": fmt(colors["log_warning"], colors["log_warning_background"], bold=True),
            "level-error": fmt(colors["log_error"], colors["log_error_background"], bold=True),
            "message-warning": fmt(colors["log_warning"]),
            "message-error": fmt(colors["log_error"]),
            "message-success": fmt(colors["log_success"]),
            "extra-info": fmt(colors["muted_text"], italic=True),
            "extra-warning": fmt(colors["log_warning"], italic=True),
            "extra-error": fmt(colors["log_error"]),
        }

    def render(self):
        bar = self.text.verticalScrollBar()
        at_end = bar.value() >= bar.maximum() - 4
        rows = logs.view_rows(self.records, self.level_filter.value(), self.query.text())
        total, warnings, errors = logs.counts(self.records)
        self.summary.setText("{:,} records  ·  {} warning{}  ·  {} error{}".format(
            total, warnings, "" if warnings == 1 else "s", errors, "" if errors == 1 else "s"))
        formats = self._formats()
        block = QtGui.QTextBlockFormat()
        block.setLineHeight(135, 1)  # 1 = proportional height (same value in PySide2 and PySide6).
        self.text.clear()
        cursor = QtGui.QTextCursor(self.text.document())
        cursor.beginEditBlock()
        for index, row in enumerate(rows or [[("Nothing matches the filter." if self.records
                                                else "The log is empty.", "time")]]):
            if index:
                cursor.insertBlock(block)
            else:
                cursor.setBlockFormat(block)
            for text, role in row:
                cursor.insertText(text, formats[role])
        cursor.endEditBlock()
        if at_end or not self.records:
            bar.setValue(bar.maximum())

    def dispose(self):
        self.live_timer.stop()
        self.controller.theme.unsubscribe(self._on_theme)
        ToolDialog.dispose(self)

    def copy_diagnostics(self):
        QtWidgets.QApplication.clipboard().setText(diagnostics() + "\n\n" + logs.tail(settings.user_data_dir(),
                                                                                       64 * 1024))
        self.copy_button.setText("Copied")
        self.copy_timer.start()


class AboutDialog(ToolDialog):
    """Full-bleed hero (icon, name, subtitle), full-width accent divider, body with About insets (24/18, spacing 12),
    metadata, links, an optional disclaimer block, credits, a 36 px gap and Donate / Close. Header and hero keep a
    fixed vertical policy so extra height goes to the scrollable body. Unknown values are left out, never invented."""

    WIDTH = 460
    ICON_SIZE = 60

    def __init__(self, controller, parent):
        ToolDialog.__init__(self, controller, "About {}".format(TOOL_NAME), parent)
        theme = controller.theme
        self.setMinimumWidth(px(320))
        about = QtWidgets.QVBoxLayout(self)
        about.setContentsMargins(0, 0, 0, 0)
        about.setSpacing(0)

        hero = QtWidgets.QFrame()
        hero.setObjectName("toolAboutHero")
        hero.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        hero_layout = QtWidgets.QHBoxLayout(hero)
        hero_layout.setContentsMargins(px(24), px(18), px(24), px(18))
        hero_layout.setSpacing(px(12))
        icon = QtWidgets.QLabel()
        icon.setFixedSize(px(self.ICON_SIZE), px(self.ICON_SIZE))
        icon.setPixmap(controls.brand_pixmap(px(self.ICON_SIZE), controls.device_pixel_ratio(self)))
        hero_layout.addWidget(icon, 0, Qt.AlignVCenter)
        names = QtWidgets.QVBoxLayout()
        names.setSpacing(0)
        title = QtWidgets.QLabel(TOOL_NAME)
        title.setObjectName("toolAboutTitle")
        font = title.font()
        font.setPointSizeF(pt(20))
        font.setBold(True)
        title.setFont(font)
        subtitle = QtWidgets.QLabel(SUBTITLE)
        subtitle.setObjectName("toolMuted")
        font = subtitle.font()
        font.setPointSizeF(pt(10))
        subtitle.setFont(font)
        names.addStretch(1)
        names.addWidget(title)
        names.addWidget(subtitle)
        names.addStretch(1)
        hero_layout.addLayout(names, 1)
        about.addWidget(hero)

        divider = QtWidgets.QFrame()
        divider.setObjectName("toolAccentDivider")
        divider.setFixedHeight(px(2))
        divider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        about.addWidget(divider)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QtWidgets.QWidget()
        body.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        content = QtWidgets.QVBoxLayout(body)
        content.setContentsMargins(px(24), px(18), px(24), px(18))
        content.setSpacing(px(12))
        content.addWidget(_wrapped(DESCRIPTION))
        meta = QtWidgets.QGridLayout()
        meta.setHorizontalSpacing(px(16))
        meta.setVerticalSpacing(px(4))
        rows = [("Version", __version__)] + ([("Developer", DEVELOPER)] if DEVELOPER else [])
        for row, (label, value) in enumerate(rows):
            meta.addWidget(controls.muted(label, wrap=False), row, 0)
            shown = QtWidgets.QLabel(value)
            shown.setTextInteractionFlags(Qt.TextSelectableByMouse)
            meta.addWidget(shown, row, 1)
        meta.setColumnStretch(1, 1)
        content.addLayout(meta)
        if LINKS:
            links = QtWidgets.QHBoxLayout()
            links.setSpacing(px(16))
            link_color = theme.colors.get("support_link", theme.colors.get("accent"))
            for label, address in LINKS:
                link = QtWidgets.QLabel('<a href="{0}" style="color:{1}; text-decoration:none">{2}</a>'.format(
                    address, link_color, label))
                link.setTextFormat(Qt.RichText)
                link.setOpenExternalLinks(True)
                link.setCursor(Qt.PointingHandCursor)
                links.addWidget(link)
            links.addStretch(1)
            content.addLayout(links)
        if DISCLAIMER:  # A warning block: rounded, warning tint fading down.
            notice = QtWidgets.QFrame()
            notice.setObjectName("toolBanner")
            notice_layout = QtWidgets.QVBoxLayout(notice)
            notice_layout.setContentsMargins(px(12), px(10), px(12), px(10))
            notice_layout.setSpacing(px(4))
            notice_title = QtWidgets.QLabel("Disclaimer")
            notice_title.setObjectName("toolBannerTitle")
            notice_layout.addWidget(notice_title)
            notice_layout.addWidget(_wrapped(DISCLAIMER, muted=True))
            content.addWidget(notice)
        content.addWidget(_wrapped("Credits: " + CREDITS, muted=True))
        content.addStretch(1)
        content.addSpacing(px(36))
        buttons = QtWidgets.QHBoxLayout()
        if DONATE_URL:
            donate = controls.Button("Donate", theme, icon="heart", variant="donate",
                                     tooltip="Support {} development".format(TOOL_NAME))
            donate.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(DONATE_URL)))
            buttons.addWidget(donate)
        buttons.addStretch(1)
        close = controls.Button("Close", theme)
        close.clicked.connect(self.close)
        buttons.addWidget(close)
        content.addLayout(buttons)
        scroll.setWidget(body)
        about.addWidget(scroll, 1)
        about.setStretchFactor(scroll, 1)
        self._hero, self._body = hero, body
        self._fitted = False
        self._fit_to_screen()

    def showEvent(self, event):
        ToolDialog.showEvent(self, event)
        if not self._fitted:  # Style sheet fonts and paddings apply at polish time: measure again once.
            self._fitted = True
            self._fit_to_screen()

    def _fit_to_screen(self):
        # A scroll area's size hint ignores its content; wrapped labels need the height at the real width.
        for widget in [self, self._body] + self._body.findChildren(QtWidgets.QWidget):
            widget.ensurePolished()
        content = self._body.layout()
        content.invalidate()
        body = content.totalHeightForWidth(px(self.WIDTH)) if content.hasHeightForWidth() else \
            self._body.sizeHint().height()
        height = self._hero.sizeHint().height() + 2 + body + 4
        area = work_area(self.frameGeometry().center())  # By position, never self.screen() (qt_compat.live_screens).
        if area is not None:
            height = min(height, int(area.height() * 0.9))
        self.resize(px(self.WIDTH), max(px(360), height))


def _wrapped(text, muted=False):
    label = QtWidgets.QLabel(text)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    if muted:
        label.setObjectName("toolMuted")
    return label


def open_folder(path):
    if path and os.path.isdir(path):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))


def diagnostics():
    try:
        from pymxs import runtime as rt
        max_version = str(rt.maxVersion())
    except Exception:
        max_version = "n/a"
    return "\n".join([
        "{} {}".format(TOOL_NAME, __version__),
        "3ds Max: {}".format(max_version),
        "Python: {}".format(sys.version.split()[0]),
        "Qt: {} {}".format(BINDING, qt_version()),
        "OS: {}".format(platform.platform()),
    ])
```
