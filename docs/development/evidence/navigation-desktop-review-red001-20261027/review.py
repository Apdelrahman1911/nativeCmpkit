"""Independent exact-Git/plan/runtime/fresh-XML navigation-only CI review."""
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
SOURCE = Path('/dev/shm/nativecmpkit-ci-70114ff3-20261027/40549350671')
OUT = BASE / 'archive'
DEST = ROOT / 'docs/development/evidence/github-actions/40549350671'
REV = '70114ff3d579af291c4a3028181efc7d884e23a9'
REPO = 'Apdelrahman1911/nativeCmpkit'
RUN, ART, JOB = 40549350671, 12755405498, 122348945397
SLOT = 'desktop-linux-x64'
SELECTED = ('calf-navigation',)

def sha(raw):
    return hashlib.sha256(raw if isinstance(raw, bytes) else raw.read_bytes()).hexdigest()

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

assert not OUT.exists() and not DEST.exists(), 'Never overwrite evidence'
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
assert collected['profile'] == 'navigation-desktop' and collected['selected_job_count'] == 1
assert collected['artifact_digests_matched'] and len(artifacts) == 1
assert len(jobs) == 3 and next(j for j in jobs if j['name'] == 'tooling')['conclusion'] == 'success'
assert next(j for j in jobs if j['name'] == 'consumer-core-io')['conclusion'] == 'skipped'
job = next(j for j in jobs if j['id'] == JOB)
assert job['name'] == 'library-tests (desktop-linux-x64, desktop, ubuntu-24.04, x64, python3, calf-navigation)'
assert job['run_attempt'] == 1 and job['status'] == 'completed' and job['conclusion'] == 'success'
steps = {s['name']: s['conclusion'] for s in job['steps']}
for name in ('Explicit dependency/compiler/runtime/slot-keyed cache',
             'Source-set-aware expected library tests (never samples)',
             'Fresh actual library suite with strict nonzero receipts',
             'Keep receipts and actual selected-task XML only; never packages'):
    assert steps[name] == 'success'
art = artifacts[0]
assert art['id'] == ART and art['name'] == 'library-evidence-' + SLOT and not art['expired']
assert art['workflow_run']['id'] == RUN and art['workflow_run']['head_sha'] == REV
assert instant(job['started_at']) <= instant(art['created_at']) <= instant(art['updated_at']) <= instant(job['completed_at'])
zip_path = SOURCE / f'{ART}.zip'
assert zip_path.stat().st_size == art['size_in_bytes'] < 64 * 1024**2
assert 'sha256:' + sha(zip_path) == art['digest']
log = SOURCE / f'job-{JOB}-log.log'
log_record = next(x for x in collected['logs'] if x['job_id'] == JOB)
assert log_record['job_log_bytes'] == log.stat().st_size and log_record['job_log_sha256'] == sha(log)
assert log_record['job_conclusion'] == 'success' and not log_record['job_log_to_be_committed']

records = {}
for row in subprocess.check_output(['git', 'ls-tree', '-rz', REV], cwd=ROOT).split(b'\0'):
    if row:
        metadata, name = row.split(b'\t', 1)
        records[name.decode()] = metadata.decode().split()

def blob(name):
    mode, kind, oid = records[name]
    assert mode in {'100644', '100755'} and kind == 'blob'
    return subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)

