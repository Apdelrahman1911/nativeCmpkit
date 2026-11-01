"""Finite mocked capability guards; zero actual SDK/app/native execution."""
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
USAGE = b'Get information about an installed app.\nUsage: simctl appinfo <device> <app bundle identifier>\n'
SHA = 'a' * 40


class AppinfoCapabilityTests(unittest.TestCase):
    def subject(self):
        return importlib.import_module('apple_appinfo_capability')

    def fixture(self, *, help_payload=USAGE, help_exit=0, dirty=False, drift=False):
        module = self.subject()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative in module.SOURCE_INPUTS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture\n')
        developer = root / 'selected-Xcode/Contents/Developer'
        for name in ('simctl', 'xcodebuild'):
            path = developer / 'usr/bin' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'owned synthetic tool')
        commands, git_reads = [], []
        def control(argv, cwd, timeout):
            commands.append(tuple(argv))
            name = next(key for key,value in module.COMMANDS.items() if value == tuple(argv))
            body = b''
            if name == 'source':
                git_reads.append(1)
                body = ((('b'*40) if drift and len(git_reads)>1 else SHA)+'\n').encode()
            if name == 'clean': body = b' M private-fixture\n' if dirty else b''
            if name == 'developer': body = (str(developer)+'\n').encode()
            if name == 'simctl': body = (str(developer/'usr/bin/simctl')+'\n').encode()
            if name == 'xcodebuild': body = (str(developer/'usr/bin/xcodebuild')+'\n').encode()
            if name == 'xcode-version': body = b'Xcode 26.6\nBuild version 17F113\n'
            if name == 'help': return module.Result(help_exit,help_payload,b'PRIVATE_HELP_SENTINEL',None)
            return module.Result(0,body,b'',None)
        original = module.tool_identity
        def identity(path, basename):
            if path == Path('/usr/bin/xcrun'):
                return {'basename':'xcrun','bytes':1,'sha256':'f'*64,'path_sha256':'e'*64,'canonical_path_sha256':'d'*64}
            return original(path,basename)
        return root,control,commands,identity

    def collect_fixture(self, **options):
        module = self.subject()
        root,control,commands,identity = self.fixture(**options)
        with patch.object(module,'host',return_value={'system':'Darwin','architecture':'arm64','python':'3.15.1'}), \
             patch.object(module.shutil,'disk_usage',return_value=(0,0,10*1024**3)), \
             patch.object(module,'tool_identity',side_effect=identity):
            receipt = module.collect(root,control=control)
        return root,receipt,commands

    def test_exact_help_syntax_is_capability_only_not_registration_schema_or_native(self):
        module = self.subject()
        result = module.help_observation(module.Result(0,USAGE,b'',None))
        self.assertTrue(result['capability_available'])
        self.assertEqual('simctl appinfo <device> <app bundle identifier>',result['known_syntax'])
        self.assertFalse(result['appinfo_output_schema_observed'])
        self.assertFalse(result['native_functionality_verified'])

    def test_nonzero_empty_unknown_ambiguous_or_foreign_help_stays_unavailable(self):
        module = self.subject()
        for code,payload in ((1,USAGE),(0,b''),(0,b'unknown'),(0,USAGE+USAGE),(0,b'Usage: simctl listapps <device>\n')):
            with self.subTest(code=code,payload=payload):
                value = module.help_observation(module.Result(code,payload,b'',None))
                self.assertFalse(value['capability_available'])
                self.assertEqual('unavailable',value['status'])

    def test_private_help_messages_and_paths_are_never_retained(self):
        module = self.subject()
        value = module.help_observation(module.Result(0,USAGE+b'PRIVATE_HELP_SENTINEL /private/user/path\n',b'PRIVATE_ERROR',None))
        for token in ('PRIVATE_HELP_SENTINEL','PRIVATE_ERROR','/private/user/path'):
            self.assertNotIn(token,json.dumps(value))

    def test_unbounded_or_invalid_control_shapes_never_establish_help(self):
        module = self.subject()
        for value in (module.Result(True,USAGE,b'',None),module.Result(0,'not bytes',b'',None),
                      module.Result(0,b'x'*(module.MAX_COMMAND_BYTES+1),b'',None),module.Result(0,USAGE,b'','timeout')):
            self.assertFalse(module.help_observation(value)['capability_available'])

    def test_collect_runs_only_fixed_metadata_commands_and_single_help(self):
        module = self.subject()
        root,value,commands = self.collect_fixture()
        self.assertEqual('observed-supported-syntax',value['status'])
        self.assertEqual(1,commands.count(module.COMMANDS['help']))
        self.assertEqual(set(module.COMMANDS.values()),set(commands))
        self.assertTrue(value['owned_private_output_removed'])
        self.assertFalse((root/module.OUTPUT/'private').exists())
        self.assertEqual(['receipt.json'],[p.name for p in (root/module.OUTPUT).iterdir()])
        for text in ('PRIVATE_HELP_SENTINEL','selected-Xcode','/private/user','listapps','install','launch'):
            self.assertNotIn(text,json.dumps(value))
        self.assertFalse(value['subsequent_appinfo_ready'])

    def test_unavailable_help_keeps_nonacceptance_receipt_and_owned_cleanup(self):
        module = self.subject()
        root,value,commands = self.collect_fixture(help_payload=b'unknown command',help_exit=1)
        self.assertEqual('unavailable',value['status'])
        self.assertFalse(value['capability_available'])
        self.assertTrue(value['owned_private_output_removed'])
        self.assertEqual(1,commands.count(module.COMMANDS['help']))
        self.assertTrue((root/module.OUTPUT/'receipt.json').is_file())

    def test_dirty_or_changed_source_never_becomes_supported_capability(self):
        for options in ({'dirty':True},{'drift':True}):
            with self.subTest(options=options):
                _,value,_ = self.collect_fixture(**options)
                self.assertEqual('unavailable',value['status'])
                self.assertFalse(value['capability_available'])

    def test_non_Apple_arch_preflight_uses_no_SDK_commands(self):
        module = self.subject()
        root,control,commands,_ = self.fixture()
        with patch.object(module,'host',return_value={'system':'Darwin','architecture':'x64','python':'3.15.1'}), \
             patch.object(module.shutil,'disk_usage',return_value=(0,0,10*1024**3)):
            value = module.collect(root,control=control)
        self.assertEqual([],commands)
        self.assertFalse(value['capability_available'])

    def test_existing_or_symlink_output_refuses_without_control_calls(self):
        module = self.subject()
        for symlink in (False,True):
            root,control,commands,_ = self.fixture()
            output=root/module.OUTPUT
            output.parent.mkdir(parents=True)
            if symlink: output.symlink_to(root,target_is_directory=True)
            else: output.mkdir()
            with self.assertRaises(module.CapabilityError): module.collect(root,control=control)
            self.assertEqual([],commands)

    def test_tool_identity_requires_actual_named_regular_bounded_stable_file(self):
        module = self.subject()
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'simctl';path.write_bytes(b'owned')
            value=module.tool_identity(path,'simctl')
            self.assertEqual(hashlib.sha256(b'owned').hexdigest(),value['sha256'])
            with self.assertRaises(module.CapabilityError): module.tool_identity(path,'foreign')
            alias=Path(temporary)/'alias';alias.symlink_to(path)
            with self.assertRaises(module.CapabilityError): module.tool_identity(alias,'alias')
            with patch.object(module,'MAX_TOOL_BYTES',2),self.assertRaises(module.CapabilityError): module.tool_identity(path,'simctl')

    def test_control_allowlist_refuses_inventory_mutation_and_other_help(self):
        module = self.subject()
        with patch.object(module.subprocess,'Popen',side_effect=AssertionError('must not execute')):
            for argv in (('/usr/bin/xcrun','simctl','listapps'),('/usr/bin/xcrun','simctl','boot','device'),
                         ('/usr/bin/xcrun','simctl','appinfo','device','bundle'),('/usr/bin/xcrun','simctl','help','listapps')):
                with self.assertRaises(module.CapabilityError): module.control(argv,ROOT,1)

    def test_owned_synthetic_output_capture_is_actually_byte_bounded(self):
        module = self.subject()
        with patch.object(module,'MAX_COMMAND_BYTES',1024):
            value=module.capture((sys.executable,'-c','import sys;sys.stdout.write("x"*8192)'),ROOT,3)
        self.assertEqual('output-bound',value.stop_reason)
        self.assertLessEqual(len(value.stdout)+len(value.stderr),1024)

    def test_owned_synthetic_timeout_does_not_target_any_app_or_other_process(self):
        module = self.subject()
        value=module.capture((sys.executable,'-c','import time;time.sleep(2)'),ROOT,.05)
        self.assertEqual('timeout',value.stop_reason)

    def test_four_source_inputs_and_exact_tool_identities_are_correlated(self):
        module = self.subject()
        _,value,_ = self.collect_fixture()
        self.assertEqual(set(module.SOURCE_INPUTS),set(value['inputs_before']))
        self.assertEqual(value['inputs_before'],value['inputs_after'])
        self.assertEqual({'xcrun','simctl','xcodebuild'},set(value['tool_identities']))
        self.assertEqual({'version':'26.6','build':'17F113'},value['xcode'])
        self.assertEqual(SHA,value['source_revision_after'])

    def test_private_output_identity_change_refuses_deletion_and_capability_success(self):
        module = self.subject()
        root,original,commands,identity = self.fixture()
        calls=[]
        def control(argv,cwd,timeout):
            result=original(argv,cwd,timeout)
            if tuple(argv)==module.COMMANDS['clean']:
                calls.append(1)
                if len(calls)>1:
                    (root/module.OUTPUT/'private/01-source.stdout').write_bytes(b'PRIVATE_CHANGED_PAYLOAD')
            return result
        with patch.object(module,'host',return_value={'system':'Darwin','architecture':'arm64','python':'3.15.1'}), \
             patch.object(module.shutil,'disk_usage',return_value=(0,0,10*1024**3)), \
             patch.object(module,'tool_identity',side_effect=identity):
            value=module.collect(root,control=control)
        self.assertEqual('unavailable',value['status'])
        self.assertFalse(value['owned_private_output_removed'])
        self.assertFalse(value['capability_available'])
        self.assertTrue((root/module.OUTPUT/'private/01-source.stdout').exists())
        self.assertNotIn('PRIVATE_CHANGED_PAYLOAD',json.dumps(value))

    def test_tool_identity_failure_stops_before_help_with_no_alternate_command(self):
        module = self.subject()
        root,control,commands,_ = self.fixture()
        with patch.object(module,'host',return_value={'system':'Darwin','architecture':'arm64','python':'3.15.1'}), \
             patch.object(module.shutil,'disk_usage',return_value=(0,0,10*1024**3)), \
             patch.object(module,'tool_identity',side_effect=module.CapabilityError('synthetic_identity_guard')):
            value=module.collect(root,control=control)
        self.assertFalse(value['capability_available'])
        self.assertNotIn(module.COMMANDS['help'],commands)
        self.assertTrue(value['owned_private_output_removed'])

    def test_disk_reserve_refusal_starts_no_metadata_or_help_command(self):
        module = self.subject()
        root,control,commands,_ = self.fixture()
        with patch.object(module,'host',return_value={'system':'Darwin','architecture':'arm64','python':'3.15.1'}), \
             patch.object(module.shutil,'disk_usage',return_value=(0,0,8*1024**3)):
            value=module.collect(root,control=control)
        self.assertEqual([],commands)
        self.assertEqual('eight_GiB_reserve_required',value['error_guard'])
        self.assertTrue(value['owned_private_output_removed'])

    def test_capability_profile_has_no_library_preflight_or_removed_full_slots(self):
        import workflow_matrix
        with patch.object(workflow_matrix.subprocess,'run',side_effect=AssertionError('must not execute')):
            self.assertEqual({'include':[]},workflow_matrix.matrix('ios-appinfo-capability'))
            self.assertEqual([],workflow_matrix.preflight_plans('ios-appinfo-capability')['slots'])
        self.assertNotIn('ios-appinfo-capability',workflow_matrix.MODULE_SUBSETS)
        self.assertEqual(11,len(workflow_matrix.matrix('all')['include']))

    def test_capability_workflow_is_fast_exact_guarded_read_only_without_build_setup(self):
        text=(ROOT/'.github/workflows/gradle.yml').read_text()
        job=text.split('\n  apple-appinfo-capability:\n',1)[1].split('\n  sample-platforms:\n',1)[0]
        for token in ("inputs.profile == 'ios-appinfo-capability'",'needs: tooling','runs-on: macos-26','timeout-minutes: 5',
                      "github.ref == 'refs/heads/development/preview-hardening'",'persist-credentials: false',
                      'python3 -B scripts/ci/apple_appinfo_capability.py','build/ci-verification/apple-appinfo-capability/receipt.json'):
            self.assertIn(token,job)
        for token in ('permissions:','setup-java','setup-android','rustup','library_tests.py','gradlew','simctl boot','listapps',
                      'xctrace','uses: actions/cache','*.log','private/','release','deploy'):
            self.assertNotIn(token,job)
        self.assertIn('permissions:\n  contents: read',text)
        self.assertIn('cancel-in-progress: false',text)

    def test_profile_choice_and_source_dictionary_remain_exact(self):
        import workflow_matrix
        text=(ROOT/'.github/workflows/gradle.yml').read_text()
        choices=re.search(r'options: \[([^\n]+)\]',text).group(1)
        self.assertEqual(set(workflow_matrix.PROFILES),{value.strip() for value in choices.split(',')})


    def test_exited_leader_pipe_descendant_is_stopped_without_foreign_group_signals(self):
        import os
        import time
        module = self.subject()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child_ready, leader_ready, survived = (root/name for name in ('child.json','leader.json','survived'))
            child_script = (
                'import json,os,pathlib,signal,sys,time;'
                'signal.signal(signal.SIGTERM,signal.SIG_IGN);'
                'pathlib.Path(sys.argv[1]).write_text(json.dumps({"pid":os.getpid(),"group":os.getpgrp(),"session":os.getsid(0)}));'
                'time.sleep(.65);pathlib.Path(sys.argv[2]).write_text("owned descendant survived capture timeout")'
            )
            leader_script = (
                'import json,os,pathlib,subprocess,sys,time\n'
                'child=subprocess.Popen([sys.executable,"-B","-c",'+repr(child_script)+',sys.argv[1],sys.argv[3]],stdin=subprocess.DEVNULL)\n'
                'deadline=time.monotonic()+1\n'
                'while not pathlib.Path(sys.argv[1]).exists() and time.monotonic()<deadline: time.sleep(.005)\n'
                'pathlib.Path(sys.argv[2]).write_text(json.dumps({"pid":os.getpid(),"child":child.pid,"group":os.getpgrp(),"session":os.getsid(0)}))\n'
                'print("OWNED_LEADER_EXITED",flush=True)\n'
            )
            value = module.capture((sys.executable,'-B','-c',leader_script,str(child_ready),str(leader_ready),str(survived)),root,.25)
            self.assertEqual('timeout',value.stop_reason)
            self.assertEqual(0,value.exit_code,'The direct owned leader must have exited successfully before pipe timeout.')
            self.assertIn(b'OWNED_LEADER_EXITED',value.stdout)
            leader,child = json.loads(leader_ready.read_text()),json.loads(child_ready.read_text())
            self.assertEqual(leader['child'],child['pid'])
            self.assertEqual(leader['pid'],leader['group'])
            self.assertEqual(leader['pid'],leader['session'])
            self.assertEqual(leader['pid'],child['group'])
            self.assertEqual(leader['pid'],child['session'])
            self.assertNotEqual(os.getpgrp(),child['group'])
            # The failing old child exits naturally within this wait; never target an unknown PID/group.
            time.sleep(.8)
            self.assertFalse(survived.exists(),'Exited leader left its owned pipe-descendant alive beyond the capture timeout.')
        fake_pid=max(os.getpid(),os.getpgrp(),os.getsid(0))+1_000_000
        class ForeignSession:
            pid,returncode = fake_pid,None
        with patch.object(module.os,'getpgid',return_value=54321), \
             patch.object(module.os,'getsid',return_value=54321), \
             patch.object(module.os,'killpg') as signal_group:
            with self.assertRaises(module.CapabilityError): module.stop(ForeignSession())
            signal_group.assert_not_called()
        class AlreadyReaped:
            pid,returncode = fake_pid,0
        with patch.object(module.os,'killpg') as signal_group:
            with self.assertRaises(module.CapabilityError): module.stop(AlreadyReaped())
            self.assertEqual([(fake_pid,0)],[(call.args[0],call.args[1]) for call in signal_group.call_args_list])


