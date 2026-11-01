"""New bounded KVM timeline models only; all KVM/identity/process operations mocked."""
from __future__ import annotations
import ast
from contextlib import ExitStack, contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import android_kvm_timeline as kvm

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "scripts/ci/android_device_tests.py"
BATCH = ROOT / "scripts/ci/android_device_batch.py"
YAML = ROOT / ".github/workflows/gradle.yml"
CI = {"GITHUB_ACTIONS": "true", "SUITE": "android-device", "ANDROID_BATCH": "android-permission-storage-api35-recovery"}
UNDEFINED = 0xffffffff


def functions(path):
    text = path.read_text()
    return text, {node.name: node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}


def acl(uid=1001, permissions=6, mask=4):
    entries = [(1, 6, UNDEFINED), (2, permissions, uid), (2, 7, 910001),
               (4, 6, UNDEFINED), (8, 7, 920002), (16, mask, UNDEFINED), (32, 0, UNDEFINED)]
    return struct.pack("<I", 2) + b"".join(struct.pack("<HHI", *entry) for entry in entries)


def info(inode=17, mode=stat.S_IFCHR | 0o660, ctime=123):
    return SimpleNamespace(st_dev=5, st_ino=inode, st_rdev=1234, st_uid=0, st_gid=108,
                           st_mode=mode, st_ctime_ns=ctime)


