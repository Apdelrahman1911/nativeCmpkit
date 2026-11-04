"""Passive source/AST/receipt custody review; no test or model execution."""
import ast
from collections import Counter
import datetime
import difflib
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
from unittest.mock import patch

ROOT = Path('/root/projects/nativecmpkit-worktrees/image-launch-readiness')
OUT = Path('/root/nativecmpkit-source-proposals-20261104/image-launch-ingress624')
BASE = '7d6b6d5b43f93ae085dc66a3377b3c7967400bf7'
HEAD = 'ddf19b1545eb05c46c7e69c087d216b03face61a'
IMAGE = 'b013cbd04997a229ee8796fca34b53d3bffab6f9'
HELPER = 'scripts/ci/apple_image_launcher_source_projection.py'
NEW_CONTROL = 'scripts/ci/test_apple_image_launcher_source_projection.py'
SELECTOR = 'scripts/ci/calendar_share_selector_source_projection.py'
CONTROL = 'scripts/ci/test_calendar_share_selector_source_projection.py'
LAUNCHER = 'scripts/ci/ios_ui_application.py'
SPEC = 'scripts/ci/fixtures/apple-image-launcher-source-inverse.json'
checks = []
git_queries = 0


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(files):
    return sha(''.join(f'{value}  {name}\n' for name, value in sorted(files.items())).encode())


def check(name, condition, detail=None):
    checks.append({'name': name, 'passed': bool(condition), 'detail': detail})
    if not condition:
        raise AssertionError(name)


def read(name):
    return (ROOT / name).read_bytes()


def record(name):
    return json.loads((OUT / name).read_bytes())