class AppinfoControlRecoveryTests(unittest.TestCase):
    """New mocked transport guards only; no SDK or real child execution."""

    def subject(self):
        return importlib.import_module('apple_appinfo_capability')

    class Process:
        pid = 7311
        def __init__(self, code=0, unknown=False):
            self.returncode = None
            self.code, self.unknown, self.waits = code, unknown, []
            class Pipe:
                closed = False
                def fileno(self): return 42
                def close(self): self.closed = True
            self.stdout, self.stderr = Pipe(), Pipe()
        def wait(self, timeout):
            self.waits.append(timeout)
            if self.unknown:
                raise subprocess.TimeoutExpired(('owned-fixed-control',), timeout)
            self.returncode = self.code
            return self.code
        def poll(self): raise AssertionError('must not reap before final owned signal')

    def owner(self, process, *, lookup=None, group_present=False, vanish_on_signal=False):
        from contextlib import ExitStack
        module, events = self.subject(), []
        def getpgid(pid):
            events.append(('owner', pid))
            if lookup is not None: return lookup(pid)
            return process.pid
        def killpg(pid, value):
            events.append(('group-read' if value == 0 else 'signal', pid, value))
            if value == 0:
                if not group_present: raise ProcessLookupError()
            elif vanish_on_signal:
                raise ProcessLookupError()
        stack = ExitStack()
        stack.enter_context(patch.object(module.os, 'getpgrp', return_value=900))
        stack.enter_context(patch.object(module.os, 'getsid', side_effect=lambda pid: 901 if pid == 0 else process.pid))
        stack.enter_context(patch.object(module.os, 'getpgid', side_effect=getpgid))
        stack.enter_context(patch.object(module.os, 'killpg', side_effect=killpg))
        stack.enter_context(patch.object(module.time, 'sleep'))
        return stack, events

    def disappeared(self, pid):
        raise ProcessLookupError()

    def test_disappeared_owner_requires_owned_exit_and_absent_group_without_signal(self):
        module, process = self.subject(), self.Process()
        stack, events = self.owner(process, lookup=self.disappeared)
        with stack: module.stop(process)
        self.assertEqual([2], process.waits)
        self.assertEqual(0, process.returncode)
        self.assertEqual([('owner', process.pid), ('group-read', process.pid, 0)], events)

    def test_disappeared_owner_unknown_exit_keeps_original_refusal_without_signal(self):
        module, process = self.subject(), self.Process(unknown=True)
        stack, events = self.owner(process, lookup=self.disappeared)
        with stack, self.assertRaisesRegex(module.CapabilityError, '^owned_control_leader_unavailable$'):
            module.stop(process)
        self.assertEqual([2], process.waits)
        self.assertIsNone(process.returncode)
        self.assertEqual([('owner', process.pid)], events)

    def test_disappeared_owner_live_or_reused_group_refuses_after_wait_without_signal(self):
        module, process = self.subject(), self.Process()
        stack, events = self.owner(process, lookup=self.disappeared, group_present=True)
        with stack, self.assertRaisesRegex(module.CapabilityError, '^reaped_control_group_still_present$'):
            module.stop(process)
        self.assertEqual([2], process.waits)
        self.assertFalse(any(event[0] == 'signal' for event in events))

    def test_owner_disappearing_after_TERM_never_gets_KILL_after_owned_wait(self):
        module, process, probes = self.subject(), self.Process(code=-15), []
        def lookup(pid):
            probes.append(pid)
            if len(probes) > 1: raise ProcessLookupError()
            return pid
        stack, events = self.owner(process, lookup=lookup)
        with stack: module.stop(process)
        self.assertEqual([2], process.waits)
        self.assertEqual(-15, process.returncode)
        self.assertEqual([('signal', process.pid, module.signal.SIGTERM)],
                         [event for event in events if event[0] == 'signal'])
        self.assertEqual(('group-read', process.pid, 0), events[-1])

    def test_group_vanishing_between_identity_and_signal_needs_owned_wait_not_fallback_signal(self):
        module, process = self.subject(), self.Process()
        stack, events = self.owner(process, vanish_on_signal=True)
        with stack: module.stop(process)
        self.assertEqual([2], process.waits)
        self.assertEqual([('signal', process.pid, module.signal.SIGTERM)],
                         [event for event in events if event[0] == 'signal'])
        self.assertEqual(('group-read', process.pid, 0), events[-1])

    def test_changed_session_and_owner_permission_denial_keep_no_wait_no_signal_refusals(self):
        module = self.subject()
        def denied(pid): raise PermissionError('PRIVATE_OWNER_ERROR')
        for lookup, kind in ((lambda pid: 123, module.CapabilityError), (denied, PermissionError)):
            with self.subTest(category=kind.__name__):
                process = self.Process()
                stack, events = self.owner(process, lookup=lookup)
                with stack, self.assertRaises(kind): module.stop(process)
                self.assertEqual([], process.waits)
                self.assertFalse(any(event[0] == 'signal' for event in events))

    def captured(self, payload, *, stop_error=None, limit=None, real_stop=False):
        from contextlib import ExitStack
        from types import SimpleNamespace
        module, process = self.subject(), self.Process()
        class Selector:
            def __init__(self): self.members = {}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def register(self, pipe, event, name):
                self.members[name] = SimpleNamespace(fileobj=pipe, data=name)
            def get_map(self): return self.members
            def select(self, timeout): return [(self.members['stdout'], 1)]
            def unregister(self, pipe):
                for name, key in list(self.members.items()):
                    if key.fileobj is pipe: del self.members[name]
        stack = ExitStack()
        popen = stack.enter_context(patch.object(module.subprocess, 'Popen', return_value=process))
        stack.enter_context(patch.object(module.selectors, 'DefaultSelector', return_value=Selector()))
        stack.enter_context(patch.object(module.os, 'read', return_value=payload))
        stack.enter_context(patch.object(module.time, 'monotonic', side_effect=[0, 0, 0, 2]))
        if limit is not None: stack.enter_context(patch.object(module, 'MAX_COMMAND_BYTES', limit))
        stop = None
        events = []
        if real_stop:
            owned, events = self.owner(process, lookup=self.disappeared)
            stack.enter_context(owned)
        else:
            stop = stack.enter_context(patch.object(module, 'stop', side_effect=stop_error))
        result, error = None, None
        with stack:
            try: result = module.capture(module.COMMANDS['help'], ROOT, 1)
            except module.CapabilityError as refusal: error = refusal
        self.assertEqual(module.COMMANDS['help'], popen.call_args.args[0])
        self.assertTrue(popen.call_args.kwargs['start_new_session'])
        self.assertTrue(process.stdout.closed and process.stderr.closed)
        return result, error, process, stop, events

    def test_timeout_refusal_preserves_partial_bytes_unknown_exit_and_exactly_one_stop(self):
        module = self.subject()
        payload = b'PRIVATE_CAPTURE_SENTINEL'
        result, error, process, stop, _ = self.captured(
            payload, stop_error=module.CapabilityError('owned_control_leader_unavailable'))
        self.assertIsNone(result)
        self.assertEqual(1, stop.call_count)
        self.assertEqual('owned_control_leader_unavailable', str(error))
        partial = getattr(error, 'control_result', None)
        self.assertIsInstance(partial, module.Result)
        self.assertIsNone(partial.exit_code)
        self.assertEqual(payload, partial.stdout)
        self.assertEqual('timeout', partial.stop_reason)
        self.assertFalse(module.valid(partial))

    def test_output_bound_refusal_preserves_only_bounded_prefix_and_one_stop(self):
        module = self.subject()
        result, error, _, stop, _ = self.captured(
            b'x' * 64, limit=32, stop_error=module.CapabilityError('owned_control_leader_unavailable'))
        self.assertIsNone(result)
        self.assertEqual(1, stop.call_count)
        partial = getattr(error, 'control_result', None)
        self.assertIsInstance(partial, module.Result)
        self.assertEqual(b'x' * 32, partial.stdout)
        self.assertEqual('output-bound', partial.stop_reason)
        self.assertFalse(module.help_observation(partial)['capability_available'])

    def test_timeout_with_observed_disappeared_child_still_never_becomes_help_acceptance(self):
        module = self.subject()
        result, error, process, _, events = self.captured(USAGE, real_stop=True)
        self.assertIsNone(error)
        self.assertEqual(0, result.exit_code)
        self.assertEqual('timeout', result.stop_reason)
        self.assertEqual([2], process.waits)
        self.assertFalse(any(event[0] == 'signal' for event in events))
        self.assertFalse(module.help_observation(result)['capability_available'])

    def partial_collect(self, partial):
        module = self.subject()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name in module.SOURCE_INPUTS:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'FIXED_SYNTHETIC_SOURCE\n')
        developer = root / 'fixed-sdk/Developer'
        developer.mkdir(parents=True)
        calls = []
        failure = module.CapabilityError('owned_control_leader_unavailable')
        if partial is not None: failure.control_result = partial
        def control(argv, cwd, timeout):
            calls.append(tuple(argv))
            name = next(key for key, value in module.COMMANDS.items() if value == tuple(argv))
            values = {'source': (SHA + '\n').encode(), 'clean': b'',
                      'developer': (str(developer) + '\n').encode(),
                      'simctl': (str(developer / 'usr/bin/simctl') + '\n').encode(),
                      'xcodebuild': (str(developer / 'usr/bin/xcodebuild') + '\n').encode(),
                      'xcode-version': b'Xcode 26.6\nBuild version 17F113\n'}
            if name == 'help': raise failure
            return module.Result(0, values[name], b'', None)
        def identity(path, basename):
            return {'basename': basename, 'bytes': 1, 'sha256': 'f' * 64,
                    'path_sha256': 'e' * 64, 'canonical_path_sha256': 'd' * 64}
        with patch.object(module, 'host', return_value={'system': 'Darwin', 'architecture': 'arm64', 'python': '3.15.1'}), \
             patch.object(module.shutil, 'disk_usage', return_value=(0, 0, 10 * 1024**3)), \
             patch.object(module, 'tool_identity', side_effect=identity):
            value = module.collect(root, control=control)
        self.assertEqual([module.COMMANDS[name] for name in
                          ('source', 'clean', 'developer', 'simctl', 'xcodebuild', 'xcode-version', 'help')], calls)
        self.assertEqual(1, calls.count(module.COMMANDS['help']))
        self.assertEqual('unavailable', value['status'])
        self.assertFalse(value['capability_available'])
        self.assertFalse(value['subsequent_appinfo_ready'])
        self.assertFalse(value['appinfo_output_schema_observed'])
        self.assertTrue(value['owned_private_output_removed'])
        self.assertFalse((root / module.OUTPUT / 'private').exists())
        self.assertNotIn('PRIVATE_CAPTURE_SENTINEL', json.dumps(value))
        self.assertNotIn(str(root), json.dumps(value))
        self.assertNotIn('help', value)
        self.assertNotIn('inputs_after', value)
        return value

    def test_unknown_exit_partial_help_is_recorded_once_with_hashes_and_original_refusal(self):
        module = self.subject()
        payload = USAGE + b'PRIVATE_CAPTURE_SENTINEL'
        value = self.partial_collect(module.Result(None, payload, b'', 'timeout'))
        self.assertEqual('owned_control_leader_unavailable', value['error_guard'])
        self.assertEqual(7, len(value['commands']))
        help_value = value['commands'][-1]
        self.assertEqual('help', help_value['name'])
        self.assertIsNone(help_value['exit_code'])
        self.assertEqual('timeout', help_value['stop_reason'])
        self.assertEqual(len(payload), help_value['stdout_bytes'])
        self.assertEqual(hashlib.sha256(payload).hexdigest(), help_value['stdout_sha256'])
        self.assertTrue(help_value['owned_control_cleanup_refused'])
        self.assertEqual('owned_control_leader_unavailable', help_value['control_error_guard'])
        self.assertEqual(sum(v['stdout_bytes'] + v['stderr_bytes'] for v in value['commands']),
                         value['private_bytes_captured'])

    def test_known_zero_exit_partial_help_with_cleanup_refusal_is_recorded_but_not_green(self):
        module = self.subject()
        value = self.partial_collect(module.Result(0, USAGE, b'PRIVATE_CAPTURE_SENTINEL', 'owned-control-refusal'))
        self.assertEqual('owned_control_leader_unavailable', value['error_guard'])
        self.assertEqual(7, len(value['commands']))
        self.assertEqual(0, value['commands'][-1]['exit_code'])
        self.assertTrue(value['commands'][-1]['owned_control_cleanup_refused'])

    def test_control_refusal_without_partial_result_never_fabricates_help_completion(self):
        value = self.partial_collect(None)
        self.assertEqual('owned_control_leader_unavailable', value['error_guard'])
        self.assertEqual(6, len(value['commands']))
        self.assertFalse(any(v['name'] == 'help' for v in value['commands']))

    def test_invalid_partial_exit_stop_reason_or_byte_bound_refuses_before_snapshot_publication(self):
        module = self.subject()
        cases = [(module.Result(True, USAGE, b'', 'timeout'), 'control_result_shape'),
                 (module.Result(None, b'x' * (module.MAX_COMMAND_BYTES + 1), b'', 'timeout'), 'control_output_bound'),
                 (module.Result(0, USAGE, b'', None), 'partial_control_stop_reason_required')]
        for partial, guard in cases:
            with self.subTest(guard=guard):
                value = self.partial_collect(partial)
                self.assertEqual(guard, value['error_guard'])
                self.assertEqual(6, len(value['commands']))

    def test_transport_recovery_keeps_original_four_Result_fields_fixed_commands_and_bounds(self):
        module = self.subject()
        self.assertEqual(['exit_code', 'stdout', 'stderr', 'stop_reason'], list(module.Result.__dataclass_fields__))
        self.assertEqual({'source', 'clean', 'developer', 'simctl', 'xcodebuild', 'xcode-version', 'help'}, set(module.COMMANDS))
        self.assertEqual(('/usr/bin/xcrun', 'simctl', 'help', 'appinfo'), module.COMMANDS['help'])
        self.assertEqual(4, len(module.SOURCE_INPUTS))
        self.assertEqual((128 * 1024, 512 * 1024, 15, 90),
                         (module.MAX_COMMAND_BYTES, module.MAX_TOTAL_BYTES, module.COMMAND_SECONDS, module.TOTAL_SECONDS))