class KvmTimelineTests(unittest.TestCase):
    @contextmanager
    def host(self, *, body=None, nodes=None, groups=None, uid=1001, euid=2002, scope=None):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(kvm.os.environ, CI if scope is None else scope, clear=True))
            stack.enter_context(patch.object(kvm.platform, "system", return_value="Linux"))
            stack.enter_context(patch.object(kvm.platform, "machine", return_value="x86_64"))
            probes = {}
            for name, value in (("getuid", uid), ("geteuid", euid), ("getgid", 100), ("getegid", 200),
                                ("getgroups", [9, 2] if groups is None else groups)):
                probes[name] = stack.enter_context(patch.object(kvm.os, name, side_effect=value if isinstance(value, Exception) else None,
                                                               return_value=value if not isinstance(value, Exception) else None))
            def stat_read(path):
                self.assertEqual("/dev/kvm", path)
                return info() if nodes is None else next(nodes)
            probes["lstat"] = stack.enter_context(patch.object(kvm.os, "lstat", side_effect=stat_read))
            def xattr_read(path, attribute, *, follow_symlinks):
                self.assertEqual("/dev/kvm", path); self.assertEqual("system.posix_acl_access", attribute)
                self.assertIs(follow_symlinks, False)
                value = acl() if body is None else body
                if isinstance(value, Exception):
                    raise value
                return value
            probes["getxattr"] = stack.enter_context(patch.object(kvm.os, "getxattr", side_effect=xattr_read))
            yield probes

    def test_selected_real_uid_row_and_mask_are_exact_without_other_user_inventory(self):
        with self.host() as probes:
            value = kvm.observe("acl-after")
        self.assertEqual("observed", value["status"]); self.assertEqual((1001, 2002, 100, 200), tuple(value[k] for k in ("uid", "euid", "gid", "egid")))
        self.assertEqual([2, 9], value["groups"]); self.assertIs(value["selected_uid_present"], True)
        self.assertEqual((6, 4, 4), tuple(value[k] for k in ("selected_uid_permissions", "acl_mask", "selected_uid_masked_permissions")))
        self.assertEqual({"device": 5, "inode": 17, "rdev": 1234, "uid": 0, "gid": 108, "mode": 0o660,
                          "ctime_ns": 123, "character_device": True}, value["node"])
        self.assertIs(value["node_stable"], True); self.assertIs(value["native_success_inferred"], False)
        self.assertNotIn("910001", json.dumps(value)); self.assertNotIn("920002", json.dumps(value))
        self.assertNotIn("/", json.dumps(value)); self.assertEqual(2, probes["lstat"].call_count)
        probes["getxattr"].assert_called_once_with("/dev/kvm", "system.posix_acl_access", follow_symlinks=False)
        self.assertEqual(value, kvm.validate(value))

    def test_unknown_malformed_or_oversized_acl_is_null_and_absence_does_not_synthesize_a_grant(self):
        original = acl()
        variants = [None, "private-untrusted-output", b"", original[:-1], original + b"x",
                    struct.pack("<I", 3) + original[4:],
                    struct.pack("<I", 2) + struct.pack("<HHI", 99, 6, UNDEFINED) + original[12:],
                    original[:4] + struct.pack("<HHI", 1, 8, UNDEFINED) + original[12:],
                    original[:4] + struct.pack("<HHI", 1, 6, 0) + original[12:],
                    original[:12] + original[12:20] + original[12:],
                    original[:-16] + original[-8:], original[:4] + original[12:],
                    struct.pack("<I", 2) + struct.pack("<HHI", 2, 6, 1001) * 65]
        for index, body in enumerate(variants):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):
                    kvm.selected_acl(body, 1001)
                if body is not None:
                    with self.host(body=body):
                        value = kvm.observe("acl-before")
                    self.assertEqual("failed-observation", value["status"])
                    for key in ("selected_uid_present", "selected_uid_permissions", "acl_mask", "selected_uid_masked_permissions"):
                        self.assertIsNone(value[key])
        with self.host(body=OSError(__import__("errno").ENODATA, "private-unpublished-body")):
            absent = kvm.observe("acl-before")
        self.assertEqual("absent", absent["acl_status"]); self.assertIs(absent["selected_uid_present"], False)
        self.assertIsNone(absent["selected_uid_permissions"]); self.assertIsNone(absent["acl_mask"])
        with self.host(body=PermissionError("private-unpublished-body")):
            denied = kvm.observe("acl-after")
        self.assertEqual("failed-observation", denied["status"]); self.assertIsNone(denied["selected_uid_present"])
        self.assertNotIn("private", json.dumps(denied))

    def test_principal_mask_and_node_changes_are_observed_but_in_frame_instability_clears_acl(self):
        with self.host(nodes=iter([info(17), info(17), info(18, ctime=124), info(18, ctime=124)])):
            with patch.object(kvm.os, "getuid", side_effect=[1001, 1002]), patch.object(kvm.os, "getxattr", side_effect=[acl(), acl(1002, 6, 6)]):
                before = kvm.observe("child-before"); after = kvm.observe("child-after")
        self.assertEqual((1001, 1002), (before["uid"], after["uid"])); self.assertEqual((17, 18), (before["node"]["inode"], after["node"]["inode"]))
        self.assertEqual((4, 6), (before["acl_mask"], after["acl_mask"]))
        self.assertEqual("observed", after["status"]); self.assertIs(after["native_success_inferred"], False)
        self.assertNotIn("cause", after)
        with self.host(nodes=iter([info(17), info(18)])):
            unstable = kvm.observe("reclaim-after")
        self.assertIs(unstable["node_stable"], False); self.assertEqual("failed-observation", unstable["status"])
        for key in ("selected_uid_present", "selected_uid_permissions", "acl_mask", "selected_uid_masked_permissions"):
            self.assertIsNone(unstable[key])

    def test_only_owned_finite_ci_scope_and_bounded_self_facts_can_probe_the_fixed_character_device(self):
        for scope in ({}, {**CI, "GITHUB_ACTIONS": "false"}, {**CI, "SUITE": "desktop"}, {**CI, "ANDROID_BATCH": "all"}):
            with self.subTest(scope=scope), self.host(scope=scope) as probes:
                value = kvm.observe("child-before")
                self.assertEqual("failed-observation", value["status"])
                for name in ("getuid", "getgroups", "lstat", "getxattr"):
                    probes[name].assert_not_called()
        with self.host() as probes:
            self.assertTrue(kvm.active(35, "android-permission-demo-contracts"))
            self.assertFalse(kvm.active(34, "android-permission-demo-contracts")); self.assertFalse(kvm.active(35, "webview-lifetime"))
        for groups in ([1] * 65, [True], ["private-name"]):
            with self.subTest(groups=groups), self.host(groups=groups) as probes:
                value = kvm.observe("child-before"); self.assertEqual("failed-observation", value["status"])
                probes["lstat"].assert_not_called(); probes["getxattr"].assert_not_called()
        for mode in (stat.S_IFLNK | 0o777, stat.S_IFREG | 0o600):
            with self.subTest(mode=mode), self.host(nodes=iter([info(mode=mode)])) as probes:
                value = kvm.observe("child-before"); self.assertEqual("failed-observation", value["status"])
                probes["getxattr"].assert_not_called()
        with self.host(groups=list(range(64)), uid=kvm.UINT32_ID_MAX, euid=kvm.UINT32_ID_MAX, body=acl(kvm.UINT32_ID_MAX)):
            largest = kvm.observe("child-before")
        self.assertLessEqual(len(json.dumps(largest).encode()), kvm.MAX_JSON_BYTES); self.assertEqual(largest, kvm.validate(largest))
        with self.host(uid=ValueError("private-unpublished-body")) as probes:
            value = kvm.observe("child-before"); self.assertIsNone(value["uid"]); probes["lstat"].assert_not_called()

    def test_original_host_conjunction_exception_marker_and_sole_acl_writer_remain_source_exact(self):
        source, found = functions(CONTROLLER)
        for name, expected in (("require_host", "7503a81c5cf4e33580ae42536a093beb73251c276c78451d58d996d83c86ff09"),
                               ("record_host_admission_refusal", "c82363d43023e678af934447deeaaa87c331ce7f0f7a2ac2cf05f5b200df7d7c")):
            self.assertEqual(expected, hashlib.sha256(ast.get_source_segment(source, found[name]).encode()).hexdigest())
        yaml = YAML.read_text(); writer = 'sudo setfacl -m "u:$(id -un):rw" /dev/kvm'
        self.assertEqual(1, yaml.count(writer)); before = yaml.index('android_kvm_timeline.py --phase acl-before'); grant = yaml.index(writer); after = yaml.index('android_kvm_timeline.py --phase acl-after')
        self.assertLess(before, grant); self.assertLess(grant, after)
        self.assertEqual(1, yaml.count('test -r /dev/kvm && test -w /dev/kvm'))
        region = yaml[yaml.index('      - name: Give only this ephemeral'):yaml.index('      - name: Record actual architecture', grant)]
        self.assertEqual(2, region.count('if [[ -n "$ANDROID_BATCH" ]]; then')); self.assertNotIn('|| true', region)
        tree = ast.parse((ROOT / 'scripts/ci/android_kvm_timeline.py').read_text())
        calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        self.assertFalse(calls & {'open', 'os.open', 'ioctl', 'os.chmod', 'os.chown', 'os.setuid',
                                 'os.seteuid', 'os.setgid', 'os.system', 'subprocess.Popen', 'subprocess.run'})
        self.assertNotIn('/proc/', (ROOT / 'scripts/ci/android_kvm_timeline.py').read_text())
        _, batch = functions(BATCH)
        for key in ('passed', 'cleanup_certified', 'stop_reason'):
            for node in ast.walk(batch['run']):
                if isinstance(node, ast.Assign) and any(key in ast.unparse(target) for target in node.targets):
                    self.assertNotIn('kvm_', ast.unparse(node.value))

    def test_diagnostic_probe_and_transport_failures_cannot_replace_original_admission_exception(self):
        _, found = functions(CONTROLLER)
        primary = ValueError('original-owned-admission-refusal')
        events = []
        def admission():
            events.append('admission'); raise primary
        namespace = {'Path': Path, 'lt': SimpleNamespace(allowed_test_focus=lambda *a: True),
                     'validate_api_selection': lambda *a: events.append('selection'), 'require_host': admission,
                     'kvm_timeline': kvm, 'API': 35}
        exec(compile(ast.Module(body=[found['run']], type_ignores=[]), 'android_device_tests.py', 'exec'), namespace)
        output = io.StringIO()
        with self.host(body=RuntimeError('private-unpublished-body')), patch.object(kvm.sys, 'stderr', output):
            with self.assertRaises(ValueError) as caught:
                namespace['run'](Path('.'), 'unused-output', ('calf-permissions/core',), focus='android-permission-demo-contracts')
        self.assertIs(primary, caught.exception); self.assertEqual(['selection', 'admission'], events)
        facts = kvm.child_observations(output.getvalue().encode()); self.assertEqual('retained', facts['status'])
        self.assertTrue(all(row['status'] == 'failed-observation' for row in facts['observations']))
        class Broken:
            def write(self, _): raise OSError('private-unpublished-body')
            def flush(self): raise OSError('private-unpublished-body')
        with self.host(), patch.object(kvm.sys, 'stderr', Broken()):
            with self.assertRaises(ValueError) as caught:
                namespace['run'](Path('.'), 'unused-output', ('calf-permissions/core',), focus='android-permission-demo-contracts')
        self.assertIs(primary, caught.exception)
        output = io.StringIO()
        with self.host(scope={}), patch.object(kvm.sys, 'stderr', output):
            with self.assertRaises(ValueError):
                namespace['run'](Path('.'), 'unused-output', ('calf-permissions/core',), focus='android-permission-demo-contracts')
        self.assertEqual('', output.getvalue())

    def test_child_transport_requires_two_ordered_exact_bounded_typed_rows_and_never_retains_private_output(self):
        def marker(value): return (kvm.MARKER + json.dumps(value, sort_keys=True) + '\n').encode()
        a, b = kvm.empty('admission-before'), kvm.empty('admission-after')
        valid = marker(a) + marker(b)
        result = kvm.child_observations(b'private child transcript must not be returned\n' + valid)
        self.assertEqual({'status': 'retained', 'observations': [a, b]}, result)
        variants = [b'', marker(a), valid + marker(b), marker(b) + marker(a), b'x' + valid, b'x' * 65537,
                    marker({**a, 'private_path': '/private/path'}) + marker(b),
                    marker({**a, 'uid': True}) + marker(b), marker({**a, 'groups': ['private-name']}) + marker(b),
                    marker({**a, 'selected_uid_present': 1}) + marker(b), marker({**a, 'native_success_inferred': True}) + marker(b),
                    marker({**a, 'schema_version': 1.0}) + marker(b), marker({**a, 'status': 'passed'}) + marker(b),
                    marker({**a, 'acl_mask': 6}) + marker(b),
                    valid.replace(b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1', 1),
                    valid.replace(b'"uid": null', b'"uid": NaN', 1), (kvm.MARKER + 'x' * 4097).encode()]
        for index, body in enumerate(variants):
            with self.subTest(index=index):
                result = kvm.child_observations(body)
                self.assertEqual({'status': 'failed-observation', 'observations': None}, result)
                self.assertNotIn('private', json.dumps(result))
        _, found = functions(BATCH)
        namespace = {'Path': Path, 'lt': SimpleNamespace(safe_path=lambda root, relative: root / relative),
                     'evidence': SimpleNamespace(read=lambda path, maximum: valid if maximum == 65536 else b''), 'kvm_timeline': kvm}
        exec(compile(ast.Module(body=[found['child_kvm_observations']], type_ignores=[]), 'android_device_batch.py', 'exec'), namespace)
        self.assertEqual('retained', namespace['child_kvm_observations'](Path('.'), 'owned.log')['status'])
        def unavailable(*_): raise FileNotFoundError('private-unpublished-body')
        namespace['evidence'].read = unavailable
        self.assertEqual({'status': 'failed-observation', 'observations': None}, namespace['child_kvm_observations'](Path('.'), 'owned.log'))

    def test_failed_observations_cannot_hide_execution_cleanup_or_reclamation_failure_in_the_owning_batch(self):
        _, found = functions(BATCH)
        revision = '1' * 40
        routes = [{'profile': profile, 'api_level': 35, 'focus': profile, 'source_suite': {}}
                  for profile in ('android-permission-demo', 'android-storage-api35-normal')]
        selection = {'routes': routes, 'requested_target_executions': 2, 'requested_distinct_methods': 2}
        for cause in ('execution-error', 'native-red', 'cleanup-refused', 'reclamation-refused'):
            with self.subTest(cause=cause), tempfile.TemporaryDirectory(prefix='kvm-timeline-model-') as folder:
                root = Path(folder); executed = []
                def execute(_root, command, log, timeout, reserve):
                    executed.append(command)
                    if cause == 'execution-error': raise OSError('original-execution-error')
                    return {'exit_code': 1 if cause == 'native-red' and len(executed) == 1 else 0, 'elapsed_seconds': 0.01}
                def document(_root, relative):
                    profile = Path(relative).parent.name
                    route = next(row for row in routes if row['profile'] == profile)
                    if relative.endswith('controller.json'):
                        return {'passed': cause != 'native-red' or len(executed) > 1}
                    return {'source_revision': revision, 'api_level': 35, 'serial': 'emulator-5588',
                            'source_suite': route['source_suite'], 'avd_name': 'nativecmpkit-api35-' + hashlib.sha256(profile.encode()).hexdigest()[:12]}
                def require(condition, _message):
                    if not condition: raise ValueError('original-owning-requirement')
                def write(path, value): path.write_text(json.dumps(value))
                lt = SimpleNamespace(safe_path=lambda base, rel: base / rel, snapshot_inputs=lambda _: {'synthetic': '2' * 64},
                    git_revision=lambda _: revision, execute=execute, sha256=lambda _: '3' * 64,
                    utc_now=lambda: '2026-11-01T00:00:00+00:00', write_json=write)
                namespace = {'Path': Path, 'os': os, 'json': json, 're': __import__('re'), 'require': require,
                    'lt': lt, 'plan': lambda *_: selection, 'control_inputs': lambda _: {'synthetic-workflow': '4' * 64},
                    'command': lambda base, relative, route: [relative], 'ROUTE_TIMEOUT_SECONDS': 4200, 'RESERVE_MIB': 8192,
                    'evidence': SimpleNamespace(document=document), 'device': SimpleNamespace(SERIAL='emulator-5588'),
                    'cleanup_certified': lambda *_: cause != 'cleanup-refused',
                    'archive_route': lambda *_: {'actual_cases': [], 'original_XML_execution_count_complete': True},
                    'reclaim_owned_state': lambda *_: {'status': 'failed' if cause == 'reclamation-refused' else 'passed'},
                    'failed_child_origin': lambda *_: {'status': 'unavailable'},
                    'failed_child_host_admission': lambda *_: {'status': 'unavailable'},
                    'child_kvm_observations': lambda *_: {'status': 'failed-observation', 'observations': None},
                    'kvm_timeline': SimpleNamespace(observe=kvm.empty)}
                exec(compile(ast.Module(body=[found['run']], type_ignores=[]), 'android_device_batch.py', 'exec'), namespace)
                result = namespace['run'](root, CI['ANDROID_BATCH'], 'build/ci-verification/synthetic-batch')
                self.assertIs(result['passed'], False); self.assertFalse((root / 'build/ci-verification/.android-device-batch.lock').exists())
                self.assertTrue((root / 'build/ci-verification/synthetic-batch/batch.json').is_file())
                first = result['routes'][0]; phases = [row['phase'] for row in first['kvm_timeline']]
                self.assertEqual(['child-before', 'child-after'], phases[:2]); self.assertTrue(all(row['status'] == 'failed-observation' for row in first['kvm_timeline']))
                if cause in ('execution-error', 'cleanup-refused', 'reclamation-refused'):
                    self.assertEqual(1, len(executed)); self.assertEqual(['android-storage-api35-normal'], result['refused_profiles'])
                else:
                    self.assertEqual(2, len(executed)); self.assertFalse(first['passed']); self.assertEqual([], result['refused_profiles'])
                if cause == 'execution-error': self.assertEqual('OSError', first['adapter_error'])
                if cause == 'cleanup-refused': self.assertFalse(first['cleanup_certified']); self.assertEqual(['child-before', 'child-after'], phases)
                if cause == 'reclamation-refused': self.assertEqual(['child-before', 'child-after', 'reclaim-before', 'reclaim-after'], phases)


if __name__ == '__main__':
    unittest.main()
