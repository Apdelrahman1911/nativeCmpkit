#!/usr/bin/env python3
"""Final passive named-source/result review and external current16 packet sealing."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import stat

PACKET = Path(__file__).resolve().parent
ROOT = Path('/root/projects/nativeCmpKit')
AUTHORITY = Path('/root/nativecmpkit-source-proposals-20261104/lead-javafx-companion-intake-20261104/CURRENT2EE-TWELVE-NEW-SOURCE-ADOPTION-RECIPE.json')
REVIEW620 = Path('/root/nativecmpkit-native-reviews-20261101/independent620-javafx-companion-correction-source-results/SEAL.json')
RECIPE_NAME = 'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json'
checks, inputs = [], {}


def check(value, label):
    checks.append({'check': label, 'passed': bool(value)})
    if not value:
        raise ValueError(label)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def row(raw):
    return {'bytes': len(raw), 'sha256': digest(raw)}


def read(path, kind='finite-passive-review-input', limit=64 * 1024**2):
    path = Path(path)
    before = path.stat(follow_symlinks=False)
    check(stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_nlink == 1 and before.st_size <= limit,
          'Bounded regular unshared named read: ' + str(path))
    raw = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    check((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
          (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
          'Stable final named read: ' + str(path))
    value = {**row(raw), 'actual_read_mode': f'{before.st_mode & 0o777:04o}', 'kind': kind}
    if str(path) in inputs:
        check({key: inputs[str(path)][key] for key in ('bytes', 'sha256', 'actual_read_mode')} ==
              {key: value[key] for key in ('bytes', 'sha256', 'actual_read_mode')}, 'Repeated final named input held: ' + str(path))
    else:
        inputs[str(path)] = value
    return raw


def write(name, raw):
    path = PACKET / name
    check(path.is_relative_to(PACKET) and not path.exists() and not path.is_symlink(), 'New external final metadata only: ' + name)
    with path.open('xb') as output:
        output.write(raw)
    path.chmod(0o600)


def write_json(name, value):
    write(name, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def assignment(container, name):
    values = [node.value for node in container.body if isinstance(node, ast.Assign) and
              any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    check(len(values) == 1, 'Unique literal source assignment: ' + name)
    return values[0]


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
        check(len(keys) == len(set(keys)), 'No duplicate finite source keys')
        return dict(zip(keys, (literal(value, names) for value in node.values)))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = literal(node.left, names), literal(node.right, names)
        check(isinstance(left, str) and isinstance(right, str), 'Finite source-path literal concatenation only')
        return left + right
    raise ValueError('Nonliteral target expression is not executable in this passive review')


def calls(container, name):
    return sorted((node for node in ast.walk(container) if isinstance(node, ast.Call) and ast.unparse(node.func) == name),
                  key=lambda node: node.lineno)


try:
    authority_raw = read(AUTHORITY, 'saved-lead-exact12-source-authority')
    check(digest(authority_raw) == 'a27e4de4f217af01269d41d9bd45938b25fe0036afbfa04489f2d910782faf3f', 'Original lead exact12 authority hash held')
    authority = json.loads(authority_raw)
    check(authority['combined_file_count'] == 12 and authority['combined_source_bytes'] == 161381,
          'Twelve-source union remains161381B')
    review620_raw = read(REVIEW620, 'cached-independent620-source-results-authority-only')
    check(digest(review620_raw) == 'b7306347b46511049babe406db0bc408525918aa79e412b7c5e33c0fcff6b356',
          'Named cached620 seal held; no review/network reacquisition or native/security inference')
    json.loads(review620_raw)
    first_qualified_raw = read(PACKET / 'QUALIFIED-SOURCE-INPUTS658.json', 'retained-initial-source-qualification-map')
    recovery_qualified_raw = read(PACKET / 'QUALIFIED-RECOVERY-SOURCE-INPUTS658.json', 'actual-recovery-source-qualification-map')
    first_qualified, recovery_qualified = json.loads(first_qualified_raw), json.loads(recovery_qualified_raw)
    check(first_qualified['passed'] is True and first_qualified['actual_named_input_count'] == 47 and
          recovery_qualified['passed'] is True and recovery_qualified['actual_named_input_count'] == 64,
          'Initial47 and recovery64 maps have separate exact source qualifications')
    retained_map = {
        str(PACKET / 'proposed/.github/workflows/javafx-library-candidate.yml'): PACKET / 'retained/javafx-library-candidate.before-actionlint-recovery658.yml',
        str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'): PACKET / 'retained/test_javafx_ordinary_maven_route.before-failed-fixture-recovery658.py',
    }
    for name, expected in first_qualified['inputs'].items():
        raw = read(retained_map.get(name, Path(name)), 'retained-initial-actual-source-or-exact-postimage-locator')
        check(row(raw) == {key: expected[key] for key in ('bytes', 'sha256')}, 'Original47 inputs held via exact original postimages: ' + name)
    for name, expected in recovery_qualified['inputs'].items():
        raw = read(name, 'actual-final-recovery-source-prerequisite-or-tool-input')
        check(row(raw) == {key: expected[key] for key in ('bytes', 'sha256')}, 'Actual64 recovery inputs remain held after both commands: ' + name)
    check(recovery_qualified['ROOT_absence_count'] == first_qualified['ROOT_absence_count'] == 17,
          'Both finite source maps retain17 named ROOT absences, not a project-wide absence claim')
    check(first_qualified['ROOT_destinations_absent'] == recovery_qualified['ROOT_destinations_absent'] and
          all(not (Path(name).exists() or Path(name).is_symlink()) for name in recovery_qualified['ROOT_destinations_absent']),
          'Named additions/metadata remain absent in ROOT; isolated worktree still requires lead/705 readback')
    check(all(str(Path(alias).resolve(strict=True)) == real for alias, real in recovery_qualified['tool_aliases'].items()),
          'Qualified installed Python alias held without new metadata query/install')

    first_plan_raw = read(PACKET / 'NEW-ROUTE-EXECUTION-PLAN658.json', 'retained-first-NEW10-and-lint-plan')
    recovery_plan_raw = read(PACKET / 'ONLYFAILED-CHANGED2-RECOVERY-EXECUTION-PLAN658.json', 'exact-failed-changed2-recovery-plan')
    first_plan, recovery_plan = json.loads(first_plan_raw), json.loads(recovery_plan_raw)
    results, result_bindings = {}, {}
    for directory, stage, expected_exit, qualified, qualified_raw, plan, plan_raw in (
        ('FIRST-NEW10-SOURCE658', 'new-controls', 1, first_qualified, first_qualified_raw, first_plan, first_plan_raw),
        ('FIRST-ACTIONLINT658', 'actionlint', 1, first_qualified, first_qualified_raw, first_plan, first_plan_raw),
        ('ONLYFAILED-CHANGED2-SOURCE-RECOVERY658', 'new-controls', 0, recovery_qualified, recovery_qualified_raw, recovery_plan, recovery_plan_raw),
        ('ONLYFAILED-ACTIONLINT-RECOVERY658', 'actionlint', 0, recovery_qualified, recovery_qualified_raw, recovery_plan, recovery_plan_raw),
    ):
        result_raw = read(PACKET / directory / 'result.json', 'retained-actual-once-command-result')
        result = json.loads(result_raw)
        check(result['exit_code'] == expected_exit and result['passed'] is (expected_exit == 0) and result['source_inputs_held'],
              'Original/recovery exit and actual held custody: ' + directory)
        check(result['command'] == plan[stage]['command'] and result['plan_sha256'] == digest(plan_raw) and
              result['qualification_map_sha256'] == digest(qualified_raw) and result['actual_named_input_count'] == len(qualified['inputs']),
              'Exact plan/qualified-map/command/input count binding: ' + directory)
        before_raw = read(PACKET / directory / 'source-inputs-before.json', 'actual-original-command-input-map')
        after_raw = read(PACKET / directory / 'source-inputs-after.json', 'actual-original-command-input-map')
        expected_snapshot = {'files': {name: {key: value[key] for key in ('bytes', 'sha256')} for name, value in qualified['inputs'].items()},
                             'ROOT_destinations_absent': qualified['ROOT_destinations_absent'], 'tool_aliases': qualified['tool_aliases']}
        check(before_raw == after_raw and json.loads(before_raw) == expected_snapshot,
              'Exact actual before/after map equals source qualification: ' + directory)
        for stream, binding in result['streams'].items():
            check(row(read(PACKET / directory / stream, 'preserved-actual-command-stream')) == binding,
                  'Exact original stream custody: ' + directory + '/' + stream)
        check(result['automatic_retry'] is False and result['accepted_private_library_Stop_replayed'] is False and
              result['target_imports_requested'] == result['old_method_populations_requested'] ==
              result['build_stage_native_dispatch_or_Git_commands_requested'] == 0,
              'No target/old-method/native/build/Git/dispatch/retry request: ' + directory)
        if stage == 'new-controls':
            audit = json.loads(read(PACKET / directory / 'audit.json', 'actual-owned-child-audit'))
            check(audit == result['audit'] and audit['passed'] is True and audit['denied_attempts'] == [],
                  'Actual passive-child no-denied-attempt audit: ' + directory)
            check(result['selected_NEW_methods'] == plan[stage]['NEW_methods'], 'Exact finite control selection: ' + directory)
        else:
            check(result['workflow_source_only'] is True, 'Actionlint is candidate source-only: ' + directory)
        results[directory] = result
        result_bindings[directory] = {**row(result_raw), 'path': directory + '/result.json', 'exit_code': expected_exit,
                                      'elapsed_seconds': result['elapsed_seconds'], 'actual_named_input_count': result['actual_named_input_count']}
    first_stderr = read(PACKET / 'FIRST-NEW10-SOURCE658/stderr.txt').decode()
    recovery_stderr = read(PACKET / 'ONLYFAILED-CHANGED2-SOURCE-RECOVERY658/stderr.txt').decode()
    check(first_stderr.count(' ... ok\n') == 9 and first_stderr.count(' ... FAIL\n') == 1 and 'Ran 10 tests in 0.112s' in first_stderr,
          'First actual NEW10 is9pass/onefail/0.112s, not fresh10green')
    check(recovery_stderr.count(' ... ok\n') == 2 and 'Ran 2 tests in 0.026s' in recovery_stderr and recovery_stderr.endswith('\nOK\n'),
          'Only failed/changed2 is2pass/0.026s; no other passing-method replay')
    check(read(PACKET / 'ONLYFAILED-ACTIONLINT-RECOVERY658/stdout.txt') == read(PACKET / 'ONLYFAILED-ACTIONLINT-RECOVERY658/stderr.txt') == b'',
          'Onlyfailed Actionlint0 has empty preserved streams')

    derivative_raw = read(PACKET / 'REGISTERED-WORKFLOW-FINAL-DERIVATIVE658.json', 'preexecution-final-workflow-source-fragment-authority')
    derivative = json.loads(derivative_raw)
    workflow_path = PACKET / 'proposed/.github/workflows/javafx-library-candidate.yml'
    workflow = read(workflow_path, 'final-canonical-workflow-postimage')
    predecessor = read(PACKET / derivative['preimage']['retained_path'], 'exact-retained-existing-workflow-preimage')
    option, append = derivative['fragments']
    check(predecessor.count(option['preimage'].encode()) == 1 and
          predecessor.replace(option['preimage'].encode(), option['postimage'].encode(), 1) + append['postimage'].encode() == workflow,
          'Two exact workflow forward fragments: finite options and original EOF append only')
    check(workflow[:-len(append['postimage'].encode())].replace(option['postimage'].encode(), option['preimage'].encode(), 1) == predecessor,
          'Exact inverse reconstructs every original workflow byte')
    old_job = predecessor[predecessor.index(b'  public-stop:\n'):]
    final_prefix, new_tail = workflow.split(b'  ordinary-windows-consumer1:\n', 1)
    check(len(old_job) == 7294 and digest(old_job) == 'b52eb257b7c5dc8cc65152c901303afa613a90a78e4c07a3e54a3cd5bd716675' and
          final_prefix[final_prefix.index(b'  public-stop:\n'):] == old_job,
          'Complete accepted old Stop7294B/job bytes retained, not replayed')
    whitelist = re.findall(r"contains\(fromJSON\('([^']+)'\), inputs.platform\)", old_job.decode())
    check(len(whitelist) == 1 and json.loads(whitelist[0]) == ['linux-arm64', 'macos-arm64', 'macos-x64', 'windows'],
          'Accepted old whitelist exactly4; NEW ordinary input excluded')
    check(b'verify-signature: true' in old_job and b'verify-signature:' not in new_tail,
          'Old voluntary-pinned action byte retained; only unsupported NEW v4 input removed, no signing/trust claim')
    check(b'windows-ordinary-consumer1' not in old_job and b'development/javafx-ordinary-consumer1' not in old_job,
          'Accepted old job cannot run on NEW focus/ref')
    check(row(workflow) == {key: derivative['postimage'][key] for key in ('bytes', 'sha256')}, 'Final workflow derivative exact postimage binding')

    controller_raw = read(PACKET / 'proposed/scripts/ci/javafx_ordinary_maven_consumer.py', 'final-controller-AST-only-no-import')
    controller = ast.parse(controller_raw.decode())
    functions = {node.name: node for node in controller.body if isinstance(node, ast.FunctionDef)}
    names = {name: literal(assignment(controller, name)) for name in ('FIXTURE', 'DEPENDENCY')}
    expected12 = literal(assignment(controller, 'EXPECTED12'), names)
    check(expected12 == {name: value['sha256'] for name, value in authority['source_files'].items()},
          'Unchanged controller exact12 pins equal authoritative actual donor union')
    check(digest(json.dumps(expected12, sort_keys=True, separators=(',', ':')).encode()) == '24bd1047c50e3b2a68fe5eeecd00087c84dd614d8e5247cd516f872b6fba3ac9',
          'Portable canonical exact12 map digest retained')
    manual_refs = ('refs/heads/development/preview-hardening', 'refs/heads/development/javafx-ordinary-consumer1')
    check(literal(assignment(controller, 'MANUAL_REFS')) == manual_refs and derivative['finite_manual_refs'] == list(manual_refs),
          'Exactly the two authorized development manual refs, not arbitrary branch/main/tag admission')
    check(literal(assignment(controller, 'WINDOWS_FOCUS')) == 'windows-ordinary-consumer1' and
          'context[\'repository\'] == \'Apdelrahman1911/nativeCmpkit\'' in ast.unparse(functions['manual_context']) and
          'context[\'event\'] == \'workflow_dispatch\'' in ast.unparse(functions['manual_context']),
          'Driver exact repository/manual event/NEW choice source policy')
    run = functions['run']
    check(len(calls(run, 'manual_context')) == 1 and calls(run, 'manual_context')[0].lineno < calls(run, 'os.open')[0].lineno <
          calls(run, 'runtime_context.capture')[0].lineno, 'Manual policy precedes lock/runtime/producer/native work')
    mode_loops = [node for node in ast.walk(run) if isinstance(node, ast.For) and ast.unparse(node.target) == 'mode' and ast.unparse(node.iter) == 'MODES']
    native_commands = [node for node in calls(run, 'command') if literal(node.args[-1]) == 'ordinaryCuredWebStop']
    equal_gates = [node for node in calls(run, 'need') if ast.unparse(node.args[0]) == 'equal']
    check(len(mode_loops) == len(native_commands) == len(equal_gates) == 1 and mode_loops[0].end_lineno < equal_gates[0].lineno < native_commands[0].lineno,
          'Both complete independent four-classpath graph modes and exact byte equality precede single NEW native request')
    check(literal(native_commands[0].args[1]) == 'module' and literal(assignment(controller, 'MODES')) == ('module', 'pom'),
          'One module-mode native request; equal POM graph reuses it, not a second native run')
    acceptance = [node for node in calls(run, 'need') if "native_execution['exit_code']" in ast.unparse(node.args[0])]
    check(len(calls(run, 'fresh_native')) == 1 and len(acceptance) == 1 and calls(run, 'fresh_native')[0].lineno < acceptance[0].lineno,
          'Failed/partial XML is captured before strict Gradle0/fresh exact1-case acceptance')
    check(not calls(controller, 'packaged.run') and not calls(controller, 'lt.run'), 'Old consumer/library Stop run entrypoints excluded')
    initial_flags = assignment(run, 'record')
    flag_values = dict(zip((literal(key) for key in initial_flags.keys), initial_flags.values))
    for name in ('publication_ready', 'packages_published', 'full_native_corresponding_source_complete', 'security_or_API_ABI_clearance',
                 'release_readiness_certified', 'independent_lead_acceptance', 'accepted_private_library_Stop_replayed', 'automatic_retries'):
        check(literal(flag_values[name]) is False, 'Material/acceptance gate remains false in source: ' + name)
    update = [node for node in calls(run, 'record.update') if any(keyword.arg == 'detached_process_absence_verified' for keyword in node.keywords)]
    check(len(update) == 1, 'One explicit final material-limit report')
    final_flags = {keyword.arg: keyword.value for keyword in update[0].keywords}
    for name in ('detached_process_absence_verified', 'dependency_verification_metadata_qualified', 'all_five_host_graphs_verified'):
        check(literal(final_flags[name]) is False, 'No inferred missing final gate: ' + name)
    check(row(controller_raw) == {'bytes': 28533, 'sha256': '628bb308bbaabf3f4d4e35063c0253d28439746d5a4ce54846fec092ea8f0a14'},
          'Controller byte-identical through formatter/lint correction, including correct producer marker regex')

    control_raw = read(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py', 'final-owning-NEW-control-AST-only')
    correction = json.loads(read(PACKET / 'CORRECTION-FAILED-AND-CHANGED2-RECIPE658.json', 'retained-exact2-AST-and-fragment-recovery'))
    check(row(control_raw) == {key: correction['final_source_controls'][key] for key in ('bytes', 'sha256')}, 'Final control postimage bound to exact failed/changed2 recipe')
    doc_raw = read(PACKET / 'proposed/docs/testing/javafx-ordinary-windows-route.md', 'unchanged-route-material-limits-document')
    check(row(doc_raw) == {'bytes': 9934, 'sha256': 'f4e7a54782f7d8b25402394b62a2140acb55669dad4218ddea7159ccf7443c20'}, 'Canonical doc byte-identical through recovery')
    route_sources = {
        '.github/workflows/javafx-library-candidate.yml': workflow,
        'scripts/ci/javafx_ordinary_maven_consumer.py': controller_raw,
        'scripts/ci/test_javafx_ordinary_maven_route.py': control_raw,
        'docs/testing/javafx-ordinary-windows-route.md': doc_raw,
    }
    check({path.relative_to(PACKET / 'proposed').as_posix() for path in (PACKET / 'proposed').rglob('*') if path.is_file()} == set(route_sources),
          'Canonical proposed inventory contains exactly route4; no standalone workflow/pycache/native additions')
    source_files = {name: dict(value) for name, value in authority['source_files'].items()}
    for name, value in source_files.items():
        payload = read(value['source_path'], 'unchanged-exact12-donor-source')
        check(row(payload) == {key: value[key] for key in ('bytes', 'sha256')} and value['expected_mode'] == '0644' and value['root_preimage'] is None,
              'Exact12 donor bytes and prospective0644 NEW preimage contract: ' + name)
        value.update(expected_git_mode='100644', source_mode_observed=inputs[value['source_path']]['actual_read_mode'],
                     source_authority_sha256=digest(authority_raw), donor_is_copied_exactly_without_source_patch=True)
    for name, payload in route_sources.items():
        existing = name == '.github/workflows/javafx-library-candidate.yml'
        source_files[name] = {**row(payload), 'source_path': str(PACKET / 'proposed' / name),
                              'destination_action': 'Exact-predecessor workflow derivative' if existing else 'NEW addition, not overwrite',
                              'origin': '658 final registered ordinary consumer1 route', 'expected_mode': '0644', 'expected_git_mode': '100644',
                              'source_mode_observed': inputs[str(PACKET / 'proposed' / name)]['actual_read_mode'],
                              'root_preimage': {**row(predecessor), 'source_path': str(PACKET / derivative['preimage']['retained_path']),
                                                'expected_destination_mode': '0644', 'expected_git_mode': '100644'} if existing else None}
    check(len(source_files) == 16 and sum(value['bytes'] for value in source_files.values()) == 232222,
          'Current16 union is232222B: unchanged12=161381B plus route4=70841B')
    check(sum(value['root_preimage'] is None for value in source_files.values()) == 15,
          'Exactly15 NEW additions plus one exact existing-workflow derivative')

    locators = {
        'registered_one_ref_workflow': {'metadata': 'REGISTERED-WORKFLOW-DERIVATIVE658.json',
                                        'locator': 'retained/javafx-library-candidate.before-finite-refs.yml', 'sha256': '23786c9a0ad877416567333ccb5c3d18439edb1a268d94ff9a9d0e8873fad99d'},
        'registered_two_ref_pre_recovery_workflow': {'metadata': 'REGISTERED-WORKFLOW-TWO-REF-DERIVATIVE658.json',
                                                    'locator': 'retained/javafx-library-candidate.before-actionlint-recovery658.yml', 'sha256': 'd1aef6e7372b0dd1be9338a44a280266c61997e00fb0921c1c4b9903af807363'},
        'first_NEW10_source_controls': {'metadata': 'FIRST-NEW10-SOURCE658/result.json',
                                       'locator': 'retained/test_javafx_ordinary_maven_route.before-failed-fixture-recovery658.py', 'sha256': '08ff18873b84f8d78a28c689d3cf2466583add6baba3235d98542d6f43a125f4'},
        'registered_one_ref_controller': {'metadata': 'REGISTERED-WORKFLOW-TWO-REF-DERIVATIVE658.json',
                                          'locator': 'retained/javafx_ordinary_maven_consumer.before-finite-refs.py', 'sha256': '6683a79aa07d2f9b291811c5d029a47e2dc729c21df7552e326b3914ae733002'},
        'registered_one_ref_document': {'metadata': 'REGISTERED-WORKFLOW-TWO-REF-DERIVATIVE658.json',
                                       'locator': 'retained/javafx-ordinary-windows-route.before-finite-refs.md', 'sha256': '0dfa58a7ab0feabbba2c4240e4b531dec2f8a3caa80a2946fa8f47b7f7cc238c'},
        'registered_one_ref_controls': {'metadata': 'REGISTERED-WORKFLOW-TWO-REF-DERIVATIVE658.json',
                                       'locator': 'retained/test_javafx_ordinary_maven_route.before-finite-refs.py', 'sha256': '86900fdac65295f8b3c3112daf4f9035bca7ffcd7a9699f1e265dadc53b02d2f'},
    }
    for name, value in locators.items():
        check(digest(read(PACKET / value['locator'], 'exact-retained-historical-postimage-locator')) == value['sha256'],
              'Historical precursor exact postimage locator held: ' + name)
    write_json('HISTORICAL-POSTIMAGE-LOCATORS658.json', {'schema': 'nativecmpkit-javafx-historical-postimage-locators658-v1', 'locators': locators,
                                                       'historical_metadata_source_paths_are_not_current_adoption_instructions': True,
                                                       'final_adoption_authority': RECIPE_NAME})
    write_json('PASSIVE-NAMED-AUTHORITY-README-ABSENCE658.json', {
        'schema': 'nativecmpkit-javafx-local-named-optional-reference-absence658-v1',
        'named_path': str(AUTHORITY.parent / 'README.md'), 'original_command_exit_code': 1,
        'cause': 'Optional named authority README was absent; directory inventory and actual JSON recipe remain available',
        'network_or_Git_reacquisition': False, 'retry': False, 'test_or_native_failure': False,
        'correction': 'Use exact JSON recipe and lead-provided cached620 seal; no guessed broader lookup'})

    registration_path = Path('/root/nativecmpkit-source-proposals-20261104/lead-workflow-registration-20261104/WORKFLOW-REGISTRATION.json')
    registration_raw = read(registration_path, 'once-acquired-existing-workflow-registration-only')
    check(digest(registration_raw) == '6bd756c3fc5491bd9544470bc31336f05ac50d0fd5436ee46bbf8ccfbf94a020', 'Once-acquired registration observation reused, not reacquired')
    current_recipe = {
        'schema': 'nativecmpkit-javafx-current16-exact-source-adoption-recipe658-v1', 'utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Unadopted independent-worktree source recipe only; exact source controls/Actionlint results are separate, ZERO compiler/stage/native/dispatch/issue/security acceptance',
        'adopted': False, 'ROOT_writes': 0, 'Git_GitHub_or_network_mutations_or_queries': 0,
        'combined_file_count': 16, 'combined_source_bytes': 232222, 'unchanged_authoritative_source_count': 12,
        'unchanged_authoritative_source_bytes': 161381, 'route_source_count': 4, 'route_source_bytes': 70841,
        'NEW_additions': 15, 'exact_existing_workflow_derivatives': 1, 'source_files': source_files,
        'destination_mode_policy': 'Preserve each actual existing independent-worktree destination mode; expected workflow0644/Git100644. All NEW files0644/Git100644. Donor0600 is not a destination policy.',
        'source_adoption_target': {'worktree': '/root/nativecmpkit-worktrees/javafx-ordinary-consumer1',
                                   'branch': 'development/javafx-ordinary-consumer1',
                                   'lead_reported_clean_base_HEAD': '086224e97cf74c1cc30277b4c6b321867de725df',
                                   'base_identity_authority': 'Lead message only, not queried by658; not a mandatory future driver HEAD pin',
                                   'lead_and_705_must_verify_actual_destination_preimages_modes_and_15_absences': True,
                                   'ROOT086_producer_Camera_Android_cohort_must_not_be_mutated': True},
        'original_exact12_authority': {**row(authority_raw), 'path': str(AUTHORITY),
                                      'saved_historical_HEAD': authority['expected_root_head'], 'saved_historical_tree': authority['expected_root_tree'],
                                      'historical_source_identity_not_future_mandatory_HEAD_pin': True},
        'cached_independent620_authority': {**row(review620_raw), 'path': str(REVIEW620),
                                            'scope': 'Original33 exact source coordinate spans/inverses and independent pins, not ordinary-native/security acceptance'},
        'workflow_derivative': {'destination': '.github/workflows/javafx-library-candidate.yml',
                                'preimage': row(predecessor), 'postimage': row(workflow), 'fragments': derivative['fragments'],
                                'existing_source_fragment_record': {**row(derivative_raw), 'path': 'REGISTERED-WORKFLOW-FINAL-DERIVATIVE658.json'},
                                'complete_old_public_stop_job': {**row(old_job), 'accepted_whitelist': ['linux-arm64', 'macos-arm64', 'macos-x64', 'windows']},
                                'old_push_guards_defaults_permissions_concurrency_and_all_other_old_bytes_held': True},
        'manual_policy': {'repository': 'Apdelrahman1911/nativeCmpkit', 'event': 'workflow_dispatch', 'exact_refs': list(manual_refs),
                          'only_NEW_choice': 'windows-ordinary-consumer1', 'only_NEW_job': 'ordinary-windows-consumer1',
                          'main_tags_foreign_or_near_match_refs_allowed': False, 'old_private_Windows_library_Stop_replayed': False},
        'existing_workflow_registration_observation': {**row(registration_raw), 'path': str(registration_path),
                                                       'workflow_id': 404301928, 'observed_name': 'NativeCmpKit Windows JavaFX library candidate',
                                                       'returned_active': 4, 'reused_not_reacquired': True,
                                                       'NEW_branch_input_job_adopted_and_actual_dispatch_HEAD_input_confirmed': False},
        'actual_source_validation': {'first_NEW10': {'requested': 10, 'passed': 9, 'failed': 1, 'unittest_seconds': 0.112,
                                                     'result': result_bindings['FIRST-NEW10-SOURCE658']},
                                     'onlyfailed_changed2': {'requested': 2, 'passed': 2, 'failed': 0, 'unittest_seconds': 0.026,
                                                             'result': result_bindings['ONLYFAILED-CHANGED2-SOURCE-RECOVERY658']},
                                     'initial_Actionlint_failed': result_bindings['FIRST-ACTIONLINT658'],
                                     'onlyfailed_Actionlint_passed': result_bindings['ONLYFAILED-ACTIONLINT-RECOVERY658'],
                                     'eight_unchanged_passing_methods_reused_not_replayed': True,
                                     'fresh10green_or_old67replay_claimed': False, 'audit_denied_attempts': 0,
                                     'finite_source_maps_are_not_Git_global_compiler_or_native_maps': True},
        'future_only_native_method': {'class': 'nativecmpkit.consumer.OrdinaryCuredWebStopConsumerTest',
                                     'method': 'normalMavenActivationBindsCuredPublicStopTransportAndOwnedLifetime',
                                     'module_mode_only': True, 'POM_reuse_only_for_complete_identical_four_classpath_byte_graph': True},
        'material_gates': {'actual_compiler_stage_native_or_consumer_execution': False, 'detached_process_absence_verified': False,
                           'dependency_verification_metadata_qualified': False, 'all_five_host_graphs_verified': False,
                           'full_native_corresponding_source_complete': False, 'security_or_API_ABI_clearance': False,
                           'release_readiness_certified': False, 'independent_lead_acceptance': False, 'publication_ready': False,
                           'packages_published': False, 'issue64_closed': False},
        'lead_only_remaining_gates': ['705 independent exact-source/results/target review', 'lead original review and exact source adoption/freeze/push',
                                      'applicable compiler preparation', 'reviewed producer plus required same-HEAD missing Camera/Android completion',
                                      'fresh combined all-status max2 INCLUDING queued/reserved capacity', 'actual NEW manual branch/HEAD/input readback',
                                      'actual Windows real module/POM graphs and strict fresh1-method XML/originals review',
                                      'all existing publication/Pages/main/history/native/consumer/API-ABI/dependency/legal/security/readiness gates'],
    }
    write_json(RECIPE_NAME, current_recipe)
    for name, expected in dict(inputs).items():
        raw = Path(name).read_bytes()
        check(row(raw) == {key: expected[key] for key in ('bytes', 'sha256')}, 'Final passive review actual named input held: ' + name)
    review = {'schema': 'nativecmpkit-javafx-final-current16-passive-source-results-review658-v1', 'utc': datetime.now(timezone.utc).isoformat(),
              'passed': True, 'checks': checks, 'check_count': len(checks), 'actual_named_input_count': len(inputs), 'named_inputs_held': True,
              'inputs': inputs, 'ROOT_named_absences_held': recovery_qualified['ROOT_destinations_absent'],
              'recipe': RECIPE_NAME, 'actual_command_results': result_bindings,
              'scope': 'Final passive AST/text/JSON/hash source/result custody only. Not controller qualification, target adoption, Git/global/native/compiler map or #64/security acceptance.',
              'new_tests_lint_build_stage_native_or_target_imports_by_this_review': 0,
              'ROOT_Git_network_dispatch_publication_mutations_or_queries': 0, 'independent705_acceptance_yet': False}
    write_json('FINAL-PASSIVE-SOURCE-RESULTS-REVIEW658.json', review)
    write_json('FINAL16-SOURCE-RESULTS-SEAL658.json', {
        'schema': 'nativecmpkit-javafx-small-final16-source-results-seal658-v1', 'utc': datetime.now(timezone.utc).isoformat(),
        'adoption_recipe': {**row((PACKET / RECIPE_NAME).read_bytes()), 'path': RECIPE_NAME},
        'source_count': 16, 'source_bytes': 232222,
        'source_files': {name: {key: value[key] for key in ('bytes', 'sha256', 'source_path', 'expected_mode', 'expected_git_mode', 'root_preimage')}
                         for name, value in source_files.items()},
        'actual_results': result_bindings,
        'passive_final_review': {**row((PACKET / 'FINAL-PASSIVE-SOURCE-RESULTS-REVIEW658.json').read_bytes()), 'path': 'FINAL-PASSIVE-SOURCE-RESULTS-REVIEW658.json',
                                 'check_count': review['check_count'], 'actual_named_inputs': review['actual_named_input_count']},
        'cached620_source_only': current_recipe['cached_independent620_authority'],
        'old_Stop_accepted_population_replayed': False, 'ordinary_native_executions': 0,
        'independent705_or_lead_acceptance_claimed': False, 'publication_or_issue64_closure': False,
        'scope': 'Portable source/result pins; no native/compiler/adoption/security claim. Full external custody is PACKET-SEAL658.json.',
    })
    print(json.dumps({'passed': True, 'passive_checks': review['check_count'], 'actual_named_inputs': review['actual_named_input_count'],
                      'source_count': 16, 'source_bytes': 232222, 'recipe': row((PACKET / RECIPE_NAME).read_bytes()),
                      'small_seal': row((PACKET / 'FINAL16-SOURCE-RESULTS-SEAL658.json').read_bytes())}, sort_keys=True))
except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
    write_json('FINAL-PASSIVE-SOURCE-RESULTS-REVIEW658-REFUSAL.json', {'passed': False, 'error_type': type(error).__name__,
                                                                  'check_count': len(checks), 'checks': checks,
                                                                  'last_check': checks[-1] if checks else None,
                                                                  'no_test_lint_build_native_or_target_execution': True})
    raise
