"""Independent exact-Git, runtime, source-method and native IO/Coil JUnit review.

Review only already-executed evidence; do not execute/extract artifact content.
"""
from collections import Counter
from pathlib import Path, PurePosixPath
import datetime as dt
import hashlib
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('/root/projects/nativeCmpKit')
BASE = Path(__file__).parent
SOURCE = BASE / '40587910531'
OUT = SOURCE / 'archive'
DEST = ROOT / 'docs/development/evidence/github-actions/40587910531'
REV = 'fc73dd47cf35085e6f9e2b964ae126eefe2be246'
PREV = '8f389ef4159dc7ee8931437405197e10d2832570'
REPO = 'Apdelrahman1911/nativeCmpkit'
RUN = 40587910531
SLOT = 'ios-iphone'
SELECTED = ('calf-io', 'calf-file-picker-coil')


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.read_bytes()).hexdigest()


def document(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, 'Duplicate JSON key'
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def instant(value):
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    assert result.utcoffset() is not None
    return result


assert not OUT.exists() and not DEST.exists(), 'No evidence overwrites'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == REV
run = document((SOURCE / 'run-final.json').read_bytes())
jobs = document((SOURCE / 'jobs-final.json').read_bytes())['jobs']
artifacts = document((SOURCE / 'artifacts-final.json').read_bytes())['artifacts']
collected = document((SOURCE / 'collection.json').read_bytes())
assert run['id'] == RUN and run['head_sha'] == REV and run['run_attempt'] == 1
assert run['repository']['full_name'] == REPO and run['event'] == 'workflow_dispatch'
assert run['status'] == 'completed' and run['conclusion'] == 'success'
assert run['head_branch'] == 'development/preview-hardening'
assert collected['run_id'] == RUN and collected['source_revision'] == REV
assert collected['profile'] == 'ios-io' and collected['selected_job_count'] == 1
assert collected['artifact_digests_matched'] and len(artifacts) == 1
assert len(jobs) == 3 and next(j for j in jobs if j['name'] == 'tooling')['conclusion'] == 'success'
assert next(j for j in jobs if j['name'] == 'consumer-core-io')['conclusion'] == 'skipped'
job = next(j for j in jobs if j['id'] == collected['job_id'])
assert job['name'] == 'library-tests (ios-iphone, ios, macos-26, arm64, python3, iphone, calf-io,calf-file-picker-coil)'
assert job['run_attempt'] == 1 and job['status'] == 'completed' and job['conclusion'] == 'success'
steps = {s['name']: s['conclusion'] for s in job['steps']}
for name in ('Explicit dependency/compiler/runtime/slot-keyed cache',
             'Source-set-aware expected library tests (never samples)',
             'Fresh actual library suite with strict nonzero receipts',
             'Keep receipts and actual selected-task XML only; never packages'):
    assert steps[name] == 'success'
art = artifacts[0]
assert art['name'] == 'library-evidence-' + SLOT and not art['expired']
assert art['workflow_run']['id'] == RUN and art['workflow_run']['head_sha'] == REV
assert instant(job['started_at']) <= instant(art['created_at']) <= instant(art['updated_at']) <= instant(job['completed_at'])
zip_path = SOURCE / f"{art['id']}.zip"
assert zip_path.stat().st_size == art['size_in_bytes'] < 64 * 1024**2
assert 'sha256:' + sha(zip_path) == art['digest']
log = SOURCE / f"job-{job['id']}-log.log"
log_record = next(x for x in collected['logs'] if x['job_id'] == job['id'])
assert log_record['job_log_bytes'] == log.stat().st_size and log_record['job_log_sha256'] == sha(log)
assert log_record['job_conclusion'] == 'success' and not log_record['job_log_to_be_committed']

records = {}
for row in subprocess.check_output(['git', 'ls-tree', '-rz', REV], cwd=ROOT).split(b'\0'):
    if row:
        metadata, name = row.split(b'\t', 1)
        records[name.decode()] = metadata.decode().split()


def blob(name, revision=None):
    if revision:
        return subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT)
    mode, kind, oid = records[name]
    assert mode in {'100644', '100755'} and kind == 'blob'
    return subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)