class AppinfoHelpDiagnosticTests(unittest.TestCase):
    """New diagnostic-only contracts; no SDK, app, build or real control call."""
    def setUp(self):
        self.module = importlib.import_module('apple_appinfo_capability')
        blocked = patch.object(self.module.subprocess, 'Popen',
                               side_effect=AssertionError('real control is forbidden in these models'))
        blocked.start()
        self.addCleanup(blocked.stop)

    def observe(self, payload, *, stderr=False):
        module = self.module
        return module.help_observation(module.Result(0, b'' if stderr else payload,
                                                     payload if stderr else b'', None))

    def assert_unavailable(self, value):
        self.assertFalse(value['capability_available'])
        self.assertEqual('unavailable', value['status'])
        self.assertIsNone(value['known_syntax'])
        self.assertFalse(value['appinfo_output_schema_observed'])
        self.assertFalse(value['native_functionality_verified'])

    def test_exact_supported_help_keeps_acceptance_and_only_finite_diagnostics(self):
        for stderr in (False, True):
            with self.subTest(stderr=stderr):
                value = self.observe(USAGE + b'PRIVATE_HELP_DIAGNOSTIC_SENTINEL /private/account/path\n', stderr=stderr)
                self.assertTrue(value['capability_available'])
                self.assertIsNone(value['refusal_reason'])
                self.assertEqual(1, value['usage_line_count'])
                self.assertEqual(1, value['strict_usage_line_count'])
                self.assertEqual('exact', value['usage_prefix_observation'])
                self.assertEqual(value['known_syntax'], value['usage_template_observation'])
                self.assertFalse(value['usage_template_normalized'])
                self.assertFalse(value['usage_lines_truncated'])
                self.assertRegex(value['usage_lines_sha256'], r'^[0-9a-f]{64}$')
                for token in ('PRIVATE_HELP_DIAGNOSTIC_SENTINEL', '/private/account/path'):
                    self.assertNotIn(token, json.dumps(value))

    def test_complete_unknown_and_invalid_UTF8_have_distinct_fixed_refusals(self):
        cases = ((b'unknown help\n', 'missing-exact-usage-line', 0),
                 (b'Usage: simctl appinfo <device> <unknown>\n', 'unrecognized-exact-usage-syntax', 1),
                 (b'Usage: simctl appinfo <device> <unknown>\xff\n', 'utf8-decoding-refused', None))
        for payload, reason, count in cases:
            with self.subTest(reason=reason):
                value = self.observe(payload, stderr=True)
                self.assert_unavailable(value)
                self.assertEqual(reason, value['refusal_reason'])
                self.assertEqual(count, value['strict_usage_line_count'])
                self.assertIsNone(value['usage_template_observation'])
                self.assertFalse(value['raw_help_or_paths_uploaded'])

    def test_diagnostic_case_indent_and_space_normalization_never_widens_acceptance(self):
        syntax = 'simctl appinfo <device> <app bundle identifier>'
        cases = (((' \tUsage: ' + syntax + '\n').encode(), 'indented', 'missing-exact-usage-line'),
                 (('usage: ' + syntax + '\n').encode(), 'other-case', 'missing-exact-usage-line'),
                 (('Usage: ' + syntax + ' \t\n').encode(), 'exact', 'unrecognized-exact-usage-syntax'),
                 (b'Usage: SIMCTL\tappinfo <device> <app  bundle identifier>\n', 'exact', 'unrecognized-exact-usage-syntax'))
        for payload, prefix, reason in cases:
            with self.subTest(prefix=prefix, payload=payload):
                value = self.observe(payload)
                self.assert_unavailable(value)
                self.assertEqual(reason, value['refusal_reason'])
                self.assertEqual(prefix, value['usage_prefix_observation'])
                self.assertEqual(1, value['usage_line_count'])
                self.assertEqual(syntax, value['usage_template_observation'])

    def test_allowlisted_alternate_templates_are_observations_without_support(self):
        templates = ('simctl appinfo <device> <app>',
                     'simctl appinfo <device> <bundle identifier>',
                     'appinfo <device> <app bundle identifier>')
        for template in templates:
            with self.subTest(template=template):
                value = self.observe(('Usage: ' + template + '\n').encode())
                self.assert_unavailable(value)
                self.assertEqual('unrecognized-exact-usage-syntax', value['refusal_reason'])
                self.assertEqual(template, value['usage_template_observation'])
                self.assertEqual(1, value['strict_usage_line_count'])

    def test_arbitrary_usage_text_paths_and_tokens_never_escape_diagnostics(self):
        payload = b'Usage: /private/account/SECRET_PATH PRIVATE_USAGE_TOKEN <PRIVATE_ARG>\n'
        value = self.observe(payload)
        self.assert_unavailable(value)
        self.assertEqual('unrecognized-exact-usage-syntax', value['refusal_reason'])
        self.assertIsNone(value['usage_template_observation'])
        self.assertRegex(value['usage_lines_sha256'], r'^[0-9a-f]{64}$')
        for token in ('/private/account/SECRET_PATH', 'PRIVATE_USAGE_TOKEN', 'PRIVATE_ARG'):
            self.assertNotIn(token, json.dumps(value))
        self.assertNotIn('usage_lines', value)
        self.assertNotIn('stdout', value)
        self.assertNotIn('stderr', value)

    def test_usage_line_and_byte_sampling_bounds_keep_ambiguous_or_long_help_unavailable(self):
        module = self.module
        many = USAGE * (module.MAX_HELP_USAGE_LINES + 5)
        value = self.observe(many)
        self.assert_unavailable(value)
        self.assertEqual('ambiguous-exact-usage-lines', value['refusal_reason'])
        self.assertEqual(module.MAX_HELP_USAGE_LINES, value['usage_line_count'])
        self.assertEqual(module.MAX_HELP_USAGE_LINES, value['strict_usage_line_count'])
        self.assertTrue(value['usage_lines_truncated'])
        self.assertIsNone(value['usage_template_observation'])
        extended = self.observe(many + USAGE)
        self.assertEqual(value['usage_lines_sha256'], extended['usage_lines_sha256'])
        prefix = b'Usage: PRIVATE_LONG_USAGE_' + b'x' * module.MAX_HELP_USAGE_LINE_BYTES
        long_value = self.observe(prefix + b'A\n')
        changed_tail = self.observe(prefix + b'B\n')
        self.assert_unavailable(long_value)
        self.assertTrue(long_value['usage_lines_truncated'])
        self.assertEqual(1, long_value['usage_line_count'])
        self.assertIsNone(long_value['usage_template_observation'])
        self.assertEqual(long_value['usage_lines_sha256'], changed_tail['usage_lines_sha256'])
        self.assertNotIn('PRIVATE_LONG_USAGE_', json.dumps(long_value))

    def test_invalid_nonzero_and_partial_controls_never_parse_or_observe_usage(self):
        module = self.module
        cases = ((module.Result(1, USAGE, b'', None), 'nonzero-help-exit'),
                 (module.Result(True, USAGE, b'', None), 'invalid-control-result'),
                 (module.Result(None, USAGE, b'', 'timeout'), 'invalid-control-result'),
                 (module.Result(0, USAGE, b'', 'timeout'), 'invalid-control-result'),
                 (module.Result(0, USAGE, b'', 'owned-control-refusal'), 'invalid-control-result'),
                 (module.Result(0, b'x' * (module.MAX_COMMAND_BYTES + 1), b'', None), 'invalid-control-result'))
        for result, reason in cases:
            with self.subTest(reason=reason, stop=result.stop_reason):
                value = module.help_observation(result)
                self.assert_unavailable(value)
                self.assertEqual(reason, value['refusal_reason'])
                self.assertIsNone(value['usage_line_count'])
                self.assertIsNone(value['strict_usage_line_count'])
                self.assertIsNone(value['usage_lines_sha256'])
                self.assertIsNone(value['usage_template_observation'])

    def test_collect_keeps_fixed_help_only_calls_nonacceptance_and_owned_private_cleanup(self):
        module = self.module
        with tempfile.TemporaryDirectory(prefix='appinfo-help-diagnostic-') as temporary:
            root = Path(temporary)
            for relative in module.SOURCE_INPUTS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('owned synthetic source\n')
            developer = root / 'private-selected-developer'
            developer.mkdir()
            calls = []
            payload = b'Usage: simctl appinfo <device> <app>\nPRIVATE_COLLECT_SENTINEL /private/account/path\n'
            def fixed_control(argv, cwd, timeout):
                self.assertIn(tuple(argv), module.COMMANDS.values())
                self.assertEqual(root, cwd)
                self.assertGreater(timeout, 0)
                self.assertLessEqual(timeout, 15)
                name = next(k for k,v in module.COMMANDS.items() if v == tuple(argv))
                calls.append(name)
                bodies = {'source':(SHA+'\n').encode(), 'clean':b'',
                          'developer':(str(developer)+'\n').encode(),
                          'simctl':(str(developer/'simctl')+'\n').encode(),
                          'xcodebuild':(str(developer/'xcodebuild')+'\n').encode(),
                          'xcode-version':b'Xcode 26.6\nBuild version 17F113\n', 'help':payload}
                return module.Result(0, b'' if name == 'help' else bodies[name],
                                     bodies[name] if name == 'help' else b'', None)
            def identity(path, name):
                return {'basename':name, 'bytes':1, 'sha256':'a'*64,
                        'path_sha256':'b'*64, 'canonical_path_sha256':'c'*64}
            with patch.object(module, 'host', return_value={'system':'Darwin','architecture':'arm64','python':'model'}), \
                 patch.object(module.shutil, 'disk_usage', return_value=(0,0,10*1024**3)), \
                 patch.object(module, 'tool_identity', side_effect=identity):
                receipt = module.collect(root, control=fixed_control)
            self.assertEqual(['source','clean','developer','simctl','xcodebuild','xcode-version','help','source','clean'], calls)
            self.assertEqual('unavailable', receipt['status'])
            self.assertFalse(receipt['capability_available'])
            self.assert_unavailable(receipt['help'])
            self.assertEqual('unrecognized-exact-usage-syntax', receipt['help']['refusal_reason'])
            self.assertEqual('simctl appinfo <device> <app>', receipt['help']['usage_template_observation'])
            self.assertTrue(receipt['owned_private_output_removed'])
            self.assertFalse((root/module.OUTPUT/'private').exists())
            self.assertEqual(['receipt.json'], sorted(p.name for p in (root/module.OUTPUT).iterdir()))
            for token in ('PRIVATE_COLLECT_SENTINEL', '/private/account/path', 'private-selected-developer'):
                self.assertNotIn(token, json.dumps(receipt))
            self.assertFalse(receipt['subsequent_appinfo_ready'])


if __name__ == '__main__':
    unittest.main()
