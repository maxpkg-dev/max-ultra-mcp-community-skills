# Template: Session controller and background jobs

The session owner (start / request_stop / poll_stop / is_stopped), the cleanup ledger, the main-thread poster, the GIL pump that lets worker threads run inside Max, the garbage-collector hold for Max 2024, and the thread pool runner.

Copy into the tool's project at the shown path and rename as described in [starter templates](../starter-templates.md). Verified as one project outside 3ds Max with Max 2022's Python 3.7.9 / PySide2 5.15.1 and Max 2027's Python 3.13.9 / PySide6 6.8.3.

## `python/mytool/controller.py`

```python
"""Session owner. Owns every window, worker, timer and handler of one tool lifecycle.

Contract used by bootstrap.py: Controller(root) is passive; start() acquires resources; request_stop() begins shutdown;
poll_stop() advances it; is_stopped() is True when nothing is left.
"""

import gc
import os
import platform
import sys
import time

from . import TOOL_NAME, __version__, logs, qt_compat, settings, startguard
from .qt_compat import QtCore, QtWidgets, Signal, is_valid, max_main_window
from .workers import JobRunner

_log = logs.get("controller")

# 3ds Max 2024 (PySide2 5.15.1 on Python 3.10) died inside Python's garbage collector as soon as one ran after the
# tool's window was built; the same Python and PySide2 outside Max did not (TerraScoop users' logs, 2026-10-27).
GC_HOLD = qt_compat.BINDING == "PySide2" and sys.version_info >= (3, 10)


def hold_gc():
    """Turn Python's automatic garbage collection off while the tool runs; None when it was off already.

    Returns the release for Cleanup: everything alive then is frozen first (gc.freeze, permanent), so no later
    collection walks over the broken object, and then collection runs again for whatever is made after that.
    """
    if not gc.isenabled():
        return None
    gc.disable()

    def release():
        gc.freeze()
        gc.enable()
    return release


def _in_max():
    try:
        import pymxs  # noqa: F401
    except ImportError:
        return False
    return True


class _Poster(QtCore.QObject):
    """Moves callables from worker threads to the main thread through a queued signal."""

    posted = Signal(object)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.posted.connect(self._run)

    def _run(self, function):
        try:
            function()
        except Exception:
            _log.exception("Main-thread callback failed")


class _GilPump(object):
    """Lets worker threads run inside 3ds Max.

    Max keeps Python's GIL on its main thread while idle, so background threads only advance while main-thread Python
    runs. While jobs are active this timer briefly releases the GIL with a short sleep; the Qt event loop still runs
    between ticks, so the UI stays responsive. It stops as soon as no job is running.
    """

    INTERVAL_MS = 16
    YIELD_S = 0.010

    def __init__(self, runner):
        self.runner = runner
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.INTERVAL_MS)
        self.timer.timeout.connect(self._tick)

    def kick(self):
        if not self.timer.isActive():
            self.timer.start()

    def _tick(self):
        if self.runner.active_count() == 0:
            self.timer.stop()
            return
        time.sleep(self.YIELD_S)

    def dispose(self):
        self.timer.stop()


class Cleanup(object):
    """Reverse-order release ledger; failed releases are kept for a retry."""

    def __init__(self):
        self.entries = []

    def own(self, label, release):
        self.entries.append((label, release))

    def release_all(self):
        failed, errors = [], []
        for label, release in reversed(self.entries):
            try:
                release()
            except Exception as error:
                failed.append((label, release))
                errors.append("{}: {}".format(label, error))
        self.entries = list(reversed(failed))
        if errors:
            raise RuntimeError("Cleanup incomplete: " + "; ".join(errors))


class Controller(object):
    def __init__(self, root):
        self.root = root
        self.state = "idle"
        self.cleanup = Cleanup()
        self.prefs = None
        self.theme = None
        self.runner = None
        self.window = None
        self.dialogs = {}
        self.guard = None
        self._job = None
        self._finalize_timer = None

    # Lifecycle ----------------------------------------------------------------------------------
    def start(self):
        from .ui.theme_manager import ThemeManager
        from .ui.main_window import MainWindow

        self.state = "starting"
        held = hold_gc() if GC_HOLD else None  # Before anything of ours exists.
        host, max_version = "", None
        try:
            from pymxs import runtime as rt
            version = rt.maxVersion()
            host, max_version = "max{}".format(int(version[7])), str(version)
        except Exception:
            pass  # Outside Max (standalone harness).
        logs.set_host(host)  # One log per Max version: two Max versions never share a file.
        # Read what the last start left behind before the crash log opens a new session (startguard).
        self.guard = startguard.StartGuard(settings.user_data_dir(), host, __version__)
        if held is None and self.guard.gc_hold:
            held = hold_gc()
        if held is not None:
            self.cleanup.own("garbage collector", held)  # Registered first, so released last.
        self.guard.note("max", max_version)
        self.guard.note("qt", "{}, Qt {}, Python {}".format(qt_compat.BINDING, qt_compat.qt_version(),
                                                            platform.python_version()))
        qt_compat.SAFE["on"] = self.guard.safe
        handler = logs.attach(settings.user_data_dir())
        self.cleanup.own("log handler", lambda: logs.detach(handler))
        release_crash_log = logs.enable_crash_log(settings.user_data_dir())
        self.cleanup.own("crash log", release_crash_log)
        _log.info("Starting %s %s from %s (%s, Qt %s)%s", TOOL_NAME, __version__, self.root, qt_compat.BINDING,
                  qt_compat.qt_version(), " in safe mode" if self.guard.safe else "")
        if self.guard.crashed_at:
            report = self.guard.report(TOOL_NAME)
            print(report)  # The MAXScript Listener: MaxPkg's log shows it to users who cannot find our files.
            _log.warning("%s", report)
        try:
            self._start_steps(ThemeManager, MainWindow)
        except Exception:
            self.guard.step("failed")  # A Python error, not a crash: the next start is a normal one.
            raise

    def _start_steps(self, ThemeManager, MainWindow):
        guard = self.guard
        guard.step("settings")
        self.prefs = settings.Settings().load()
        if self.prefs.load_error:
            _log.warning("Settings unreadable, defaults used: %s", self.prefs.load_error)
        guard.step("scale")  # Interface size before any window exists: every size is multiplied by it.
        factors = qt_compat.measure_scale(max_main_window(), self.prefs.get("ui_scale") or "auto")
        _log.info("Interface size %d %% (auto %d %%)", factors["target"] * 100, factors["auto"] * 100)
        guard.step("theme")
        poster = _Poster()
        self.cleanup.own("poster", poster.deleteLater)
        self.runner = JobRunner(post=poster.posted.emit)
        self.cleanup.own("runner", self.runner.request_stop)
        self.pump = _GilPump(self.runner)
        self.cleanup.own("gil pump", self.pump.dispose)
        self.runner.on_submit = self.pump.kick
        self.theme = ThemeManager(self.root, self.prefs)
        self.theme.load_initial()
        self.cleanup.own("theme", self.theme.dispose)
        guard.step("window")
        self.window = MainWindow(self, max_main_window())
        guard.step("geometry")
        self.window.restore_geometry_state(None if guard.safe else self.prefs.get("window_geometry"))
        self.cleanup.own("main window", self._dispose_window)
        self.theme.register(self.window)
        guard.step("show")
        self.window.show()
        self.state = "running"
        QtCore.QTimer.singleShot(0, self._ready)  # After Qt has shown the window: the start worked.
        if guard.crashed_at:
            self.window.set_status("Safe start: the last start of {} crashed 3ds Max. Please send the logs (Logs "
                                   "button) to the developer.".format(TOOL_NAME))
        _log.info("Started")

    def _ready(self):
        if self.state == "running":
            self.guard.step("ready")

    def _dispose_window(self):
        for dialog in list(self.dialogs.values()):
            if is_valid(dialog):
                dialog.dispose()
        self.dialogs = {}
        window, self.window = self.window, None
        if window is not None and is_valid(window):
            # Position and size come back on the next launch (also after a relaunch or Max restart).
            self.prefs.set("window_geometry", window.geometry_state())
            self._save_prefs()
            self.theme.unregister(window)
            window.dispose()
            window.hide()
            window.deleteLater()

    running = property(lambda self: self.state == "running")

    def request_stop(self):
        """Idempotent. Stops accepting work, cancels jobs and closes windows."""
        if self.state in ("stopping", "stopped"):
            return
        _log.info("Stopping %s", TOOL_NAME)
        if self.guard is not None and self.state == "running":
            self.guard.step("stopped")  # Closed before it was ready: not a crash.
        self.state = "stopping"
        if self.runner is not None:
            self.runner.request_stop()
        self._dispose_window()  # Windows go now; the log handler and poster stay until workers are idle.
        if self._finalize_timer is None:
            self._finalize_timer = QtCore.QTimer()  # Finishes cleanup after a user close even when no relaunch polls.
            self._finalize_timer.setInterval(100)
            self._finalize_timer.timeout.connect(self.poll_stop)
            self._finalize_timer.start()

    def poll_stop(self):
        if self.state != "stopping":
            return
        if self.runner is not None and not self.runner.is_idle():
            return
        try:
            self.cleanup.release_all()
        except RuntimeError:
            _log.exception("Cleanup failed; it will be retried on the next launch")
            return
        if self._finalize_timer is not None:
            self._finalize_timer.stop()
            self._finalize_timer = None
        self.state = "stopped"

    def is_stopped(self):
        return self.state in ("stopped", "idle")

    # Preferences --------------------------------------------------------------------------------
    def _save_prefs(self):
        try:
            self.prefs.save()
        except OSError as error:
            _log.warning("Settings not saved: %s", error)
            if self.window is not None:
                self.window.set_status("Settings could not be saved: {}".format(error))

    def set_preference(self, key, value):
        if key in self.prefs.overrides:
            self.prefs.override(key, value)  # Session-only value (tests, fixtures): never reaches the file.
        else:
            self.prefs.set(key, value)
            self._save_prefs()

    def reopen(self):
        """Close the tool and open it again through its launcher (inside Max), e.g. for a new interface size, which
        applies while windows are built. False outside Max."""
        try:
            from pymxs import runtime as rt
        except ImportError:
            return False
        script = os.path.join(self.root, "Start{}.ms".format(TOOL_NAME))
        QtCore.QTimer.singleShot(0, lambda: rt.fileIn(script))  # After the click that asked for it returns.
        return True

    def can_reopen(self):
        return _in_max()

    # Dialogs ------------------------------------------------------------------------------------
    def show_settings(self):
        self._show_dialog("settings", lambda d: d.SettingsDialog(self, self.window))

    def show_logs(self):
        self._show_dialog("logs", lambda d: d.LogDialog(self, self.window))

    def show_about(self):
        self._show_dialog("about", lambda d: d.AboutDialog(self, self.window))

    def _show_dialog(self, key, factory):
        from .ui import dialogs
        dialog = self.dialogs.get(key)
        if dialog is None or not is_valid(dialog):
            dialog = factory(dialogs)
            dialog.finished.connect(lambda *_: self._close_dialog(key))
            self.dialogs[key] = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog

    def _close_dialog(self, key):
        dialog = self.dialogs.pop(key, None)
        if dialog is not None and is_valid(dialog):
            dialog.dispose()

    # Work ---------------------------------------------------------------------------------------
    def run_job(self, work, on_progress, on_done):
        """Run work(cancel, report) in a worker; report(label, done, total) and on_done(result or error) arrive on
        the main thread. Workers get plain data and never touch pymxs or Qt widgets."""
        def report(label, done, total):
            self.runner.post(lambda: on_progress(label, done, total))

        def finished(value):
            self._job = None
            on_done(value)

        self._job = self.runner.submit(lambda cancel: work(cancel, report), on_done=finished, on_error=finished,
                                       name="job")
        return self._job

    def confirm_stop(self, reason="close"):
        """Ask before a close or relaunch would cancel running work. True = go ahead."""
        if self._job is None:
            return True
        window = self.window if self.window is not None and is_valid(self.window) else None
        action = "Relaunch" if reason == "relaunch" else "Close"
        box = QtWidgets.QMessageBox(window)
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setWindowTitle(TOOL_NAME)
        box.setText("Work is running.")
        box.setInformativeText("{} {} and cancel it?".format(action, TOOL_NAME))
        stop = box.addButton("Cancel It and {}".format(action), QtWidgets.QMessageBox.DestructiveRole)
        keep = box.addButton("Keep Working", QtWidgets.QMessageBox.RejectRole)
        box.setDefaultButton(keep)
        qt_compat.exec_dialog(box)
        if box.clickedButton() is stop:
            self.runner.cancel(self._job)
            return True
        return False
```