with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-fc73dd47-io-review-', dir='/dev/shm') as directory:
    view = Path(directory)
    def materialize(name):
        path = view / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob(name))
    materialize('settings.gradle.kts')
    for name in records:
        if name.startswith('scripts/ci/') or (name.startswith(('calf-', 'sample/')) and name.endswith('/build.gradle.kts')):
            materialize(name)
    sys.path.insert(0, str(view / 'scripts/ci'))
    import library_tests as lt
    import dependency_cache_inputs as keys
    import native_test_policy as policy
    import runtime_context as rc
    projects = lt.projects(view)
    prefixes = ['gradle/', 'convention-plugins/', 'scripts/ci/', 'scripts/native/', 'kotlin-js-store/', '.cargo/']
    prefixes += [f'{module}/{folder}/' for module in projects for folder in ('src', 'native', '.cargo', 'gradle')]
    exact = set(lt.ROOT_INPUTS) | {f'{module}/{name}' for module in projects for name in ('build.gradle.kts', 'gradle.properties', 'gradle.lockfile')}
    exact |= {name for name in records if name.startswith('sample/') and name.count('/') == 2 and name.endswith('/build.gradle.kts')}
    for name in records:
        if (name in exact or any(name.startswith(prefix) for prefix in prefixes) or
                (name.startswith('sample/') and Path(name).name in keys.PROJECT_FILES)) and not set(PurePosixPath(name).parts[:-1]) & lt.IGNORED_INPUT_DIRS:
            materialize(name)
    inputs = lt.snapshot_inputs(view)
    assert len(inputs) == 733 and lt.input_digest(inputs) == 'eb487cbd8e4b3f01b2b6951f3a2b8462eb1fb6aa11923029212c3a465df54cdd'
    dep_inputs = keys.selected_inputs(view, 'libraries')
    dep_digest = keys.fingerprint('libraries', dep_inputs)
    selection = keys.selection_contract(view, 'calf-io,calf-file-picker-coil')
    plan = lt.plan(view, 'ios', only_modules=SELECTED)
    assert len(plan['expected']) == 2 and not plan['complete_suite_requested']
    methods = {}
    previous_ids = set()
    for item in plan['expected']:
        for name in item['test_source_files']:
            source = blob(name).decode()
            names = re.findall(r'@Test\s+fun\s+([A-Za-z0-9_]+)\s*\(', source)
            assert len(names) == len(re.findall(r'@Test\b', source)), 'Unrecognized actual test declaration'
            package = re.search(r'^package ([\w.]+)$', source, re.M).group(1)
            classname = 'iosSimulatorArm64Test.' + package + '.' + Path(name).stem
            methods[classname] = names
            old = subprocess.run(['git', 'show', PREV + ':' + name], cwd=ROOT, capture_output=True)
            if old.returncode == 0:
                previous_ids |= {(classname, x + '[iosSimulatorArm64]') for x in re.findall(
                    r'@Test\s+fun\s+([A-Za-z0-9_]+)\s*\(', old.stdout.decode())}
    assert len(methods) == 8 and sum(map(len, methods.values())) == 47
    assert len(previous_ids) == 28
    owning = {name: sha(blob(name)) for name in records if name.startswith(tuple(module + '/src/' for module in SELECTED))}
    assert all((ROOT / name).read_bytes() == blob(name) for name in owning)
    with zipfile.ZipFile(zip_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        assert len(names) == len(set(names)) == 17 and sum(entry.file_size for entry in entries) < 64 * 1024**2
        for entry in entries:
            path = PurePosixPath(entry.filename)
            assert not path.is_absolute() and not {'.', '..'} & set(path.parts) and '\\' not in entry.filename
            assert not entry.is_dir() and not entry.flag_bits & 1
            assert stat.S_IFMT(entry.external_attr >> 16) in {0, stat.S_IFREG}
            assert entry.filename.endswith(('.json', '.xml')) and entry.file_size <= lt.MAX_REPORT_BYTES
        def get(name):
            return document(archive.read(name))
        base = 'build/ci-verification/' + SLOT + '/'
        receipt = get(base + 'receipt.json')
        runtime, actual, selected = get(base + 'runtime.json'), get('build/ci-runtime/actual.json'), get('build/ci-runtime/selection.json')
        dependencies = get('build/ci-runtime/library-dependencies.json')
        assert get(base + 'inputs-before.json') == get(base + 'inputs-after.json') == inputs
        assert receipt['source_revision'] == receipt['source_revision_after'] == REV
        assert not receipt['source_tree_dirty'] and not receipt['changed_inputs']
        assert receipt['inputs_before_sha256'] == receipt['inputs_after_sha256'] == lt.input_digest(inputs)
        assert get(base + 'plan.json') == get('build/ci-plan/plan.json') == plan
        assert receipt['explicit_module_subset'] == list(SELECTED) and not receipt['complete_suite_requested']
        assert receipt['test_bearing_modules_not_requested'] == plan['test_bearing_modules_not_requested']
        assert dependencies['source_revision'] == REV and dependencies['scope'] == 'libraries'
        assert dependencies['inputs'] == dep_inputs and dependencies['dependency_input_count'] == len(dep_inputs)
        assert dependencies['dependency_inputs_sha256'] == dep_digest
        assert dependencies['selected_modules'] == selection['modules'] == ['calf-file-picker-coil', 'calf-io']
        assert dependencies['selection_cache_key'] == selection['cache_key']
        assert not dependencies['compiled_or_test_results_reused'] and not dependencies['ordinary_dependency_trust_certified']
        assert not dependencies['release_readiness_certified']
        assert receipt['runtime_receipt_sha256'] == sha(archive.read(base + 'runtime.json'))
        for context in (actual, runtime):
            assert context['source_revision'] == REV and not context['source_tree_dirty']
            assert context['compiler_runtime_fingerprint'] == rc.compiler_runtime_fingerprint(context)
            assert context['host']['system'] == 'Darwin' and context['host']['architecture'] == 'arm64'
            assert context['java']['major'] == 17 and context['rust']['release'] == '1.98.0'
            assert context['simulator']['state'] == 'Booted' and rc.UUID.fullmatch(context['simulator']['udid'])
            assert context['simulator']['device_type'].startswith('com.apple.CoreSimulator.SimDeviceType.iPhone')
            assert instant(job['started_at']) <= instant(context['observed_at_utc']) <= instant(job['completed_at'])
        assert {k for k in set(actual) | set(runtime) if actual.get(k) != runtime.get(k)} == {'observed_at_utc'}
        assert actual['compiler_runtime_fingerprint'] == runtime['compiler_runtime_fingerprint']
        assert actual['android_platform'] == runtime['android_platform'] and runtime['android_platform']['package'] == 'platforms;android-37.0'
        assert selected['source_revision'] == REV and selected['simulator']['udid'] == runtime['simulator']['udid']
        assert receipt['command'] == lt.gradle_command('ios', plan, simulator=runtime['simulator']['udid'], root=view)
        assert receipt['execution']['exit_code'] == 0 and not receipt['execution'].get('stop_reason')
        assert receipt['task_execution_markers'] == {':calf-io:iosSimulatorArm64Test': 1, ':calf-file-picker-coil:iosSimulatorArm64Test': 1}
        assert receipt['quarantined_prior_reports'] == [] and receipt['passed'] and receipt['errors'] == []
        assert receipt['uncovered'] == [] and receipt['ios_applications'] == []
        start, end = instant(receipt['started_at_utc']), instant(receipt['finished_at_utc'])
        assert instant(job['started_at']) <= start < end <= instant(job['completed_at'])
        assert len(receipt['modules']) == 2
        all_cases, stamps, native_cases = [], [], []
        module_results = {}
        for module in receipt['modules']:
            assert module['module'] in SELECTED
            expected = next(x for x in plan['expected'] if x['module'] == module['module'])
            assert module['task'] == expected['task']
            cases = []
            for report in module['reports']:
                assert report['path'].startswith(expected['report_directory'] + '/')
                payload = archive.read(report['path'])
                assert sha(payload) == report['sha256']
                parsed = lt.junit_cases(payload)
                assert all(report[key] == value for key, value in lt.case_counts(parsed).items())
                tree = ET.fromstring(payload, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
                assert start <= instant(tree.attrib['timestamp']) <= end
                assert not list(tree.iter('failure')) and not list(tree.iter('error')) and not list(tree.iter('skipped'))
                stamps.append({'path': report['path'], 'timestamp': tree.attrib['timestamp'], 'sha256': sha(payload)})
                cases += parsed
            assert sorted(cases, key=lambda c: (c['classname'], c['name'])) == sorted(module['testcases'], key=lambda c: (c['classname'], c['name']))
            counts = lt.case_counts(cases)
            assert all(module[key] == value for key, value in counts.items())
            scenarios, errors = policy.apply(module['module'], 'ios', cases, 'Darwin', False)
            assert not errors and scenarios == module['native_scenarios']
            assert all(x['required_on_host'] and x['disposition'] == 'required-executed' for x in scenarios)
            native_cases += scenarios
            all_cases += cases
            module_results[module['module']] = counts
        assert len(stamps) == 8 and {x['path'] for x in stamps} == {n for n in names if n.endswith('.xml')}
        totals = lt.case_counts(all_cases)
        assert len(all_cases) == len({(c['classname'], c['name']) for c in all_cases}) == 47
        assert totals == receipt['totals'] == {'tests': 47, 'failures': 0, 'errors': 0, 'skipped': 0,
            'passed': 47, 'executed': 47, 'not_applicable': 0, 'unexpected_skipped': 0}
        assert module_results['calf-io']['passed'] == 40 and module_results['calf-file-picker-coil']['passed'] == 7
        for cls, source_names in methods.items():
            found = [c for c in all_cases if c['classname'] == cls]
            assert len(found) == len(source_names)
            assert {c['name'] for c in found} == {n + '[iosSimulatorArm64]' for n in source_names}
            assert all(c['status'] == 'passed' for c in found)
        assert len(native_cases) == 22
        current_ids = {(c['classname'], c['name']) for c in all_cases}
        assert previous_ids < current_ids and len(current_ids - previous_ids) == 19
        expected_key = 'nativecmpkit-deps-v2-macOS-ARM64-' + SLOT + '-ios-' + selection['cache_key'] + '-' + actual['compiler_runtime_fingerprint'] + '-' + dep_digest
        console = log.read_text()
        misses = re.findall(r'Cache not found for input keys: ([^\r\n]+)', console)
        saved = re.findall(r'Cache saved with key: ([^\r\n]+)', console)
        assert misses == saved == [expected_key] and not re.search(r'Cache restored (?:from key|successfully)', console)
        assert 'ReserveCacheError' not in console

OUT.mkdir()
(OUT / 'raw').mkdir()
for name in ('run-final.json', 'jobs-final.json', 'artifacts-final.json', 'collection.json', f"{art['id']}.zip"):
    shutil.copyfile(SOURCE / name, OUT / 'raw' / name)
    assert sha(SOURCE / name) == sha(OUT / 'raw' / name)
shutil.copyfile(Path(__file__), OUT / 'review.py')
review = {'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'evidence_integrity_passed': True,
    'run_id': RUN, 'run_url': run['html_url'], 'source_revision': REV, 'run_attempt': 1,
    'job_id': job['id'], 'job_url': job['html_url'], 'profile': 'ios-io',
    'artifact_id': art['id'], 'artifact_digest': art['digest'], 'artifact_members': names,
    'all_selected_inputs_reconstructed_from_this_exact_Git_revision': True,
    'source_input_count': len(inputs), 'source_digest': lt.input_digest(inputs),
    'reviewed_current_IO_Coil_source_hashes': owning, 'owning_sources_identical_in_current_worktree': True,
    'dependency_input_count': len(dep_inputs), 'dependency_fingerprint': dep_digest,
    'setup_test_SDK_and_global_fingerprints_match': True, 'only_setup_test_context_difference_is_observed_time': True,
    'runtime': runtime, 'command': receipt['command'], 'execution': receipt['execution'],
    'totals': totals, 'module_results': module_results, 'actual_xml_reports': len(stamps), 'xml_timestamps_and_hashes': stamps,
    'actual_source_methods': methods, 'actual_cases': all_cases, 'mandatory_native_cases': native_cases,
    'all_28_previous_IO_source_method_identities_retained': True,
    'new_native_case_identities': sorted([list(pair) for pair in current_ids - previous_ids]),
    'cache_key': expected_key, 'cache_observation': 'Exact new subset key missed then saved; not a cache hit or test-result reuse',
    'raw_log_sha256': sha(log), 'raw_log_bytes': log.stat().st_size, 'raw_log_archived': False,
    'issues_closed_by_review': 0, 'publication_performed': False, 'release_readiness_certified': False,
    'limits': ['Real guarded Darwin mappings and Foundation copying, not ASan or a proof all native memory operations are safe.',
        'Descriptor tests cover owned local inode/device streams and finite20-cycle tests, not external provider/security-scope grants or general peak-memory profiling.',
        'Decoder fault-injection uses the real Coil engine/fetcher/stream, not every image codec or a packaged consumer.',
        'iPhone simulator runtime is not a physical/minimum-iOS device, native parent, full-library/API-ABI/legal/dependency/full-consumer/security/release clearance.'],
    'scope': 'Exact immutable IO/Coil native suite with47 actual executions/eight fresh XML, all22 mandatory native cases and all28 previous IO source methods. Original IO-001 six criteria need their separate evidence acceptance before issue closure.'}
(OUT / 'lead-independent-review.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
(OUT / 'README.md').write_text('# Immutable native IO/Coil verification\n\n'
    'Run40587910531 at exactfc73dd47 passes47/47 actual native simulator executions '
    'in eight fresh XML (IO40/Coil7), with all22 required cases and all28 previous '
    'IO source method identities retained. Exact own-Git inputs, plans, commands, '
    'SDK/runtime, fresh reports and new canonical subset key are independently reviewed. '
    'Guard pages/owned descriptors/real Coil fault injection are scoped integration '
    'evidence, not sanitizer, external-provider/device, packaged-consumer, legal, '
    'dependency, ABI or release certification. No issue mutation or publication.\n')
(OUT / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + p.relative_to(OUT).as_posix() + '\n'
    for p in sorted(OUT.rglob('*')) if p.is_file()))
shutil.copytree(OUT, DEST)
assert all(sha(p) == sha(DEST / p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file())
print(json.dumps({'passed': True, 'run_id': RUN, 'source_inputs': len(inputs), 'native_executions': 47,
                  'fresh_XML': 8, 'mandatory_native_cases': 22, 'issues_closed': 0, 'archive': str(DEST)}, indent=2))
