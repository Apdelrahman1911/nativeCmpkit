#!/usr/bin/env python3
"""Seal the external packet only, without imports/ROOT/Git/network/execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat

PACKET = Path(__file__).resolve().parent
DESTINATION = PACKET / 'PACKET-SEAL658.json'
if DESTINATION.exists() or DESTINATION.is_symlink():
    raise SystemExit('Full packet seal already exists; never silently reseal')
files, directories = {}, []
for path in sorted(PACKET.rglob('*')):
    metadata = path.stat(follow_symlinks=False)
    relative = path.relative_to(PACKET).as_posix()
    if path.is_symlink():
        raise ValueError('No symlink in frozen packet')
    if stat.S_ISDIR(metadata.st_mode):
        directories.append(relative)
        continue
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_size > 64 * 1024**2:
        raise ValueError('Only bounded regular unshared packet files can be sealed')
    payload = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    if (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError('Packet changed during sealed read')
    files[relative] = {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
                       'external_mode': f'{metadata.st_mode & 0o777:04o}'}
for relative, expected in files.items():
    payload = (PACKET / relative).read_bytes()
    if len(payload) != expected['bytes'] or hashlib.sha256(payload).hexdigest() != expected['sha256']:
        raise ValueError('Packet inventory changed before final seal')
value = {'schema': 'nativecmpkit-javafx-external-final-current16-packet-seal658-v1',
         'utc': datetime.now(timezone.utc).isoformat(), 'packet': str(PACKET),
         'file_count': len(files), 'file_bytes': sum(row['bytes'] for row in files.values()),
         'files': files, 'directories': directories, 'excludes_only_self': 'PACKET-SEAL658.json',
         'inventory_held': True, 'canonical_source_count': 16, 'canonical_source_bytes': 232222,
         'source_recipe': 'CURRENT16-ORDINARY-MAVEN-WINDOWS-ADOPTION-RECIPE658.json',
         'small_source_results_seal': 'FINAL16-SOURCE-RESULTS-SEAL658.json',
         'ROOT_Git_GitHub_network_test_build_stage_native_dispatch_or_publication': 0,
         'scope': 'Full external source/evidence custody, not adoption/compiler/native/security/lead acceptance or issue closure',
         'independent705_acceptance_claimed': False}
with DESTINATION.open('x', encoding='utf-8') as output:
    json.dump(value, output, indent=2, sort_keys=True)
    output.write('\n')
DESTINATION.chmod(0o600)
raw = DESTINATION.read_bytes()
print(json.dumps({'passed': True, 'packet_file_count_excluding_self': len(files),
                  'packet_bytes_excluding_self': value['file_bytes'],
                  'seal_path': str(DESTINATION), 'seal_bytes': len(raw),
                  'seal_sha256': hashlib.sha256(raw).hexdigest()}, sort_keys=True))
