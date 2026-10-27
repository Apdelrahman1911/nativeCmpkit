"""Review actual D2 Core/IO staging and independent Kotlin-DSL failure; execute no artifacts."""
from pathlib import Path, PurePosixPath
import datetime as dt
import hashlib
import importlib.util
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path('/root/projects/nativeCmpKit')
TMP = Path(__file__).resolve().parent
OUT = TMP / 'review-archive'
REV = 'd2b47840e352e0e04c3ae5c19d8b81b04fd967ab'
REPO = 'Apdelrahman1911/nativeCmpkit'
RUN, JOB, ART = 40486697786, 122130445827, 12724559477


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def document(payload):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result
            result[key] = value
        return result
    return json.loads(payload, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


assert not OUT.exists()
run = document((TMP / 'run-final.json').read_bytes())
jobs = document((TMP / 'jobs-final.json').read_bytes())['jobs']
arts = document((TMP / 'artifacts-final.json').read_bytes())['artifacts']
assert run['id'] == RUN and run['head_sha'] == REV and run['run_attempt'] == 1
assert run['repository']['full_name'] == REPO and run['head_branch'] == 'development/preview-hardening'
assert run['event'] == 'workflow_dispatch' and run['status'] == 'completed' and run['conclusion'] == 'failure'
job = next(j for j in jobs if j['id'] == JOB)
assert job['name'] == 'consumer-core-io' and job['status'] == 'completed' and job['conclusion'] == 'failure'
assert next(j for j in jobs if j['name'] == 'tooling')['conclusion'] == 'success'
assert next(j for j in jobs if j['name'] == 'library-tests')['conclusion'] == 'skipped'
assert len(arts) == 1
art = arts[0]
raw = (TMP / f'{ART}.zip').read_bytes()
digest = 'sha256:' + sha(raw)
assert art['id'] == ART and not art['expired'] and art['workflow_run']['id'] == RUN and art['workflow_run']['head_sha'] == REV
assert len(raw) == art['size_in_bytes'] == 81312 and art['digest'] == digest
records = {}
for row in subprocess.check_output(['git', 'ls-tree', '-rz', REV], cwd=ROOT).split(b'\0'):
    if row:
        meta, name = row.split(b'\t', 1)
        records[name.decode()] = meta.decode().split()


def blob(name):
    mode, kind, oid = records[name]
    assert kind == 'blob' and mode in {'100644', '100755'}
    return subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)


