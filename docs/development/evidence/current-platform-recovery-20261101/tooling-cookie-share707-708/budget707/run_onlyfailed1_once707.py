"""Only the one failed NEW17 method; accepted sixteen are not replayed."""
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time
import unittest
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
SOURCE = OUT / 'final'
PATHS = ('.github/workflows/gradle.yml', 'scripts/ci/offline_tooling_reuse.py',
         'scripts/ci/offline_tooling_provenance.py', 'scripts/ci/offline_tooling_failure_inventory.py',
         'scripts/ci/test_offline_tooling_scope_observation707.py')
METHOD = 'test_expired_time_does_not_call_fstat_or_claim_an_oversized_output_operand'


def capture():
    result = {}
    for relative in PATHS:
        path = SOURCE / relative
        before = path.stat()
        raw = path.read_bytes()
        after = path.stat()
        fields = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        if (path.is_symlink() or before.st_nlink != 1
                or tuple(getattr(before, field) for field in fields) != tuple(getattr(after, field) for field in fields)):
            raise ValueError('stable ordinary inputs required')
        result[relative] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                           'identity': [before.st_dev, before.st_ino, before.st_mtime_ns, before.st_ctime_ns]}
    return result


def write(leaf, value):
    with (OUT / leaf).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2); stream.write('\n')


def main():
    first = json.loads((OUT / 'FIRST17-EXECUTION-RESULT707.json').read_text())
    if first['tests_run'] != 17 or len(first['failures']) != 1 or first['errors']:
        raise ValueError('only the exact one original failed method may run')
    before = capture()
    write('ONLYFAILED1-EXECUTION-STARTED707.json', {'before': before, 'method': METHOD,
        'accepted16_replays': 0, 'started_at_utc': datetime.now(timezone.utc).isoformat()})
    started = time.monotonic()
    sys.path.insert(0, str(SOURCE / 'scripts/ci'))
    module = importlib.import_module('test_offline_tooling_scope_observation707')
    suite = unittest.TestSuite([module.ScopeObservation707Tests(METHOD)])
    with (OUT / 'ONLYFAILED1-ORIGINAL-UNITTEST.log').open('x') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    after = capture()
    receipt = {'before': before, 'after': after, 'inputs_held': before == after,
        'tests_run': result.testsRun, 'unit_success': result.wasSuccessful(),
        'failures': [item.id() for item, _ in result.failures], 'errors': [item.id() for item, _ in result.errors],
        'wrapper_seconds': time.monotonic() - started, 'accepted16_replays': 0,
        'ROOT_Git_GitHub_writes': 0, 'library_device_browser_consumer_executions': 0}
    write('ONLYFAILED1-EXECUTION-RESULT707.json', receipt)
    print(json.dumps({key: receipt[key] for key in ('tests_run', 'unit_success', 'inputs_held', 'wrapper_seconds', 'accepted16_replays')}))
    return 0 if result.wasSuccessful() and before == after else 1


if __name__ == '__main__':
    raise SystemExit(main())