## `python/mytool/workers.py`

```python
"""Background jobs with cooperative cancellation and lifecycle generations.

Pure code. Jobs receive a `threading.Event` that is set when they should stop, and return plain data.
Completion callbacks are handed to `post`, which the controller binds to a Qt queued signal so they run
on the main thread. Results from a stopped runner are dropped.
"""

import concurrent.futures
import itertools
import threading

from . import logs

_log = logs.get("workers")


class JobRunner(object):
    def __init__(self, post, max_workers=4):
        self._post = post
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers,
                                                               thread_name_prefix="mytool")
        self._jobs = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()
        self._stopping = False
        self.on_submit = None  # Main-thread hook, e.g. to start the GIL pump inside 3ds Max.

    def submit(self, work, on_done=None, on_error=None, name="job"):
        """Run work(cancel_event) in a thread; returns a job id usable with cancel()."""
        if self._stopping:
            raise RuntimeError("Runner is stopping; no new work accepted.")
        job_id = next(self._ids)
        cancel = threading.Event()

        def run():
            try:
                result = work(cancel)
            except Exception as error:  # Reported on the main thread, never raised in the worker.
                if not cancel.is_set():
                    _log.exception("Job %s failed", name)
                self._finish(job_id, cancel, on_error, error)
                return
            self._finish(job_id, cancel, on_done, result)

        with self._lock:
            self._jobs[job_id] = (cancel, self._executor.submit(run))
        if self.on_submit is not None:
            self.on_submit()
        return job_id

    def _finish(self, job_id, cancel, callback, value):
        with self._lock:
            self._jobs.pop(job_id, None)
        if callback is None or cancel.is_set() or self._stopping:
            return
        self._post(lambda: None if (cancel.is_set() or self._stopping) else callback(value))

    def post(self, callback):
        """Run callback() on the main thread soon; dropped if the runner is stopping."""
        if not self._stopping:
            self._post(lambda: None if self._stopping else callback())

    def cancel(self, job_id):
        with self._lock:
            entry = self._jobs.get(job_id)
        if entry is not None:
            entry[0].set()

    def request_stop(self):
        self._stopping = True
        with self._lock:
            entries = list(self._jobs.values())
        for cancel, _future in entries:
            cancel.set()
        # Python 3.7 has no cancel_futures; queued jobs see the cancel event and return at once.
        self._executor.shutdown(wait=False)

    def is_idle(self):
        with self._lock:
            return all(future.done() for _cancel, future in self._jobs.values())

    def active_count(self):
        with self._lock:
            return sum(1 for _cancel, future in self._jobs.values() if not future.done())
```
