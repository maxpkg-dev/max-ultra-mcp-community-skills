import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import stat
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import Request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import catalog
import release
import validate as v

MINIMAL = {'SKILL.md': b'---\nname: sample\ndescription: A useful sample\n---\n# Sample\n'}


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def archive(self, entries, compression=zipfile.ZIP_STORED):
        target = self.root / 'input.zip'
        with zipfile.ZipFile(target, 'w', compression=compression) as z:
            for name, data in entries:
                z.writestr(name, data)
        return target

    def test_minimal_and_quoted_frontmatter(self):
        self.assertEqual(v.validate_files(MINIMAL)['name'], 'sample')
        data = b'\xef\xbb\xbf---\r\nname: "sample"\r\ndescription: \'Author: a \'\'sample\'\'\'\r\n---\r\nBody'
        self.assertEqual(v.frontmatter(data)['description'], "Author: a 'sample'")

    def test_frontmatter_rejects_extra_duplicate_multiline_and_invalid_name(self):
        for header in ['name: sample\ndescription: Test\nlicense: MIT', 'name: sample\nname: sample\ndescription: Test', 'name: Sample\ndescription: Test', 'name: sample\ndescription: |\n  Text', 'name: sample\ndescription: {bad}', 'name: sample\ndescription: "bad\\ntext"']:
            with self.subTest(header=header), self.assertRaises(ValueError):
                v.frontmatter(('---\n' + header + '\n---\nBody').encode())

    def test_unsupported_files_and_private_paths(self):
        for name in ['README.md', 'script.py', 'references/script.js', 'references/backup.zip', 'assets/readme.md', 'references/SKILL.md']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                v.validate_files({**MINIMAL, name: b'example'})
        for value in [b'C:\\Users\\Person\\secret', b'/home/person/project']:
            with self.assertRaises(ValueError):
                v.validate_files({**MINIMAL, 'references/note.txt': value})

    def test_paths_and_case_collisions(self):
        for name in ['../escape', '/absolute', 'C:/path', 'a\\b', 'references/nul.txt', 'references/a.', 'references/a /b', 'references//a', 'references/a\x00']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                v.safe_path(name)
        for additions in [{'references/A.md': b'', 'references/a.md': b''}, {'references/X/a.md': b'', 'references/x/b.md': b''}]:
            with self.assertRaises(ValueError):
                v.validate_files({**MINIMAL, **additions})

    def test_link_resolution_and_preprocessing(self):
        files = {**MINIMAL, 'references/note.md': b'[entry](../SKILL.md#sample)\n[space](a%20b.txt)\n[web](https://example.org)\n[anchor](#ok)', 'references/a b.txt': b'OK'}
        v.validate_files(files)
        for link in ['../../outside.md', '%2e%2e/%2e%2e/outside.md', '/outside', 'file:///secret', 'missing.md', 'bad%zz']:
            with self.subTest(link=link), self.assertRaises(ValueError):
                v.validate_files({**MINIMAL, 'references/note.md': f'[link]({link})'.encode()})
        for text in [b'!`command`', b'@../../private']:
            with self.assertRaises(ValueError):
                v.validate_files({**MINIMAL, 'references/note.md': text})
        with self.assertRaises(ValueError):
            v.validate_files({**MINIMAL, 'references/note.md': b'[ref]: missing.md'})

    def test_utf8_and_size_limits(self):
        for name, data in [('references/a.txt', b'\xff'), ('SKILL.md', b'x' * (65536 + 1)), ('references/a.txt', b'x' * (v.MIB + 1)), ('assets/a.png', b'x' * (5 * v.MIB + 1))]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                v.validate_files({**MINIMAL, name: data})
        with self.assertRaises(ValueError):
            v.validate_files({**MINIMAL, **{f'references/{i}.txt': b'' for i in range(200)}})
        with patch.object(v, 'MAX_TOTAL', 1), self.assertRaises(ValueError):
            v.validate_files(MINIMAL)

    def test_zip_root_wrapper_and_deflate(self):
        for prefix in ['', 'enclosing/']:
            for method in [0, 8]:
                self.assertEqual(v.read_zip(self.archive([(prefix + k, b) for k, b in MINIMAL.items()], method)), MINIMAL)

    def test_malicious_zip_paths_roots_and_collisions(self):
        bad = [('../escape.md', b''), ('second/SKILL.md', b''), ('extra.txt', b''), ('references/A.md', b''), ('assets/readme.md', b'')]
        for entry in bad:
            base = list(MINIMAL.items()) + [('references/a.md', b'')]
            with self.subTest(entry=entry[0]), self.assertRaises(ValueError):
                v.read_zip(self.archive(base + [entry]))
        with self.assertRaises(ValueError):
            v.read_zip(self.archive([('a/b/SKILL.md', MINIMAL['SKILL.md'])]))
        with self.assertRaises(ValueError):
            v.read_zip(self.archive([('a/SKILL.md', MINIMAL['SKILL.md']), ('outside/', b'')]))
        with self.assertRaises(ValueError):
            v.read_zip(self.archive(list(MINIMAL.items()) + [('unknown/', b'')]))

    def test_zip_symlink_and_unsupported_compression(self):
        link = zipfile.ZipInfo('references/link.md')
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(ValueError):
            v.read_zip(self.archive(list(MINIMAL.items()) + [(link, b'outside')]))
        with self.assertRaises(ValueError):
            v.read_zip(self.archive(list(MINIMAL.items()), zipfile.ZIP_BZIP2))

    def test_corrupt_crc_and_local_name(self):
        archive = self.archive(list(MINIMAL.items()))
        raw = bytearray(archive.read_bytes())
        raw[30 + len('SKILL.md')] ^= 1
        archive.write_bytes(raw)
        with self.assertRaises((ValueError, zipfile.BadZipFile)):
            v.read_zip(archive)
        archive = self.archive(list(MINIMAL.items()))
        raw = bytearray(archive.read_bytes())
        raw[30] = ord('X')
        archive.write_bytes(raw)
        with self.assertRaises(ValueError):
            v.read_zip(archive)

    def test_zip_limits_and_zip64(self):
        archive = self.archive(list(MINIMAL.items()))
        with patch.object(v, 'MAX_ZIP', 1), self.assertRaises(ValueError):
            v.read_zip(archive)
        raw = bytearray(archive.read_bytes())
        central = raw.index(b'PK\x01\x02')
        struct.pack_into('<I', raw, central + 24, v.MAX_TOTAL + 1)
        archive.write_bytes(raw)
        with self.assertRaises(ValueError):
            v.read_zip(archive)
        entry = zipfile.ZipInfo('SKILL.md')
        entry.extra = struct.pack('<HHQ', 1, 8, 0)
        with self.assertRaises(ValueError):
            v.read_zip(self.archive([(entry, MINIMAL['SKILL.md'])]))

    def test_folder_rejects_symlink_when_supported(self):
        package = self.root / 'package'
        package.mkdir()
        (package / 'SKILL.md').write_bytes(MINIMAL['SKILL.md'])
        (package / 'references').mkdir()
        try:
            (package / 'references' / 'link.md').symlink_to(package / 'SKILL.md')
        except OSError:
            self.skipTest('OS account cannot create symlinks; ZIP symlink test still runs')
        with self.assertRaises(ValueError):
            v.read_folder(package)

    def test_deterministic_packaging_and_staging(self):
        files = {**MINIMAL, 'references/a.txt': b'unchanged\r\n'}
        data = v.package_bytes(files)
        self.assertEqual(data, v.package_bytes(dict(reversed(list(files.items())))))
        archive = self.root / 'input.zip'
        archive.write_bytes(data)
        self.assertEqual(v.read_zip(archive), files)
        target = self.root / 'staged'
        self.assertEqual(catalog.stage(archive, target), v.fingerprint(files))
        self.assertEqual(v.read_folder(target), files)
        with self.assertRaises(ValueError):
            catalog.stage(archive, target)
        invalid = self.archive(list(files.items()) + [('script.py', b'')])
        with self.assertRaises(ValueError):
            catalog.stage(invalid, self.root / 'invalid')
        self.assertFalse((self.root / 'invalid').exists())


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(catalog.ROOT / 'skills', self.root / 'skills')
        shutil.copyfile(catalog.ROOT / 'README.md', self.root / 'README.md')
        catalog.generate(self.root)

    def test_catalog_is_current_and_preserves_surrounding_readme(self):
        catalog.generate(self.root, check=True)
        path = self.root / 'README.md'
        path.write_text(path.read_text(encoding='utf-8') + '\nMaintainer note.\n', encoding='utf-8')
        catalog.generate(self.root)
        self.assertTrue(path.read_text(encoding='utf-8').endswith('Maintainer note.\n'))

    def test_metadata_drift_unknown_fields_and_fingerprint(self):
        path = next((self.root / 'skills').glob('*/metadata.json'))
        original = json.loads(path.read_text())
        for change in [{'unknown': True}, {'id': '../bad'}, {'version': '01.0.0'}, {'packageSha256': 'wrong'}, {'verification': {'level': 'practically-tested', 'evidence': 'Untested'}}, {'author': {'name': 'Author', 'profile': 'javascript:alert(1)'}}]:
            path.write_text(json.dumps({**original, **change}), encoding='utf-8')
            with self.subTest(change=change), self.assertRaises(ValueError):
                catalog.load(self.root)
        path.write_text(json.dumps({**original, 'purpose': 'New purpose'}), encoding='utf-8')
        with self.assertRaises(ValueError):
            catalog.generate(self.root, check=True)
        catalog.generate(self.root)
        catalog.generate(self.root, check=True)

    def test_catalog_escapes_untrusted_text(self):
        value = catalog.escape('<script>|[fake](bad)')
        self.assertNotIn('<script>', value)
        self.assertIn('\\|', value)
        self.assertIn('\\[', value)

    def test_build_excludes_metadata_and_is_repeatable(self):
        first = catalog.build(self.root)
        data = (self.root / 'dist' / first[0]['asset']).read_bytes()
        second = catalog.build(self.root)
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(data).hexdigest(), first[0]['sha256'])
        files = v.read_zip(self.root / 'dist' / first[0]['asset'])
        self.assertEqual(len(files), 84)
        self.assertNotIn('metadata.json', files)
        self.assertNotIn('README.md', files)


