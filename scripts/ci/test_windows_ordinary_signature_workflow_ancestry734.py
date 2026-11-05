# SPDX-License-Identifier: Apache-2.0
"""Sole NEW1 pure routing AST control: no observer import, legacy body, worker or GET."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import unittest

SOURCE_ROOT = Path(os.environ.get('NATIVECMPKIT_SIGNATURE734_ANCESTRY_SOURCE_ROOT',
    str(Path(__file__).resolve().parents[2])))
WORKFLOW_ROOT = Path(os.environ.get('NATIVECMPKIT_SIGNATURE734_ANCESTRY_WORKFLOW_ROOT', str(SOURCE_ROOT)))
PLAN_ROOT = Path(os.environ.get('NATIVECMPKIT_SIGNATURE734_ANCESTRY_PLAN_ROOT', str(SOURCE_ROOT)))
OWN_PATH = 'scripts/ci/windows_ordinary_vanniktech_signature_observer734.py'
WORKFLOW_PATH = '.github/workflows/javafx-library-candidate.yml'
PLAN_PATH = 'scripts/ci/windows-ordinary-signature734-plan.json'
OBSERVERBYTES = 49128
OBSERVERSHA = '6d573297c1f6b5f5581b98540d490de36728cef9b043cf7ea45a509275546b1f'
WORKFLOWBYTES = 17637
WORKFLOWSHA = '1f32078e6aa3508a404e7718f822017c7a2d8b464cf82d443f6ec427852aefe5'
PLANSHA = 'bf3cdca3083092e7e79ab583e34d48eb04a8e7bd1d337963e1a1aad5bf266632'
HISTORICAL_ROUTING_ASTSHA = 'b79ff5948cce74d0b974938d91ff20cff181dd3d21a9138c30e2af13dfc7e12c'
IMPORT_DIAGNOSTIC_SOURCE_SHA = 'bea6937a80b16602f9e3134ccdf5c848964c5c7af3eb084c1ab13d8e5040fce5'
STAT_SUFFIX_SHA = '45130b6cc1189cf03f85f5104b0d9a08e2fe8a35778c6fe8886eb996ed321a8f'
FIELDS = ('st_mode', 'st_dev', 'st_ino', 'st_nlink', 'st_uid', 'st_gid',
          'st_size', 'st_atime_ns', 'st_mtime_ns', 'st_ctime_ns')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def view(info):
    return tuple(getattr(info, key) for key in FIELDS)


def read_exact(path, expected_bytes, expected_sha):
    if path.resolve(strict=True) != path:
        raise AssertionError('Exact named source endpoint, no alias')
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != expected_bytes:
        raise AssertionError('Only the declared bounded regular source endpoint')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME)
    try:
        opened = os.fstat(fd)
        if view(opened) != view(before):
            raise AssertionError('Named and opened source full10 differ')
        raw = bytearray()
        while True:
            part = os.read(fd, min(16384, expected_bytes + 1 - len(raw)))
            if not part:
                break
            raw.extend(part)
            if len(raw) > expected_bytes:
                raise AssertionError('Declared source cap')
        ended = os.fstat(fd)
    finally:
        os.close(fd)
    after = path.lstat()
    if not view(before) == view(opened) == view(ended) == view(after):
        raise AssertionError('Source full10 custody changed')
    raw = bytes(raw)
    if len(raw) != expected_bytes or digest(raw) != expected_sha:
        raise AssertionError('Exact source byte/hash seal')
    return raw, view(before)


class WorkflowAncestry734Tests(unittest.TestCase):
    def test_NEW01_exact_current_chain_historical_guards_and_unknowns_refuse(self):
        inputs = [(SOURCE_ROOT / OWN_PATH, OBSERVERBYTES, OBSERVERSHA),
                  (WORKFLOW_ROOT / WORKFLOW_PATH, WORKFLOWBYTES, WORKFLOWSHA),
                  (PLAN_ROOT / PLAN_PATH, 6448, PLANSHA)]
        raw, own_stat = read_exact(*inputs[0])
        current, workflow_stat = read_exact(*inputs[1])
        plan_raw, plan_stat = read_exact(*inputs[2])
        held = [own_stat, workflow_stat, plan_stat]
        plan = json.loads(plan_raw)
        text = raw.decode('utf-8', errors='strict')
        tree = ast.parse(text)
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        routing = functions['restore_signature_workflow_routing']
        self.assertEqual(digest(ast.dump(ast.Module(body=routing.body[1:], type_ignores=[]),
                                        include_attributes=False).encode()), HISTORICAL_ROUTING_ASTSHA)
        self.assertEqual(digest(ast.get_source_segment(text, functions['_read_pinned_base_source']).encode()),
                         IMPORT_DIAGNOSTIC_SOURCE_SHA)
        # Extract only the already-pinned pure routing function and four byte constants.
        scope = {'__builtins__': {'type': type, 'bytes': bytes, 'len': len}, 'digest': digest}
        guard_calls = []
        def need(ok, message):
            guard_calls.append(message)
            if not ok:
                raise ValueError(message)
        scope['need'] = need
        for name in ('OLD_RUN', 'NEW_RUN', 'OLD_UPLOAD', 'NEW_UPLOAD'):
            assignments = [node for node in tree.body if isinstance(node, ast.Assign) and
                           any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
            self.assertEqual(len(assignments), 1)
            value = ast.literal_eval(assignments[0].value)
            self.assertIs(type(value), bytes)
            scope[name] = value
        only_routing = ast.Module(body=[routing], type_ignores=[])
        exec(compile(only_routing, '<sole-pure-routing734-NEW1>', 'exec'), scope)
        restore = scope['restore_signature_workflow_routing']
        context_choice = b', windows-import-context-stat-only-diagnostic1'
        stat_choice = b', windows-import-stat-only-diagnostic1'
        context_suffix = current[-1133:]
        self.assertEqual(digest(context_suffix), '3d96f39abeb19a440307bc9f58725ba30ef1af28389165164d7a6929a21e02df')
        self.assertEqual(current[:-1133].count(context_choice), 1)
        accepted813 = current[:-1133].replace(context_choice, b'', 1)
        self.assertEqual((len(accepted813), digest(accepted813)),
                         (16458, '0e835bce9fd2fdcd2b437171ef7332525199d1c670f08d982f8477646485dd93'))
        stat_suffix = accepted813[-1113:]
        self.assertEqual(digest(stat_suffix), STAT_SUFFIX_SHA)
        self.assertEqual(accepted813[:-1113].count(stat_choice), 1)
        historical = accepted813[:-1113].replace(stat_choice, b'', 1)
        self.assertEqual((len(historical), digest(historical)),
                         (15307, 'f98d48c7c0343d1fe0e8e07c3c87bca1d0d55c3341a3ab232d200b89433a4493'))
        before = historical.replace(scope['NEW_RUN'], scope['OLD_RUN']).replace(scope['NEW_UPLOAD'], scope['OLD_UPLOAD'])
        self.assertEqual((len(before), digest(before)),
                         (15299, '204c367e1da4f234a6d7fc1131baa4b94d48be5a50f0a402b95759c92ff76e00'))
        self.assertEqual(restore(current, plan), before)
        self.assertEqual(restore(historical, plan), before)
        class BytesSubclass(bytes):
            pass
        malformed = [accepted813, current[:-1133], current.replace(context_choice, b'', 1),
                     current + b'\n', current[:-1], b'X' + current[1:],
                     current.replace(context_choice, context_choice[:-1] + b'2', 1),
                     current.replace(stat_choice, stat_choice[:-1] + b'2', 1),
                     current[:-1133] + context_suffix.replace(b'timeout-minutes: 2', b'timeout-minutes: 3', 1),
                     current + context_suffix, current.replace(context_choice, context_choice + context_choice, 1),
                     historical + b'\n  unrelated-job: {}\n', b'X' + historical[1:],
                     historical.replace(scope['NEW_RUN'], scope['OLD_RUN'], 1),
                     historical.replace(scope['NEW_UPLOAD'], scope['OLD_UPLOAD'], 1),
                     bytearray(current), current.decode(), BytesSubclass(current)]
        for index, payload in enumerate(malformed):
            with self.subTest(refusal=index):
                with self.assertRaises(ValueError):
                    restore(payload, plan)
        for key, value in [('after_bytes', 17637), ('after_sha256', WORKFLOWSHA),
                           ('before_bytes', 15300), ('before_sha256', '0' * 64)]:
            changed_plan = dict(plan)
            changed_plan['workflow_routing'] = dict(plan['workflow_routing'])
            changed_plan['workflow_routing'][key] = value
            with self.subTest(plan_refusal=key):
                with self.assertRaises(ValueError):
                    restore(current, changed_plan)
        self.assertIn('Exactly two coupled observational command/public-JSON output spans', guard_calls)
        self.assertIn('All prior native, ordinary-consumer, private Stop, permissions and action bytes remain exact', guard_calls)
        for spec, original_stat in zip(inputs, held):
            _again, after_stat = read_exact(*spec)
            self.assertEqual(after_stat, original_stat)


if __name__ == '__main__':
    unittest.main()
