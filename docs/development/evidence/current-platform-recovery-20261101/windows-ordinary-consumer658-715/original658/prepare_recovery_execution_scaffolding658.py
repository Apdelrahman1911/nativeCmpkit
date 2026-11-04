#!/usr/bin/env python3
"""Create separately named passive recovery plan/qualifier/runner, externally only."""
import ast
import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent


def read(name):
    path = PACKET / name
    if not path.is_relative_to(PACKET) or path.is_symlink() or not path.is_file() or path.stat().st_size > 4 * 1024**2:
        raise ValueError('Finite external source input required')
    return path.read_bytes()


def write(name, raw):
    path = PACKET / name
    if not path.is_relative_to(PACKET) or path.exists() or path.is_symlink():
        raise ValueError('New external scaffolding destination required')
    with path.open('xb') as output:
        output.write(raw)
    path.chmod(0o600)


def replace(source, before, after):
    if source.count(before) != 1:
        raise ValueError('One exact scaffolding transition required: ' + before[:120])
    return source.replace(before, after, 1)


plan_name = 'ONLYFAILED-CHANGED2-RECOVERY-EXECUTION-PLAN658.json'
qualified_name = 'QUALIFIED-RECOVERY-SOURCE-INPUTS658.json'
outcome_name = 'PASSIVE-RECOVERY-SOURCE-QUALIFICATION658.json'
refusal_name = 'PASSIVE-RECOVERY-SOURCE-QUALIFICATION658-REFUSAL.json'
qualifier_name = 'qualify_route_recovery_before_execution658.py'
runner_name = 'run_failed_changed_route_recovery_once658.py'
methods = [
    'JavafxOrdinaryMavenRouteSourceTests.test_final_custody_and_material_gates_keep_missing_scope_unqualified',
    'JavafxOrdinaryMavenRouteSourceTests.test_new_job_is_separate_manual_windows_and_read_only',
]
original_plan = json.loads(read('NEW-ROUTE-EXECUTION-PLAN658.json'))
plan = dict(original_plan)
plan.update(schema='nativecmpkit-javafx-exact-onlyfailed-changed2-and-failed-lint-plan658-v1',
            scope='Only failed1+changed owning1 passive source methods, then only failed candidate Actionlint; eight unaffected passes reused, no old/native/build/Git/dispatch',
            original_NEW10_plan='NEW-ROUTE-EXECUTION-PLAN658.json',
            first_NEW10_result='FIRST-NEW10-SOURCE658/result.json',
            first_Actionlint_result='FIRST-ACTIONLINT658/result.json',
            original_NEW10_requested=10, original_NEW10_passed=9, original_NEW10_failed=1,
            onlyfailed_plus_changed_method_count=2, eight_unchanged_passing_methods_replayed=False,
            tool_metadata={'result_reused': 'TOOL-METADATA658/result.json', 'new_version_queries_requested': 0})
plan['new-controls'] = {
    'NEW_methods': methods,
    'command': ['/usr/bin/python3', '-I', '-B', str(PACKET / 'new_controls_audit_bootstrap.py'),
                str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'),
                str(PACKET / 'ONLYFAILED-CHANGED2-SOURCE-RECOVERY658/audit.json'), *methods],
    'timeout_seconds': 120,
}
write(plan_name, (json.dumps(plan, indent=2, sort_keys=True) + '\n').encode())

runner = read('run_new_route_selection_once.py').decode()
runner = replace(runner, "PLAN = PACKET / 'NEW-ROUTE-EXECUTION-PLAN658.json'", "PLAN = PACKET / '" + plan_name + "'")
runner = replace(runner, "QUALIFIED = PACKET / 'QUALIFIED-SOURCE-INPUTS658.json'", "QUALIFIED = PACKET / '" + qualified_name + "'")
runner = replace(runner, "('FIRST-NEW10-SOURCE658' if stage == 'new-controls' else 'FIRST-ACTIONLINT658')",
                 "('ONLYFAILED-CHANGED2-SOURCE-RECOVERY658' if stage == 'new-controls' else 'ONLYFAILED-ACTIONLINT-RECOVERY658')")
