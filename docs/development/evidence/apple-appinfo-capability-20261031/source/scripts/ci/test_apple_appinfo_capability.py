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


if __name__ == '__main__':
    unittest.main()
