# Template: Logging, crash log and the log view data

A rotating file log per Max version (never shown in the Listener), the faulthandler crash log with session marks, and the parsing the Logs window uses for filters and colours.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `python/mytool/logs.py`

```python
"""File logging. The log is never shown unless the user opens it from the Logs button.

The handler is owned by the session and removed on shutdown so relaunches do not stack handlers.
"""

import logging
import logging.handlers
import os
import re

LOGGER_NAME = "mytool"
FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  # No milliseconds.
# Host tag such as "max2027": each Max version gets its own files, so two running versions never share
# (and fight over rotating) one log.
_host = ""


def set_host(tag):
    global _host
    _host = "".join(c for c in str(tag) if c.isalnum())


def _file(folder, stem):
    return os.path.join(folder, "logs", "{}-{}.log".format(stem, _host) if _host else stem + ".log")


def log_path(folder):
    return _file(folder, "mytool")


def attach(folder):
    """Attach a rotating file handler; returns it so the owner can detach exactly this handler."""
    path = log_path(folder)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(path, maxBytes=2 * 1024 * 1024, backupCount=3,
                                                   encoding="utf-8")
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
    path = _file(folder, "crash")
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


def tail(folder, max_bytes=256 * 1024):
    """Last part of the current log file as text (for the log viewer)."""
    path = log_path(folder)
    if not os.path.isfile(path):
        return ""
    with open(path, "rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - max_bytes))
        data = handle.read()
    text = data.decode("utf-8", errors="replace")
    if size > max_bytes:
        text = text.split("\n", 1)[-1]  # Drop the partial first line.
    return text


# Log viewer model (pure; ui/dialogs.LogDialog renders it with theme colours) ---------------------------
_RECORD = re.compile(r"^(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d)(?:,\d{3})? "
                     r"(DEBUG|INFO|WARNING|ERROR|CRITICAL) +(\S+?): ?(.*)$")
LEVEL_ROLES = {"DEBUG": "debug", "INFO": "info", "WARNING": "warning", "ERROR": "error", "CRITICAL": "error"}
SUCCESS_PREFIXES = ("Started",)
SESSION_PREFIX = "Starting MyTool"
SOURCE_WIDTH = 15
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


def counts(records):
    warnings = sum(1 for r in records if r["level"] == "WARNING")
    errors = sum(1 for r in records if r["level"] in ("ERROR", "CRITICAL"))
    return len(records), warnings, errors


def view_rows(records, level_filter="all", query=""):
    """Rows of (text, role) runs for the viewer, after filtering by level and a case-insensitive query.

    Roles: day, session, time, level-<debug|info|warning|error>, source, text, message-<warning|error|
    success>, extra-<warning|error|info>, gap.
    """
    levels = FILTERS.get(level_filter, FILTERS["all"])
    needle = query.strip().lower()
    rows = []
    day = None
    indent = " " * (8 + 2 + 9 + 2 + SOURCE_WIDTH + 2)
    for record in records:
        if record["level"] not in levels:
            continue
        haystack = " ".join([record["source"], record["message"]] + record["extra"]).lower()
        if needle and needle not in haystack:
            continue
        if record["date"] != day:
            day = record["date"]
            rows.append([(" {} ".format(day), "day")])
        if record["message"].startswith(SESSION_PREFIX):
            rows.append([("", "gap")])
            rows.append([("▸ Session started {}".format(record["time"]), "session"),
                         ("  " + record["message"][len(SESSION_PREFIX):].strip(), "source")])
            continue
        role = LEVEL_ROLES[record["level"]]
        if role in ("warning", "error"):
            message_role = "message-" + role
        elif record["message"].startswith(SUCCESS_PREFIXES):
            message_role = "message-success"
        else:
            message_role = "text"
        source = record["source"]
        if len(source) > SOURCE_WIDTH:
            source = source[:SOURCE_WIDTH - 1] + "…"
        rows.append([(record["time"], "time"), ("  ", "text"), (" {:<7} ".format(record["level"]), "level-" + role),
                     ("  ", "text"), (source.ljust(SOURCE_WIDTH), "source"), ("  ", "text"),
                     (record["message"], message_role)])
        extra_role = "extra-" + (role if role in ("warning", "error") else "info")
        for line in record["extra"]:
            rows.append([(indent + line, extra_role)])
    return rows
```
