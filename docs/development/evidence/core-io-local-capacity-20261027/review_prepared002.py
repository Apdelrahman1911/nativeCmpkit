"""Read-only reconciliation after a late source-scope count error; no Gradle tests."""
from pathlib import Path
import hashlib,json,shutil,stat,subprocess,sys
R=Path('/root/projects/nativeCmpKit');O=Path(__file__).resolve().parent;RESERVE=8192*1024**2
sys.path.insert(0,str(R/'scripts/ci'));import library_tests as lt
assert not (O/'prepared-inputs.json').exists()

fixtures=sorted(p.relative_to(R).as_posix() for p in (R/'tests/consumer/io-desktop').rglob('*') if p.is_file());assert len(fixtures)==5
names=fixtures+['tests/consumer/build.gradle.kts','tests/consumer/settings.gradle.kts','tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt','tests/consumer/verify_artifacts.py','tests/consumer/test_gradle_module_identity.py','tests/consumer/test_core_io_fixture_contract.py']
inputs={n:lt.sha256(R/n) for n in names};assert all(lt.sha256(O/'project'/Path(n).relative_to('tests/consumer/io-desktop'))==inputs[n] for n in fixtures)
for n in ['tests/consumer/build.gradle.kts','tests/consumer/settings.gradle.kts','tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt']:
 assert (R/n).read_bytes()==subprocess.check_output(['git','show','b5a4508a:'+n],cwd=R)
original=json.loads((R/'docs/development/evidence/maven-staging-001/staged-files.json').read_bytes());files={}
for p in sorted((O/'candidate-maven').rglob('*')):
 if p.is_dir():continue
 assert p.is_file() and not p.is_symlink();n=p.relative_to(O/'candidate-maven').as_posix();record={'size_bytes':p.stat().st_size,'sha256':lt.sha256(p)};assert original[n]==record;files[n]=record
selected_coordinates={'nativecmpkit-core','nativecmpkit-core-desktop','nativecmpkit-io','nativecmpkit-io-desktop'}
expected={n for n in original if Path(n).parts[-3] in selected_coordinates and Path(n).parts[-2]=='0.1.0-preview.1'}
assert set(files)==expected and len({Path(n).parts[-3] for n in files})==4
(O/'first-readonly-review-count-failure.json').write_text(json.dumps({'recorded_utc':lt.utc_now(),'original_driver':'review_prepared.py','original_driver_sha256':lt.sha256(O/'review_prepared.py'),'observed_exit_code':1,'location':'review_prepared.py:17','cause':'Caller guessed120 selected files instead of deriving the complete selected-coordinate file set from the original1425-file staging manifest.','actual_selected_files':len(files),'selected_original_manifest_file_set_exactly_preserved':True,'consumer_or_Gradle_methods_executed':0,'observation_source':'Original exec tool output; no separate first-review log captured.','new_review_uses_exact_manifest_file_set_not_guessed_count':True},indent=2)+'\n')
copy=O/'readonly-dependencies/modules-2';cache=Path('/root/.gradle/caches/modules-2');count=0;size=0;digest=hashlib.sha256()
for p in sorted(copy.rglob('*')):
 assert not p.is_symlink()
 if p.is_dir():assert p.stat().st_mode & 0o222 == 0;continue
 assert p.is_file() and p.stat().st_mode & 0o222 == 0 and not p.name.endswith('.lock') and p.name!='gc.properties'
 n=p.relative_to(copy).as_posix();h=lt.sha256(p);original_path=cache/n;assert original_path.is_file() and not original_path.is_symlink() and lt.sha256(original_path)==h
 count+=1;size+=p.stat().st_size;digest.update(f'{h}  {n}\n'.encode())
old=json.loads((R/'docs/development/evidence/maven-staging-001/inputs-before.json').read_bytes())
shared=sorted(n for n in old if (n in ['calf-core/build.gradle.kts','calf-io/build.gradle.kts','build.gradle.kts','settings.gradle.kts','gradle.properties'] or n.startswith(('convention-plugins/','gradle/')) or (n.startswith(('calf-core/src/','calf-io/src/')) and not Path(n).parts[2].endswith('Test'))))
assert len(shared)==65 and all(lt.sha256(R/n)==old[n] for n in shared)
assert inputs=={n:lt.sha256(R/n) for n in inputs}
record={'recorded_utc':lt.utc_now(),'source_revision':lt.git_revision(R),'dirty_staged_source_held':True,'input_hashes':inputs,'original_strict21_root_fixture_unchanged':True,'candidate_modules':['nativecmpkit-core','nativecmpkit-core-desktop','nativecmpkit-io','nativecmpkit-io-desktop'],'candidate_files':files,'candidate_files_count':len(files),'candidate_bytes':sum(x['size_bytes'] for x in files.values()),'original_producer_staging_source_revision':'6eb7c66eb01b390353100c63882cd102846c7b8d','original_staging_dirty_and_failed':True,'65_original_core_io_production_shared_build_inputs_unchanged':{n:old[n] for n in shared},'readonly_dependency_copy':{'regular_files':count,'file_bytes':size,'observed_content_digest':digest.hexdigest(),'uses_fresh_separate_readonly_copy_not_live_installation_cache':True,'every_copy_file_matches_original_cache_at_independent_review':True,'independent_provenance':False,'individual_inventory_not_archived_or_shared':True},'root_free_bytes':shutil.disk_usage(R).free,'tmpfs_free_bytes':shutil.disk_usage(O).free,'reserve_bytes':RESERVE,'consumer_methods_executed':0,'release_readiness_certified':False,'scope':'Independent postfailure prepared-copy/source recheck, not retroactive prestart freeze for first failed preparation. Real Gradle execution has not started.'}
assert record['root_free_bytes']>=RESERVE and record['tmpfs_free_bytes']>=RESERVE
(O/'prepared-inputs.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps({'fixture_files':len(fixtures),'candidate_files':len(files),'cache_files':count,'cache_bytes':size,'root_free_bytes':record['root_free_bytes'],'tmpfs_free_bytes':record['tmpfs_free_bytes'],'consumer_methods_executed':0}))
