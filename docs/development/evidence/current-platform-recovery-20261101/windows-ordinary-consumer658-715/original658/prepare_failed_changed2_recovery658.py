#!/usr/bin/env python3
"""External-only exact fixture/NEW-job recovery; never import or execute targets."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat

PACKET = Path(__file__).resolve().parent
checks = []


def check(value, label):
    checks.append({'check': label, 'passed': bool(value)})
    if not value:
        raise ValueError(label)


def read(relative, expected=None):
    path = PACKET / relative
    check(path.is_relative_to(PACKET) and not path.is_symlink(), 'Confined external named input: ' + relative)
    before = path.stat(follow_symlinks=False)
    check(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size < 4 * 1024**2,
          'Bounded unshared external input: ' + relative)
    raw = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    check((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
          (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
          'Stable external read: ' + relative)
    if expected:
        check(hashlib.sha256(raw).hexdigest() == expected, 'Exact original postimage held: ' + relative)
    return raw


def row(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(relative, raw):
    path = PACKET / relative
    check(path.is_relative_to(PACKET) and not path.exists() and not path.is_symlink(),
          'New external evidence destination only: ' + relative)
    with path.open('xb') as output:
        output.write(raw)
    path.chmod(0o600)


def write_json(relative, value):
    write(relative, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def exact(payload, before, after, label):
    check(payload.count(before.encode()) == 1, 'One exact recovery fragment: ' + label)
    result = payload.replace(before.encode(), after.encode(), 1)
    check(result.count(after.encode()) == 1 and result.replace(after.encode(), before.encode(), 1) == payload,
          'Exact fragment inverse held: ' + label)
    return result


workflow_relative = 'proposed/.github/workflows/javafx-library-candidate.yml'
control_relative = 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'
workflow = read(workflow_relative, 'd1aef6e7372b0dd1be9338a44a280266c61997e00fb0921c1c4b9903af807363')
control = read(control_relative, '08ff18873b84f8d78a28c689d3cf2466583add6baba3235d98542d6f43a125f4')
unchanged = {}
for relative, expected in (
    ('proposed/scripts/ci/javafx_ordinary_maven_consumer.py', '628bb308bbaabf3f4d4e35063c0253d28439746d5a4ce54846fec092ea8f0a14'),
    ('proposed/docs/testing/javafx-ordinary-windows-route.md', 'f4e7a54782f7d8b25402394b62a2140acb55669dad4218ddea7159ccf7443c20')):
    unchanged[relative] = row(read(relative, expected))
write('retained/javafx-library-candidate.before-actionlint-recovery658.yml', workflow)
write('retained/test_javafx_ordinary_maven_route.before-failed-fixture-recovery658.py', control)

header = b'  ordinary-windows-consumer1:\n'
check(workflow.count(header) == 1, 'Exactly one appended NEW job')
old_prefix, new_job_tail = workflow.split(header, 1)
new_job = header + new_job_tail
workflow_before = "          java-version: '17'\n          verify-signature: true\n          overwrite-settings: false\n"
workflow_after = "          java-version: '17'\n          overwrite-settings: false\n"
new_job_after = exact(new_job, workflow_before, workflow_after, 'Only NEW setup-java unsupported option')
workflow_after_raw = old_prefix + new_job_after
check(old_prefix.count(b'          verify-signature: true\n') == 1 and
      workflow_after_raw.split(header, 1)[0] == old_prefix,
      'Old job setup-java byte and every old-prefix byte stay unchanged')

fixture_before = "                         'read(lt.safe_path(private_repository, name))', 'all(runtime[key] == after_runtime[key] for key in keys)',\n"
fixture_after = "                         'read(lt.safe_path(private_repository, name))',\n"
insert_before = "            self.assertIn(required, rendered)\n        receipt_update = [node for node in calls(run, 'record.update') if any(keyword.arg == 'detached_process_absence_verified' for keyword in node.keywords)]\n"
insert_after = """            self.assertIn(required, rendered)
        runtime_identity = [node.value for node in ast.walk(run) if isinstance(node, ast.Assign)
                            and len(node.targets) == 1 and isinstance(node.targets[0], ast.Subscript)
                            and isinstance(node.targets[0].value, ast.Name) and node.targets[0].value.id == 'record'
                            and isinstance(node.targets[0].slice, ast.Constant)
                            and node.targets[0].slice.value == 'runtime_identity_held']
        self.assertEqual(len(runtime_identity), 1)
        expected_runtime_identity = ast.parse('all(runtime[key] == after_runtime[key] for key in keys)', mode='eval').body
        self.assertEqual(ast.dump(runtime_identity[0], include_attributes=False),
                         ast.dump(expected_runtime_identity, include_attributes=False))
        receipt_update = [node for node in calls(run, 'record.update') if any(keyword.arg == 'detached_process_absence_verified' for keyword in node.keywords)]
