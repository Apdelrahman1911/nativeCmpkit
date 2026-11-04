"""Freeze the already-executed XML correction; passive byte/AST work only.

This is a post-execution custody/adoption script, not the original FIRST8 runner
and not permission to execute that accepted scope again.
"""
from pathlib import Path
import ast
import copy
import datetime
import difflib
import hashlib
import json
import os
import stat

R = Path('/root/nativecmpkit-worktrees/android-permission-lifecycle')
P = Path('/root/nativecmpkit-source-proposals-20261104/android-permission-lifecycle-api35-ygaa_ud4')
C = P / 'xml-correction'
CORRECTED = (
    'scripts/ci/android_permission_lifecycle_contract.py',
    'scripts/ci/test_android_permission_lifecycle_source.py',
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def metadata(path):
    info = path.lstat()
    assert stat.S_ISREG(info.st_mode), path
    data = path.read_bytes()
    return {'sha256': digest(data), 'bytes': len(data), 'mode': oct(stat.S_IMODE(info.st_mode))}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


initial_patch = json.loads((P / 'PATCH.json').read_text())
initial_map = json.loads((P / 'FROZEN-MAP.json').read_text())
first23 = json.loads((P / 'NEW-SOURCE-FIRST23.json').read_text())
green8 = json.loads((P / 'XML-CORRECTION-FIRST8.json').read_text())
final_map = green8['after_inputs']
assert len(initial_map) == len(final_map) == 43
assert initial_map == first23['after_inputs'] == first23['before_inputs']
assert green8['before_inputs'] == final_map and green8['held']
assert green8['exit_code'] == 0
assert set(initial_map) == set(final_map)
assert {rel for rel in final_map if final_map[rel] != initial_map[rel]} == set(CORRECTED)
assert green8['delta_from_first23_source_map'] == list(CORRECTED)
assert not green8['accepted23_broad_replay']
assert len(green8['new_methods']) == 3 and len(green8['directly_affected_methods']) == 5

source_bytes = {}
for rel in final_map:
    assert metadata(R / rel) == final_map[rel], (rel, 'current source drift')
    source_bytes[rel] = (R / rel).read_bytes()
    origin = P / ('frozen' if (P / 'frozen' / rel).exists() else 'dependencies') / rel
    assert metadata(origin) == initial_map[rel], (rel, 'initial capsule drift')

retained_names = [
    'PATCH.json', 'FROZEN-MAP.json', 'PASSIVE-RECIPE-VALIDATION.json',
    'PREIMAGES.json', 'DEPENDENCIES-CUSTODY.json', 'ORIGINAL-CRITERIA.json',
    'NATIVE-VERIFICATION-PLAN.json', 'NEW-CONTROLS.txt',
    'NEW-SOURCE-RED.json', 'NEW-SOURCE-RED.stdout', 'NEW-SOURCE-RED.stderr',
    'NEW-SOURCE-RED-controls14.py', 'NEW-SOURCE-RED-source-reconstruction.json',
    'NEW-SOURCE-FIRST23.json', 'NEW-SOURCE-FIRST23.stdout', 'NEW-SOURCE-FIRST23.stderr',
    'NEW-XML-RED1.json', 'NEW-XML-RED1.stdout', 'NEW-XML-RED1.stderr',
    'test_xml_error_domain_new.py',
    'NEW-ENCODED-DTD-RED1.json', 'NEW-ENCODED-DTD-RED1.stdout', 'NEW-ENCODED-DTD-RED1.stderr',
    'test_encoded_dtd_error_domain_new.py',
    'XML-CORRECTION-FIRST8.json', 'XML-CORRECTION-FIRST8.stdout', 'XML-CORRECTION-FIRST8.stderr',
]
retained = {name: metadata(P / name) for name in retained_names}
for stem in ('NEW-SOURCE-RED', 'NEW-SOURCE-FIRST23', 'NEW-XML-RED1', 'NEW-ENCODED-DTD-RED1', 'XML-CORRECTION-FIRST8'):
    receipt = json.loads((P / (stem + '.json')).read_text())
    for channel in ('stdout', 'stderr'):
        if channel + '_sha256' in receipt:
            assert digest((P / (stem + '.' + channel)).read_bytes()) == receipt[channel + '_sha256']
for stem in ('NEW-XML-RED1', 'NEW-ENCODED-DTD-RED1'):
    receipt = json.loads((P / (stem + '.json')).read_text())
    assert receipt['before_inputs'] == receipt['after_inputs'] == initial_map
    assert receipt['accepted'] == 0 and receipt['exit_code'] == 1

review_path = P.parent / 'android-permission-lifecycle-review712' / 'ESSENTIAL-REVIEW.json'
review_hash = digest(review_path.read_bytes())
assert review_hash == 'bf82c04b60acb7e8f2a3b690d1c444e9f9b786b86622c361c57b4d72db28ef50'

delta_rows = []
correction_fragment_count = 0
for rel in CORRECTED:
    before = (P / 'frozen' / rel).read_bytes()
    after = source_bytes[rel]
    old_lines = before.decode().splitlines(keepends=True)
    new_lines = after.decode().splitlines(keepends=True)
    fragments = []
    for index, group in enumerate(difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_grouped_opcodes(6), 1):
        ai, aj = group[0][1], group[-1][2]
        bi, bj = group[0][3], group[-1][4]
        old = ''.join(old_lines[ai:aj])
        new = ''.join(new_lines[bi:bj])
        assert old != new and before.decode().count(old) == after.decode().count(new) == 1
        fragments.append({'id': f'xml-correction:{rel}:{index}', 'before': old, 'after': new,
                          'before_line': ai + 1, 'after_line': bi + 1})
    forward = before.decode()
    for fragment in fragments:
        assert forward.count(fragment['before']) == 1
        forward = forward.replace(fragment['before'], fragment['after'], 1)
    assert forward.encode() == after
    inverse = forward
    for fragment in reversed(fragments):
        assert inverse.count(fragment['after']) == 1
        inverse = inverse.replace(fragment['after'], fragment['before'], 1)
    assert inverse.encode() == before
    assert initial_map[rel]['mode'] == final_map[rel]['mode'] == '0o644'
    correction_fragment_count += len(fragments)
    delta_rows.append({'path': rel, 'before': initial_map[rel], 'after': final_map[rel],
                       'before_source': 'frozen/' + rel,
                       'after_source': 'xml-correction/frozen/' + rel,
                       'fragments': fragments})

test_relative = CORRECTED[1]
initial_ast = ast.parse((P / 'frozen' / test_relative).read_text(), filename='initial/' + test_relative)
final_ast = ast.parse(source_bytes[test_relative].decode(), filename='successor/' + test_relative)
old_methods = {node.name: ast.dump(node) for node in ast.walk(initial_ast)
               if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}
new_methods = {node.name: node for node in ast.walk(final_ast)
               if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}
assert len(old_methods) == 23 and len(new_methods) == 26
assert set(new_methods) - set(old_methods) == set(green8['new_methods'])
assert all(ast.dump(new_methods[name]) == old_methods[name] for name in old_methods)
assert set(green8['directly_affected_methods']) <= set(old_methods)

reasons = {
    'test_new_malformed_source_compiled_and_reporter_xml_normalize_into_named_failure_domain':
        'NEW three-domain malformed XML must yield exact bounded ValueError with parser context suppressed.',
    'test_new_utf16_dtd_cannot_bypass_source_compiled_or_reporter_entity_refusals':
        'NEW three-domain inert UTF16 DTD cannot bypass parser-level entity/DTD refusal.',
    'test_new_entity_free_compiled_api35_helper_manifest_keeps_signature_and_sdk_policy':
        'NEW inert compiled-positive manifest exercises the changed helper parser with API35/target37 signature policy and wrong-SDK refusals; not an actual APK.',
    'test_manifest_exact_five_runtime_permissions_and_signature_only_control':
        'Direct helper parser valid-source path preserves exact runtime permission/signature control policy.',
    'test_manifest_refuses_extra_permission_shared_uid_and_unprotected_component':
        'Direct helper parser negative policy branches must keep permission/shared-UID/component/API/target refusals.',
    'test_new_reporter_permission_exception_is_exact_signature_only_not_native_grant':
        'Direct reporter parser admission/refusal preserves the exact named signature-only exception.',
    'test_new_complete_source_readback_and_receipt_refuse_missing_forged_native_inputs':
        'Transitive source_contract calls both changed parsers before exact source receipt validation and native-claim refusals.',
    'test_new_request_refuses_boolean_old_api_wrong_module_broad_focus_and_unbound_plan':
        'Transitive source_contract calls both changed parsers before focus-bound request/plan refusal checks.',
}
selection_rows = []
text_lines = source_bytes[test_relative].decode().splitlines(keepends=True)
for kind, names in (('NEW', green8['new_methods']), ('directly_affected', green8['directly_affected_methods'])):
    for name in names:
        node = new_methods[name]
        body = ''.join(text_lines[node.lineno - 1:node.end_lineno])
        selection_rows.append({'method': name, 'kind': kind, 'rationale': reasons[name],
                               'source': 'xml-correction/frozen/' + test_relative,
                               'line': node.lineno, 'end_line': node.end_lineno,
                               'method_body_sha256': digest(body.encode())})

# Nothing above executes candidate code or writes candidate source bytes.
C.mkdir(exist_ok=False)
private = C / 'private-final-apply'
private.mkdir(exist_ok=False)
for row in delta_rows:
    destination = C / 'frozen' / row['path']
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source_bytes[row['path']])
    os.chmod(destination, 0o644)

