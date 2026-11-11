# Template: Daily logs, the Logs window and the mini log

One log file per day (`mytool-2026-11-11.log`, appended and closed at once, so no file stays open; never shown in the Listener; days older than 60 are removed at start), the faulthandler crash log with session marks, the record parsing, the Logs window (`ui/logwindow.py`: day picker, All / Warnings / Errors, search, summary, Refresh, Live, Copy, Export, Open Folder, Clear Logs after a question, whole-record selection; not modal, resizable with a size grip; opened from View Logs) and the mini log inside the main window (`ui/statuslog.py`: statuses only, plus the pill painting both views share).

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP, with the windows off screen.

## `python/mytool/logs.py`

```python
"""File logging: one file per day. The log is never shown unless the user opens it from the Logs button.

Every record is appended to logs/mytool-YYYY-MM-DD.log and the file is closed again at once, so no file stays open:
Clear Logs can delete every day, and two 3ds Max versions can write the same day's file. Files older than 60 days are
removed when the tool starts. The handler is owned by the session and removed on shutdown so
relaunches do not stack handlers.
"""

import datetime
import logging
import os
import re
import threading

LOGGER_NAME = "mytool"
FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  # No milliseconds.
DAY_FILE = re.compile(r"^mytool-(\d{4})-(\d\d)-(\d\d)\.log$")
KEEP_DAYS = 60
READ_LIMIT = 2 * 1024 * 1024  # A day's log larger than this is shown from its last 2 MB
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
# Host tag such as "max2027": names the crash log of each 3ds Max version and appears in the session line.
_host = ""


def set_host(tag):
    global _host
    _host = "".join(c for c in str(tag) if c.isalnum())


def logs_folder(folder):
    return os.path.join(folder, "logs")


def day_path(folder, date=None):
    date = date or datetime.date.today()
    return os.path.join(logs_folder(folder), "mytool-{:%Y-%m-%d}.log".format(date))


def log_path(folder):
    """Today's log file."""
    return day_path(folder)


class DailyFileHandler(logging.Handler):
    """Appends each record to the day's file and closes it again (nothing stays open)."""

    def __init__(self, folder):
        logging.Handler.__init__(self)
        self.folder = folder
        self._write_lock = threading.Lock()

    def emit(self, record):
        try:
            line = self.format(record) + "\n"
            path = day_path(self.folder)
            with self._write_lock:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "a", encoding="utf-8") as stream:
                    stream.write(line)
        except Exception:
            self.handleError(record)


def attach(folder):
    """Attach the daily file handler; returns it so the owner can detach exactly this handler."""
    os.makedirs(logs_folder(folder), exist_ok=True)
    prune(folder)
    handler = DailyFileHandler(folder)
    handler.setFormatter(logging.Formatter(FORMAT, DATE_FORMAT))
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Keep MyTool output out of Max's listener and other handlers.
    logger.addHandler(handler)
    return handler


def enable_crash_log(folder):
    """Dump Python stacks of all threads to logs/crash[-host].log if Max dies from a native fault.

    Returns a release function. Does nothing if another component already enabled faulthandler.
    """
    import faulthandler
    if faulthandler.is_enabled():
        return lambda: None
    path = os.path.join(logs_folder(folder), "crash-{}.log".format(_host) if _host else "crash.log")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    stream = open(path, "a", encoding="utf-8")
    stream.write("\n=== session start ===\n")
    stream.flush()
    faulthandler.enable(file=stream, all_threads=True)

    def release():
        faulthandler.disable()
        stream.close()

    return release


def detach(handler):
    logger = logging.getLogger(LOGGER_NAME)
    if handler in logger.handlers:
        logger.removeHandler(handler)
    handler.close()


def get(name=None):
    return logging.getLogger(LOGGER_NAME if not name else LOGGER_NAME + "." + name)


# Days ----------------------------------------------------------------------------------------------------------
class LogDay(object):
    __slots__ = ("date", "file_path", "size")

    def __init__(self, date, file_path, size):
        self.date, self.file_path, self.size = date, file_path, size


def log_days(folder):
    """[LogDay] of the daily log files, newest first."""
    days = []
    try:
        names = os.listdir(logs_folder(folder))
    except OSError:
        return days
    for name in names:
        match = DAY_FILE.match(name)
        if not match:
            continue
        try:
            date = datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            path = os.path.join(logs_folder(folder), name)
            days.append(LogDay(date, path, os.path.getsize(path)))
        except (ValueError, OSError):
            continue
    days.sort(key=lambda day: day.date, reverse=True)
    return days


def day_label(date, today=None):
    """'Today', 'Yesterday' or 'Thu 29 Oct 2026' (English, whatever the Windows language)."""
    today = today or datetime.date.today()
    if date == today:
        return "Today"
    if date == today - datetime.timedelta(days=1):
        return "Yesterday"
    return "{} {} {} {}".format(WEEKDAYS[date.weekday()], date.day, MONTHS[date.month - 1], date.year)


def prune(folder, keep_days=KEEP_DAYS):
    """Remove day files older than `keep_days` (they are never shown again)."""
    limit = datetime.date.today() - datetime.timedelta(days=keep_days)
    for day in log_days(folder):
        if day.date < limit:
            try:
                os.remove(day.file_path)
            except OSError:
                pass


def log_files(folder):
    """Every log file of the tool: the day files and any older log of the same name (an earlier version's)."""
    try:
        names = os.listdir(logs_folder(folder))
    except OSError:
        return []
    return sorted(os.path.join(logs_folder(folder), name) for name in names
                  if name.startswith(LOGGER_NAME) and ".log" in name)


def clear_logs(folder):
    """Delete the log files of every day. Nothing is kept open, so they can all go; a file that is being written by
    another 3ds Max at this moment is skipped. Returns (removed, kept, freed bytes)."""
    removed, kept, freed = 0, 0, 0
    for path in log_files(folder):
        size = os.path.getsize(path) if os.path.isfile(path) else 0
        try:
            os.remove(path)
            removed, freed = removed + 1, freed + size
        except OSError:
            kept += 1
    return removed, kept, freed


def read_text(file_path, limit=READ_LIMIT):
    """A day's log text; a file over `limit` is read from its end (the cut first line is dropped)."""
    try:
        with open(file_path, "rb") as stream:
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(max(0, size - limit))
            data = stream.read()
    except OSError:
        return ""
    text = data.decode("utf-8", errors="replace").replace("\r\n", "\n")  # Windows line ends
    return text.split("\n", 1)[-1] if size > limit else text


def tail(folder, max_bytes=256 * 1024):
    """Last part of today's log as text (Copy Diagnostics)."""
    return read_text(log_path(folder), max_bytes)


def size_text(size):
    if size < 1024:
        return "{} B".format(size)
    if size < 1024 * 1024:
        return "{:.0f} KB".format(size / 1024.0)
    return "{:.1f} MB".format(size / (1024.0 * 1024.0))


def summary_text(records):
    """'35 records · 1 warning · 2 errors' (warnings and errors only when there are any)."""
    warnings = sum(1 for r in records if r["level"] == "WARNING")
    errors = sum(1 for r in records if r["level"] in ("ERROR", "CRITICAL"))

    def count(number, noun):
        return "{:,} {}{}".format(number, noun, "" if number == 1 else "s")
    parts = [count(len(records), "record")]
    if warnings:
        parts.append(count(warnings, "warning"))
    if errors:
        parts.append(count(errors, "error"))
    return " · ".join(parts)


def record_text(record):
    """A record as it stands in the file (for Copy and Export)."""
    head = "{} {} {:<7} {}: {}".format(record["date"], record["time"], record["level"], record["source"],
                                       record["message"])
    return "\n".join([head] + record["extra"])


# Records (pure; ui/logwindow.LogDialog renders them with theme colours) ----------------------------------
_RECORD = re.compile(r"^(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d)(?:,\d{3})? "
                     r"(DEBUG|INFO|WARNING|ERROR|CRITICAL) +(\S+?): ?(.*)$")
SUCCESS_PREFIXES = ("Started",)  # Shown in the success colour
SESSION_PREFIX = "Starting MyTool"  # The controller's first record of a session
FILTERS = {"all": ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"), "warnings": ("WARNING", "ERROR", "CRITICAL"),
           "errors": ("ERROR", "CRITICAL")}


def parse_records(text):
    """Log text -> [dict(date, time, level, source, message, extra=[continuation lines])].

    Accepts lines with or without milliseconds; lines without a header (tracebacks) belong to the
    record above them. Text before the first header is dropped (a partial record from tail()).
    """
    records = []
    for line in text.splitlines():
        match = _RECORD.match(line)
        if match:
            date, time, level, source, message = match.groups()
            if source.startswith(LOGGER_NAME + "."):
                source = source[len(LOGGER_NAME) + 1:]
            elif source == LOGGER_NAME:
                source = "core"
            records.append(dict(date=date, time=time, level=level, source=source, message=message, extra=[]))
        elif records and line.strip():
            records[-1]["extra"].append(line.rstrip())
    return records
```

