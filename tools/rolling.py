"""Maintain only explicitly managed per-skill rolling downloads.

Numbered releases/tags are read-only here. Upload and verify before swapping names;
GitHub does not provide an atomic asset replacement operation. See ROLLING_DOWNLOADS.md.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from uuid import uuid4
from urllib.parse import quote

from catalog import ROOT, REPO, build, confirm_publication
from release import GitHub
from validate import require


def version_tuple(value):
    require(re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value), 'Invalid stable version')
    return tuple(map(int, value.split('.')))


def latest_numbered(api, skill_id):
    found = []
    page = 1
    pattern = re.compile(re.escape(skill_id) + r'-v((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))$')
    while True:
        rows = api.request('GET', f'/releases?per_page=100&page={page}')
        for row in rows:
            match = pattern.fullmatch(row['tag_name'])
            if match and not row['draft'] and not row['prerelease']:
                found.append((version_tuple(match[1]), row))
        if len(rows) < 100:
            break
        page += 1
    require(found, 'No public stable numbered release for this skill')
    return max(found, key=lambda pair: pair[0])[1]


def marker(skill_id):
    return f'<!-- max-ultra-managed-rolling:v1:{skill_id} -->'


def stable_name(skill_id):
    return f'{skill_id}-latest-max-ultra-mcp.zip'


def asset_bytes(api, asset):
    require(asset['state'] == 'uploaded', 'Asset upload is incomplete; do not replace the live download')
    return api.request('GET', '/releases/assets/' + str(asset['id']), binary=True)


def refresh(api, item, commit, output):
    """Refresh one reviewed version; idempotent, no deletes, no numbered-release writes."""
    skill_id, version = item['id'], item['version']
    data = (output / item['asset']).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == item['sha256'], 'Local artifact mismatch')
    source = latest_numbered(api, skill_id)
    require(source['tag_name'] == item['tag'], 'A newer/different public version exists; use its accepted source, never downgrade')
    numbered = {a['name']: a for a in source['assets']}
    require(item['asset'] in numbered and item['asset'] + '.sha256' in numbered, 'Numbered ZIP/checksum missing')
    require(asset_bytes(api, numbered[item['asset']]) == data, 'Numbered ZIP differs from reviewed build')
    require(asset_bytes(api, numbered[item['asset'] + '.sha256']).decode().strip() == f"{digest}  {item['asset']}", 'Numbered checksum mismatch')
    # Inspect per-release immutability; the repository settings endpoint requires admin
    # permissions unavailable to GITHUB_TOKEN. Never change those global settings.
    tag = skill_id + '-latest'
    name = stable_name(skill_id)
    managed_marker = marker(skill_id)
    alias = api.find(tag)
    if alias is None:
        api.check_new_tag(tag, commit)
        alias = api.request('POST', '/releases', {
            'tag_name': tag, 'target_commitish': commit,
            'name': item['title'] + ' - latest download', 'draft': True,
            'prerelease': False, 'make_latest': 'false',
            'body': managed_marker + '\n\nManaged rolling download. Numbered release history remains unchanged.'
        })
    require(alias['tag_name'] == tag and (alias.get('body') or '').startswith(managed_marker + '\n'), 'Refusing to modify an unmanaged release')
    require(not alias.get('immutable', False) and not alias['prerelease'], 'Rolling release is immutable or a prerelease')
    alias_id = alias['id']

    def current():
        row = api.request('GET', '/releases/' + str(alias_id))
        require(row['tag_name'] == tag and (row.get('body') or '').startswith(managed_marker + '\n') and not row.get('immutable', False), 'Rolling release changed unexpectedly')
        return row

    def by_name(row):
        return {a['name']: a for a in row['assets']}

    def rename(asset, new_name):
        # Recheck membership: only assets in the designated rolling release can be renamed.
        require(any(a['id'] == asset['id'] for a in current()['assets']), 'Asset is not owned by this rolling release')
        return api.request('PATCH', '/releases/assets/' + str(asset['id']), {'name': new_name})

    aliases = by_name(current())
    live = aliases.get(name)
    if live and asset_bytes(api, live) == data:
        pass  # Retry after a successful swap or a metadata-only source update.
    else:
        if live:
            label_match = re.fullmatch(r'version=([0-9.]+);sha256=([a-f0-9]{64})', live.get('label') or '')
            require(label_match is not None and version_tuple(label_match[1]) <= version_tuple(version), 'Unknown live version or attempted rollback')
            require(hashlib.sha256(asset_bytes(api, live)).hexdigest() == label_match[2], 'Existing live asset is corrupt; inspect manually')
        candidate_name = f'candidate-{digest}-{name}'
        candidate = None
        for possible in aliases.values():
            if possible['name'].startswith(f'candidate-{digest}-') and possible['name'].endswith(name) and possible['state'] == 'uploaded':
                if asset_bytes(api, possible) == data:
                    candidate = possible
                    break
        if candidate is None:
            # A failed GitHub upload can leave a starter/partial asset. Retain it and use
            # a fresh name rather than deleting anything or poisoning every future retry.
            if candidate_name in aliases:
                candidate_name = f'candidate-{digest}-{uuid4().hex}-{name}'
            endpoint = alias['upload_url'].split('{')[0] + '?name=' + quote(candidate_name) + '&label=' + quote(f'version={version};sha256={digest}')
            candidate = api.request('POST', endpoint, data)
        require(asset_bytes(api, candidate) == data, 'Candidate upload failed verification; old download retained')
        require(latest_numbered(api, skill_id)['tag_name'] == item['tag'], 'New release appeared during refresh; retry from latest accepted source')
        now = by_name(current()).get(name)
        require((now or {}).get('id') == (live or {}).get('id'), 'Concurrent updater detected; retry serially')
        try:
            if live:
                rename(live, f"backup-{live['id']}-{name}")
            rename(candidate, name)
        except Exception:
            # A timeout may occur after GitHub applied the rename. Inspect before recovery.
            visible = by_name(current()).get(name)
            if visible and asset_bytes(api, visible) == data:
                pass
            elif visible is None and live:
                rename(live, name)
                raise
            else:
                raise
    visible = by_name(current()).get(name)
    require(visible is not None and asset_bytes(api, visible) == data, 'Stable asset verification failed')
    body = (managed_marker + f"\n\nLatest verified version: **{version}**.\n\n"
            f"[Download ZIP]({REPO}/releases/download/{tag}/{name})\n\n"
            f"SHA-256: `{digest}`\n\n"
            f"[Numbered release and checksum]({REPO}/releases/tag/{item['tag']})\n\n"
            "This release is the only mutable download alias for this skill. Its tag is an anchor, not the current package source. "
            "Numbered releases remain unchanged. Retained backup/candidate files support recovery; use Download ZIP above.")
    published_alias = api.request('PATCH', '/releases/' + str(alias_id), {'draft': False, 'make_latest': 'false', 'body': body})
    require(not published_alias.get('immutable', False), 'GitHub made the alias immutable; do not disable protections, choose a different stable endpoint')
    return f'{REPO}/releases/download/{tag}/{name}'


def git(*args, root=ROOT, env=None):
    result = subprocess.run(['git', *args], cwd=root, env=env, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def accepted_commit(api, item, root=ROOT):
    """Bind local package metadata to the actual accepted default-branch source."""
    repository = api.request('GET', '')
    default = repository['default_branch']
    head = api.request('GET', '/commits/' + quote(default, safe=''))['sha']
    require(git('rev-parse', 'HEAD', root=root) == head, 'Checkout must be at the current accepted default-branch commit')
    remote = api.request('GET', f"/contents/skills/{item['id']}/metadata.json?ref={head}")
    metadata = json.loads(base64.b64decode(remote['content']))
    local = json.loads((root / 'skills' / item['id'] / 'metadata.json').read_text(encoding='utf-8'))
    require(all(metadata[k] == local[k] for k in ('id', 'version', 'packageSha256')), 'Local package metadata is not the accepted version')
    return head, default


def commit_catalog(api, ids, default, root=ROOT):
    """Publish only verified catalog metadata/pages, using a normal non-force push."""
    paths = ['README.md'] + [p for skill in ids for p in (f'skills/{skill}/metadata.json', f'docs/skills/{skill}.md')]
    changed = git('diff', '--name-only', root=root).splitlines()
    require(set(changed) <= set(paths) and not git('diff', '--cached', '--name-only', root=root), 'Unexpected checkout changes; refusing catalog commit')
    if not changed:
        return
    git('add', '--', *paths, root=root)
    git('-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com', 'commit', '-m', 'Confirm verified rolling skill downloads', root=root)
    # Token exists only in the child process environment; never print or persist it.
    env = os.environ.copy()
    env.update({'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'http.https://github.com/.extraheader',
                'GIT_CONFIG_VALUE_0': 'AUTHORIZATION: basic ' + base64.b64encode(('x-access-token:' + api.token).encode()).decode()})
    repository_url = api.base.replace('https://api.github.com/repos/', 'https://github.com/') + '.git'
    git('push', repository_url, 'HEAD:refs/heads/' + default, root=root, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--skill', help='Manual recovery/initialization for one accepted skill')
    group.add_argument('--event', action='store_true', help='Handle a numbered release published event')
    args = parser.parse_args()
    token = os.environ.get('GH_TOKEN')
    if not token:
        token = subprocess.run(['gh', 'auth', 'token'], check=True, capture_output=True, text=True).stdout.strip()
    api = GitHub('maxpkg-dev/max-ultra-mcp-community-skills', token)
    records = build()
    if args.event:
        trigger = os.environ.get('GITHUB_EVENT_NAME')
        require(trigger in ('release', 'workflow_dispatch'), 'Expected release or recovery event')
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        if trigger == 'release':
            release = event['release']
            require(event['action'] == 'published' and not release['draft'] and not release['prerelease'], 'Expected published stable release')
            records = [item for item in records if item['tag'] == release['tag_name']]
        else:
            records = [item for item in records if item['id'] == event['inputs']['skill']]
            require(len(records) == 1, 'Unknown recovery skill')
        if not records:
            print('No current accepted skill version matches this release; nothing mutated.')
            return
    else:
        records = [item for item in records if item['id'] == args.skill]
        require(len(records) == 1, 'Unknown skill ID')
    ids = []
    for item in records:
        commit, default = accepted_commit(api, item)
        address = refresh(api, item, commit, ROOT / 'dist')
        confirm_publication(item['id'])
        ids.append(item['id'])
        print('Verified stable download: ' + address)
    if args.event:
        commit_catalog(api, ids, default)
    else:
        print('Catalog metadata was confirmed locally. Commit/push it if changed; the release-event workflow handles this automatically for normal publications.')


if __name__ == '__main__':
    main()
