import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import rolling


class FakeGitHub:
    def __init__(self):
        self.releases = {}
        self.bytes = {}
        self.next_id = 100
        self.mutations = []
        self.fail_promotion = False
        self.interrupt_promotion = False
        self.timeout_after_promotion = False
        self.corrupt_upload = False

    def add_asset(self, release, name, data, label=''):
        self.next_id += 1
        a = {'id': self.next_id, 'name': name, 'label': label, 'state': 'uploaded'}
        release['assets'].append(a)
        self.bytes[a['id']] = data
        return a

    def numbered(self, skill, version, data, draft=False, prerelease=False):
        self.next_id += 1
        row = {'id': self.next_id, 'tag_name': f'{skill}-v{version}', 'draft': draft, 'prerelease': prerelease, 'assets': []}
        self.releases[row['id']] = row
        name = f'{skill}-{version}-max-ultra-mcp.zip'
        self.add_asset(row, name, data)
        self.add_asset(row, name + '.sha256', f'{hashlib.sha256(data).hexdigest()}  {name}\n'.encode())
        return row

    def find(self, tag):
        return copy.deepcopy(next((r for r in self.releases.values() if r['tag_name'] == tag), None))

    def check_new_tag(self, tag, commit):
        assert tag.endswith('-latest')

    def request(self, method, path, body=None, binary=False):
        if method == 'GET':
            if path.startswith('/releases?'):
                return copy.deepcopy(list(self.releases.values()))
            if path.startswith('/releases/assets/'):
                return self.bytes[int(path.split('/')[-1])]
            if path.startswith('/releases/'):
                return copy.deepcopy(self.releases[int(path.split('/')[-1])])
        self.mutations.append((method, path, copy.deepcopy(body)))
        if method == 'POST' and path == '/releases':
            assert body['tag_name'].endswith('-latest')
            self.next_id += 1
            row = {**body, 'id': self.next_id, 'immutable': False, 'assets': [], 'upload_url': f'https://uploads.github.com/repos/test/repo/releases/{self.next_id}/assets{{?name,label}}'}
            self.releases[row['id']] = row
            return copy.deepcopy(row)
        if method == 'POST' and path.startswith('https://uploads.'):
            parsed = urlparse(path)
            rid = int(parsed.path.split('/')[-2])
            fields = parse_qs(parsed.query)
            return copy.deepcopy(self.add_asset(self.releases[rid], fields['name'][0], b'corrupt' if self.corrupt_upload else body, fields.get('label', [''])[0]))
        if method == 'PATCH' and path.startswith('/releases/assets/'):
            aid = int(path.split('/')[-1])
            parent, asset = next((r,a) for r in self.releases.values() for a in r['assets'] if a['id'] == aid)
            assert parent['tag_name'].endswith('-latest'), 'Mutation of numbered assets forbidden'
            promotion = asset['name'].startswith('candidate-') and not body['name'].startswith('candidate-')
            if promotion and self.interrupt_promotion:
                self.interrupt_promotion = False
                raise SystemExit('Simulated process interruption')
            if promotion and self.fail_promotion:
                self.fail_promotion = False
                raise OSError('Promotion failed')
            assert not any(a['name'] == body['name'] and a['id'] != aid for a in parent['assets'])
            asset.update(body)
            if promotion and self.timeout_after_promotion:
                self.timeout_after_promotion = False
                raise OSError('Response lost after successful promotion')
            return copy.deepcopy(asset)
        if method == 'PATCH' and path.startswith('/releases/'):
            row = self.releases[int(path.split('/')[-1])]
            assert row['tag_name'].endswith('-latest'), 'Mutation of numbered release forbidden'
            row.update(body)
            return copy.deepcopy(row)
        raise AssertionError((method, path))


class RollingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.api = FakeGitHub()
        self.item = self.add_version('sample', '1.0.0', b'first ZIP')

    def add_version(self, skill, version, data):
        row = self.api.numbered(skill, version, data)
        name = f'{skill}-{version}-max-ultra-mcp.zip'
        (self.output / name).write_bytes(data)
        return {'id': skill, 'version': version, 'title': 'Example', 'tag': row['tag_name'], 'asset': name, 'sha256': hashlib.sha256(data).hexdigest()}

    def refresh(self, item=None):
        return rolling.refresh(self.api, item or self.item, 'a' * 40, self.output)

    def live(self, skill='sample'):
        row = self.api.find(skill + '-latest')
        asset = next(a for a in row['assets'] if a['name'] == rolling.stable_name(skill))
        return self.api.bytes[asset['id']]

    def test_new_alias_and_retries_leave_numbered_release_untouched(self):
        original = copy.deepcopy(self.api.find(self.item['tag']))
        original_bytes = copy.deepcopy(self.api.bytes)
        url = self.refresh()
        self.assertIn('/sample-latest/sample-latest-max-ultra-mcp.zip', url)
        self.assertEqual(self.live(), b'first ZIP')
        count = len(self.api.bytes)
        self.assertEqual(self.refresh(), url)
        self.assertEqual(len(self.api.bytes), count)
        self.assertEqual(self.api.find(self.item['tag']), original)
        for aid, data in original_bytes.items():
            self.assertEqual(self.api.bytes[aid], data)
        self.assertFalse(any(method == 'DELETE' for method, _, _ in self.api.mutations))

    def test_latest_semver_is_per_skill_and_excludes_drafts_prereleases(self):
        self.api.numbered('sample', '1.9.0', b'old')
        self.api.numbered('sample', '1.10.0', b'new')
        self.api.numbered('sample', '2.0.0', b'draft', draft=True)
        self.api.numbered('sample', '3.0.0', b'pre', prerelease=True)
        self.api.numbered('other', '99.0.0', b'other')
        self.assertEqual(rolling.latest_numbered(self.api, 'sample')['tag_name'], 'sample-v1.10.0')
        with self.assertRaises(ValueError):
            self.refresh()  # Older accepted source must never downgrade a newer public version.
        self.assertEqual(self.api.mutations, [])

    def test_other_skill_is_not_changed(self):
        self.refresh()
        before = self.api.find('sample-latest')
        other = self.add_version('other', '5.0.0', b'other')
        self.refresh(other)
        self.assertEqual(self.api.find('sample-latest'), before)
        self.assertEqual(self.live('other'), b'other')

    def test_update_stages_then_retains_last_good_bytes(self):
        url = self.refresh()
        newer = self.add_version('sample', '1.1.0', b'second ZIP')
        self.assertEqual(self.refresh(newer), url)
        self.assertEqual(self.live(), b'second ZIP')
        backups = [a for a in self.api.find('sample-latest')['assets'] if a['name'].startswith('backup-')]
        self.assertEqual(self.api.bytes[backups[0]['id']], b'first ZIP')

    def test_unverified_candidate_cannot_replace_good_download(self):
        self.refresh()
        newer = self.add_version('sample', '1.1.0', b'second ZIP')
        self.api.corrupt_upload = True
        with self.assertRaises(ValueError):
            self.refresh(newer)
        self.assertEqual(self.live(), b'first ZIP')
        self.api.corrupt_upload = False
        self.refresh(newer)
        self.assertEqual(self.live(), b'second ZIP')

    def test_missing_source_asset_retains_good_download(self):
        self.refresh()
        newer = self.add_version('sample', '1.1.0', b'second ZIP')
        row = next(r for r in self.api.releases.values() if r['tag_name'] == newer['tag'])
        row['assets'].pop()
        with self.assertRaises(ValueError):
            self.refresh(newer)
        self.assertEqual(self.live(), b'first ZIP')

    def test_promotion_failure_restores_old_name_and_retry_succeeds(self):
        self.refresh()
        newer = self.add_version('sample', '1.1.0', b'second ZIP')
        self.api.fail_promotion = True
        with self.assertRaises(OSError):
            self.refresh(newer)
        self.assertEqual(self.live(), b'first ZIP')
        self.refresh(newer)
        self.assertEqual(self.live(), b'second ZIP')

    def test_interrupted_swap_is_recoverable_on_retry(self):
        self.refresh()
        newer = self.add_version('sample', '1.1.0', b'second ZIP')
        self.api.interrupt_promotion = True
        with self.assertRaises(SystemExit):
            self.refresh(newer)
        self.refresh(newer)
        self.assertEqual(self.live(), b'second ZIP')

    def test_lost_success_response_does_not_rollback_good_new_zip(self):
        self.refresh()
        newer = self.add_version('sample', '1.1.0', b'second ZIP')
        self.api.timeout_after_promotion = True
        self.refresh(newer)
        self.assertEqual(self.live(), b'second ZIP')

    def test_unmanaged_or_immutable_alias_is_not_mutated(self):
        self.refresh()
        row = next(r for r in self.api.releases.values() if r['tag_name'] == 'sample-latest')
        for change in [{'immutable': True}, {'body': 'Unmanaged release'}]:
            old = copy.deepcopy(row)
            row.update(change)
            self.api.mutations.clear()
            with self.assertRaises(ValueError):
                self.refresh()
            self.assertEqual(self.api.mutations, [])
            row.clear()
            row.update(old)


    def test_event_path_ignores_alias_and_unknown_numbered_versions(self):
        event = self.output / 'event.json'
        for tag in ['sample-latest', 'sample-v99.0.0', 'other-v1.0.0']:
            event.write_text(json.dumps({'action': 'published', 'release': {'tag_name': tag, 'draft': False, 'prerelease': False}}))
            with patch.dict('os.environ', {'GH_TOKEN': 'dummy', 'GITHUB_EVENT_NAME': 'release', 'GITHUB_EVENT_PATH': str(event)}), patch.object(sys, 'argv', ['rolling.py', '--event']), patch.object(rolling, 'GitHub', return_value=self.api), patch.object(rolling, 'build', return_value=[self.item]), patch.object(rolling, 'refresh') as refresh:
                rolling.main()
                refresh.assert_not_called()

    def test_manual_release_event_refreshes_and_commits_without_version_publish_gate(self):
        event = self.output / 'event.json'
        event.write_text(json.dumps({'action': 'published', 'release': {'tag_name': self.item['tag'], 'draft': False, 'prerelease': False}}))
        with patch.dict('os.environ', {'GH_TOKEN': 'dummy', 'GITHUB_EVENT_NAME': 'release', 'GITHUB_EVENT_PATH': str(event)}, clear=True), patch.object(sys, 'argv', ['rolling.py', '--event']), patch.object(rolling, 'GitHub', return_value=self.api), patch.object(rolling, 'build', return_value=[self.item]), patch.object(rolling, 'accepted_commit', return_value=('a' * 40, 'main')), patch.object(rolling, 'refresh', return_value='https://example.org/stable') as refresh, patch.object(rolling, 'confirm_publication') as confirm, patch.object(rolling, 'commit_catalog') as commit:
            rolling.main()
            refresh.assert_called_once()
            confirm.assert_called_once_with('sample')
            commit.assert_called_once_with(self.api, ['sample'], 'main')

    def test_catalog_commit_is_allowlisted_and_never_force_pushes(self):
        calls = []
        api = type('API', (), {'base': 'https://api.github.com/repos/test/repo', 'token': 'dummy'})()
        def git(*args, **kwargs):
            calls.append((args, kwargs))
            return 'README.md' if args == ('diff', '--name-only') else ''
        with patch.object(rolling, 'git', side_effect=git):
            rolling.commit_catalog(api, ['sample'], 'main')
        push = next((args, kwargs) for args, kwargs in calls if args[0] == 'push')
        self.assertEqual(push[0], ('push', 'https://github.com/test/repo.git', 'HEAD:refs/heads/main'))
        self.assertNotIn('dummy', str(push[0]))
        with patch.object(rolling, 'git', return_value='tools/changed.py'), self.assertRaises(ValueError):
            rolling.commit_catalog(api, ['sample'], 'main')


if __name__ == '__main__':
    unittest.main()