def git(*args, data=None):
    global git_queries
    git_queries += 1
    return subprocess.run(['git', *args], cwd=ROOT, input=data, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout


def assignment(raw, name):
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError('Missing literal assignment: ' + name)


def invert(raw, row):
    check('complete-after-hash-' + row['after_sha256'][:10], sha(raw) == row['after_sha256'])
    restored = raw
    for fragment in reversed(row['fragments']):
        before, after = fragment['before'].encode(), fragment['after'].encode()
        assert sha(before) == fragment['before_fragment_sha256']
        assert sha(after) == fragment['after_fragment_sha256']
        assert restored.count(after) == 1
        restored = restored.replace(after, before, 1)
    assert sha(restored) == row['before_sha256']
    forward = restored
    for fragment in row['fragments']:
        before, after = fragment['before'].encode(), fragment['after'].encode()
        assert forward.count(before) == 1
        forward = forward.replace(before, after, 1)
    assert forward == raw
    return restored


def class_methods(raw, class_name):
    cls = next(node for node in ast.parse(raw).body if isinstance(node, ast.ClassDef) and node.name == class_name)
    return {node.name: ast.dump(node, include_attributes=False) for node in cls.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}


def run():
    preserved = record('PASSIVE-REVIEW-FIRST-REFUSAL.json')
    reused = [row for row in preserved['checks'] if row['passed']]
    assert len(reused) == 21 and len(preserved['checks']) == 22
    assert preserved['checks'][-1]['name'] == 'image609-fragment-copied-exactly-and-original-source-hashes-held'
    checks.extend(dict(row, reused_from='PASSIVE-REVIEW-FIRST-REFUSAL.json') for row in reused)
    plan, approval = record('PLAN-REVISED.json'), record('PLAN-APPROVED.json')
    first, recovery, recovery_plan = record('IMPORTANT-FIRST.json'), record('IMPORTANT-RECOVERY1.json'), record('RECOVERY-PLAN.json')
    maps = {name: record(name) for name in ('BASE-INPUTS-7D6B.json', 'CHERRY-INPUTS-BEFORE-INGRESS.json',
            'INPUTS-FIRST-BEFORE.json', 'INPUTS-FIRST-AFTER.json',
            'INPUTS-RECOVERY1-BEFORE.json', 'INPUTS-RECOVERY1-AFTER.json')}
    first_files = maps['INPUTS-FIRST-BEFORE.json']['files']
    final_files = maps['INPUTS-RECOVERY1-BEFORE.json']['files']
    manifest_raw = read(SPEC)
    manifest = json.loads(manifest_raw)
    restored = {name: git('show', BASE + ':' + name) for name in manifest['bindings']}
    image_fragment = json.loads(git('show', IMAGE + ':docs/development/evidence/current-platform-recovery-20261101/'
                              'image-launch-readiness609/FRAGMENT609.json'))['bindings'][LAUNCHER]
    check('image609-four-fragment-fields-exact-new-id-metadata-only-original-source-hashes-held',
          [{key: value for key, value in fragment.items() if key != 'id'}
           for fragment in manifest['bindings'][LAUNCHER]['fragments']] == image_fragment['fragments'] and
          manifest['bindings'][LAUNCHER]['fragments'][0]['id'] == 'unchanged-image609-ten-line-hook' and
          all(read(name) == git('show', IMAGE + ':' + name) for name in [LAUNCHER, *manifest['added_inputs']]))
    check('original-image609-evidence-bytes-unchanged', not git('diff', '--name-only', IMAGE, HEAD, '--',
          'docs/development/evidence/current-platform-recovery-20261101/image-launch-readiness609').strip())
    launcher = restored[LAUNCHER]
    ancestors = [launcher]
    for spec in ('ios-popover-geometry-source-inverse.json', 'ios-worker-completion-source-inverse.json',
                 'ios-modal-xcui-source-inverse.json'):
        launcher = invert(launcher, json.loads(read('scripts/ci/fixtures/' + spec))['bindings'][LAUNCHER])
        ancestors.append(launcher)
    row = assignment(read('scripts/ci/test_ui_alert_important_recovery.py'), 'SHARE_ALERT153_REBASE')[LAUNCHER]
    launcher = invert(launcher, {'after_sha256': row['share_composed_sha256'],
                                'before_sha256': row['original153_sha256'], 'fragments': row['fragments']})
    ancestors.append(launcher)
    check('exact-five-already-pinned-launcher-ancestors-no-arbitrary-Git-fallback',
          assignment(read(HELPER), 'PINNED_LAUNCHER_ANCESTORS') == {sha(raw) for raw in ancestors})
    helper = read(HELPER)
    old_text = b'Unknown image-launch bytes are not a fixed pinned ancestor'
    new_text = b'Unknown image-launch bytes cannot satisfy exact current source or a fixed pinned ancestor'
    assert helper.count(new_text) == 1
    helper_first = helper.replace(new_text, old_text, 1)
    check('recovery-helper-diff-is-one-refusal-string-only', sha(helper_first) == first_files[HELPER])
    new_control = read(NEW_CONTROL)
    old_pin, new_pin = first_files[HELPER].encode(), final_files[HELPER].encode()
    stronger = b'with self.assertRaisesRegex(ValueError, "exact current source or a fixed pinned ancestor"):'
    ordinary = b'with self.assertRaises(ValueError):'
    assert new_control.count(new_pin) == new_control.count(stronger) == 1
    control_first = new_control.replace(new_pin, old_pin, 1).replace(stronger, ordinary, 1)
    check('recovery-control-diff-is-only-owning-helper-pin-and-one-strengthened-assertion',
          sha(control_first) == first_files[NEW_CONTROL] and
          assignment(new_control, 'HELPER_SHA256') == final_files[HELPER])
    changed_methods = {name.rsplit('.', 1)[1] for name in recovery_plan['changed_owning_new_methods']}
    first_methods = class_methods(control_first, 'ImageLauncherSourceProjectionControls')
    final_methods = class_methods(new_control, 'ImageLauncherSourceProjectionControls')
    check('all-ten-unaffected-new-method-ASTs-unchanged-after-recovery',
          len(first_methods) == len(final_methods) == 12 and set(first_methods) == set(final_methods) and
          all(first_methods[name] == final_methods[name] for name in final_methods if name not in changed_methods))
    class OnlyQualifiedOperand(ast.NodeTransformer):
        def visit_Call(self, node):
            node = self.generic_visit(node)
            if ast.unparse(node.func) == 'image_history.current_source_before_image_launch':
                assert len(node.args) == 2 and not node.keywords and ast.unparse(node.args[0]) == 'LAYER'
                return node.args[1]
            return node
    def original_obligations(raw):
        tree = OnlyQualifiedOperand().visit(ast.parse(raw))
        methods = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
        assertions = [ast.dump(node, include_attributes=False) for node in ast.walk(tree)
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                      ast.unparse(node.func.value) == 'self' and node.func.attr.startswith('assert')]
        return methods, assertions
    obligations = original_obligations(restored[CONTROL])
    check('every-original-calendar-control-method-and-assertion-retained',
          obligations == original_obligations(read(CONTROL)) and
          assignment(read(CONTROL), 'LAYER_SHA256') == sha(restored[SELECTOR]),
          {'original_methods': len(obligations[0]), 'original_assertions': len(obligations[1])})
    def original_launcher_obligations(raw):
        tree = ast.parse(raw)
        final = [ast.dump(ast.Module(body=node.finalbody, type_ignores=[]), include_attributes=False)
                 for node in ast.walk(tree) if isinstance(node, ast.Try) and node.finalbody]
        launch = [ast.dump(node, include_attributes=False) for node in ast.walk(tree)
                  if isinstance(node, ast.Call) and ast.unparse(node.func) == 'forward_application']
        timeout = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'application_timeout_seconds')
        assert 'return 360' in ast.unparse(timeout)
        return final, launch, ast.dump(timeout, include_attributes=False)
    check('original-all-finally-launch-argv-and360second-focus-deadline-AST-retained',
          original_launcher_obligations(restored[LAUNCHER]) == original_launcher_obligations(read(LAUNCHER)))
    calls = [node for node in ast.walk(ast.parse(helper)) if isinstance(node, ast.Call)]
    forbidden = {'eval', 'exec', 'compile', '__import__', 'run', 'Popen', 'control', 'observe', 'write_bytes', 'write_text'}
    check('new-helper-never-executes-reconstructed-source-model-observer-or-process',
          not any((isinstance(node.func, ast.Name) and node.func.id in forbidden) or
                  (isinstance(node.func, ast.Attribute) and node.func.attr in forbidden) for node in calls))
    check('new-confined-path-wrapper-delegates-one-unchanged-bridge-call',
          sum(ast.unparse(node.func) == 'bridge.current_source_for_history' for node in calls) == 1 and
          HELPER not in manifest['added_inputs'] and NEW_CONTROL not in manifest['added_inputs'] and
          HELPER not in manifest['unchanged_inputs'] and NEW_CONTROL not in manifest['unchanged_inputs'])
    all_names = plan['new_controls_proposed'] + plan['affected_old_methods_proposed']
    check('first-exact20-selection-and-recorded19pass-one-regex-failure', first['planned_names'] ==
          first['actual_names'] == all_names and len(set(all_names)) == first['methods_executed'] == 20 and
          first['counts'] == {'passed': 19, 'failures': 1, 'errors': 0, 'skipped': 0} and
          [event['name'] for event in first['events']] == all_names and
          Counter(event['status'] for event in first['events']) == {'passed': 19, 'failed': 1})
    failed = [event['name'] for event in first['events'] if event['status'] == 'failed']
    check('first-real-failure-is-retained-old-exact-current-regex-not-admission',
          failed == recovery_plan['failed_methods'] and len(first['failure_records']) == 1 and
          '"exact current" does not match' in first['failure_records'][0]['traceback'] and
          'ValueError: Unknown image-launch bytes are not a fixed pinned ancestor' in first['failure_records'][0]['traceback'])
    check('recovery-exact-failed1-and-changed-owning-new2-only', recovery['planned_names'] ==
          recovery['actual_names'] == recovery_plan['only_selected_methods'] ==
          recovery_plan['failed_methods'] + recovery_plan['changed_owning_new_methods'] and
          recovery['methods_executed'] == 3 and recovery['counts'] ==
          {'passed': 3, 'failures': 0, 'errors': 0, 'skipped': 0} and
          all(event['status'] == 'passed' for event in recovery['events']))
    accepted = {}
    for receipt_name, report in [('IMPORTANT-FIRST.json', first), ('IMPORTANT-RECOVERY1.json', recovery)]:
        for event in report['events']:
            if event['status'] == 'passed':
                accepted[event['name']] = {'receipt': receipt_name, 'status': event['status'],
                                           'elapsed_seconds': event['elapsed_seconds']}
    check('twenty-unique-qualified-obligations-over23-invocations-with17unchanged-results-reused',
          set(accepted) == set(all_names) and len(accepted) == 20 and
          sum(value['receipt'] == 'IMPORTANT-FIRST.json' for value in accepted.values()) == 17)
    check('zero-recorded-subprocess-compiler-SDK-native-profile-and-accepted-image609-replay',
          all(report['unexpected_subprocess_attempts'] == report['native_SDK_compiler_profile_executions'] == 0 and
              report['accepted_image_NEW18_replayed'] is False for report in (first, recovery)) and
          not any('test_apple_image_launch_readiness.' in name for name in all_names) and
          manifest['native_tests_executed'] == 0 and manifest['issue141_closed'] is False)
    diff = git('diff', '--check')
    check('source-whitespace-check', not diff)
    (OUT / 'RECOVERY-EXACT-DIFF.patch').write_text(''.join(
          ''.join(difflib.unified_diff(previous.decode().splitlines(True), current.decode().splitlines(True),
              fromfile=name + '.first-tested', tofile=name + '.recovery-tested'))
          for name, previous, current in [(HELPER, helper_first, helper), (NEW_CONTROL, control_first, new_control)]))
    artifacts = {p.name: {'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size}
                 for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in {'PASSIVE-REVIEW-RECOVERY1.json'}}
    return {'schema_version': 1, 'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'reviewer': '/root/calendar_independent609',
            'scope': 'Passive source/AST/Git-blob/recorded-result custody only. No important-control, observer, model, compiler, SDK, native or profile replay.',
            'head_before_ingress_overlay': HEAD, 'base_revision': BASE, 'original_image_commit_reused': IMAGE,
            'passed_checks': len(checks), 'reused_first_passive_checks': 21,
            'new_or_failed_only_passive_checks': len(checks) - 21,
            'first_passive_review_refusal_sha256': sha((OUT / 'PASSIVE-REVIEW-FIRST-REFUSAL.json').read_bytes()),
            'checks': checks, 'source_inputs_sha256':
            {name: final_files[name] for name in [HELPER, NEW_CONTROL, SELECTOR, CONTROL, SPEC, LAUNCHER]},
            'input_maps': {name: {'count': len(row['files']), 'input_digest': row['input_digest'],
                                'sha256': sha((OUT / name).read_bytes())} for name, row in maps.items()},
            'actual_final_input_count': len(final_files), 'actual_final_input_digest': digest(final_files),
            'important_execution': {'first_counts': first['counts'], 'first_elapsed_seconds': first['elapsed_seconds'],
             'recovery_counts': recovery['counts'], 'recovery_elapsed_seconds': recovery['elapsed_seconds'],
             'unique_obligations': 20, 'invocations': 23, 'unchanged_first_passes_reused': 17,
             'accepted_obligations': accepted, 'subprocess_attempts': 0, 'compiler_SDK_native_profile_executions': 0,
             'accepted_image609_NEW18_replayed': False},
            'passive_activity': {'local_readonly_git_queries': git_queries, 'passive_source_inventory_processes': 0,
             'control_model_observer_executions': 0, 'compiler_SDK_native_profile_executions': 0,
             'network_GitHub_dispatch_publication_mutations': 0, 'source_edits': 0},
            'retained_refusals': [
                'First passive fragment-dictionary equality refused the new harmless id metadata field. All four original before/after byte/hash fields were equal; failed-only review qualifies only that new fixed metadata ID and unchanged original fields. No source or control changes.',
                'First planning inspection used old b013-parent tooling rather than exact7d; refused before implementation/tests; revised outer layer preserves recovery175c, Camera, bridge and old manifests/pins.',
                'First important20 correctly refused unknown launcher bytes but its NEW message missed the unchanged modal exact-current regex; only failed1 plus owning/changed NEW2 recovered.',
                'A passive metadata printer used unavailable python alias and stopped before executing any review code; python3 read the same existing records. No source or test changes.',
                'Combined passive source display exceeded output budget; remaining owning source portions were read in bounded slices without control execution.'],
            'limitations': {'issue141_remains_open': True, 'original_launch_cause_known': False,
             'native_launch_Worker_XML_Instruments_leaks_schema_registration_readiness_acceptance': False,
             'original_image609_NEW18_results_are_historical_not_current1375_execution': True,
             'lead_integration_push_dispatch_result_acceptance_and_issue_closure_pending': True,
             'native_consumer_API_ABI_dependency_legal_security_publication_readiness_gates_unchanged': True},
            'artifacts': artifacts}


target = OUT / 'PASSIVE-REVIEW-RECOVERY1.json'
assert not target.exists(), 'Never overwrite a preserved passive review'
try:
    report = run()
except Exception as error:
    failure = OUT / 'PASSIVE-REVIEW-RECOVERY1-REFUSAL.json'
    assert not failure.exists()
    failure.write_text(json.dumps({'schema_version': 1, 'checks': checks,
        'refusal_type': type(error).__name__, 'refusal': str(error),
        'source_test_native_SDK_profile_changes_or_executions': 0}, indent=2, sort_keys=True) + '\n')
    raise
target.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({'receipt': str(target), 'sha256': sha(target.read_bytes()),
                 'passed_checks': report['passed_checks'], 'count': report['actual_final_input_count'],
                 'input_digest': report['actual_final_input_digest'],
                 'important_controls_reexecuted': 0}, sort_keys=True))