class FakeAPI:
    def __init__(self, release=None, remote=None):
        self.release, self.remote, self.calls = release, remote or {}, []

    def find(self, tag):
        return self.release

    def check_new_tag(self, tag, commit):
        pass

    def request(self, method, path, body=None, binary=False):
        self.calls.append((method, path, body))
        if method == 'GET':
            return self.remote[path]
        if method == 'POST' and path == '/releases':
            return {'id': 1, 'draft': True, 'assets': [], 'upload_url': 'https://uploads.github.com/repos/test/repo/releases/1/assets{?name,label}'}
        return {}


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.item = {'id': 'sample', 'version': '1.0.0', 'title': 'Sample', 'tag': 'sample-v1.0.0', 'asset': 'sample-1.0.0-max-ultra-mcp.zip', 'sha256': hashlib.sha256(b'zip').hexdigest()}
        (self.output / self.item['asset']).write_bytes(b'zip')
        (self.output / (self.item['asset'] + '.sha256')).write_bytes(b'checksum')

    def test_new_release_is_draft_until_all_assets_uploaded(self):
        api = FakeAPI()
        release.publish(api, self.item, 'a' * 40, self.output)
        self.assertTrue(api.calls[0][2]['draft'])
        self.assertEqual([c[0] for c in api.calls], ['POST', 'POST', 'POST', 'PATCH'])
        self.assertFalse(api.calls[-1][2]['draft'])

    def test_existing_release_is_immutable_and_idempotent(self):
        existing = {'id': 1, 'draft': False, 'assets': [{'name': self.item['asset'], 'id': 2}, {'name': self.item['asset'] + '.sha256', 'id': 3}]}
        api = FakeAPI(existing, {'/releases/assets/2': b'zip', '/releases/assets/3': b'checksum'})
        release.publish(api, self.item, 'b' * 40, self.output)
        self.assertTrue(all(c[0] == 'GET' for c in api.calls))
        api.remote['/releases/assets/2'] = b'changed'
        with self.assertRaises(ValueError):
            release.publish(api, self.item, 'b' * 40, self.output)

    def test_incomplete_public_release_cannot_be_mutated(self):
        api = FakeAPI({'id': 1, 'draft': False, 'assets': []})
        with self.assertRaises(ValueError):
            release.publish(api, self.item, 'b' * 40, self.output)
        self.assertEqual(api.calls, [])

    def test_partial_draft_resumes_without_replacing_existing_asset(self):
        existing = {'id': 1, 'draft': True, 'assets': [{'name': self.item['asset'], 'id': 2}], 'upload_url': 'https://uploads.github.com/repos/test/repo/releases/1/assets{?name,label}'}
        api = FakeAPI(existing, {'/releases/assets/2': b'zip'})
        release.publish(api, self.item, 'b' * 40, self.output)
        self.assertEqual([c[0] for c in api.calls], ['GET', 'POST', 'PATCH'])

    def test_new_release_rejects_conflicting_tag(self):
        api = release.GitHub('test/repo', 'dummy')
        with patch.object(api, 'request', return_value={'object': {'type': 'commit', 'sha': 'b' * 40}}):
            with self.assertRaises(ValueError):
                api.check_new_tag('sample-v1.0.0', 'a' * 40)

    def test_asset_redirect_does_not_forward_credentials_cross_host(self):
        request = Request('https://api.github.com/repos/test/repo/releases/assets/1', headers={'Authorization': 'Bearer dummy'})
        redirect = release.AssetRedirect().redirect_request(request, None, 302, 'Found', {}, 'https://release-assets.githubusercontent.com/asset')
        self.assertIsNone(redirect.get_header('Authorization'))
        with self.assertRaises(ValueError):
            release.AssetRedirect().redirect_request(request, None, 302, 'Found', {}, 'http://example.org')

    def test_publisher_refuses_local_execution(self):
        with patch.dict('os.environ', {}, clear=True), self.assertRaises(ValueError):
            release.main()

    def test_publisher_refuses_pr_and_nondefault_refs(self):
        event = self.output / 'event.json'
        event.write_text(json.dumps({'repository': {'default_branch': 'main'}}))
        for trigger, ref in [('pull_request', 'refs/heads/main'), ('workflow_dispatch', 'refs/heads/feature')]:
            env = {'GITHUB_ACTIONS': 'true', 'GITHUB_EVENT_PATH': str(event), 'GITHUB_EVENT_NAME': trigger, 'GITHUB_REF': ref}
            with patch.dict('os.environ', env, clear=True), self.assertRaises(ValueError):
                release.main()


if __name__ == '__main__':
    unittest.main()
