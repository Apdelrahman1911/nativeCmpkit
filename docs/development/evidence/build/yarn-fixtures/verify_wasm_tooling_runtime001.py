#!/usr/bin/env python3
"""Independently read back the lead's completed Wasm tooling run; never rerun it.

Only standard-library file/JSON/ZIP reads and optional exclusive receipt creation.
No subprocess, Gradle, Groovy, Node/Yarn, network, fixture or policy execution.
Lock counts below are lexical observations, not a Yarn parser or closure check.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shlex
import sys
import zipfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
ARCHIVE = ROOT / 'docs/development/evidence/wasm-tooling-001'
RUN = ROOT / 'build/wasm-tooling-runtime-001'
PROPOSAL = ROOT / 'scripts/dependencies/yarn/tooling-receipt-init-proposal-v2.md'
PROPOSAL_SHA = 'e1697dc6345bc9e5fb4f2b78a2f3ea86f796929184e272fdfc634afbc32d338d'
KGP = Path('/root/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-gradle-plugin/2.4.20/d64b6d447eecf2b0f6d19bdd677cae3bbce37585/kotlin-gradle-plugin-2.4.20-gradle96.jar')
NODE = '/root/.gradle/nodejs/node-v24.16.0-linux-x64/bin/node'
YARN = '/root/.gradle/yarn/yarn-v1.22.22/bin/yarn.js'
EXTERNAL = {KGP, Path(NODE), Path(YARN),
            Path('/root/.gradle/yarn/yarn-v1.22.22/lib/cli.js'),
            Path('/root/.gradle/yarn/yarn-v1.22.22/lib/v8-compile-cache.js'),
            Path('/root/.gradle/yarn/yarn-v1.22.22/package.json'),
            Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java'),
            Path('/tmp/nativecmpkit-wasm-tooling-run001.py')}
checks = 0
inputs = {}


def check(ok, message):
    global checks
    checks += 1
    if not ok:
        raise ValueError(message)


def path_for(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    check('..' not in path.parts and (path.is_relative_to(ROOT) or path in EXTERNAL), 'Unexpected input scope')
    check(path.is_file() and not path.is_symlink() and not any(p.is_symlink() for p in path.parents), 'Missing/symlink input: ' + str(path))
    return path


def bind(path, expected=None):
    path = path_for(path)
    h = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
            size += len(block)
    meta = {'sha256': h.hexdigest(), 'bytes': size}
    name = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    check(name not in inputs or inputs[name] == meta, 'Input changed during readback: ' + name)
    if expected is not None:
        check(meta['sha256'] == expected, 'Hash mismatch: ' + name)
    inputs[name] = meta
    return meta


def read(path):
    path = path_for(path)
    meta = bind(path)
    data = path.read_bytes()
    check(hashlib.sha256(data).hexdigest() == meta['sha256'], 'Input changed while reading')
    return data


def document(path):
    return json.loads(read(path))


def verify():
    bind(ARCHIVE / 'archive.json', '09dc2a49c6d7ecf47e5f1fd31f2821c07d8eb23c4583ecf3dd4799f6c32eba0f')
    bind(ARCHIVE / 'SHA256SUMS', '3f5200eafdcf61d9fa7518d2f3935a93825950c15de5d38222eff7b3d27d9b67')
    manifest = {}
    for line in read(ARCHIVE / 'SHA256SUMS').decode().splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        check(match is not None, 'Malformed archive manifest')
        digest, name = match.groups()
        check(not Path(name).is_absolute() and '..' not in Path(name).parts and name not in manifest, 'Unsafe/duplicate archive name')
        manifest[name] = digest
        bind(ARCHIVE / name, digest)
    check(len(manifest) == 13, 'Unexpected archive manifest count')
    actual_files = {str(p.relative_to(ARCHIVE)) for p in ARCHIVE.rglob('*') if p.is_file()}
    check(actual_files == set(manifest) | {'SHA256SUMS'}, 'Unlisted/missing archived file')
    archive = document(ARCHIVE / 'archive.json')
    check(len(archive['archive_pairs']) == 11, 'Archive pair count changed')
    for pair in archive['archive_pairs']:
        check(manifest[pair['archive']] == pair['sha256'], 'Pair/manifest mismatch')
        check(bind(ARCHIVE / pair['archive'], pair['sha256'])['bytes'] == pair['bytes'], 'Archived byte count changed')
        check(bind(pair['source'], pair['sha256'])['bytes'] == pair['bytes'], 'Local source/copy differs')
    context = document(ARCHIVE / 'context.json')
    result = document(ARCHIVE / 'result.json')
    before = document(ARCHIVE / 'inputs-before.json')
    after = document(ARCHIVE / 'inputs-after.json')
    check(before == after and len(before) == 691, 'Selected before/after inputs differ')
    check(archive['selected_inputs_count'] == context['selected_input_count'] == result['selected_input_count'] == 691, 'Input counts differ')
    check(result['changed_inputs'] == [] and result['extra_input_changes'] == [], 'Recorded input mutation')
    for name, digest in before.items():
        check(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unexpected selected source path')
        bind(name, digest)
    check(len(context['extra_inputs']) == archive['extra_inputs_rechecked'] == 12, 'Extra-input count differs')
    for name, digest in context['extra_inputs'].items():
        bind(name, digest)
    check(context['source_revision'] == result['source_revision_after'] == archive['source_revision'], 'Recorded base revision changed')
    check(context['dirty_source'] is True and archive['dirty_source'] is True, 'Dirty-source qualification lost')

    bind(PROPOSAL, PROPOSAL_SHA)
    blocks = re.findall(rb'```groovy\n(.*?)\n```', read(PROPOSAL), re.S)
    placeholder = b'/REPLACE_WITH_LEAD_ALLOCATED_ABSOLUTE_RUN_ROOT'
    check(len(blocks) == 1 and blocks[0].count(placeholder) == 1, 'Ambiguous proposal extraction')
    transformed = blocks[0].replace(placeholder, str(RUN).encode()) + b'\n'
    check(transformed == read(ARCHIVE / 'observe-tooling.init.gradle'), 'Init script differs beyond exact run-root substitution')
    check(context['command'] == archive['command'], 'Archived commands differ')
    command = context['command']
    check(command[:3] == ['./gradlew', ':kotlinWasmToolingSetup', '--rerun-tasks'], 'Unexpected root command')
    check(command[-2:] == ['--init-script', str(RUN / 'observe-tooling.init.gradle')], 'Wrong init-script argument')
    check('-Pkotlin.user.home=' + str(RUN / 'kotlin-user-home') in command, 'Wrong Kotlin home property')
    check('--no-configuration-cache' in command and '--info' in command and '--max-workers=2' in command, 'Required command flags absent')
    check(context['timeout_seconds'] == 300 and context['reserve_mib'] == 8192, 'Configured bounds differ')
    check(min(context['free_bytes_before'], result['free_bytes_after']) >= 8192 * 1024**2, 'Recorded endpoint reserve too low')
    check(context['kotlin_home_existed_before'] is False, 'Recorded Kotlin home was not fresh')
    check(result['execution'] == archive['execution'] == {'elapsed_seconds': 94.94, 'exit_code': 0}, 'Unexpected recorded execution result')
    started = dt.datetime.fromisoformat(result['started_utc'])
    finished = dt.datetime.fromisoformat(result['finished_utc'])
    check(abs((finished - started).total_seconds() - 94.94) < 0.02, 'Execution timestamps disagree')
    check(result['gradle_success'] is True, 'Gradle result not successful')

    names = {'requested-task.json', 'tooling-pre-action.json', 'tooling-task-outcome.json'}
    check(set(result['receipt_files']) == names, 'Receipt set differs')
    check({p.name for p in (RUN / 'receipts').iterdir()} == names, 'Unexpected live receipt entry')
    receipts = {name: document(ARCHIVE / 'receipts' / name) for name in names}
    identity = {'settingsDir': str(ROOT), 'buildPath': ':', 'topLevelBuild': True}
    for name, receipt in receipts.items():
        check(receipt['schemaVersion'] == 2 and receipt['scopeHook'] == 'Gradle.beforeSettings', 'Wrong receipt schema/hook')
        check(receipt['buildIdentity'] == identity, 'Receipt belongs to wrong build')
        stamp = dt.datetime.fromisoformat(receipt['observedUtc'].replace('Z', '+00:00'))
        check(started < stamp < finished, 'Receipt outside execution window')
        bind(ARCHIVE / 'receipts' / name, result['receipt_files'][name]['sha256'])
    request = receipts['requested-task.json']
    pre = receipts['tooling-pre-action.json']
    outcome = receipts['tooling-task-outcome.json']
    check(request['taskNames'] == [':kotlinWasmToolingSetup'] and request['excludedTaskNames'] == [], 'Wrong request/exclusions')
    check(request['rerunTasks'] and not request['dryRun'] and not request['configurationCacheRequested'], 'Wrong request flags')
    check(request['kotlinUserHome'] == str(RUN / 'kotlin-user-home'), 'Receipt home differs')
    graph = [':kotlinWasmNodeJsSetup', ':kotlinWasmYarnSetup', ':kotlinWasmToolingSetup']
    check(pre['graphTaskPaths'] == archive['root_graph_task_paths'] == graph, 'Actual root graph differs')
    check(pre['taskPath'] == outcome['taskPath'] == ':kotlinWasmToolingSetup', 'Wrong observed target')
    check(pre['args'] == [] and pre['yarnResolutions'] == [] and pre['yarnStandalone'] is False and pre['ignoreScripts'] is True, 'Environment assumptions differ')
    check(pre['nodeExecutable'] == NODE and pre['yarnExecutable'] == YARN, 'Selected executable path differs')
    destination = RUN / 'kotlin-user-home/kotlin-npm-tooling/yarn/9c7852378f220e63c4f92e7d93026c2f'
    check(pre['destination'] == str(destination) and pre['nodeModules'] == str(destination / 'node_modules'), 'Wrong destination/modules')
    check(pre['nodeModulesExisted'] is False, 'Node modules not absent before action')
    check(outcome['executed'] and outcome['didWork'] and not outcome['skipped'] and not outcome['upToDate'] and not outcome['noSource'] and outcome['failureType'] is None, 'Task was skipped or failed')
    check(request['actualProcessObserved'] is False and pre['actualProcessObserved'] is False and outcome['actualProcessObservedByThisListener'] is False, 'Listener overclaims process proof')

    log_path = archive['raw_local_log']['path']
    bind(log_path, archive['raw_local_log']['sha256'])
    raw = read(log_path)
    check(len(raw) == result['raw_log_bytes'] and hashlib.sha256(raw).hexdigest() == result['raw_log_sha256'], 'Raw log binding differs')
    lines = raw.decode().splitlines()
    sanitized = read(ARCHIVE / 'gradle.sanitized.log').decode().splitlines()
    position = 0
    for line in sanitized:
        check(line in lines[position:], 'Sanitized line not an ordered exact raw-log excerpt')
        position = lines.index(line, position) + 1
    starts = [(i + 1, line) for i, line in enumerate(lines) if line.startswith("Starting process 'command '" + NODE + "''.")]
    check(len(starts) == 1, 'Unexpected selected Node launch count')
    line_number, launch_line = starts[0]
    launch = re.fullmatch(r"Starting process 'command '(.+)''\. Working directory: (.+) Command: (.+)", launch_line)
    check(launch is not None, 'Cannot read actual launch line')
    executable, cwd, argv_text = launch.groups()
    argv = shlex.split(argv_text)
    expected_argv = [NODE, YARN, '--ignore-scripts', '--network-concurrency', '1', '--mutex', 'network']
    observed = archive['observed_gradle_process_launch']
    check(executable == NODE and argv == observed['argv'] == expected_argv, 'Actual logged argv differs')
    check(cwd == observed['cwd'] == str(destination), 'Actual logged cwd differs')
    check(hashlib.sha256(launch_line.encode()).hexdigest() == observed['start_line_sha256'], 'Launch-line hash differs')
    started_line = "Successfully started process 'command '" + NODE + "''"
    check(lines.count(started_line) == observed['successful_start_message_count'] == 1, 'Successful-start receipt differs')
    task_lines = [line for line in lines if line.startswith('> Task ')]
    check(task_lines == result['task_lines'], 'Task log summary differs')
    check('> Task :convention-plugins:compileKotlin' in task_lines, 'Convention compilation not observed')
    check([line.split()[2] for line in task_lines if not line.startswith('> Task :convention-plugins:')] == graph, 'Unexpected non-convention task')
    check('BUILD SUCCESSFUL in 1m 34s' in lines and '12 actionable tasks: 12 executed' in lines, 'Terminal Gradle log result differs')

    for row in result['output_files']:
        check(bind(RUN / row['path'], row['sha256'])['bytes'] == row['bytes'], 'Output hash/size differs')
    package = document(ARCHIVE / 'generated/package.json')
    check(package['private'] is True and len(package['dependencies']) == 24, 'Generated root dependency count differs')
    lock = read(ARCHIVE / 'generated/yarn.lock')
    with zipfile.ZipFile(KGP) as jar:
        embedded = jar.read('org/jetbrains/kotlin/gradle/targets/js/yarn/yarn.lock')
    check(lock == embedded and len(lock) == 160311, 'Output lock is not byte-identical to pinned embedded lock')
    resolved = len(re.findall(rb'^  resolved ', lock, re.M))
    integrity = len(re.findall(rb'^  integrity ', lock, re.M))
    check((resolved, integrity) == (489, 488), 'Tooling lexical lock counts differ')
    lock_lines = lock.decode().splitlines()
    karma_url = 'https://codeload.github.com/Kotlin/karma/tar.gz/239a8fc984584f0d96b1dd750e7a5e2c79da93a6'
    karma_index = lock_lines.index('  resolved "' + karma_url + '"')
    begin = end = karma_index
    while begin > 0 and lock_lines[begin - 1].strip():
        begin -= 1
    while end + 1 < len(lock_lines) and lock_lines[end + 1].strip():
        end += 1
    check(lock_lines[begin] == '"karma@github:Kotlin/karma#6.4.5":', 'Unexpected Karma stanza')
    check(not any(line.startswith('  integrity ') for line in lock_lines[begin:end + 1]), 'Karma SRI assumption changed')
    primary = read(ROOT / 'kotlin-js-store/wasm/yarn.lock')
    check(len(re.findall(rb'^  resolved ', primary, re.M)) == 2, 'Primary Wasm graph count differs')

    preserved = {
        'scripts/dependencies/yarn/tooling-receipt-init-proposal.md': '7febc84a82896342a38e42bcd328eb9a77e91e4127577a1b3720c643e9727af1',
        'docs/development/evidence/build/yarn-fixtures/wasm-tooling-init-api-review.json': '6354cf0d56f11e116c3c4df218edba1debffb01b701e9cb95eca8b03ed68522e',
        'docs/development/evidence/build/yarn-fixtures/documentation-verification001.json': 'f05ddb3fe38ce51e8c59e010655d7eeb6396169df1a850e60481b4686b18d092',
        'docs/development/evidence/build/yarn-fixtures/tooling-scope-verification002.json': 'c2f4b2a9e2ca88d83ff89462c6a254bdcc5b6a1b1328fe1eea52631eba6e23ac',
        'docs/development/evidence/build/yarn-fixtures/documentation-verification002.json': '53ba0321b030917f235bfaa14c38a973b1ef6c798f79570057863cdb72f1e082'}
    for path, digest in preserved.items():
        bind(path, digest)
    review_path = context['review_at_start']['path']
    current_review = bind(review_path, 'c8edade1ce1c9f7a41542aace597909afdfede8ef022368bfc1a7105f7419199')
    for flag in ('ordinary_policy_adopted', 'ordinary_frozen_or_closure_enforcement_verified',
                 'independent_provenance_verified', 'release_verified'):
        check(archive[flag] is False, 'Archive overclaims verification: ' + flag)
    check(archive['library_tests_executed'] == result['library_tests_executed'] == 0, 'Install must not count as library tests')
    for path, meta in list(inputs.items()):
        bind(path, meta['sha256'])
    return {
        'archive_manifest_entries_verified': 13, 'archive_source_copies_verified': 11,
        'selected_inputs_before_after_equal': 691, 'selected_inputs_currently_hash_equal': 691,
        'extra_inputs_currently_hash_equal': 12, 'inspected_inputs_rehashed_at_end': True,
        'historical_source_revision': archive['source_revision'], 'dirty_source': True,
        'execution_from_bound_lead_records': result['execution'],
        'configured_timeout_seconds': 300, 'configured_reserve_mib': 8192,
        'exact_v2_snippet_substitution': True, 'executed_init_script_sha256': hashlib.sha256(transformed).hexdigest(),
        'root_receipt_count': 3, 'root_build_identity': identity, 'root_graph_task_paths': graph,
        'included_build_evidence': 'Convention compileKotlin task observed with one set of exclusive root receipts; included callback not independently instrumented.',
        'actual_launch_log': {'path': log_path, 'line': line_number, 'argv': argv, 'cwd': cwd,
                              'start_line_sha256': observed['start_line_sha256'], 'successful_start_message_count': 1,
                              'os_process_attach_or_instrumentation': False},
        'actual_ignore_scripts_flag_observed': True, 'actual_frozen_lockfile_flag_observed': False,
        'output_lock_matches_embedded_kgp_bytes': True, 'output_lock_bytes': len(lock),
        'output_lock_sha256': hashlib.sha256(lock).hexdigest(), 'generated_root_dependencies': 24,
        'lexical_tooling_resolved_entries': resolved, 'lexical_tooling_integrity_entries': integrity,
        'karma_resolved_url': karma_url, 'karma_stanza_lines': [begin + 1, end + 1], 'karma_integrity_field_present': False,
        'lexical_primary_wasm_resolved_entries': 2, 'primary_wasm_lock_sha256': hashlib.sha256(primary).hexdigest(),
        'review_at_start_binding_limit': {
            'path': review_path, 'recorded_historical_sha256': context['review_at_start']['sha256'],
            'current_sealed_sha256': current_review['sha256'],
            'earlier_whole_file_bytes_reverified': False,
            'explanation': 'At-start reviewer JSON was subsequently finalized; its earlier whole-file bytes are not included in the 13-file runtime archive. Current sealed bytes are not substituted for the older hash. Exact v2 proposal/init hashes are independently bound.'},
        'limits': ['One recorded successful cold tooling invocation, not negative-context/reuse/mixed-task tests or an all-configuration boundary.',
                   'Gradle --info launch evidence plus receipts/output hashes, not OS instrumentation or per-package script-marker controls.',
                   'No --frozen-lockfile in the actual argv; embedded-lock equality is not frozen policy, closure validation or tamper rejection.',
                   '489/488 and primary Wasm 2 are lexical counts, not a parser, package provenance review or feature/runtime coverage.',
                   'Fresh task-owned Kotlin home does not isolate shared Gradle/Yarn caches, all network requests or OS context.',
                   '691 selected source/build inputs at a dirty base revision, not an immutable release candidate or every possible environmental input.',
                   'Raw full log and installed .yarn-integrity stay local; this review does not copy terminal transcripts, environment dumps or installed packages.',
                   'No library/native/browser/consumer/script-marker tests, policy adoption, BUILD-007 closure or release/publication verification.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report')
    args = parser.parse_args()
    if args.report:
        check(re.fullmatch(r'wasm-tooling-runtime001-review(?:[0-9]{3})?\.json', args.report), 'Invalid report name')
        check(not (BASE / args.report).exists() and not (BASE / args.report).is_symlink(), 'Existing report')
    record = {'schema_version': 1, 'reviewer': '/root/audit_history_architecture', 'argv': sys.argv,
              'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'review_scope': 'Independent readback of completed lead run; no new runtime invocation.',
              'reviewer_executed_gradle_groovy_node_yarn_or_network': False, 'reviewer_library_tests_executed': 0,
              'policy_adopted': False, 'independent_provenance_verified': False, 'build007_closed': False,
              'frozen_source_only_evidence_rewritten': False, 'error': None}
    try:
        record.update(verify())
    except Exception as exc:
        record['error'] = type(exc).__name__ + ': ' + str(exc)
    record.update(exit_code=1 if record['error'] else 0, data_checks=checks, inspected_file_hashes=inputs,
                  ended_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    if args.report:
        with (BASE / args.report).open('x') as stream:
            json.dump(record, stream, indent=2, sort_keys=True)
            stream.write('\n')
    print(json.dumps({key: record.get(key) for key in ('exit_code', 'error', 'data_checks',
                     'archive_manifest_entries_verified', 'selected_inputs_currently_hash_equal',
                     'exact_v2_snippet_substitution', 'actual_ignore_scripts_flag_observed',
                     'actual_frozen_lockfile_flag_observed', 'output_lock_matches_embedded_kgp_bytes')}, indent=2))
    return record['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
