"""Parse real YAML and assert the workflow/form security contract, offline."""
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read_yaml(path):
    # BaseLoader retains 'on' as a key instead of YAML 1.1's boolean conversion.
    return yaml.load(path.read_text(encoding='utf-8'), Loader=yaml.BaseLoader)


class AutomationTests(unittest.TestCase):
    def test_workflows_are_pinned_and_have_no_untrusted_publication_trigger(self):
        workflows = {p.stem: read_yaml(p) for p in (ROOT / '.github/workflows').glob('*.yml')}
        self.assertEqual(set(workflows), {'validate', 'release', 'download'})
        for name, data in workflows.items():
            self.assertEqual(data['permissions'], {'contents': 'read'})
            self.assertFalse({'issues', 'issue_comment', 'pull_request_target', 'workflow_run'} & set(data['on']))
            for job in data['jobs'].values():
                self.assertEqual(job['runs-on'], 'ubuntu-24.04')
                self.assertLessEqual(int(job['timeout-minutes']), 15)
                for step in job['steps']:
                    if 'uses' in step:
                        self.assertRegex(step['uses'], r'^[\w/-]+@[a-f0-9]{40}$')
                    if step.get('uses', '').startswith('actions/checkout@'):
                        self.assertEqual(step['with']['persist-credentials'], 'false')
                    if 'run' in step:
                        self.assertNotIn('${{', step['run'])
        validation = workflows['validate']['jobs']['validate']
        self.assertNotIn('permissions', validation)
        publication = workflows['release']['jobs']['release']
        self.assertEqual(publication['environment'], 'skill-releases')
        self.assertEqual(publication['permissions'], {'contents': 'write'})
        self.assertIn("vars.ENABLE_SKILL_RELEASES == 'true'", publication['if'])
        self.assertIn('github.event.repository.default_branch', publication['if'])
        self.assertEqual(set(workflows['release']['on']), {'push', 'workflow_dispatch'})
        self.assertEqual(workflows['release']['concurrency']['cancel-in-progress'], 'false')
        token_steps = [step for step in publication['steps'] if 'GH_TOKEN' in step.get('env', {})]
        self.assertEqual(len(token_steps), 1)
        self.assertEqual(token_steps[0]['run'], 'python3 tools/release.py')
        refresh = workflows['download']
        self.assertEqual(refresh['on']['release'], {'types': ['published']})
        self.assertEqual(set(refresh['on']), {'release', 'workflow_dispatch'})
        self.assertEqual(refresh['on']['workflow_dispatch']['inputs']['skill']['type'], 'string')
        self.assertEqual(refresh['concurrency']['group'], workflows['release']['concurrency']['group'])
        job = refresh['jobs']['refresh']
        self.assertEqual(job['permissions'], {'contents': 'write'})
        self.assertIn("!endsWith(github.event.release.tag_name, '-latest')", job['if'])
        self.assertEqual(job['steps'][0]['with']['ref'], '${{ github.event.repository.default_branch }}')
        self.assertEqual(job['steps'][-1]['run'], 'python tools/rolling.py --event')

    def test_issue_form_uses_documented_fields(self):
        data = read_yaml(ROOT / '.github/ISSUE_TEMPLATE/submit-skill.yml')
        self.assertEqual(set(data), {'name', 'description', 'title', 'body'})
        allowed = {
            'markdown': {'value'},
            'input': {'label', 'description', 'placeholder', 'value'},
            'textarea': {'label', 'description', 'placeholder', 'value', 'render'},
            'dropdown': {'label', 'description', 'multiple', 'options', 'default'},
            'checkboxes': {'label', 'description', 'options'},
            'upload': {'label', 'description'},
        }
        ids = set()
        for field in data['body']:
            self.assertIn(field['type'], allowed)
            self.assertFalse(set(field) - {'type', 'id', 'attributes', 'validations'})
            self.assertTrue(set(field['attributes']) <= allowed[field['type']])
            if field['type'] != 'markdown':
                self.assertRegex(field['id'], r'^[A-Za-z0-9_-]+$')
                self.assertNotIn(field['id'], ids)
                ids.add(field['id'])
                self.assertIn('label', field['attributes'])
            validations = field.get('validations', {})
            self.assertTrue(set(validations) <= ({'required', 'accept'} if field['type'] == 'upload' else {'required'}))
            if 'required' in validations:
                self.assertIn(validations['required'], ('true', 'false'))
        self.assertTrue({'author', 'terms', 'provenance', 'evidence', 'dependencies', 'package', 'package-link'} <= ids)
        upload = next(f for f in data['body'] if f['type'] == 'upload')
        self.assertEqual(upload['validations'], {'required': 'false', 'accept': '.zip'})
        self.assertIn('blank_issues_enabled', read_yaml(ROOT / '.github/ISSUE_TEMPLATE/config.yml'))


if __name__ == '__main__':
    unittest.main()