"""
owning_before = "        for forbidden in ('run_library_candidate.py', 'library_tests.py', 'actions/cache/', 'push:', 'pull_request:', 'schedule:', '*.jar', '*.log', '*.stdout', '*.stderr'):\n"
owning_after = "        for forbidden in ('run_library_candidate.py', 'library_tests.py', 'actions/cache/', 'push:', 'pull_request:', 'schedule:', 'verify-signature:', '*.jar', '*.log', '*.stdout', '*.stderr'):\n"
control_after_raw = exact(control, fixture_before, fixture_after, 'Only failed fixture raw formatter spelling removed')
control_after_raw = exact(control_after_raw, insert_before, insert_after, 'Exact runtime identity assignment value AST replaces spelling assumption')
control_after_raw = exact(control_after_raw, owning_before, owning_after, 'Changed NEW-job owning method denies unsupported option')
old_tree, new_tree = ast.parse(control.decode()), ast.parse(control_after_raw.decode())
old_class = [node for node in old_tree.body if isinstance(node, ast.ClassDef)]
new_class = [node for node in new_tree.body if isinstance(node, ast.ClassDef)]
check(len(old_class) == len(new_class) == 1 and old_class[0].name == new_class[0].name,
      'One identical owning NEW source-only TestCase')
old_methods = {node.name: ast.dump(node, include_attributes=False) for node in old_class[0].body if isinstance(node, ast.FunctionDef)}
new_methods = {node.name: ast.dump(node, include_attributes=False) for node in new_class[0].body if isinstance(node, ast.FunctionDef)}
failed = 'test_final_custody_and_material_gates_keep_missing_scope_unqualified'
changed = 'test_new_job_is_separate_manual_windows_and_read_only'
check(old_methods.keys() == new_methods.keys(), 'No control method addition/deletion')
check({name for name in old_methods if old_methods[name] != new_methods[name]} == {failed, changed},
      'Only failed1 plus changed owning1 method ASTs differ')
method_rows = {name: {'before_AST_sha256': hashlib.sha256(old_methods[name].encode()).hexdigest(),
                      'after_AST_sha256': hashlib.sha256(new_methods[name].encode()).hexdigest(),
                      'unchanged': old_methods[name] == new_methods[name]}
               for name in old_methods}


def outside_methods(payload):
    tree = ast.parse(payload.decode())
    owner = [node for node in tree.body if isinstance(node, ast.ClassDef)][0]
    nodes = [node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name in (failed, changed)]
    lines = payload.splitlines(keepends=True)
    output, cursor = bytearray(), 0
    for node in sorted(nodes, key=lambda value: value.lineno):
        check(not node.decorator_list, 'No hidden decorator scope in recovery')
        output.extend(b''.join(lines[cursor:node.lineno - 1]))
        output.extend(('__EXACT_RECOVERY_' + node.name + '__\n').encode())
        cursor = node.end_lineno
    output.extend(b''.join(lines[cursor:]))
    return bytes(output)


check(outside_methods(control) == outside_methods(control_after_raw),
      'Every other control byte/helper/setUp/eight unaffected methods remains identical')
check(len([name for name in old_methods if name.startswith('test_')]) == 10,
      'Original NEW10 population stays finite; recovery selects only2')
reconstruction = control_after_raw
for before, after in reversed(((fixture_before, fixture_after), (insert_before, insert_after), (owning_before, owning_after))):
    reconstruction = reconstruction.replace(after.encode(), before.encode(), 1)
check(reconstruction == control, 'Three exact source-control fragments reconstruct original failure bytes')

# Only the two owned proposal files are updated, after retaining exact originals.
for relative, original, replacement in ((workflow_relative, workflow, workflow_after_raw), (control_relative, control, control_after_raw)):
    check(read(relative) == original, 'Owned proposal preimage held immediately before correction: ' + relative)
    (PACKET / relative).write_bytes(replacement)
    (PACKET / relative).chmod(0o600)

prior_derivative = json.loads(read('REGISTERED-WORKFLOW-TWO-REF-DERIVATIVE658.json'))
final_derivative = dict(prior_derivative)
final_derivative.update(schema='nativecmpkit-javafx-registered-file-final-failed-only-derivative658-v1',
                        utc=datetime.now(timezone.utc).isoformat(),
                        scope='External final exact2-recovery postimages only; source qualification/results remain separate, not adoption/native/dispatch')
final_derivative['postimage'] = {**row(workflow_after_raw), 'source_path': str(PACKET / workflow_relative)}
final_derivative['fragments'] = [prior_derivative['fragments'][0],
                               {'kind': 'append-at-exact-predecessor-EOF', 'preimage': '', 'postimage': new_job_after.decode()}]
final_derivative['new_job_sha256'] = hashlib.sha256(new_job_after).hexdigest()
final_derivative['source_controls'] = {**prior_derivative['source_controls'], 'bytes': len(control_after_raw),
                                      'after_sha256': hashlib.sha256(control_after_raw).hexdigest(),
                                      'initial_NEW10_execution': 'FIRST-NEW10-SOURCE658/result.json',
                                      'initial_requested': 10, 'initial_passed': 9, 'initial_failed': 1,
                                      'onlyfailed_changed_recovery_methods': [failed, changed],
                                      'recovery_execution_yet': False}
final_derivative['pre_recovery_derivative_recipe'] = {'path': 'REGISTERED-WORKFLOW-TWO-REF-DERIVATIVE658.json',
                                                     'retained_postimage': 'retained/javafx-library-candidate.before-actionlint-recovery658.yml'}
final_derivative['unsupported_setup_java_v4_input_removed_only_from_NEW_job'] = True
final_derivative['signature_trust_security_or_dependency_clearance_inferred'] = False
write_json('REGISTERED-WORKFLOW-FINAL-DERIVATIVE658.json', final_derivative)

write_json('CORRECTION-FAILED-AND-CHANGED2-RECIPE658.json', {
    'schema': 'nativecmpkit-javafx-onlyfailed-plus-changed2-source-recovery658-v1',
    'utc': datetime.now(timezone.utc).isoformat(), 'checks': checks, 'check_count': len(checks), 'passed': True,
    'scope': 'External-only exact NEW-job option/failed formatter-fixture recovery; no controller/doc/native/ROOT/Git/network changes',
    'original_source_controls': {**row(control), 'retained_path': 'retained/test_javafx_ordinary_maven_route.before-failed-fixture-recovery658.py'},
    'final_source_controls': {**row(control_after_raw), 'source_path': str(PACKET / control_relative)},
    'original_workflow': {**row(workflow), 'retained_path': 'retained/javafx-library-candidate.before-actionlint-recovery658.yml'},
    'final_workflow': {**row(workflow_after_raw), 'source_path': str(PACKET / workflow_relative)},
    'workflow_fragment': {'kind': 'scoped-exact-once-in-appended-NEW-job', 'scope_header': header.decode(),
                          'preimage': workflow_before, 'postimage': workflow_after},
    'control_fragments': [{'kind': 'replace-exact-once', 'preimage': before, 'postimage': after}
                          for before, after in ((fixture_before, fixture_after), (insert_before, insert_after), (owning_before, owning_after))],
    'method_AST_bindings': method_rows, 'unchanged_controller_and_doc': unchanged,
    'only_requested_recovery_methods': ['JavafxOrdinaryMavenRouteSourceTests.' + name for name in (failed, changed)],
    'eight_unchanged_initial_passes_reused_not_replayed': True,
    'old_public_stop_job_and_old_option_line_prefix_unchanged': True,
    'signature_trust_security_or_dependency_clearance_inferred': False,
    'ROOT_writes': 0, 'target_imports': 0, 'tests_lint_build_native_stage_dispatch_or_Git_execution': 0})

print(json.dumps({'passed': True, 'check_count': len(checks), 'final_workflow': row(workflow_after_raw),
                  'final_controls': row(control_after_raw), 'changed_test_methods': [failed, changed]}, sort_keys=True))
