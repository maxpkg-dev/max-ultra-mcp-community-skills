"""Validate metadata, generate catalog pages, build ZIPs, or stage a reviewed submission."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
from time import sleep
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from validate import MAX_ZIP, NAME, fingerprint, frontmatter, no_links, package_bytes, read_folder, read_zip, require

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/maxpkg-dev/max-ultra-mcp-community-skills'
CATEGORIES = ('Architectural visualization', 'Modeling', 'Materials', 'Lighting', 'Cameras', 'Scene preparation', 'Other')
BEGIN, END = '<!-- catalog:start -->', '<!-- catalog:end -->'


def text(value):
    require(isinstance(value, str) and value.strip() and len(value) <= 4000 and not re.search(r'[\x00-\x1f\x7f]', value), 'Expected nonempty single-line text')
    require(not re.search(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/Users/|/home/', value), 'Private path in metadata')
    return value


def url(value):
    if value is None:
        return
    parsed = urlparse(text(value))
    require(parsed.scheme == 'https' and parsed.hostname and not parsed.username and not re.search(r'[\s<>"()]', value), 'Expected public HTTPS URL')


def person(value):
    require(isinstance(value, dict) and set(value) == {'name', 'profile'}, 'Person needs name and profile')
    text(value['name'])
    url(value['profile'])


def metadata(path, files):
    m = json.loads(no_links(path).read_text(encoding='utf-8'))
    keys = {'schemaVersion', 'id', 'title', 'version', 'publishedVersion', 'category', 'purpose', 'usage', 'author', 'submitter', 'reviewer', 'dependencies', 'testedVersions', 'verification', 'terms', 'provenance', 'submission', 'packageSha256'}
    require(set(m) == keys and m['schemaVersion'] == 1, 'Unknown/missing metadata fields')
    require(NAME.fullmatch(m['id']) and len(m['id']) <= 64 and m['id'] == path.parent.name, 'Metadata ID mismatch')
    require(frontmatter(files['SKILL.md'])['name'] == m['id'], 'Frontmatter ID mismatch')
    require(re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', m['version']), 'Use stable X.Y.Z version')
    if m['publishedVersion'] is not None:
        require(isinstance(m['publishedVersion'], str) and re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', m['publishedVersion']), 'Invalid published version')
        require(tuple(map(int, m['publishedVersion'].split('.'))) <= tuple(map(int, m['version'].split('.'))), 'Published version exceeds catalog version')
    require(m['category'] in CATEGORIES, 'Unknown category')
    for key in ('title', 'purpose', 'provenance'):
        text(m[key])
    require(isinstance(m['usage'], dict) and set(m['usage']) == {'steps', 'examples', 'expectedOutput'}, 'Usage needs steps, examples, and expectedOutput')
    for key in ('steps', 'examples'):
        require(isinstance(m['usage'][key], list) and 1 <= len(m['usage'][key]) <= 10, 'Usage needs a bounded nonempty list')
        for value in m['usage'][key]:
            text(value)
    text(m['usage']['expectedOutput'])
    person(m['author'])
    for key in ('submitter', 'reviewer'):
        if m[key] is not None:
            person(m[key])
    url(m['submission'])
    for key in ('dependencies', 'testedVersions'):
        require(isinstance(m[key], list) and len(m[key]) <= 30, 'Expected bounded list')
        for item in m[key]:
            text(item)
    require(set(m['verification']) == {'level', 'evidence'}, 'Verification needs level and evidence')
    require(m['verification']['level'] in ('package-validated', 'discovery-reported', 'practically-tested'), 'Invalid verification level')
    text(m['verification']['evidence'])
    if m['verification']['level'] == 'practically-tested':
        require(m['testedVersions'] and m['reviewer'], 'Practical testing requires versions and reviewer')
    require(set(m['terms']) == {'distribution', 'adaptation', 'evidence'}, 'Incomplete distribution terms')
    for value in m['terms'].values():
        text(value)
    require(m['packageSha256'] == fingerprint(files), 'Package changed: review content, bump version if released, and refresh packageSha256')
    return m


def load(root=ROOT):
    records = []
    for directory in sorted((root / 'skills').iterdir()):
        no_links(directory)
        require(directory.is_dir() and {p.name for p in directory.iterdir()} == {'metadata.json', 'package'}, 'Skill directory must contain metadata.json and package only')
        files = read_folder(directory / 'package')
        records.append((metadata(directory / 'metadata.json', files), files))
    require(records, 'Empty catalog')
    return records


def escape(value):
    return re.sub(r'([\\`*{}_\[\]()|#!])', r'\\\1', html.escape(value, quote=False))


def credit(value):
    if value is None:
        return 'Not recorded'
    label = escape(value['name'])
    return f"[{label}]({value['profile']})" if value['profile'] else label


def asset_name(m):
    return f"{m['id']}-{m['version']}-max-ultra-mcp.zip"


def tag_name(m):
    return f"{m['id']}-v{m['version']}"


def download_url(m):
    if m['publishedVersion'] is None:
        return None
    return f"{REPO}/releases/download/{m['id']}-latest/{m['id']}-latest-max-ultra-mcp.zip"


def download_link(m):
    target = download_url(m)
    return f"[Download ZIP]({target})" if target else 'Publication pending'


def download_section(m):
    target = download_url(m)
    if target is None:
        return f"Version {m['version']} is awaiting confirmed publication. No download is available yet."
    return (f"**{download_link(m)}** · [Version history and checksums]({REPO}/releases?q={m['id']}-v)"
            "\n\nThis permanent link downloads this skill's latest verified published ZIP. "
            "It stays the same when a new version is released. Numbered releases remain available in the history.")


def public_bytes(address, limit):
    # Only caller-constructed GitHub endpoints are used; no submitted URLs or credentials.
    request = Request(address, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'max-ultra-community-catalog', 'Cache-Control': 'no-cache'})
    with urlopen(request, timeout=60) as response:
        data = response.read(limit + 1)
    require(len(data) <= limit, 'Published response exceeds size limit')
    return data


def confirm_publication(skill_id, root=ROOT, fetch=public_bytes):
    """Verify the public current-version ZIP/checksum, then update local catalog files only."""
    records = load(root)
    matches = [(m, files) for m, files in records if m['id'] == skill_id]
    require(len(matches) == 1, 'Unknown skill ID')
    m, files = matches[0]
    api = REPO.replace('https://github.com/', 'https://api.github.com/repos/')
    published = json.loads(fetch(f'{api}/releases/tags/{tag_name(m)}', 1024 * 1024))
    require(published['tag_name'] == tag_name(m) and not published['draft'] and not published['prerelease'], 'A public stable release is required')
    names = {asset['name'] for asset in published['assets'] if asset['state'] == 'uploaded'}
    asset = asset_name(m)
    require({asset, asset + '.sha256'} <= names, 'ZIP and checksum must both be uploaded')
    versioned_target = f'{REPO}/releases/download/{tag_name(m)}/{asset_name(m)}'
    target = download_url({**m, 'publishedVersion': m['version']})
    expected_hash = hashlib.sha256(package_bytes(files)).hexdigest()
    require(hashlib.sha256(fetch(versioned_target, MAX_ZIP)).hexdigest() == expected_hash, 'Published ZIP differs from reviewed package')
    checksum = fetch(versioned_target + '.sha256', 4096).decode('utf-8').strip()
    require(checksum == f'{expected_hash}  {asset}', 'Published checksum differs from reviewed package')
    alias = json.loads(fetch(f"{api}/releases/tags/{m['id']}-latest", 1024 * 1024))
    require(not alias['draft'] and not alias['prerelease'], 'Stable download alias is not public')
    matches = False
    for attempt in range(4):
        try:
            matches = hashlib.sha256(fetch(target, MAX_ZIP)).hexdigest() == expected_hash
        except URLError:
            if attempt == 3:
                raise
        if matches:
            break
        if attempt < 3:
            sleep(2 ** attempt)
    require(matches, 'Stable download has not advanced to this verified version; retry after GitHub cache propagation')
    # All remote checks finish before local metadata or links change.
    m['publishedVersion'] = m['version']
    path = root / 'skills' / m['id'] / 'metadata.json'
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    generate(root)
    return target


def detail(m, files):
    bullet = lambda values: '\n'.join('- ' + escape(v) for v in values) if values else '- No practical software-version tests recorded.'
    usage_steps = '\n'.join(f'{i}. {escape(step)}' for i, step in enumerate(m['usage']['steps'], 1))
    return f"""<!-- Generated by tools/catalog.py; edit metadata.json instead. -->
