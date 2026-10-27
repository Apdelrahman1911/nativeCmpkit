"""Read-only review and evidence packaging; no test/native/archive execution."""
from pathlib import Path
import datetime, hashlib, json, re, subprocess, sys, zipfile
ROOT=Path('/root/projects/nativeCmpKit')
OLD=Path('/dev/shm/nativecmpkit-uikit-native-identity-20261027')
NEW=Path(__file__).resolve().parent
OUT=ROOT/'docs/development/evidence/uikit-native-object-identity-20261027'
assert not OUT.exists(); OUT.mkdir()
sys.path.insert(0,str(ROOT/'scripts/ci')); import library_tests as lt
selected={}
def take(prefix,base,exclude=()):
 for p in sorted(base.rglob('*')):
  if p.is_file() and p.name not in exclude:
   name=prefix+'/'+p.relative_to(base).as_posix(); assert name not in selected
   selected[name]=p.read_bytes()
# API dump remains private tmpfs: preserve its hash and only bounded signatures.
take('original',OLD,exclude=('foundation-metadata.log',))
take('corrected',NEW)
old_receipt=json.loads((OLD/'ui/receipt.json').read_bytes()); new_receipt=json.loads((NEW/'ui/receipt.json').read_bytes())
assert old_receipt['execution']['exit_code']==1 and new_receipt['execution']['exit_code']==0
for base,receipt in [(OLD,old_receipt),(NEW,new_receipt)]:
 ui=base/'ui'; before=json.loads((ui/'library-inputs-before.json').read_bytes())
 assert before==json.loads((ui/'library-inputs-after.json').read_bytes())==json.loads((ui/'copied-inputs-before.json').read_bytes())==json.loads((ui/'copied-inputs-after.json').read_bytes())
 assert len(before)==receipt['selected_input_count']==712 and receipt['selected_inputs_sha256']==lt.input_digest(before)
 assert receipt['compile_log_sha256']==lt.sha256(ui/'compile.log')
 assert receipt['driver_sha256']==lt.sha256(base/'driver.py')
 assert receipt['model_init_sha256']==lt.sha256(base/'model.init.gradle')
 assert receipt['source_inputs_held'] and receipt['copied_inputs_held'] and receipt['library_or_device_tests_executed']==0
 assert receipt['host_disk_reserve_maintained_at_completion']
current=json.loads((NEW/'ui/library-inputs-before.json').read_bytes()); assert current==lt.snapshot_inputs(ROOT)
old=json.loads((OLD/'ui/library-inputs-before.json').read_bytes())
changed=[n for n in sorted(set(old)|set(current)) if old.get(n)!=current.get(n)]
assert len(changed)==3
hostdir='calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/'
identity=hostdir+'NativeObjectIdentity.kt'; test=hostdir+'NativeUiApplicationHostTest.kt'
source=(ROOT/identity).read_text().replace('import platform.darwin.NSObject','import platform.Foundation.NSObject')
assert hashlib.sha256(source.encode()).hexdigest()==old[identity]
selected['failed-compile-source/'+identity]=source.encode()
source=(ROOT/test).read_text().replace('import platform.Foundation.NSMutableData\nimport platform.Foundation.dataWithLength\nimport platform.Foundation.isEqualToData\n','import platform.Foundation.NSMutableString\n')
start=source.index('            // Mutable native data owns')
end=source.index('            assertTrue(sameNativeObject(first, first))',start)
source=source[:start]+('            val first = NSMutableString().apply { appendString("Equal values do not prove native ownership") }\n'
 '            val second = NSMutableString().apply { appendString("Equal values do not prove native ownership") }\n'
 '            assertTrue(first.isEqual(second), "The adversarial objects must really have equal native values")\n')+source[end:]
assert hashlib.sha256(source.encode()).hexdigest()==old[test]
selected['failed-compile-source/'+test]=source.encode()
for n in current:
 if n.startswith('scripts/ci/') or n.startswith(hostdir): selected['current-source/'+n]=(ROOT/n).read_bytes()
redlog=(OLD/'ui/compile.log').read_text(); errors=[l for l in redlog.splitlines() if l.startswith('e:')]
assert any("Unresolved reference 'NSObject'" in e for e in errors) and any("Unresolved reference 'NSMutableString'" in e for e in errors)
newlog=(NEW/'ui/compile.log').read_text()
assert ':calf-ui:compileTestKotlinIosSimulatorArm64\n' in newlog and ':calf-ui:compileTestKotlinIosSimulatorArm64 UP-TO-DATE' not in newlog
assert 'NATIVECMPKIT_UIKIT_MODEL' in newlog and 'BUILD SUCCESSFUL' in newlog and not re.search(r'^e:',newlog,re.M)
for prefix in ['red','green','green002']:
 before=json.loads((OLD/(prefix+'-inputs-before.json')).read_bytes()); after=json.loads((OLD/(prefix+'-inputs-after.json')).read_bytes()); assert before==after
