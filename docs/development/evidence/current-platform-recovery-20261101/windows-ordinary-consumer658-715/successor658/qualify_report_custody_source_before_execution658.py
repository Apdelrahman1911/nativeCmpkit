#!/usr/bin/env python3
"""Finite passive AST/text source qualification; no target/helper/test imports."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat

PACKET = Path(__file__).resolve().parent
ORIGINAL = Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-current2ee707-route658')
REVIEW705 = Path('/root/nativecmpkit-source-proposals-20261104/producer-budget-review705/windows-ordinary-consumer658')
checks, inputs, absences = [], {}, {}


def check(value, label):
    checks.append({'check': label, 'passed': bool(value)})
    if not value:
        raise ValueError(label)


def read(path, kind='finite-source-or-saved-result', limit=64 * 1024**2):
    path = Path(path)
    before = path.stat(follow_symlinks=False)
    check(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_nlink == 1 and before.st_size <= limit,
          'Bounded unshared named passive input: ' + str(path))
    raw = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    check((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
          (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Stable named passive input: ' + str(path))
    value = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'actual_read_mode': f'{before.st_mode & 0o777:04o}', 'kind': kind}
    if str(path) in inputs:
        check(inputs[str(path)]['bytes'] == value['bytes'] and inputs[str(path)]['sha256'] == value['sha256'], 'Repeated named source input held: ' + str(path))
    else:
        inputs[str(path)] = value
    return raw


def row(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, value):
    with (PACKET / name).open('x') as output:
        json.dump(value, output, indent=2, sort_keys=True); output.write('\n')
    (PACKET / name).chmod(0o600)


def calls(container, name):
    return sorted((node for node in ast.walk(container) if isinstance(node, ast.Call) and ast.unparse(node.func) == name), key=lambda node: node.lineno)


def function_map(raw):
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


try:
    original_seal_raw = read(ORIGINAL / 'PACKET-SEAL658.json', 'frozen-original-full-packet-seal')
    check(row(original_seal_raw)['sha256'] == '52b7415a32687bc4dc9838057cca8ab3dee45e11c2dc43cead1b5ad80bd3df34', 'Original80-file packet custody authority held, not rewritten')
    original_recipe_raw = read(ORIGINAL / 'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json', 'frozen-original-current16-recipe')
    check(row(original_recipe_raw)['sha256'] == 'adf80ea4a7ae3aa0d4acad299b8efe4ffd2444aca6a797694a2689b363072b32', 'Original16 recipe authority held')
    original_recipe = json.loads(original_recipe_raw)
    for name, expected in original_recipe['source_files'].items():
        if name in ('.github/workflows/javafx-library-candidate.yml', 'scripts/ci/javafx_ordinary_maven_consumer.py',
                    'scripts/ci/test_javafx_ordinary_maven_route.py', 'docs/testing/javafx-ordinary-windows-route.md'):
            continue
        check(row(read(expected['source_path'], 'unchanged-exact12-authoritative-donor')) == {key: expected[key] for key in ('bytes', 'sha256')}, 'Unchanged exact12 donor source: ' + name)
    for name, expected in (
        ('REPORT-BYTE-CUSTODY-REFUSAL705.json', '6eeade9add7f714605fbc0c0bd6fc158aac29199df4b7cb1381416f3b69c05a3'),
        ('PASSIVE-BASE-SOURCE-RESULTS705.json', 'a7ed7fd5692b8f1f7052e91d0b076319f55141a0c7bbc04e4574cdc09c8195d3'),
        ('LOCATION-ONLY-CORRECTION705.json', '070eb85670dc9c8e879a42f0c350a3cb73fba6cb14a66cf744a16d2f78d17d73'),
        ('SUCCESSOR-PREEXECUTION-SOURCE-QUALIFICATION705.json', '3680b7ff66169e99e7176b9be5b4d824b19263ca4d68ee15c8735474a0e01e12'),
    ):
        check(row(read(REVIEW705 / name, 'independent705-original-base-refusal-or-coordinate-correction'))['sha256'] == expected, 'Independent705 named original authority held: ' + name)
    review_raw = read(REVIEW705 / 'FINAL-SUCCESSOR-PREEXECUTION-SOURCE-QUALIFICATION705.json', 'independent705-current-closed-baseline-source-only-qualification')
    check(row(review_raw)['sha256'] == '4b272823a92d6c0a3a1042c8e0405414fce270974c71929660462045cccee907', 'Exact705 final closed-baseline delta qualification held, not native/results/adoption acceptance')
    review705 = json.loads(review_raw)
    precursor_raw = read(PACKET / 'EXACT-REPORT-CUSTODY-CORRECTION658.json', 'retained-pre-close-precursor-inverse-fragment-recipe-not-current-acceptance')
    check(row(precursor_raw)['sha256'] == '498af0e70ba061e178abdf325970bfaa568d73679fecac9fa97ecc8012d65746', 'Retained exact pre-close source precursor unchanged')
    precursor = json.loads(precursor_raw)
    correction_raw = read(PACKET / 'EXACT-REPORT-CUSTODY-CLOSED-BASELINE-CORRECTION658.json', 'exact-current-successor-inverse-fragment-and-AST-recipe')
    check(row(correction_raw)['sha256'] == '34090afea91d10fe1a49f1d94902142186ceafa99b11bd3b9b8876d1cdfffd38', 'Exact current prepared8-driver/2-control closed-baseline recipe held')
    correction = json.loads(correction_raw)
    check(review705['final_correction_recipe'] == {'path': str(PACKET / 'EXACT-REPORT-CUSTODY-CLOSED-BASELINE-CORRECTION658.json'), **row(correction_raw)} and
          review705['only_qualified_selection'] == correction['source_controls']['only_selected_methods'] and
          review705['only_qualified_method_count'] == 3,
          'Exact705 current recipe and only changed1+NEW2 source selection, no result/native/adoption clearance')
    check(correction['passed'] is True and len(correction['driver']['fragments']) == 8 and len(correction['source_controls']['fragments']) == 2,
          'Only exact8 driver and2 control inverse-forward fragments')
    for name, key in (('scripts/ci/javafx_ordinary_maven_consumer.py', 'driver'), ('scripts/ci/test_javafx_ordinary_maven_route.py', 'source_controls')):
        old = read(PACKET / 'retained/predecessor' / name, 'exact-frozen-original-route-predecessor')
        new = read(PACKET / 'proposed' / name, 'exact-successor-canonical-source')
        check(row(old) == correction[key]['before'] and row(new) == correction[key]['after'], 'Exact old/new source correction hashes: ' + name)
        composed = old
        for fragment in correction[key]['fragments']:
            check(composed.count(fragment['preimage'].encode()) == 1, 'Exact predecessor fragment location: ' + fragment['scope'])
            composed = composed.replace(fragment['preimage'].encode(), fragment['postimage'].encode(), 1)
        check(composed == new, 'Exact complete forward correction: ' + name)
        for fragment in reversed(correction[key]['fragments']):
            check(composed.count(fragment['postimage'].encode()) == 1, 'Exact inverse fragment location: ' + fragment['scope'])
            composed = composed.replace(fragment['postimage'].encode(), fragment['preimage'].encode(), 1)
        check(composed == old, 'Exact complete inverse reconstructs original frozen source: ' + name)
    for name, retained_name, key, fragment_key, changed_scope in (
        ('scripts/ci/javafx_ordinary_maven_consumer.py', 'javafx_ordinary_maven_consumer.before-closed-file-baseline658.py', 'driver', 'driver_fragment', 'retained_resolution'),
        ('scripts/ci/test_javafx_ordinary_maven_route.py', 'test_javafx_ordinary_maven_route.before-closed-file-baseline658.py', 'source_controls', 'source_control_fragment', 'JavafxOrdinaryMavenRouteSourceTests.test_new_retained_resolution_uses_one_raw_payload_for_exclusive_report_and_strict_observation'),
    ):
        old = read(PACKET / 'retained' / retained_name, 'retained-exact-pre-close-precursor-postimage')
        new = read(PACKET / 'proposed' / name, 'exact-final-closed-baseline-postimage')
        fragment = correction['pre_execution_portability_refinement'][fragment_key]
        check(row(old) == precursor[key]['after'] and old.count(fragment['preimage'].encode()) == 1 and
              old.replace(fragment['preimage'].encode(), fragment['postimage'].encode(), 1) == new and
              new.count(fragment['postimage'].encode()) == 1 and new.replace(fragment['postimage'].encode(), fragment['preimage'].encode(), 1) == old,
              'Only one exact own closed-baseline forward/inverse refinement: ' + name)
        _, old_functions = function_map(old)
        _, new_functions = function_map(new)
        check(set(old_functions) == set(new_functions) and
              {scope for scope in old_functions if ast.dump(old_functions[scope], include_attributes=False) != ast.dump(new_functions[scope], include_attributes=False)} == {changed_scope},
              'Only stated closed-baseline AST differs from qualified precursor: ' + name)
        check(review705['final_two_source_pins'][Path(name).name] == {'path': str(PACKET / 'proposed' / name), **row(new)}, 'Exact705 current source postimage held: ' + name)
    for name in ('.github/workflows/javafx-library-candidate.yml', 'docs/testing/javafx-ordinary-windows-route.md'):
        payload = read(PACKET / 'proposed' / name, 'unchanged-route-workflow-or-doc')
        check(row(payload) == correction['unchanged_workflow_and_doc'][name] and payload == read(ORIGINAL / 'proposed' / name, 'unchanged-frozen-original-workflow-or-doc'),
              'Whole workflow/old Stop/manual triggers/ref policy/permissions/doc/lint source unchanged: ' + name)
    old_controller_raw = read(PACKET / 'retained/predecessor/scripts/ci/javafx_ordinary_maven_consumer.py')
    controller_raw = read(PACKET / 'proposed/scripts/ci/javafx_ordinary_maven_consumer.py')
    old_tree, old_functions = function_map(old_controller_raw)
    tree, functions = function_map(controller_raw)
    check(set(functions) - set(old_functions) == {'retained_resolution', 'resolution_report_held'} and
          {name for name in old_functions if ast.dump(old_functions[name], include_attributes=False) != ast.dump(functions[name], include_attributes=False)} == {'fresh_resolution', 'run'},
          'Only fresh_resolution/run ASTs and exactly2 NEW helpers; native/XML/other driver function scopes unchanged')
    capture, guard, fresh, run = (functions[name] for name in ('retained_resolution', 'resolution_report_held', 'fresh_resolution', 'run'))
    check(len(calls(capture, 'read')) == len(calls(capture, 'saved.open')) == len(calls(capture, 'json.loads')) == 1,
          'Exactly one original raw read, one exclusive retained report creation and one parsed observation')
    check(ast.unparse(calls(capture, 'read')[0].args[0]) == 'path' and
          ast.unparse(calls(capture, 'stream.write')[0].args[0]) == ast.unparse(calls(capture, 'json.loads')[0].args[0]) == 'payload',
          'Exclusive file and parsed observation consume the same captured original payload')
    check(calls(capture, 'saved.open')[0].args[0].value == 'xb' and
          calls(capture, 'stream.write')[0].lineno < calls(capture, 'stream.flush')[0].lineno < calls(capture, 'os.fstat')[0].lineno,
          'Owned file is exclusively created; identity captured after flushed raw write, never overwrite')
    opened = [node for node in capture.body if isinstance(node, ast.With)]
    closed = [node for node in capture.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'closed' for target in node.targets)]
    custody = [node for node in capture.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'custody' for target in node.targets)]
    ownership = [node for node in calls(capture, 'need') if '(owned.st_dev, owned.st_ino)' in ast.unparse(node.args[0])]
    check(len(opened) == len(closed) == len(custody) == len(ownership) == 1 and
          calls(capture, 'os.fstat')[0].lineno <= opened[0].end_lineno < closed[0].lineno < ownership[0].lineno < custody[0].lineno and
          ast.unparse(closed[0].value) == 'saved.stat(follow_symlinks=False)',
          'Owned handle dev/inode captured inside exclusive write; guarded stat baseline occurs only after write handle closes')
    check(all(required in ast.unparse(ownership[0].args[0]) for required in ('not saved.is_symlink()', 'closed.st_nlink == 1',
          '(owned.st_dev, owned.st_ino) == (closed.st_dev, closed.st_ino)', 'closed.st_size == len(payload)')),
          'Closed owned report refuses symlink/hardlink/replacement/size drift while preserving descriptor ownership')
    entries = {key.value: value for key, value in zip(custody[0].value.keys, custody[0].value.values)}
    check(ast.unparse(entries['file_identity']) == '[closed.st_dev, closed.st_ino, closed.st_size, closed.st_mtime_ns, closed.st_ctime_ns]',
          'Subsequent custody timestamps bind exact guarded closed-file baseline, not a hypothetical Windows runtime result')
    check({keyword.arg: ast.unparse(keyword.value) for keyword in calls(capture, 'json.loads')[0].keywords} == {'object_pairs_hook': 'unique', 'parse_constant': 'finite'},
          'Strict duplicate/nonfinite JSON gates preserved on the exact captured raw payload')
    check(not calls(capture, 'packaged.read_json') and not calls(capture, 'json.dumps') and not calls(capture, 'write'), 'No original-path second parse or JSON reserialization substitutes for captured bytes')
    check(ast.unparse(calls(fresh, 'invoke')[0].args[1].elts[-1]) == "custody['path']" and
          calls(fresh, 'bound_resolution')[0].lineno < calls(fresh, 'resolution_report_held')[0].lineno,
          'Pre-native verifier reads retained payload; held-byte identity gate follows independent verification before graph return')
    post = [node for node in calls(run, 'invoke') if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 'post-native-production-pin-graph-binding']
    check(len(post) == 1 and ast.unparse(post[0].args[1].elts[-1]) == "native_custody['path']", 'Post-native verifier reads retained payload, never mutable original fixture report')
    post_held = [node for node in calls(run, 'resolution_report_held') if ast.unparse(node.args[0]) == 'native_custody']
    post_graph = [node for node in calls(run, 'graph_signature') if ast.unparse(node.args[0]) == 'current']
    check(len(post_held) == len(post_graph) == 1 and post[0].lineno < calls(run, 'bound_resolution')[0].lineno < post_held[0].lineno < post_graph[0].lineno,
          'Exact post-native retained input is independently bound and held before comparing current graph/native reuse')
    check(len(calls(guard, 'need')) == 2 and len(calls(guard, 'read')) == 1 and
          calls(guard, 'need')[0].lineno < calls(guard, 'read')[0].lineno < calls(guard, 'need')[1].lineno,
          'Retained input file identity guarded before read and identity+length+digest guarded after stable read')
    check(not any(calls(guard, name) for name in ('path.unlink', 'path.write_bytes', 'path.write_text', 'path.rename', 'os.remove', 'os.replace')),
          'Changed/replaced retained report is refused and preserved, never deleted/replaced')
    check("record['resolution_reports_held'] = False" in ast.unparse(run) and "held.append(record['resolution_reports_held'])" in ast.unparse(run),
          'Finally records failed retained input custody and gates final overall acceptance')
    old_control_raw = read(PACKET / 'retained/predecessor/scripts/ci/test_javafx_ordinary_maven_route.py')
    control_raw = read(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py')
    _, old_controls = function_map(old_control_raw)
    control_tree, controls = function_map(control_raw)
    check(set(controls) - set(old_controls) == set(correction['source_controls']['NEW_methods']), 'Exactly2 NEW source-only methods; no helper import/discovery')
    check({name for name in old_controls if ast.dump(old_controls[name], include_attributes=False) != ast.dump(controls[name], include_attributes=False)} ==
          {correction['source_controls']['only_changed_existing_method']}, 'Only1 existing owning graph method changed; other9 methods/setUp/helper ASTs unchanged')
    imported = {alias.name.split('.')[0] for node in ast.walk(control_tree) if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module.split('.')[0] for node in ast.walk(control_tree) if isinstance(node, ast.ImportFrom)}
    check(imported == {'__future__', 'ast', 'hashlib', 'json', 'pathlib', 're', 'stat', 'unittest'}, 'Source controls import stdlib only, no controller/helper/old-test/native modules')
    check(not any(calls(control_tree, name) for name in ('eval', 'exec', 'compile', '__import__', 'subprocess.run', 'runpy.run_path')), 'Controls do not execute or evaluate target code')
    plan_raw = read(PACKET / 'REPORT-CUSTODY-CHANGED1-NEW2-EXECUTION-PLAN658.json', 'authorized-exact-changed1-NEW2-plan')
    plan = json.loads(plan_raw)
    check(plan['new-controls']['selected_methods'] == correction['source_controls']['only_selected_methods'] and
          plan['changed_existing_methods'] == 1 and plan['genuinely_NEW_methods'] == 2 and len(plan['new-controls']['selected_methods']) == 3,
          'Exactly changed1 plus genuinely NEW2 selections, no unchanged9 or Actionlint replay')
    check(plan['new-controls']['command'] == ['/usr/bin/python3', '-I', '-B', str(ORIGINAL / 'new_controls_audit_bootstrap.py'),
          str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'), str(PACKET / 'CHANGED1-NEW2-SOURCE658/audit.json'), *plan['new-controls']['selected_methods']],
          'Exact isolated/audited source3 command and owned receipt only')
    check(plan['exact_current_source_recipe'] == {'path': str(PACKET / 'EXACT-REPORT-CUSTODY-CLOSED-BASELINE-CORRECTION658.json'), **row(correction_raw)} and
          plan['independent705_current_source_only_qualification'] == {'path': str(REVIEW705 / 'FINAL-SUCCESSOR-PREEXECUTION-SOURCE-QUALIFICATION705.json'), **row(review_raw)} and
          plan['independent705_current_postimage_pins'] == review705['final_two_source_pins'],
          'Source execution plan binds current exact recipe705 receipt and both current postimages')
    for name in ('prepare_narrow_source_execution658.py', 'run_report_custody_selection_once658.py', 'qualify_report_custody_source_before_execution658.py'):
        ast.parse(read(PACKET / name, 'external-own-qualification-or-once-runner-source').decode())
    read(ORIGINAL / 'new_controls_audit_bootstrap.py', 'unchanged-original-audited-source-only-child-bootstrap')
    for name in ('FIRST-NEW10-SOURCE658/result.json', 'ONLYFAILED-CHANGED2-SOURCE-RECOVERY658/result.json',
                 'FIRST-ACTIONLINT658/result.json', 'ONLYFAILED-ACTIONLINT-RECOVERY658/result.json', 'TOOL-METADATA658/result.json'):
        json.loads(read(ORIGINAL / name, 'sealed-original-results-reused-not-replayed'))
    original_qualified = json.loads(read(ORIGINAL / 'QUALIFIED-RECOVERY-SOURCE-INPUTS658.json', 'historical-finite-17-named-absence-authority'))
    for name in original_qualified['ROOT_destinations_absent']:
        absences[name] = not (Path(name).exists() or Path(name).is_symlink())
        check(absences[name], 'Named ROOT unadopted addition/metadata remains absent: ' + name)
    python_real = Path('/usr/bin/python3').resolve(strict=True)
    tool_raw = read(python_real, 'installed-Python-no-download-or-new-version-query')
    check(row(tool_raw)['sha256'] == '1643dacd9feaedc58f3cc581e4d22577dfe25c09b10282936186ccf0f2e61118', 'Installed qualified Python identity unchanged')
    aliases = {'/usr/bin/python3': str(python_real)}
    for name, expected in dict(inputs).items():
        check(row(Path(name).read_bytes()) == {key: expected[key] for key in ('bytes', 'sha256')}, 'Final pre-execution named input held: ' + name)
    qualified = {'schema': 'nativecmpkit-javafx-report-custody-qualified-source-inputs658-v1', 'utc': datetime.now(timezone.utc).isoformat(),
                 'passed': True, 'plan_sha256': row(plan_raw)['sha256'], 'inputs': inputs, 'ROOT_destinations_absent': absences,
                 'tool_aliases': aliases, 'actual_named_input_count': len(inputs), 'ROOT_absence_count': len(absences),
                 'scope': 'Finite passive source-control/prerequisite input map only; no global/Git/compiler/native or runtime controller qualification'}
    write('QUALIFIED-REPORT-CUSTODY-SOURCE-INPUTS658.json', qualified)
    write('PASSIVE-REPORT-CUSTODY-SOURCE-QUALIFICATION658.json', {'passed': True, 'checks': checks, 'check_count': len(checks),
          'actual_named_input_count': len(inputs), 'actual_named_inputs_held': True, 'ROOT_absence_count': len(absences),
          'only_authorized_selection': plan['new-controls']['selected_methods'], 'source_tests_yet': 0,
          'ROOT_worktree_Git_network_build_stage_native_or_target_imports': 0})
    print(json.dumps({'passed': True, 'passive_checks': len(checks), 'actual_named_inputs': len(inputs), 'ROOT_absences': len(absences)}, sort_keys=True))
except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
    write('PASSIVE-REPORT-CUSTODY-SOURCE-QUALIFICATION658-REFUSAL.json', {'passed': False, 'error_type': type(error).__name__,
          'checks': checks, 'check_count': len(checks), 'last_check': checks[-1] if checks else None, 'command_started': False})
    raise
