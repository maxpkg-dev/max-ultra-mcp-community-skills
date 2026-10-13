# Official MaxPkg MZP delivery

## Scope and authority

Creating a 3ds Max script/tool with this skill normally ends with a locally built installable MZP plus its source project. Make packaging part of the plan from the start. A request limited to a narrow edit, audit, explanation or review does not trigger a packaging migration or unrelated rebuild; honor explicit source-only or other narrower user instructions. Updating this instruction-only community skill still produces its custom-skill ZIP, not an MZP.

The user-defined creation default supplies authority for in-scope project preparation and a local build; do not ask again merely because packaging is the next stage. Reuse saved consent/preferences. Read project/Git state and preserve local work. Do not require a remote push as a prerequisite for an authorized local build. Ask only for genuinely missing required facts or additional consequential scope, such as replacing a conflicting authoring file, choosing an unknown license, or testing an install in a user's working profile. Local build authority does not authorize marketplace upload, publication, Git push, or destructive cleanup of user data.

Use the Max Ultra MaxPkg Packaging skill when available for its current implementation guidance and helper. This standalone skill also describes the workflow below so it is usable without that installed skill. Broader preflight checklists do not require repeating permissions already supplied by the user's creation request or session. Do not manufacture backup, license or test evidence. Standard package deployment is required here; a separate custom installer, daemon or service is not.

## Refresh official sources