runner = replace(runner, "'schema': 'nativecmpkit-javafx-new-source-execution658-v1'",
                 "'schema': 'nativecmpkit-javafx-exact-failed-changed-recovery-execution658-v1'")
runner = replace(runner, "'automatic_retry': False, 'accepted_private_library_Stop_replayed': False}",
                 "'automatic_retry': False, 'accepted_private_library_Stop_replayed': False,\n          'initial_failures_preserved': True, 'eight_unchanged_passing_methods_replayed': False}")
runner = replace(runner, "record['selected_method_count'] = len(plan[stage]['NEW_methods'])",
                 "record['selected_method_count'] = len(plan[stage]['NEW_methods'])\n        record['selection_scope'] = 'Onlyfailed formatter fixture1 plus changed NEW-job owning1; not fresh NEW10 green'")
ast.parse(runner, filename=runner_name)
write(runner_name, runner.encode())

qualifier = read('qualify_route_source_before_execution.py').decode()
qualifier = replace(qualifier, "PACKET / 'REGISTERED-WORKFLOW-TWO-REF-DERIVATIVE658.json'",
                    "PACKET / 'REGISTERED-WORKFLOW-FINAL-DERIVATIVE658.json'")
qualifier = replace(qualifier, "PACKET / 'NEW-ROUTE-EXECUTION-PLAN658.json'", "PACKET / '" + plan_name + "'")
selection_before = """    check(len(selected) == 10 and selected == plan['new-controls']['NEW_methods'], 'Exactly NEW10 finite affected selection; no discovery/old methods')
"""
selection_after = """    original_plan_raw = read(PACKET / 'NEW-ROUTE-EXECUTION-PLAN658.json', 'retained-first-NEW10-plan')
    original_plan = json.loads(original_plan_raw)
    recovery_methods = [
        'JavafxOrdinaryMavenRouteSourceTests.test_final_custody_and_material_gates_keep_missing_scope_unqualified',
        'JavafxOrdinaryMavenRouteSourceTests.test_new_job_is_separate_manual_windows_and_read_only',
    ]
    check(len(selected) == 10 and selected == original_plan['new-controls']['NEW_methods'],
          'Original NEW10 source population retained; no discovery or method changes beyond exact2')
    check(plan['new-controls']['NEW_methods'] == recovery_methods and plan['onlyfailed_plus_changed_method_count'] == 2,
          'Only failed formatter-fixture1 plus changed NEW-job owning1 selected; other8 passing methods not replayed')
    expected_command = ['/usr/bin/python3', '-I', '-B', str(PACKET / 'new_controls_audit_bootstrap.py'),
                        str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'),
                        str(PACKET / 'ONLYFAILED-CHANGED2-SOURCE-RECOVERY658/audit.json'), *recovery_methods]
    check(plan['new-controls']['command'] == expected_command and plan['new-controls']['timeout_seconds'] == 120,
          'Exact audited source-only2 command and finite deadline')
    check(plan['actionlint']['command'] == original_plan['actionlint']['command'] and
          plan['actionlint']['timeout_seconds'] == 120,
          'Only failed candidate Actionlint surface reused; no new tool download/query or old-method action')
    first_results = {}
    for directory in ('FIRST-NEW10-SOURCE658', 'FIRST-ACTIONLINT658'):
        result_raw = read(PACKET / directory / 'result.json', 'retained-first-failed-execution-receipt')
        result = json.loads(result_raw)
        check(result['exit_code'] == 1 and result['passed'] is False and result['source_inputs_held'] and
              result['actual_named_input_count'] == 47 and result['ROOT_absence_count'] == 17,
              'Retained initial execution1 failure with47 inputs/17 absences held: ' + directory)
        check(result['plan_sha256'] == hashlib.sha256(original_plan_raw).hexdigest(),
              'Retained initial failed receipt exact plan: ' + directory)
        for stream, row in result['streams'].items():
            raw = read(PACKET / directory / stream, 'retained-original-failed-stream')
            check(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'],
                  'Retained original failed stream held: ' + directory + '/' + stream)
        before_raw = read(PACKET / directory / 'source-inputs-before.json', 'retained-initial-actual-input-map')
        after_raw = read(PACKET / directory / 'source-inputs-after.json', 'retained-initial-actual-input-map')
        check(before_raw == after_raw, 'Retained initial exact before/after maps equal: ' + directory)
        first_results[directory] = result
    first_control = first_results['FIRST-NEW10-SOURCE658']
    check(first_control['selected_NEW_methods'] == original_plan['new-controls']['NEW_methods'] and
          first_control['selected_method_count'] == 10 and first_control['audit']['passed'] and not first_control['audit']['denied_attempts'],
          'Initial NEW10 controls had no target/native/process/network/ROOT isolation attempt')
    first_stderr = (PACKET / 'FIRST-NEW10-SOURCE658/stderr.txt').read_text()
    check(first_stderr.count(' ... ok\\n') == 9 and first_stderr.count(' ... FAIL\\n') == 1 and
          'Ran 10 tests in 0.112s' in first_stderr and 'FAILED (failures=1)' in first_stderr,
          'Original NEW10 chronology is9pass/onefail, not fresh10green')
    first_lint_stdout = (PACKET / 'FIRST-ACTIONLINT658/stdout.txt').read_text()
    check(first_lint_stdout.count('\\n') == 1 and 'input "verify-signature" is not defined in action "actions/setup-java@v4"' in first_lint_stdout,
          'Original Actionlint only unsupported NEW-job option failure retained')
    audit_raw = read(PACKET / 'FIRST-NEW10-SOURCE658/audit.json', 'retained-initial-child-audit')
    check(json.loads(audit_raw) == first_control['audit'], 'Retained initial audit exact receipt binding')

    correction_raw = read(PACKET / 'CORRECTION-FAILED-AND-CHANGED2-RECIPE658.json', 'exact-recovery-fragment-and-AST-authority')
    correction = json.loads(correction_raw)
    check(correction['passed'] is True and correction['only_requested_recovery_methods'] == recovery_methods,
          'Correction authority owns exactly failed/changed2')
    old_control = read(PACKET / correction['original_source_controls']['retained_path'], 'retained-exact-initial-control-failure-postimage')
    old_workflow = read(PACKET / correction['original_workflow']['retained_path'], 'retained-exact-initial-Actionlint-failure-postimage')
    for raw, row in ((old_control, correction['original_source_controls']), (old_workflow, correction['original_workflow']),
                     (control_raw, correction['final_source_controls']), (workflow, correction['final_workflow'])):
        check(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'],
              'Exact original/final correction postimages held: ' + row['sha256'])
    reconstructed = old_control
    for fragment in correction['control_fragments']:
        check(reconstructed.count(fragment['preimage'].encode()) == 1, 'Exact control recovery predecessor fragment location')
        reconstructed = reconstructed.replace(fragment['preimage'].encode(), fragment['postimage'].encode(), 1)
    check(reconstructed == control_raw, 'Only three finite control source fragments compose final exact2-method postimage')
    old_owner = [node for node in ast.parse(old_control.decode()).body if isinstance(node, ast.ClassDef)][0]
    old_methods = {node.name: node for node in old_owner.body if isinstance(node, ast.FunctionDef)}
    new_methods = {node.name: node for node in classes[0].body if isinstance(node, ast.FunctionDef)}
    check(old_methods.keys() == new_methods.keys(), 'Every original owning control method remains')
    changed_methods = {name for name in old_methods if ast.dump(old_methods[name], include_attributes=False) !=
                       ast.dump(new_methods[name], include_attributes=False)}
    check(changed_methods == {name.split('.', 1)[1] for name in recovery_methods},
          'Onlyfailed/changed2 method ASTs differ; all eight unaffected methods/setUp remain identical')
    for name, old in old_methods.items():
        binding = correction['method_AST_bindings'][name]
        check(binding['before_AST_sha256'] == hashlib.sha256(ast.dump(old, include_attributes=False).encode()).hexdigest() and
              binding['after_AST_sha256'] == hashlib.sha256(ast.dump(new_methods[name], include_attributes=False).encode()).hexdigest(),
              'Every method AST exact correction binding: ' + name)
    owner = new_methods['test_new_job_is_separate_manual_windows_and_read_only']
    check('verify-signature:' in {node.value for node in ast.walk(owner) if isinstance(node, ast.Constant) and isinstance(node.value, str)},
          'Changed owning method explicitly denies unsupported option in NEW job')
    fixture = new_methods['test_final_custody_and_material_gates_keep_missing_scope_unqualified']
    check(len(calls(fixture, 'ast.dump')) == 2 and len(calls(fixture, 'ast.parse')) == 1 and
          'all(runtime[key] == after_runtime[key] for key in keys)' in {node.value for node in ast.walk(fixture) if isinstance(node, ast.Constant) and isinstance(node.value, str)},
          'Failed formatter fixture now compares exact runtime assignment-value AST, preserving custody semantics')
    old_prefix, old_new_job = old_workflow.split(b'  ordinary-windows-consumer1:\\n', 1)
    current_prefix, current_new_job = workflow.split(b'  ordinary-windows-consumer1:\\n', 1)
    fragment = correction['workflow_fragment']
    check(old_prefix == current_prefix and old_new_job.count(fragment['preimage'].encode()) == 1 and
          old_new_job.replace(fragment['preimage'].encode(), fragment['postimage'].encode(), 1) == current_new_job,
          'Only unsupported option removed in appended NEW job; every old byte retained')
    check(old_prefix.count(b'          verify-signature: true\\n') == 1 and b'verify-signature:' not in current_new_job,
          'Old pinned setup-java option remains; NEW v4 unsupported option excluded without signing/trust inference')
"""
qualifier = replace(qualifier, selection_before, selection_after)
qualifier = replace(qualifier, "for name in ('new_controls_audit_bootstrap.py', 'run_new_route_selection_once.py', 'qualify_route_source_before_execution.py'):",
                    "for name in ('new_controls_audit_bootstrap.py', '" + runner_name + "', '" + qualifier_name + "', 'prepare_failed_changed2_recovery658.py', 'prepare_recovery_execution_scaffolding658.py'):")
