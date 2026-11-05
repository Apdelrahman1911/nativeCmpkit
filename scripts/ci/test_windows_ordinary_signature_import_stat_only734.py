# SPDX-License-Identifier: Apache-2.0
"""One NEW fake/AST selector only. Never import the observer or legacy module."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import types
import unittest

ROOT = Path(__file__).resolve().parents[2]
OWN = 'scripts/ci/windows_ordinary_vanniktech_signature_observer734.py'
ENTRY = 'scripts/ci/windows_ordinary_signature_import_stat_only734.py'
OWN_BYTES = 47766
OWN_SHA256 = '5b50b082d29cc633ca5a6054904cb1c49362969d70e74ff224f8ebaabc42cb2e'
ENTRY_BYTES = 3742
ENTRY_SHA256 = '96eaff08c64138e8a382b08ef2e47ec8728386741efabf873702c0b285f53fcd'
FIELDS = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
STAT10 = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size',
          'st_atime_ns', 'st_mtime_ns', 'st_ctime_ns')


def read_exact(relative, count, expected_sha):
    path = ROOT / relative
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != count:
        raise AssertionError('Exact declared owning source only')
    pin = tuple(getattr(before, key) for key in STAT10)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME)
    try:
        if tuple(getattr(os.fstat(fd), key) for key in STAT10) != pin:
            raise AssertionError('Source descriptor custody')
        raw = b''
        while True:
            block = os.read(fd, min(65536, count + 1 - len(raw)))
            if not block:
                break
            raw += block
            if len(raw) > count:
                raise AssertionError('Source cap')
        if tuple(getattr(os.fstat(fd), key) for key in STAT10) != pin:
            raise AssertionError('Source read custody')
    finally:
        os.close(fd)
    if tuple(getattr(path.lstat(), key) for key in STAT10) != pin or len(raw) != count or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise AssertionError('Exact held source bytes/hash/full10')
    return raw


class ImportNumericOnly734Tests(unittest.TestCase):
    def test_NEW01_failed_import_numeric_refusal_and_stat_only_stop_are_exact(self):
        observer_raw = read_exact(OWN, OWN_BYTES, OWN_SHA256)
        entry_raw = read_exact(ENTRY, ENTRY_BYTES, ENTRY_SHA256)
        observer_tree, entry_tree = ast.parse(observer_raw), ast.parse(entry_raw)
        owner = next(node for node in observer_tree.body if isinstance(node, ast.FunctionDef) and node.name == '_read_pinned_base_source')
        probe = next(node for node in entry_tree.body if isinstance(node, ast.FunctionDef) and node.name == '_fixed_import_stat_only')
        expected_comparison = ast.dump(ast.parse('view(opened) != view(before)', mode='eval').body, include_attributes=False)
        for function in (owner, probe):
            self.assertEqual(sum(isinstance(node, ast.If) and ast.dump(node.test, include_attributes=False) == expected_comparison
                                 for node in ast.walk(function)), 1)
        for node in ast.walk(entry_tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
                self.assertNotIn(name, {'read', 'read_bytes', 'read_text', 'fdopen', 'exec', 'eval', 'compile', '__import__',
                    'sha256', 'controller', 'worker', 'observe_one', 'Popen', 'urlopen', 'request'})
        text = observer_raw.decode()
        controller = next(node for node in observer_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'controller')
        critical = ast.get_source_segment(text, controller).split('    process = job = None' + chr(10), 1)[1].split('    worker_report = None' + chr(10), 1)[0]
        self.assertEqual(hashlib.sha256(critical.encode()).hexdigest(), 'ff425c9110024f90b8b1f2ce45426bd32737e8965d89851bdf9db7fa6495d14a')
        named_values = (2**63 + 9, 2**127 + 51, stat.S_IFREG | 0o644, 1, 65242, 1793904432737934301, 1793904432737934303)
        fixed_path = 'scripts/ci/windows_ordinary_dependency_observer742.py'
        original = 'Named/descriptor import source differs'
        prefix = original + '; numeric-only='

        def fake(function, opened_values):
            events = []
            named = types.SimpleNamespace(**dict(zip(FIELDS, named_values)))
            opened = types.SimpleNamespace(**dict(zip(FIELDS, opened_values)))
            directory = types.SimpleNamespace(st_dev=17, st_ino=19, st_mode=stat.S_IFDIR | 0o700, st_file_attributes=0)

            class Endpoint:
                def __init__(self, label):
                    self.label = label
                def __truediv__(self, relative):
                    return Endpoint(self.label + '/' + relative)
                def __eq__(self, other):
                    return type(other) is Endpoint and self.label == other.label
                def resolve(self, strict=True):
                    return self
                def lstat(self):
                    events.append(('lstat', self.label))
                    return named if self.label == 'fixed/' + fixed_path else directory

            root = Endpoint('fixed')
            def opened_fd(path, flags):
                self.assertEqual(path.label, 'fixed/' + fixed_path)
                events.append(('open', 987))
                return 987
            def fstat_fd(fd):
                self.assertEqual(fd, 987)
                events.append(('fstat', fd))
                return opened
            def closed_fd(fd):
                self.assertEqual(fd, 987)
                events.append(('close', fd))
            def forbidden(*args, **kwargs):
                raise AssertionError('No source body read/hash/exec or further stage on this diagnostic')
            fake_os = types.SimpleNamespace(O_RDONLY=0, O_BINARY=0, O_NOFOLLOW=0, O_NOATIME=0,
                open=opened_fd, fstat=fstat_fd, close=closed_fd, read=forbidden)
            namespace = {'ROOT': root, 'BASE_PATH': fixed_path, 'BASE_BYTES': 65242, 'os': fake_os,
                'stat': stat, 'json': json, 'hashlib': types.SimpleNamespace(sha256=forbidden)}
            isolated = ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(function)], type_ignores=[]))
            exec(compile(isolated, '<exact-owning-failed-import-function-only>', 'exec'), namespace)
            return (lambda: namespace[function.name](root)) if function is probe else namespace[function.name], events

        expected_events = [('lstat', 'fixed'), ('lstat', 'fixed/scripts'), ('lstat', 'fixed/scripts/ci'),
                           ('lstat', 'fixed/' + fixed_path), ('open', 987), ('fstat', 987), ('close', 987)]
        for index in range(7):
            opened_values = list(named_values)
            opened_values[index] += 1
            for function in (owner, probe):
                invoke, events = fake(function, opened_values)
                with self.subTest(function=function.name, differing_index=index), self.assertRaises(ValueError) as refusal:
                    invoke()
                message = str(refusal.exception)
                self.assertTrue(message.startswith(prefix))
                self.assertLessEqual(len(message), len(prefix) + 2048)
                self.assertEqual(json.loads(message[len(prefix):]), {'fields': list(FIELDS),
                    'named7_decimal': [str(value) for value in named_values],
                    'descriptor7_decimal': [str(value) for value in opened_values],
                    'differing_zero_based_indexes': [index]})
                self.assertEqual(events, expected_events)
        for invalid in (True, 1.0, 'unqualified-text-must-not-render', 2**256):
            opened_values = list(named_values)
            opened_values[0] = invalid
            for function in (owner, probe):
                invoke, events = fake(function, opened_values)
                with self.subTest(function=function.name, invalid_type=type(invalid).__name__), self.assertRaises(ValueError) as refusal:
                    invoke()
                self.assertEqual(str(refusal.exception), original)
                self.assertEqual(events, expected_events)
        invoke, events = fake(probe, named_values)
        detail = invoke()
        self.assertLessEqual(len(detail), 2048)
        self.assertEqual(json.loads(detail), {'fields': list(FIELDS),
            'named7_decimal': [str(value) for value in named_values],
            'descriptor7_decimal': [str(value) for value in named_values], 'differing_zero_based_indexes': []})
        self.assertEqual(events, expected_events)


if __name__ == '__main__':
    unittest.main()