At the start of packaging, resolve current HEAD of the [official MaxPkg development repository](https://github.com/maxpkg-dev/max-dev-tool) to one immutable commit. Fetch and read that revision's `README.md`, `code-rules.md`, `maxpkg-adaptation-prompt.md`, and `maxpkg-api.md` completely. Obtain `maxpkg-packager.ms`, `_install.ms`, and `_uninstall.ms` from the same revision. If the packaging skill is available, its `get-maxpkg-upstream.ps1 -Prompt Adaptation` helper performs this pinned fetch; otherwise use the official GitHub API/raw files or a read-only checkout with the same consistency checks. Marketplace onboarding is a separate requested scope and is not implied by this default.

Record the upstream SHA and hashes of downloaded tooling. Use current API documentation and live schema, not a memorized INI format or this reference as a frozen specification. If retrieval fails, report the official-tooling blocker, preserve source work, and leave preparation notes/static inventory; do not fabricate authoring files or claim the project is fully build-ready without them. Clean up only the exact verified temporary fetch directory after copying/inspection; preserve user sources.

This reference was checked on 2026-10-13 against [commit 1281d283b30d885382c12804ca12da3f092d888b](https://github.com/maxpkg-dev/max-dev-tool/tree/1281d283b30d885382c12804ca12da3f092d888b). Recheck live sources on use. Upstream treats standard hooks as optional in general; this skill's delivery contract retains **both** original hooks for a complete standard authoring project.

## Prepare the authoring project

```text
tool-project/
  StartMyTool.ms           # normal runtime entry; starts Python
  python/                 # bootstrap and complete tool package
  assets/                 # required themes, icons and other resources
  licenses/               # applicable shipped asset/dependency licenses
  docs/                   # source documentation; ship runtime help if needed
  tests/                  # source-only fixtures
  maxpkg-packager.ms       # original official tooling
  _install.ms             # original standard hook
  _uninstall.ms           # original standard hook
  maxpkg-packager.ini      # actual project configuration
  maxpkg-changelog.ini     # current version's factual changelog
  maxpkg-icon.svg          # square authorized project icon
  dist/                   # real packager output, separate from sources
```

Keep the three official `.ms` files and their headers/implementation intact. Review different existing same-named files before replacement; do not overwrite local adaptations silently. Generated `mzp.run`/manifests are build output, not substitutes for these authoring files. Use focused custom `.ms` install/uninstall hooks only for necessary project-owned work not performed by MaxPkg, such as lifecycle cleanup. Configure them through the dedicated fields; do not also add them to the ordinary file list. Never chain an old complete installer or duplicate extraction, generated macros, icon deployment or notification. Preserve old source files on disk while excluding obsolete installation launchers from the package.

Configure from actual evidence: project identity, developer, confirmed license, square SVG icon, output path, entry, version/channel/date/minimum Max and changelog. Preserve an existing package GUID; generate one only for a genuinely new package. Do not borrow a GUID, license, developer or supported version from an example. Treat GUID and developer-machine paths as private build identity, not public marketplace prose. Ask one grouped question for missing required identity/legal facts while completing independent work.

Select `StartMyTool.ms` (or the project's actual `.ms` launcher) as entry after adding it to the file list. Explicitly choose `compileEntry=false` for this skill's default visible `.ms` launcher; upstream may default to compilation. Compile only if the user requests it and the resulting `.mse` path behavior is verified. Do not substitute direct `.py` entry just because the packager supports it.

Use a reviewed runtime allowlist: launcher, bootstrap, every imported Python module, selected editable theme JSON files, original Lucide SVG icons, necessary icon/asset licenses, templates/presets, and runtime help. Verify dynamic/lazy imports and resources, not only top-level imports. Exclude tests, test data, `.git`, environments, caches/bytecode, logs, credentials, private paths, development notes, old installers, backups, source archives and previous build output. Packager automatic exclusions are a starting filter, not proof that this tool's list is complete or private-data-free. Standard hooks/icon/custom hook files have dedicated handling; avoid duplicate inclusion.

Derive installed paths from the executing `.ms` file and Python `__file__`, preserving their relative layout. Do not hard-code the extracted GUID/temp folder or author checkout. Use Build Path Remap only when necessary and verify imports, entry/macro targets and assets after remapping. A source launch working does not prove the installed layout works.

Classify settings intentionally: disposable package-owned settings may be initialized lazily beneath the installed runtime root; durable user preferences (including a theme choice intended to survive removal), shared data and user-authored content belong in an appropriate writable user-data directory. This follows the official ownership distinction while preserving the tool's intended retention policy. Updates must preserve existing values; uninstall must not search broadly for data to delete. Runtime shutdown still stops only owned resources, never 3ds Max or unrelated processes.

## Build with the original API

Use Max Ultra MCP's available tools, inspecting schemas rather than assuming tool arguments. List instances first and explicitly select the intended instance; resolve ambiguity before executing code. Record actual Max/Python/Qt versions. Use a suitable isolated fixture for runtime tests; do not reset or touch a working scene to build a package.

1. Run the target project's original `maxpkg-packager.ms` through the selected Max instance (`max_run_script_file` where available).
2. Call `MaxPkgPackerApi.ping()` through MaxScript execution. Parse the outer MCP response and then the inner JSON string. Require `ok == true`; verify `data.projectRoot` equals the intended resolved project and record API/packager versions before mutations.
3. Inspect `getSchema()` and `getState()` for the current revision. Configure through supported methods or the verified project-local format. Prefer `setOptions` for related options; add runtime files before selecting entry, set version before its changelog, and relist 1-based collections after mutations. Do not clear dependent references with `force` unless that change is intentional.
4. Preserve any important unsaved packager state before `reload()`, which discards it. After saving/configuring, call `reload()` and inspect the returned persisted state. The official API's mutations save synchronously in the inspected revision.
5. Call `validate()` and parse its inner result. Resolve errors from evidence; stop dependent steps when `ok` is false. Read warnings/logs rather than clearing them to manufacture success.
6. Call the original `MaxPkgPackerApi.build()` serially. Require inner `ok == true`, `data.exists == true`, and `data.outputFile`. Verify that path belongs to the expected output directory and is the output of this build; a stale file's existence or successful outer execution is insufficient.
7. Call `getState()` after the build, record final version/configuration, then inspect the returned archive. Keep the packager's output filename, currently `<slug>@<major.minor.patch>@<guid>.mzp`, with channel stored separately. Do not rename the archive or generate a replacement ZIP/MZP yourself.

Read each response before the next dependent call; do not paste a batch that ignores failed results. If no suitable Max connection, original tooling or usable public API is available, report that exact blocker. Leave the verified configured source project and remaining build action; never call it a built MZP. For an older API-less packager, prefer refreshing the official tooling after reviewing local conflicts; do not bypass this default API workflow with a homemade archive. Once prerequisites become available, resume the real build instead of assigning routine execution to the user.

## Archive verification and acceptance

Inspect the output as an archive without executing its installation scripts. Verify filename, version, identity and entry consistency across final `manifest.ini`, `manifest.json`, `maxpkg-changelog.ini`, `mzp.run` and `mzp.run.ms`; check both original hooks, selected custom hook declarations, generated macro targets and `icons/icon.svg`. Compare the actual file inventory against the reviewed allowlist and remapped layout, including Python modules, theme files, icons and licenses. Reject unexpected/private/dev files and unsafe or case-conflicting paths. Record the output size and checksum and confirm no unintended source changes. Do not patch the output archive to fix a bad build; fix configuration/source and rebuild through the original packager.

Report evidence separately:

| Claim | Required evidence |
| --- | --- |
| Package-ready | Official authoring files, valid known configuration, allowlist and unresolved requirements stated |
| Built | Successful parsed API build result and verified returned artifact |
| Archive-verified | Inspected final inventory/manifests, identity/version/paths, checksum and no excluded data |
| Install/launch-tested | Authorized isolated installation, generated button launching the installed `.ms`, correct Python/resources/UI and relaunch cleanup |
| Update-tested | Controlled prior-version update with settings/data preserved and old lifecycle stopped |
| Uninstall/reinstall-tested | Owned integrations/resources cleaned without deleting durable user data or stopping Max; successful reinstall |

Perform install/update/uninstall tests only within an authorized isolated profile/fixture. Creating a local MZP does not grant permission to replace a user's installed tool. Mark unavailable tests as not run; archive validity does not prove install behavior. Deliver source project, exact local artifact path when built, upstream revision, checks and remaining limitations. External release/upload/push remains a separate user-authorized action.