# {escape(m['title'])}

By **{credit(m['author'])}** · Version **{m['version']}** · {escape(m['category'])}

{escape(m['purpose'])}

## Download and install

{download_section(m)}

In Max Ultra MCP, use **Skills → Custom → Import ZIPs**, then start a new AI chat.
For updates and duplicate-name handling, see the [installation guide](../INSTALL.md).

## How to use

{usage_steps}

Example requests:

{bullet(m['usage']['examples'])}

Expected output: {escape(m['usage']['expectedOutput'])}

## Dependencies

{bullet(m['dependencies'])}

## Verification

Level: **{m['verification']['level']}**. Package validation runs independently of practical testing.

{escape(m['verification']['evidence'])}

Tested software versions:

{bullet(m['testedVersions'])}

## Attribution and permission

- Author: {credit(m['author'])}
- Submitter: {credit(m['submitter'])}
- Reviewer: {credit(m['reviewer'])}
- Submission: {m['submission'] or 'Prepared initial contribution; no public issue recorded.'}

Distribution: {escape(m['terms']['distribution'])}

Adaptation: {escape(m['terms']['adaptation'])}

Permission evidence: {escape(m['terms']['evidence'])}

Provenance: {escape(m['provenance'])}

## Package

{len(files)} files · {sum(map(len, files.values())):,} bytes expanded · instruction-only.

