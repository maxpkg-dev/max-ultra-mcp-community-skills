# Template: Settings, Logs and About

Every window of the tool besides the main one has the main window's own chrome (`ToolDialog`: frameless, a title bar with the icon, the title and a round close button, the header shade, rounded corners, a size grip when resizable): modal ones (Settings, About, questions) veil the owner window, a modeless one (Logs, in [its own module](logs.md)) leaves it usable. Questions are `ConfirmDialog` / `ask`, never a `QMessageBox`. Settings with tabs and titled groups (Appearance first, switches for on / off options); About with the How to use card (`how_to_card`: numbered steps in help markup) and its buttons in a footer outside the scrolling body. Every dialog unifies its control heights when shown.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP, with the windows off screen.

## `python/mytool/ui/dialogs.py`

```python
"""Settings, About, questions and the base of every other window of the tool. All compose the shared controls and the
shared stylesheet; the Logs window is in logwindow.py.

Every window of the tool has the main window's own chrome (no Windows title bar). Every message is the tool's own:
questions are ConfirmDialog (`ask`), information, warnings and errors MessageDialog (`inform`), text prompts
InputDialog (`ask_text`), the donation request SupportDialog. Never QMessageBox, QInputDialog, QErrorMessage or QProgressDialog; only the system's file
and folder pickers stay native.
"""

import os
import platform
import sys

from .. import (DEVELOPER, DONATE_OFFERS, DONATE_URL, LINKS, SUBTITLE, TOOL_NAME, UPDATE_URL, __version__, themes,
               ui_scale)
from ..qt_compat import (BINDING, QtCore, QtGui, QtWidgets, Qt, exec_dialog, inherit_fonts, is_valid, own_keyboard,
                         qt_version, repolish, round_window_corners, work_area)
from ..ui_scale import pt, px, space
from . import controls
from .sections import SectionBook, choose_side, page_row
from .switch import Switch

DESCRIPTION = "What the tool does in two or three sentences: the input, the result in the scene, the main options."
DISCLAIMER = ""  # A warning block in About (third-party data, unofficial sources); "" leaves it out.
# How to use in About, as numbered steps in a card (help markup: **bold**, `code`, [label](https://...)); () leaves it
# out. Few words per step.
USE_STEPS = (
    "Run `StartMyTool.ms`: drag it into a viewport or use **Scripting > Run Script**.",
    "Fill in the fields. A red star marks what is required.",
    "Press **Run**. The mini log shows what is wrong, or one green line when all is well.",
)
USE_NOTE = "**View Logs** is at the bottom left of the window; Settings and About are at the bottom right."
CREDITS = "Lucide icons (ISC)."
# The welcome window of the first start (WelcomeDialog): (Lucide icon, title, help markup), few words each; () = no
# welcome window.
WELCOME_POINTS = (
    ("sparkles", "Quick start", "Fill in the fields and press **Run**. A red star marks what is required."),
    ("settings", "Make it yours", "The theme and the interface size are in **Settings**."),
    ("logs", "Help when needed", "**View Logs** shows what happened; send the logs to the developer."),
)
# The Support window (SupportDialog): why a donation matters, in the owner's own words; ask them, never invent facts
# about money. The first line is the heading beside the heart; then one idea per paragraph, few words.
DONATED_TEXT = "I've already donated, don't remind me"  # The reminder's way out: the user's word that they donated
SUPPORT_TEXT = (
    "{} is free, and it keeps improving thanks to the people who use it.".format(TOOL_NAME),
    "Every new version takes evenings of work: testing in each 3ds Max version, fixing what users report and keeping "
    "the tool working when 3ds Max changes.",
    "If {} saves you time, please consider a donation. Every contribution, big or small, keeps it going. "
    "Thank you!".format(TOOL_NAME),
)


class Veil(QtWidgets.QWidget):
    """Translucent cover over a tool window while a modal tool dialog is open. It lives and dies with its dialog: it
    goes when the dialog hides or is destroyed by any path, so a cover without a window can never stay behind. Nothing
    on it can be clicked: a window-modal dialog blocks every input to its owner window, the cover included."""

    def __init__(self, target, theme, dialog=None):
        QtWidgets.QWidget.__init__(self, target)
        self.target = target
        self.theme = theme
        self.dialog = dialog
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.NoFocus)
        target.installEventFilter(self)
        if dialog is not None:
            dialog.installEventFilter(self)  # Hidden: the cover goes too
            dialog.destroyed.connect(self._dialog_gone)  # Destroyed without a hide: the cover goes too
        self.setGeometry(target.rect())
        self.raise_()
        self.show()

    def eventFilter(self, watched, event):
        if watched is self.target and event.type() == QtCore.QEvent.Resize:
            self.setGeometry(watched.rect())
        elif watched is self.dialog and event.type() == QtCore.QEvent.Hide:
            QtCore.QTimer.singleShot(0, self._dialog_gone)
        return False

    def _dialog_gone(self, *_args):
        if is_valid(self):
            self.dispose()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        shade = QtGui.QColor(self.theme.color("recessed"))
        shade.setAlpha(150)
        painter.fillRect(self.rect(), shade)
        painter.end()

    def dispose(self):
        if not is_valid(self):
            return
        try:
            self.target.removeEventFilter(self)
            if self.dialog is not None and is_valid(self.dialog):
                self.dialog.removeEventFilter(self)
        except RuntimeError:  # The target or the dialog is already gone
            pass
        self.hide()
        self.deleteLater()


def _global_pos(event):
    """Global cursor position of a mouse event (PySide6 globalPosition, PySide2 globalPos)."""
    position = getattr(event, "globalPosition", None)
    return position().toPoint() if position else event.globalPos()


class ToolDialog(QtWidgets.QDialog):
    """Base for every window of the tool besides the main one, in the main window's own style: no Windows frame, a
    title bar with the tool's icon, the title and a round close button (red on hover), the dark header shade and
    rounded corners. Subclasses build into `self.content`. A modal dialog veils the owner window while visible; a
    modeless one (Logs) leaves the owner usable, so it can be watched while working. `resizable` adds a size grip."""

    HEADER_SHADE = 0.7  # As the main window (ToolWindow)

    def __init__(self, controller, title, parent, modal=True, resizable=False):
        QtWidgets.QDialog.__init__(self, parent)
        self.controller = controller
        self.modal = modal
        theme = controller.theme
        self.setObjectName("toolDialog")
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModal if modal else Qt.NonModal)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.veil = None
        self._drag = None
        self._placed = False  # Centred over the owner once, at the first show
        frame = QtWidgets.QVBoxLayout(self)
        frame.setContentsMargins(0, 0, 0, 0)
        frame.setSpacing(0)
        self.title_bar = QtWidgets.QFrame()
        self.title_bar.setObjectName("toolTitleBar")
        bar = QtWidgets.QHBoxLayout(self.title_bar)
        bar.setContentsMargins(space(12), space(8), space(8), space(6))  # Where the main window's title bar puts them
        bar.setSpacing(space(4))
        bar.addWidget(controls.BrandIcon(18))
        bar.addSpacing(space(4))
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("toolWindowTitle")
        bar.addWidget(self.title_label)
        bar.addStretch(1)
        close = controls.WindowButton("x", theme, "Close", close=True)
        close.clicked.connect(self.close)
        bar.addWidget(close)
        self.title_bar.installEventFilter(self)  # Dragging it moves the window
        frame.addWidget(self.title_bar)
        self.content = QtWidgets.QWidget()
        frame.addWidget(self.content, 1)
        self.grip = None
        if resizable:
            self.grip = QtWidgets.QSizeGrip(self)
            self.grip.setFixedSize(px(16), px(16))
        theme.register(self)

    # Moving by the title bar --------------------------------------------------------------------------
    def eventFilter(self, watched, event):
        if watched is self.title_bar:
            kind = event.type()
            if kind == QtCore.QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                handle = self.windowHandle()
                if handle is not None and hasattr(handle, "startSystemMove") and handle.startSystemMove():
                    return True  # Windows moves it (with snapping), Qt 5.15 and newer
                self._drag = _global_pos(event) - self.frameGeometry().topLeft()
                return True
            if kind == QtCore.QEvent.MouseMove and self._drag is not None:
                self.move(_global_pos(event) - self._drag)
                return True
            if kind == QtCore.QEvent.MouseButtonRelease:
                self._drag = None
        return QtWidgets.QDialog.eventFilter(self, watched, event)

    # Painting, showing ----------------------------------------------------------------------------------
    def header_bottom(self):
        return self.title_bar.geometry().bottom() + px(6)

    def paintEvent(self, event):
        """The dark shade behind the header, as in the main window."""
        QtWidgets.QDialog.paintEvent(self, event)
        bottom = self.header_bottom()
        shade = QtGui.QLinearGradient(0, 0, 0, bottom)
        dark = QtGui.QColor(0, 0, 0)
        dark.setAlphaF(self.HEADER_SHADE)
        shade.setColorAt(0.0, dark)
        shade.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(self)
        painter.fillRect(QtCore.QRect(0, 0, self.width(), bottom), shade)
        painter.end()

    def resizeEvent(self, event):
        QtWidgets.QDialog.resizeEvent(self, event)
        if self.grip is not None:
            self.grip.move(self.width() - self.grip.width(), self.height() - self.grip.height())
            self.grip.raise_()

    def showEvent(self, event):
        QtWidgets.QDialog.showEvent(self, event)
        own_keyboard([self] + self.findChildren(QtWidgets.QWidget))  # Esc, Enter and typing reach it, not 3ds Max
        inherit_fonts(self)  # Interface size for what the dialog built after its font was set.
        controls.unify_heights(self)  # One height for every field, dropdown and button
        if not self._placed:
            # Qt placed the dialog before the interface-size font and the control height made it taller: lay it out
            # at its real size now and centre it over its owner (else it sits below the middle).
            self._placed = True
            if self.layout() is not None:
                self.layout().activate()
            self.centre_on_owner()
        round_window_corners(self, self.controller.theme.colors.get("border"))  # Windows 11, as the main window
        if self.modal and self.veil is None and self.parentWidget() is not None:
            self.veil = Veil(self.parentWidget(), self.controller.theme, self)

    def centre_on_owner(self):
        """Centre over the owner's window, inside the work area of the screen it is on."""
        owner = self.parentWidget()
        if owner is None:
            return
        anchor = owner.window().frameGeometry()
        point = anchor.center() - QtCore.QPoint(self.width() // 2, self.height() // 2)
        area = work_area(anchor.center())
        if area is not None:
            point.setX(max(area.left(), min(point.x(), area.right() - self.width() + 1)))
            point.setY(max(area.top(), min(point.y(), area.bottom() - self.height() + 1)))
        self.move(point)

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
    inner.setContentsMargins(space(12), space(8), space(12), space(12))
    inner.setSpacing(space(6))
    caption = QtWidgets.QLabel(title)
    caption.setObjectName("toolGroupTitle")
    inner.addWidget(caption)
    form = QtWidgets.QFormLayout()
    form.setContentsMargins(0, 0, 0, 0)
    form.setHorizontalSpacing(space(12))
    form.setVerticalSpacing(space(6))
    form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
    form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    inner.addLayout(form)
    layout.addWidget(frame)
    return form


class SettingsDialog(ToolDialog):
    """The tool's settings in sections (sections.SectionBook): tabs on top for up to three sections, a list on the
    left from four (as the MaxPkg Package Manager); `side` forces one style. Every change saves at once.

    General holds the tool's own options (an example group here), Appearance the theme and the interface size,
    Updates the self-update (only with an UPDATE_URL), Support the donation (only with a DONATE_URL) and Reset, in
    red, puts every setting back. A tool adds its own sections to SECTIONS and a `_build_<key>` method for each."""

    SECTIONS = (("general", "General", "sliders-horizontal"), ("appearance", "Appearance", "palette"),
                ("updates", "Updates", "refresh-cw"), ("support", "Support", "heart"), ("reset", "Reset", "rotate-ccw"))
    DANGER = ("reset",)

    def __init__(self, controller, parent, side=None):
        ToolDialog.__init__(self, controller, "{} Settings".format(TOOL_NAME), parent, resizable=True)
        theme = controller.theme
        sections = [section for section in self.SECTIONS if self._applies(section[0])]
        self.side = choose_side(len(sections)) if side is None else bool(side)
        layout = QtWidgets.QVBoxLayout(self.content)
        if self.side:  # The list reaches the window's edges; the close button is in the title bar (and Esc)
            layout.setContentsMargins(0, space(4), 0, 0)
            self.resize(px(700), px(470))
        else:
            layout.setContentsMargins(space(16), space(16), space(16), space(16))
            self.resize(px(520), px(470))
        layout.setSpacing(space(8))
        self.book = SectionBook(theme, side=self.side)
        layout.addWidget(self.book, 1)
        for key, title, icon in sections:
            page = self.book.add_page(key, title, icon, danger=key in self.DANGER)
            getattr(self, "_build_" + key)(page, theme)
            page.addStretch(1)
        if not self.side:
            footer = QtWidgets.QHBoxLayout()
            footer.addStretch(1)
            close = controls.Button("Close", theme)
            close.clicked.connect(self.close)
            controls.same_width(close)
            footer.addWidget(close)
            layout.addLayout(footer)

    def _applies(self, key):
        if key == "updates":
            return bool(UPDATE_URL)  # Only a tool that updates itself shows Updates
        if key == "support":
            return bool(DONATE_URL)
        return True

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

    def on_check_updates(self):
        self.update_button.setEnabled(False)
        self.update_label.setText("Checking...")

        def done(result):
            if not self.isVisible():
                return
            self.update_button.setEnabled(True)
            if result.get("error"):
                self.update_label.setText(result["error"])
            elif not result.get("version"):
                self.update_label.setText("You have the latest version ({}).".format(__version__))
            elif result.get("installed"):
                self.update_label.setText("Version {} is installed. It starts when {} opens again.".format(
                    result["version"], TOOL_NAME))
            else:
                self.update_label.setText("Version {} is available.".format(result["version"]))

        if not self.controller.check_updates(done):
            self.update_button.setEnabled(True)
            self.update_label.setText("An update check is already running.")

    def _build_general(self, page, theme):
        form = settings_group(page, "Example options")
        switch = Switch(theme, "An option the tool remembers")  # Switches, not check boxes, for on / off settings
        switch.setChecked(True)
        form.addRow(switch)
        combo = controls.ComboBox()
        for label in ("Balanced", "Fast", "Best"):
            combo.addItem(label)
        form.addRow("Quality", combo)

    def _build_appearance(self, page, theme):
        controller = self.controller
        form = settings_group(page, "Appearance")
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
        note.setSpacing(space(8))
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

    def _build_updates(self, page, theme):
        controller = self.controller
        self.auto_update = Switch(theme, "Check for updates automatically and install them in the background")
        self.auto_update.setChecked(bool(controller.prefs.get("auto_update")))
        self.auto_update.toggled.connect(lambda on: controller.set_preference("auto_update", bool(on)))
        page.addWidget(self.auto_update)
        self.update_label = controls.muted("Version {}. A new version starts when {} opens again.".format(
            __version__, TOOL_NAME))
        page.addWidget(self.update_label)
        self.update_button = controls.Button("Check Now", theme, icon="refresh-cw",
                                             tooltip="Look for a newer version of {}".format(TOOL_NAME))
        self.update_button.clicked.connect(self.on_check_updates)
        page.addLayout(page_row(self.update_button))

    def _build_support(self, page, theme):
        controller = self.controller
        page.addWidget(_wrapped(SUPPORT_TEXT[0], muted=True))
        donate = controls.Button("Donate", theme, icon="heart", variant="donate",
                                 tooltip="Opens the donation page in your browser")
        donate.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(DONATE_URL)))
        self.donate_shimmer = controls.Shimmer(donate)  # A light band sweeps over it every few seconds
        self.donate_shimmer.set_active(True)
        page.addLayout(page_row(donate))
        if "reminder" in DONATE_OFFERS:
            self.remind = Switch(theme, "Remind me about donations now and then (off once you have donated)")
            self.remind.setChecked(bool(controller.prefs.get("donate_reminders")))
            self.remind.toggled.connect(lambda on: controller.donations.set_reminders(on))
            page.addWidget(self.remind)

    def _build_reset(self, page, theme):
        page.addWidget(_wrapped("Put every setting of {} back to its default: the theme, the interface size, the "
                                "window's place and the options. Your scenes and logs are not touched.".format(
                                    TOOL_NAME), muted=True))
        reset = controls.Button("Reset Settings", theme, icon="rotate-ccw", variant="danger")
        reset.clicked.connect(self.on_reset)
        page.addLayout(page_row(reset))

    def on_reset(self):
        if ask(self.controller, self, "Reset Settings", "Reset every setting of {}?".format(TOOL_NAME),
               "The theme, the interface size, the window's place and the options go back to their defaults.",
               "Reset Settings"):
            self.close()
            self.controller.reset_settings()

class AboutDialog(ToolDialog):
    """Full-bleed hero (icon, name, subtitle), full-width accent divider, body with About insets (24/18, spacing 12),
    metadata, links, an optional disclaimer block, credits, a 36 px gap and Donate / Close. Header and hero keep a
    fixed vertical policy so extra height goes to the scrollable body. Unknown values are left out, never invented."""

    WIDTH = 460
    ICON_SIZE = 60

    def header_bottom(self):
        """The header shade ends where the hero starts: the hero's gradient takes over from the window colour there."""
        return self.title_bar.geometry().bottom() + 1

    def __init__(self, controller, parent):
        ToolDialog.__init__(self, controller, "About {}".format(TOOL_NAME), parent)
        theme = controller.theme
        self.setMinimumWidth(px(320))
        about = QtWidgets.QVBoxLayout(self.content)
        about.setContentsMargins(0, 0, 0, 0)
        about.setSpacing(0)

        hero = QtWidgets.QFrame()
        hero.setObjectName("toolAboutHero")
        hero.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        hero_layout = QtWidgets.QHBoxLayout(hero)
        hero_layout.setContentsMargins(space(24), space(16), space(24), space(16))
        hero_layout.setSpacing(space(12))
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
        content.setContentsMargins(space(24), space(16), space(24), space(16))
        content.setSpacing(space(12))
        content.addWidget(_wrapped(DESCRIPTION))
        if USE_STEPS:
            content.addWidget(how_to_card(theme, USE_STEPS, USE_NOTE))
        meta = QtWidgets.QGridLayout()
        meta.setHorizontalSpacing(space(16))
        meta.setVerticalSpacing(space(4))
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
            links.setSpacing(space(16))
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
            notice_layout.setContentsMargins(space(12), space(12), space(12), space(12))
            notice_layout.setSpacing(space(4))
            notice_title = QtWidgets.QLabel("Disclaimer")
            notice_title.setObjectName("toolBannerTitle")
            notice_layout.addWidget(notice_title)
            notice_layout.addWidget(_wrapped(DISCLAIMER, muted=True))
            content.addWidget(notice)
        content.addWidget(_wrapped("Credits: " + CREDITS, muted=True))
        content.addStretch(1)
        # The buttons stay at the bottom of the window, outside the scrolling part: always in view
        footer = QtWidgets.QWidget()
        buttons = QtWidgets.QHBoxLayout(footer)
        buttons.setContentsMargins(space(24), space(12), space(24), space(16))
        close = controls.Button("Close", theme)
        close.clicked.connect(self.close)
        if DONATE_URL and "about" in DONATE_OFFERS:
            donate = controls.Button("Donate", theme, icon="heart", variant="donate",
                                     tooltip="Why a donation helps {}".format(TOOL_NAME))
            donate.clicked.connect(lambda: controller.show_support(self))
            buttons.addWidget(donate)
            controls.same_width(donate, close)  # One size: a short Close never looks smaller than Donate
        else:
            controls.same_width(close)
        buttons.addStretch(1)
        buttons.addWidget(close)
        scroll.setWidget(body)
        controls.fade_edges(scroll, theme)  # A short screen: the body fades at its clipped edges
        about.addWidget(scroll, 1)
        about.setStretchFactor(scroll, 1)
        about.addWidget(footer)
        self._hero, self._body, self._footer, self._scroll = hero, body, footer, scroll
        self._fitted = False
        self._fit_to_screen()

    def showEvent(self, event):
        ToolDialog.showEvent(self, event)
        if not self._fitted:  # Style sheet fonts and paddings apply at polish time: measure again once.
            self._fitted = True
            self._fit_to_screen()
            self.centre_on_owner()
            QtCore.QTimer.singleShot(0, self._fit_to_content)

    def _fit_to_content(self):
        """Once, after the first layout pass: rich-text labels (the how-to card) measure taller at their real width
        than predicted, so grow by what still scrolls, within the work area."""
        extra = self._scroll.verticalScrollBar().maximum()
        area = work_area(self.frameGeometry().center())
        if extra > 0 and area is not None:
            self.resize(self.width(), min(self.height() + extra, int(area.height() * 0.9)))
            self.centre_on_owner()

    def _fit_to_screen(self):
        # A scroll area's size hint ignores its content; wrapped labels need the height at the real width.
        for widget in [self, self._body] + self._body.findChildren(QtWidgets.QWidget):
            widget.ensurePolished()
        content = self._body.layout()
        content.invalidate()
        body = content.totalHeightForWidth(px(self.WIDTH)) if content.hasHeightForWidth() else \
            self._body.sizeHint().height()
        height = (self.title_bar.sizeHint().height() + self._hero.sizeHint().height() + 2 + body +
                  self._footer.sizeHint().height() + 4)
        area = work_area(self.frameGeometry().center())  # By position, never self.screen() (qt_compat.live_screens).
        if area is not None:
            height = min(height, int(area.height() * 0.9))
        self.resize(px(self.WIDTH), max(px(360), height))


class ConfirmDialog(ToolDialog):
    """A question in the tool's own style, never a Windows message box: the question, what it means (help markup),
    a neutral button (the default: Enter or Esc keep things as they are) and the action (red when it destroys
    something)."""

    def __init__(self, controller, parent, title, question, detail="", action="OK", cancel="Cancel", danger=True):
        ToolDialog.__init__(self, controller, title, parent)
        theme = controller.theme
        layout = QtWidgets.QVBoxLayout(self.content)
        layout.setContentsMargins(space(16), space(8), space(16), space(16))
        layout.setSpacing(space(8))
        heading = QtWidgets.QLabel(question)
        heading.setObjectName("toolSection")
        heading.setWordWrap(True)
        layout.addWidget(heading)
        if detail:
            layout.addWidget(_rich(detail, theme))
        layout.addSpacing(space(6))
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(6))
        row.addStretch(1)
        self.keep_button = controls.Button(cancel, theme)
        self.keep_button.clicked.connect(self.reject)
        self.action_button = controls.Button(action, theme, variant="danger" if danger else "primary")
        controls.same_width(self.keep_button, self.action_button)
        self.action_button.clicked.connect(self.accept)
        row.addWidget(self.keep_button)
        row.addWidget(self.action_button)
        layout.addLayout(row)
        self.keep_button.setDefault(True)
        self.keep_button.setFocus()
        self.setFixedWidth(px(380))


def ask(controller, parent, title, question, detail="", action="OK", cancel="Cancel", danger=True):
    """Ask in a ConfirmDialog (modal, blocking); True when the action was chosen."""
    dialog = ConfirmDialog(controller, parent, title, question, detail, action, cancel, danger)
    try:
        return exec_dialog(dialog) == QtWidgets.QDialog.Accepted
    finally:
        dialog.dispose()


class MessageDialog(ToolDialog):
    """Information, a warning or an error in the tool's own style, never a Windows message box: an animated status icon
    on a tinted disc (as in the toasts), the message as a section title, what it means in help markup, and one button.
    `kind`: info, success, warning or error."""

    ICONS = {"info": ("info", "accent"), "success": ("done", "log_success"), "warning": ("warning", "log_warning"),
             "error": ("error", "log_error")}

    def __init__(self, controller, parent, title, message, detail="", kind="info", button="OK"):
        ToolDialog.__init__(self, controller, title, parent)
        from .toast import StatusIcon
        theme = controller.theme
        state, self._role = self.ICONS.get(kind, self.ICONS["info"])
        layout = QtWidgets.QVBoxLayout(self.content)
        layout.setContentsMargins(space(16), space(8), space(16), space(16))
        layout.setSpacing(space(8))
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(12))
        self.disc = QtWidgets.QWidget()
        self.disc.setFixedSize(px(40), px(40))
        disc_layout = QtWidgets.QHBoxLayout(self.disc)
        disc_layout.setContentsMargins(space(6), space(6), space(6), space(6))
        self.icon = StatusIcon(theme, size=28)
        self.icon.set_state(state)
        disc_layout.addWidget(self.icon)
        self.disc.installEventFilter(self)
        row.addWidget(self.disc, 0, Qt.AlignVCenter)  # On the vertical middle of the message and its detail
        texts = QtWidgets.QVBoxLayout()
        texts.setSpacing(space(2))
        heading = QtWidgets.QLabel(message)
        heading.setObjectName("toolSection")
        heading.setWordWrap(True)
        texts.addWidget(heading)
        if detail:
            texts.addWidget(_rich(detail, theme))
        row.addLayout(texts, 1)
        layout.addLayout(row)
        layout.addSpacing(space(6))
        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.button = controls.Button(button, theme, variant="primary" if kind != "error" else "secondary")
        controls.same_width(self.button)
        self.button.clicked.connect(self.accept)
        self.button.setDefault(True)
        buttons.addWidget(self.button)
        layout.addLayout(buttons)
        self.setFixedWidth(px(400))

    def eventFilter(self, watched, event):
        # getattr: PySide6 calls this filter from ToolDialog.__init__ already, before the disc exists
        if watched is getattr(self, "disc", None) and event.type() == QtCore.QEvent.Paint:  # The disc behind the icon
            painter = QtGui.QPainter(self.disc)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            fill = QtGui.QColor(self.controller.theme.colors[self._role])
            fill.setAlphaF(0.14)
            painter.setPen(Qt.NoPen)
            painter.setBrush(fill)
            painter.drawEllipse(QtCore.QRectF(self.disc.rect()))
            painter.end()
            return False
        return ToolDialog.eventFilter(self, watched, event)


def inform(controller, parent, title, message, detail="", kind="info", button="OK"):
    """Show a MessageDialog (modal, blocking) until it is closed. Prefer a toast for the outcome of an action; use
    this when the user must read it before going on (a failed save, a missing file)."""
    dialog = MessageDialog(controller, parent, title, message, detail, kind, button)
    try:
        exec_dialog(dialog)
    finally:
        dialog.dispose()


class InputDialog(ToolDialog):
    """A one-line prompt in the tool's own style, never a QInputDialog: a caption, the field checked while typing
    (`check(text)` returns "" or what is wrong, shown under the field in the error colour), Cancel and OK (OK only
    while the text is valid)."""

    def __init__(self, controller, parent, title, label, text="", placeholder="", check=None, action="OK"):
        ToolDialog.__init__(self, controller, title, parent)
        theme = controller.theme
        self._check = check or (lambda value: "" if value.strip() else "Required")
        layout = QtWidgets.QVBoxLayout(self.content)
        layout.setContentsMargins(space(16), space(8), space(16), space(16))
        layout.setSpacing(space(4))
        caption = QtWidgets.QLabel(label)
        caption.setObjectName("toolCaption")
        layout.addWidget(caption)
        self.field = QtWidgets.QLineEdit(text)
        self.field.setPlaceholderText(placeholder)
        self.field.textChanged.connect(self._validate)
        self.field.returnPressed.connect(lambda: self.ok.isEnabled() and self.accept())
        layout.addWidget(self.field)
        self.error = QtWidgets.QLabel("")
        self.error.setObjectName("toolError")
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        layout.addSpacing(space(6))
        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(space(6))
        buttons.addStretch(1)
        cancel = controls.Button("Cancel", theme)
        cancel.clicked.connect(self.reject)
        self.ok = controls.Button(action, theme, icon="check", variant="primary")
        controls.same_width(cancel, self.ok)
        self.ok.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(self.ok)
        layout.addLayout(buttons)
        self.setFixedWidth(px(380))
        self._validate(text)
        self.field.selectAll()
        self.field.setFocus()

    def _validate(self, text):
        problem = self._check(text)
        shown = problem if text.strip() else ""  # An empty field is not an error before the user typed
        self.error.setText(shown)
        self.error.setVisible(bool(shown))
        self.field.setProperty("invalid", "true" if shown else "false")
        repolish(self.field)
        self.ok.setEnabled(not problem)

    def text(self):
        return self.field.text().strip()


def ask_text(controller, parent, title, label, text="", placeholder="", check=None, action="OK"):
    """Ask for one line in an InputDialog (modal, blocking): the text, or None when cancelled."""
    dialog = InputDialog(controller, parent, title, label, text, placeholder, check, action)
    try:
        return dialog.text() if exec_dialog(dialog) == QtWidgets.QDialog.Accepted else None
    finally:
        dialog.dispose()


class SupportDialog(ToolDialog):
    """Why a donation matters, in the owner's words (SUPPORT_TEXT), with Not now and a shimmering Donate (as the
    MaxPkg Package Manager's Support window). Donate opens DONATE_URL in the browser and closes the window. As the
    start reminder (`reminder`) it also offers "I've already donated, don't remind me": an honour system that turns
    the reminders off for whoever says so, and makes no one who has not donated feel good about pressing it."""

    WIDTH = 440

    def __init__(self, controller, parent, reminder=False):
        ToolDialog.__init__(self, controller, "Support {}".format(TOOL_NAME), parent)
        theme = controller.theme
        layout = QtWidgets.QVBoxLayout(self.content)
        layout.setContentsMargins(space(16), space(8), space(16), space(16))
        layout.setSpacing(space(12))
        head = QtWidgets.QHBoxLayout()
        head.setSpacing(space(12))
        self.badge = QtWidgets.QWidget()
        self.badge.setFixedSize(px(38), px(38))
        self.badge.installEventFilter(self)
        head.addWidget(self.badge, 0, Qt.AlignVCenter)
        heading = QtWidgets.QLabel(SUPPORT_TEXT[0])  # The title bar already names the window
        heading.setObjectName("toolSection")
        heading.setWordWrap(True)
        head.addWidget(heading, 1, Qt.AlignVCenter)
        layout.addLayout(head)
        for text in SUPPORT_TEXT[1:]:
            paragraph = _wrapped(text, muted=True)
            paragraph.setFixedWidth(px(self.WIDTH - 36))
            layout.addWidget(paragraph)
        layout.addSpacing(space(4))
        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(space(8))
        if reminder:
            never = controls.StatusAction(DONATED_TEXT, theme, "heart",
                                          tooltip="Thank you! No more reminders. Settings > Support turns them on "
                                                  "again")
            never.clicked.connect(self.on_never)
            buttons.addWidget(never, 0, Qt.AlignVCenter)
        buttons.addStretch(1)
        later = controls.Button("Not now", theme)
        later.clicked.connect(self.reject)
        self.donate_button = controls.Button("Donate", theme, icon="heart", variant="donate",
                                             tooltip="Opens the donation page in your browser")
        self.donate_button.clicked.connect(self.on_donate)
        self.donate_button.setDefault(True)
        self.shimmer = controls.Shimmer(self.donate_button)  # A light band sweeps over it every few seconds
        self.shimmer.set_active(True)
        controls.same_width(later, self.donate_button)
        buttons.addWidget(later)
        buttons.addWidget(self.donate_button)
        layout.addLayout(buttons)
        self.setFixedWidth(px(self.WIDTH))

    def on_donate(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(DONATE_URL))
        self.accept()

    def on_never(self):
        self.controller.donations.set_reminders(False)
        self.reject()

    def eventFilter(self, watched, event):
        # getattr: PySide6 calls this filter from ToolDialog.__init__ already, before the badge exists
        if watched is getattr(self, "badge", None) and event.type() == QtCore.QEvent.Paint:  # Heart on a ringed disc
            colors = self.controller.theme.colors
            painter = QtGui.QPainter(self.badge)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            ring = QtGui.QColor(colors["donate_border"])
            fill = QtGui.QColor(colors["donate_background"])
            fill.setAlphaF(0.35)
            painter.setPen(QtGui.QPen(ring, 1))
            painter.setBrush(fill)
            painter.drawEllipse(QtCore.QRectF(self.badge.rect()).adjusted(0.5, 0.5, -0.5, -0.5))
            size = px(18)
            painter.drawPixmap((self.badge.width() - size) // 2, (self.badge.height() - size) // 2,
                               controls.icon_pixmap("heart", colors["donate_border"], size,
                                                    controls.device_pixel_ratio(self)))
            painter.end()
            return False
        return ToolDialog.eventFilter(self, watched, event)


class _Emblem(QtWidgets.QWidget):
    """The tool's icon on a soft glow of the accent colour, centred (the welcome window)."""

    ICON = 64

    def __init__(self, theme, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.theme = theme
        self.setFixedHeight(px(self.ICON + 40))
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        centre = QtCore.QPointF(self.width() / 2.0, self.height() / 2.0)
        radius = self.height() / 2.0  # The glow fades to nothing inside the block: no cut edge
        glow = QtGui.QRadialGradient(centre, radius)
        tone = QtGui.QColor(self.theme.colors["accent"])
        for stop, alpha in ((0.0, 0.26), (0.5, 0.10), (1.0, 0.0)):
            tone.setAlphaF(alpha)
            glow.setColorAt(stop, tone)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QBrush(glow))
        painter.drawEllipse(centre, radius, radius)
        size = px(self.ICON)
        painter.drawPixmap(int(centre.x() - size / 2.0), int(centre.y() - size / 2.0),
                           controls.brand_pixmap(size, controls.device_pixel_ratio(self)))
        painter.end()


class WelcomeDialog(ToolDialog):
    """The first start, not a second About: the tool's icon centred on a soft accent glow, "Welcome to Name" and what
    it is for centred below it (no hero plate, no accent line), three points (WELCOME_POINTS: icon, title, help
    markup), Open Settings and Get Started. Shown once (controller._ready)."""

    WIDTH = 460

    def __init__(self, controller, parent):
        ToolDialog.__init__(self, controller, "Welcome", parent)
        theme = controller.theme
        layout = QtWidgets.QVBoxLayout(self.content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        head = QtWidgets.QVBoxLayout()
        head.setContentsMargins(space(24), space(4), space(24), space(6))
        head.setSpacing(space(2))
        self.emblem = _Emblem(theme)
        head.addWidget(self.emblem)
        title = QtWidgets.QLabel("Welcome to {}".format(TOOL_NAME))
        title.setObjectName("toolAboutTitle")
        title.setAlignment(Qt.AlignCenter)
        font = title.font()
        font.setPointSizeF(pt(15))
        font.setBold(True)
        title.setFont(font)
        head.addWidget(title)
        subtitle = controls.muted(SUBTITLE)
        subtitle.setAlignment(Qt.AlignCenter)
        head.addWidget(subtitle)
        layout.addLayout(head)
        body = QtWidgets.QVBoxLayout()
        body.setContentsMargins(space(24), space(16), space(24), space(8))
        body.setSpacing(space(12))
        self._discs = []
        for icon_name, heading, text in WELCOME_POINTS:
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(space(12))
            disc = QtWidgets.QLabel()
            disc.setFixedSize(px(34), px(34))
            disc.setProperty("icon", icon_name)
            self._discs.append(disc)
            row.addWidget(disc, 0, Qt.AlignVCenter)  # On the vertical middle of the point's title and line
            texts = QtWidgets.QVBoxLayout()
            texts.setSpacing(space(2))
            name = QtWidgets.QLabel(heading)
            name.setObjectName("toolSection")
            texts.addWidget(name)
            texts.addWidget(_rich(text, theme))
            row.addLayout(texts, 1)
            body.addLayout(row)
        layout.addLayout(body)
        buttons = QtWidgets.QHBoxLayout()
        buttons.setContentsMargins(space(24), space(12), space(24), space(16))
        buttons.setSpacing(space(8))
        settings_button = controls.Button("Open Settings", theme, icon="settings")
        settings_button.clicked.connect(lambda: (self.close(), controller.show_settings()))
        start = controls.Button("Get Started", theme, icon="play", variant="primary")
        start.clicked.connect(self.accept)
        start.setDefault(True)
        controls.same_width(settings_button, start)
        buttons.addWidget(settings_button)
        buttons.addStretch(1)
        buttons.addWidget(start)
        layout.addLayout(buttons)
        self.setFixedWidth(px(self.WIDTH))
        self._paint_discs(theme.colors)

    def _paint_discs(self, colors):
        size = px(34)
        ratio = controls.device_pixel_ratio(self)
        for disc in self._discs:
            pixmap = QtGui.QPixmap(int(size * ratio), int(size * ratio))
            pixmap.setDevicePixelRatio(ratio)
            pixmap.fill(Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            fill = QtGui.QColor(colors["accent"])
            fill.setAlphaF(0.16)
            painter.setPen(Qt.NoPen)
            painter.setBrush(fill)
            painter.drawEllipse(QtCore.QRectF(0, 0, size, size))
            icon = px(17)
            painter.drawPixmap((size - icon) // 2, (size - icon) // 2,
                               controls.icon_pixmap(disc.property("icon"), colors["accent"], icon, ratio))
            painter.end()
            disc.setPixmap(pixmap)


def how_to_card(theme, steps, note="", title="How to use"):
    """Steps in a card of their own: a title, numbered steps (controls.NumberBadge) with room between them, a line and
    a note. Steps and note use help markup (controls.help_html)."""
    card = QtWidgets.QFrame()
    card.setObjectName("toolHowTo")
    layout = QtWidgets.QVBoxLayout(card)
    layout.setContentsMargins(space(16), space(12), space(16), space(12))
    layout.setSpacing(space(12))
    heading = QtWidgets.QLabel(title)
    heading.setObjectName("toolSection")
    layout.addWidget(heading)
    grid = QtWidgets.QGridLayout()
    grid.setHorizontalSpacing(space(12))
    grid.setVerticalSpacing(space(8))
    for row, step in enumerate(steps):
        grid.addWidget(controls.NumberBadge(row + 1, theme), row, 0, Qt.AlignTop)
        text = _rich(step, theme)
        text.setContentsMargins(0, space(2), 0, 0)  # The first line on the number's centre line
        grid.addWidget(text, row, 1)
    grid.setColumnStretch(1, 1)
    layout.addLayout(grid)
    if note:
        layout.addWidget(_rule())
        layout.addWidget(_rich(note, theme, muted=True))
    return card


def _rich(text, theme, muted=False):
    """A wrapped label from help markup (controls.help_html): bold terms, code chips, links that open."""
    label = QtWidgets.QLabel(controls.help_html(text, theme.colors, "muted_text" if muted else "text"))
    label.setTextFormat(Qt.RichText)
    label.setWordWrap(True)
    label.setOpenExternalLinks(True)
    label.setTextInteractionFlags(Qt.TextBrowserInteraction)
    return label


def _rule():
    """A thin line between parts of a dialog."""
    line = QtWidgets.QFrame()
    line.setObjectName("toolRule")
    line.setFixedHeight(1)
    return line


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


from .logwindow import LogDialog  # noqa: E402,F401  (the Logs window lives in its own module)
```
