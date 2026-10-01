"""Self-contained instruction-only package validation. Never executes package content.

Independent implementation of the Max Ultra MCP custom-skill import contract.
See docs/VALIDATION.md for scope and compatibility notes.
"""
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import stat
import struct
from urllib.parse import unquote
import zipfile

MIB = 1024 * 1024
MAX_FILES, MAX_TOTAL, MAX_ZIP = 200, 50 * MIB, 54 * MIB
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
TEXT = {'.md', '.txt', '.json', '.csv'}
IMAGES = {'.png', '.jpg', '.jpeg', '.webp'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_path(name):
    require(isinstance(name, str) and 0 < len(name) <= 240, 'Invalid path length')
    require(not re.search(r'[\\:\x00-\x1f\x7f<>"|?*]', name), 'Unsafe path characters')
    for part in name.split('/'):
        require(part not in ('', '.', '..') and not part.endswith(('.', ' ')), 'Unsafe path segment')
        require(not re.match(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)', part, re.I), 'Reserved device name')
    return name


def no_links(path):
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        info = part.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not (getattr(info, 'st_file_attributes', 0) & 0x400), 'Linked/reparse path')
    return path


def frontmatter(data):
    text = data.decode('utf-8-sig').replace('\r\n', '\n')
    match = re.fullmatch(r'---\n(.*?)\n---\n(.+)', text, re.S)
    require(match is not None and match[2].strip(), 'Missing strict frontmatter or instructions')
    result = {}
    for line in match[1].splitlines():
        if not line.strip():
            continue
        field = re.fullmatch(r'(name|description):[ \t]*(.+)', line)
        require(field is not None and field[1] not in result, 'Only one name and description allowed')
        value = field[2].strip()
        if value.startswith('"'):
            value = json.loads(value)
        elif value.startswith("'"):
            require(re.fullmatch(r"'(?:[^']|'')*'", value), 'Invalid quoted field')
            value = value[1:-1].replace("''", "'")
        else:
            require(not re.search(r'^[!&*\[{>|%@`]|:\s|\s#', value), 'Quote special YAML characters')
        require(isinstance(value, str) and not re.search(r'[\x00-\x1f\x7f]', value), 'Single-line fields required')
        result[field[1]] = value
    require(NAME.fullmatch(result.get('name', '')) and len(result['name']) <= 64, 'Invalid skill name')
    require(result.get('description', '').strip() and len(result['description']) <= 1024, 'Invalid description')
    return result


def limit_for(name):
    if name == 'SKILL.md':
        return 64 * 1024
    extension = Path(name).suffix.lower()
    if name.startswith('references/') and extension in TEXT:
        return MIB
    if name.startswith('assets/') and extension in IMAGES:
        return 5 * MIB
    raise ValueError('Unsupported package file: ' + name)


def validate_files(files):
    require(0 < len(files) <= MAX_FILES, 'File count limit')
    require(sum(map(len, files.values())) <= MAX_TOTAL, 'Expanded size limit')
    require(sum(Path(n).name == 'SKILL.md' for n in files) == 1 and 'SKILL.md' in files, 'Exactly one root SKILL.md required')
    seen = {}
    for name, data in files.items():
        safe_path(name)
        require(len(name.split('/')) <= 9, 'Directory depth limit')
        parts = name.split('/')
        for i in range(1, len(parts) + 1):
            part = '/'.join(parts[:i])
            kind = 'file' if i == len(parts) else 'directory'
            require(part.lower() not in seen or seen[part.lower()] == (part, kind), 'Case or file/directory collision')
            seen[part.lower()] = (part, kind)
        require(len(data) <= limit_for(name), 'Per-file size limit: ' + name)
        if Path(name).suffix.lower() in TEXT:
            text = data.decode('utf-8-sig')
            require(not re.search(r'[A-Za-z]:[\\/](?:Users|Projects)[\\/]|/Users/|/home/[^/]+/', text), 'Private machine path')
            if name.lower().endswith('.md'):
                require(not re.search(r'!`|^\s*@[A-Za-z./\\~]', text, re.M), 'Native preprocessing is forbidden')
                links = re.findall(r'\]\(([^)\n]+)\)', text)
                links += re.findall(r'^\s*\[[^\]]+\]:\s*(\S+)', text, re.M)
                for link in links:
                    link = link.strip()
                    if link.startswith('<') and link.endswith('>'):
                        link = link[1:-1]
                    if re.match(r'^(https?://|#)', link, re.I):
                        continue
                    require(not re.search(r'%(?![0-9a-fA-F]{2})', link), 'Malformed encoded reference')
                    link = unquote(link.split('#')[0], errors='strict')
                    require(not re.search(r'^[/\\]|[:\\]', link), 'Reference escapes package')
                    target = safe_path(posixpath.normpath(posixpath.join(posixpath.dirname(name), link)))
                    require(target in files, 'Missing relative reference: ' + target)
    return frontmatter(files['SKILL.md'])


def read_folder(root):
    root = no_links(root)
    require(root.is_dir(), 'Expected package directory')
    files, seen, total = {}, set(), 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in sorted(dirs + names):
            path = no_links(Path(directory) / name)
            relative = safe_path(path.relative_to(root).as_posix())
            require(relative.lower() not in seen, 'Case collision')
            seen.add(relative.lower())
            if path.is_dir():
                require(relative.split('/')[0] in ('references', 'assets') and len(relative.split('/')) <= 8, 'Unsupported directory')
                continue
            require(path.is_file(), 'Only regular files supported')
            size = path.stat().st_size
            total += size
            require(size <= limit_for(relative) and total <= MAX_TOTAL and len(files) < MAX_FILES, 'Package size/count limit')
            files[relative] = path.read_bytes()
    validate_files(files)
    return dict(sorted(files.items()))


def read_zip(source):
    source = no_links(source)
    require(source.is_file() and source.stat().st_size <= MAX_ZIP, 'ZIP size/type limit')
    raw = source.read_bytes()
    # Exclude split/ZIP64 archives explicitly; importer accepts classic ZIP only.
    end = raw.rfind(b'PK\x05\x06', max(0, len(raw) - 65557))
    require(end >= 0 and end + 22 <= len(raw), 'Missing ZIP directory')
    disk, central_disk, count_disk, count, size, offset, comment = struct.unpack_from('<4H2IH', raw, end + 4)
    require(not disk and not central_disk and count_disk == count and 0 < count <= 1800, 'Split/entry-count ZIP unsupported')
    require(offset + size == end and end + 22 + comment == len(raw), 'ZIP64/trailing or corrupt directory')
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        require(len(entries) == count, 'ZIP entry count mismatch')
        seen, total, file_count, ranges = {}, 0, 0, []
        for entry in entries:
            require(entry.orig_filename == entry.filename, 'NUL ZIP name')
            name = safe_path(entry.filename[:-1] if entry.is_dir() else entry.filename)
            require(len(name.split('/')) <= 10, 'ZIP directory depth')
            require(name.lower() not in seen, 'Duplicate ZIP path')
            seen[name.lower()] = (name, entry.is_dir())
            require(not entry.flag_bits & ~0x80e and entry.compress_type in (0, 8), 'Encrypted/unsupported ZIP')
            require(entry.flag_bits & 0x800 or name.isascii(), 'ZIP names must use UTF-8')
            kind = stat.S_IFMT(entry.external_attr >> 16)
            require(kind in (0, stat.S_IFDIR if entry.is_dir() else stat.S_IFREG) and not entry.external_attr & 0x400, 'ZIP link/special file')
            cursor = 0
            while cursor < len(entry.extra):
                require(cursor + 4 <= len(entry.extra), 'Corrupt ZIP extra')
                tag, length = struct.unpack_from('<HH', entry.extra, cursor)
                require(tag != 1 and cursor + 4 + length <= len(entry.extra), 'ZIP64/corrupt ZIP extra')
                cursor += 4 + length
            local = entry.header_offset
            require(local >= 0 and local + 30 <= offset and raw[local:local+4] == b'PK\x03\x04', 'Invalid local ZIP header')
            flags, method = struct.unpack_from('<HH', raw, local + 6)
            nl, el = struct.unpack_from('<HH', raw, local + 26)
            require(flags == entry.flag_bits and method == entry.compress_type, 'ZIP header mismatch')
            require(raw[local+30:local+30+nl] == entry.filename.encode('utf-8' if flags & 0x800 else 'ascii'), 'ZIP name mismatch')
            finish = local + 30 + nl + el + entry.compress_size
            require(finish <= offset, 'ZIP data out of bounds')
            ranges.append((local, finish))
            if entry.is_dir():
                require(entry.file_size == entry.compress_size == 0, 'Nonempty ZIP directory')
            else:
                total += entry.file_size
                file_count += 1
                require(entry.file_size <= 5 * MIB and total <= MAX_TOTAL and file_count <= MAX_FILES, 'Expanded ZIP limit')
        ranges.sort()
        require(all(a[1] <= b[0] for a, b in zip(ranges, ranges[1:])), 'Overlapping ZIP entries')
        for name, is_dir in list(seen.values()):
            parts = name.split('/')
            for i in range(1, len(parts)):
                parent = '/'.join(parts[:i])
                require(parent.lower() not in seen or seen[parent.lower()] == (parent, True), 'ZIP directory collision')
                seen[parent.lower()] = (parent, True)
        roots = [e.filename for e in entries if not e.is_dir() and Path(e.filename).name == 'SKILL.md']
        require(len(roots) == 1 and len(roots[0].split('/')) <= 2, 'One root or enclosing folder required')
        prefix = roots[0][:-len('SKILL.md')]
        files = {}
        for entry in entries:
            require(not prefix or entry.filename == prefix or entry.filename.startswith(prefix), 'File outside skill folder')
            if entry.is_dir():
                relative = entry.filename[len(prefix):].rstrip('/')
                require(not relative or (relative.split('/')[0] in ('references', 'assets') and len(relative.split('/')) <= 8), 'Unsupported ZIP directory')
                continue
            name = entry.filename[len(prefix):]
            require(entry.file_size <= limit_for(name), 'ZIP per-file size limit')
            with archive.open(entry) as stream:
                data = stream.read(limit_for(name) + 1)
            require(len(data) == entry.file_size, 'ZIP length mismatch')
            files[name] = data
    validate_files(files)
    return dict(sorted(files.items()))


def fingerprint(files):
    records = [{'path': n, 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)} for n, b in sorted(files.items())]
    return hashlib.sha256(json.dumps(records, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def package_bytes(files):
    import io
    validate_files(files)
    buffer = io.BytesIO()
    # STORE avoids compressor-version differences; bounded packages stay below 54 MiB.
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(entry, data)
    require(buffer.tell() <= MAX_ZIP, 'Output ZIP limit')
    return buffer.getvalue()
