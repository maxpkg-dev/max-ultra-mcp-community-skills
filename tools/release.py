"""Publish accepted default-branch packages; called only by gated release workflow.

Existing public assets are verified, never overwritten. Partial drafts can resume.
No requests are made at import time. Package content is never executed.
"""
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from catalog import ROOT, build
from validate import require


class AssetRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require(urlparse(newurl).scheme == 'https', 'Non-HTTPS asset redirect')
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if urlparse(newurl).hostname != urlparse(req.full_url).hostname:
            redirected.remove_header('Authorization')
        return redirected


class GitHub:
    def __init__(self, repository, token):
        require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository), 'Invalid repository')
        self.base = 'https://api.github.com/repos/' + repository
        self.upload_base = 'https://uploads.github.com/repos/' + repository
        self.token = token

    def request(self, method, path, body=None, binary=False):
        url = path if path.startswith('https://') else self.base + path
        require(url.startswith((self.base + '/', self.upload_base + '/')), 'Unexpected API endpoint')
        headers = {'Authorization': 'Bearer ' + self.token, 'Accept': 'application/octet-stream' if binary else 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
        if isinstance(body, bytes):
            data = body
            headers['Content-Type'] = 'application/octet-stream'
        else:
            data = json.dumps(body).encode() if body is not None else None
            headers['Content-Type'] = 'application/json'
        with build_opener(AssetRedirect()).open(Request(url, data=data, headers=headers, method=method), timeout=60) as response:
            result = response.read()
        return result if binary else json.loads(result)

    def find(self, tag):
        try:
            return self.request('GET', '/releases/tags/' + tag)
        except HTTPError as error:
            if error.code != 404:
                raise
        # The tag endpoint may not expose drafts; authenticated listing includes them.
        page = 1
        while True:
            releases = self.request('GET', f'/releases?per_page=100&page={page}')
            for release in releases:
                if release['tag_name'] == tag:
                    return release
            if len(releases) < 100:
                return None
            page += 1

    def check_new_tag(self, tag, commit):
        try:
            ref = self.request('GET', '/git/ref/tags/' + tag)
        except HTTPError as error:
            if error.code == 404:
                return
            raise
        require(ref['object']['type'] == 'commit' and ref['object']['sha'] == commit,
                'Existing tag does not point to this accepted commit; inspect manually')


def publish(api, item, commit, output):
    asset = item['asset']
    files = {asset: (output / asset).read_bytes(), asset + '.sha256': (output / (asset + '.sha256')).read_bytes()}
    require(hashlib.sha256(files[asset]).hexdigest() == item['sha256'], 'Local asset hash mismatch')
    release = api.find(item['tag'])
    if release is None:
        api.check_new_tag(item['tag'], commit)
        release = api.request('POST', '/releases', {
            'tag_name': item['tag'], 'target_commitish': commit, 'name': item['title'] + ' ' + item['version'],
            'draft': True, 'prerelease': False,
            'body': f"Reviewed catalog package. Download `{asset}`, not Source code.\n\nSHA-256: `{item['sha256']}`\n\nSource commit: `{commit}`. Attribution, permission and verification evidence are recorded in `skills/{item['id']}/metadata.json` at that commit. Structural checks do not establish practical test coverage."
        })
    existing = {entry['name']: entry for entry in release['assets']}
    require(set(existing) <= set(files), 'Unexpected release assets; inspect manually')
    for name, data in files.items():
        if name in existing:
            remote = api.request('GET', '/releases/assets/' + str(existing[name]['id']), binary=True)
            require(remote == data, 'Released content differs; use a new version: ' + name)
        else:
            require(release['draft'], 'Public release incomplete; inspect manually, no automatic mutation')
            endpoint = release['upload_url'].split('{')[0] + '?name=' + name
            api.request('POST', endpoint, data)
    if release['draft']:
        api.request('PATCH', '/releases/' + str(release['id']), {'draft': False, 'make_latest': 'false'})
    print('Verified release: ' + item['tag'])


def main():
    require(os.environ.get('GITHUB_ACTIONS') == 'true', 'Publication is restricted to GitHub Actions')
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    require(os.environ['GITHUB_EVENT_NAME'] in ('push', 'workflow_dispatch'), 'Unsupported release trigger')
    require(os.environ['GITHUB_REF'] == 'refs/heads/' + event['repository']['default_branch'], 'Default branch only')
    commit = os.environ['GITHUB_SHA']
    require(re.fullmatch(r'[a-f0-9]{40}', commit), 'Expected commit SHA')
    api = GitHub(os.environ['GITHUB_REPOSITORY'], os.environ['GH_TOKEN'])
    for item in build():
        publish(api, item, commit, ROOT / 'dist')


if __name__ == '__main__':
    main()
