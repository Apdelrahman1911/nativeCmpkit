"""Isolated partial Maven/test/cache copy. Cache hashes are observations, not trust."""
from pathlib import Path
import datetime as dt,hashlib,json,os,shutil,subprocess,sys
R=Path('/root/projects/nativeCmpKit');O=Path(__file__).resolve().parent;RESERVE=8192*1024**2
sys.path.insert(0,str(R/'scripts/ci'));import library_tests as lt
assert shutil.disk_usage(R).free>=RESERVE and shutil.disk_usage(O).free>=RESERVE
assert not (R/'build/ci-verification/.library-tests.lock').exists()
assert not (O/'project').exists() and not (O/'candidate-maven').exists() and not (O/'readonly-dependencies').exists()
fixtures=sorted(p.relative_to(R).as_posix() for p in (R/'tests/consumer/io-desktop').rglob('*') if p.is_file())
assert len(fixtures)==5 and not any((R/n).is_symlink() for n in fixtures)
input_hashes={n:lt.sha256(R/n) for n in fixtures+['tests/consumer/build.gradle.kts','tests/consumer/settings.gradle.kts','tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt','tests/consumer/verify_artifacts.py','tests/consumer/test_gradle_module_identity.py','tests/consumer/test_core_io_fixture_contract.py']}
assert all((R/n).read_bytes()==subprocess.check_output(['git','show','b5a4508a:'+n],cwd=R) for n in ['tests/consumer/build.gradle.kts','tests/consumer/settings.gradle.kts','tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt'])
shutil.copytree(R/'tests/consumer/io-desktop',O/'project');assert all(lt.sha256(O/'project'/Path(n).relative_to('tests/consumer/io-desktop'))==input_hashes[n] for n in fixtures)
original=json.loads((R/'docs/development/evidence/maven-staging-001/staged-files.json').read_bytes());repo=R/'build/verification-repo'
selected=['nativecmpkit-core','nativecmpkit-core-desktop','nativecmpkit-io','nativecmpkit-io-desktop'];group='io/github/apdelrahman1911/nativecmpkit'
candidate_files={}
for module in selected:
 source=repo/group/module/'0.1.0-preview.1';dest=O/'candidate-maven'/group/module/'0.1.0-preview.1';dest.mkdir(parents=True)
 for p in sorted(source.iterdir()):
  assert p.is_file() and not p.is_symlink();name=p.relative_to(repo).as_posix();observed={'size_bytes':p.stat().st_size,'sha256':lt.sha256(p)}
  assert observed==original[name];shutil.copyfile(p,dest/p.name);assert observed=={'size_bytes':(dest/p.name).stat().st_size,'sha256':lt.sha256(dest/p.name)};candidate_files[name]=observed
# Independent copy, NOT the live installation cache named as a read-only cache.
# Ignore only documented cache locks/GC bookkeeping. Copy contains untrusted
# dependency bytes; its digest is an observation, never independent provenance.
cache=Path('/root/.gradle/caches/modules-2');copy=O/'readonly-dependencies/modules-2';copy.mkdir(parents=True)
cache_bytes=0;cache_count=0;cache_digest=hashlib.sha256()
for base,dirs,files in os.walk(cache,followlinks=False):
 dirs.sort()
 for n in dirs:assert not (Path(base)/n).is_symlink()
 for name in sorted(files):
  if name.endswith('.lock') or name=='gc.properties':continue
  source=Path(base)/name;assert source.is_file() and not source.is_symlink();relative=source.relative_to(cache);dest=copy/relative
  if shutil.disk_usage(O).free-source.stat().st_size<RESERVE:raise ValueError('Owned cache seed would exhaust tmpfs reserve')
  before=source.stat();h=lt.sha256(source);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
  after=source.stat();assert (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino) and h==lt.sha256(dest)==lt.sha256(source)
  dest.chmod(0o444);cache_count+=1;cache_bytes+=before.st_size;cache_digest.update(f'{h}  {relative.as_posix()}\n'.encode())
for base,dirs,files in os.walk(O/'readonly-dependencies',topdown=False):Path(base).chmod(0o555)
assert input_hashes=={n:lt.sha256(R/n) for n in input_hashes}
old_inputs=json.loads((R/'docs/development/evidence/maven-staging-001/inputs-before.json').read_bytes())
shared=sorted(n for n in old_inputs if (n in ['calf-core/build.gradle.kts','calf-io/build.gradle.kts','build.gradle.kts','settings.gradle.kts','gradle.properties'] or n.startswith(('convention-plugins/','gradle/')) or (n.startswith(('calf-core/src/','calf-io/src/')) and not Path(n).parts[2].endswith('Test'))))
assert len(shared)==67 and all(lt.sha256(R/n)==old_inputs[n] for n in shared)
record={'recorded_utc':lt.utc_now(),'source_revision':lt.git_revision(R),'dirty_staged_source_held':True,'input_hashes':input_hashes,'original_strict21_root_fixture_unchanged':True,'candidate_modules':selected,'candidate_files':candidate_files,'candidate_files_count':len(candidate_files),'candidate_bytes':sum(x['size_bytes'] for x in candidate_files.values()),'original_producer_staging_source_revision':'6eb7c66eb01b390353100c63882cd102846c7b8d','original_staging_dirty_and_failed':True,'67_original_core_io_production_shared_build_inputs_unchanged':{n:old_inputs[n] for n in shared},'readonly_dependency_copy':{'regular_files':cache_count,'file_bytes':cache_bytes,'observed_content_digest':cache_digest.hexdigest(),'uses_fresh_separate_copy_not_live_installation_cache':True,'independent_provenance':False,'individual_inventory_not_archived_or_shared':True},'root_free_bytes':shutil.disk_usage(R).free,'tmpfs_free_bytes':shutil.disk_usage(O).free,'reserve_bytes':RESERVE,'consumer_methods_executed':0,'release_readiness_certified':False}
assert record['root_free_bytes']>=RESERVE and record['tmpfs_free_bytes']>=RESERVE
(O/'prepared-inputs.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps({'fixture_files':len(fixtures),'candidate_files':len(candidate_files),'cache_files':cache_count,'cache_bytes':cache_bytes,'root_free_bytes':record['root_free_bytes'],'tmpfs_free_bytes':record['tmpfs_free_bytes']}))
