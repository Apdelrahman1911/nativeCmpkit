#!/usr/bin/env python3
"""Seal finite exact source/result adoption recipe; never import candidate controllers."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import stat

PACKET = Path(__file__).resolve().parent
ORIGINAL = Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-current2ee707-route658')
REVIEW705 = Path('/root/nativecmpkit-source-proposals-20261104/producer-budget-review705/windows-ordinary-consumer658')
checks, inputs = [], {}


def check(value, label):
    checks.append({'check': label, 'passed': bool(value)})
    if not value:
        raise ValueError(label)


def row(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read(path, kind='finite-passive-source-or-retained-evidence'):
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
              {key: value[key] for key in ('bytes', 'sha256', 'actual_read_mode')}, 'Repeated named input held: ' + str(path))
    else:
        inputs[str(path)] = value
    return raw


def pointer(path, kind='retained-authority-or-result'):
    path = Path(path)
    return {'path': str(path), **row(read(path, kind))}


def write(name, value):
    with (PACKET / name).open('x') as output:
        json.dump(value, output, indent=2, sort_keys=True); output.write('\n')
    (PACKET / name).chmod(0o600)


def functions(raw):
    tree = ast.parse(raw.decode())
    result = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            result[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    result[node.name + '.' + child.name] = ast.dump(child, include_attributes=False)
    return result


try:
    original_seal_raw = read(ORIGINAL / 'PACKET-SEAL658.json', 'frozen-original80-full-packet-custody-seal')
    check(row(original_seal_raw)['sha256'] == '52b7415a32687bc4dc9838057cca8ab3dee45e11c2dc43cead1b5ad80bd3df34', 'Original80 packet seal exact authority held')
    original_seal = json.loads(original_seal_raw)
    for name, expected in original_seal['files'].items():
        current = read(ORIGINAL / name, 'original80-sealed-source-or-result-reused-not-replayed')
        check(row(current) == {key: expected[key] for key in ('bytes', 'sha256')} and
              inputs[str(ORIGINAL / name)]['actual_read_mode'] == expected['external_mode'], 'Original80 bytes/mode held: ' + name)
    check({str(path.relative_to(ORIGINAL)) for path in ORIGINAL.rglob('*') if path.is_file()} == set(original_seal['files']) | {'PACKET-SEAL658.json'} and
          {str(path.relative_to(ORIGINAL)) for path in ORIGINAL.rglob('*') if path.is_dir()} == set(original_seal['directories']), 'Original full80 file/directory inventory held, never rewritten')
    check(original_seal['file_count'] == 80 and original_seal['file_bytes'] == 1168578, 'Original80/1168578B excluding self retained, not candidate/native maps')
    original_recipe_raw = read(ORIGINAL / 'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json', 'frozen-original16-source-adoption-recipe')
    check(row(original_recipe_raw)['sha256'] == 'adf80ea4a7ae3aa0d4acad299b8efe4ffd2444aca6a797694a2689b363072b32', 'Original16 adoption recipe held')
    original_recipe = json.loads(original_recipe_raw)
    for key in ('original_exact12_authority', 'cached_independent620_authority', 'existing_workflow_registration_observation'):
        authority = original_recipe[key]
        check(row(read(authority['path'], 'cached-unchanged-original-source-or-registration-authority-not-reacquired')) ==
              {name: authority[name] for name in ('bytes', 'sha256')}, 'Named cached unchanged source/registration authority held: ' + key)
    correction_raw = read(PACKET / 'EXACT-REPORT-CUSTODY-ONLYFAILED2-STRUCTURAL-CORRECTION658.json', 'current-composed8-driver-and2-control-exact-inverse-recipe')
    check(row(correction_raw)['sha256'] == '49c9c6d39524f12cc7ea16628e7039d4945403c0bea98d52594c759c26233fdd', 'Current final source correction exact authority held')
    correction = json.loads(correction_raw)
    for name, key in (('scripts/ci/javafx_ordinary_maven_consumer.py', 'driver'), ('scripts/ci/test_javafx_ordinary_maven_route.py', 'source_controls')):
        old = read(PACKET / 'retained/predecessor' / name, 'exact-frozen-original-route-predecessor')
        current = read(PACKET / 'proposed' / name, 'current-canonical-route-postimage')
        check(row(old) == correction[key]['before'] and row(current) == correction[key]['after'], 'Exact old/current source pins: ' + name)
        value = old
        for fragment in correction[key]['fragments']:
            check(value.count(fragment['preimage'].encode()) == 1, 'Exact forward fragment location: ' + fragment['scope'])
            value = value.replace(fragment['preimage'].encode(), fragment['postimage'].encode(), 1)
        check(value == current, 'Complete original-to-final source correction: ' + name)
        for fragment in reversed(correction[key]['fragments']):
            check(value.count(fragment['postimage'].encode()) == 1, 'Exact inverse fragment location: ' + fragment['scope'])
            value = value.replace(fragment['postimage'].encode(), fragment['preimage'].encode(), 1)
        check(value == old, 'Complete final-to-frozen-original inverse: ' + name)
        old_functions, current_functions = functions(old), functions(current)
        if key == 'driver':
            check(set(current_functions) - set(old_functions) == {'retained_resolution', 'resolution_report_held'} and
                  {scope for scope in old_functions if old_functions[scope] != current_functions[scope]} == {'fresh_resolution', 'run'},
                  'Driver only fresh_resolution/run plus2 helpers; unchanged donors/verifier/native/XML/other scopes reused')
        else:
            check(set(current_functions) - set(old_functions) == set(correction['source_controls']['NEW_methods']) and
                  {scope for scope in old_functions if old_functions[scope] != current_functions[scope]} == {correction['source_controls']['only_changed_existing_method']},
                  'Exactly2 NEW methods plus changed owning graph1; original other9/setUp/helpers held')
    for name in ('.github/workflows/javafx-library-candidate.yml', 'docs/testing/javafx-ordinary-windows-route.md'):
        current = read(PACKET / 'proposed' / name, 'whole-unchanged-workflow-or-doc-postimage')
        check(current == read(ORIGINAL / 'proposed' / name, 'original-accepted-workflow-or-doc-source-reused') and
              row(current) == correction['unchanged_workflow_and_doc'][name], 'Whole unchanged workflow/doc/old Stop/manual refs/permissions source: ' + name)
    for name, digest in (
        ('EXACT-REPORT-CUSTODY-CORRECTION658.json', '498af0e70ba061e178abdf325970bfaa568d73679fecac9fa97ecc8012d65746'),
        ('EXACT-REPORT-CUSTODY-CLOSED-BASELINE-CORRECTION658.json', '34090afea91d10fe1a49f1d94902142186ceafa99b11bd3b9b8876d1cdfffd38'),
        ('EXACT-ONLYFAILED2-STRUCTURAL-SOURCE-CONTROL-RECOVERY658.json', '635ae29f8678dabe5243a8dd73799470b3ce5d99c663a949b156f8011b353d6b'),
    ):
        check(row(read(PACKET / name, 'retained-exact-predecessor-or-own-recovery-recipe'))['sha256'] == digest, 'Retained predecessor/recovery recipe held: ' + name)
    read(PACKET / 'retained/javafx_ordinary_maven_consumer.before-closed-file-baseline658.py', 'retained-pre-close-driver-postimage')
    read(PACKET / 'retained/test_javafx_ordinary_maven_route.before-closed-file-baseline658.py', 'retained-pre-close-control-postimage')
    read(PACKET / 'retained/test_javafx_ordinary_maven_route.before-onlyfailed2-structural-recovery658.py', 'retained-f865-failed-first3-control-postimage')
    first_result_raw = read(PACKET / 'CHANGED1-NEW2-SOURCE658/result.json', 'original-first3-FAILED-source-result')
    first_result = json.loads(first_result_raw)
    check(row(first_result_raw)['sha256'] == '4b509328642b13fc8ae93dc91ea7f4f23427b3d210cd3cc44a288e3abd8ede3c' and
          first_result['exit_code'] == 1 and first_result['passed'] is False and first_result['selected_method_count'] == 3, 'Original first3 is terminal FAILED, not fresh3green')
    final_result_raw = read(PACKET / 'ONLYFAILED2-STRUCTURAL-SOURCE-RECOVERY658/result.json', 'onlyfailed2-original-passing-source-result')
    final_result = json.loads(final_result_raw)
    check(row(final_result_raw)['sha256'] == 'f74ec9e9b12214f6365af0a3e6765a98ddf3ffafe57c543fa4867696e814f05f' and
          final_result['exit_code'] == 0 and final_result['passed'] is True and final_result['selected_method_count'] == 2, 'Onlyfailed2 executes2/2 once, not a replay of original3')
    first_qualified = json.loads(read(PACKET / 'QUALIFIED-REPORT-CUSTODY-SOURCE-INPUTS658.json', 'first3-recorded-finite43-qualified-input-authority'))
    final_qualified = json.loads(read(PACKET / 'QUALIFIED-ONLYFAILED2-STRUCTURAL-SOURCE-INPUTS658.json', 'onlyfailed2-recorded-finite61-qualified-input-authority'))
    for dirname, result, qualified, count, summary_pattern in (
        ('CHANGED1-NEW2-SOURCE658', first_result, first_qualified, 43, r'Ran 3 tests in 0\.059s\s+FAILED \(failures=1, errors=1\)'),
        ('ONLYFAILED2-STRUCTURAL-SOURCE-RECOVERY658', final_result, final_qualified, 61, r'Ran 2 tests in 0\.046s\s+OK'),
    ):
        before = json.loads(read(PACKET / dirname / 'source-inputs-before.json', 'original-recorded-finite-before-map'))
        after = json.loads(read(PACKET / dirname / 'source-inputs-after.json', 'original-recorded-finite-after-map'))
        check(before == after and result['source_inputs_held'] is True and len(before['files']) == count and
              before['files'] == {name: {key: expected[key] for key in ('bytes', 'sha256')} for name, expected in qualified['inputs'].items()},
              'Original execution finite source map held at its own capture: ' + dirname)
        check(len(before['ROOT_destinations_absent']) == 17 and all(before['ROOT_destinations_absent'].values()) and
              before['tool_aliases'] == qualified['tool_aliases'], 'Original17 named ROOT absences/tool aliases recorded held: ' + dirname)
        audit = json.loads(read(PACKET / dirname / 'audit.json', 'original-child-isolation-finalizer'))
        check(audit['passed'] is True and not audit['denied_attempts'] and result['audit'] == audit, 'Original audit zero denied attempts/target/helper execution: ' + dirname)
        for name, expected in result['streams'].items():
            raw = read(PACKET / dirname / name, 'original-source-control-result-stream')
            check(row(raw) == expected, 'Original result stream digest held: ' + dirname + '/' + name)
        check(re.search(summary_pattern, (PACKET / dirname / 'stderr.txt').read_text()) is not None, 'Exact original unittest count/time/result summary: ' + dirname)
        check(result['automatic_retry'] is False and result['Actionlint_replayed'] is False and result['accepted_private_library_Stop_replayed'] is False and
              result['target_imports_requested'] == result['build_stage_native_dispatch_or_Git_commands_requested'] == 0, 'No automatic/native/Stop/lint/target replay: ' + dirname)
    for name, expected in final_qualified['inputs'].items():
        check(row(read(name, 'actual-current-finite61-source-result-tool-input')) == {key: expected[key] for key in ('bytes', 'sha256')} and
              inputs[name]['actual_read_mode'] == expected['actual_read_mode'], 'Every current finite61 qualified input still holds: ' + name)
    retained_failed = read(PACKET / 'retained/test_javafx_ordinary_maven_route.before-onlyfailed2-structural-recovery658.py')
    initial_differences = []
    for name, expected in first_qualified['inputs'].items():
        value = row(read(name, 'first3-current-input-held-except-exact-one-control-postimage-delta'))
        if value != {key: expected[key] for key in ('bytes', 'sha256')}:
            initial_differences.append(name)
            check(name == str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py') and
                  row(retained_failed) == {key: expected[key] for key in ('bytes', 'sha256')}, 'Original first3 source only changes through retained exact f865 preimage')
    check(initial_differences == [str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py')], 'Only deliberately corrected source file differs from first43 snapshot, never claim all current43 bytes unchanged')
    absences = {name: not (Path(name).exists() or Path(name).is_symlink()) for name in final_qualified['ROOT_destinations_absent']}
    check(len(absences) == 17 and all(absences.values()), 'Only17 named ROOT additions/metadata remain unadopted; not actual isolated-target verification')
    reviews = {}
    for name, digest in (
        ('REPORT-BYTE-CUSTODY-REFUSAL705.json', '6eeade9add7f714605fbc0c0bd6fc158aac29199df4b7cb1381416f3b69c05a3'),
        ('PASSIVE-BASE-SOURCE-RESULTS705.json', 'a7ed7fd5692b8f1f7052e91d0b076319f55141a0c7bbc04e4574cdc09c8195d3'),
        ('LOCATION-ONLY-CORRECTION705.json', '070eb85670dc9c8e879a42f0c350a3cb73fba6cb14a66cf744a16d2f78d17d73'),
        ('SUCCESSOR-PREEXECUTION-SOURCE-QUALIFICATION705.json', '3680b7ff66169e99e7176b9be5b4d824b19263ca4d68ee15c8735474a0e01e12'),
        ('FINAL-SUCCESSOR-PREEXECUTION-SOURCE-QUALIFICATION705.json', '4b272823a92d6c0a3a1042c8e0405414fce270974c71929660462045cccee907'),
        ('ORIGINAL-SUCCESSOR3-RESULT-REVIEW705.json', '7ebdf2a9a2f33c853623ca85f32dc98a128c8b17521754b0af8e1dbe241d565a'),
        ('ONLYFAILED2-PREEXECUTION-STRUCTURAL-QUALIFICATION705.json', '7eefafe9147d09b45fd3abf2ba271e17b523cb6aa0ed953934e4aada8be01251'),
    ):
        authority = pointer(REVIEW705 / name, 'independent705-prior-refusal-source-only-or-original3-result-authority')
        check(authority['sha256'] == digest, 'Independent705 retained named authority held: ' + name)
        reviews[name] = authority
    recipe = json.loads(json.dumps(original_recipe))
    recipe['schema'] = 'nativecmpkit-javafx-current16-report-byte-custody-successor-adoption-recipe658-v1'
    recipe['utc'] = datetime.now(timezone.utc).isoformat()
    recipe['scope'] = 'Unadopted isolated-worktree exact source-only successor recipe; original9+passingNEWcoupling1 reused and onlyfailed2 actual results separate, ZERO compiler/stage/Windows/native/dispatch/issue/security acceptance'
    recipe['source_results_predecessor'] = {'original_packet': str(ORIGINAL), 'original_packet_seal': {'path': str(ORIGINAL / 'PACKET-SEAL658.json'), **row(original_seal_raw)},
                                           'original_current16_recipe': {'path': str(ORIGINAL / 'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json'), **row(original_recipe_raw)},
                                           'original80_bytes_and_modes_held': True, 'original_full_packet_file_count': 80, 'original_full_packet_bytes_excluding_self': 1168578}
    recipe['current_exact_source_correction'] = {'path': str(PACKET / 'EXACT-REPORT-CUSTODY-ONLYFAILED2-STRUCTURAL-CORRECTION658.json'), **row(correction_raw),
                                                 'driver_fragments_from_frozen_original': 8, 'control_fragments_from_frozen_original': 2,
                                                 'own_failed2_control_refinement_fragments': 2, 'whole_forward_and_inverse_qualified': True,
                                                 'precursor_tests_yet_fields_are_historical_preparation_observations': True}
    route_names = set(correction['unchanged_workflow_and_doc']) | {'scripts/ci/javafx_ordinary_maven_consumer.py', 'scripts/ci/test_javafx_ordinary_maven_route.py'}
    donor_bytes = 0
    route_bytes = 0
    for name, expected in recipe['source_files'].items():
        if name in route_names:
            source_path = PACKET / 'proposed' / name
            current = read(source_path, 'exact-current-four-route-source-postimage')
            expected.update({**row(current), 'source_path': str(source_path), 'source_mode_observed': inputs[str(source_path)]['actual_read_mode'],
                             'origin': '658 current report-byte-custody successor; workflow/doc unchanged accepted original bytes'})
            route_bytes += len(current)
        else:
            current = read(expected['source_path'], 'unchanged-exact12-authoritative-donor-source')
            check(row(current) == {key: expected[key] for key in ('bytes', 'sha256')}, 'Exact authoritative donor unchanged: ' + name)
            donor_bytes += len(current)
        check(expected['expected_mode'] == '0644' and expected['expected_git_mode'] == '100644', 'Destination policy0644/Git100644, not donor/source mode: ' + name)
    recipe['route_source_bytes'] = route_bytes
    recipe['combined_source_bytes'] = route_bytes + donor_bytes
    check(recipe['combined_file_count'] == len(recipe['source_files']) == 16 and route_bytes == 83559 and donor_bytes == 161381 and
          recipe['combined_source_bytes'] == 244940 and recipe['NEW_additions'] == 15 and recipe['exact_existing_workflow_derivatives'] == 1,
          'Exact current16/244940B=route4/83559B+held12/161381B;15 NEW destinations plus whole unchanged original workflow derivative')
    recipe['workflow_derivative']['existing_source_fragment_record']['path'] = str(ORIGINAL / recipe['workflow_derivative']['existing_source_fragment_record']['path'])
    workflow_preimage = recipe['source_files']['.github/workflows/javafx-library-candidate.yml']['root_preimage']
    preimage = read(workflow_preimage['source_path'], 'sealed-existing-workflow-base-preimage')
    current_workflow = read(PACKET / 'proposed/.github/workflows/javafx-library-candidate.yml', 'unchanged-workflow-exact-full-postimage')
    check(row(preimage) == recipe['workflow_derivative']['preimage'], 'Actual named existing workflow preimage gate exact8268B, separate from donor mode')
    value = preimage
    for fragment in recipe['workflow_derivative']['fragments']:
        if fragment['kind'] == 'replace-exact-once':
            check(value.count(fragment['preimage'].encode()) == 1, 'Exact existing workflow choice fragment unique')
            value = value.replace(fragment['preimage'].encode(), fragment['postimage'].encode(), 1)
        else:
            check(fragment['kind'] == 'append-at-exact-predecessor-EOF' and fragment['preimage'] == '', 'Only exact registered workflow NEW EOF append; no old Stop edits')
            value += fragment['postimage'].encode()
    check(value == current_workflow and row(value) == recipe['workflow_derivative']['postimage'], 'Whole final workflow reconstructs accepted original lint postimage without replay')
    recipe['actual_source_validation'] = {
        'historical_original_route_result_paths_base': str(ORIGINAL),
        'historical_original_route_source_results_reused_not_replayed': original_recipe['actual_source_validation'],
        'first_changed_graph1_NEW_custody2': {'requested': 3, 'passed': 1, 'failed': 1, 'errors': 1, 'exit_code': 1,
                                            'unittest_seconds': 0.059, 'wrapper_seconds': first_result['elapsed_seconds'], 'finite_named_inputs': 43,
                                            'ROOT_named_absences': 17, 'source_inputs_held_at_execution': True,
                                            'result': {'path': str(PACKET / 'CHANGED1-NEW2-SOURCE658/result.json'), **row(first_result_raw)},
                                            'terminal_FAILED_retained': True},
        'onlyfailed2_structural_source_recovery': {'requested': 2, 'passed': 2, 'failed': 0, 'errors': 0, 'exit_code': 0,
                                                  'unittest_seconds': 0.046, 'wrapper_seconds': final_result['elapsed_seconds'], 'finite_named_inputs': 61,
                                                  'ROOT_named_absences': 17, 'source_inputs_held_at_execution': True,
                                                  'result': {'path': str(PACKET / 'ONLYFAILED2-STRUCTURAL-SOURCE-RECOVERY658/result.json'), **row(final_result_raw)}},
        'original_other9_methods_and_setUp_helpers_reused_not_replayed': True,
        'passing_NEW_coupling1_reused_not_replayed': True,
        'current12_or_successor3_fresh_allgreen_claimed': False,
        'original_Actionlint_accepted_result_reused_whole_workflow_unchanged': True,
        'audit_denied_attempts': 0, 'finite_source_maps_are_not_Git_global_compiler_or_native_maps': True,
        'first43_current_deliberate_delta': 'Only canonical control postimage f865->0f50 through exact retained failed2 inverse; other42 held',
        'final61_current_held': True,
    }
    recipe['independent705_authorities_reused'] = reviews
    recipe['independent705_final_source_results_acceptance'] = 'Pending separate final receipt; source-only gates and original3 review do not infer result/adoption/native clearance'
    recipe['lead_only_remaining_gates'][0] = '705 independent final original source/results and actual isolated-target preimage/mode/15-absence review'
    check(all(value is False for value in recipe['material_gates'].values()) and recipe['adopted'] is False and
          recipe['ROOT_writes'] == recipe['Git_GitHub_or_network_mutations_or_queries'] == 0, 'All material/native/security/API-ABI/dependency/issue64/publication/lead adoption gates remain false')
    read(PACKET / 'SOURCE-CONTROL-REFUSAL-LOCATION-CORRECTION658.json', 'explicit-cause-coordinate-correction-preserving-original-failures')
    read(PACKET / 'PREPARATION-EXACT-PATH-FRAGMENT-REFUSAL658.json', 'retained-source-preparation-only-spelling-refusal')
    read(PACKET / 'FROZEN-ORIGINAL-POSTPREPARATION-READBACK658.json', 'retained-original-custody-preparation-recovery-readback')
    for name in ('PASSIVE-REPORT-CUSTODY-SOURCE-QUALIFICATION658.json', 'PASSIVE-ONLYFAILED2-STRUCTURAL-SOURCE-QUALIFICATION658.json', 'FINAL-PRESPAWN-GATE658.json'):
        check(json.loads(read(PACKET / name, 'saved-passive-source-or-custody-prerequisite-review'))['passed'] is True, 'Passive prerequisite original held: ' + name)
    ast.parse(read(PACKET / 'seal_current16_report_custody_source_results658.py', 'external-own-final-source-review-and-recipe-writer').decode())
    for name, expected in dict(inputs).items():
        check(row(Path(name).read_bytes()) == {key: expected[key] for key in ('bytes', 'sha256')}, 'Final passive named actual input held: ' + name)
    write('CURRENT16-REPORT-CUSTODY-WINDOWS-ADOPTION-RECIPE658.json', recipe)
    write('PASSIVE-FINAL16-SOURCE-RESULTS-INPUTS658.json', {'schema': 'nativecmpkit-javafx-current16-successor-finite-source-results-map658-v1',
          'utc': datetime.now(timezone.utc).isoformat(), 'passed': True, 'inputs': inputs, 'actual_named_input_count': len(inputs),
          'ROOT_destinations_absent': absences, 'scope': 'Finite actual named original/canonical source/result/tool/authority map only, no global/Git/compiler/native map'})
    write('PASSIVE-FINAL16-SOURCE-RESULTS-REVIEW658.json', {'schema': 'nativecmpkit-javafx-current16-successor-passive-source-results-review658-v1',
          'utc': datetime.now(timezone.utc).isoformat(), 'passed': True, 'checks': checks, 'check_count': len(checks),
          'actual_named_input_count': len(inputs), 'actual_named_inputs_held': True, 'ROOT_named_absence_count': len(absences),
          'current16_source_count': 16, 'current16_source_bytes': 244940, 'unchanged_donors': 12,
          'original80_packet_and_modes_held': True, 'original3_FAILED_retained': True, 'onlyfailed2_original_passed': True,
          'passing_NEW_coupling1_and_original_other9_reused': True, 'source_tests_lint_native_build_stage_Git_or_dispatch_replayed': False,
          'independent_or_lead_adoption_native_security_or_issue_acceptance_claimed': False})
    print(json.dumps({'passed': True, 'passive_checks': len(checks), 'actual_named_inputs': len(inputs), 'current16_sources': 16,
                      'current16_bytes': 244940, 'original80_held': True, 'source_or_native_tests_replayed': False}, sort_keys=True))
except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
    write('PASSIVE-FINAL16-SOURCE-RESULTS-REVIEW658-REFUSAL.json', {'passed': False, 'error_type': type(error).__name__,
          'checks': checks, 'check_count': len(checks), 'last_check': checks[-1] if checks else None, 'tests_or_targets_started': False})
    raise
