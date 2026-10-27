"""Review exact source-defined canonical cache identity; never replay dispatch or artifacts."""
from pathlib import Path
import hashlib,json,re,zipfile,subprocess,datetime as dt,shutil,sys
ROOT=Path('/root/projects/nativeCmpKit');source=Path('/dev/shm/nativecmpkit-ci-ea79ab8c-20261027/40540209480');out=Path(__file__).parent/'review-archive'
review=json.loads((out/'lead-independent-review.json').read_bytes());rev=review['source_revision'];art=review['artifact_id']
sys.path.insert(0,str(ROOT/'scripts/ci'));import dependency_cache_inputs as keys
for name in ('scripts/ci/dependency_cache_inputs.py','scripts/ci/library_tests.py','settings.gradle.kts'):
 assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',rev+':'+name],cwd=ROOT)
with zipfile.ZipFile(source/f'{art}.zip') as z:
 actual=json.loads(z.read('build/ci-runtime/actual.json'));key=json.loads(z.read('build/ci-runtime/library-dependencies.json'));runtime=json.loads(z.read('build/ci-verification/ios-iphone/runtime.json'))
 assert actual['source_revision']==runtime['source_revision']==key['source_revision']==rev
 selected=keys.selection_contract(ROOT,'calf-ui')
 assert key['selected_modules']==selected['modules']==['calf-ui'] and key['selection_cache_key']==selected['cache_key']
 assert key['inputs']==keys.selected_inputs(ROOT,'libraries')
 assert key['dependency_inputs_sha256']==keys.fingerprint('libraries',key['inputs'])==review['independently_recomputed_dependency_fingerprint']
 expected='nativecmpkit-deps-v2-macOS-ARM64-ios-iphone-ios-'+key['selection_cache_key']+'-'+actual['compiler_runtime_fingerprint']+'-'+key['dependency_inputs_sha256']
 log=(source/'job-122316654541-log.log').read_text()
 misses=re.findall(r'Cache not found for input keys: ([^\r\n]+)',log);saved=re.findall(r'Cache saved with key: ([^\r\n]+)',log)
 assert misses==saved==[expected] and not re.search(r'Cache restored (?:from key|successfully)',log)
 assert key['ordinary_dependency_trust_certified'] is False and key['release_readiness_certified'] is False
 row={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':rev,'run_id':40540209480,'expected_cache_key':expected,'cache_observation':'Exact canonical calf-ui key missed then saved. Zero cache-hit or successful-result reuse claim; no cached XML/project outputs/candidate payloads accepted.','runtime_key_bound_to_pre_cache_actual_json':True,'source_defined_selection_schema_verified':True,'dependency_fingerprint_independently_recomputed':key['dependency_inputs_sha256'],'selected_dependency_inputs':key['dependency_input_count'],'original_raw-string-hash_reviewer_failure_preserved':True,'ordinary_dependency_trust_certified':False,'release_readiness_certified':False,'scope':'Workflow cache acceptance only; full dependency locks/checksums/native provenance remain independent release blockers.'}
 (out/'lead-cache-review.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
shutil.copyfile(Path(__file__),out/'cache-review.py');shutil.copyfile(Path(__file__).parent/'cache-review-red001.json',out/'cache-review-red001.json')
(out/'README.md').write_text('# Current genuine UIKit runtime evidence\n\nImmutable ea79ab8cf30132b4b37985f175d00287382ddca8 /run40540209480 passes123 actual iPhone26.5 Native-simulator methods in25 fresh XML, zero failures/errors/skips. All16 mandatory application cases and six required sources are verified against this run\'s own725 Git inputs, exact runtime/plans/commands, Mach-O/application protocol and owned cleanup. All121 prior method identities are retained, with two new callback/remember methods. Primary and cache reviews distinguish simulator completion from physical-device/assistive/sanitizer/consumer/ABI/dependency/legal/release gates. Cache key missed then saved, not a hit. The auxiliary raw-string-hash reviewer mistake is preserved; no production/test guard was weakened. Raw logs, native binaries and packages are not archived or published.\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
target=ROOT/'docs/development/evidence/github-actions/40540209480';assert not target.exists();shutil.copytree(out,target)
for p in out.rglob('*'):
 if p.is_file():assert sha(p)==sha(target/p.relative_to(out))
print(json.dumps({'archive':str(target),'native_methods':review['totals']['passed'],'fresh_XML':review['actual_xml_reports'],'mandatory_methods':review['mandatory_application_methods_passed'],'cache':'miss then save','source_inputs':review['source_input_count'],'release_readiness':False},indent=2))