with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-d2-consumer-review-', dir='/dev/shm') as directory:
    view = Path(directory)
    def materialize(name):
        path = view / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob(name))
    # Reconstruct the enumerator's inputs independently, not just ZIP-listed paths.
    materialize('settings.gradle.kts')
    for name in records:
        if name.startswith(('calf-', 'sample/')) and name.endswith('/build.gradle.kts'):
            materialize(name)
    for name in records:
        if name.startswith(('scripts/ci/', 'scripts/native/')):
            materialize(name)
    sys.path.insert(0, str(view / 'scripts/ci'))
    import core_io_consumer as c
    import library_tests as lt
    projects = lt.projects(view)
    prefixes = ['gradle/', 'convention-plugins/', 'scripts/ci/', 'scripts/native/', 'kotlin-js-store/', 'licenses/', 'tests/consumer/io-desktop/']
    prefixes += [f'{module}/{part}/' for module in projects for part in ('src', 'native', '.cargo', 'gradle')]
    exact = set(lt.ROOT_INPUTS) | {f'{m}/{n}' for m in projects for n in ('build.gradle.kts', 'gradle.properties', 'gradle.lockfile')}
    exact |= {n for n in records if n.startswith('sample/') and n.count('/') == 2 and n.endswith('/build.gradle.kts')}
    exact |= {'tests/consumer/verify_artifacts.py', 'docs/migration/identity.json', 'tests/consumer/build.gradle.kts',
              'tests/consumer/settings.gradle.kts', 'tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt',
              'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md'}
    for name in records:
        if (name in exact or any(name.startswith(p) for p in prefixes)) and not set(PurePosixPath(name).parts[:-1]) & lt.IGNORED_INPUT_DIRS:
            materialize(name)
    inputs = c.inputs(view)
    assert len(inputs) == 737
    with zipfile.ZipFile(TMP / f'{ART}.zip') as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        assert len(names) == len(set(names)) == 8 and sum(i.file_size for i in infos) < 16 * 1024**2
        for info in infos:
            path = PurePosixPath(info.filename)
            assert not path.is_absolute() and not set(path.parts) & {'.', '..'} and '\\' not in info.filename
            assert not info.is_dir() and not info.flag_bits & 1 and info.filename.endswith('.json')
            assert info.file_size <= lt.MAX_REPORT_BYTES and stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG)
        def doc(name):
            return document(archive.read(name))
        base = 'ci-consumer/core-io-desktop/'
        receipt, runtime = doc(base + 'receipt.json'), doc(base + 'runtime-before.json')
        assert doc(base + 'inputs-before.json') == doc(base + 'inputs-after.json') == inputs
        copied = doc(base + 'fixture-copy.json')
        assert set(copied) == set(c.FIXTURE_FILES)
        assert copied == {name: sha(blob(c.FIXTURE + '/' + name)) for name in c.FIXTURE_FILES}
        assert receipt['source_revision'] == receipt['source_revision_after'] == REV
        assert receipt['source_tree_dirty'] is False and receipt['source_inputs_held'] is True and not receipt['changed_inputs'] and receipt['passed'] is False
        assert receipt['inputs_before_sha256'] == receipt['inputs_after_sha256'] == lt.input_digest(inputs)
        assert runtime['source_revision'] == REV and runtime['source_tree_dirty'] is False
        assert runtime['host']['system'] == 'Linux' and runtime['host']['architecture'] == 'x64'
        assert runtime['java']['major'] == 17 and runtime['rust']['release'] == '1.98.0'
        assert doc('ci-runtime/consumer-core-io.json')['compiler_runtime_fingerprint'] == runtime['compiler_runtime_fingerprint']
        producer, child = receipt['executions']
        assert producer['phase'] == 'real-producer-staging' and child['phase'] == 'independent-packaged-consumer'
        assert producer['execution'] == {'elapsed_seconds': 244.08, 'exit_code': 0}
        assert child['execution'] == {'elapsed_seconds': 19.01, 'exit_code': 1}
        runner_root = Path(producer['command'][0]).parent
        consumer = runner_root / 'build/ci-consumer/core-io-desktop/independent-consumer'
        assert (producer['command'], child['command']) == c.commands(runner_root, consumer)
        tasks = sorted(f':calf-{module}:publish{publication}PublicationToNativecmpkitVerificationRepository'
                       for module in ('core', 'io') for publication in ('KotlinMultiplatform', 'Desktop'))
        assert receipt['actual_publication_task_markers'] == tasks
        staged = doc(base + 'staging-before.json')
        assert len(staged) == 150 and sum(x['bytes'] for x in staged.values()) == 323460
        coordinates = set()
        for path, value in staged.items():
            parts = PurePosixPath(path).parts
            assert tuple(parts[:len(c.GROUP.split('.'))]) == tuple(c.GROUP.split('.')) and parts[len(c.GROUP.split('.'))] in c.COORDINATES
            assert value.keys() == {'bytes', 'sha256'} and type(value['bytes']) is int and re.fullmatch('[0-9a-f]{64}', value['sha256'])
            coordinates.add(parts[len(c.GROUP.split('.'))])
        assert coordinates == c.COORDINATES
        static_report = doc(base + 'static-packages.json')
        c.static_contract(static_report)
        assert static_report['check_count'] == len(static_report['checks']) == 308 and all(row['passed'] is True for row in static_report['checks'])
        assert len({row['name'] for row in static_report['checks']}) == 308 and len(static_report['artifact_files']) == 20
        assert all(staged[row['path']] == {k: row[k] for k in ('bytes', 'sha256')} for row in static_report['artifact_files'])
        assert not static_report['native_provenance_observed']
        assert receipt['actual_consumer_methods_verified'] == 0 and 'consumer_tests' not in receipt and 'resolution_review' not in receipt
        assert receipt['error'] == {'contract': 'Verification phase failed; inspect bounded public fixture diagnostics', 'phase': 'fresh-independent-resolution-and-tests', 'type': 'FileNotFoundError'}
        assert receipt['packages_published'] is False and receipt['release_created'] is False and receipt['release_readiness_certified'] is False and receipt['ordinary_dependency_trust_certified'] is False
        assert receipt['owned_lock_removed'] is True
