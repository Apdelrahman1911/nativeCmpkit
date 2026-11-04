#!/usr/bin/env python3
"""Genuinely NEW JavaFX route source controls; text/AST only, no target imports."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import stat
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = '.github/workflows/javafx-library-candidate.yml'
CONTROLLER = 'scripts/ci/javafx_ordinary_maven_consumer.py'
PREIMAGE_SHA256 = '4e3bec6b1ae93414ad1e663d232d2d264ab191908fb9493ff0f787c0278df5e8'
PUBLIC_STOP_JOB_SHA256 = 'b52eb257b7c5dc8cc65152c901303afa613a90a78e4c07a3e54a3cd5bd716675'
RECIPE_SHA256 = 'a27e4de4f217af01269d41d9bd45938b25fe0036afbfa04489f2d910782faf3f'
EXPECTED12_CANONICAL_SHA256 = '24bd1047c50e3b2a68fe5eeecd00087c84dd614d8e5247cd516f872b6fba3ac9'
OLD_OPTIONS = '        options: [linux-arm64, macos-arm64, macos-x64, windows]\n'
NEW_OPTIONS = '        options: [linux-arm64, macos-arm64, macos-x64, windows, windows-ordinary-consumer1]\n'
NEW_JOB_HEADER = '  ordinary-windows-consumer1:\n'


def passive_text(relative):
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(part in ('.', '..') for part in parts):
        raise ValueError('Confined source-control input required')
    path = ROOT
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Symlinked source-control input refused')
    before = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 1024**2:
        raise ValueError('Bounded unshared source input required')
    payload = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    if identity(before) != identity(after):
        raise ValueError('Source changed during passive read')
    return payload.decode('utf-8')


def assigned(container, name):
    matches = [node.value for node in container.body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    if len(matches) != 1:
        raise ValueError('One exact named source assignment required')
    return matches[0]


def literal(node, names=None):
    """Evaluate only finite AST literals/string concatenations; never eval/compile."""
    names = names or {}
    if isinstance(node, ast.Constant) and type(node.value) in (str, int, bool, type(None)):
        return node.value
    if isinstance(node, ast.Name) and node.id in names:
        return names[node.id]
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [literal(item, names) for item in node.elts]
        return tuple(values) if isinstance(node, ast.Tuple) else values
    if isinstance(node, ast.Dict):
        keys = [literal(key, names) for key in node.keys]
        if len(set(keys)) != len(keys):
            raise ValueError('Duplicate source-pin key')
        return dict(zip(keys, (literal(value, names) for value in node.values)))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = literal(node.left, names), literal(node.right, names)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
    raise ValueError('Executable/nonliteral source expression refused')


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return call_name(node.value) + '.' + node.attr
    return ''


def calls(container, name):
    return sorted((node for node in ast.walk(container) if isinstance(node, ast.Call)
                   and call_name(node.func) == name), key=lambda node: node.lineno)


def strings(container):
    return {node.value for node in ast.walk(container) if isinstance(node, ast.Constant) and isinstance(node.value, str)}


class JavafxOrdinaryMavenRouteSourceTests(unittest.TestCase):
    def setUp(self):
        self.source = passive_text(CONTROLLER)
        self.tree = ast.parse(self.source, filename=CONTROLLER)
        self.functions = {node.name: node for node in self.tree.body if isinstance(node, ast.FunctionDef)}
        self.workflow = passive_text(WORKFLOW)
        self.assertEqual(self.workflow.count(NEW_JOB_HEADER), 1)
        self.old_prefix, self.new_job = self.workflow.split(NEW_JOB_HEADER, 1)
        self.new_job = NEW_JOB_HEADER + self.new_job

    def test_finite_choice_reconstructs_exact_historical_workflow(self):
        self.assertEqual(self.old_prefix.count(NEW_OPTIONS), 1)
        predecessor = self.old_prefix.replace(NEW_OPTIONS, OLD_OPTIONS, 1).encode('utf-8')
        self.assertEqual(hashlib.sha256(predecessor).hexdigest(), PREIMAGE_SHA256)
        self.assertTrue(predecessor.endswith(b'\n'))
        self.assertEqual(literal(assigned(self.tree, 'WORKFLOW')), WORKFLOW)
        self.assertEqual(re.findall(r'^  ([a-z0-9-]+):$', self.workflow.split('jobs:\n', 1)[1], re.M),
                         ['public-stop', 'ordinary-windows-consumer1'])

    def test_accepted_public_stop_job_and_whitelist_are_unchanged(self):
        original_job = self.old_prefix[self.old_prefix.index('  public-stop:\n'):]
        self.assertEqual(hashlib.sha256(original_job.encode()).hexdigest(), PUBLIC_STOP_JOB_SHA256)
        whitelist = re.findall(r"contains\(fromJSON\('([^']+)'\), inputs.platform\)", original_job)
        self.assertEqual(len(whitelist), 1)
        self.assertEqual(json.loads(whitelist[0]), ['linux-arm64', 'macos-arm64', 'macos-x64', 'windows'])
        self.assertNotIn('windows-ordinary-consumer1', json.loads(whitelist[0]))

    def test_new_job_is_separate_manual_windows_and_read_only(self):
        guard = '    if: github.repository == \'Apdelrahman1911/nativeCmpkit\' && contains(fromJSON(\'["refs/heads/development/preview-hardening","refs/heads/development/javafx-ordinary-consumer1"]\'), github.ref) && github.event_name == \'workflow_dispatch\' && inputs.platform == \'windows-ordinary-consumer1\'\n'
        self.assertEqual(self.new_job.splitlines(keepends=True)[1], guard)
        for required in ('    runs-on: windows-2025\n', '    timeout-minutes: 120\n',
                         "          java-version: '17'\n", "          python-version: '3.12'\n",
                         '          persist-credentials: false\n', 'gradle/actions/wrapper-validation@v4',
                         'rustup toolchain install 1.98.0 --profile minimal --no-self-update',
                         "          packages: 'cmdline-tools;23.0 platforms;android-37.0'\n",
                         'python -B scripts/development/validate_resolutions.py --check',
                         'python -B scripts/ci/javafx_ordinary_maven_consumer.py --timeout 6600'):
            self.assertIn(required, self.new_job)
        self.assertIn('\npermissions:\n  contents: read\n', self.old_prefix)
        self.assertEqual(re.findall(r'^          python -B scripts/ci/([^ ]+)', self.new_job, re.M),
                         ['javafx_ordinary_maven_consumer.py'])
        for forbidden in ('run_library_candidate.py', 'library_tests.py', 'actions/cache/', 'push:', 'pull_request:', 'schedule:', '*.jar', '*.log', '*.stdout', '*.stderr'):
            self.assertNotIn(forbidden, self.new_job)

    def test_exact_two_manual_development_refs_have_positive_source_admission(self):
        expected = ('refs/heads/development/preview-hardening', 'refs/heads/development/javafx-ordinary-consumer1')
        driver_refs = literal(assigned(self.tree, 'MANUAL_REFS'))
        workflow_lists = re.findall(r"contains\(fromJSON\('([^']+)'\), github.ref\)", self.new_job)
        self.assertEqual(len(workflow_lists), 1)
        workflow_refs = tuple(json.loads(workflow_lists[0]))
        self.assertEqual(driver_refs, expected)
        self.assertEqual(workflow_refs, expected)
        self.assertEqual(literal(assigned(self.tree, 'WINDOWS_FOCUS')), 'windows-ordinary-consumer1')
        self.assertIn('      NATIVECMPKIT_ORDINARY_PLATFORM: ${{ inputs.platform }}\n', self.new_job)
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
        workflow_refs = tuple(json.loads(re.findall(r"contains\(fromJSON\('([^']+)'\), github.ref\)", self.new_job)[0]))
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
        original_job = self.old_prefix[self.old_prefix.index('  public-stop:\n'):]
        self.assertNotIn('refs/heads/development/javafx-ordinary-consumer1', original_job)
        self.assertNotIn('windows-ordinary-consumer1', original_job)

    def test_exact_twelve_source_pins_match_authoritative_recipe(self):
        names = {name: literal(assigned(self.tree, name)) for name in ('FIXTURE', 'DEPENDENCY')}
        pins = literal(assigned(self.tree, 'EXPECTED12'), names)
        self.assertEqual(len(pins), 12)
        self.assertTrue(all(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) for value in pins.values()))
        digest = hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(digest, EXPECTED12_CANONICAL_SHA256)
        self.assertEqual(literal(assigned(self.tree, 'SOURCE_RECIPE_AUTHORITY')), RECIPE_SHA256)
        source_inputs = ast.unparse(self.functions['inputs'])
        self.assertIn('for relative, expected in EXPECTED12.items():', source_inputs)
        self.assertIn('lt.sha256(path) == expected', source_inputs)

    def test_ordinary_command_has_only_two_tasks_without_runtime_fallback(self):
        function = self.functions['command']
        predicate = ast.unparse(calls(function, 'need')[0].args[0])
        self.assertEqual(predicate, "mode in MODES and task in ('observePrivateWebResolution', 'ordinaryCuredWebStop')")
        self.assertEqual(literal(assigned(self.tree, 'MODES')), ('module', 'pom'))
        returned = [node.value for node in function.body if isinstance(node, ast.Return)]
        self.assertEqual(len(returned), 1)
        self.assertIsInstance(returned[0], ast.List)
        self.assertEqual(ast.unparse(returned[0].elts[-1]), 'task')
        literals = strings(function)
        self.assertTrue({'--no-daemon', '--no-parallel', '--no-configuration-cache', '--no-build-cache', '--max-workers=2', '--dependency-verification', 'strict', '-p'} <= literals)
        self.assertTrue({'-PnativecmpkitPrivateJavafxRepository=', '-PnativecmpkitJavafxClassifier=win', '-PnativecmpkitMetadataMode='} <= literals)
        for forbidden in ('--init-script', '-I', '--include-build', '--patch-module', 'test', 'verifyCandidateResolution', '-PnativecmpkitVerification=true'):
            self.assertNotIn(forbidden, literals)
        producer_calls = calls(self.tree, 'packaged.commands')
        self.assertEqual(len(producer_calls), 1)
        self.assertEqual([ast.unparse(arg) for arg in producer_calls[0].args], ['ROOT', 'None'])
        self.assertFalse(calls(self.tree, 'packaged.run') or calls(self.tree, 'lt.run'))

    def test_both_complete_graphs_bind_before_single_new_native_request(self):
        run = self.functions['run']
        mode_loops = [node for node in ast.walk(run) if isinstance(node, ast.For)
                      and ast.unparse(node.target) == 'mode' and ast.unparse(node.iter) == 'MODES']
        self.assertEqual(len(mode_loops), 1)
        self.assertEqual(len(calls(mode_loops[0], 'fresh_resolution')), 1)
        ordinary_calls = calls(run, 'command')
        self.assertEqual(len(ordinary_calls), 2)
        self.assertEqual(literal(ordinary_calls[0].args[-1]), 'observePrivateWebResolution')
        native = ordinary_calls[1]
        self.assertEqual(literal(native.args[1]), 'module')
        self.assertEqual(literal(native.args[-1]), 'ordinaryCuredWebStop')
        equal_gate = [node for node in calls(run, 'need') if ast.unparse(node.args[0]) == 'equal']
        self.assertEqual(len(equal_gate), 1)
        self.assertLess(mode_loops[0].end_lineno, equal_gate[0].lineno)
        self.assertLess(equal_gate[0].lineno, native.lineno)
        binding = ast.unparse(calls(self.functions['bound_resolution'], 'need')[0].args[0])
        for required in ("verifier.get('passed') is True", "verifier.get('ordinary_resolution_bytes_bound') is True",
                         "verifier.get('official_companion_pins_bound') is True", "verifier.get('production_pins_required') is True",
                         "verifier.get('classpath_count') == 4", "verifier.get('classifier') == 'win'",
                         "verifier.get('metadata_mode') == mode", "verifier.get('native_executions') == 0", "verifier.get('publication_ready') is False"):
            self.assertIn(required, binding)
        graph = self.functions['graph_signature']
        append = calls(graph, 'signature.append')[0].args[0]
        self.assertEqual(literal(append.left.args[0].generators[0].iter), ('configuration', 'group', 'module', 'version'))
        self.assertEqual([ast.unparse(item) for item in append.right.elts], ['filename', "row['bytes']", "row['sha256']"])
        self.assertEqual(ast.unparse([node for node in graph.body if isinstance(node, ast.Return)][0].value), 'sorted(signature)')
        self.assertIn("current.get('metadata_mode') == 'module' and graph_signature(current) == signatures['module']", ast.unparse(run))
        post_binding = [node for node in calls(run, 'bound_resolution') if ast.unparse(node.args[0]) == 'native_binding']
        self.assertEqual(len(post_binding), 1)
        self.assertGreater(post_binding[0].lineno, native.lineno)
        self.assertEqual(literal(post_binding[0].args[1]), 'module')

    def test_original_failed_xml_is_captured_before_native_acceptance(self):
        run = self.functions['run']
        invoke = [node for node in ast.walk(run) if isinstance(node, ast.FunctionDef) and node.name == 'invoke'][0]
        self.assertIs(literal(invoke.args.defaults[-1]), False)
        preserved = [node for node in calls(run, 'invoke') if any(keyword.arg == 'preserve_failed_native' and literal(keyword.value) is True for keyword in node.keywords)]
        self.assertEqual(len(preserved), 1)
        self.assertIn('if not preserve_failed_native:', ast.unparse(invoke))
        captured = calls(run, 'fresh_native')
        self.assertEqual(len(captured), 1)
        acceptance = [node for node in calls(run, 'need') if "native_execution['exit_code']" in ast.unparse(node.args[0])]
        self.assertEqual(len(acceptance), 1)
        self.assertLess(preserved[0].lineno, captured[0].lineno)
        self.assertLess(captured[0].lineno, acceptance[0].lineno)
        predicate = ast.unparse(acceptance[0].args[0])
        for required in ("native_execution['exit_code'] == 0", "not native_execution.get('stop_reason')",
                         "record['native']['exact_task_marker']", "record['native']['all_reports_fresh']",
                         "record['native']['exact_source_method_passed']", "not record['native']['XML_parse_errors']"):
            self.assertIn(required, predicate)
        native = self.functions['fresh_native']
        saved = calls(native, 'saved.open')
        self.assertEqual(literal(saved[0].args[0]), 'xb')
        self.assertLess(saved[0].lineno, calls(native, 'lt.junit_cases')[0].lineno)
        value = assigned(native, 'value')
        exact = dict(zip((literal(key) for key in value.keys), value.values))['exact_source_method_passed']
        self.assertEqual(ast.unparse(exact), "len(reports) == len(cases) == 1 and cases == [{'classname': CLASS, 'name': METHOD, 'status': 'passed'}]")
        self.assertEqual(literal(assigned(self.tree, 'CLASS')), 'nativecmpkit.consumer.OrdinaryCuredWebStopConsumerTest')
        self.assertEqual(literal(assigned(self.tree, 'METHOD')), 'normalMavenActivationBindsCuredPublicStopTransportAndOwnedLifetime')
        self.assertIn('NATIVECMPKIT_ORDINARY_CURED_STOP task=:ordinaryCuredWebStop gradle=9.7.1 java=17 mode=module classifier=win methods=1', strings(native))
        self.assertIn('native/test-outcomes.json', strings(native))

    def test_final_custody_and_material_gates_keep_missing_scope_unqualified(self):
        run = self.functions['run']
        rendered = ast.unparse(run)
        for required in ('before == after and lt.git_revision(ROOT)', 'private_stage_sha == lt.sha256(',
                         'read(lt.safe_path(private_repository, name))', 'all(runtime[key] == after_runtime[key] for key in keys)',
                         '(owned.st_dev, owned.st_ino) == (current.st_dev, current.st_ino)',
                         "record['passed'] = record['passed'] and bool(held) and all(held)"):
            self.assertIn(required, rendered)
        receipt_update = [node for node in calls(run, 'record.update') if any(keyword.arg == 'detached_process_absence_verified' for keyword in node.keywords)]
        self.assertEqual(len(receipt_update), 1)
        flags = {keyword.arg: keyword.value for keyword in receipt_update[0].keywords}
        for name in ('detached_process_absence_verified', 'dependency_verification_metadata_qualified', 'all_five_host_graphs_verified'):
            self.assertIs(literal(flags[name]), False)
        initial = assigned(run, 'record')
        initial_flags = dict(zip((literal(key) for key in initial.keys), initial.values))
        for name in ('publication_ready', 'packages_published', 'full_native_corresponding_source_complete',
                     'security_or_API_ABI_clearance', 'release_readiness_certified', 'independent_lead_acceptance',
                     'accepted_private_library_Stop_replayed', 'automatic_retries'):
            self.assertIs(literal(initial_flags[name]), False)
        self.assertEqual(literal(assigned(self.tree, 'RESERVE_MIB')), 8192)
        invoke = [node for node in ast.walk(run) if isinstance(node, ast.FunctionDef) and node.name == 'invoke'][0]
        self.assertLess(calls(invoke, 'resources')[0].lineno, calls(invoke, 'lt.execute')[0].lineno)
        self.assertIn('GlobalMemoryStatusEx', ast.unparse(self.functions['resources']))
        self.assertIn('min(', ast.unparse(self.functions['resources']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
