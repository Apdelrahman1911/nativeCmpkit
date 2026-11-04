#!/usr/bin/env python3
"""Finite passive failed2 source/retained-original qualification; no target imports."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import stat

PACKET = Path(__file__).resolve().parent
REVIEW705 = Path('/root/nativecmpkit-source-proposals-20261104/producer-budget-review705/windows-ordinary-consumer658')
checks, inputs = [], {}


def check(value, label):
    checks.append({'check': label, 'passed': bool(value)})
    if not value:
        raise ValueError(label)


def row(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read(path, kind='finite-passive-source-or-retained-original'):
    path = Path(path)
    before = path.stat(follow_symlinks=False)
    check(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_nlink == 1 and before.st_size <= 64 * 1024**2,
          'Bounded unshared named input: ' + str(path))
    raw = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    check((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
          (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Stable named input: ' + str(path))
    value = {**row(raw), 'actual_read_mode': f'{before.st_mode & 0o777:04o}', 'kind': kind}
    if str(path) in inputs:
        check({key: inputs[str(path)][key] for key in ('bytes', 'sha256', 'actual_read_mode')} ==
              {key: value[key] for key in ('bytes', 'sha256', 'actual_read_mode')}, 'Repeated input held: ' + str(path))
    else:
        inputs[str(path)] = value
    return raw


def write(name, value):
    with (PACKET / name).open('x') as output:
        json.dump(value, output, indent=2, sort_keys=True); output.write('\n')
    (PACKET / name).chmod(0o600)


def functions(raw):
    tree = ast.parse(raw.decode())
    result = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            result[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    result[node.name + '.' + child.name] = child
    return tree, result


def calls(container, name):
    return sorted((node for node in ast.walk(container) if isinstance(node, ast.Call) and ast.unparse(node.func) == name), key=lambda node: node.lineno)


try:
    review_raw = read(REVIEW705 / 'ONLYFAILED2-PREEXECUTION-STRUCTURAL-QUALIFICATION705.json', 'independent705-exact-failed2-source-only-qualification')
    check(row(review_raw)['sha256'] == '7eefafe9147d09b45fd3abf2ba271e17b523cb6aa0ed953934e4aada8be01251', 'Exact705 onlyfailed2 source authority held')
    review705 = json.loads(review_raw)
    recovery_raw = read(PACKET / 'EXACT-ONLYFAILED2-STRUCTURAL-SOURCE-CONTROL-RECOVERY658.json', 'exact-control-only-two-fragment-recovery-recipe')
    check(row(recovery_raw)['sha256'] == '635ae29f8678dabe5243a8dd73799470b3ce5d99c663a949b156f8011b353d6b', 'Exact two-fragment source recovery held')
    recovery = json.loads(recovery_raw)
    composed_raw = read(PACKET / 'EXACT-REPORT-CUSTODY-ONLYFAILED2-STRUCTURAL-CORRECTION658.json', 'current-composed-original8-driver-and2-control-recipe')
    check(row(composed_raw)['sha256'] == '49c9c6d39524f12cc7ea16628e7039d4945403c0bea98d52594c759c26233fdd', 'Exact current composed8+2 source correction held')
    composed = json.loads(composed_raw)
    selected = recovery['only_selected_methods']
    check(selected == review705['only_qualified_selection'] and len(selected) == 2 and review705['only_qualified_method_count'] == 2,
          'Only previously failed owning graph1 and previously failed NEW raw-capture1, not passing NEW coupling1')
    check(review705['recovery_recipe'] == {'path': str(PACKET / 'EXACT-ONLYFAILED2-STRUCTURAL-SOURCE-CONTROL-RECOVERY658.json'), **row(recovery_raw)} and
          review705['composed_correction'] == {'path': str(PACKET / 'EXACT-REPORT-CUSTODY-ONLYFAILED2-STRUCTURAL-CORRECTION658.json'), **row(composed_raw)},
          '705 exact fragment/composed source authorities bound before source execution')
    old_controls = read(recovery['retained_preimage'], 'retained-exact-failed-first3-control-postimage')
    current_controls = read(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py', 'current-onlyfailed2-canonical-controls')
    check(row(old_controls) == recovery['before'] and row(current_controls) == recovery['after'], 'Exact failed preimage/current source controls')
    check(len(recovery['fragments']) == 2, 'Only two control fragments; no production/helper changes')
    forward = old_controls
    for fragment in recovery['fragments']:
        check(forward.count(fragment['preimage'].encode()) == 1, 'Exact control fragment location: ' + fragment['scope'])
        forward = forward.replace(fragment['preimage'].encode(), fragment['postimage'].encode(), 1)
    check(forward == current_controls, 'Whole two-fragment source forward proof')
    for fragment in reversed(recovery['fragments']):
        check(forward.count(fragment['postimage'].encode()) == 1, 'Exact source inverse location: ' + fragment['scope'])
        forward = forward.replace(fragment['postimage'].encode(), fragment['preimage'].encode(), 1)
    check(forward == old_controls, 'Whole two-fragment inverse reconstructs failed first3 controls')
    _, old_methods = functions(old_controls)
    control_tree, current_methods = functions(current_controls)
    check(set(old_methods) == set(current_methods) and
          {name for name in old_methods if ast.dump(old_methods[name], include_attributes=False) != ast.dump(current_methods[name], include_attributes=False)} == set(selected),
          'Only failed2 method ASTs differ; passing NEW coupling1, other9/setUp/all helpers held')
    check(review705['final_source_controls'] == {'path': str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'), **row(current_controls)}, '705 exact current control postimage bound')
    driver_raw = read(PACKET / 'proposed/scripts/ci/javafx_ordinary_maven_consumer.py', 'unchanged-final705-source-qualified-production-driver')
    check(row(driver_raw) == recovery['driver_pin'] == composed['driver']['after'] and
          review705['held_driver'] == {'path': str(PACKET / 'proposed/scripts/ci/javafx_ordinary_maven_consumer.py'), **row(driver_raw)},
          'Driver final29135be8 exact source/custody/native/XML scopes unchanged; no Windows result inference')
    _, driver_functions = functions(driver_raw)
    run = driver_functions['run']
    assignments = [node for node in ast.walk(run) if isinstance(node, ast.Assign) and
                   any(isinstance(target, ast.Name) and target.id == 'signatures' for target in node.targets)]
    expected_graph = ast.parse('{mode: graph_signature(graphs[mode]) for mode in MODES}', mode='eval').body
    check(len(assignments) == 1 and ast.dump(assignments[0].value, include_attributes=False) == ast.dump(expected_graph, include_attributes=False),
          'Actual sole try-nested assignment binds complete exact module/POM DictComp, not direct-body helper or renderer spelling')
    graph_control = current_methods[selected[0]]
    check(not calls(graph_control, 'assigned') and any(isinstance(node, ast.Call) and ast.unparse(node.func) == 'ast.parse' and
          isinstance(node.args[0], ast.Constant) and node.args[0].value == '{mode: graph_signature(graphs[mode]) for mode in MODES}' for node in ast.walk(graph_control)) and
          len(calls(graph_control, 'ast.dump')) == 4, 'Changed owning graph uses expected complete AST plus unchanged strict retained-report gate')
    capture = driver_functions['retained_resolution']
    outward_returns = [node for node in capture.body if isinstance(node, ast.Return)]
    expected_return = ast.parse('observed, custody', mode='eval').body
    check(len(outward_returns) == 1 and ast.dump(outward_returns[0].value, include_attributes=False) == ast.dump(expected_return, include_attributes=False),
          'One exact outward observed/custody tuple source shape, independent of ast.unparse parentheses')
    raw_control = current_methods[selected[1]]
    check(len(calls(raw_control, 'ast.dump')) == 2 and any(isinstance(node.args[0], ast.Constant) and node.args[0].value == 'observed, custody' for node in calls(raw_control, 'ast.parse')),
          'Failed raw-capture recovery requires strict expected tuple AST; no assertion weakening')
    imported = {alias.name.split('.')[0] for node in ast.walk(control_tree) if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module.split('.')[0] for node in ast.walk(control_tree) if isinstance(node, ast.ImportFrom)}
    check(imported == {'__future__', 'ast', 'hashlib', 'json', 'pathlib', 're', 'stat', 'unittest'} and
          not any(calls(control_tree, name) for name in ('eval', 'exec', 'compile', '__import__', 'subprocess.run', 'runpy.run_path')),
          'Same stdlib-only passive source controls; no helper/controller/old-test/process/native imports or execution')
    original_qualified_raw = read(PACKET / 'QUALIFIED-REPORT-CUSTODY-SOURCE-INPUTS658.json', 'sealed-first3-finite43-source-qualification-reused')
    original_qualified = json.loads(original_qualified_raw)
    first_result_raw = read(PACKET / 'CHANGED1-NEW2-SOURCE658/result.json', 'retained-FAILED-first3-original-result')
    first_result = json.loads(first_result_raw)
    check(row(first_result_raw) == {key: recovery['original_source3_result'][key] for key in ('bytes', 'sha256')} and
          first_result['exit_code'] == 1 and not first_result['passed'] and first_result['source_inputs_held'] and
          first_result['qualification_map_sha256'] == row(original_qualified_raw)['sha256'], 'First3 FAILED original result/qualification remains preserved')
    first_before = json.loads(read(PACKET / 'CHANGED1-NEW2-SOURCE658/source-inputs-before.json', 'first3-original-before-map'))
    first_after = json.loads(read(PACKET / 'CHANGED1-NEW2-SOURCE658/source-inputs-after.json', 'first3-original-after-map'))
    check(first_before == first_after and first_before['files'] ==
          {name: {key: value[key] for key in ('bytes', 'sha256')} for name, value in original_qualified['inputs'].items()},
          'Recorded original43/17 maps held at first3; not relabelled as current after deliberate only-control delta')
    stderr_raw = read(PACKET / 'CHANGED1-NEW2-SOURCE658/stderr.txt', 'once-retained-first3-original-failure-stream')
    read(PACKET / 'CHANGED1-NEW2-SOURCE658/stdout.txt', 'once-retained-first3-original-stdout')
    audit = json.loads(read(PACKET / 'CHANGED1-NEW2-SOURCE658/audit.json', 'first3-original-isolation-finalizer'))
    check(audit['passed'] and not audit['denied_attempts'] and first_result['audit'] == audit, 'First3 audit zero denied attempts/target actions')
    check(re.search(r'Ran 3 tests in 0\.059s\s+FAILED \(failures=1, errors=1\)', stderr_raw.decode()) is not None and
          'test_new_each_verifier_consumes_only_held_retained_report_and_finalization_preserves_changes' in stderr_raw.decode(),
          'Exact original3 count/failure/error chronology retained, accepted NEW coupling1 is reused not replayed')
    differences = []
    for name, expected in original_qualified['inputs'].items():
        current = row(read(name, 'held-first3-finite-input-except-one-controlled-source-delta'))
        if current != {key: expected[key] for key in ('bytes', 'sha256')}:
            differences.append(name)
            check(name == str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py') and
                  row(old_controls) == {key: expected[key] for key in ('bytes', 'sha256')} and current == recovery['after'], 'Only exact retained failed2 canonical control postimage changes from original43')
        check(inputs[name]['actual_read_mode'] == expected['actual_read_mode'], 'Finite original input mode held: ' + name)
    check(differences == [str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py')], 'Exactly one deliberate source file delta from recorded first3 inputs, no donor/driver/tool/workflow changes')
    for name, digest in (
        ('ORIGINAL-SUCCESSOR3-RESULT-REVIEW705.json', '7ebdf2a9a2f33c853623ca85f32dc98a128c8b17521754b0af8e1dbe241d565a'),
        ('FINAL-SUCCESSOR-PREEXECUTION-SOURCE-QUALIFICATION705.json', '4b272823a92d6c0a3a1042c8e0405414fce270974c71929660462045cccee907'),
    ):
        check(row(read(REVIEW705 / name, 'retained705-prior-source-or-original3-result-authority'))['sha256'] == digest, 'Retained705 prerequisite authority: ' + name)
    read(PACKET / 'SOURCE-CONTROL-REFUSAL-LOCATION-CORRECTION658.json', 'explicit-original-error-location-only-correction')
    read(PACKET / 'FINAL-PRESPAWN-GATE658.json', 'original80-inventory-and-source43-pre-spawn-authority-reused')
    plan_raw = read(PACKET / 'ONLYFAILED2-STRUCTURAL-EXECUTION-PLAN658.json', 'authorized-onlyfailed2-exact-plan')
    plan = json.loads(plan_raw)
    check(plan['new-controls']['selected_methods'] == selected and
          plan['new-controls']['command'] == ['/usr/bin/python3', '-I', '-B',
          '/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-current2ee707-route658/new_controls_audit_bootstrap.py',
          str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'), str(PACKET / 'ONLYFAILED2-STRUCTURAL-SOURCE-RECOVERY658/audit.json'), *selected],
          'Exactly two previously failed selections under unchanged isolated/audited original bootstrap, no discovery')
    check(plan['exact_two_control_fragment_recipe'] == {'path': str(PACKET / 'EXACT-ONLYFAILED2-STRUCTURAL-SOURCE-CONTROL-RECOVERY658.json'), **row(recovery_raw)} and
          plan['independent705_onlyfailed2_source_only_qualification'] == {'path': str(REVIEW705 / 'ONLYFAILED2-PREEXECUTION-STRUCTURAL-QUALIFICATION705.json'), **row(review_raw)} and
          plan['accepted_NEW_coupling_method_replayed'] is False and plan['unchanged_nine_replayed'] is False and plan['Actionlint_replayed'] is False,
          'Exact705/current recovery sources bound; passing coupling1 and other9/lint explicitly excluded')
    for name in ('prepare_onlyfailed2_source_execution658.py', 'run_onlyfailed2_structural_selection_once658.py', 'qualify_onlyfailed2_source_before_execution658.py'):
        ast.parse(read(PACKET / name, 'external-own-recovery-plan-runner-or-qualifier-source').decode())
    absences = {name: not (Path(name).exists() or Path(name).is_symlink()) for name in original_qualified['ROOT_destinations_absent']}
    check(all(absences.values()) and len(absences) == 17, 'Only17 named ROOT additions/metadata remain absent; no target/ROOT edits or global map claims')
    check({name: str(Path(name).resolve(strict=True)) for name in original_qualified['tool_aliases']} == original_qualified['tool_aliases'], 'Installed Python alias remains source-qualified, not downloaded/queried again')
    for name, expected in dict(inputs).items():
        check(row(Path(name).read_bytes()) == {key: expected[key] for key in ('bytes', 'sha256')}, 'Final pre-execution finite named input held: ' + name)
    qualified = {'schema': 'nativecmpkit-javafx-onlyfailed2-structural-qualified-source-inputs658-v1', 'utc': datetime.now(timezone.utc).isoformat(),
                 'passed': True, 'plan_sha256': row(plan_raw)['sha256'], 'inputs': inputs, 'ROOT_destinations_absent': absences,
                 'tool_aliases': original_qualified['tool_aliases'], 'actual_named_input_count': len(inputs), 'ROOT_absence_count': len(absences),
                 'scope': 'Finite passive source/recovery/prerequisite map only; not global/Git/compiler/native/driver runtime qualification'}
    write('QUALIFIED-ONLYFAILED2-STRUCTURAL-SOURCE-INPUTS658.json', qualified)
    write('PASSIVE-ONLYFAILED2-STRUCTURAL-SOURCE-QUALIFICATION658.json', {'passed': True, 'checks': checks, 'check_count': len(checks),
          'actual_named_input_count': len(inputs), 'actual_named_inputs_held': True, 'ROOT_absence_count': len(absences),
          'only_authorized_selection': selected, 'only_failed_recovery_tests_yet': 0, 'first3_passed_NEW_coupling1_replayed': False,
          'ROOT_worktree_Git_network_build_stage_native_or_target_imports': 0})
    print(json.dumps({'passed': True, 'passive_checks': len(checks), 'actual_named_inputs': len(inputs), 'ROOT_absences': len(absences), 'only_selected_methods': selected}, sort_keys=True))
except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
    write('PASSIVE-ONLYFAILED2-STRUCTURAL-SOURCE-QUALIFICATION658-REFUSAL.json', {'passed': False, 'error_type': type(error).__name__,
          'checks': checks, 'check_count': len(checks), 'last_check': checks[-1] if checks else None, 'command_started': False})
    raise
