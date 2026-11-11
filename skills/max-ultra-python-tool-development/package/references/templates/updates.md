# Template: Self-update

The pure update module (`updater.py`: manifest, verified download, staging, syntax check, one-step switch, two kept versions, rollback) and the release script that writes the archive and `update.json` (`tools/release.py`). The launcher's `bootstrap.py` starts the newest copy and rolls back a version that cannot start ([launcher-bootstrap](launcher-bootstrap.md)); `Controller.check_updates`, the Settings group and the status bar pill are in [controller-workers](controller-workers.md), [dialogs](dialogs.md) and [tool-window](tool-window.md). The procedure is in [updates](../updates.md).

Verified as one project inside 3ds Max 2022 (Python 3.7.9 / PySide2 5.15.1) and 3ds Max 2027 (Python 3.13.9 / PySide6 6.8.3) through Max Ultra MCP, with the windows off screen. Downloads were checked from `file:///` folders; no network release was made.

## `python/mytool/updater.py`

```python
"""Self-update that cannot leave the tool half-updated (as MaxPkg Packager does it). Pure code: no Qt, no pymxs.

Layout under the app home (%LOCALAPPDATA%\\MyTool\\app):

    current.json      {"version": "1.0.2", "dir": "v1.0.2", "sha256": "<payload>", "previous": "1.0.1",
                       "previousDir": "v1.0.1"}
    v1.0.1\\ v1.0.2\\  one complete, verified copy of python\\ and assets\\ per version

An update is downloaded, checked against its SHA-256, unpacked into a staging folder, compiled as a syntax check and
only then moved into place with one rename; current.json switches with one atomic replace. The running tool keeps
using its own folder, the new version starts at the next launch (bootstrap.pick_root starts the newest of the copy
next to the launcher and the installed one), and the previous version stays on disk so a failed start rolls back.

The published update.json (tools/release.py writes it):
    {"schema": 1, "version": "1.0.2", "payload": {"url": "https://.../mytool-app-1.0.2.zip", "sha256": "...",
     "size": 123456}, "notes": ["+ Added: ...", "- Fixed: ..."]}
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

PACKAGE = "mytool"
USER_AGENT = "MyTool"
KEEP_VERSIONS = 2  # current + previous


class UpdateError(Exception):
    pass


class UpdateInfo(object):
    def __init__(self, version, url, sha256, notes=None):
        self.version = version
        self.url = url
        self.sha256 = (sha256 or "").lower()
        self.notes = list(notes or [])


def parse_version(text):
    parts = re.findall(r"\d+", text or "")
    return tuple(int(part) for part in parts[:3]) + (0,) * (3 - len(parts[:3]))


def is_newer(candidate, current):
    return parse_version(candidate) > parse_version(current)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def app_home(data_dir):
    """Where updates are installed: the "app" folder in the tool's user data folder."""
    return os.path.join(data_dir, "app")


# ---- state -----------------------------------------------------------------------------------------------------
def current_path(home):
    return os.path.join(home, "current.json")


def read_current(home):
    try:
        with open(current_path(home), "r", encoding="utf-8") as handle:
            state = json.load(handle)
        return state if isinstance(state, dict) and state.get("dir") else None
    except (OSError, ValueError):
        return None


def _write_current(home, state):
    os.makedirs(home, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".current-", suffix=".tmp", dir=home)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(state, stream, indent=2)
        os.replace(temporary, current_path(home))
    except BaseException:
        try:
            os.remove(temporary)
        except OSError:
            pass
        raise


def current_root(home):
    """Folder of the active installed version, or None when nothing valid is installed."""
    state = read_current(home)
    if state:
        root = os.path.join(home, state["dir"])
        if os.path.isfile(os.path.join(root, "python", "bootstrap.py")):
            return root
    return None


def rollback(home):
    """Make the previous installed version current again. True when it was switched; False when there is none
    (the launcher then starts the copy next to it)."""
    state = read_current(home)
    if not state or not state.get("previousDir"):
        if state:  # Nothing to go back to: forget the broken version, the bundled copy starts
            os.remove(current_path(home))
            return True
        return False
    if not os.path.isfile(os.path.join(home, state["previousDir"], "python", "bootstrap.py")):
        return False
    _write_current(home, {"version": state.get("previous", ""), "dir": state["previousDir"], "previous": "",
                          "previousDir": ""})
    return True


# ---- install ---------------------------------------------------------------------------------------------------
def _safe_extract(archive, folder):
    base = os.path.realpath(folder)
    for member in archive.infolist():
        target = os.path.realpath(os.path.join(folder, member.filename))
        if target != base and not target.startswith(base + os.sep):
            raise UpdateError("Unsafe path in update: {}".format(member.filename))
    archive.extractall(folder)


def _check_payload(folder, version):
    boot = os.path.join(folder, "python", "bootstrap.py")
    init = os.path.join(folder, "python", PACKAGE, "__init__.py")
    if not os.path.isfile(boot) or not os.path.isfile(init):
        raise UpdateError("Update is incomplete: bootstrap or package is missing")
    with open(init, "r", encoding="utf-8") as handle:
        match = re.search(r"^__version__\s*=\s*['\"]{1}([^'\"]+)['\"]", handle.read(), re.M)
    if not match or match.group(1) != version:
        raise UpdateError("Update version does not match its manifest")
    for current, _directories, names in os.walk(os.path.join(folder, "python")):
        for name in names:
            if name.endswith(".py"):
                path = os.path.join(current, name)
                with open(path, "r", encoding="utf-8") as handle:
                    try:
                        compile(handle.read(), path, "exec")  # Syntax check only; nothing is imported or run.
                    except SyntaxError as error:
                        raise UpdateError("Update has a syntax error in {}: {}".format(name, error))


def install_payload(home, info, zip_path):
    """Verify, unpack and activate a downloaded payload. Any failure leaves the current version untouched."""
    if sha256_file(zip_path) != info.sha256:
        raise UpdateError("Downloaded update does not match its checksum")
    os.makedirs(home, exist_ok=True)
    staging = tempfile.mkdtemp(prefix=".staging-", dir=home)
    try:
        try:
            with zipfile.ZipFile(zip_path) as archive:
                _safe_extract(archive, staging)
        except zipfile.BadZipFile as error:
            raise UpdateError("Update archive is damaged: {}".format(error))
        _check_payload(staging, info.version)
        target_name = "v" + info.version
        target = os.path.join(home, target_name)
        if os.path.isdir(target):
            os.rename(target, target + ".old-{}".format(int(time.time())))
        os.replace(staging, target)
        state = read_current(home) or {}
        previous = state if state.get("dir") and state.get("dir") != target_name else {}
        _write_current(home, {"version": info.version, "dir": target_name, "sha256": info.sha256,
                              "previous": previous.get("version", ""), "previousDir": previous.get("dir", "")})
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    prune(home)


def prune(home):
    state = read_current(home) or {}
    keep = {state.get("dir"), state.get("previousDir")}
    for name in os.listdir(home):
        path = os.path.join(home, name)
        if os.path.isdir(path) and name not in keep and (name.startswith("v") or name.startswith(".staging-")):
            shutil.rmtree(path, ignore_errors=True)


# ---- network ---------------------------------------------------------------------------------------------------
def _request(url, timeout):
    if url.lower().startswith("http"):  # Defeat caches of the raw-file host; file:// URLs take no query.
        url += ("&" if "?" in url else "?") + "t=" + str(int(time.time()))
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"})
    return urllib.request.urlopen(request, timeout=timeout)


def download(url, destination, timeout=30):
    """Download to `destination` (via a .part file). Falls back to curl.exe when urllib cannot connect."""
    part = destination + ".part"
    try:
        with _request(url, timeout) as response, open(part, "wb") as handle:
            shutil.copyfileobj(response, handle)
    except Exception as first_error:
        curl = shutil.which("curl.exe") or shutil.which("curl")
        if not curl or not url.lower().startswith("http"):
            raise UpdateError("Download failed: {}".format(first_error))
        flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
        done = subprocess.run([curl, "-fsSL", "--max-time", str(timeout * 4), "-o", part, url],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
        if done.returncode != 0 or not os.path.isfile(part):
            raise UpdateError("Download failed: {}".format(first_error))
    if not os.path.isfile(part) or os.path.getsize(part) == 0:
        raise UpdateError("Downloaded file is empty")
    os.replace(part, destination)
    return destination


def fetch_manifest(update_url, timeout=15):
    """The published update.json as a dict. Raises UpdateError when it cannot be read."""
    try:
        with _request(update_url, timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise UpdateError("No update has been published yet.")
        raise UpdateError("The update server answered with an error ({}).".format(error.code))
    except urllib.error.URLError as error:
        raise UpdateError("Could not reach the update server: {}".format(error.reason))
    except Exception as error:
        raise UpdateError("Could not check for updates: {}".format(error))
    if not isinstance(data, dict):
        raise UpdateError("Update information is invalid")
    return data


def fetch_info(update_url, current_version, timeout=15, data=None):
    """UpdateInfo when a newer version is published, else None. Raises UpdateError when the check itself fails."""
    data = data if data is not None else fetch_manifest(update_url, timeout)
    try:
        payload = data["payload"]
        info = UpdateInfo(str(data["version"]), payload["url"], payload["sha256"], data.get("notes"))
    except (KeyError, ValueError, TypeError) as error:
        raise UpdateError("Update information is invalid: {}".format(error))
    return info if is_newer(info.version, current_version) else None


def download_and_install(home, info, timeout=60):
    temp = tempfile.mkdtemp(prefix=PACKAGE + "-update-")
    try:
        archive = download(info.url, os.path.join(temp, "payload.zip"), timeout)
        install_payload(home, info, archive)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
```

