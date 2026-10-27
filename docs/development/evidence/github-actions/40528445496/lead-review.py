"""Read-only independent Git/ZIP/XML/plan review of four navigation/geo runtimes.

Materialize only reviewed source at this run's own immutable revision. Treat
reports as bounded data, never execute artifacts or export console bodies.
Original issue acceptance is deliberately narrower than library release gates.
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
SOURCE = Path('/dev/shm/nativecmpkit-ci-769bf7de-20261027/40528445496')
OUT = Path(__file__).parent / 'archive'
DEST = ROOT / 'docs/development/evidence/github-actions/40528445496'
REV = '769bf7dea1ca69ac23ef74d7f7140303b130657a'
REPO = 'Apdelrahman1911/nativeCmpkit'
RUN = 40528445496
SELECTED = ('calf-navigation', 'calf-geo')
SLOTS = {
    'desktop-linux-x64': (12744504874, 122274721004, 'desktop', 91, 10, 39, 52),
    'browser-js': (12745517807, 122274721184, 'js', 76, 7, 38, 38),
    'browser-wasm': (12747096405, 122274720927, 'wasm', 76, 7, 38, 38),
    'ios-iphone': (12747972641, 122274721146, 'ios', 78, 8, 38, 40),
}


def sha(payload):
    return hashlib.sha256(payload if isinstance(payload, bytes) else payload.read_bytes()).hexdigest()


def document(payload):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, 'Duplicate JSON key'
            result[key] = value
        return result
    return json.loads(payload, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def instant(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    assert parsed.utcoffset() is not None
    return parsed


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


assert not OUT.exists() and not DEST.exists(), 'Never overwrite previous evidence'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == REV
run = document((SOURCE / 'run-final.json').read_bytes())
jobs = document((SOURCE / 'jobs-final.json').read_bytes())['jobs']
arts = document((SOURCE / 'artifacts-final.json').read_bytes())['artifacts']
collection = document((SOURCE / 'collection.json').read_bytes())
assert run['id'] == RUN and run['head_sha'] == REV and run['run_attempt'] == 1
assert run['repository']['full_name'] == REPO and run['status'] == 'completed' and run['conclusion'] == 'success'
assert run['event'] == 'workflow_dispatch' and run['head_branch'] == 'development/preview-hardening'
assert collection['run_id'] == RUN and collection['source_revision'] == REV and collection['profile'] == 'navigation-geo-matrix'
assert collection['selected_job_count'] == 4 and collection['artifact_digests_matched']
assert {a['id'] for a in arts} == {v[0] for v in SLOTS.values()}
assert len(jobs) == 6 and next(j for j in jobs if j['name'] == 'tooling')['conclusion'] == 'success'
assert next(j for j in jobs if j['name'] == 'consumer-core-io')['conclusion'] == 'skipped'

records = {}
for row in subprocess.check_output(['git', 'ls-tree', '-rz', REV], cwd=ROOT).split(b'\0'):
    if row:
        metadata, name = row.split(b'\t', 1)
        records[name.decode()] = metadata.decode().split()


def blob(name):
    mode, kind, oid = records[name]
    assert kind == 'blob' and mode in {'100644', '100755'}, name
    return subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)


reviews = []
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-769bf-nav-review-', dir='/dev/shm') as directory:
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
        if (name in exact or any(name.startswith(p) for p in prefixes) or
                (name.startswith('sample/') and Path(name).name in keys.PROJECT_FILES)) and not set(PurePosixPath(name).parts[:-1]) & lt.IGNORED_INPUT_DIRS:
            materialize(name)
    inputs = lt.snapshot_inputs(view)
    assert len(inputs) == 724
    dep_inputs = keys.selected_inputs(view, 'libraries')
    assert len(dep_inputs) == 65
    selection = keys.selection_contract(view, ','.join(SELECTED))
    assert selection == {'modules': ['calf-geo', 'calf-navigation'], 'cache_key': 'subset-c550576a207298ef404008f5760d1d283a623f9ac2e3a56e570847fde1d05316'}
    dep_digest = keys.fingerprint('libraries', dep_inputs)
    assert dep_digest == 'f1d935fd411f43ae29ee5ebf4c44f1f32a5efeee8266e08e9a61cfc8b0e24a37'
    # Derive source method identities, not the list claimed by downloaded receipts.
    class_sources = {
        'navigation.NavArgumentAndBundleTest': 'calf-navigation/src/commonTest/kotlin/com/mohamedrejeb/calf/navigation/NavArgumentAndBundleTest.kt',
        'navigation.CheckedNavArraysTest': 'calf-navigation/src/commonTest/kotlin/com/mohamedrejeb/calf/navigation/CheckedNavArraysTest.kt',
        'geo.LatLngTest': 'calf-geo/src/commonTest/kotlin/com/mohamedrejeb/calf/geo/LatLngTest.kt',
    }
    source_methods = {cls: re.findall(r'@Test\s+(?:\n\s*)?fun ([A-Za-z][A-Za-z0-9_]*)\(', blob(name).decode())
                      for cls, name in class_sources.items()}
    assert {cls: len(methods) for cls, methods in source_methods.items()} == {
        'navigation.NavArgumentAndBundleTest': 10, 'navigation.CheckedNavArraysTest': 5, 'geo.LatLngTest': 11}
    assert all(len(m) == len(set(m)) for m in source_methods.values())
    reviewed_owning = {name: sha(blob(name)) for name in records if name.startswith(('calf-navigation/src/', 'calf-geo/src/'))}
    assert all((ROOT / name).read_bytes() == blob(name) for name in reviewed_owning), 'Current owning source differs'
    for slot, (art_id, job_id, suite_name, tests, xml_count, geo_count, nav_count) in SLOTS.items():
        base = f'build/ci-verification/{slot}/'
        job = next(j for j in jobs if j['id'] == job_id)
        assert job['name'].startswith(f'library-tests ({slot}, {suite_name}, ') and job['name'].endswith('calf-navigation,calf-geo)')
        assert job['run_attempt'] == 1 and job['status'] == 'completed' and job['conclusion'] == 'success'
        assert instant(run['created_at']) <= instant(job['started_at']) <= instant(job['completed_at']) <= instant(run['updated_at'])
        steps = {s['name']: s['conclusion'] for s in job['steps']}
        for step in ['Explicit dependency/compiler/runtime/slot-keyed cache',
                     'Source-set-aware expected library tests (never samples)',
                     'Fresh actual library suite with strict nonzero receipts',
                     'Keep receipts and actual selected-task XML only; never packages']:
            assert steps[step] == 'success'
        art = next(a for a in arts if a['id'] == art_id)
        assert art['name'] == 'library-evidence-' + slot and not art['expired']
        assert art['workflow_run']['id'] == RUN and art['workflow_run']['head_sha'] == REV
        assert instant(job['started_at']) <= instant(art['created_at']) <= instant(art['updated_at']) <= instant(job['completed_at'])
        raw = (SOURCE / f'{art_id}.zip').read_bytes()
        assert len(raw) == art['size_in_bytes'] < 64 * 1024**2 and 'sha256:' + sha(raw) == art['digest']
        log = SOURCE / f'job-{job_id}-log.log'
        collected = next(j for j in collection['logs'] if j['job_id'] == job_id)
        assert collected['job_conclusion'] == 'success' and collected['job_log_sha256'] == sha(log)
        assert collected['job_log_bytes'] == log.stat().st_size and collected['job_log_to_be_committed'] is False
        with zipfile.ZipFile(SOURCE / f'{art_id}.zip') as archive:
            infos = archive.infolist()
            names = [i.filename for i in infos]
            assert len(names) == len(set(names)) == xml_count + 8 + (suite_name == 'ios')
            assert sum(i.file_size for i in infos) < 64 * 1024**2
            for entry in infos:
                path = PurePosixPath(entry.filename)
                assert not path.is_absolute() and not {'.', '..'} & set(path.parts) and '\\' not in entry.filename
                assert not entry.is_dir() and not entry.flag_bits & 1 and entry.filename.endswith(('.json', '.xml'))
                assert entry.file_size <= lt.MAX_REPORT_BYTES and stat.S_IFMT(entry.external_attr >> 16) in {0, stat.S_IFREG}

            def get(name): return document(archive.read(name))

            receipt, runtime = get(base + 'receipt.json'), get(base + 'runtime.json')
            actual, dependencies = get('build/ci-runtime/actual.json'), get('build/ci-runtime/library-dependencies.json')
            assert get(base + 'inputs-before.json') == get(base + 'inputs-after.json') == inputs
            assert receipt['source_revision'] == receipt['source_revision_after'] == REV and receipt['source_tree_dirty'] is False
            assert not receipt['changed_inputs'] and receipt['inputs_before_sha256'] == receipt['inputs_after_sha256'] == lt.input_digest(inputs)
            plan = lt.plan(view, suite_name, only_modules=SELECTED)
            assert get(base + 'plan.json') == get('build/ci-plan/plan.json') == plan
            assert receipt['explicit_module_subset'] == list(SELECTED) and not receipt['complete_suite_requested']
            assert receipt['test_bearing_modules_not_requested'] == plan['test_bearing_modules_not_requested']
            assert dependencies['source_revision'] == REV and dependencies['scope'] == 'libraries'
            assert dependencies['inputs'] == dep_inputs and dependencies['dependency_input_count'] == len(dep_inputs)
            assert dependencies['dependency_inputs_sha256'] == dep_digest
            assert dependencies['selection_cache_key'] == selection['cache_key'] and dependencies['selected_modules'] == selection['modules']
            assert dependencies['compiled_or_test_results_reused'] is False and dependencies['ordinary_dependency_trust_certified'] is False
            assert dependencies['release_readiness_certified'] is False
            assert receipt['runtime_receipt_sha256'] == sha(archive.read(base + 'runtime.json'))
            for context in (actual, runtime):
                assert context['source_revision'] == REV and context['source_tree_dirty'] is False
                assert context['compiler_runtime_fingerprint'] == rc.compiler_runtime_fingerprint(context)
                assert context['java']['major'] == 17 and context['rust']['release'] == '1.98.0'
                assert instant(job['started_at']) <= instant(context['observed_at_utc']) <= instant(job['completed_at'])
            assert actual['host'] == runtime['host'] and actual['rust'] == runtime['rust'] and actual['java'] == runtime['java']
            if suite_name == 'ios':
                assert runtime['host']['system'] == 'Darwin' and runtime['host']['architecture'] == 'arm64'
                assert runtime['simulator'] == actual['simulator'] and runtime['simulator']['state'] == 'Booted'
                assert runtime['simulator']['runtime_version'] == '26.5' and runtime['xcode']['version'] == '26.6'
                assert runtime['apple_sdks'] == actual['apple_sdks']
            else:
                assert runtime['host']['system'] == 'Linux' and runtime['host']['architecture'] == 'x64'
                if suite_name in {'js', 'wasm'}:
                    assert runtime['browser'] == actual['browser'] == {'name': 'Google Chrome', 'version': '156.0.8078.47'}
            assert receipt['command'] == lt.gradle_command(suite_name, plan, simulator=runtime.get('simulator', {}).get('udid'), root=view)
            assert receipt['execution']['exit_code'] == 0 and not receipt['execution'].get('stop_reason')
            assert receipt['task_execution_markers'] == {item['task']: 1 for item in plan['expected']}
            assert receipt['quarantined_prior_reports'] == [] and receipt['passed'] is True and receipt['errors'] == []
            assert receipt['uncovered'] == [] and receipt['ios_applications'] == []
            start, end = instant(receipt['started_at_utc']), instant(receipt['finished_at_utc'])
            assert instant(job['started_at']) <= start < end <= instant(job['completed_at'])
            xmls = [name for name in names if name.endswith('.xml')]
            assert len(xmls) == xml_count and set(xmls) == {r['path'] for m in receipt['modules'] for r in m['reports']}
            cases, stamps = [], []
            per_module = {}
            for module in receipt['modules']:
                item = next(i for i in plan['expected'] if i['module'] == module['module'])
                assert module['task'] == item['task'] and not module['native_scenarios']
                module_cases = []
                for report in module['reports']:
                    assert report['path'].startswith(item['report_directory'] + '/')
                    payload = archive.read(report['path'])
                    assert sha(payload) == report['sha256']
                    parsed = lt.junit_cases(payload)
                    assert all(report[k] == v for k, v in lt.case_counts(parsed).items())
                    module_cases += parsed
                    tree = ET.fromstring(payload, parser=ET.XMLParser(target=lt.NoDtdBuilder()))
                    # XML has whole-second UTC precision; allow no earlier testcase timestamp.
                    timestamp = instant(tree.attrib['timestamp'])
                    assert start <= timestamp <= end
                    assert not list(tree.iter('failure')) and not list(tree.iter('error')) and not list(tree.iter('skipped'))
                    stamps.append({'path': report['path'], 'timestamp': tree.attrib['timestamp'], 'sha256': sha(payload)})
                sort = lambda c: (c['classname'], c['name'])
                assert sorted(module_cases, key=sort) == sorted(module['testcases'], key=sort)
                totals = lt.case_counts(module_cases)
                assert all(module[k] == v for k, v in totals.items())
                assert totals['tests'] == totals['executed'] == totals['passed'] == (geo_count if module['module'] == 'calf-geo' else nav_count)
                per_module[module['module']] = totals
                cases += module_cases
            assert len(cases) == len({(c['classname'], c['name']) for c in cases}) == tests
            assert lt.case_counts(cases) == receipt['totals'] == {'tests': tests, 'failures': 0, 'errors': 0, 'skipped': 0,
                                                              'passed': tests, 'executed': tests, 'not_applicable': 0, 'unexpected_skipped': 0}
            prefix = {'desktop': '', 'js': 'jsBrowserTest.', 'wasm': 'wasmJsBrowserTest.', 'ios': 'iosSimulatorArm64Test.'}[suite_name]
            suffix = {'desktop': r'\[desktop\]', 'js': r'\[js, browser, ChromeHeadless156\.0\.0\.0, Linux0\.0\.0\]',
                      'wasm': r'\[wasmJs, browser, ChromeHeadless156\.0\.0\.0, Linux0\.0\.0\]', 'ios': r'\[iosSimulatorArm64\]'}[suite_name]
            acceptance_cases = {}
            for cls, methods in source_methods.items():
                actual_cases = [c for c in cases if c['classname'] == prefix + 'com.mohamedrejeb.calf.' + cls]
                assert len(actual_cases) == len(methods)
                assert {re.sub(suffix + '$', '', c['name']) for c in actual_cases} == set(methods)
                assert all(c['status'] == 'passed' and any(re.fullmatch(re.escape(m) + suffix, c['name']) for m in methods) for c in actual_cases)
                acceptance_cases[cls] = actual_cases
            if suite_name == 'desktop':
                assert any(c['classname'] == 'com.mohamedrejeb.calf.geo.LatLngJvmCompatibilityTest' and
                           c['name'] == 'legacyEarthRadiusRemainsAJavaVisiblePublicStaticFinalDouble[desktop]' and c['status'] == 'passed' for c in cases)
            if suite_name == 'ios':
                assert len([c for c in cases if c['classname'] == prefix + 'com.mohamedrejeb.calf.navigation.NativeArrayErasureTest']) == 2
            runner_os, runner_arch = ('macOS', 'ARM64') if suite_name == 'ios' else ('Linux', 'X64')
            key = f"nativecmpkit-deps-v2-{runner_os}-{runner_arch}-{slot}-{suite_name}-{selection['cache_key']}-{actual['compiler_runtime_fingerprint']}-{dep_digest}"
            # Source-bound log observation only; do not export console bodies.
            console = log.read_text()
            assert f'Cache not found for input keys: {key}' in console
            assert f'Cache saved with key: {key}' in console and 'Cache restored from key:' not in console
            assert 'ReserveCacheError' not in console
            reviews.append({'slot': slot, 'suite': suite_name, 'job_id': job_id, 'job_url': job['html_url'],
                            'artifact_id': art_id, 'artifact_digest': art['digest'], 'artifact_bytes': len(raw),
                            'artifact_members': names, 'source_input_count': len(inputs), 'source_digest': lt.input_digest(inputs),
                            'command': receipt['command'], 'execution': receipt['execution'], 'runtime': runtime,
                            'cache_key': key, 'cache_runtime_fingerprint_from_actual_not_test_context': actual['compiler_runtime_fingerprint'],
                            'cache_observation': 'Exact key missed then saved; zero restored successful test/compilation results',
                            'raw_log_archived': False, 'raw_log_sha256': sha(log), 'raw_log_bytes': log.stat().st_size,
                            'totals': receipt['totals'], 'modules': per_module, 'xml_report_count': xml_count,
                            'xml_timestamps_and_hashes': stamps, 'original_acceptance_class_methods': acceptance_cases})

assert sum(r['totals']['executed'] for r in reviews) == 321 and sum(r['xml_report_count'] for r in reviews) == 32
OUT.mkdir()
raw_dir = OUT / 'raw'
raw_dir.mkdir()
for name in ('run-final.json', 'jobs-final.json', 'artifacts-final.json', 'collection.json', *(str(v[0]) + '.zip' for v in SLOTS.values())):
    shutil.copyfile(SOURCE / name, raw_dir / name)
    assert sha(SOURCE / name) == sha(raw_dir / name)
shutil.copyfile(Path(__file__), OUT / 'lead-review.py')
review = {'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'evidence_integrity_passed': True,
          'run_id': RUN, 'run_url': run['html_url'], 'source_revision': REV, 'run_attempt': 1,
          'all_selected_inputs_reconstructed_from_this_exact_Git_revision': True, 'source_input_count': len(inputs),
          'reviewed_current_NAV_GEO_source_hashes': reviewed_owning, 'owning_sources_identical_in_current_worktree': True,
          'dependency_input_count': len(dep_inputs), 'dependency_fingerprint': dep_digest, 'selection': selection,
          'four_runtime_results': reviews, 'actual_executions': 321, 'actual_xml_reports': 32,
          'failures': 0, 'errors': 0, 'skipped': 0,
          'original_scope_NAV003': 'All four original criteria passed on JVM/JS/Wasm/Native;10 owning argument/bundle methods per runtime plus five checked-array methods. Includes all11 declared built-in types, Reference alias, required vs null defaults, immediate rejection, predicate/value verification and defensive array boundaries.',
          'original_scope_PERM023': 'Eleven owning numerical-contract methods pass on all four runtimes: identical/cardinal/dateline/poles/antipodes/tiny/nonfinite/out-of-range values;500 seeded symmetry/bounds/bearing-rounding iterations per method invocation. Constructor/copy remain unchecked; public JVM EarthRadius reflection fixture also passes.',
          'issues_closed_by_review': 0, 'packages_or_releases_or_deployments_published': False, 'release_readiness_certified': False,
          'limits': ['These321 target executions overlap common methods; not321 unique source tests.',
                     'Apple native tests are iPhone26.5 simulator Arm64, not physical or minimum-iOS execution.',
                     'Geo intentionally unsupported native tracker remains separate; numeric tests do not establish native GPS functionality.',
                     'Only two modules selected. No full21-root packaged/native/minimum-platform consumer, whole-library ABI, legal, dependency-trust, sanitizer or release certification.',
                     'Strict command exit/task markers are held-source controller receipts; raw child Gradle logs/native binaries are not exported. Fresh XML independently establishes nonzero named runtime cases.',
                     'Cache steps succeed with exact canonical hashed module identities; all four keys missed then saved. No cache-hit or successful test-result reuse claim.'],
          'scope': 'Independent Git/ZIP/XML/plan/cache/runtime integrity and original NAV-003/PERM-023 acceptance; pending additive pushed documentation and exact issue closure/readback.'}
save(OUT / 'lead-independent-review.json', review)
(OUT / 'README.md').write_text('# Four-runtime navigation/geo evidence\n\nRun40528445496 at immutable `'+REV+'` passes321 target executions in32 fresh XML, zero failures/errors/skips. `lead-independent-review.json` binds exact Git source, artifact digests, runtime, selected commands and original acceptance cases. Raw ZIPs contain only bounded public JSON/XML; raw job/child logs and binaries are not archived. No package/release/deployment or whole-library certification.\n')
(OUT / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.rglob('*')) if p.is_file()))
shutil.copytree(OUT, DEST)
assert all(sha(p) == sha(DEST / p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file())
print(json.dumps({'passed': True, 'run_id': RUN, 'source_inputs': len(inputs), 'actual_executions': 321,
                  'fresh_xml': 32, 'issues_closed': 0, 'archive': str(DEST)}, indent=2))