with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-70114ff-nav-review-', dir='/dev/shm') as directory:
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
    assert len(inputs) == 726
    dep_inputs = keys.selected_inputs(view, 'libraries')
    assert len(dep_inputs) == 65
    dep_digest = keys.fingerprint('libraries', dep_inputs)
    selection = keys.selection_contract(view, 'calf-navigation')
    plan = lt.plan(view, 'desktop', only_modules=SELECTED)
    assert len(plan['expected']) == 1 and plan['expected'][0]['task'] == ':calf-navigation:desktopTest'
    expected_sources = plan['expected'][0]['test_source_files']
    source_methods = {Path(name).stem: re.findall(r'@Test\s+(?:\n\s*)?fun ([A-Za-z][A-Za-z0-9_]*)\(', blob(name).decode())
                      for name in expected_sources}
    assert len(source_methods) == 7 and sum(map(len, source_methods.values())) == 54
    assert len(source_methods['AdaptiveNavTypeCodecTest']) == 10
    assert len(source_methods['NavArrayParsingWorkTest']) == 2
    current_owning = {name: sha(blob(name)) for name in records if name.startswith('calf-navigation/src/')}
    assert all((ROOT / name).read_bytes() == blob(name) for name in current_owning)
    with zipfile.ZipFile(zip_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        assert len(names) == len(set(names)) == 15 and sum(entry.file_size for entry in entries) < 64 * 1024**2
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
        runtime, actual = get(base + 'runtime.json'), get('build/ci-runtime/actual.json')
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
        assert dependencies['selected_modules'] == selection['modules'] == ['calf-navigation']
        assert dependencies['selection_cache_key'] == selection['cache_key']
        assert not dependencies['compiled_or_test_results_reused'] and not dependencies['ordinary_dependency_trust_certified']
        assert not dependencies['release_readiness_certified']
        assert receipt['runtime_receipt_sha256'] == sha(archive.read(base + 'runtime.json'))
        for context in (actual, runtime):
            assert context['source_revision'] == REV and not context['source_tree_dirty']
            assert context['compiler_runtime_fingerprint'] == rc.compiler_runtime_fingerprint(context)
            assert context['host']['system'] == 'Linux' and context['host']['architecture'] == 'x64'
            assert context['java']['major'] == 17 and context['rust']['release'] == '1.98.0'
            assert instant(job['started_at']) <= instant(context['observed_at_utc']) <= instant(job['completed_at'])
        assert actual['host'] == runtime['host'] and actual['rust'] == runtime['rust'] and actual['java'] == runtime['java']
        assert receipt['command'] == lt.gradle_command('desktop', plan, root=view)
        assert receipt['execution']['exit_code'] == 0 and not receipt['execution'].get('stop_reason')
        assert receipt['task_execution_markers'] == {':calf-navigation:desktopTest': 1}
        assert receipt['quarantined_prior_reports'] == [] and receipt['passed'] and receipt['errors'] == []
        assert receipt['uncovered'] == [] and receipt['ios_applications'] == []
        start, end = instant(receipt['started_at_utc']), instant(receipt['finished_at_utc'])
        assert instant(job['started_at']) <= start < end <= instant(job['completed_at'])
        assert len(receipt['modules']) == 1 and receipt['modules'][0]['module'] == 'calf-navigation'
        module = receipt['modules'][0]
        assert module['task'] == ':calf-navigation:desktopTest' and not module['native_scenarios']
        reports = module['reports']
        assert len(reports) == 7 and {r['path'] for r in reports} == {n for n in names if n.endswith('.xml')}
        cases, stamps, allocation_rows = [], [], []
        for report in reports:
            assert report['path'].startswith(plan['expected'][0]['report_directory'] + '/')
            payload = archive.read(report['path'])
            assert sha(payload) == report['sha256']
            parsed = lt.junit_cases(payload)
            assert all(report[key] == value for key, value in lt.case_counts(parsed).items())
            tree = ET.fromstring(payload, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
            assert start <= instant(tree.attrib['timestamp']) <= end
            assert not list(tree.iter('failure')) and not list(tree.iter('error')) and not list(tree.iter('skipped'))
            stamps.append({'path': report['path'], 'timestamp': tree.attrib['timestamp'], 'sha256': sha(payload)})
            cases += parsed
            if report['path'].endswith('NavArrayParsingWorkTest.xml'):
                for line in (tree.findtext('system-out') or '').splitlines():
                    assert line.startswith('nativecmpkit-nav-array-probe:')
                    value = document(line.split(':', 1)[1])
                    assert set(value) == {'elements', 'trial', 'bulk_bytes', 'legacy_bytes', 'bulk_ns', 'legacy_ns'}
                    assert all(type(v) is int and v >= 0 for v in value.values())
                    allocation_rows.append(value)
        assert sorted(cases, key=lambda c: (c['classname'], c['name'])) == sorted(module['testcases'], key=lambda c: (c['classname'], c['name']))
        totals = lt.case_counts(cases)
        assert all(module[key] == value for key, value in totals.items())
        assert len(cases) == len({(c['classname'], c['name']) for c in cases}) == 54
        assert totals == receipt['totals'] == {'tests': 54, 'failures': 0, 'errors': 0, 'skipped': 0,
            'passed': 54, 'executed': 54, 'not_applicable': 0, 'unexpected_skipped': 0}
        for cls, methods in source_methods.items():
            found = [case for case in cases if case['classname'] == 'com.mohamedrejeb.calf.navigation.' + cls]
            assert len(found) == len(methods) and len(methods) == len(set(methods))
            assert {case['name'] for case in found} == {name + '[desktop]' for name in methods}
            assert all(case['status'] == 'passed' for case in found)
        assert len(allocation_rows) == 12 and Counter((row['elements'], row['trial']) for row in allocation_rows) == Counter(
            (elements, trial) for elements in (128, 512, 2048, 4096) for trial in range(3))
        assert all(row['legacy_bytes'] > row['bulk_bytes'] for row in allocation_rows if row['elements'] == 4096)
        prior = document((ROOT / 'docs/development/evidence/github-actions/40528445496/lead-independent-review.json').read_bytes())
        previous_cases = next(r for r in prior['four_runtime_results'] if r['suite'] == 'desktop')
        with zipfile.ZipFile(ROOT / f"docs/development/evidence/github-actions/40528445496/raw/{previous_cases['artifact_id']}.zip") as old:
            old_cases = [case for name in old.namelist() if name.startswith('calf-navigation/') and name.endswith('.xml')
                         for case in lt.junit_cases(old.read(name))]
        previous_ids = {(c['classname'], c['name']) for c in old_cases}
        current_ids = {(c['classname'], c['name']) for c in cases}
        assert len(previous_ids) == 52 and previous_ids < current_ids and len(current_ids - previous_ids) == 2
        expected_key = 'nativecmpkit-deps-v2-Linux-X64-' + SLOT + '-desktop-' + selection['cache_key'] + '-' + actual['compiler_runtime_fingerprint'] + '-' + dep_digest
        console = log.read_text()
        misses = re.findall(r'Cache not found for input keys: ([^\r\n]+)', console)
        saved = re.findall(r'Cache saved with key: ([^\r\n]+)', console)
        assert misses == saved == [expected_key] and not re.search(r'Cache restored (?:from key|successfully)', console)
        assert 'ReserveCacheError' not in console

OUT.mkdir()
(OUT / 'raw').mkdir()
for name in ('run-final.json', 'jobs-final.json', 'artifacts-final.json', 'collection.json', f'{ART}.zip'):
    shutil.copyfile(SOURCE / name, OUT / 'raw' / name)
    assert sha(SOURCE / name) == sha(OUT / 'raw' / name)
shutil.copyfile(Path(__file__), OUT / 'review.py')
review = {'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'evidence_integrity_passed': True,
    'run_id': RUN, 'run_url': run['html_url'], 'source_revision': REV, 'run_attempt': 1,
    'job_id': JOB, 'job_url': job['html_url'], 'profile': 'navigation-desktop',
    'artifact_id': ART, 'artifact_digest': art['digest'], 'artifact_members': names,
    'all_selected_inputs_reconstructed_from_this_exact_Git_revision': True,
    'source_input_count': len(inputs), 'source_digest': lt.input_digest(inputs),
    'reviewed_current_navigation_source_hashes': current_owning, 'owning_sources_identical_in_current_worktree': True,
    'dependency_input_count': len(dep_inputs), 'dependency_fingerprint': dep_digest,
    'runtime': runtime, 'command': receipt['command'], 'execution': receipt['execution'],
    'totals': totals, 'actual_xml_reports': 7, 'xml_timestamps_and_hashes': stamps,
    'actual_source_methods': source_methods, 'actual_cases': cases,
    'all_previous_52_desktop_case_identities_retained': True,
    'new_actual_case_identities': sorted([list(pair) for pair in current_ids - previous_ids]),
    'allocation_probe_rows': allocation_rows, 'allocation_assertions_are_not_timing_budgets': True,
    'cache_key': expected_key, 'cache_observation': 'Exact key missed then saved; not a cache hit or test-result reuse',
    'raw_log_sha256': sha(log), 'raw_log_bytes': log.stat().st_size, 'raw_log_archived': False,
    'issues_closed_by_review': 0, 'publication_performed': False, 'release_readiness_certified': False,
    'limits': ['Finite JDK17 current-thread allocation observations, not peak heap, latency guarantee or Native performance.',
        'Legacy incremental parseValue(previous) still copies; bulk parseValues does not impose an external-input limit.',
        'Navigation desktop only; earlier exact unchanged common source has four-runtime evidence, not an Android device or full-library consumer/ABI pass.',
        'NAV-004 erased get<T>, native-parent/device/minimum-platform/legal/dependency/security and release gates remain independent.'],
    'scope': 'Exact immutable navigation desktop suite and the two original work/allocation probes. Original NAV-005 acceptance reviewed separately before any closure.'}
(OUT / 'lead-independent-review.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
(OUT / 'README.md').write_text('# Immutable navigation desktop verification\n\n'
    'Run 40549350671 at 70114ff3 passes 54/54 actual library methods in seven fresh XML, '
    'including both bounded work/allocation probes and all 52 prior desktop testcase identities. '
    'Exact own-Git inputs, plans, commands, runtime, reports and canonical cache key were reviewed. '
    'Cache missed then saved. Finite JVM allocations are not latency, peak-heap, Native-performance '
    'or external-input-limit promises. No packages or broader release gate are certified.\n')
(OUT / 'SHA256SUMS').write_text(''.join(sha(path) + '  ' + path.relative_to(OUT).as_posix() + '\n'
    for path in sorted(OUT.rglob('*')) if path.is_file()))
shutil.copytree(OUT, DEST)
assert all(sha(path) == sha(DEST / path.relative_to(OUT)) for path in OUT.rglob('*') if path.is_file())
print(json.dumps({'passed': True, 'run_id': RUN, 'source_inputs': len(inputs), 'executions': 54,
                  'fresh_XML': 7, 'allocation_rows': 12, 'issues_closed': 0, 'archive': str(DEST)}, indent=2))