## `python/mytool/ui/statuslog.py`

```python
"""The mini log inside the tool's window: the current state, never a history.

It is rebuilt on every check: the problems in red (errors) and yellow (warnings), or one green line when everything
is fine. Nothing piles up, so there is nothing to clear or copy; the history belongs in the Logs window.
One row per message in a monospaced font: a rounded level pill (OK green, ERROR red, WARNING yellow, INFO blue) and
the message; long messages wrap under the message, not under the pill. A row that points at a field is clickable as
a whole: on hover it is tinted in its level's colour from one edge of the box to the other, and a click goes to the
field.
"""

import math

from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal
from ..ui_scale import pt, px
from . import controls
from .controls import Themed

MAX_ENTRIES = 30
LEVELS = {  # level -> (label, colour role)
    "OK": ("OK", "log_success"),
    "ERROR": ("ERROR", "log_error"),
    "WARNING": ("WARN", "log_warning"),
    "INFO": ("INFO", "log_info"),
}
PILL_CHARS = 8  # Every pill has the same width, so the messages start in one column; ERROR has room to breathe
LINE_HEIGHT = 100  # percent: the room between rows comes from ROW_PADDING, so it is the same above and below
ROW_PADDING = 5  # Above and below the text of a row, inside its hover tint
SIDE_PADDING = 8
FONT_FAMILIES = ("Cascadia Mono", "Consolas", "Courier New")


def monospace(size):
    font = QtGui.QFont()
    font.setStyleHint(QtGui.QFont.TypeWriter)
    try:
        families = set(QtGui.QFontDatabase.families())  # Qt 6: static
    except TypeError:
        families = set(QtGui.QFontDatabase().families())  # Qt 5 (3ds Max 2022-2024)
    for family in FONT_FAMILIES:
        if family in families:
            font.setFamily(family)
            break
    font.setPointSizeF(size)
    return font


def event_point(event):
    """A mouse event's position in the widget (PySide6 position(), PySide2 pos())."""
    position = getattr(event, "position", None)
    return position().toPoint() if position else event.pos()


def _text_x(line, position):
    x = line.cursorToX(position)  # A number, or an (x, position) pair in some Qt for Python versions
    return x[0] if isinstance(x, tuple) else x


def pill_box(line, cap_height):
    """Top (within the block) and height of a level pill on `line`, centred on the capital letters, so the label
    sits in the middle of its pill. Every text line is measured the same way for even rows."""
    height = cap_height + px(6)
    return line.y() + line.ascent() - (cap_height + height) / 2.0, height


def paint_pills(view, painter, offset):
    """Every level pill of `view`: a rounded box over the blank cells kept for it in the text, and its label painted
    exactly in the middle, across and up and down (centred on the capital letters), whatever the label's length.
    `view.pills`: block -> (start, length, colour, label, label colour)."""
    document = view.document()
    layout = document.documentLayout()
    metrics = QtGui.QFontMetricsF(view.pill_font)
    ratio = view.devicePixelRatioF() or 1.0

    def snap(value):  # To a whole screen pixel (also at 125 % and 150 %): sharp text. Down, never up: round()
        return math.floor(value * ratio + 0.5) / ratio  # goes to the even pixel and shifts some labels right
    painter.setFont(view.pill_font)
    for number, (start, length, color, label, text_color) in view.pills.items():
        block = document.findBlockByNumber(number)
        line = block.layout().lineForTextPosition(start)
        if not line.isValid():
            continue
        origin = layout.blockBoundingRect(block).topLeft() + offset
        left, right = _text_x(line, start), _text_x(line, start + length)
        top, height = pill_box(line, view.cap_height)
        rect = QtCore.QRectF(origin.x() + left, origin.y() + top, right - left, height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(rect, height / 2.0, height / 2.0)
        painter.setPen(text_color)
        painter.drawText(QtCore.QPointF(snap(rect.center().x() - metrics.horizontalAdvance(label) / 2.0),
                                        snap(rect.center().y() + view.cap_height / 2.0)), label)
    painter.setPen(Qt.NoPen)


def _visual_span(document, number, cap_height):
    block = document.findBlockByNumber(number)
    layout = block.layout()
    origin = document.documentLayout().blockBoundingRect(block).top()
    first, last = layout.lineAt(0), layout.lineAt(max(0, layout.lineCount() - 1))
    if not first.isValid():
        return origin, origin
    last_top, height = pill_box(last, cap_height)
    return origin + pill_box(first, cap_height)[0], origin + last_top + height


def band_span(document, number, cap_height, to_edges=False):
    """Top and bottom (document coordinates) of the band behind a block: halfway to the block above and halfway to
    the block below, so the text has the same room above and below and neighbouring bands meet. The first and the
    last block reach the ends of the document (`to_edges`) or get the same room as between blocks."""
    count = document.blockCount()
    top, bottom = _visual_span(document, number, cap_height)
    above = _visual_span(document, number - 1, cap_height)[1] if number > 0 else None
    below = _visual_span(document, number + 1, cap_height)[0] if number + 1 < count else None
    half = ((below - bottom) if below is not None else (top - above) if above is not None else px(8)) / 2.0
    if above is not None:
        start = (above + top) / 2.0
    else:
        start = 0.0 if to_edges else top - half
    if below is not None:
        end = (bottom + below) / 2.0
    else:
        end = document.documentLayout().documentSize().height() if to_edges else bottom + half
    return start, end


class _LogView(QtWidgets.QTextEdit):
    """Read-only text whose blocks are rows. `rows`: block -> target (a field key, or ""); `pills`: block ->
    (start, length, colour). Pills and the hover tint are painted under the text (a character background has no
    rounded ends)."""

    row_clicked = Signal(str)

    def __init__(self):
        QtWidgets.QTextEdit.__init__(self)
        self.rows, self.pills = {}, {}
        self.hover = -1
        self.hover_colors = {}  # row -> the tint of its level (red for an error row)
        self.cap_height = 8.0
        self.pill_font = QtGui.QFont()
        self.setObjectName("toolStatusView")  # No style sheet padding: the hover tint goes from edge to edge
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.setWordWrapMode(QtGui.QTextOption.WordWrap)  # Breaks at spaces only: web addresses stay whole
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setFocusPolicy(Qt.NoFocus)

    def apply_margins(self):
        """Text inset from the box: SIDE_PADDING on the sides, ROW_PADDING above the first and below the last row."""
        document = self.document()
        document.setDocumentMargin(0)
        root = document.rootFrame()
        frame = root.frameFormat()
        frame.setLeftMargin(px(SIDE_PADDING))
        frame.setRightMargin(px(SIDE_PADDING))
        frame.setTopMargin(px(ROW_PADDING))
        frame.setBottomMargin(px(ROW_PADDING))
        root.setFrameFormat(frame)

    # ---- rows --------------------------------------------------------------------------------------------------
    def row_band(self, number):
        """The rectangle a row's tint fills: the full width of the box, the same room above and below the text."""
        top, bottom = band_span(self.document(), number, self.cap_height, to_edges=True)
        shift = self.verticalScrollBar().value()
        return QtCore.QRectF(0, top - shift, self.viewport().width(), bottom - top)

    def row_at(self, point):
        for number in self.rows:
            if self.row_band(number).contains(QtCore.QPointF(point)):
                return number
        return -1

    # ---- mouse -------------------------------------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        number = self.row_at(event_point(event))
        hover = number if self.rows.get(number) else -1
        if hover != self.hover:
            self.hover = hover
            self.viewport().setCursor(Qt.PointingHandCursor if hover >= 0 else Qt.ArrowCursor)
            self.viewport().update()
        event.accept()

    def leaveEvent(self, event):
        if self.hover >= 0:
            self.hover = -1
            self.viewport().update()
        QtWidgets.QTextEdit.leaveEvent(self, event)

    def mousePressEvent(self, event):
        target = self.rows.get(self.row_at(event_point(event)))
        if event.button() == Qt.LeftButton and target:
            self.row_clicked.emit(target)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        event.accept()

    # ---- painting ----------------------------------------------------------------------------------------------
    def _box_shape(self):
        """The inside of the rounded box in viewport coordinates: the tint never covers the rounded corners."""
        box = self.parentWidget()
        path = QtGui.QPainterPath()
        if box is None:
            path.addRect(QtCore.QRectF(self.viewport().rect()))
            return path
        inner = QtCore.QRectF(box.contentsRect())
        inner.translate(QtCore.QPointF(self.viewport().mapFrom(box, QtCore.QPoint(0, 0))))
        path.addRoundedRect(inner, px(5), px(5))
        return path

    def paintEvent(self, event):
        offset = QtCore.QPointF(0, -self.verticalScrollBar().value())
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        if self.hover >= 0:
            painter.save()
            painter.setClipPath(self._box_shape())
            painter.setBrush(self.hover_colors.get(self.hover, QtGui.QColor(0, 0, 0, 0)))
            painter.drawRect(self.row_band(self.hover))
            painter.restore()
        paint_pills(self, painter, offset)
        painter.end()
        QtWidgets.QTextEdit.paintEvent(self, event)


class StatusLog(QtWidgets.QWidget, Themed):
    tab_requested = Signal(str)

    def __init__(self, theme, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.entries = []  # [(level, message, target, place)]
        self._colors = theme.colors
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.view = _LogView()
        self.view.row_clicked.connect(self.tab_requested)
        self.mono_font = monospace(pt(8.5))
        layout.addWidget(controls.boxed(self.view, margin=0), 1)
        self.bind_theme(theme)

    # ---- content -----------------------------------------------------------------------------------------------
    def set_entries(self, entries):
        """Replace the rows with the current state (the log never keeps older messages). `entries`: (level, message,
        target) with level OK, ERROR, WARNING or INFO; a row with a target is clickable (`tab_requested`)."""
        self.entries = [tuple(entry) + ("", "", "")[:4 - len(entry)] for entry in entries][-MAX_ENTRIES:]
        self._render()

    def _on_theme(self, colors):
        self._colors = colors
        self._render()

    def _render(self):
        colors = self._colors
        view = self.view
        view.setUpdatesEnabled(False)
        view.clear()
        view.apply_margins()
        view.rows, view.pills = {}, {}
        view.hover = -1
        view.hover_colors = {}
        bold = QtGui.QFont(self.mono_font)
        bold.setBold(True)
        view.cap_height = QtGui.QFontMetricsF(bold).capHeight()
        view.pill_font = bold
        cursor = QtGui.QTextCursor(view.document())
        indent = QtGui.QFontMetricsF(self.mono_font).horizontalAdvance(" ") * (PILL_CHARS + 2)
        block = QtGui.QTextBlockFormat()
        block.setLineHeight(LINE_HEIGHT, 1)  # 1 = proportional height
        block.setLeftMargin(indent)  # Wrapped lines continue under the message
        block.setTextIndent(-indent)
        block.setTopMargin(px(ROW_PADDING) * 2)  # The space between rows; each tint takes half of it
        cursor.beginEditBlock()
        cursor.setBlockFormat(block)
        if not self.entries:
            muted = QtGui.QTextCharFormat()
            muted.setFont(self.mono_font)
            muted.setForeground(QtGui.QColor(colors["muted_text"]))
            cursor.insertText("Nothing to check yet.", muted)
        for index, (level, message, target, _place) in enumerate(self.entries):
            if index:
                cursor.insertBlock(block)
            label, role = LEVELS.get(level, LEVELS["INFO"])
            number = cursor.blockNumber()
            badge = " " * PILL_CHARS  # Room for the pill; its label is painted in the middle (paint_pills)
            view.pills[number] = (cursor.positionInBlock(), len(badge), QtGui.QColor(colors[role + "_background"]),
                                  label, QtGui.QColor(colors[role]))
            pill_format = QtGui.QTextCharFormat()
            pill_format.setFont(self.mono_font)
            pill_format.setFontWeight(QtGui.QFont.Bold)
            pill_format.setForeground(QtGui.QColor(colors[role]))
            cursor.insertText(badge, pill_format)
            text_format = QtGui.QTextCharFormat()
            text_format.setFont(self.mono_font)
            text_format.setForeground(QtGui.QColor(colors[role]))  # OK rows are green, errors red, warnings yellow
            cursor.insertText("  " + controls.keep_urls_whole(message), text_format)  # Addresses wrap whole
            if target:
                view.rows[number] = target
                tint = QtGui.QColor(colors[role])  # The row's own colour, light enough for the pill to stand out
                tint.setAlphaF(0.12)
                view.hover_colors[number] = tint
        cursor.endEditBlock()
        view.setUpdatesEnabled(True)
        view.moveCursor(QtGui.QTextCursor.Start)  # Else the first show scrolls to the cursor at the end
        view.verticalScrollBar().setValue(0)  # The first problem is in view
```

