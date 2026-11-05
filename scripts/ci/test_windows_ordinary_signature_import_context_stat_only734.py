# SPDX-License-Identifier: Apache-2.0
"""One NEW fake/AST selector only. Never import the observer or legacy module."""
import ast
import copy
import contextlib
import io
import hashlib
import json
import os
from pathlib import Path
import stat
import types
import unittest

ROOT = Path(__file__).resolve().parents[2]
OWN = 'scripts/ci/windows_ordinary_vanniktech_signature_observer734.py'
ENTRY = 'scripts/ci/windows_ordinary_signature_import_context_stat_only734.py'
OWN_BYTES = 47766
OWN_SHA256 = '5b50b082d29cc633ca5a6054904cb1c49362969d70e74ff224f8ebaabc42cb2e'
ENTRY_BYTES = 9794
ENTRY_SHA256 = '53ec009e15b3f62ac17693b8d7e357950020df72afe951d93eee64b18c8090ed'
WORKFLOW = '.github/workflows/javafx-library-candidate.yml'
WORKFLOW_BYTES = 17637
WORKFLOW_SHA256 = '1f32078e6aa3508a404e7718f822017c7a2d8b464cf82d443f6ec427852aefe5'
WORKFLOW_BASE_BYTES = 16458
WORKFLOW_BASE_SHA256 = '0e835bce9fd2fdcd2b437171ef7332525199d1c670f08d982f8477646485dd93'
OPTIONS_BEFORE = b'        options: [linux-arm64, macos-arm64, macos-x64, windows, windows-ordinary-consumer1, windows-ordinary-dependency-observation1, windows-observer-one-request-diagnostic1, windows-import-stat-only-diagnostic1]\n'
OPTIONS_AFTER = b'        options: [linux-arm64, macos-arm64, macos-x64, windows, windows-ordinary-consumer1, windows-ordinary-dependency-observation1, windows-observer-one-request-diagnostic1, windows-import-stat-only-diagnostic1, windows-import-context-stat-only-diagnostic1]\n'
ADDITIVE_JOB = b"\n  # Context-matched pre-read comparison only: original failure cause remains unknown.\n  windows-import-context-stat-only-diagnostic1:\n    if: github.repository == 'Apdelrahman1911/nativeCmpkit' && github.ref == 'refs/heads/development/javafx-ordinary-consumer1' && github.event_name == 'workflow_dispatch' && inputs.platform == 'windows-import-context-stat-only-diagnostic1'\n    runs-on: windows-2025\n    timeout-minutes: 2\n    permissions:\n      contents: read\n    defaults:\n      run:\n        shell: pwsh\n    env:\n      GIT_CONFIG_COUNT: '2'\n      GIT_CONFIG_KEY_0: core.autocrlf\n      GIT_CONFIG_VALUE_0: 'false'\n      GIT_CONFIG_KEY_1: core.longpaths\n      GIT_CONFIG_VALUE_1: 'true'\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          persist-credentials: false\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.12'\n      - name: Exact import prologue and global stat call only, no base body or GET\n        run: python -I -S -B scripts/ci/windows_ordinary_signature_import_context_stat_only734.py\n      # No artifact upload: only bounded numeric metadata appears in the job log.\n"
EXACT_NEW_IF = b"    if: github.repository == 'Apdelrahman1911/nativeCmpkit' && github.ref == 'refs/heads/development/javafx-ordinary-consumer1' && github.event_name == 'workflow_dispatch' && inputs.platform == 'windows-import-context-stat-only-diagnostic1'\n"
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


