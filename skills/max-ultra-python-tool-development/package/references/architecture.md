# Architecture and bundled-runtime compatibility

## Scale the layout to the tool

An illustrative output project (these are files to create for the requested tool, not executable files bundled in this skill):

```text
my_tool/
  StartMyTool.ms
  maxpkg-packager.ms          # original official authoring tool
  _install.ms                # original standard hook
  _uninstall.ms              # original standard hook
  maxpkg-packager.ini         # project-local reviewed build configuration
  maxpkg-changelog.ini
  maxpkg-icon.svg
  python/
    bootstrap.py              # stable-session coordination, controlled imports
    studio_my_tool/
      __init__.py             # passive package marker
      controller.py           # lifecycle owner and orchestration
      qt_compat.py            # one binding choice, host parenting, API differences
      ui/                     # windows and reusable controls
      domain/                 # plain-data computation and validation
      max_api.py              # main-thread pymxs boundary
      workers.py              # optional bounded I/O/CPU jobs
      resources.py            # package-relative asset resolution
      settings.py             # optional writable user preferences
  assets/                     # icons, themes, templates actually required
  docs/                       # launch, supported versions, behavior and limitations
  tests/                      # pure logic and separate disposable host fixtures
  licenses/                   # shipped asset/dependency license texts
  dist/                       # official MaxPkg MZP output, excluded from runtime inputs
```

Use a unique package namespace. Merge tiny modules when separation would add no value; do not create empty folders, a framework, or a transport layer for a small utility. Let widgets call controller actions, and keep scene mutation out of paint events and worker completion threads. Pass data into domain code rather than importing `pymxs` there. Use direct supported `pymxs` APIs rather than constructing executable MaxScript strings from user input.

For this layout, `resources.py` can derive the root with `Path(__file__).resolve().parents[2]` and use `root / "assets" / "icons"`. That parent count belongs to this layout; update it when moving modules, or inject the bootstrap root. Validate required files and report a useful path when missing. Keep durable preferences outside a potentially read-only installation directory; deliberately disposable package-owned settings may use the installed runtime root with a documented retention policy. Include required assets and licenses in the official MZP allowlist. See [MaxPkg delivery](maxpkg-delivery.md) for the required creation-stage build and scoped-edit exception.

## Runtime targets

Autodesk's [Python release history](https://help.autodesk.com/cloudhelp/2026/ENU/MAXDEV-Python/files/MAXDEV_Python_what_s_new_in_3ds_max_python_api_html.html) records these baselines (checked 2026-10-13):

| Max release | Recorded Python version | Qt binding target |
| --- | --- | --- |
| 2022 | 3.7.9; 2022.3 updates to 3.7.12 | PySide2 (5.15.1 at 2022 baseline) |
| 2023 | 3.9.7 | PySide2 per reference implementation |
| 2024 | 3.10.8 | PySide2 per reference implementation |
| 2025 | 3.11.4; 2025.1 updates to 3.11.8 | PySide6 (6.5.3 at 2025 baseline) |
| 2026 | 3.11.9 | PySide6 per reference implementation |
| 2027 | Not independently established here | PySide6 is the reference's declared target; verify in host |

This is a targeting aid, not a tested support matrix. Record `sys.version`, `QtCore.qVersion()`, binding version, and Max build from the actual supported installations. Check update-specific Autodesk documentation; do not extrapolate exact patch versions. If 2022 is required, keep Python syntax and standard-library calls compatible with 3.7 (for example, avoid evaluated `list[str]` annotations and newer-only executor shutdown arguments). Compile against the oldest target interpreter as well as newer targets when available. Compiling with a newer system Python proves neither older syntax compatibility nor Max API behavior.

Centralize binding selection. The reference tries PySide6 then PySide2. For a new tool, catch only absence of the requested binding when falling back; a broken installed binding or missing dependency should produce a diagnostic instead of silently mixing families. Keep Qt enums, event-position APIs, `exec`/`exec_`, and any Shiboken wrapper differences inside a narrow compatibility layer as needed. Use shiboken6 with PySide6 and shiboken2 with PySide2, never cross-wrap objects. Prefer `qtmax.GetQMaxMainWindow()` where available. Feature-detect optional `qtmax` helpers such as accelerator handling.

Use `QApplication.instance()`; do not create or execute a second application event loop. Keep strong Python ownership of tool windows and respect Qt's parent ownership and deferred deletion. A surviving Python wrapper can refer to a deleted C++ object; do not treat a non-null wrapper as proof of validity.

## UI patterns worth retaining

Use layouts, minimum sizes, scrolling where needed, logical-pixel sizing, and point-sized fonts. Ask about breakpoint-driven adaptation as required by SKILL.md before enabling it. Preserve accessible names/tooltips when the approved compact mode collapses labels to icons. Make busy operations cancellable when feasible and restore controls on success, failure, and cancellation. Stop animation timers when hidden. The shared theme and control requirements live in [Qt design system](qt-design-system.md); they apply to generated tools independently of the optional breakpoint choice.

The reference's custom frameless chrome, Windows DWM shadow code, promotion rows, journal pagination and exact dimensions are product choices. Do not copy them as requirements. This skill does require editable themes and a Warm Graphite starting default by user instruction. `docs/UI_DESIGN.md` even contains a later breakpoint note differing from its table; check implementation and actual resize behavior before inheriting exact values.
