#!/usr/bin/env python3
"""External successor only: exact retained-report consumed-byte custody correction."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat

ORIGINAL = Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-current2ee707-route658')
SUCCESSOR = Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-report-custody-successor658')
REFUSAL = Path('/root/nativecmpkit-source-proposals-20261104/producer-budget-review705/windows-ordinary-consumer658/REPORT-BYTE-CUSTODY-REFUSAL705.json')
checks = []


def check(value, label):
    checks.append({'check': label, 'passed': bool(value)})
    if not value:
        raise ValueError(label)


def read(path):
    path = Path(path)
    before = path.stat(follow_symlinks=False)
    check(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_nlink == 1 and before.st_size < 4 * 1024**2,
          'Bounded unshared named predecessor input: ' + str(path))
    payload = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    check((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
          (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Stable named predecessor read: ' + str(path))
    return payload


def row(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, raw):
    path = SUCCESSOR / name
    check(path.is_relative_to(SUCCESSOR) and not path.is_symlink(), 'Confined successor evidence/source only: ' + name)
    if path.exists():
        check(read(path) == raw, 'Reuse exact already-written passive preparation prefix only: ' + name)
        return
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('xb') as output:
        output.write(raw)
    path.chmod(0o600)


def write_json(name, value):
    write(name, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def apply(raw, before, after, label, fragments):
    check(raw.count(before.encode()) == 1, 'One exact source transition: ' + label)
    postimage = raw.replace(before.encode(), after.encode(), 1)
    check(postimage.count(after.encode()) == 1 and postimage.replace(after.encode(), before.encode(), 1) == raw,
          'Exact local transition inverse: ' + label)
    fragments.append({'kind': 'replace-exact-once', 'scope': label, 'preimage': before, 'postimage': after})
    return postimage


def function_rows(raw):
    tree = ast.parse(raw.decode())
    result = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            result[node.name] = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
        elif isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, ast.FunctionDef):
                    result[node.name + '.' + method.name] = hashlib.sha256(ast.dump(method, include_attributes=False).encode()).hexdigest()
    return result


check(SUCCESSOR.is_dir() and not SUCCESSOR.is_symlink() and not (SUCCESSOR / 'proposed').exists(),
      'Exact owned partial preparation only; no canonical postimages/execution yet')
expected_partial = {'prepare-javafx-report-custody-successor658.py', 'ORIGINAL-AUTHORITIES658.json',
                    'PREPARATION-EXACT-PATH-FRAGMENT-REFUSAL658.json',
                    'retained/predecessor/.github/workflows/javafx-library-candidate.yml',
                    'retained/predecessor/scripts/ci/javafx_ordinary_maven_consumer.py',
                    'retained/predecessor/scripts/ci/test_javafx_ordinary_maven_route.py',
                    'retained/predecessor/docs/testing/javafx-ordinary-windows-route.md'}
check({path.relative_to(SUCCESSOR).as_posix() for path in SUCCESSOR.rglob('*') if path.is_file()} == expected_partial,
      'Exact seven-file owned preparation prefix and original refusal retained')
original_seal_raw = read(ORIGINAL / 'PACKET-SEAL658.json')
check(row(original_seal_raw)['sha256'] == '52b7415a32687bc4dc9838057cca8ab3dee45e11c2dc43cead1b5ad80bd3df34', 'Exact frozen original full packet seal held')
original_seal = json.loads(original_seal_raw)
original_recipe_raw = read(ORIGINAL / 'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json')
check(row(original_recipe_raw)['sha256'] == 'adf80ea4a7ae3aa0d4acad299b8efe4ffd2444aca6a797694a2689b363072b32', 'Exact original current16 recipe held')
original_recipe = json.loads(original_recipe_raw)
refusal_raw = read(REFUSAL)
check(row(refusal_raw) == {'bytes': 2642, 'sha256': '6eeade9add7f714605fbc0c0bd6fc158aac29199df4b7cb1381416f3b69c05a3'},
      'Independent705 original consumed-report-byte custody refusal held')
json.loads(refusal_raw)
SUCCESSOR.mkdir(mode=0o700, exist_ok=True)
write('prepare-javafx-report-custody-successor-recovery658.py', read(Path(__file__).resolve()))
write_json('ORIGINAL-AUTHORITIES658.json', {
    'schema': 'nativecmpkit-javafx-report-custody-original-authorities658-v1',
    'original_packet': str(ORIGINAL), 'original_packet_seal': {**row(original_seal_raw), 'path': str(ORIGINAL / 'PACKET-SEAL658.json')},
    'original_current16_recipe': {**row(original_recipe_raw), 'path': str(ORIGINAL / 'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json')},
    'independent705_refusal': {**row(refusal_raw), 'path': str(REFUSAL)},
    'ROOT_worktree_Git_network_build_stage_native_or_original_packet_writes': 0,
    'scope': 'Confirmed separate mutable observation/verifier report reads had no input-report digest gate; exact NEW-driver source successor only'})

sources = {}
for name in ('.github/workflows/javafx-library-candidate.yml', 'scripts/ci/javafx_ordinary_maven_consumer.py',
             'scripts/ci/test_javafx_ordinary_maven_route.py', 'docs/testing/javafx-ordinary-windows-route.md'):
    raw = read(ORIGINAL / 'proposed' / name)
    check(row(raw) == {key: original_recipe['source_files'][name][key] for key in ('bytes', 'sha256')}, 'Exact original route predecessor held: ' + name)
    sources[name] = raw
    write('retained/predecessor/' + name, raw)

controller_name = 'scripts/ci/javafx_ordinary_maven_consumer.py'
controller_before = sources[controller_name]
controller = controller_before
driver_fragments = []
helper_before = "\n\ndef fresh_resolution(consumer, output, mode, start, end, private_repository, invoke):\n"
helper_after = """