final_patch = copy.deepcopy(initial_patch)
for row in final_patch['changed_paths']:
    rel = row['path']
    if rel in CORRECTED:
        assert row['kind'] == 'addition'
        row['after_sha256'] = final_map[rel]['sha256']
        row['after_bytes'] = final_map[rel]['bytes']
        row['source'] = 'xml-correction/frozen/' + rel
    if row['kind'] == 'existing':
        before = (P / 'preimages' / rel).read_bytes()
        assert digest(before) == row['before_sha256']
        forward = before.decode()
        for fragment in row['fragments']:
            assert forward.count(fragment['before']) == 1
            forward = forward.replace(fragment['before'], fragment['after'], 1)
        assert forward.encode() == source_bytes[rel]
        inverse = forward
        for fragment in reversed(row['fragments']):
            assert inverse.count(fragment['after']) == 1
            inverse = inverse.replace(fragment['after'], fragment['before'], 1)
        assert inverse.encode() == before
        data = forward.encode()
        mode = int(row['worktree_reference_mode'], 8)
    else:
        data = (P / row['source']).read_bytes()
        assert digest(data) == row['after_sha256']
        mode = 0o644
    destination = private / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    os.chmod(destination, mode)
    assert metadata(destination) == final_map[rel]

python_paths = final_patch['parsed_python_only']
for rel in python_paths:
    ast.parse((private / rel).read_text(), filename='private-final/' + rel)