qualifier = replace(qualifier, "PACKET / 'QUALIFIED-SOURCE-INPUTS658.json'", "PACKET / '" + qualified_name + "'")
qualifier = replace(qualifier, "PACKET / 'PASSIVE-ROUTE-SOURCE-QUALIFICATION658.json'", "PACKET / '" + outcome_name + "'")
qualifier = replace(qualifier, "PACKET / 'PASSIVE-ROUTE-SOURCE-QUALIFICATION658-REFUSAL.json'", "PACKET / '" + refusal_name + "'")
qualifier = replace(qualifier, "'NEW10_and_Actionlint_execution_yet': 0, 'ROOT_Git_network_native_build_or_target_imports': 0,",
                    "'onlyfailed_changed2_and_failed_Actionlint_recovery_execution_yet': 0,\n               'first_NEW10_retained': {'requested': 10, 'passed': 9, 'failed': 1, 'replayed_other8': False},\n               'ROOT_Git_network_native_build_or_target_imports': 0,")
qualifier = replace(qualifier, "'scope': 'Exact final source/ref/tool qualification before only NEW source controls/Actionlint; no current HEAD, native acceptance or #64 closure'",
                    "'scope': 'Exact recovered source/ref/tool qualification before only failed/changed2 and failed candidate Actionlint; no current HEAD, native acceptance or #64 closure'")
ast.parse(qualifier, filename=qualifier_name)
write(qualifier_name, qualifier.encode())
print(json.dumps({'passed': True, 'plan': plan_name, 'qualifier': qualifier_name, 'runner': runner_name,
                  'only_selected_methods': methods, 'ROOT_writes': 0, 'target_or_test_execution': 0}, sort_keys=True))