def resolution_report_held(custody):
    path = Path(custody['path'])
    before = path.stat(follow_symlinks=False)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    need(not path.is_symlink() and before.st_nlink == 1 and identity == tuple(custody['file_identity']),
         'Replaced or changed retained verifier input refused; preserve all report evidence')
    payload = read(path)
    after = path.stat(follow_symlinks=False)
    need((after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) == identity and
         len(payload) == custody['bytes'] and hashlib.sha256(payload).hexdigest() == custody['sha256'],
         'Retained verifier input bytes/identity must hold; no changed report graph acceptance')
    return True


def retained_resolution(path, saved, start, end):
    before = path.stat(follow_symlinks=False)
    payload = read(path)
    after = path.stat(follow_symlinks=False)
    source_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    need(source_identity == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) and
         start - 2_000_000_000 <= before.st_mtime_ns <= end + 2_000_000_000,
         'Exactly captured original resolution report identity must be fresh and held')
    saved.parent.mkdir(parents=True, exist_ok=True)
    with saved.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        owned = os.fstat(stream.fileno())
    custody = {'path': str(saved), 'source_path': str(path), 'bytes': len(payload),
               'sha256': hashlib.sha256(payload).hexdigest(), 'source_identity': list(source_identity),
               'file_identity': [owned.st_dev, owned.st_ino, owned.st_size, owned.st_mtime_ns, owned.st_ctime_ns]}

    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'Duplicate resolution JSON key refused')
            result[key] = value
        return result

    def finite(_):
        raise packaged.EvidenceError('Nonfinite resolution JSON number refused')

    observed = json.loads(payload, object_pairs_hook=unique, parse_constant=finite)
    need(isinstance(observed, dict), 'Original resolution JSON object required')
    need(resolution_report_held(custody), 'Initial retained original observation must hold before verifier work')
    return observed, custody


