#!/usr/bin/env python3
"""Passive source qualification only; no controller/test-module imports or calls."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat

PACKET = Path(__file__).resolve().parent
ROOT = Path('/root/projects/nativeCmpKit')
LEAD = Path('/root/nativecmpkit-source-proposals-20261104/lead-javafx-companion-intake-20261104')
RECIPE = LEAD / 'CURRENT2EE-TWELVE-NEW-SOURCE-ADOPTION-RECIPE.json'
REGISTRATION = Path('/root/nativecmpkit-source-proposals-20261104/lead-workflow-registration-20261104/WORKFLOW-REGISTRATION.json')
checks, inputs, absences = [], {}, {}


def check(condition, label):
    checks.append({'check': label, 'passed': bool(condition)})
    if not condition:
        raise ValueError(label)


def read(path, kind='passive-source', limit=4 * 1024**2):
    path = Path(path)
    before = path.stat(follow_symlinks=False)
    check(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_nlink == 1 and before.st_size <= limit,
          'Bounded regular unshared named input: ' + str(path))
    raw = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    check((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
          (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Stable named passive read: ' + str(path))
    row = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'actual_read_mode': oct(before.st_mode & 0o777), 'kind': kind}
    if str(path) in inputs:
        check(inputs[str(path)] == row, 'Repeated named reference held: ' + str(path))
    inputs[str(path)] = row
    return raw


def absent(path):
    path = Path(path)
    value = not (path.exists() or path.is_symlink())
    absences[str(path)] = value
    check(value, 'Named ROOT prospective addition/metadata remains absent: ' + str(path))


def assignment(container, name):
    matches = [node.value for node in container.body if isinstance(node, ast.Assign) and
               any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    check(len(matches) == 1, 'Unique passive literal source assignment: ' + name)
    return matches[0]


def literal(node, names=None):
    names = names or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in names:
        return names[node.id]
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [literal(item, names) for item in node.elts]
        return tuple(values) if isinstance(node, ast.Tuple) else values
    if isinstance(node, ast.Dict):
        keys = [literal(key, names) for key in node.keys]
        check(len(set(keys)) == len(keys), 'No duplicate literal pin keys')
        return dict(zip(keys, (literal(value, names) for value in node.values)))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = literal(node.left, names), literal(node.right, names)
        check(isinstance(left, str) and isinstance(right, str), 'Only literal source-path concatenation')
        return left + right
    raise ValueError('Executable/nonliteral source expression is outside passive qualification')


def calls(container, name):
    return sorted((node for node in ast.walk(container) if isinstance(node, ast.Call) and ast.unparse(node.func) == name),
                  key=lambda node: node.lineno)


def write(path, value):
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write('\n')
    path.chmod(0o600)


try:
    recipe_raw = read(RECIPE, 'saved-lead-exact12-authority')
    check(hashlib.sha256(recipe_raw).hexdigest() == 'a27e4de4f217af01269d41d9bd45938b25fe0036afbfa04489f2d910782faf3f', 'Lead exact12 recipe authority held')
    recipe = json.loads(recipe_raw)
    check(recipe['combined_file_count'] == 12 and recipe['combined_source_bytes'] == 161381, 'Exact12 source union count/bytes retained')
    check(recipe['expected_root_head'] == '2ee751a203f488249839873bfe6590edd73b65ea' and recipe['expected_root_tree'] == '13c1e99a619170990d34280c7c75bc3f1fc3f356', 'Saved identities remain historical source authority, not a current Git query')
    for relative, row in recipe['source_files'].items():
        raw = read(row['source_path'], 'unchanged-exact12-donor-source')
        check(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'Exact12 donor bytes held: ' + relative)
        check(row['expected_mode'] == '0644' and row['root_preimage'] is None, 'Prospective destination mode/preimage distinct from donor mode: ' + relative)
        absent(ROOT / relative)
    intake = json.loads(read(PACKET / 'PASSIVE-INTAKE658.json', 'reused-sealed-original-intake-result'))
    check(intake['outcome'] == 'passed' and intake['check_count'] == 222 and intake['sparse_read_input_count'] == 84 and intake['sparse_reads_held'], 'Reuse prior passive222/84 held intake, not a new execution')
    for path, expected in (
        (Path('/root/nativecmpkit-native-reviews-20261101/agent606-javafx-ordinary-adoption-implementation/DELIVERY-MANIFEST.json'), 'd8c1c0ac227bd90c706835a2925b3a47f3bd74b55cebf80eeff2c6512b67d438'),
        (Path('/root/nativecmpkit-native-reviews-20261101/agent606-javafx-companion-provenance-correction/DELIVERY-MANIFEST.json'), 'd15c0df74c0bb211ed208aeaf61318d80ddeed91732c2a84bc739645f4500b22')):
        check(hashlib.sha256(read(path, 'sealed-original-delivery-manifest')).hexdigest() == expected, 'Original delivery envelope manifest unchanged: ' + str(path))

    refs = json.loads(read(PACKET / 'CURRENT-BOUNDED-ROUTE-REFERENCES658.json', 'saved-finite-helper-reference-snapshot'))
    for relative, row in refs['references'].items():
        raw = read(ROOT / relative, 'named-ROOT-source-reference-only')
        check(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'Named historical helper/workflow reference held: ' + relative)
    absent(ROOT / 'gradle/verification-metadata.xml')
    for relative in ('scripts/ci/javafx_ordinary_maven_consumer.py', 'scripts/ci/test_javafx_ordinary_maven_route.py',
                     'docs/testing/javafx-ordinary-windows-route.md', '.github/workflows/javafx-ordinary-maven-consumer.yml'):
        absent(ROOT / relative)

    derivative = json.loads(read(PACKET / 'REGISTERED-WORKFLOW-TWO-REF-DERIVATIVE658.json', 'final-exact-workflow-derivative-recipe'))
    predecessor = read(PACKET / derivative['preimage']['retained_path'], 'retained-exact-existing-workflow-preimage')
    workflow = read(PACKET / 'proposed/.github/workflows/javafx-library-candidate.yml', 'canonical-route-source-postimage')
    check(hashlib.sha256(predecessor).hexdigest() == derivative['preimage']['sha256'] and hashlib.sha256(workflow).hexdigest() == derivative['postimage']['sha256'], 'Exact existing-workflow predecessor/postimage held')
    first, append = derivative['fragments']
    check(first['kind'] == 'replace-exact-once' and append['kind'] == 'append-at-exact-predecessor-EOF' and append['preimage'] == '', 'Only finite options plus EOF job append composition')
    check(predecessor.count(first['preimage'].encode()) == 1, 'One exact finite input-option predecessor location')
    composed = predecessor.replace(first['preimage'].encode(), first['postimage'].encode(), 1) + append['postimage'].encode()
    check(composed == workflow, 'Exact two-fragment forward composition')
    prior = workflow[:-len(append['postimage'].encode())].replace(first['postimage'].encode(), first['preimage'].encode(), 1)
    check(prior == predecessor, 'Exact two-fragment inverse reconstruction')
    old_job = predecessor[predecessor.index(b'  public-stop:\n'):]
    check(hashlib.sha256(old_job).hexdigest() == 'b52eb257b7c5dc8cc65152c901303afa613a90a78e4c07a3e54a3cd5bd716675', 'Complete accepted public-stop job bytes retained')
    check(b'windows-ordinary-consumer1' not in old_job and b'development/javafx-ordinary-consumer1' not in old_job, 'Old accepted job cannot select NEW choice/ref')
    check(not (PACKET / 'proposed/.github/workflows/javafx-ordinary-maven-consumer.yml').exists(), 'Standalone workflow is excluded from canonical delivery')
    read(PACKET / 'retained/javafx-ordinary-maven-consumer.standalone-unadopted.yml', 'retained-unadopted-alternative-only')

    registration_raw = read(REGISTRATION, 'lead-once-acquired-read-only-registration-observation')
    check(hashlib.sha256(registration_raw).hexdigest() == '6bd756c3fc5491bd9544470bc31336f05ac50d0fd5436ee46bbf8ccfbf94a020', 'Saved live registration observation hash held; no reacquisition')
    registration = json.loads(registration_raw)
    check(registration['total_count'] == len(registration['workflows']) == 4 and all(row['state'] == 'active' for row in registration['workflows']), 'Lead observed exactly four active registrations')
    observed = [row for row in registration['workflows'] if row['path'] == '.github/workflows/javafx-library-candidate.yml']
    check(len(observed) == 1 and observed[0]['id'] == 404301928 and observed[0]['name'] == 'NativeCmpKit Windows JavaFX library candidate', 'Observed existing workflow ID/path/name held; NEW branch input/job still unadopted')
    check(derivative['new_finite_input_job_adopted_or_dispatch_HEAD_verified'] is False, 'No invented new-input adoption/dispatch/HEAD acceptance')

    controller_raw = read(PACKET / 'proposed/scripts/ci/javafx_ordinary_maven_consumer.py', 'canonical-route-controller-source-only')
    controller = ast.parse(controller_raw.decode(), filename='proposed/scripts/ci/javafx_ordinary_maven_consumer.py')
    functions = {node.name: node for node in controller.body if isinstance(node, ast.FunctionDef)}
    check(hashlib.sha256(controller_raw).hexdigest() == derivative['controller']['after_sha256'], 'Canonical controller final derivative held')
    names = {name: literal(assignment(controller, name)) for name in ('FIXTURE', 'DEPENDENCY')}
    expected12 = literal(assignment(controller, 'EXPECTED12'), names)
    check(expected12 == {key: row['sha256'] for key, row in recipe['source_files'].items()}, 'Controller exact12 map matches actual unchanged authoritative donors')
    check(literal(assignment(controller, 'SOURCE_RECIPE_AUTHORITY')) == hashlib.sha256(recipe_raw).hexdigest(), 'Controller saved authority is source-only, not current HEAD pinning')
    refs2 = ('refs/heads/development/preview-hardening', 'refs/heads/development/javafx-ordinary-consumer1')
    check(literal(assignment(controller, 'MANUAL_REFS')) == refs2 and literal(assignment(controller, 'WINDOWS_FOCUS')) == 'windows-ordinary-consumer1', 'Driver finite manual two-ref/one-focus source policy')
    check(derivative['finite_manual_refs'] == list(refs2), 'Workflow/source recipe exact manual ref union')
    check(len(calls(functions['run'], 'manual_context')) == 1 and calls(functions['run'], 'manual_context')[0].lineno < calls(functions['run'], 'runtime_context.capture')[0].lineno, 'Manual source admission precedes runtime/producer/native actions')
    check(len(calls(controller, 'packaged.commands')) == 1 and [ast.unparse(arg) for arg in calls(controller, 'packaged.commands')[0].args] == ['ROOT', 'None'], 'Only unchanged producer helper composition, never old consumer commands')
    check(not calls(controller, 'packaged.run') and not calls(controller, 'lt.run'), 'No old consumer/library Stop population invocation')
    check(len(calls(functions['run'], 'command')) == 2 and len(calls(functions['run'], 'fresh_native')) == 1, 'One resolution-loop builder plus only one NEW native builder/capture site')
    capture = calls(functions['run'], 'fresh_native')[0]
    acceptance = [node for node in calls(functions['run'], 'need') if "native_execution['exit_code']" in ast.unparse(node.args[0])]
    check(len(acceptance) == 1 and capture.lineno < acceptance[0].lineno, 'Original failed/partial XML capture before Gradle/native acceptance')
    check("current.get('metadata_mode') == 'module' and graph_signature(current) == signatures['module']" in ast.unparse(functions['run']), 'Post-native exact fresh module graph remains bound before reuse')
    check(len(calls(functions['run'], 'bound_resolution')) == 1, 'Post-native production verifier receipt is independently checked')
    update = [node for node in calls(functions['run'], 'record.update') if any(keyword.arg == 'detached_process_absence_verified' for keyword in node.keywords)]
    check(len(update) == 1, 'One explicit final material-gate report')
    keywords = {keyword.arg: keyword.value for keyword in update[0].keywords}
    check(all(literal(keywords[name]) is False for name in ('detached_process_absence_verified', 'dependency_verification_metadata_qualified', 'all_five_host_graphs_verified')), 'Detached/dependency/all-host missing gates remain false')

    control_raw = read(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py', 'only-NEW-text-AST-control-source')
    control = ast.parse(control_raw.decode(), filename='proposed/scripts/ci/test_javafx_ordinary_maven_route.py')
    check(hashlib.sha256(control_raw).hexdigest() == derivative['source_controls']['after_sha256'], 'NEW10 source control postimage held')
    imported = {alias.name.split('.')[0] for node in ast.walk(control) if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module.split('.')[0] for node in ast.walk(control) if isinstance(node, ast.ImportFrom)}
    check(imported == {'__future__', 'ast', 'hashlib', 'json', 'pathlib', 're', 'stat', 'unittest'}, 'NEW controls import stdlib only; never controller/helpers/old population')
    check(not any(calls(control, name) for name in ('eval', 'exec', 'compile', '__import__', 'subprocess.run', 'subprocess.Popen', 'runpy.run_path')), 'NEW controls cannot evaluate/compile/import/execute targets')
    classes = [node for node in control.body if isinstance(node, ast.ClassDef)]
    check(len(classes) == 1 and ast.unparse(classes[0].bases[0]) == 'unittest.TestCase', 'One owning NEW source-only TestCase')
    selected = [classes[0].name + '.' + node.name for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
    plan_raw = read(PACKET / 'NEW-ROUTE-EXECUTION-PLAN658.json', 'exact-authorized-NEW-control-and-lint-plan')
    plan = json.loads(plan_raw)
    check(len(selected) == 10 and selected == plan['new-controls']['NEW_methods'], 'Exactly NEW10 finite affected selection; no discovery/old methods')
    check(any('positive_source_admission' in name for name in selected) and any('no_source_admission' in name for name in selected), 'Genuinely NEW positive and foreign-ref source methods included')
    canonical = hashlib.sha256(json.dumps(expected12, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    check(literal(assignment(control, 'EXPECTED12_CANONICAL_SHA256')) == canonical == '24bd1047c50e3b2a68fe5eeecd00087c84dd614d8e5247cd516f872b6fba3ac9', 'Portable source controls pin exact12 recipe without external imports/old test replay')
    doc = read(PACKET / 'proposed/docs/testing/javafx-ordinary-windows-route.md', 'canonical-prospective-route-document')
    check(hashlib.sha256(doc).hexdigest() == derivative['doc']['after_sha256'], 'Route scope/material-limit final documentation held')
    for phrase in ('UNADOPTED', 'No stage, build, target-code', 'Main/tags/foreign/near-match refs refuse', 'changing that frozen cohort HEAD',
                   '404301928', 'detached_process_absence_verified=false', 'dependency_verification_metadata_qualified=false', '**not fresh67**', '#64 closure'):
        check(phrase in doc.decode(), 'Document retains required scoped limit: ' + phrase)

    for name in ('new_controls_audit_bootstrap.py', 'run_new_route_selection_once.py', 'qualify_route_source_before_execution.py'):
        raw = read(PACKET / name, 'external-qualification-or-NEW-execution-custody-source')
        ast.parse(raw.decode(), filename=name)
    python_real = Path('/usr/bin/python3').resolve(strict=True)
    read(python_real, 'installed-Python-binary-observation-only', 64 * 1024**2)
    actionlint = Path('/tmp/nativecmpkit-actionlint-1.7.12/actionlint')
    read(actionlint, 'installed-Actionlint-binary-no-download', 64 * 1024**2)
    check(bool(actionlint.stat().st_mode & 0o100), 'Existing Actionlint binary is executable; no download')
    aliases = {'/usr/bin/python3': str(python_real)}
    before = dict(inputs)
    for name, row in before.items():
        raw = Path(name).read_bytes()
        check(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'Final passive preexecution named input hold: ' + name)
    check(all(not (Path(name).exists() or Path(name).is_symlink()) for name in absences), 'All named ROOT destination/metadata absences held before execution')
    qualified = {'schema': 'nativecmpkit-javafx-qualified-finite-source-control-inputs658-v1', 'utc': datetime.now(timezone.utc).isoformat(),
                 'passed': True, 'plan_sha256': hashlib.sha256(plan_raw).hexdigest(), 'inputs': inputs, 'ROOT_destinations_absent': absences,
                 'tool_aliases': aliases, 'actual_named_input_count': len(inputs), 'ROOT_absence_count': len(absences),
                 'scope': 'Finite actual source-control/prerequisite/tool read map only; NOT a Git/global/native/compiler/controller execution map',
                 'historical_current2ee_identity_queried_now': False, 'ROOT_writes': 0, 'target_imports': 0, 'test_build_stage_native_dispatch_or_Git_execution': 0}
    write(PACKET / 'QUALIFIED-SOURCE-INPUTS658.json', qualified)
    outcome = {'schema': 'nativecmpkit-javafx-route-passive-source-qualification658-v1', 'utc': datetime.now(timezone.utc).isoformat(),
               'passed': True, 'check_count': len(checks), 'checks': checks, 'named_input_count': len(inputs), 'named_inputs_held': True,
               'ROOT_absence_count': len(absences), 'reused_original_intake': {'passive_checks': 222, 'actual_sparse_inputs': 84, 'executions_replayed': 0},
               'NEW10_and_Actionlint_execution_yet': 0, 'ROOT_Git_network_native_build_or_target_imports': 0,
               'scope': 'Exact final source/ref/tool qualification before only NEW source controls/Actionlint; no current HEAD, native acceptance or #64 closure'}
    write(PACKET / 'PASSIVE-ROUTE-SOURCE-QUALIFICATION658.json', outcome)
    print(json.dumps({key: outcome[key] for key in ('passed', 'check_count', 'named_input_count', 'named_inputs_held', 'ROOT_absence_count')}, sort_keys=True))
except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
    failed = {'passed': False, 'check_count': len(checks), 'checks': checks, 'error_type': type(error).__name__,
              'last_named_check': checks[-1] if checks else None, 'execution_started': False,
              'scope': 'Passive preexecution reviewer refusal only; no tests/lint/target/native/ROOT execution'}
    write(PACKET / 'PASSIVE-ROUTE-SOURCE-QUALIFICATION658-REFUSAL.json', failed)
    print(json.dumps(failed, sort_keys=True))
    raise SystemExit(1)
