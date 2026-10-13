# Launcher, ownership, and restart

## Thin MaxScript entry

New example for `StartMyTool.ms`, paired with the layout in [architecture](architecture.md):

```maxscript
(
    local entryPath = getThisScriptFileName()
    local bootstrapPath = (getFilenamePath entryPath) + @"python\bootstrap.py"
    if not doesFileExist bootstrapPath do
        throw "My Tool bootstrap is missing. Restore the complete tool folder."
    python.ExecuteFile bootstrapPath
)
```

Use a file execution API rather than quoting an arbitrary path inside Python source. A toolbar action may invoke this launcher; it should not implement a second lifecycle.

## Restart state machine

`idle/running -> stopping -> stopped -> loading -> running`, with a retained `failed` owner when cleanup cannot be confirmed. Keep a process-local anchor such as `_studio_my_tool_session` outside `studio_my_tool.*`. Repeated launches during a transition coalesce; they must not each schedule another replacement.

1. Set a restart guard before imports or asynchronous callbacks can reenter.
2. Tell the old controller to stop accepting work and invalidate its generation token. Do not clear the anchor yet.
3. Request cleanup. Poll quiescence on an owned Qt timer in the main thread; never sleep, run nested `processEvents`, or join a running worker indefinitely in a UI callback.
4. Only when stopped, remove this tool's exact package namespace and submodules if fresh code loading is required. Do not evict PySide, pymxs, unrelated packages, or the anchor.
5. Import from the launcher's own package directory using an explicit package spec (or another deterministic import strategy), create a passive controller, assign it to the anchor, then call `start()`.
6. On any failure, stop the candidate, retain its cleanup handle if necessary, clear the transition guard in `finally`, and report the failure. No replacement may run beside a failed or still-stopping owner.

Module eviction is optional for production restarts; restart of the instance is mandatory. Development reload must wait until old callbacks and workers cannot import or call replaced modules. Do not globally change bytecode settings, interpreter paths, or environment variables merely for convenience.

## Concrete synchronous bootstrap

This example assumes a controller with **no asynchronous workers**, a passive constructor, and `stop()` that either fully unregisters active resources or raises. Deferred Qt deletion is allowed after widgets are hidden, disconnected, and inactive. Adapt the asynchronous contract below before adding workers. The Qt design system lives in the controller/UI layer, not this bootstrap.

```python
# python/bootstrap.py -- executed by the .ms launcher
def launch(root):
    import importlib
    import importlib.util
    import sys
    import types

    package_name = "studio_my_tool"
    state = sys.modules.setdefault(
        "_studio_my_tool_session", types.ModuleType("_studio_my_tool_session")
    )
    if getattr(state, "transitioning", False):
        return
    state.transitioning = True
    candidate = None
    try:
        previous = getattr(state, "owner", None)
        if previous is not None:
            previous.stop()  # raises if cleanup is incomplete; retains owner
            state.owner = None
        for name in list(sys.modules):
            if name == package_name or name.startswith(package_name + "."):
                del sys.modules[name]
        importlib.invalidate_caches()
        folder = root / "python" / package_name
        spec = importlib.util.spec_from_file_location(
            package_name, str(folder / "__init__.py"),
            submodule_search_locations=[str(folder)]
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Cannot load My Tool package")
        package = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = package
        spec.loader.exec_module(package)  # __init__.py has no side effects
        controller = importlib.import_module(package_name + ".controller")
        candidate = controller.Controller(root)  # constructor is passive
        state.owner = candidate
        candidate.start()
    except Exception:
        if candidate is not None:
            candidate.stop()  # retained in state if this fails; do not hide error
            state.owner = None
        raise
    finally:
        state.transitioning = False


from pathlib import Path
launch(Path(__file__).resolve().parent.parent)
```

`Controller.start()` must record cleanup immediately after each acquisition, before the next step can fail. A newly written ledger pattern for synchronous resources:

```python
class Cleanup:
    def __init__(self):
        self.entries = []

    def own(self, label, release):
        self.entries.append((label, release))

    def release_all(self):
        failed = []
        errors = []
        for label, release in reversed(self.entries):
            try:
                release()
            except Exception as error:
                failed.append((label, release))
                errors.append("{}: {}".format(label, error))
        self.entries = list(reversed(failed))  # keep failed handles for retry
        if errors:
            raise RuntimeError("Cleanup incomplete: " + "; ".join(errors))
```

Register idempotent release functions (not arbitrary `disconnect()` calls that fail on retry). A controller marks itself stopping before invoking them and returns early only after successful full cleanup, not just because stopping was requested. In a real tool, make acquisition exception-safe too: if registering an acquired object in the owner fails, release that object immediately. Route window close through the same controller shutdown; a hide action deliberately keeps the owner alive.

## Resource contracts

| Resource | Acquire / record | Release and proof |
| --- | --- | --- |
| Windows/dialogs | Strong controller reference, Max parent, registry of owned windows | Hide and disable actions, remove filters/connections, call `deleteLater()` on main thread; remove registry references when safe |
| Timers, copy feedback, overlays | Parent `QTimer` to owner/widget; record timeout slot | Stop, disconnect owned slot, invalidate callbacks and defer deletion; use owned single-shot timers for cancellable delayed work |
| Max callbacks | Unique tool-specific callback ID; retain callable; `persistent=False` where appropriate | Remove only this ID with `rt.callbacks.removeScripts(id=...)`; clear callable references after removal |
| Qt signals | Record sender, signal and exact connected slot | Disconnect this connection only; application-wide senders outlive windows |
| Event filters/accelerators | Record installed filter and prior host state | Remove filter and restore state if still owned; do not overwrite another tool's later change |
| Threads/futures | Stop event, bounded I/O, task registry and generation | Signal cancellation, poll completion; `future.cancel()` and `shutdown(wait=False)` do not stop running work |
| QThread workers | Owned thread and worker, queued plain-data results | Cooperative stop, quit event loop when appropriate, await `finished` without blocking UI; never destroy a running QThread |
| Sockets/files/logging | Exact owned handles and handlers | Unblock reads via owned connection shutdown, finish work, close handles/remove only own handlers |
| Child processes | Retained process handle and verified identity/ownership | Graceful stop and bounded wait; fallback only for provably owned private helper; never kill by broad name, port, or guessed PID |

A queued result must check `owner.running` and its captured generation before touching UI. If scene identity matters, include a scene revision and revalidate it on the main thread. Guard active ticks so a restart requested from inside a callback waits until that callback returns. Do not replay pending actions into the new lifecycle.

## Extending to asynchronous shutdown

Split `stop()` into `request_stop()` (idempotent initiation), `poll_stop()` (incremental cleanup), and `is_stopped()` (all workers exited, resources inactive, no failed cleanup). The stable bootstrap owns a polling timer, restart generation, deadline from `time.monotonic()`, and candidate reference:

```text
launch:
  if transition active: return
  mark transition active; retain old owner
  request_stop(old); start owned main-thread poll timer
poll:
  poll_stop(old)
  if stopped: stop/delete poll timer; import/create/start replacement
  elif deadline expired: stop/delete poll timer; keep old owner; report failure
  else: return to Qt event loop
all error exits:
  retain cleanup handle; stop/delete poll timer; release transition guard
```

Stop-request exceptions follow the same retained-owner failure path. A timeout aborts replacement, not Max. The next explicit launcher run may resume cleanup and retry; do not auto-retry forever. A partial replacement start also needs this asynchronous cleanup path. If an owned background task cannot cooperate, report that restart is blocked and retain its state instead of pretending it stopped.