## `python/mytool/ui/logwindow.py`

```python
"""The Logs window.

A day picker (Today, Yesterday, Thu 29 Oct 2026 ... : one log file per day), the level filter (All / Warnings /
Errors), a search and a summary on top. Records in a monospaced view: each level is a rounded pill, long messages wrap
under the message column, no horizontal scrolling. Whole records are selected with a click, Shift, Ctrl or a drag, and
copied (Ctrl+C) or exported (Ctrl+E); the context menu has the same. Clear Logs deletes the log files of every day
after a confirmation. Live follows new records and new days. F5 reloads, Ctrl+F searches, Esc clears the selection,
then closes. The window is not modal: the tool stays usable while Live shows what it writes.
"""

import os

from .. import TOOL_NAME, logs, settings
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal
from ..ui_scale import pt, px, space
from . import controls
from .dialogs import ToolDialog, ask, diagnostics, open_folder
from .statuslog import band_span, event_point, monospace, paint_pills
from .switch import Switch

SOURCE_WIDTH = 12
MESSAGE_COLUMN = 8 + 2 + 9 + 2 + SOURCE_WIDTH + 2  # time, level pill and source, each followed by two spaces
SHOWN_LIMIT = 4000
LINE_HEIGHT = 135
LEVEL_ROLES = {"DEBUG": "log_debug", "INFO": "log_info", "WARNING": "log_warning", "ERROR": "log_error",
               "CRITICAL": "log_error"}
SCROLL_KEYS = (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home, Qt.Key_End)


def _stamp_of(path):
    """Size and modification time of a log file (Live reads it again when they change), or None."""
    try:
        status = os.stat(path)
    except OSError:
        return None
    return status.st_size, status.st_mtime


class RecordView(QtWidgets.QTextEdit):
    """Read-only log text with whole-record selection. `rows`: line -> record index; `pills`: line -> (start,
    length, colour, label, label colour). The selection and the pills are painted under the text."""

    selection_changed = Signal()
    menu_requested = Signal(QtCore.QPoint)

    def __init__(self):
        QtWidgets.QTextEdit.__init__(self)
        self.rows, self.pills = {}, {}
        self.count = 0
        self.selected = set()
        self.anchor = None
        self.selection_color = QtGui.QColor(0, 0, 0, 0)
        self.cap_height = 8.0
        self.pill_font = QtGui.QFont()
        self._dragging = False
        self.setReadOnly(True)  # Before the flags: setReadOnly resets them
        self.setUndoRedoEnabled(False)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.viewport().setCursor(Qt.ArrowCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.setWordWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)  # Paths have no spaces to break at
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(px(10))

    def row_at(self, point):
        block = self.cursorForPosition(point).block()
        rect = self.document().documentLayout().blockBoundingRect(block)
        top = rect.top() - self.verticalScrollBar().value()
        if not top <= point.y() < top + rect.height():
            return -1
        return self.rows.get(block.blockNumber(), -1)

    def set_selection(self, indices, anchor=None):
        self.selected = set(index for index in indices if 0 <= index < self.count)
        self.anchor = anchor if anchor is not None and 0 <= anchor < self.count else None
        self.viewport().update()
        self.selection_changed.emit()

    def select_all(self):
        self.set_selection(range(self.count), 0 if self.count else None)

    def clear_selection(self):
        self.set_selection(())

    def mousePressEvent(self, event):
        self.setFocus()
        index = self.row_at(event_point(event))
        modifiers = event.modifiers()
        if event.button() == Qt.LeftButton:
            if index < 0:
                if not modifiers & (Qt.ShiftModifier | Qt.ControlModifier):
                    self.clear_selection()
            elif modifiers & Qt.ShiftModifier and self.anchor is not None:
                low, high = sorted((self.anchor, index))
                span = set(range(low, high + 1))
                self.set_selection(self.selected | span if modifiers & Qt.ControlModifier else span, self.anchor)
            elif modifiers & Qt.ControlModifier:
                self.set_selection(self.selected ^ {index}, index)
            else:
                self.set_selection({index}, index)
            self._dragging = index >= 0 and not modifiers & (Qt.ShiftModifier | Qt.ControlModifier)
        elif event.button() == Qt.RightButton and index >= 0 and index not in self.selected:
            self.set_selection({index}, index)  # The menu acts on the record under the cursor
        event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.LeftButton and self.anchor is not None:
            point = event_point(event)
            index = self.row_at(point)
            if index >= 0:
                low, high = sorted((self.anchor, index))
                if self.selected != set(range(low, high + 1)):
                    self.set_selection(range(low, high + 1), self.anchor)
            if point.y() < 0 or point.y() > self.viewport().height():  # Keep scrolling past an edge
                bar = self.verticalScrollBar()
                bar.setValue(bar.value() + (-20 if point.y() < 0 else 20))
        event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        event.accept()

    def mouseDoubleClickEvent(self, event):
        event.accept()

    def contextMenuEvent(self, event):
        self.menu_requested.emit(event.globalPos())
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in SCROLL_KEYS:  # Only scrolling keys are the view's; the window has the shortcuts
            QtWidgets.QTextEdit.keyPressEvent(self, event)
        else:
            event.ignore()

    def paintEvent(self, event):
        document = self.document()
        offset = QtCore.QPointF(0, -self.verticalScrollBar().value())
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        if self.selected:  # One rounded band per run of selected lines, the same room above and below the text
            painter.setBrush(self.selection_color)
            run = None
            for number in range(document.blockCount() + 1):
                chosen = number < document.blockCount() and self.rows.get(number, -1) in self.selected
                if chosen:
                    run = (run[0] if run else number, number)
                elif run is not None:
                    top = band_span(document, run[0], self.cap_height)[0] + offset.y()
                    bottom = band_span(document, run[1], self.cap_height)[1] + offset.y()
                    painter.drawRoundedRect(QtCore.QRectF(px(4), top, self.viewport().width() - px(8), bottom - top),
                                            px(6), px(6))
                    run = None
        paint_pills(self, painter, offset)
        painter.end()
        QtWidgets.QTextEdit.paintEvent(self, event)


class LogDialog(ToolDialog):
    FILTERS = (("all", "All", "Every record"), ("warnings", "Warnings", "Warnings and errors"),
               ("errors", "Errors", "Errors only"))

    def __init__(self, controller, parent):
        # Modeless: the tool stays usable while the log is open, and Live shows what it writes
        ToolDialog.__init__(self, controller, "{} Logs".format(TOOL_NAME), parent, modal=False, resizable=True)
        theme = controller.theme
        self.resize(px(900), px(520))
        self.folder = settings.user_data_dir()
        self.records, self.shown, self.days = [], [], []
        self._stamp = None
        layout = QtWidgets.QVBoxLayout(self.content)
        layout.setContentsMargins(space(16), space(16), space(16), space(12))
        layout.setSpacing(space(12))

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(space(12))
        self.day = controls.ComboBox()
        self.day.setToolTip("Each day of 3ds Max work has its own log file")
        self.day.setMinimumWidth(px(160))
        self.day.currentIndexChanged.connect(lambda *_: self.load(to_end=True))
        top.addWidget(self.day)
        self.level = controls.Segmented(self.FILTERS, theme, "all")
        self.level.setFixedWidth(px(260))
        self.level.changed.connect(lambda *_: self.render(to_end=True))
        top.addWidget(self.level)
        self.query = QtWidgets.QLineEdit()
        self.query.setPlaceholderText("Filter messages  (Ctrl+F)")
        self.query.setClearButtonEnabled(True)
        self.query.textChanged.connect(lambda *_: self.render(to_end=True))
        top.addWidget(self.query, 1)
        self.summary = controls.muted("", wrap=False)
        top.addWidget(self.summary)
        layout.addLayout(top)

        self.view = RecordView()
        self.view.menu_requested.connect(self.show_menu)
        self.view.selection_changed.connect(self.sync_buttons)
        self.mono_font = monospace(pt(9.0))
        layout.addWidget(controls.boxed(self.view), 1)
        controls.fade_edges(self.view, theme, "field")  # A record cut at the top or bottom edge fades out

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(space(8))
        refresh = controls.Button("Refresh", theme, icon="refresh-cw", tooltip="Read the log again (F5)")
        refresh.clicked.connect(self.reload)
        self.live = Switch(theme, "Live")
        self.live.setToolTip("Show new records as they are written")
        self.copy_button = controls.Button("Copy", theme, icon="copy",
                                           tooltip="Copy the selected records, or every shown record (Ctrl+C)")
        self.copy_button.clicked.connect(self.copy_records)
        self.export_button = controls.Button("Export", theme, icon="download",
                                             tooltip="Save the shown records to a text file (Ctrl+E)")
        self.export_button.clicked.connect(self.export_records)
        folder = controls.Button("Open Folder", theme, icon="folder-open", tooltip="Open the folder with the log files")
        folder.clicked.connect(lambda: open_folder(os.path.dirname(logs.log_path(self.folder))))
        self.clear_button = controls.Button("Clear Logs", theme, icon="trash-2", variant="danger",
                                            tooltip="Delete the log files of every day")
        self.clear_button.clicked.connect(self.clear_logs)
        close = controls.Button("Close", theme)
        close.clicked.connect(self.close)
        for widget in (refresh, self.live):
            row.addWidget(widget)
        row.addStretch(1)
        for widget in (self.copy_button, self.export_button, folder, self.clear_button, close):
            row.addWidget(widget)
        layout.addLayout(row)

        self.flash_timer = QtCore.QTimer(self)  # "Copied" / "Exported" on a button for 2 s
        self.flash_timer.setSingleShot(True)
        self.flash_timer.setInterval(2000)
        self.flash_timer.timeout.connect(self._end_flash)
        self._flashing = None
        self.live_timer = QtCore.QTimer(self)
        self.live_timer.setInterval(2000)
        self.live_timer.timeout.connect(self._poll)
        self.live.toggled.connect(lambda on: self.live_timer.start() if on else self.live_timer.stop())
        theme.subscribe(self._on_theme)
        self._list_days(select_newest=True)  # A fresh open shows today
        self.load(to_end=True)

    # ---- data --------------------------------------------------------------------------------------------------
    def _list_days(self, select_newest):
        """Fill the day picker; keeps the chosen day unless `select_newest`."""
        self.days = logs.log_days(self.folder)
        current = None if select_newest else self.day.currentData()
        self.day.blockSignals(True)
        self.day.clear()
        for day in self.days:
            self.day.addItem(logs.day_label(day.date), day.file_path)
        if not self.days:
            self.day.addItem("No logs yet", "")
        self.day.setCurrentIndex(max(0, self.day.findData(current)) if current else 0)
        self.day.blockSignals(False)
        self.day.setEnabled(bool(self.days))

    def load(self, to_end):
        path = self.day.currentData() or ""
        self.records = logs.parse_records(logs.read_text(path)) if path else []
        self._stamp = _stamp_of(path) if path else None
        self.render(to_end)

    def reload(self):
        """Refresh / F5: the list of days and the chosen day read again."""
        self._list_days(select_newest=False)
        self.load(to_end=False)

    def _poll(self):
        """Live: a new day file or new lines in the shown one are read again."""
        if not self.isVisible():
            return
        if [day.file_path for day in logs.log_days(self.folder)] != [day.file_path for day in self.days]:
            newest = bool(self.days) and self.day.currentData() == self.days[0].file_path
            self._list_days(select_newest=newest)
            self.load(to_end=False)
        elif self.day.currentData() and _stamp_of(self.day.currentData()) != self._stamp:
            self.load(to_end=False)

    def _on_theme(self, _colors):
        self.render(to_end=False)

    # ---- view --------------------------------------------------------------------------------------------------
    def _shown(self):
        levels = logs.FILTERS.get(self.level.value() or "all", logs.FILTERS["all"])
        needle = self.query.text().strip().lower()
        result = []
        for record in self.records:
            if record["level"] not in levels:
                continue
            if needle and needle not in " ".join([record["source"], record["message"]] + record["extra"]).lower():
                continue
            result.append(record)
        return result

    def render(self, to_end):
        colors = self.controller.theme.colors
        view = self.view
        bar = view.verticalScrollBar()
        at_end = to_end or bar.value() >= bar.maximum() - 4
        position = bar.value()
        chosen = set(id(self.shown[i]) for i in view.selected if i < len(self.shown))
        shown = self._shown()[-SHOWN_LIMIT:]
        self.summary.setText(logs.summary_text(shown) if self.records else "")
        view.setUpdatesEnabled(False)
        view.clear()
        view.rows, view.pills = {}, {}
        accent = QtGui.QColor(colors["accent"])
        accent.setAlphaF(0.22)
        view.selection_color = accent
        bold = QtGui.QFont(self.mono_font)
        bold.setBold(True)
        view.cap_height = QtGui.QFontMetricsF(bold).capHeight()
        view.pill_font = bold
        cursor = QtGui.QTextCursor(view.document())
        hanging = QtGui.QFontMetricsF(self.mono_font).horizontalAdvance(" ") * MESSAGE_COLUMN
        block = QtGui.QTextBlockFormat()
        block.setLineHeight(LINE_HEIGHT, 1)
        block.setLeftMargin(hanging)  # Long lines continue under the message, not under the time
        block.setTextIndent(-hanging)
        cursor.beginEditBlock()
        cursor.setBlockFormat(block)
        first = [True]

        def run(text, role, bold=False, pill=None):
            character = QtGui.QTextCharFormat()
            character.setFont(self.mono_font)
            character.setForeground(QtGui.QColor(colors[role]))
            if bold:
                character.setFontWeight(QtGui.QFont.Bold)
            if pill is not None:  # (colour, label): the label is painted in the middle of the pill
                view.pills[cursor.blockNumber()] = (cursor.positionInBlock(), len(text), pill[0], pill[1],
                                                    QtGui.QColor(colors[role]))
            cursor.insertText(text, character)
            first[0] = False

        def line(record_index=-1):
            if record_index >= 0:
                view.rows[cursor.blockNumber()] = record_index
            cursor.insertBlock(block)

        if not shown:
            if not self.days:
                run("Nothing has been logged yet.", "muted_text")
            elif not self.records:
                run("This day's log is empty.", "muted_text")
            else:
                run("No records match the filter.", "muted_text")
        for index, record in enumerate(shown):
            if record["message"].startswith(logs.SESSION_PREFIX):
                if not first[0] and index:
                    line()  # A gap before every session
                run("Session started {}  ·  {}".format(record["time"], record["message"][len(logs.SESSION_PREFIX):]
                                                      .strip()), "accent", bold=True)
                view.rows[cursor.blockNumber()] = index
                line()
                continue
            role = LEVEL_ROLES.get(record["level"], "log_info")
            pill = QtGui.QColor(colors[role + "_background"])
            if record["level"] in ("WARNING", "ERROR", "CRITICAL"):
                message_role = role
            elif record["message"].startswith(logs.SUCCESS_PREFIXES):
                message_role = "log_success"
            else:
                message_role = "field_text"
            source = record["source"]
            source = source if len(source) <= SOURCE_WIDTH else source[:SOURCE_WIDTH - 1] + "…"
            view.rows[cursor.blockNumber()] = index
            run(record["time"], "muted_text")
            run("  ", "field_text")
            label = "WARN" if record["level"] == "WARNING" else record["level"][:7]
            run(" " * 9, role, True, (pill, label))
            run("  ", "field_text")
            run(source.ljust(SOURCE_WIDTH), "log_system")
            run("  " + record["message"], message_role)
            for extra in record["extra"]:
                line(index)
                run(" " * MESSAGE_COLUMN + extra, message_role if message_role != "field_text" else "muted_text")
            line(index)
        cursor.endEditBlock()
        self.shown = shown
        view.count = len(shown)
        view.set_selection([i for i, record in enumerate(shown) if id(record) in chosen])
        view.setUpdatesEnabled(True)
        if at_end:
            QtCore.QTimer.singleShot(0, lambda: bar.setValue(bar.maximum()))
        else:
            bar.setValue(min(position, bar.maximum()))
        self.sync_buttons()

    def sync_buttons(self):
        self.copy_button.setEnabled(bool(self.shown))
        self.export_button.setEnabled(bool(self.shown))
        self.clear_button.setEnabled(bool(logs.log_files(self.folder)))

    # ---- actions -----------------------------------------------------------------------------------------------
    def _selected_records(self):
        if self.view.selected:
            return [self.shown[index] for index in sorted(self.view.selected)]
        return self.shown

    def copy_records(self):
        records = self._selected_records()
        if records:
            QtWidgets.QApplication.clipboard().setText("\n".join(logs.record_text(r) for r in records))
            self._flash(self.copy_button, "Copied")

    def copy_diagnostics(self):
        QtWidgets.QApplication.clipboard().setText(diagnostics() + "\n\n" + logs.tail(self.folder, 64 * 1024))
        self._flash(self.copy_button, "Copied")

    def export_records(self):
        if not self.shown:
            return
        documents = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DocumentsLocation)
        target, _choice = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Log", os.path.join(documents, TOOL_NAME + ".log"), "Log files (*.log);;Text files (*.txt)")
        if not target:
            return
        try:
            with open(target, "w", encoding="utf-8") as stream:
                stream.write("\n".join(logs.record_text(r) for r in self.shown) + "\n")
        except OSError:
            self._flash(self.export_button, "Not saved")
            return
        self._flash(self.export_button, "Exported")

    def clear_logs(self):
        """Delete the log files of every day after a confirmation; the view then shows the empty state."""
        days = logs.log_days(self.folder)
        files = logs.log_files(self.folder)
        if not files:
            return
        size = logs.size_text(sum(os.path.getsize(path) for path in files if os.path.isfile(path)))
        if len(days) > 1:
            text = "The log files of {} days ({}) will be deleted. This cannot be undone.".format(len(days), size)
        else:
            text = "The log file ({}) will be deleted. This cannot be undone.".format(size)
        if not ask(self.controller, self, "Clear Logs", "Clear all logs?", text, "Clear Logs", "Cancel"):
            return
        _removed, kept, _freed = logs.clear_logs(self.folder)
        self.view.clear_selection()
        self._list_days(select_newest=True)
        self.load(to_end=True)
        if kept:
            self.summary.setText("{} file{} in use, kept".format(kept, "" if kept == 1 else "s"))

    def go_to_latest(self):
        """The newest day, scrolled to its last record."""
        if self.days and self.day.currentData() != self.days[0].file_path:
            self.day.setCurrentIndex(0)  # Loads the newest day
        bar = self.view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def show_menu(self, global_pos):
        theme = self.controller.theme
        menu = controls.Menu(theme, self)
        selected = bool(self.view.selected)
        menu.add_item("Search / Filter", "search", lambda: (self.query.setFocus(), self.query.selectAll()),
                      shortcut="Ctrl+F")
        menu.add_item("Copy Selected" if selected else "Copy All Shown", "copy", self.copy_records,
                      enabled=bool(self.shown), shortcut="Ctrl+C")
        menu.add_item("Select All", "check", self.view.select_all, enabled=bool(self.shown), shortcut="Ctrl+A")
        menu.add_item("Export…", "download", self.export_records, enabled=bool(self.shown), shortcut="Ctrl+E")
        menu.add_item("Copy Diagnostics", "info", self.copy_diagnostics)
        menu.add_item("Go to Latest", "chevron-down", self.go_to_latest)
        menu.addSeparator()
        menu.add_item("Clear Logs…", "trash-2", self.clear_logs, danger=True, enabled=self.clear_button.isEnabled())
        menu.popup_at(global_pos)

    def showEvent(self, event):
        ToolDialog.showEvent(self, event)
        if not getattr(self, "_opened", False):
            # The window opens for reading: the dialog itself takes the keys (Ctrl+F, Ctrl+C, F5, Esc), and no field
            # lights up its focus outline until the user picks one (Qt would give the focus to the day dropdown).
            self._opened = True
            self.setFocus(Qt.OtherFocusReason)

    def keyPressEvent(self, event):
        key = event.key()
        control = bool(event.modifiers() & Qt.ControlModifier)
        if key == Qt.Key_Escape:
            if self.view.selected:
                self.view.clear_selection()
            else:
                self.close()
        elif key == Qt.Key_F5:
            self.reload()
        elif control and key == Qt.Key_F:
            self.query.setFocus()
            self.query.selectAll()
        elif control and key == Qt.Key_C:
            self.copy_records()
        elif control and key == Qt.Key_A:
            self.view.select_all()
        elif control and key == Qt.Key_E:
            self.export_records()
        else:
            ToolDialog.keyPressEvent(self, event)

    def _flash(self, button, text):
        self._end_flash()
        self._flashing = (button, button.text())
        button.setText(text)
        self.flash_timer.start()

    def _end_flash(self):
        if self._flashing is not None:
            self._flashing[0].setText(self._flashing[1])
            self._flashing = None

    def dispose(self):
        self.live_timer.stop()
        self.controller.theme.unsubscribe(self._on_theme)
        ToolDialog.dispose(self)
```
