#!/usr/bin/env python3
"""Narrow pre-execution Windows close-baseline portability refinement, externally."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent


def row(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, raw):
    path = PACKET / name
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('xb') as output:
        output.write(raw)
    path.chmod(0o600)


def functions(raw):
    result = {}
    for node in ast.parse(raw.decode()).body:
        if isinstance(node, ast.FunctionDef):
            result[node.name] = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    result[node.name + '.' + child.name] = hashlib.sha256(ast.dump(child, include_attributes=False).encode()).hexdigest()
    return result


recipe_path = PACKET / 'EXACT-REPORT-CUSTODY-CORRECTION658.json'
recipe_raw = recipe_path.read_bytes()
assert row(recipe_raw)['sha256'] == '498af0e70ba061e178abdf325970bfaa568d73679fecac9fa97ecc8012d65746'
recipe = json.loads(recipe_raw)
driver_path = PACKET / 'proposed/scripts/ci/javafx_ordinary_maven_consumer.py'
control_path = PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'
driver_before, control_before = driver_path.read_bytes(), control_path.read_bytes()
assert row(driver_before) == recipe['driver']['after'] and row(control_before) == recipe['source_controls']['after']
write('retained/javafx_ordinary_maven_consumer.before-closed-file-baseline658.py', driver_before)
write('retained/test_javafx_ordinary_maven_route.before-closed-file-baseline658.py', control_before)
driver_old = """        owned = os.fstat(stream.fileno())
    custody = {'path': str(saved), 'source_path': str(path), 'bytes': len(payload),
               'sha256': hashlib.sha256(payload).hexdigest(), 'source_identity': list(source_identity),
               'file_identity': [owned.st_dev, owned.st_ino, owned.st_size, owned.st_mtime_ns, owned.st_ctime_ns]}
"""
driver_new = """        owned = os.fstat(stream.fileno())
    closed = saved.stat(follow_symlinks=False)
    need(not saved.is_symlink() and closed.st_nlink == 1 and
         (owned.st_dev, owned.st_ino) == (closed.st_dev, closed.st_ino) and closed.st_size == len(payload),
         'Closed retained input must remain the exact exclusively written owned file')
    custody = {'path': str(saved), 'source_path': str(path), 'bytes': len(payload),
               'sha256': hashlib.sha256(payload).hexdigest(), 'source_identity': list(source_identity),
               'file_identity': [closed.st_dev, closed.st_ino, closed.st_size, closed.st_mtime_ns, closed.st_ctime_ns]}
"""
control_old = """        self.assertEqual(ast.unparse(entries['file_identity']),
                         '[owned.st_dev, owned.st_ino, owned.st_size, owned.st_mtime_ns, owned.st_ctime_ns]')
        self.assertEqual(ast.unparse([node for node in capture.body if isinstance(node, ast.Return)][0].value), 'observed, custody')
"""
control_new = """        self.assertEqual(ast.unparse(entries['file_identity']),
                         '[closed.st_dev, closed.st_ino, closed.st_size, closed.st_mtime_ns, closed.st_ctime_ns]')
        opened = [node for node in capture.body if isinstance(node, ast.With)][0]
        self.assertLess(opened.end_lineno, assigned(capture, 'closed').lineno)
        ownership = [node for node in calls(capture, 'need') if '(owned.st_dev, owned.st_ino)' in ast.unparse(node.args[0])]
        self.assertEqual(len(ownership), 1)
        for required in ('not saved.is_symlink()', 'closed.st_nlink == 1',
                         '(owned.st_dev, owned.st_ino) == (closed.st_dev, closed.st_ino)', 'closed.st_size == len(payload)'):
            self.assertIn(required, ast.unparse(ownership[0].args[0]))
        self.assertEqual(ast.unparse([node for node in capture.body if isinstance(node, ast.Return)][0].value), 'observed, custody')
"""
assert driver_before.count(driver_old.encode()) == control_before.count(control_old.encode()) == 1
driver_after = driver_before.replace(driver_old.encode(), driver_new.encode(), 1)
control_after = control_before.replace(control_old.encode(), control_new.encode(), 1)
assert driver_after.replace(driver_new.encode(), driver_old.encode(), 1) == driver_before
assert control_after.replace(control_new.encode(), control_old.encode(), 1) == control_before
assert {name for name, sha in functions(driver_before).items() if functions(driver_after)[name] != sha} == {'retained_resolution'}
assert {name for name, sha in functions(control_before).items() if functions(control_after)[name] != sha} == {
    'JavafxOrdinaryMavenRouteSourceTests.test_new_retained_resolution_uses_one_raw_payload_for_exclusive_report_and_strict_observation'}
driver_path.write_bytes(driver_after)
control_path.write_bytes(control_after)
recipe['schema'] = 'nativecmpkit-javafx-retained-report-closed-baseline-exact-successor658-v1'
recipe['utc'] = datetime.now(timezone.utc).isoformat()
recipe['driver']['after'] = row(driver_after)
recipe['driver']['new_function_ASTs'] = functions(driver_after)
recipe['source_controls']['after'] = row(control_after)
recipe['source_controls']['new_function_and_method_ASTs'] = functions(control_after)
assert recipe['driver']['fragments'][0]['postimage'].count(driver_old) == 1
recipe['driver']['fragments'][0]['postimage'] = recipe['driver']['fragments'][0]['postimage'].replace(driver_old, driver_new, 1)
assert recipe['source_controls']['fragments'][1]['postimage'].count(control_old) == 1
recipe['source_controls']['fragments'][1]['postimage'] = recipe['source_controls']['fragments'][1]['postimage'].replace(control_old, control_new, 1)
recipe['pre_close_baseline_source_recipe'] = {**row(recipe_raw), 'path': 'EXACT-REPORT-CUSTODY-CORRECTION658.json',
                                             'retained_driver': 'retained/javafx_ordinary_maven_consumer.before-closed-file-baseline658.py',
                                             'retained_controls': 'retained/test_javafx_ordinary_maven_route.before-closed-file-baseline658.py'}
recipe['pre_execution_portability_refinement'] = {
    'authority': 'Independent705 pre-source observation; not a Windows failure or execution claim',
    'reason': 'Windows last-write timestamps may be finalized at write-handle close',
    'fix': 'Require closed file dev/ino equal owned handle dev/ino and exact byte size; use guarded closed-file timestamp baseline for subsequent custody',
    'driver_fragment': {'preimage': driver_old, 'postimage': driver_new},
    'source_control_fragment': {'preimage': control_old, 'postimage': control_new},
    'selected_methods_changed': False, 'tests_native_or_target_execution_yet': 0,
}
write('EXACT-REPORT-CUSTODY-CLOSED-BASELINE-CORRECTION658.json', (json.dumps(recipe, indent=2, sort_keys=True) + '\n').encode())
print(json.dumps({'passed': True, 'driver': row(driver_after), 'controls': row(control_after),
                  'recipe': row((PACKET / 'EXACT-REPORT-CUSTODY-CLOSED-BASELINE-CORRECTION658.json').read_bytes()),
                  'selection_remains_changed1_NEW2': True, 'native_execution': 0}, sort_keys=True))
