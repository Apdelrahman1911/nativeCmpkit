"""Review failed immutable local consumer staging and preserve owned old artifacts."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess

ROOT = Path('/root/projects/nativeCmpKit')
TMP = Path(__file__).resolve().parent
RUN = ROOT / 'build/ci-consumer/core-io-local-d2b47840'
OUT = TMP / 'review-archive'
REV = 'd2b47840e352e0e04c3ae5c19d8b81b04fd967ab'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def put(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


assert not OUT.exists()
OUT.mkdir()
receipt = json.loads((RUN / 'receipt.json').read_bytes())
before = json.loads((RUN / 'inputs-before.json').read_bytes())
after = json.loads((RUN / 'inputs-after.json').read_bytes())
fixture = json.loads((RUN / 'fixture-copy.json').read_bytes())
runtime = json.loads((RUN / 'runtime-before.json').read_bytes())
assert receipt['source_revision'] == receipt['source_revision_after'] == runtime['source_revision'] == REV
assert receipt['source_tree_dirty'] is False and before == after and len(before) == receipt['source_input_count'] == 737
assert receipt['source_inputs_held'] is True and receipt['changed_inputs'] == []
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
raw = subprocess.check_output(['git', 'ls-tree', '-rz', REV], cwd=ROOT)
records = {}
for row in raw.split(b'\0'):
    if row:
        meta, name = row.split(b'\t', 1)
        records[name.decode()] = meta.decode().split()
oids = []
for name in sorted(before):
    mode, kind, oid = records[name]
    assert kind == 'blob' and mode in {'100644', '100755'}
    oids.append(oid)
output = subprocess.check_output(['git', 'cat-file', '--batch'], input=('\n'.join(oids) + '\n').encode(), cwd=ROOT)
position = 0
for name, oid in zip(sorted(before), oids):
    end = output.index(b'\n', position)
    header = output[position:end].split()
    assert header[0].decode() == oid and header[1] == b'blob'
    size = int(header[2])
    payload = output[end + 1:end + 1 + size]
    assert hashlib.sha256(payload).hexdigest() == before[name] == sha(ROOT / name)
    assert output[end + 1 + size:end + 2 + size] == b'\n'
    position = end + 2 + size
assert position == len(output)
inputs_hash = hashlib.sha256(''.join(f'{value}  {name}\n' for name, value in sorted(before.items())).encode()).hexdigest()
assert inputs_hash == receipt['inputs_before_sha256'] == receipt['inputs_after_sha256']
assert len(fixture) == 6
for name, digest in fixture.items():
    assert before['tests/consumer/io-desktop/' + name] == digest == sha(RUN / 'independent-consumer' / name)
assert runtime['host']['system'] == 'Linux' and runtime['host']['architecture'] == 'x64'
assert runtime['java']['major'] == 17 and runtime['rust']['release'] == '1.98.0'
assert runtime['android_platform']['package'] == 'platforms;android-37.0'
assert receipt['passed'] is False and receipt['actual_consumer_methods_verified'] == 0
assert receipt['owned_lock_removed'] is True and not (ROOT / 'build/ci-consumer/.core-io-consumer.lock').exists()
assert len(receipt['executions']) == 1
execution = receipt['executions'][0]
assert execution['execution']['exit_code'] == 1 and not execution['execution'].get('stop_reason')
assert execution['execution']['elapsed_seconds'] == 478.5 and receipt['error']['phase'] == 'real-producer-staging'
assert sha(RUN / 'producer.log') == execution['log_sha256']
log = (RUN / 'producer.log').read_text()
markers = re.findall(r'(?m)^NATIVECMPKIT_PARTIAL_STAGE task=([^ ]+) group=io.github.apdelrahman1911.nativecmpkit version=0.1.0-preview.1$', log)
assert len(markers) == 2 and set(markers) == {
    ':calf-core:publishDesktopPublicationToNativecmpkitVerificationRepository',
    ':calf-core:publishKotlinMultiplatformPublicationToNativecmpkitVerificationRepository'}
assert "Project with path ':calf-core' could not be found" not in log
assert "Execution failed for task ':calf-io:compileKotlinDesktop'" in log
assert 'Remote host terminated the handshake' in log
missing = ['kotlinx-io-core-jvm-0.9.1.jar', 'kotlinx-coroutines-core-jvm-1.11.0.jar', 'kotlinx-io-bytestring-jvm-0.9.1.jar']
assert all(name in log for name in missing)
assert not (RUN / 'consumer.log').exists() and not list(RUN.rglob('TEST-*.xml'))
prior = json.loads((TMP / 'owned-old-staging-relocation.json').read_bytes())
prior_before = json.loads((TMP / 'previous-staging-before.json').read_bytes())
prior_after = json.loads((TMP / 'previous-staging-after.json').read_bytes())
assert prior_before == prior_after and len(prior_before) == prior['files'] == 1425
assert sha(TMP / 'previous-staging-before.json') == prior['before_file_sha256']
assert sha(TMP / 'previous-staging-after.json') == prior['after_file_sha256']
for name, row in prior_before.items():
    p = ROOT / prior['new_owned_path'] / name
    s = p.stat()
    assert not p.is_symlink() and s.st_nlink == 1 and s.st_size == row['bytes'] and (s.st_dev, s.st_ino) == (row['device'], row['inode'])
    assert sha(p) == row['sha256']
# Snapshot only byte hashes, never upload local Maven package payloads.
staged = {}
repository = ROOT / 'build/verification-repo'
for base, directories, files in os.walk(repository, followlinks=False):
    for name in directories + files:
        p = Path(base) / name
        s = p.lstat()
        assert not stat.S_ISLNK(s.st_mode)
        if stat.S_ISDIR(s.st_mode):
            continue
        assert stat.S_ISREG(s.st_mode) and s.st_nlink == 1
        relative = p.relative_to(repository).as_posix()
        assert relative.startswith('io/github/apdelrahman1911/nativecmpkit/nativecmpkit-core')
        staged[relative] = {'bytes': s.st_size, 'sha256': sha(p)}
assert staged
for name in ['receipt.json', 'inputs-before.json', 'inputs-after.json', 'fixture-copy.json', 'runtime-before.json']:
    shutil.copyfile(RUN / name, OUT / name)
for name in ['owned-old-staging-relocation.json', 'previous-staging-before.json', 'previous-staging-after.json']:
    shutil.copyfile(TMP / name, OUT / name)
put('partial-staging-observation.json', dict(sorted(staged.items())))
# Read exact former own PIDs only. This is a point-in-time observation, not a
# pidfd descendant/daemon cleanup attestation from the bounded controller.
process_observation = {str(pid): Path(f'/proc/{pid}').exists() for pid in (21750, 21862)}
assert not any(process_observation.values())
review = {'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'evidence_integrity_passed': True,
    'source_revision': REV, 'source_inputs_reconstructed_from_Git_and_held': 737, 'source_inputs_sha256': inputs_hash,
    'original_controller_receipt_sha256': sha(RUN / 'receipt.json'), 'execution': execution,
    'actual_root_binding_configuration_passed': True, 'actual_Core_publication_task_markers': sorted(markers),
    'actual_IO_publication_tasks_passed': False, 'independently_copied_fixture_files': 6,
    'Kotlin_consumer_methods_executed': 0, 'consumer_XML_reports': 0,
    'confirmed_failure': 'Producer reaches the real owning root and both Core metadata/desktop file publications. IO compilation then fails downloading three exact Maven Central JARs after TLS handshakes terminate. This is an actual environment/dependency acquisition failure; IO/static/consumer verification never runs. No insecure TLS flag, version downgrade, fabricated test or checksum waiver was used.',
    'missing_public_artifacts': missing, 'current_partial_staged_files': len(staged),
    'owned_prior_staged_files_preserved_with_inodes_and_bytes': 1425,
    'former_own_processes_present_at_this_observation': process_observation, 'ordinary_detached_daemon_cleanup_attested': False,
    'producer_log_bytes': (RUN / 'producer.log').stat().st_size, 'producer_log_sha256': sha(RUN / 'producer.log'), 'full_producer_log_archived': False,
    'root_disk_free_before': receipt['free_bytes_before'], 'root_disk_free_after': receipt['free_bytes_after'],
    'next_step': 'Execute exactly consumer-core-io on the same immutable repaired revision using the authorized hosted host; preserve this failure. No unchanged UIKit rerun. All four fresh task markers, exact resolved/loaded JAR bytes and seven named consumer methods still required.',
    'issues_closed': 0, 'packages_published': False, 'release_created': False, 'release_readiness_certified': False,
    'scope': 'Immutable Linux configuration/two Core local-publication evidence and zero consumer tests. Ordinary trust, detached descendant ownership, full21-root graph, other platforms, API/legal/native and release gates remain unverified.'}
shutil.copyfile(Path(__file__), OUT / 'lead-review.py')
put('lead-independent-review.json', review)
with (OUT / 'SHA256SUMS').open('x') as stream:
    stream.write(''.join(f'{sha(p)}  {p.relative_to(OUT)}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
print(json.dumps({'input_integrity': True, 'source_inputs': 737, 'Core_publications': 2, 'consumer_methods': 0, 'preserved_old_staging_files': 1425, 'partial_staged_file_count': len(staged)}, indent=2))
