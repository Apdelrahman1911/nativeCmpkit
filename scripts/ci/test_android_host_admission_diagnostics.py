"""New synthetic host-refusal diagnostics only; no real KVM/SDK/native commands."""
from __future__ import annotations
import ast
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(os.environ.get('NATIVECMPKIT_HOST_DIAGNOSTIC_SOURCE_ROOT', Path(__file__).resolve().parents[2]))
CONTROLLER = ROOT / 'scripts/ci/android_device_tests.py'
BATCH = ROOT / 'scripts/ci/android_device_batch.py'
PREFIX = 'NATIVECMPKIT_ANDROID_HOST_ADMISSION '
FIELDS = {'schema_version', 'observation_phase', 'character_device', 'read_access', 'write_access', 'native_success_inferred'}
PRIMARY = 'KVM is unavailable; do not silently substitute slow/unverified acceleration'

def functions(path):
    return {node.name: node for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef)}

def strict_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('Duplicate synthetic JSON key')
        result[key] = value
    return result

def require(value, message):
    if not value: raise ValueError(message)

class HostAdmissionDiagnosticTests(unittest.TestCase):
    def host(self, characters, *, paired=False, read=False, write=False, system='Linux', arch='x86_64', stderr=None):
        facts = {'characters': iter(characters), 'character_calls': 0, 'access_masks': []}
        def character():
            facts['character_calls'] += 1
            value = next(facts['characters'])
            if isinstance(value, Exception): raise value
            return value
        def fake_path(value):
            self.assertEqual('/dev/kvm', value)
            return SimpleNamespace(is_char_device=character)
        def access(path, mask):
            self.assertEqual('/dev/kvm', path)
            facts['access_masks'].append(mask)
            value = paired if mask == os.R_OK | os.W_OK else read if mask == os.R_OK else write
            if isinstance(value, Exception): raise value
            return value
        output = io.StringIO() if stderr is None else stderr
        namespace = {'Path': fake_path, 'os': SimpleNamespace(R_OK=os.R_OK, W_OK=os.W_OK, access=access),
                     'platform': SimpleNamespace(system=lambda: system, machine=lambda: arch),
                     'json': json, 'sys': SimpleNamespace(stderr=output)}
        found = functions(CONTROLLER)
        nodes = [found[name] for name in ('record_host_admission_refusal', 'require_host') if name in found]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'android_device_tests.py', 'exec'), namespace)
        return namespace['require_host'], output, facts

    def emitted(self, output):
        rows = output.getvalue().splitlines()
        self.assertEqual(1, len(rows), 'A failed KVM admission must retain one bounded diagnostic marker')
        self.assertTrue(rows[0].startswith(PREFIX)); self.assertLessEqual(len(rows[0].encode()), 512)
        value = json.loads(rows[0][len(PREFIX):], object_pairs_hook=strict_unique)
        self.assertEqual(FIELDS, set(value));self.assertEqual('after-refusal', value['observation_phase'])
        self.assertIs(value['native_success_inferred'], False)
        return value

    def refused(self, run):
        with self.assertRaises(ValueError) as caught: run()
        self.assertEqual(PRIMARY, str(caught.exception))

    def reader(self, body, origin=None, *, missing_log=False, missing_source=False):
        fn = functions(BATCH).get('failed_child_host_admission')
        self.assertIsNotNone(fn, 'The strict bounded host-admission reader must be authored')
        with tempfile.TemporaryDirectory(prefix='host-admission-model-') as td:
            root = Path(td)
            source = root/'scripts/ci/android_device_tests.py';source.parent.mkdir(parents=True)
            if not missing_source:source.write_bytes(CONTROLLER.read_bytes())
            log = root/'failed.log'
            if not missing_log:log.write_bytes(body)
            def safe_path(base, relative):
                path = Path(base)/relative
                if Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink():raise ValueError('Unsafe synthetic evidence path')
                return path
            def read(path, maximum):
                info = path.lstat()
                if path.is_symlink() or not path.is_file() or not 0<info.st_size<=maximum: raise ValueError('Unbounded synthetic evidence')
                return path.read_bytes()
            namespace={'Path':Path,'json':json,'ast':ast,'require':require,
                       'evidence':SimpleNamespace(read=read,unique_object=strict_unique),'lt':SimpleNamespace(safe_path=safe_path)}
            exec(compile(ast.Module(body=[fn],type_ignores=[]),'android_device_batch.py','exec'),namespace)
            if origin is None:
                throw = next(n for n in ast.walk(functions(CONTROLLER)['require_host']) if isinstance(n,ast.Raise) and PRIMARY in ast.unparse(n))
                origin={'status':'retained','origin':{'source':'android_device_tests.py','symbol':'require_host','line':throw.lineno},'raw_log_uploaded':False,'native_success_inferred':False}
            return namespace['failed_child_host_admission'](root,'failed.log',origin)

    @staticmethod
    def facts(**changes):
        value={'schema_version':1,'observation_phase':'after-refusal','character_device':True,'read_access':True,'write_access':False,'native_success_inferred':False}
        value.update(changes);return value

    def marker(self, value):return (PREFIX+json.dumps(value,sort_keys=True)+'\n').encode()

    def test_refused_character_device_retains_read_write_without_changing_primary_gate(self):
        run,output,facts=self.host([False,False],read=False,write=True);self.refused(run)
        emitted=self.emitted(output)
        self.assertIs(emitted['character_device'],False);self.assertIs(emitted['read_access'],False);self.assertIs(emitted['write_access'],True)
        self.assertEqual([os.R_OK,os.W_OK],facts['access_masks'])

    def test_refused_paired_access_preserves_paired_gate_and_separately_observes_read_write(self):
        run,output,facts=self.host([True,True],paired=False,read=True,write=False);self.refused(run)
        emitted=self.emitted(output)
        self.assertIs(emitted['character_device'],True);self.assertIs(emitted['read_access'],True);self.assertIs(emitted['write_access'],False)
        self.assertEqual([os.R_OK|os.W_OK,os.R_OK,os.W_OK],facts['access_masks'])

    def test_allowed_host_is_unchanged_without_extra_probes_or_marker(self):
        run,output,facts=self.host([True],paired=True,read=False,write=False)
        self.assertIsNone(run());self.assertEqual('',output.getvalue())
        self.assertEqual(1,facts['character_calls']);self.assertEqual([os.R_OK|os.W_OK],facts['access_masks'])

    def test_wrong_architecture_refusal_is_unchanged_and_never_probes_KVM(self):
        for system,arch in [('Darwin','x86_64'),('Linux','aarch64')]:
            with self.subTest(system=system,arch=arch):
                run,output,facts=self.host([],system=system,arch=arch)
                with self.assertRaisesRegex(ValueError,'Linux x64 KVM host'):run()
                self.assertEqual('',output.getvalue());self.assertEqual(0,facts['character_calls']);self.assertEqual([],facts['access_masks'])

    def test_unknown_probe_values_stay_null_and_diagnostic_write_errors_do_not_replace_refusal(self):
        run,output,_=self.host([False,OSError('private synthetic body')],read=ValueError('private synthetic body'),write=0)
        self.refused(run);emitted=self.emitted(output)
        for key in ('character_device','read_access','write_access'):self.assertIsNone(emitted[key])
        class BrokenOutput:
            def write(self,_):raise OSError('private synthetic transport body')
            def flush(self):raise OSError('private synthetic transport body')
        run,_,_=self.host([False,False],stderr=BrokenOutput());self.refused(run)

    def test_after_refusal_observations_can_differ_without_native_recovery_or_cause_claim(self):
        run,output,facts=self.host([False,True],paired=True,read=True,write=True);self.refused(run)
        emitted=self.emitted(output)
        for key in ('character_device','read_access','write_access'):self.assertIs(emitted[key],True)
        self.assertEqual('after-refusal',emitted['observation_phase']);self.assertIs(emitted['native_success_inferred'],False)
        self.assertNotIn(os.R_OK|os.W_OK,facts['access_masks'])

    def test_strict_batch_reader_retains_only_bounded_source_bound_boolean_or_null_facts(self):
        for value in [self.facts(),self.facts(character_device=None,read_access=None,write_access=None),self.facts(write_access=True)]:
            with self.subTest(value=value):
                result=self.reader(self.marker(value));self.assertEqual('retained',result['status']);self.assertEqual(value,result['observations'])
                self.assertIs(result['native_success_inferred'],False);self.assertIs(result['raw_log_uploaded'],False)

    def test_batch_marker_foreign_duplicate_wrong_type_nonfinite_or_oversize_inputs_are_refused(self):
        valid=self.marker(self.facts())
        variants=[valid+valid,b'x'+valid,valid.replace(b'"schema_version": 1',b'"schema_version": 1, "schema_version": 1'),
                  self.marker(self.facts(source='/foreign/private/path')),self.marker(self.facts(character_device=1)),
                  self.marker(self.facts(read_access='false')),self.marker(self.facts(native_success_inferred=0)),
                  self.marker(self.facts(schema_version=True)),self.marker(self.facts(schema_version=1.0)),
                  self.marker(self.facts(observation_phase='before-refusal')),
                  valid.replace(b'"read_access": true',b'"read_access": NaN'),b'z'*65537,
                  (PREFIX+' '+('x'*513)).encode(),self.marker([]),self.marker({'character_device':False})]
        for index,body in enumerate(variants):
            with self.subTest(index=index):
                result=self.reader(body);self.assertEqual('refused',result['status']);self.assertNotIn('observations',result)
                self.assertIs(result['native_success_inferred'],False);self.assertIs(result['raw_log_uploaded'],False)
                self.assertNotIn('private',json.dumps(result));self.assertNotIn('/foreign',json.dumps(result))

    def test_batch_marker_requires_exact_KVM_throw_frame_not_another_host_failure(self):
        host=functions(CONTROLLER)['require_host']
        other=next(n for n in ast.walk(host) if isinstance(n,ast.Raise) and 'Linux x64 KVM host' in ast.unparse(n))
        wrong=[{'status':'unavailable'},{'status':'retained','origin':[]},[],
               {'status':'retained','origin':{'source':'android_device_tests.py','symbol':'require_host','line':other.lineno}},
               {'status':'retained','origin':{'source':'foreign.py','symbol':'require_host','line':other.lineno}},
               {'status':'retained','origin':{'source':'android_device_tests.py','symbol':'require_host','line':True}},
               {'status':'retained','origin':{'source':'android_device_tests.py','symbol':'foreign','line':other.lineno}}]
        for origin in wrong:
            with self.subTest(origin=origin):self.assertEqual('refused',self.reader(self.marker(self.facts()),origin)['status'])

    def test_missing_marker_is_unavailable_and_ordinary_failed_child_shape_stays_unchanged(self):
        result=self.reader(b'ordinary unrelated public child refusal\n',{})
        self.assertEqual({'status':'unavailable','raw_log_uploaded':False,'native_success_inferred':False},result)
        self.assertEqual(result,self.reader(b'unread missing log',{},missing_log=True))
        missing_source=self.reader(self.marker(self.facts()),missing_source=True)
        self.assertEqual('refused',missing_source['status']);self.assertEqual('FileNotFoundError',missing_source['diagnostic_error'])
        self.assertNotIn('observations',missing_source)
        source=BATCH.read_text()
        self.assertIn('if admission.get("status") != "unavailable":\n                        item["failed_child_host_admission"] = admission',source)

    def test_nonzero_child_retention_runs_before_controller_read_without_changing_control_flow(self):
        run=functions(BATCH)['run'];calls=[n for n in ast.walk(run) if isinstance(n,ast.Call)]
        diagnostic=next(n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='failed_child_host_admission')
        original=next(n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='failed_child_origin')
        controller=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='document' and '/controller.json' in ast.unparse(n))
        self.assertLess(original.lineno,diagnostic.lineno);self.assertLess(diagnostic.lineno,controller.lineno)
        gated=next(n for n in ast.walk(run) if isinstance(n,ast.If) and any(isinstance(child,ast.Call) and isinstance(child.func,ast.Name) and child.func.id=='failed_child_host_admission' for child in ast.walk(n)) and 'execution.get' in ast.unparse(n.test))
        self.assertEqual("type(execution.get('exit_code')) is int and execution['exit_code'] != 0",ast.unparse(gated.test))
        self.assertIn('controller = evidence.document(root, route_relative + "/controller.json")',BATCH.read_text())

    def test_new_diagnostics_do_not_mutate_permissions_files_or_device_selection(self):
        found=functions(CONTROLLER);self.assertIn('record_host_admission_refusal',found)
        body=ast.unparse(found['record_host_admission_refusal'])
        for forbidden in ('chmod','chown','setuid','setgid','sudo','subprocess','unlink','rmtree','mkdir','open('):self.assertNotIn(forbidden,body)
        original='if not Path("/dev/kvm").is_char_device() or not os.access("/dev/kvm", os.R_OK | os.W_OK):'
        self.assertIn(original,CONTROLLER.read_text());self.assertIn('raise ValueError("'+PRIMARY+'")',CONTROLLER.read_text())
        self.assertIn('except Exception:',ast.unparse(found['require_host']))

if __name__=='__main__':unittest.main()
