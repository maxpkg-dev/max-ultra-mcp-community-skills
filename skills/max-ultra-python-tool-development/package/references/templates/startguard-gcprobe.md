# Template: Start guard and garbage-collector probe

Start steps on disk so a start that crashed Max is noticed; safe mode, a report in the Listener (and so in MaxPkg's log); `gcprobe.run()` names the object that breaks Python's collector.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `python/mytool/startguard.py`

```python
"""Remember how far the tool's start got, so a start that took 3ds Max down is noticed the next time.

Users whose Max crashes at start can usually send only MaxPkg's log, which mirrors the MAXScript Listener. The guard
writes the current start step to logs/start-<host>.json before every step, and "ready" once the window works. When the
next start finds a step that never finished, Max died during it: that start runs in safe mode (optional native extras
off, see qt_compat.SAFE) and prints the step and the end of the crash log to the Listener, where MaxPkg's log shows it.

A crash whose faulthandler dump says "Garbage-collecting" died inside Python's garbage collector (3ds Max 2024,
PySide2 5.15.1 on Python 3.10): the next starts also hold the collector while the tool runs (controller.hold_gc).
Safe mode and the collector hold stay on for this tool version; a new version tries the normal start again.
"""

import io
import json
import os
import time

DONE = ("ready", "failed", "stopped")  # A start that got here did not take Max down.
SESSION_MARK = "=== session start ==="  # Written by logs.enable_crash_log at every start.
GC_MARK = "Garbage-collecting"  # faulthandler's frame line when Max died inside a garbage collection.


class StartGuard(object):
    def __init__(self, folder, host, version):
        name = "{}-{}".format("{}", host) if host else "{}"
        self.path = os.path.join(folder, "logs", name.format("start") + ".json")
        self.crash_path = os.path.join(folder, "logs", name.format("crash") + ".log")
        self.probe_path = os.path.join(folder, "logs", name.format("gc-probe") + ".txt")  # gcprobe.run()
        self.version = version
        self.previous = self._read()
        step = self.previous.get("step")
        self.crashed_at = step if step and step not in DONE else None
        kept = self.previous.get("version") == version  # Modes stay for the version they were found with.
        self.crash_tail = self._crash_tail() if self.crashed_at else ""
        self.gc_crash = GC_MARK in self.crash_tail
        self.gc_hold = self.gc_crash or bool(self.previous.get("gc_hold") and kept)
        self.safe = bool(self.crashed_at) or bool(self.previous.get("safe") and kept)
        self.details = {}  # Facts about this start (versions, OpenGL, ...) kept in the file for the next report.

    def _read(self):
        try:
            with io.open(self.path, encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _crash_tail(self, lines=30):
        """What faulthandler wrote for the session that died: the text after the last session mark."""
        try:
            with io.open(self.crash_path, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            return ""
        last = text.rsplit(SESSION_MARK, 1)[-1].strip()
        return "\n".join(last.splitlines()[-lines:])

    def note(self, key, value):
        """Keep a fact about this start; it is written with the next step."""
        self.details[key] = value

    def step(self, name):
        """Record that the start is now at `name` (written before the step runs). Never raises."""
        data = {"version": self.version, "step": name, "safe": self.safe, "gc_hold": self.gc_hold,
                "time": time.strftime("%Y-%m-%d %H:%M:%S"), "details": self.details}
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            temporary = self.path + ".tmp"
            with io.open(temporary, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(data))
            os.replace(temporary, self.path)
        except OSError:
            pass

    def report(self, tool_name="The tool"):
        """Lines for the Listener (and so MaxPkg's log) about a start that took Max down; empty when none did."""
        if not self.crashed_at:
            return ""
        prefix = tool_name + ": "
        lines = [prefix + "the last start in this 3ds Max ended unexpectedly at step '{}' (version {}{}). This start "
                 "is in safe mode{}.".format(self.crashed_at, self.previous.get("version", "?"),
                                             ", inside Python's garbage collector" if self.gc_crash else "",
                                             " with the garbage collector held" if self.gc_hold else ""),
                 prefix + "please send this text to the developer."]
        details = self.previous.get("details") or {}
        if details:
            lines.append(prefix + "that start: " + "; ".join("{}={}".format(k, details[k]) for k in sorted(details)))
        try:
            with io.open(self.probe_path, encoding="utf-8", errors="replace") as handle:
                probe = handle.read().split("\x00", 1)[0].strip()
        except OSError:
            probe = ""
        if probe:
            lines.append(prefix + "garbage collector probe: " + probe)
        if self.crash_tail:
            lines.append(prefix + "crash log of that start:")
            lines.extend("  " + line for line in self.crash_tail.splitlines())
        return "\n".join(lines)
```

## `python/mytool/gcprobe.py`

```python
"""Find the object that breaks Python's garbage collector inside 3ds Max (Max 2024 reports, 2026-10-27).

Users' Max 2024 died in "Garbage-collecting" right after MyTool built its window; the same Python 3.10 + PySide2
5.15.1 outside Max did not. To learn which object it is, run this from the MAXScript Listener while MyTool is open:

    python.execute "from mytool import gcprobe; gcprobe.run()"

It walks every object the collector tracks and follows its references, as a collection does, and before each object
writes where it is into logs/gc-probe-<host>.txt through a memory-mapped file: if 3ds Max dies there, the file still
names the object's type. The next MyTool start prints the file in the Listener (and MaxPkg's log). Without a
crash the file says that no object broke it, and a real collection follows.
"""

import gc
import io
import mmap
import os
import sys
import time

SIZE = 4096


def _session():
    return getattr(sys.modules.get("_mytool_session"), "owner", None)


def _path():
    owner = _session()
    guard = getattr
    if guard is not None:
        return guard.probe_path
    from . import settings
    return os.path.join(settings.user_data_dir(), "logs", "gc-probe.txt")


def _name(kind):
    return "{}.{}".format(getattr(kind, "__module__", "?"), getattr(kind, "__qualname__", "?"))


def run(collect=True):
    """Visit every tracked object (and the ones it refers to). Returns the text it wrote."""
    path = _path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "wb") as handle:
        handle.write(b"\x00" * SIZE)
    owner = _session()
    guard = getattr
    if guard is not None:
        guard.step("gc-probe")  # A crash here is reported by the next start with the crash log and this file.
    with io.open(path, "r+b") as handle:
        view = mmap.mmap(handle.fileno(), SIZE)

        def mark(text):  # NUL-terminated; the reader stops there.
            data = text.encode("utf-8", "replace")[:SIZE - 1] + b"\x00"
            view[:len(data)] = data

        try:
            gc.unfreeze()  # Objects frozen when MyTool closed (controller._hold_gc) are looked at too.
            objects = gc.get_objects()
            total = len(objects)
            started = time.time()
            for index, obj in enumerate(objects):
                kind = type(obj)
                mark("broke at object {} of {}: {} (MyTool {})".format(index, total, _name(kind), _version()))
                for referent in gc.get_referents(obj):
                    if gc.is_tracked(referent):  # Reads the referent's collector header, as a collection does.
                        type(referent)
            del objects
            if collect:
                mark("all {} objects visited; broke in a real collection".format(total))
                found = gc.collect()
            else:
                found = 0
            text = "no object broke the collector: {} objects in {:.1f} s, {} collected ({})".format(
                total, time.time() - started, found, time.strftime("%Y-%m-%d %H:%M:%S"))
            mark(text)
            view.flush()
        finally:
            view.close()
    if guard is not None:
        guard.step("ready")
    print("MyTool gc probe: " + text)  # The Listener.
    return text


def _version():
    from . import __version__
    return __version__
```