## `tools/release.py`

```python
"""Prepare a self-update of MyTool (any Python 3.7+, no Qt):

    python tools/release.py --base-url https://raw.githubusercontent.com/<owner>/<repo>/main/release/ [--note "..."]

It writes two files into release/:
    mytool-app-<version>.zip   the application: python/ and assets/ of this project (caches left out)
    update.json                read by installed copies: version, payload URL + SHA-256 + size, notes

The version comes from python/mytool/__init__.py. Notes come from --note (repeatable) or, when there is none, from
release/notes.txt (one line per change, "+ Added: ...", "- Fixed: ...", "* Changed: ..."). Nothing is uploaded,
committed or published: put both files at --base-url, the archive first and update.json last (an installed copy that
reads update.json must find its archive), and set UPDATE_URL in python/mytool/__init__.py to <base-url>update.json.
Never replace a published archive of a version with different bytes: publish a new version instead.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = "mytool"
RELEASE = os.path.join(ROOT, "release")
INCLUDE = ("python", "assets")
SKIP_DIRS = {"__pycache__", ".git"}
SKIP_SUFFIXES = (".pyc", ".pyo", ".bak", ".tmp", ".log")


def package_version():
    with open(os.path.join(ROOT, "python", PACKAGE, "__init__.py"), encoding="utf-8") as handle:
        return re.search(r"^__version__\s*=\s*['\"]{1}([^'\"]+)['\"]", handle.read(), re.M).group(1)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def build_payload(version):
    """The archive with fixed timestamps, so the same sources give the same bytes."""
    os.makedirs(RELEASE, exist_ok=True)
    target = os.path.join(RELEASE, "{}-app-{}.zip".format(PACKAGE, version))
    files = []
    for top in INCLUDE:
        for folder, directories, names in os.walk(os.path.join(ROOT, top)):
            directories[:] = sorted(d for d in directories if d not in SKIP_DIRS)
            for name in sorted(names):
                if not name.endswith(SKIP_SUFFIXES):
                    path = os.path.join(folder, name)
                    files.append((os.path.relpath(path, ROOT).replace(os.sep, "/"), path))
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in files:
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(path, "rb") as handle:
                archive.writestr(info, handle.read())
    return target, len(files)


def read_notes(given):
    if given:
        return list(given)
    path = os.path.join(RELEASE, "notes.txt")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [line.rstrip() for line in handle if line.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prepare a self-update of MyTool (writes release/).")
    parser.add_argument("--base-url", required=True, help="The published address of the release folder, ending in /")
    parser.add_argument("--note", action="append", default=[], help="One line of the release notes (repeatable)")
    arguments = parser.parse_args(argv)
    base = arguments.base_url if arguments.base_url.endswith("/") else arguments.base_url + "/"
    if not base.lower().startswith(("https://", "file:")):
        parser.error("--base-url must be an https:// address (file: only for tests)")
    version = package_version()
    payload, count = build_payload(version)
    data = {
        "schema": 1,
        "version": version,
        "payload": {"url": base + os.path.basename(payload), "sha256": sha256(payload),
                    "size": os.path.getsize(payload)},
        "notes": read_notes(arguments.note),
    }
    with open(os.path.join(RELEASE, "update.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    print("version ", version)
    print("payload ", payload, "({} files, {} bytes)".format(count, data["payload"]["size"]))
    print("sha256  ", data["payload"]["sha256"])
    print("update  ", os.path.join(RELEASE, "update.json"))
    print("Publish the archive, then update.json, at", base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