class ImportContextStatOnly734Tests(unittest.TestCase):
    def test_NEW01_context_exact_prologue_global_call_stat_stops_and_exact_manual_windows_job(self):
        observer_raw = read_exact(OWN, OWN_BYTES, OWN_SHA256)
        entry_raw = read_exact(ENTRY, ENTRY_BYTES, ENTRY_SHA256)
        observer_tree, entry_tree = ast.parse(observer_raw), ast.parse(entry_raw)
        owner = next(node for node in observer_tree.body if isinstance(node, ast.FunctionDef) and node.name == '_read_pinned_base_source')
        probe = next(node for node in entry_tree.body if isinstance(node, ast.FunctionDef) and node.name == '_read_pinned_base_source')
        owner_index, probe_index = observer_tree.body.index(owner), entry_tree.body.index(probe)
        dump = lambda node: ast.dump(node, include_attributes=False)
        self.assertEqual([dump(node) for node in observer_tree.body[:owner_index]],
                         [dump(node) for node in entry_tree.body[:probe_index]])
        self.assertEqual(dump(owner.args), dump(probe.args))
        owner_try = next(node for node in owner.body if isinstance(node, ast.Try))
        probe_try = next(node for node in probe.body if isinstance(node, ast.Try))
        self.assertEqual(owner.body.index(owner_try), 11)
        self.assertEqual([dump(node) for node in owner.body[:11]], [dump(node) for node in probe.body[:11]])
        self.assertEqual([dump(node) for node in owner_try.body[:2]], [dump(node) for node in probe_try.body[:2]])
        self.assertEqual([dump(node) for node in owner_try.finalbody], [dump(node) for node in probe_try.finalbody])
        original_call = next(node for node in observer_tree.body if isinstance(node, ast.Assign) and
            any(isinstance(target, ast.Name) and target.id == '_base_source' for target in node.targets))
        top = entry_tree.body[probe_index + 1:]
        self.assertEqual(len(top), 3)
        self.assertIsInstance(top[0], ast.Try)
        self.assertEqual([dump(node) for node in top[0].body], [dump(original_call)])
        self.assertEqual(len([node for node in entry_tree.body if isinstance(node, ast.FunctionDef)]), 1)
        expected_comparison = ast.dump(ast.parse('view(opened) != view(before)', mode='eval').body, include_attributes=False)
        for function in (owner, probe):
            self.assertEqual(sum(isinstance(node, ast.If) and ast.dump(node.test, include_attributes=False) == expected_comparison
                                 for node in ast.walk(function)), 1)
        for node in ast.walk(entry_tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
                self.assertNotIn(name, {'read', 'read_bytes', 'read_text', 'fdopen', 'exec', 'eval', 'compile', '__import__',
                    'sha256', 'controller', 'worker', 'observe_one', 'Popen', 'urlopen', 'request'})
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
            return namespace[function.name], events

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
        for differing in (False, True):
            opened_values = list(named_values)
            if differing:
                opened_values[6] += 1
            invoke, events = fake(probe, opened_values)
            out, err = io.StringIO(), io.StringIO()
            namespace = {'_read_pinned_base_source': invoke, 'sys': types.SimpleNamespace(stderr=err)}
            isolated = ast.fix_missing_locations(ast.Module(body=copy.deepcopy(top), type_ignores=[]))
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as terminal:
                exec(compile(isolated, '<exact-module-global-stat-only-call-with-fake-operands>', 'exec'), namespace)
            self.assertEqual(terminal.exception.code, int(differing))
            self.assertEqual(events, expected_events)
            emitted = err.getvalue() if differing else out.getvalue()
            self.assertEqual(out.getvalue() if differing else err.getvalue(), '')
            self.assertTrue(emitted.endswith(chr(10)))
            payload = emitted[len(prefix):-1] if differing else emitted[:-1]
            self.assertLessEqual(len(payload), 2048)
            self.assertEqual(json.loads(payload), {'fields': list(FIELDS),
                'named7_decimal': [str(value) for value in named_values],
                'descriptor7_decimal': [str(value) for value in opened_values],
                'differing_zero_based_indexes': [6] if differing else []})

        # Fourth exact source input only: static workflow/selector guard, never execute it.
        workflow_raw = read_exact(WORKFLOW, WORKFLOW_BYTES, WORKFLOW_SHA256)
        self.assertTrue(workflow_raw.endswith(ADDITIVE_JOB))
        self.assertEqual(workflow_raw.count(OPTIONS_AFTER), 1)
        prior = workflow_raw[:-len(ADDITIVE_JOB)]
        prior = prior.replace(OPTIONS_AFTER, OPTIONS_BEFORE)
        self.assertEqual((len(prior), hashlib.sha256(prior).hexdigest()),
                         (WORKFLOW_BASE_BYTES, WORKFLOW_BASE_SHA256))
        self.assertEqual(ADDITIVE_JOB.count(EXACT_NEW_IF), 1)
        self.assertEqual(ADDITIVE_JOB.count(b'    runs-on: windows-2025\n'), 1)
        self.assertEqual(ADDITIVE_JOB.count(b'    timeout-minutes: 2\n'), 1)
        self.assertEqual(ADDITIVE_JOB.count(b'    permissions:\n      contents: read\n'), 1)
        self.assertEqual(ADDITIVE_JOB.count(b"          python-version: '3.12'\n"), 1)
        self.assertEqual(ADDITIVE_JOB.count(b'\n        run:'), 1)
        self.assertEqual(ADDITIVE_JOB.count(('        run: python -I -S -B ' + ENTRY + '\n').encode()), 1)
        self.assertEqual(ADDITIVE_JOB.count(b'\n      - uses:'), 2)
        self.assertEqual(ADDITIVE_JOB.count(b'          persist-credentials: false\n'), 1)
        self.assertNotIn(b'uses: actions/upload-artifact', ADDITIVE_JOB)


if __name__ == '__main__':
    unittest.main()
