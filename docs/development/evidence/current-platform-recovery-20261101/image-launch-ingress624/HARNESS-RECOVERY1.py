import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path('/root/projects/nativecmpkit-worktrees/image-launch-readiness')
OUT = Path('/root/nativecmpkit-source-proposals-20261104/image-launch-ingress624')
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests as lt

plan = json.loads((OUT / 'RECOVERY-PLAN.json').read_bytes())
names = plan['only_selected_methods']
assert len(names) == len(set(names)) == 3
original = json.loads((OUT / 'PLAN-REVISED.json').read_bytes())
assert set(names) <= set(original['new_controls_proposed'] + original['affected_old_methods_proposed'])
assert not any('test_apple_image_launch_readiness.' in name for name in names)
assert not (OUT / 'IMPORTANT-RECOVERY1.json').exists()

def write(name, value):
    path = OUT / name
    assert not path.exists(), 'Refuse to overwrite first receipt'
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

before = lt.snapshot_inputs(ROOT)
write('INPUTS-RECOVERY1-BEFORE.json', {'schema_version': 1, 'scope': 'Actual current local source overlay before failed/changed-only3 recovery, not a compiler/native execution map', 'files': before, 'input_digest': lt.input_digest(before)})
class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []
        self.times = {}
        self.states = {}
    def startTest(self, test):
        super().startTest(test)
        self.times[test.id()] = time.monotonic()
        self.states[test.id()] = 'running'
    def addSuccess(self, test):
        super().addSuccess(test)
        self.states[test.id()] = 'passed'
    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.states[test.id()] = 'failed'
    def addError(self, test, error):
        super().addError(test, error)
        self.states[test.id()] = 'error'
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.states[test.id()] = 'skipped'
    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        if error:
            self.states[test.id()] = 'failed' if issubclass(error[0], test.failureException) else 'error'
    def stopTest(self, test):
        self.events.append({'name': test.id(), 'status': self.states[test.id()], 'elapsed_seconds': time.monotonic() - self.times[test.id()]})
        super().stopTest(test)

suite = unittest.defaultTestLoader.loadTestsFromNames(names)
def flatten(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten(test)
        else:
            yield test.id()
actual = list(flatten(suite))
assert actual == names, (actual, names)
attempts = []
def no_process(*args, **kwargs):
    attempts.append('unexpected-source-control-subprocess-boundary')
    raise AssertionError('Source-only ingress controls cannot execute subprocesses')
stream = io.StringIO()
started = time.monotonic()
with patch.object(subprocess, 'Popen', side_effect=no_process), patch.object(subprocess, 'run', side_effect=no_process):
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Result).run(suite)
elapsed = time.monotonic() - started
after = lt.snapshot_inputs(ROOT)
write('INPUTS-RECOVERY1-AFTER.json', {'schema_version': 1, 'scope': 'Actual current local source overlay after failed/changed-only3 recovery, not a compiler/native execution map', 'files': after, 'input_digest': lt.input_digest(after)})
held = before == after
assert held
report = {'schema_version': 1, 'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': 'Failure-only recovery: one failed old modal method plus two changed/owning NEW ingress methods; unchanged accepted first19 excluded and no image/native/SDK/compiler/profile replay', 'head_before_ingress_overlay': 'ddf19b1545eb05c46c7e69c087d216b03face61a', 'planned_names': names, 'actual_names': actual, 'methods_executed': result.testsRun, 'counts': {'passed': sum(event['status'] == 'passed' for event in result.events), 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped)}, 'successful': result.wasSuccessful(), 'elapsed_seconds': elapsed, 'events': result.events, 'failure_records': [{'name': test.id(), 'traceback': detail} for test, detail in result.failures], 'error_records': [{'name': test.id(), 'traceback': detail} for test, detail in result.errors], 'current_inputs_held': held, 'current_input_count': len(before), 'current_input_digest': lt.input_digest(before), 'unexpected_subprocess_attempts': len(attempts), 'native_SDK_compiler_profile_executions': 0, 'accepted_image_NEW18_replayed': False}
digest = write('IMPORTANT-RECOVERY1.json', report)
log = OUT / 'IMPORTANT-RECOVERY1.log'
assert not log.exists()
log.write_text(stream.getvalue())
print(json.dumps({'receipt': str(OUT / 'IMPORTANT-RECOVERY1.json'), 'sha256': digest, 'successful': report['successful'], 'counts': report['counts'], 'methods': result.testsRun, 'elapsed_seconds': elapsed, 'inputs_held': held, 'input_count': len(before), 'subprocess_attempts': len(attempts)}, sort_keys=True))
for error in report['failure_records'] + report['error_records']:
    print(error['name'])
    print(error['traceback'][-1200:])
sys.exit(0 if result.wasSuccessful() and held and not attempts else 1)
