#!/usr/bin/env python3
"""Read saved JavaFX originals/source only; never import or execute target code."""
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat

ROOT = Path('/root/projects/nativeCmpKit')
PACKET = Path(__file__).parent
INTAKE = Path('/root/nativecmpkit-source-proposals-20261104/lead-javafx-companion-intake-20261104')
ORIGINAL = Path('/root/nativecmpkit-native-reviews-20261101/agent606-javafx-ordinary-adoption-implementation')
CORRECTION = Path('/root/nativecmpkit-native-reviews-20261101/agent606-javafx-companion-provenance-correction')
checks, observations = [], {}
watched = {}


def need(ok, label):
    checks.append({'obligation': label, 'passed': bool(ok)})
    if not ok:
        raise ValueError(label)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def read(path):
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or path.is_symlink():
        raise ValueError('Unshared regular passive input required')
    if before.st_size > 2 * 1024 * 1024:
        raise ValueError('Passive input size exceeded')
    payload = path.read_bytes()
    after = path.lstat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError('Passive input changed during read')
    watched[str(path)] = {'bytes': len(payload), 'sha256': sha(payload)}
    return payload


def document(path):
    return json.loads(read(path))


def bindings(path):
    value = document(path)
    rows = value if isinstance(value, list) else value['bindings']
    if len({row['path'] for row in rows}) != len(rows):
        raise ValueError('Duplicate sparse binding path')
    return rows