log = (TMP / 'job-log.log').read_bytes()
assert len(log) == 76680
lines = [re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ', '', line) for line in log.decode('utf-8-sig').splitlines()]
expected_errors = ["Unresolved reference 'io'", "Unresolved reference 'security'", "Unresolved reference 'it'"]
assert all(any(value in line for line in lines) for value in expected_errors)
assert any('build.gradle.kts:20:32' in line for line in lines)
assert any('build.gradle.kts:40:23' in line for line in lines)
assert any('build.gradle.kts:49:61' in line for line in lines)
assert not any(line.startswith('NATIVECMPKIT_PARTIAL_CONSUMER_TEST ') for line in lines)
fixture = blob('tests/consumer/io-desktop/build.gradle.kts').decode()
assert 'val candidateRepository = java.io.File(' in fixture and 'java.security.MessageDigest.getInstance' in fixture
locations = [{'path': 'tests/consumer/io-desktop/build.gradle.kts', 'lines': str(i + 1), 'code': line.strip()}
             for i, line in enumerate(fixture.splitlines()) if 'java.io.File' in line or 'java.security.MessageDigest' in line]
review = {
    'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'run_id': RUN, 'run_attempt': 1,
    'source_revision': REV, 'url': run['html_url'], 'job_id': JOB, 'job_url': job['html_url'], 'run_conclusion': 'failure',
    'evidence_integrity_passed': True, 'artifact_id': ART, 'artifact_digest': digest, 'artifact_bytes': len(raw), 'artifact_members': names,
    'source_input_count': len(inputs), 'source_inputs_sha256': lt.input_digest(inputs), 'all_inputs_reconstructed_from_Git_and_before_after_match': True,
    'independent_fixture_files_matched': len(copied), 'producer_execution': producer['execution'], 'producer_command': producer['command'],
    'actual_publication_task_markers': tasks, 'staged_file_count': len(staged), 'staged_total_bytes': sum(x['bytes'] for x in staged.values()),
    'actual_static_check_count': 308, 'actual_static_checks_passed': 308, 'static_artifact_hash_bindings': 20,
    'consumer_execution': child['execution'], 'consumer_command': child['command'], 'actual_consumer_methods_verified': 0,
    'consumer_resolution_reports': 0, 'actual_xml_reports': 0, 'runtime': runtime,
    'confirmed_failure': "The independent consumer Kotlin DSL fails before resolution/tests: the JVM plugin's java extension receiver shadows java.io.File and java.security.MessageDigest expressions. All four producer tasks execute and partial308 static checks pass; zero consumer methods/XML. Import the Java types and execute the corrected DSL without weakening resolution/runtime checks.",
    'current_source_locations': locations, 'bounded_actual_job_diagnostics': {'log_bytes': len(log), 'log_sha256': sha(log), 'full_log_archived': False},
    'scope': 'Actual four-coordinate Core/IO staging plus PARTIAL static inspection, not a passing independent consumer, complete21-root/native/ABI/legal/dependency or release gate.',
    'issues_closed': 0, 'packages_published': False, 'release_created': False, 'release_readiness_certified': False,
    'review_script_sha256': sha(Path(__file__).read_bytes())}
(OUT / 'raw').mkdir(parents=True)
for name in ('run-final.json', 'jobs-final.json', 'artifacts-final.json'):
    shutil.copyfile(TMP / name, OUT / name)
(OUT / f'raw/{ART}.zip').write_bytes(raw)
shutil.copyfile(Path(__file__), OUT / 'lead-review.py')
with (OUT / 'lead-independent-review.json').open('x') as stream:
    json.dump(review, stream, indent=2, sort_keys=True); stream.write('\n')
with (OUT / 'SHA256SUMS').open('x') as stream:
    stream.write(''.join(f'{sha(p.read_bytes())}  {p.relative_to(OUT)}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
print(json.dumps({key: review[key] for key in ('run_id', 'evidence_integrity_passed', 'source_input_count', 'actual_static_checks_passed', 'actual_consumer_methods_verified')}, indent=2))