assert final_patch['existing_count'] == 6 and final_patch['addition_count'] == 12
assert final_patch['exact_fragment_count'] == 36
assert sum(len(row.get('fragments', [])) for row in final_patch['changed_paths']) == 36
assert [row for row in final_patch['changed_paths'] if row['kind'] == 'existing'] == [
    row for row in initial_patch['changed_paths'] if row['kind'] == 'existing']
assert all(metadata(R / rel) == final_map[rel] for rel in final_map)
assert all(metadata(P / name) == value for name, value in retained.items())

utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
final_patch.update({
    'initial_frozen_at_utc': initial_patch['frozen_at_utc'],
    'frozen_at_utc': utc,
    'supersedes_for_adoption_only': 'PATCH.json; original remains preserved as historical FIRST23 evidence',
    'final_finite_map': 'FINAL-FROZEN-MAP.json',
    'xml_correction_delta': 'xml-correction/DELTA.json',
    'scoped_saved_correction_results': 'XML-CORRECTION-FIRST8.json',
    'selection_review_timing': 'post-execution; independent pre-GREEN qualification not available',
    'accepted_test_executions_replayed_during_freeze': 0,
})
write_json(C / 'DELTA.json', {
    'schema_version': 1, 'initial_source_map': 'FROZEN-MAP.json',
    'final_source_map': 'FINAL-FROZEN-MAP.json', 'changed_path_count': 2,
    'correction_fragment_count': correction_fragment_count,
    'changed_paths': delta_rows,
    'scope': 'Two NEW owning XML source/control files only; unchanged original six existing/36 fragments and ten other additions.',
    'private_forward_inverse_exact': True, 'compiled_native_issue_closure_or_security_success_inferred': False,
})
write_json(P / 'FINAL-PATCH.json', final_patch)
write_json(P / 'FINAL-FROZEN-MAP.json', final_map)
write_json(C / 'SELECTIONS-AND-EXECUTION-ORDER.json', {
    'schema_version': 1, 'selection_review_timing': 'post-execution',
    'pre_GREEN_independent_qualification': False,
    'reason': 'Actual FIRST8 had already executed before the reviewer continuation requested pre-GREEN selection qualification. It is not replayed or relabeled.',
    'exact_saved_child_command': green8['command'], 'working_directory': str(R),
    'candidate_test_source': 'xml-correction/frozen/' + test_relative,
    'child_runner': 'Python standard library unittest through python3 -B -m unittest -v',
    'original_outer_capture_wrapper_source': 'Not retained as a separate file; only the saved exact child command, outputs, before/after maps and outer elapsed receipt are available. No wrapper is reconstructed as original execution evidence.',
    'new_methods': green8['new_methods'], 'directly_affected_methods': green8['directly_affected_methods'],
    'obligations': selection_rows, 'initial23_bodies_AST_identical': True,
    'initial23_total_replayed': False, 'accepted8_replayed_now': False,
    'actual_saved_results': {'methods': 8, 'passed': 8, 'exit_code': 0, 'suite_seconds': 0.080,
                            'outer_seconds': green8['outer_seconds'], 'held_finite_inputs': 43},
    'not_a_fresh_26_green_or_native_certificate': True,
})
write_json(C / 'PASSIVE-FINAL-ADOPTION-VALIDATION.json', {
    'utc': utc, 'private_path': str(private), 'combined_adoption_paths': 18,
    'existing_source_paths': 6, 'unchanged_existing_reversible_fragments': 36,
    'additions_explicit_0644': 12, 'corrected_addition_paths': 2,
    'correction_reversible_fragments': correction_fragment_count,
    'final_finite_inputs': 43, 'initial_finite_inputs': 43, 'only_two_XML_inputs_differ': True,
    'initial23_bodies_AST_identical': True, 'exact_private_forward_inverse_readback': True,
    'original_existing_modes_preserved_in_private_copy': True,
    'canonical_existing_mode_policy': 'Lead preserves canonical ROOT existing modes, never substitutes sparse capsule0600 modes; require all six original byte preimages. New twelve are0644.',
    'python_AST_paths_only_no_candidate_imports': python_paths,
    'retained_originals': retained,
    'RED14_original_receipt_output_digests': 'Not retained in that original receipt; present originals remain preserved and accepted review712 scope is reused, not re-executed or relabeled.',
    'review712_report': {'path': str(review_path), 'sha256': review_hash},
    'accepted_test_reruns_Git_ROOT_network_compiler_native_planner_controller_mutations': 0,
})
(C / 'INITIAL-README.md').write_bytes((P / 'README.md').read_bytes())
(P / 'FINAL-CONTROLS-DECLARED26-NOT-EXECUTED.txt').write_text('\n'.join(new_methods) + '\n')

seal_paths = [str(path.relative_to(P)) for path in C.rglob('*') if path.is_file()]
seal_paths += ['FINAL-PATCH.json', 'FINAL-FROZEN-MAP.json', 'FINAL-CONTROLS-DECLARED26-NOT-EXECUTED.txt', 'freeze-xml-correction.py']
write_json(C / 'FROZEN-CORRECTION-SEAL.json', {
    'schema_version': 1, 'utc': utc,
    'artifacts': {rel: metadata(P / rel) for rel in sorted(seal_paths)},
    'scope': 'Post-execution source/results custody seal; not pre-GREEN qualification, source execution, compiler/native acceptance or a global checkout map.',
})
print(json.dumps({'frozen_utc': utc, 'combined_adoption_paths': 18, 'existing_fragments': 36,
                  'new_0644': 12, 'corrected_paths': 2, 'correction_fragments': correction_fragment_count,
                  'final_finite_inputs': 43, 'accepted_test_replays': 0}, indent=2))