def delivery(directory, expected_sha, expected_count):
    payload = read(directory / 'DELIVERY-MANIFEST.json')
    need(sha(payload) == expected_sha, directory.name + ': exact original delivery SHA')
    value = json.loads(payload)
    rows = value['files']
    need(value['file_count'] == len(rows) == expected_count and len({row['path'] for row in rows}) == expected_count,
         directory.name + ': complete unique delivery inventory')
    for row in rows:
        relative = PurePosixPath(row['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe delivery path')
        payload = read(directory / row['path'])
        need((len(payload), sha(payload)) == (row['bytes'], row['sha256']),
             directory.name + ': delivery-held ' + row['path'])
    return {'directory': str(directory), 'manifest_sha256': expected_sha, 'files_verified': expected_count,
            'unlisted_private_acquisitions_not_reacquired': True}


def chronology(directory, leaf, count, exit_code, unittest_seconds, wrapper_seconds, sparse_count):
    base = directory / leaf
    receipt = document(base / 'execution.json')
    stdout, stderr = read(base / 'stdout'), read(base / 'stderr')
    before, after = read(base / 'source-bindings-before.json'), read(base / 'source-bindings-after.json')
    rows = json.loads(before)
    rows = rows if isinstance(rows, list) else rows['bindings']
    need(before == after and len(rows) == sparse_count, leaf + ': exact held original sparse maps')
    need(receipt['exit_code'] == exit_code and receipt.get('bindings_held', receipt.get('held_inputs')) is True,
         leaf + ': original terminal exit and held-input receipt')
    elapsed = receipt.get('elapsed_seconds', receipt.get('wrapper_elapsed_seconds'))
    need(elapsed == wrapper_seconds, leaf + ': exact original wrapper time')
    text = stderr.decode('utf-8')
    summary = re.findall(r'^Ran (\d+) tests in ([0-9.]+)s$', text, re.M)
    need(summary == [(str(count), unittest_seconds)] and stdout == b'', leaf + ': original unittest count/time and empty stdout')
    selected = receipt['command'][5:]
    ids = re.findall(r'^(test_\w+) \((test_[^() ]+)\)(?: \.\.\. ok| \.\.\. )$', text, re.M)
    method_ids = [identity for _, identity in ids]
    need(len(method_ids) == len(set(method_ids)) == count, leaf + ': exact distinct logged method identities')
    if len(selected) == 1 and '.' not in selected[0]:
        need(all(identity.startswith(selected[0] + '.') for identity in method_ids), leaf + ': module selection owns all logged methods')
    else:
        need(set(selected) == set(method_ids) and len(selected) == count, leaf + ': selected IDs equal logged IDs')
    tamper_failures = re.findall(r'^FAIL: (test_\w+) .*\(mode=\'(module|pom)\', configuration=\'(\w+)\', module=\'(\w+)\'\)$', text, re.M)
    if exit_code:
        need(text.rstrip().endswith('FAILED (failures=80)') and len(tamper_failures) == len(set(tamper_failures)) == 80 and
             text.count('AssertionError: StageError not raised') == 80 and '\nERROR:' not in text,
             leaf + ': retained80 refreshed-byte admission failures, not loader/native errors')
    else:
        need(text.rstrip().endswith('OK') and not tamper_failures and '\nERROR:' not in text,
             leaf + ': exact original green summary without skips/failures/errors')
    return {'directory': leaf, 'method_count': count, 'original_exit_code': exit_code,
            'unittest_seconds': unittest_seconds, 'wrapper_seconds': elapsed,
            'sparse_inputs': sparse_count, 'original_receipt_sha256': sha(read(base / 'execution.json')),
            'held_sparse_map_sha256': sha(before), 'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr),
            'selected_method_ids': method_ids, 'tamper_subcase_failures': len(tamper_failures),
            'target_execution_replayed': False}


def main():
    recipe_path = INTAKE / 'CURRENT2EE-TWELVE-NEW-SOURCE-ADOPTION-RECIPE.json'
    recipe = document(recipe_path)
    need(sha(read(recipe_path)) == 'a27e4de4f217af01269d41d9bd45938b25fe0036afbfa04489f2d910782faf3f',
         'Exact lead current2ee12-source recipe authority')
    lead_checks = INTAKE / 'PASSIVE-ORIGINAL-SOURCE-CHECKS.json'
    need(sha(read(lead_checks)) == '94040ff7d6cb57d4f6c78a6b222639849ce11afc1cd16275240f0d47abf51133',
         'Exact lead original/source custody record, independently checked below')
    observations['deliveries'] = [
        delivery(ORIGINAL, recipe['original_delivery_sha256'], 36),
        delivery(CORRECTION, recipe['correction_delivery_sha256'], 37)]
    additions = {}
    for relative, row in recipe['source_files'].items():
        source, destination = Path(row['source_path']), ROOT / relative
        payload = read(source)
        present = destination.exists() or destination.is_symlink()
        need(not present, relative + ': current bounded ROOT destination absent; no overwrite')
        need((len(payload), sha(payload), f'{stat.S_IMODE(source.stat().st_mode):04o}') ==
             (row['bytes'], row['sha256'], row['expected_mode']), relative + ': exact addition bytes/SHA/mode')
        additions[relative] = {'source_path': str(source), 'bytes': len(payload), 'sha256': sha(payload),
                               'mode': '0644', 'ROOT_preimage': None, 'ROOT_absent': True, 'origin': row['origin']}
    need(len(additions) == 12 and sum(row['bytes'] for row in additions.values()) == 161381,
         'Exact twelve-source union161381B, currently absent and unadopted')
    observations['exact12'] = additions
    refs = {}
    for relative, expected in recipe['ROOT_reference_hashes'].items():
        payload = read(ROOT / relative)
        refs[relative] = {'lead_current2ee_sha256': expected, 'observed_sha256': sha(payload), 'bytes': len(payload),
                          'matches_saved_current2ee_reference': sha(payload) == expected}
    observations['bounded_ROOT_reference_readbacks'] = refs
    observations['reference_drift'] = [name for name, row in refs.items() if not row['matches_saved_current2ee_reference']]
    observations['root_identity'] = {'lead_saved_head': recipe['expected_root_head'], 'lead_saved_tree': recipe['expected_root_tree'],
                                     'current_Git_queried': False, 'current_HEAD_match_claimed': False,
                                     'prospective_context': 'current2ee plus lead-controlled707 producer/Camera/Android completion; not yet adopted'}

    records = document(CORRECTION / 'SOURCE-DERIVATIVES.json')
    derivative_rows, total = [], 0
    for row in records['fragments']:
        predecessor = read(ORIGINAL / 'proposed' / row['path']).decode('utf-8')
        postimage = read(CORRECTION / 'proposed' / row['path']).decode('utf-8')
        need((sha(predecessor.encode()), sha(postimage.encode())) == (row['predecessor_sha256'], row['postimage_sha256']),
             row['path'] + ': exact derivative whole-file predecessor/postimage')
        prior_lines, next_lines = predecessor.splitlines(keepends=True), postimage.splitlines(keepends=True)
        for fragment in row['fragments']:
            old, new = fragment['before'], fragment['after']
            need((sha(old.encode()), sha(new.encode())) == (fragment['before_sha256'], fragment['after_sha256']) and
                 ''.join(prior_lines[fragment['old_start_line'] - 1:fragment['old_end_line_exclusive'] - 1]) == old and
                 ''.join(next_lines[fragment['new_start_line'] - 1:fragment['new_end_line_exclusive'] - 1]) == new,
                 row['path'] + ': exact owning inverse fragment' + str(total + 1))
            total += 1
        forward, inverse = prior_lines[:], next_lines[:]
        for fragment in reversed(row['fragments']):
            forward[fragment['old_start_line'] - 1:fragment['old_end_line_exclusive'] - 1] = fragment['after'].splitlines(keepends=True)
            inverse[fragment['new_start_line'] - 1:fragment['new_end_line_exclusive'] - 1] = fragment['before'].splitlines(keepends=True)
        need(''.join(forward) == postimage and ''.join(inverse) == predecessor, row['path'] + ': exact full forward and inverse composition')
        derivative_rows.append({'path': row['path'], 'fragments': len(row['fragments']),
                                'predecessor_sha256': row['predecessor_sha256'], 'postimage_sha256': row['postimage_sha256']})
    need(len(derivative_rows) == 5 and total == 33, 'Exact5 derivatives/33 fragments, no unrelated ROOT/hash-pin rewrite')
    observations['derivatives'] = derivative_rows

    original_chronology = [
        chronology(ORIGINAL, 'new35-first', 35, 0, '0.447', 0.6681959750130773, 11),
        chronology(ORIGINAL, 'new6-provenance', 6, 0, '0.104', 0.36849781195633113, 11),
        chronology(ORIGINAL, 'new8-fixture-source', 8, 0, '0.002', 0.16652312991209328, 17),
        chronology(ORIGINAL, 'new2-object-refusal', 2, 0, '0.021', 0.21812199288979173, 17)]
    correction_chronology = [
        chronology(CORRECTION, 'new2-gap-red', 2, 1, '1.075', 1.2505045339930803, 94),
        chronology(CORRECTION, 'new2-onlyfailed-green', 2, 0, '0.509', 0.6764159169979393, 95),
        chronology(CORRECTION, 'new14-companion-owning', 14, 0, '0.305', 0.4965894240885973, 96)]
    ids51 = [identity for row in original_chronology for identity in row['selected_method_ids']]
    need(len(ids51) == len(set(ids51)) == 51, 'FIRST51 are separate NEW35+6+8+2, not a cumulative fresh51 execution')
    need(correction_chronology[0]['selected_method_ids'] == correction_chronology[1]['selected_method_ids'] and
         not set(correction_chronology[2]['selected_method_ids']) & set(correction_chronology[1]['selected_method_ids']) and
         not set(ids51) & {identity for row in correction_chronology for identity in row['selected_method_ids']},
         'OnlyfailedNEW2 matches RED2; NEW14 distinct; original51 excluded, not fresh67')
    observations['original51_chronology'] = original_chronology
    observations['correction_chronology'] = correction_chronology

    reuse = document(CORRECTION / 'NEW2-FINAL-SOURCE-REUSE.json')
    prior = read(CORRECTION / 'retained-executed-sources/new2-model.py').decode('utf-8')
    final = read(CORRECTION / 'proposed/tests/dependency/javafx-http2-cancellation/test_official_companion_provenance.py').decode('utf-8')
    need((sha(prior.encode()), sha(final.encode())) == (reuse['original_new2_model_source_sha256'], reuse['final_model_source_sha256']),
         'NEW2 exact retained executed source and final source identities')
    first, last = prior.splitlines(keepends=True), final.splitlines(keepends=True)
    changed = [row for row in difflib.SequenceMatcher(a=first, b=last, autojunk=False).get_opcodes() if row[0] != 'equal']
    need(len(changed) == 2 and all(row[0] == 'insert' for row in changed) and
         ''.join(last[changed[0][3]:changed[0][4]]) == 'import json\n', 'NEW2-to-final only JSON import and method append, no earlier byte edit')
    insert = ''.join(last[changed[1][3]:changed[1][4]])
    need(len(re.findall(r'^    def test_new_', insert, re.M)) == 8, 'NEW2 retained source gains exactly NEW8 model methods')
    restored = last[:]
    for _, _, _, begin, end in reversed(changed):
        restored[begin:end] = []
    need(''.join(restored) == prior, 'NEW2 final source reconstructs original executed bytes exactly without replay')
    for name in reuse['unchanged_fragments']:
        def segment(source):
            node = next(node for node in ast.walk(ast.parse(source)) if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == name)
            return '\n'.join(source.splitlines()[node.lineno - 1:node.end_lineno])
        need(segment(prior) == segment(final), 'NEW2 helper/body passive AST equality: ' + name)
    observations['NEW2_final_source_reuse'] = {'original_model_sha256': sha(prior.encode()), 'final_model_sha256': sha(final.encode()),
                                              'retained2_helpers_and_bodies_unchanged': True, 'only_NEW8_and_JSON_import_appended': True,
                                              'fresh_execution': False}

    supplement = document(CORRECTION / 'proposed/tests/dependency/javafx-http2-cancellation/official-companion-supplement.json')
    pin_path = Path('/root/nativecmpkit-source-proposals-20261104/javafx-official-companion-pins699/EXPECTED-COMPANION-PINS699.json')
    pins_payload = read(pin_path)
    need(sha(pins_payload) == supplement['official_acquisition_expected_pins_sha256'], 'Independent699 exact metadata-only pin authority')
    pins = json.loads(pins_payload)['pins']
    matched = 0
    for category, name in (('classified', 'classified_swing'), ('generic', 'generic')):
        for key, row in supplement[name].items():
            need({field: row[field] for field in ('file', 'bytes', 'sha256', 'url')} ==
                 {field: pins[category][key][field] for field in ('file', 'bytes', 'sha256', 'url')},
                 '699 supplemental metadata exact filename/length/digest/official origin: ' + category + '/' + key)
            matched += 1
    need(matched == 10 and supplement['original_artifacts_sha256'] == recipe['ROOT_reference_hashes']['tests/dependency/javafx-http2-cancellation/artifacts.json'],
         'Ten reviewed supplemental pins preserve original four-companion document and candidate14 inputs')
    observations['supplemental_metadata'] = {'matching_pins': matched, 'classified_companion_pin_count': 25,
                                           'generic_companion_pin_count': 5, 'real_JAR_reads': 0,
                                           'not_security_signing_legal_native_consumer_clearance': True}
    for relative, row in additions.items():
        if relative.endswith('.py'):
            ast.parse(read(row['source_path']), filename=relative)
    need(True, 'All six prospective Python sources AST-parsed passively; no target imports or tests')
    # Review-time holds only: these are not executable invocation maps or a Git freeze.
    hold = {path: {'bytes': len(payload), 'sha256': sha(payload)} for path in watched for payload in [Path(path).read_bytes()]}
    need(hold == watched, 'All actually read sparse source/original inputs held during this passive review')
    return {'schema': 'nativecmpkit-javafx-passive-intake658-v1', 'outcome': 'passed',
            'utc': datetime.now(timezone.utc).isoformat(), 'check_count': len(checks), 'checks': checks,
            'observations': observations, 'sparse_read_input_count': len(watched), 'sparse_reads_held': True,
            'inputs': watched, 'ROOT_writes': 0, 'target_imports': 0, 'new_tests_builds_stages_native_dispatches': 0,
            'scope': 'Exact retained originals/source/chronology only; current Git identity not queried; unadopted prospective current2ee/707 route; no new execution, native, consumer, publication, security/legal/API-ABI or #64 closure'}


try:
    result = main()
except (ValueError, OSError, KeyError, TypeError, SyntaxError) as error:
    result = {'schema': 'nativecmpkit-javafx-passive-intake658-v1', 'outcome': 'refused',
              'utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
              'observations': observations, 'refusal': str(error), 'target_execution_replayed': False}
with (PACKET / 'PASSIVE-INTAKE658.json').open('x') as output:
    json.dump(result, output, indent=2, sort_keys=True)
    output.write('\n')
print(json.dumps({key: result[key] for key in ('outcome', 'check_count', 'refusal') if key in result}))
