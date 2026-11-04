#!/usr/bin/env python3
"""Lead-authorized two-ref source derivative; no target import/test/Git execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PACKET = Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-current2ee707-route658')
PROPOSED = PACKET / 'proposed'
ROOT = Path('/root/projects/nativeCmpKit')

def read(path):
    before = path.stat(follow_symlinks=False)
    assert path.is_file() and not path.is_symlink() and before.st_nlink == 1 and before.st_size <= 512 * 1024
    raw = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    return raw

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def retain(name, raw):
    path = PACKET / 'retained' / name
    with path.open('xb') as output:
        output.write(raw)
    path.chmod(0o600)

def replace_once(source, before, after):
    assert source.count(before) == 1
    return source.replace(before, after, 1)

workflow_path = PROPOSED / '.github/workflows/javafx-library-candidate.yml'
workflow_before = read(workflow_path)
assert sha(workflow_before) == '23786c9a0ad877416567333ccb5c3d18439edb1a268d94ff9a9d0e8873fad99d'
retain('javafx-library-candidate.before-finite-refs.yml', workflow_before)
source = workflow_before.decode()
old_guard = "    if: github.repository == 'Apdelrahman1911/nativeCmpkit' && github.ref == 'refs/heads/development/preview-hardening' && github.event_name == 'workflow_dispatch' && inputs.platform == 'windows-ordinary-consumer1'\n"
new_guard = "    if: github.repository == 'Apdelrahman1911/nativeCmpkit' && contains(fromJSON('[\"refs/heads/development/preview-hardening\",\"refs/heads/development/javafx-ordinary-consumer1\"]'), github.ref) && github.event_name == 'workflow_dispatch' && inputs.platform == 'windows-ordinary-consumer1'\n"
source = replace_once(source, old_guard, new_guard)
old_new_env = "      CARGO_BUILD_JOBS: '1'\n    steps:\n"
new_new_env = "      CARGO_BUILD_JOBS: '1'\n      NATIVECMPKIT_ORDINARY_PLATFORM: ${{ inputs.platform }}\n    steps:\n"
source = replace_once(source, old_new_env, new_new_env)
workflow_after = source.encode()
workflow_path.write_bytes(workflow_after)

controller_path = PROPOSED / 'scripts/ci/javafx_ordinary_maven_consumer.py'
controller_before = read(controller_path)
assert sha(controller_before) == '6683a79aa07d2f9b291811c5d029a47e2dc729c21df7552e326b3914ae733002'
retain('javafx_ordinary_maven_consumer.before-finite-refs.py', controller_before)
source = controller_before.decode()
source = replace_once(source,
'''Prospective source only: exact current2ee12-source intake plus lead-controlled707
producer/Camera/Android completion is required before adoption/freeze/dispatch.
''',
'''Prospective source only: exact current2ee12-source intake and frozen lead707
producer/native HEAD precede isolated branch source adoption. Required reviewed
producer/Camera/Android completion remains a gate before ordinary native dispatch.
''')
source = replace_once(source, "WORKFLOW = '.github/workflows/javafx-library-candidate.yml'\n", "WORKFLOW = '.github/workflows/javafx-library-candidate.yml'\nMANUAL_REFS = ('refs/heads/development/preview-hardening', 'refs/heads/development/javafx-ordinary-consumer1')\nWINDOWS_FOCUS = 'windows-ordinary-consumer1'\n")
manual = '''def manual_context():
    context = {'repository': os.environ.get('GITHUB_REPOSITORY'), 'event': os.environ.get('GITHUB_EVENT_NAME'),
               'ref': os.environ.get('GITHUB_REF'), 'platform': os.environ.get('NATIVECMPKIT_ORDINARY_PLATFORM')}
    need(context['repository'] == 'Apdelrahman1911/nativeCmpkit' and context['event'] == 'workflow_dispatch' and
         context['ref'] in MANUAL_REFS and context['platform'] == WINDOWS_FOCUS,
         'Only the exact repository/manual ordinary choice on the finite two development refs is admitted')
    return context


'''
source = replace_once(source, 'def write(path, value):\n', manual + 'def write(path, value):\n')
source = replace_once(source, "    try:\n        need(os.name == 'nt' and sys.platform == 'win32',", "    try:\n        record['manual_dispatch'] = manual_context()\n        need(os.name == 'nt' and sys.platform == 'win32',")
controller_after = source.encode()
controller_path.write_bytes(controller_after)

control_path = PROPOSED / 'scripts/ci/test_javafx_ordinary_maven_route.py'
control_before = read(control_path)
retain('test_javafx_ordinary_maven_route.before-finite-refs.py', control_before)
source = control_before.decode()
source = replace_once(source, '        guard = ' + repr(old_guard) + '\n', '        guard = ' + repr(new_guard) + '\n') if ('        guard = ' + repr(old_guard) + '\n') in source else replace_once(source, '        guard = "' + old_guard.replace('"', '\\"').replace('\n', '\\n') + '"\n', '        guard = ' + repr(new_guard) + '\n')
new_tests = '''    def test_exact_two_manual_development_refs_have_positive_source_admission(self):
        expected = ('refs/heads/development/preview-hardening', 'refs/heads/development/javafx-ordinary-consumer1')
        driver_refs = literal(assigned(self.tree, 'MANUAL_REFS'))
        workflow_lists = re.findall(r"contains\\(fromJSON\\('([^']+)'\\), github.ref\\)", self.new_job)
        self.assertEqual(len(workflow_lists), 1)
        workflow_refs = tuple(json.loads(workflow_lists[0]))
        self.assertEqual(driver_refs, expected)
        self.assertEqual(workflow_refs, expected)
        self.assertEqual(literal(assigned(self.tree, 'WINDOWS_FOCUS')), 'windows-ordinary-consumer1')
        self.assertIn('      NATIVECMPKIT_ORDINARY_PLATFORM: ${{ inputs.platform }}\\n', self.new_job)
        predicate = ast.unparse(calls(self.functions['manual_context'], 'need')[0].args[0])
        self.assertEqual(predicate, "context['repository'] == 'Apdelrahman1911/nativeCmpkit' and context['event'] == 'workflow_dispatch' and (context['ref'] in MANUAL_REFS) and (context['platform'] == WINDOWS_FOCUS)")
        for ref in expected:
            with self.subTest(ref=ref):
                self.assertIn(ref, driver_refs)
                self.assertIn(ref, workflow_refs)
        admission = calls(self.functions['run'], 'manual_context')
        self.assertEqual(len(admission), 1)
        self.assertLess(admission[0].lineno, calls(self.functions['run'], 'os.open')[0].lineno)
        self.assertLess(admission[0].lineno, calls(self.functions['run'], 'runtime_context.capture')[0].lineno)

    def test_main_tags_foreign_and_near_match_refs_have_no_source_admission(self):
        driver_refs = literal(assigned(self.tree, 'MANUAL_REFS'))
        workflow_refs = tuple(json.loads(re.findall(r"contains\\(fromJSON\\('([^']+)'\\), github.ref\\)", self.new_job)[0]))
        foreign_refs = ('refs/heads/main', 'refs/heads/development/other', 'refs/heads/development/javafx-ordinary-consumer10',
                        'refs/tags/development/javafx-ordinary-consumer1', 'refs/pull/1/head', 'refs/heads/feature/javafx-ordinary-consumer1',
                        'refs/heads/development/javafx-ordinary-consumer1/', 'refs/heads/development/preview-hardening-extra',
                        'refs/heads/Development/javafx-ordinary-consumer1', 'development/javafx-ordinary-consumer1', '', None)
        for ref in foreign_refs:
            with self.subTest(ref=ref):
                self.assertNotIn(ref, driver_refs)
                self.assertNotIn(ref, workflow_refs)
        predicate = ast.unparse(calls(self.functions['manual_context'], 'need')[0].args[0])
        self.assertIn("context['ref'] in MANUAL_REFS", predicate)
        self.assertNotIn('startswith', predicate)
        self.assertNotIn('endswith', predicate)
        original_job = self.old_prefix[self.old_prefix.index('  public-stop:\\n'):]
        self.assertNotIn('refs/heads/development/javafx-ordinary-consumer1', original_job)
        self.assertNotIn('windows-ordinary-consumer1', original_job)

'''
source = replace_once(source, '    def test_exact_twelve_source_pins_match_authoritative_recipe(self):\n', new_tests + '    def test_exact_twelve_source_pins_match_authoritative_recipe(self):\n')
control_after = source.encode()
control_path.write_bytes(control_after)

doc_path = PROPOSED / 'docs/testing/javafx-ordinary-windows-route.md'
doc_before = read(doc_path)
retain('javafx-ordinary-windows-route.before-finite-refs.md', doc_before)
source = doc_before.decode()
source = replace_once(source,
'''Before adoption, the lead must complete the reviewed producer and same-HEAD
missing Camera/Android cohort, review this separate candidate's NEW controls,
qualify applicable compiler preparation, integrate/freeze/push, and perform a
fresh all-status combined hosted-capacity readback. No source-preparation result
may stand in for those gates or actual Windows native evidence.
''',
'''After the CI707 producer/native cohort HEAD freezes, the lead may integrate,
commit and push this candidate on the isolated
`development/javafx-ordinary-consumer1` branch while the first CI runs, without
changing that frozen cohort HEAD. Before ordinary native dispatch, the reviewed
producer and required same-HEAD missing Camera/Android completion, this separate
candidate's NEW controls, applicable compiler preparation, exact integration/
freeze/push and fresh all-status hosted-capacity readback remain gates. No source
preparation stands in for those gates or actual Windows native evidence.
''')
source = replace_once(source,
'''* The NEW job is guarded by the exact repository, development branch, manual
  event and NEW platform choice. It uses''',
'''* Only the NEW job and driver admit the two exact manual development refs:
  `refs/heads/development/preview-hardening` and
  `refs/heads/development/javafx-ordinary-consumer1`, with the exact repository,
  manual event and NEW platform choice. Main/tags/foreign/near-match refs refuse;
  no wildcard or arbitrary branch is admitted. The old job's original one-ref
  guard remains unchanged. NEW positive and foreign-ref AST/text controls qualify
  only this finite source admission. The NEW job uses''')
source = replace_once(source, 'only the lead controls Git, metadata readback and dispatch.', 'only the lead controls isolated-branch Git, metadata readback and dispatch.')
doc_after = source.encode()
doc_path.write_bytes(doc_after)

base = read(ROOT / '.github/workflows/javafx-library-candidate.yml')
assert sha(base) == '4e3bec6b1ae93414ad1e663d232d2d264ab191908fb9493ff0f787c0278df5e8'
old_options = '        options: [linux-arm64, macos-arm64, macos-x64, windows]\\n'.replace('\\n', '\n')
new_options = '        options: [linux-arm64, macos-arm64, macos-x64, windows, windows-ordinary-consumer1]\\n'.replace('\\n', '\n')
new_job = workflow_after.decode().split('  ordinary-windows-consumer1:\n', 1)[1]
new_job = ('  ordinary-windows-consumer1:\n' + new_job).encode()
assert workflow_after == replace_once(base.decode(), old_options, new_options).encode() + new_job
recipe = {
    'schema': 'nativecmpkit-javafx-registered-file-two-exact-manual-refs658-v1',
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Canonical external derivative after lead two-ref amendment, source-only/not adoption or native/dispatch',
    'destination': '.github/workflows/javafx-library-candidate.yml', 'destination_action': 'Exact-predecessor derivative; lead integration only', 'expected_destination_mode': '0644',
    'preimage': {'sha256': sha(base), 'bytes': len(base), 'retained_path': 'retained/javafx-library-candidate.preimage.yml'},
    'postimage': {'sha256': sha(workflow_after), 'bytes': len(workflow_after), 'source_path': str(workflow_path)},
    'fragments': [{'kind': 'replace-exact-once', 'preimage': old_options, 'postimage': new_options}, {'kind': 'append-at-exact-predecessor-EOF', 'preimage': '', 'postimage': new_job.decode()}],
    'new_job_sha256': sha(new_job),
    'finite_manual_refs': ['refs/heads/development/preview-hardening', 'refs/heads/development/javafx-ordinary-consumer1'],
    'old_public_stop_job_sha256': 'b52eb257b7c5dc8cc65152c901303afa613a90a78e4c07a3e54a3cd5bd716675',
    'old_public_stop_job_whitelist_push_permissions_concurrency_and_all_other_old_bytes_unchanged': True,
    'registered_existing_workflow_observation': {'source_path': '/root/nativecmpkit-source-proposals-20261104/lead-workflow-registration-20261104/WORKFLOW-REGISTRATION.json', 'sha256': '6bd756c3fc5491bd9544470bc31336f05ac50d0fd5436ee46bbf8ccfbf94a020', 'workflow_id': 404301928, 'state': 'active', 'name': 'NativeCmpKit Windows JavaFX library candidate', 'returned_active_workflows': 4, 'reused_not_reacquired': True},
    'new_finite_input_job_adopted_or_dispatch_HEAD_verified': False,
    'earlier_registered_derivative_postimage_retained_path': 'retained/javafx-library-candidate.before-finite-refs.yml',
    'controller': {'before_sha256': sha(controller_before), 'after_sha256': sha(controller_after), 'bytes': len(controller_after)},
    'source_controls': {'before_sha256': sha(control_before), 'after_sha256': sha(control_after), 'bytes': len(control_after), 'NEW_methods': 10, 'executions_yet': 0},
    'doc': {'before_sha256': sha(doc_before), 'after_sha256': sha(doc_after), 'bytes': len(doc_after)},
    'isolated_lead_source_branch_may_follow_frozen_CI707_HEAD_without_mutating_cohort_HEAD': True,
    'ROOT_writes': 0, 'Git_queries': 0, 'target_imports': 0, 'build_native_or_dispatch_executions': 0,
}
with (PACKET / 'REGISTERED-WORKFLOW-TWO-REF-DERIVATIVE658.json').open('x', encoding='utf-8') as output:
    json.dump(recipe, output, indent=2, sort_keys=True)
    output.write('\n')
for path in (workflow_path, controller_path, control_path, doc_path, PACKET / 'REGISTERED-WORKFLOW-TWO-REF-DERIVATIVE658.json'):
    path.chmod(0o600)
print(json.dumps({'workflow_postimage': recipe['postimage'], 'controller': recipe['controller'], 'source_controls': recipe['source_controls'], 'doc': recipe['doc']}, sort_keys=True))