ci=json.loads((NEW/'ci/receipt.json').read_bytes()); assert ci['passed'] and ci['python_tooling_methods']==226 and ci['source_inputs_held']
assert json.loads((NEW/'ci/inputs-before.json').read_bytes())==current==json.loads((NEW/'ci/inputs-after.json').read_bytes())
cilog=(NEW/'ci/tests.log').read_text(); assert re.search(r'^Ran 226 tests in ',cilog,re.M) and re.search(r'^OK$',cilog,re.M)
for n in ['nativeObjectIdentityRejectsNullAndEqualButDistinctObjects','generatedBodyRunsOnOwnedWorkerWithActiveAttachedApplication']:
 assert n in (ROOT/test).read_text() and ('internal.NativeUiApplicationHostTest',n) in lt.IOS_APPLICATION_CASES
assert len(lt.IOS_APPLICATION_CASES)==11 and len(lt.IOS_APPLICATION_SOURCES)==3
# Observe actual produced test KLIB components; never put binaries in reports.
output=Path('/dev/shm/nativecmpkit-owned-webview-compile-4qk3k_6c/project/calf-ui/build/classes/kotlin/iosSimulatorArm64/test')
components={p.relative_to(output).as_posix():{'bytes':p.stat().st_size,'sha256':lt.sha256(p)} for p in sorted(output.rglob('*')) if p.is_file()}
assert components and any(n.endswith('/manifest') for n in components)
assert all(lt.sha256(output/n)==v['sha256'] for n,v in components.items())
api=(OLD/'foundation-metadata.log').read_text(); lines=api.splitlines()
sigs=[]
for i,l in enumerate(lines):
 if any(term in l for term in ['public open class platform/Foundation/NSMutableData :','constructor()','platform/Foundation/NSData.isEqualToData','platform/Foundation/NSMutableDataMeta.dataWithLength']):
  if 'constructor()' not in l: sigs.append({'line':i+1,'text':l})
assert len(sigs)==3 and 'platform/Foundation/NSMutableString' not in api
api_record={'configured_kotlin_native':'2.4.20','target':'ios_simulator_arm64','dump_command':['klib','dump-metadata','org.jetbrains.kotlin.native.platform.Foundation'],'dump_sha256':lt.sha256(OLD/'foundation-metadata.log'),'NSMutableString_declaration_present':False,'bounded_signatures':sigs,'scope':'Configured compiler platform metadata API inspection only. Full private generated dump retained in temporary tmpfs; no platform KLIB redistributed and no Apple execution implied.'}
selected['compiler-platform-api-observation.json']=(json.dumps(api_record,indent=2)+'\n').encode()
archive=OUT/'original-observations.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,b in sorted(selected.items()): z.writestr(n,b)
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(set(z.namelist()))==len(selected)
 assert all(z.read(n)==b for n,b in selected.items())
record={'reviewed_utc':lt.utc_now(),'source_revision':lt.git_revision(ROOT),'dirty_source_held_diagnostic':True,'selected_inputs':712,'selected_inputs_sha256':lt.input_digest(current),'failed_compilation':old_receipt['execution'],'compiler_error_observations':errors,'failed_import_source_reconstructed_and_exact_hash_checked':True,'corrected_compilation':new_receipt['execution'],'corrected_compile_task_fresh':True,'unchanged_production_compilation_caches_reused':True,'source_and_copied_inputs_held_per_run':True,'changed_inputs_between_failed_and_corrected_compile':changed,'python_ci_methods':226,'python_red_methods':9,'python_red_failures':4,'python_red_errors':1,'first_full_ci_methods':225,'first_full_ci_failed_methods':3,'first_full_ci_error_events':4,'later_full_ci_passes_overlap_current226':True,'strict_required_application_methods':11,'strict_required_host_sources':3,'current_native_objects_adversary':'Two NSMutableData allocations with equal native contents; reject distinct pointers and any null ownership, and verify actual UIWindow root getter','output_component_hashes_observed_and_rechecked':components,'compiled_output_bytes_not_distributed_or_archived':True,'pointer_API':'Configured public kotlinx.cinterop.Any?.objcPtr(): NativePtr; exact nonnull NSObject pointers, not Kotlin wrapper or native value equality','publication_or_deployment_performed':False,'library_native_device_or_packaged_consumer_methods_executed':0,'issues_closed':0,'release_readiness_certified':False,'archive_members':len(selected),'archive_bytes':archive.stat().st_size,'archive_sha256':lt.sha256(archive),'archive_all_member_bytes_rechecked':True,'review_script_sha256':lt.sha256(Path(__file__)),'scope':'Source-held actual full iOS test KLIB/model compile and Python CI guards; failed imports and earlier synthetic fixtures retained. Original failed driver exit0 is not actual Gradle success. No Apple linking/application/native pointer runtime, presenter/device/ABI/dependency/legal/consumer or release certification. Immutable affected-profile CI remains required.'}
(OUT/'lead-independent-review.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
(OUT/'archive-manifest.json').write_text(json.dumps({'archive_sha256':record['archive_sha256'],'members':{n:hashlib.sha256(b).hexdigest() for n,b in sorted(selected.items())}},indent=2,sort_keys=True)+'\n')
(OUT/'review.py').write_bytes(Path(__file__).read_bytes())
(OUT/'SHA256SUMS').write_text(''.join(f'{lt.sha256(p)}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps({k:record[k] for k in ['failed_compilation','corrected_compilation','python_ci_methods','strict_required_application_methods','archive_members','archive_bytes','archive_sha256']},indent=2))
