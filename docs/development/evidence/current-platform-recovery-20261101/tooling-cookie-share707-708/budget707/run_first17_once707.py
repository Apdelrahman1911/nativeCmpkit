"""One source-bound NEW17 invocation, not a library/native-platform result."""
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import time
import unittest
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
SOURCE = OUT / 'final'
PATHS = ('.github/workflows/gradle.yml', 'scripts/ci/offline_tooling_reuse.py',
         'scripts/ci/offline_tooling_provenance.py', 'scripts/ci/offline_tooling_failure_inventory.py',
         'scripts/ci/test_offline_tooling_scope_observation707.py')


def capture():
    result = {}
    for relative in PATHS:
        path = SOURCE / relative
        before = path.stat()
        if path.is_symlink() or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 128 * 1024**2:
            raise ValueError('ordinary bounded NEW source required')
        raw = path.read_bytes()
        after = path.stat()
        if before != after:
            raise ValueError('NEW source changed while reading')
        result[relative] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                            'mode': stat.S_IMODE(before.st_mode), 'identity': [before.st_dev, before.st_ino, before.st_mtime_ns, before.st_ctime_ns]}
    return result


def write(leaf, value):
    with (OUT / leaf).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')


def main():
    before = capture()
    write('FIRST17-EXECUTION-STARTED707.json', {'before': before, 'test_population': '17 genuinely NEW methods',
        'started_at_utc': datetime.now(timezone.utc).isoformat(), 'accepted_population_replays': 0,
        'library_device_browser_consumer_executions': 0, 'declared_real_Linux_owned_child_tests': 1})
    started = time.monotonic()
    sys.path.insert(0, str(SOURCE / 'scripts/ci'))
    module = importlib.import_module('test_offline_tooling_scope_observation707')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(module.ScopeObservation707Tests)
    if suite.countTestCases() != 17:
        raise ValueError('exact NEW17 test population required')
    with (OUT / 'FIRST17-ORIGINAL-UNITTEST.log').open('x') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    elapsed = time.monotonic() - started
    after = capture()
    write('FIRST17-EXECUTION-RESULT707.json', {'before': before, 'after': after, 'inputs_held': before == after,
        'tests_run': result.testsRun, 'failures': [item.id() for item, _ in result.failures],
        'errors': [item.id() for item, _ in result.errors], 'skips': len(result.skipped),
        'wrapper_seconds': elapsed, 'unit_success': result.wasSuccessful(),
        'library_device_browser_consumer_executions': 0, 'declared_real_Linux_owned_child_tests': 1,
        'accepted_population_replays': 0, 'ROOT_writes': 0, 'GitHub_or_Git_operations': 0,
        'ended_at_utc': datetime.now(timezone.utc).isoformat()})
    print(json.dumps({'tests_run': result.testsRun, 'failed_ids': [item.id() for item, _ in result.failures + result.errors],
                      'inputs_held': before == after, 'unit_success': result.wasSuccessful(), 'wrapper_seconds': elapsed}, sort_keys=True))
    return 0 if result.wasSuccessful() and before == after else 1


if __name__ == '__main__':
    raise SystemExit(main())