def fresh_resolution(consumer, output, mode, start, end, private_repository, invoke, resolution_reports):
"""
controller = apply(controller, helper_before, helper_after, 'NEW retained raw/strict parsed payload and byte+file-identity helper scopes', driver_fragments)
fresh_before = """    need(start - 2_000_000_000 <= path.stat().st_mtime_ns <= end + 2_000_000_000, 'Fresh actual ordinary resolution required')
    observed = packaged.read_json(path)
    write(output / f'{mode}/resolution.json', observed)
    invoke('bind-resolution-' + mode,
           [sys.executable, '-B', str(ROOT / DEPENDENCY / 'private_web_resolution.py'), '--repository', str(private_repository), '--resolution', str(path)],
"""
fresh_after = """    observed, custody = retained_resolution(path, output / f'{mode}/resolution.json', start, end)
    resolution_reports.append(custody)
    invoke('bind-resolution-' + mode,
           [sys.executable, '-B', str(ROOT / DEPENDENCY / 'private_web_resolution.py'), '--repository', str(private_repository), '--resolution', custody['path']],
"""
controller = apply(controller, fresh_before, fresh_after, 'Each pre-native verifier consumes only its exact retained observation payload', driver_fragments)
fresh_tail_before = """    bound_resolution(verifier, mode)
    write(output / mode / 'resolution-verification.json', verifier)
    return observed
"""
fresh_tail_after = """    bound_resolution(verifier, mode)
    need(resolution_report_held(custody), 'Exact retained verifier input must hold before this graph can be returned')
    write(output / mode / 'resolution-verification.json', verifier)
    write(output / f'{mode}/resolution-input-custody.json', custody)
    return observed
"""
controller = apply(controller, fresh_tail_before, fresh_tail_after, 'Pre-native returned graph gated by exact retained verifier input custody', driver_fragments)
controller = apply(controller, "    producer_environment, private_stage_sha = None, None\n", "    producer_environment, private_stage_sha = None, None\n    resolution_reports = []\n",
                   'One owned retained-report custody list persists through finalization', driver_fragments)
controller = apply(controller, "            graphs[mode] = fresh_resolution(consumer, output, mode, start, end, private_repository, invoke)\n",
                   "            graphs[mode] = fresh_resolution(consumer, output, mode, start, end, private_repository, invoke, resolution_reports)\n",
                   'Both independently admitted modes register exact retained verifier inputs', driver_fragments)
controller = apply(controller, "        phase = 'complete-four-classpath-graph-comparison'\n        signatures = {mode: graph_signature(graphs[mode]) for mode in MODES}\n",
                   "        phase = 'complete-four-classpath-graph-comparison'\n        need(all(resolution_report_held(custody) for custody in resolution_reports),\n             'Every exact retained verifier input must hold before complete graph comparison and NEW native request')\n        signatures = {mode: graph_signature(graphs[mode]) for mode in MODES}\n",
                   'All admitted verifier input bytes/identities hold before complete signatures/native request', driver_fragments)
post_before = """        need(start - 2_000_000_000 <= native_resolution_path.stat().st_mtime_ns <= end + 2_000_000_000,
             'Fresh native-task module graph observation required')
        current = packaged.read_json(native_resolution_path)
        write(output / 'native/resolution.json', current)
        need(current.get('metadata_mode') == 'module' and graph_signature(current) == signatures['module'],
             'Native task must hold the exact independently admitted module byte graph')
        invoke('post-native-production-pin-graph-binding',
               [sys.executable, '-B', str(ROOT / DEPENDENCY / 'private_web_resolution.py'), '--repository', str(private_repository),
                '--resolution', str(native_resolution_path)],
               output / 'native/resolution-verifier.log', 180, producer_environment)
        native_binding = json.loads(read(output / 'native/resolution-verifier.log').decode('utf-8'))
        bound_resolution(native_binding, 'module')
        write(output / 'native/resolution-verification.json', native_binding)
"""
post_after = """        current, native_custody = retained_resolution(native_resolution_path, output / 'native/resolution.json', start, end)
        resolution_reports.append(native_custody)
        invoke('post-native-production-pin-graph-binding',
               [sys.executable, '-B', str(ROOT / DEPENDENCY / 'private_web_resolution.py'), '--repository', str(private_repository),
                '--resolution', native_custody['path']],
               output / 'native/resolution-verifier.log', 180, producer_environment)
        native_binding = json.loads(read(output / 'native/resolution-verifier.log').decode('utf-8'))
        bound_resolution(native_binding, 'module')
        need(resolution_report_held(native_custody), 'Exact post-native verifier input must hold before graph/native reuse acceptance')
        need(current.get('metadata_mode') == 'module' and graph_signature(current) == signatures['module'],
             'Native task must hold the exact independently admitted module byte graph')
        write(output / 'native/resolution-verification.json', native_binding)
        write(output / 'native/resolution-input-custody.json', native_custody)
"""
controller = apply(controller, post_before, post_after, 'Post-native graph consumes exactly retained independently verified payload before reuse', driver_fragments)
final_before = "        if runtime is not None:\n            try:\n                after_runtime = runtime_context.capture(expected_arch='x64', android_package='android-37.0', require_clean=True)\n"
final_after = """        if resolution_reports:
            try:
                record['resolution_report_count'] = len(resolution_reports)
                record['resolution_reports_held'] = all(resolution_report_held(custody) for custody in resolution_reports)
                write(output / 'resolution-report-custody.json', {'inputs': resolution_reports, 'held': record['resolution_reports_held']})
                held.append(record['resolution_reports_held'])
            except (packaged.EvidenceError, OSError, ValueError):
                record['resolution_reports_held'] = False
                held.append(False)
        if runtime is not None:
            try:
                after_runtime = runtime_context.capture(expected_arch='x64', android_package='android-37.0', require_clean=True)
"""
controller = apply(controller, final_before, final_after, 'Finally rejects changed retained verifier input and preserves originals/foreign files', driver_fragments)
ast.parse(controller.decode())
old_functions, new_functions = function_rows(controller_before), function_rows(controller)
check({name for name in old_functions if old_functions[name] != new_functions[name]} == {'fresh_resolution', 'run'},
      'Only existing fresh_resolution/run ASTs changed; no old native/XML/helper/other driver function change')
check(set(new_functions) - set(old_functions) == {'resolution_report_held', 'retained_resolution'}, 'Only two NEW bounded report-custody helper functions')

control_name = 'scripts/ci/test_javafx_ordinary_maven_route.py'
control_before = sources[control_name]
control, control_fragments = control_before, []
owning_before = """        self.assertEqual(len(post_binding), 1)
        self.assertGreater(post_binding[0].lineno, native.lineno)
        self.assertEqual(literal(post_binding[0].args[1]), 'module')
"""
owning_after = """        self.assertEqual(len(post_binding), 1)
        self.assertGreater(post_binding[0].lineno, native.lineno)
        self.assertEqual(literal(post_binding[0].args[1]), 'module')
        self.assertEqual([ast.unparse(arg) for arg in calls(mode_loops[0], 'fresh_resolution')[0].args],
                         ['consumer', 'output', 'mode', 'start', 'end', 'private_repository', 'invoke', 'resolution_reports'])
        expected_report_gate = ast.parse('all(resolution_report_held(custody) for custody in resolution_reports)', mode='eval').body
        report_gate = [node for node in calls(run, 'need') if ast.dump(node.args[0], include_attributes=False) ==
                       ast.dump(expected_report_gate, include_attributes=False)]
        self.assertEqual(len(report_gate), 1)
        signatures = assigned(run, 'signatures')
        self.assertLess(report_gate[0].lineno, signatures.lineno)
        self.assertLess(report_gate[0].lineno, native.lineno)
        post_custody = calls(run, 'resolution_report_held')
        self.assertTrue(any(ast.unparse(node.args[0]) == 'native_custody' and
                            post_binding[0].lineno < node.lineno < calls(run, 'graph_signature')[-1].lineno
                            for node in post_custody))
"""
control = apply(control, owning_before, owning_after, 'Changed owning complete-graph method binds both mode/post-native retained-input gates', control_fragments)
new_before = "\n\nif __name__ == '__main__':\n    unittest.main(verbosity=2)\n"
new_after = """

    def test_new_retained_resolution_uses_one_raw_payload_for_exclusive_report_and_strict_observation(self):
        capture = self.functions['retained_resolution']
        self.assertEqual(len(calls(capture, 'read')), 1)
        self.assertEqual(ast.unparse(calls(capture, 'read')[0].args[0]), 'path')
        self.assertEqual(len(calls(capture, 'saved.open')), 1)
        self.assertEqual(literal(calls(capture, 'saved.open')[0].args[0]), 'xb')
        self.assertEqual(ast.unparse(calls(capture, 'stream.write')[0].args[0]), 'payload')
        self.assertLess(calls(capture, 'stream.write')[0].lineno, calls(capture, 'stream.flush')[0].lineno)
        self.assertLess(calls(capture, 'stream.flush')[0].lineno, calls(capture, 'os.fstat')[0].lineno)
        parsed = calls(capture, 'json.loads')
        self.assertEqual(len(parsed), 1)
        self.assertEqual(ast.unparse(parsed[0].args[0]), 'payload')
        self.assertEqual({keyword.arg: ast.unparse(keyword.value) for keyword in parsed[0].keywords},
                         {'object_pairs_hook': 'unique', 'parse_constant': 'finite'})
        nested = {node.name: node for node in capture.body if isinstance(node, ast.FunctionDef)}
        self.assertEqual(ast.unparse(calls(nested['unique'], 'need')[0].args[0]), 'key not in result')
        self.assertTrue(any(isinstance(node, ast.Raise) for node in ast.walk(nested['finite'])))
        predicate = ast.unparse(calls(capture, 'need')[0].args[0])
        self.assertIn('source_identity == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)', predicate)
        self.assertIn('start - 2000000000 <= before.st_mtime_ns <= end + 2000000000', predicate)
        custody = assigned(capture, 'custody')
        entries = dict(zip((literal(key) for key in custody.keys), custody.values))
        self.assertEqual(ast.unparse(entries['path']), 'str(saved)')
        self.assertEqual(ast.unparse(entries['bytes']), 'len(payload)')
        self.assertEqual(ast.unparse(entries['sha256']), 'hashlib.sha256(payload).hexdigest()')
        self.assertEqual(ast.unparse(entries['file_identity']),
                         '[owned.st_dev, owned.st_ino, owned.st_size, owned.st_mtime_ns, owned.st_ctime_ns]')
        self.assertEqual(ast.unparse([node for node in capture.body if isinstance(node, ast.Return)][0].value), 'observed, custody')
        self.assertFalse(calls(capture, 'packaged.read_json') or calls(capture, 'write') or calls(capture, 'json.dumps'))

    def test_new_each_verifier_consumes_only_held_retained_report_and_finalization_preserves_changes(self):
        fresh = self.functions['fresh_resolution']
        captured = calls(fresh, 'retained_resolution')
        self.assertEqual(len(captured), 1)
        self.assertEqual([ast.unparse(arg) for arg in captured[0].args],
                         ['path', "output / f'{mode}/resolution.json'", 'start', 'end'])
        invoke = calls(fresh, 'invoke')[0]
        self.assertEqual(ast.unparse(invoke.args[1].elts[-1]), "custody['path']")
        self.assertLess(calls(fresh, 'resolution_reports.append')[0].lineno, invoke.lineno)
        self.assertLess(calls(fresh, 'bound_resolution')[0].lineno, calls(fresh, 'resolution_report_held')[0].lineno)
        self.assertLess(calls(fresh, 'resolution_report_held')[0].lineno,
                        [node for node in fresh.body if isinstance(node, ast.Return)][0].lineno)
        run = self.functions['run']
        post_capture = calls(run, 'retained_resolution')
        self.assertEqual(len(post_capture), 1)
        self.assertEqual([ast.unparse(arg) for arg in post_capture[0].args],
                         ['native_resolution_path', "output / 'native/resolution.json'", 'start', 'end'])
        post = [node for node in calls(run, 'invoke') if node.args and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == 'post-native-production-pin-graph-binding']
        self.assertEqual(len(post), 1)
        self.assertEqual(ast.unparse(post[0].args[1].elts[-1]), "native_custody['path']")
        self.assertFalse(calls(fresh, 'packaged.read_json'))
        guard = self.functions['resolution_report_held']
        self.assertEqual(ast.unparse(assigned(guard, 'path')), "Path(custody['path'])")
        first = ast.unparse(calls(guard, 'need')[0].args[0])
        self.assertIn('not path.is_symlink()', first)
        self.assertIn('before.st_nlink == 1', first)
        self.assertIn("identity == tuple(custody['file_identity'])", first)
        last = ast.unparse(calls(guard, 'need')[1].args[0])
        for required in ('(after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) == identity',
                         "len(payload) == custody['bytes']", "hashlib.sha256(payload).hexdigest() == custody['sha256']"):
            self.assertIn(required, last)
        self.assertLess(calls(guard, 'need')[0].lineno, calls(guard, 'read')[0].lineno)
        self.assertLess(calls(guard, 'read')[0].lineno, calls(guard, 'need')[1].lineno)
        for prohibited in ('path.unlink', 'path.write_bytes', 'path.write_text', 'path.rename', 'os.remove', 'os.replace'):
            self.assertFalse(calls(guard, prohibited))
        final = [node for node in ast.walk(run) if isinstance(node, ast.Try) and node.finalbody]
        self.assertEqual(len(final), 1)
        final_tree = ast.Module(body=final[0].finalbody, type_ignores=[])
        assignments = [node for node in ast.walk(final_tree) if isinstance(node, ast.Assign)
                       and any(ast.unparse(target) == "record['resolution_reports_held']" for target in node.targets)]
        self.assertEqual(len(assignments), 2)
        self.assertTrue(any(isinstance(node.value, ast.Constant) and node.value.value is False for node in assignments))
        expected_final_gate = ast.parse('all(resolution_report_held(custody) for custody in resolution_reports)', mode='eval').body
        self.assertTrue(any(ast.dump(node.value, include_attributes=False) == ast.dump(expected_final_gate, include_attributes=False)
                            for node in assignments))
        self.assertTrue(any(ast.unparse(node.args[0]) == "record['resolution_reports_held']" for node in calls(final_tree, 'held.append')))
        self.assertIn("record['passed'] = record['passed'] and bool(held) and all(held)", ast.unparse(final_tree))


if __name__ == '__main__':
    unittest.main(verbosity=2)
"""
control = apply(control, new_before, new_after, 'NEW raw-capture and verifier/final-custody AST-only source methods', control_fragments)
ast.parse(control.decode())
old_controls, new_controls = function_rows(control_before), function_rows(control)
owning = 'JavafxOrdinaryMavenRouteSourceTests.test_both_complete_graphs_bind_before_single_new_native_request'
new_method_names = {
    'JavafxOrdinaryMavenRouteSourceTests.test_new_retained_resolution_uses_one_raw_payload_for_exclusive_report_and_strict_observation',
    'JavafxOrdinaryMavenRouteSourceTests.test_new_each_verifier_consumes_only_held_retained_report_and_finalization_preserves_changes',
}
check({name for name in old_controls if old_controls[name] != new_controls[name]} == {owning}, 'Only existing owning graph method AST changed')
check(set(new_controls) - set(old_controls) == new_method_names, 'Exactly two NEW AST/text source methods; no old population replay')
selected = [owning, *sorted(new_method_names)]
sources[controller_name], sources[control_name] = controller, control
for name, raw in sources.items():
    write('proposed/' + name, raw)
reconstruction = controller
for fragment in reversed(driver_fragments):
    reconstruction = reconstruction.replace(fragment['postimage'].encode(), fragment['preimage'].encode(), 1)
check(reconstruction == controller_before, 'Complete exact NEW-driver fragment inverse recovers frozen predecessor')
reconstruction = control
for fragment in reversed(control_fragments):
    reconstruction = reconstruction.replace(fragment['postimage'].encode(), fragment['preimage'].encode(), 1)
check(reconstruction == control_before, 'Complete exact source-control fragment inverse recovers frozen predecessor')
for name in ('.github/workflows/javafx-library-candidate.yml', 'docs/testing/javafx-ordinary-windows-route.md'):
    check(sources[name] == read(ORIGINAL / 'proposed' / name), 'Workflow/old Stop/manual guard/doc/lint source bytes wholly unchanged: ' + name)
write_json('EXACT-REPORT-CUSTODY-CORRECTION658.json', {
    'schema': 'nativecmpkit-javafx-minimal-retained-report-byte-custody-successor658-v1', 'utc': datetime.now(timezone.utc).isoformat(),
    'passed': True, 'checks': checks, 'check_count': len(checks), 'original_packet': str(ORIGINAL),
    'independent705_refusal': {**row(refusal_raw), 'path': str(REFUSAL)},
    'driver': {'before': row(controller_before), 'after': row(controller), 'fragments': driver_fragments,
               'old_function_ASTs': old_functions, 'new_function_ASTs': new_functions,
               'only_changed_existing_functions': ['fresh_resolution', 'run'], 'only_NEW_functions': ['resolution_report_held', 'retained_resolution']},
    'source_controls': {'before': row(control_before), 'after': row(control), 'fragments': control_fragments,
                        'old_function_and_method_ASTs': old_controls, 'new_function_and_method_ASTs': new_controls,
                        'only_changed_existing_method': owning, 'NEW_methods': sorted(new_method_names), 'only_selected_methods': selected,
                        'other_nine_existing_methods_reused_not_replayed': True},
    'unchanged_workflow_and_doc': {name: row(sources[name]) for name in ('.github/workflows/javafx-library-candidate.yml', 'docs/testing/javafx-ordinary-windows-route.md')},
    'unchanged_exact12_donor_sources': {name: value for name, value in original_recipe['source_files'].items() if name not in sources},
    'Actionlint_original_and_recovery_reused_not_replayed': True,
    'ROOT_worktree_Git_network_build_stage_native_or_original_packet_writes': 0,
    'source_tests_or_target_imports_yet': 0, 'ordinary_native_and_security_acceptance': False})
# The original full inventory must remain exact after successor preparation.
for name, expected in original_seal['files'].items():
    check(row(read(ORIGINAL / name)) == {key: expected[key] for key in ('bytes', 'sha256')}, 'Frozen original80-file inventory remains held: ' + name)
    check(f'{(ORIGINAL / name).stat(follow_symlinks=False).st_mode & 0o777:04o}' == expected['external_mode'],
          'Frozen original external-file mode remains held: ' + name)
write_json('FROZEN-ORIGINAL-POSTPREPARATION-READBACK658.json', {'passed': True, 'file_count': len(original_seal['files']),
                                                            'original_seal': row(original_seal_raw),
                                                            'original_packet_changed': False, 'ROOT_worktree_Git_network_or_execution': 0})
print(json.dumps({'passed': True, 'packet': str(SUCCESSOR), 'controller': row(controller), 'source_controls': row(control),
                  'selected_methods': selected, 'driver_fragments': len(driver_fragments), 'control_fragments': len(control_fragments),
                  'original_packet_files_held': len(original_seal['files'])}, sort_keys=True))