Content fingerprint: `{fingerprint(files)}`.

[Read the instructions](../../skills/{m['id']}/package/SKILL.md) · [Metadata](../../skills/{m['id']}/metadata.json)
"""


def generated(root=ROOT):
    records = load(root)
    rows = ['| Skill | Author | Purpose | Version | Download |', '| --- | --- | --- | --- | --- |']
    output = {}
    for m, files in records:
        rows.append(f"| [{escape(m['title'])}](docs/skills/{m['id']}.md) | {credit(m['author'])} | {escape(m['purpose'])} | {m['version']} | {download_link(m)} |")
        output[root / 'docs' / 'skills' / (m['id'] + '.md')] = detail(m, files)
    readme = (root / 'README.md').read_text(encoding='utf-8')
    require(readme.count(BEGIN) == readme.count(END) == 1, 'README catalog markers missing/duplicated')
    start, tail = readme.split(BEGIN)
    _, end = tail.split(END)
    output[root / 'README.md'] = start + BEGIN + '\n\n' + '\n'.join(rows) + '\n\n' + END + end
    return output


def generate(root=ROOT, check=False):
    output = generated(root)
    existing = set((root / 'docs' / 'skills').glob('*.md'))
    require(not existing - set(output), 'Stale detail pages: remove pages for removed skills')
    for path, content in output.items():
        if check:
            require(path.exists() and path.read_text(encoding='utf-8') == content, 'Generated catalog is stale: ' + path.name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')


def build(root=ROOT, output=None):
    generate(root, check=True)
    output = output or root / 'dist'
    output.mkdir(parents=True, exist_ok=True)
    no_links(output)
    manifest = []
    for m, files in load(root):
        data = package_bytes(files)
        name = asset_name(m)
        destination = output / name
        if destination.exists():
            no_links(destination)
        destination.write_bytes(data)
        require(read_zip(destination) == files, 'Built ZIP roundtrip mismatch')
        sha = hashlib.sha256(data).hexdigest()
        checksum = output / (name + '.sha256')
        if checksum.exists():
            no_links(checksum)
        checksum.write_text(f'{sha}  {name}\n', encoding='utf-8', newline='\n')
        manifest.append({'id': m['id'], 'version': m['version'], 'title': m['title'], 'tag': tag_name(m), 'asset': name, 'sha256': sha})
    target = output / 'manifest.json'
    if target.exists():
        no_links(target)
    target.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    return manifest


def stage(source, destination):
    files = read_zip(source)
    destination = Path(destination).absolute()
    require(not destination.exists(), 'Staging destination must not exist')
    no_links(destination.parent)
    destination.mkdir()
    for name, data in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return fingerprint(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'generate', 'check', 'build'):
        commands.add_parser(name)
    inspect = commands.add_parser('inspect')
    inspect.add_argument('source', type=Path)
    staging = commands.add_parser('stage')
    staging.add_argument('zip', type=Path)
    staging.add_argument('destination', type=Path)
    confirmation = commands.add_parser('confirm-publication', help='Verify a public release and update local download links; does not publish or push')
    confirmation.add_argument('skill_id')
    args = parser.parse_args()
    if args.command == 'validate':
        print(f'Validated {len(load())} skill(s)')
    elif args.command in ('generate', 'check'):
        generate(check=args.command == 'check')
        print('Catalog is current')
    elif args.command == 'build':
        print(json.dumps(build(), indent=2))
    elif args.command == 'stage':
        print('Staged validated content. Review before copying into skills/. Fingerprint: ' + stage(args.zip, args.destination))
    elif args.command == 'confirm-publication':
        print('Confirmed download; review and commit the generated catalog changes: ' + confirm_publication(args.skill_id))
    else:
        files = read_folder(args.source) if args.source.is_dir() else read_zip(args.source)
        print(json.dumps({'files': len(files), 'bytes': sum(map(len, files.values())), 'packageSha256': fingerprint(files), **frontmatter(files['SKILL.md'])}, indent=2))


if __name__ == '__main__':
    main()
