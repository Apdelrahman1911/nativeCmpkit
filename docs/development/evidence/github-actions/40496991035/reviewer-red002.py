"""Independently bind actual partial staging/resolution/compile failure to immutable Git."""
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,importlib.util,json,re,shutil,stat,subprocess,sys,tempfile,zipfile
ROOT=Path('/root/projects/nativeCmpKit');TMP=Path(__file__).parent;OUT=TMP/'review-archive'
REV='8ab48555a30d8fe2dbf6f422a6f2cf1bd2423c8f';REPO='Apdelrahman1911/nativeCmpkit';RUN=40496991035;JOB=122165124527;ART=12731960617

def sha(p):return hashlib.sha256(p if isinstance(p,bytes) else p.read_bytes()).hexdigest()
def doc(payload):
 def unique(pairs):
  result={}
  for k,v in pairs:assert k not in result;result[k]=v
  return result
 return json.loads(payload,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
assert not OUT.exists()
run=doc((TMP/'run-final.json').read_bytes());jobs=doc((TMP/'jobs-final.json').read_bytes())['jobs'];arts=doc((TMP/'artifacts-final.json').read_bytes())['artifacts']
assert run['id']==RUN and run['head_sha']==REV and run['run_attempt']==1 and run['repository']['full_name']==REPO
assert run['status']=='completed' and run['conclusion']=='failure' and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening'
job=next(j for j in jobs if j['id']==JOB);assert job['name']=='consumer-core-io' and job['conclusion']=='failure'
assert next(j for j in jobs if j['name']=='tooling')['conclusion']=='success'
assert next(j for j in jobs if j['name']=='library-tests')['conclusion']=='skipped'
assert len(arts)==1;art=arts[0];raw=(TMP/f'{ART}.zip').read_bytes()
assert art['id']==ART and not art['expired'] and art['workflow_run']['head_sha']==REV and art['workflow_run']['id']==RUN
assert len(raw)==art['size_in_bytes'] and 'sha256:'+sha(raw)==art['digest']
records={}
for row in subprocess.check_output(['git','ls-tree','-rz',REV],cwd=ROOT).split(b'\0'):
 if row:meta,name=row.split(b'\t',1);records[name.decode()]=meta.decode().split()
def blob(name):
 mode,kind,oid=records[name];assert kind=='blob' and mode in {'100644','100755'}
 return subprocess.check_output(['git','cat-file','blob',oid],cwd=ROOT)
with tempfile.TemporaryDirectory(prefix='nativecmpkit-owned-consumer8ab-review-',dir='/dev/shm') as directory:
 view=Path(directory)
 def materialize(name):
  p=view/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob(name))
 for name in records:
  if name=='settings.gradle.kts' or name.startswith('scripts/ci/') or (name.startswith(('calf-','sample/')) and name.endswith('/build.gradle.kts')):materialize(name)
 sys.path.insert(0,str(view/'scripts/ci'))
 import core_io_consumer as c,library_tests as lt,dependency_cache_inputs as keys
 projects=lt.projects(view)
 prefixes=['gradle/','convention-plugins/','scripts/ci/','scripts/native/','kotlin-js-store/','licenses/','tests/consumer/io-desktop/']
 prefixes += [f'{m}/{part}/' for m in projects for part in ('src','native','.cargo','gradle')]
 exact=set(lt.ROOT_INPUTS)|{f'{m}/{n}' for m in projects for n in ('build.gradle.kts','gradle.properties','gradle.lockfile')}
 exact|={n for n in records if n.startswith('sample/') and n.count('/')==2 and n.endswith('/build.gradle.kts')}
 exact|={'tests/consumer/verify_artifacts.py','docs/migration/identity.json','tests/consumer/build.gradle.kts','tests/consumer/settings.gradle.kts',
 'tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt','tests/consumer/src/commonMain/kotlin/nativecmpkit/consumer/PublicApiConsumer.kt','LICENSE','NOTICE','THIRD_PARTY_NOTICES.md'}
 for name in records:
  if (name in exact or any(name.startswith(p) for p in prefixes) or (name.startswith('sample/') and Path(name).name in keys.PROJECT_FILES)) and not set(PurePosixPath(name).parts[:-1])&lt.IGNORED_INPUT_DIRS:materialize(name)
 inputs=c.inputs(view)
 with zipfile.ZipFile(TMP/f'{ART}.zip') as z:
  infos=z.infolist();names=[i.filename for i in infos]
  assert len(names)==len(set(names))==15 and sum(i.file_size for i in infos)<64*1024**2
  for i in infos:
   p=PurePosixPath(i.filename)
   assert not p.is_absolute() and not {'.','..'}&set(p.parts) and '\\' not in i.filename
   assert not i.is_dir() and not i.flag_bits&1 and i.filename.endswith('.json') and i.file_size<=lt.MAX_REPORT_BYTES
   assert stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG)
  def get(n):return doc(z.read(n))
  base='ci-consumer/core-io-desktop/';receipt=get(base+'receipt.json');runtime=get(base+'runtime-before.json')
  assert len(inputs)==receipt['source_input_count']==741
  assert get(base+'inputs-before.json')==get(base+'inputs-after.json')==inputs
  assert receipt['source_revision']==receipt['source_revision_after']==REV and receipt['source_tree_dirty'] is False
  assert receipt['source_inputs_held'] is True and receipt['staging_inputs_held'] is True and receipt['independent_fixture_inputs_held'] is True
  assert receipt['changed_inputs']==[] and receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==lt.input_digest(inputs)
  copied=get(base+'fixture-copy.json');assert get(base+'fixture-copy-after.json')==copied=={n:sha(blob(c.FIXTURE+'/'+n)) for n in c.FIXTURE_FILES}
  assert runtime['source_revision']==REV and runtime['source_tree_dirty'] is False and runtime['host']['system']=='Linux' and runtime['host']['architecture']=='x64'
  assert runtime['java']['major']==17 and runtime['rust']['release']=='1.98.0'
  assert get('ci-runtime/consumer-core-io.json')['compiler_runtime_fingerprint']==runtime['compiler_runtime_fingerprint']
  cache_key=get('ci-runtime/consumer-dependencies.json');selected=keys.selected_inputs(view,'core-io')
  assert cache_key['inputs']==selected, {'missing':sorted(set(cache_key['inputs'])-set(selected)),'extra':sorted(set(selected)-set(cache_key['inputs'])),'changed':[n for n in set(selected)&set(cache_key['inputs']) if selected[n]!=cache_key['inputs'][n]]}
  assert cache_key['inputs']==selected and cache_key['dependency_inputs_sha256']==keys.fingerprint('core-io',selected) and cache_key['source_revision']==REV
  producer,child=receipt['executions'];assert producer['phase']=='real-producer-staging' and producer['execution']['exit_code']==0 and not producer['execution'].get('stop_reason')
  assert child['phase']=='independent-packaged-consumer' and child['execution']['exit_code']==1 and not child['execution'].get('stop_reason')
  runner_root=Path(producer['command'][0]).parent;consumer=runner_root/'build/ci-consumer/core-io-desktop/independent-consumer'
  assert (producer['command'],child['command'])==c.commands(runner_root,consumer)
  tasks=sorted(f':calf-{m}:publish{pub}PublicationToNativecmpkitVerificationRepository' for m in ('core','io') for pub in ('KotlinMultiplatform','Desktop'))
  assert receipt['actual_publication_task_markers']==tasks
  staged=get(base+'staging-before.json');assert get(base+'staging-after.json')==staged
  for n,value in staged.items():
   parts=PurePosixPath(n).parts;assert tuple(parts[:len(c.GROUP.split('.'))])==tuple(c.GROUP.split('.')) and parts[len(c.GROUP.split('.'))] in c.COORDINATES
   assert set(value)=={'bytes','sha256'} and type(value['bytes']) is int and re.fullmatch('[0-9a-f]{64}',value['sha256'])
  report=get(base+'static-packages.json');c.static_contract(report)
  assert report['check_count']==len(report['checks'])==308 and len({r['name'] for r in report['checks']})==308 and all(r['passed'] is True for r in report['checks'])
  assert len(report['artifact_files'])==20 and all(staged[r['path']]=={k:r[k] for k in ('bytes','sha256')} for r in report['artifact_files'])
  bindings=get(base+'module-file-bindings.json')
  for module,b in bindings.items():
   assert module in {root+'-desktop' for root in c.ROOTS} and b['declared_file_name']==module.replace('nativecmpkit-','calf-',1)+'-'+c.VERSION+'.jar'
   assert b['declared_file_url']==module+'-'+c.VERSION+'.jar' and b['metadata_file']==b['staged_file'].removesuffix('.jar')+'.module'
   assert staged[b['staged_file']]=={k:b[k] for k in ('bytes','sha256')} and staged[b['metadata_file']]['sha256']==b['metadata_sha256']
  resolution=get(base+'resolution.json');review=c.resolution_contract(resolution,staged,bindings)
  assert review['classpath_count']==4 and len(review['candidate_artifact_rows'])==8 and review['all_resolved_artifact_rows']==109
  assert receipt['resolution_review']=={'path':'independent-consumer/build/reports/partial-consumer-resolution.json','sha256':sha(z.read(base+'resolution.json')),**review}
  caches={n:get(base+'producer-cache-'+n+'.json') for n in ('before','after')}
  assert all(x['candidate_payload_group_absent'] is True and not any(x['candidate_group_paths_present'].values()) for x in caches.values())
  assert all(receipt['cache_containment'][k] is True for k in ('consumer_home_fresh_and_not_cached','candidate_payload_group_absent_before','candidate_payload_group_absent_after'))
  assert receipt['cache_containment']['consumer_gradle_home']!=receipt['cache_containment']['producer_gradle_home']
  assert receipt['owned_lock_removed'] is True and receipt['actual_consumer_methods_verified']==0 and 'consumer_tests' not in receipt
  assert receipt['passed'] is False and not any(n.endswith('.xml') for n in names)
  assert receipt['error']=={'contract':'Expected exactly one fresh independent Gradle9.7.1/JDK17 test-task marker','phase':'fresh-independent-resolution-and-tests','type':'ConsumerEvidenceError'}
  assert all(receipt[k] is False for k in ('packages_published','release_created','release_readiness_certified','ordinary_dependency_trust_certified'))
log=(TMP/'job-log.log').read_bytes();lines=[re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ','',s) for s in log.decode('utf-8-sig').splitlines()]
assert any('PublishedIoConsumerTest.kt:34:17' in s and "Unresolved reference 'consumeStream'" in s for s in lines)
assert not any(s.startswith('NATIVECMPKIT_PARTIAL_CONSUMER_TEST ') for s in lines)
helper_path='tests/consumer/src/commonMain/kotlin/nativecmpkit/consumer/PublicApiConsumer.kt';test_path=c.FIXTURE+'/'+c.FIXTURE_FILES[-1]
assert 'suspend fun consumeStream(file: KmpFile, context: PlatformContext): RawSource = file.source(context)' in blob(helper_path).decode()
assert 'consumeStream(file, PlatformContext.INSTANCE).buffered().use {' in blob(test_path).decode() and not any(n.endswith('PublicApiConsumer.kt') for n in copied)
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':RUN,'run_attempt':1,'source_revision':REV,'url':run['html_url'],'run_conclusion':'failure','job_id':JOB,'job_url':job['html_url'],
 'evidence_integrity_passed':True,'artifact_id':ART,'artifact_bytes':len(raw),'artifact_digest':art['digest'],'artifact_members':names,
 'source_input_count':len(inputs),'source_inputs_sha256':lt.input_digest(inputs),'all_inputs_reconstructed_from_Git_and_before_after_match':True,
 'independent_fixture_files_matched':len(copied),'producer_execution':producer['execution'],'producer_command':producer['command'],'consumer_execution':child['execution'],'consumer_command':child['command'],
 'actual_publication_task_markers':tasks,'staged_file_count':len(staged),'staged_total_bytes':sum(v['bytes'] for v in staged.values()),'static_checks_passed':308,'static_artifact_hash_bindings':20,
 'independent_classpath_count':4,'resolved_artifact_rows':109,'exact_candidate_rows':8,'metadata_report_hash_bindings':bindings,
 'independently_recomputed_dependency_key':cache_key['dependency_inputs_sha256'],'candidate_cached_producer_groups_absent_before_after':True,'consumer_home_fresh_uncached_observed':True,
 'actual_consumer_methods_verified':0,'actual_xml_reports':0,'runtime':runtime,'bounded_actual_job_diagnostics':{'log_bytes':len(log),'log_sha256':sha(log),'full_log_archived':False},
 'confirmed_failure':'Partial fixture copied the six IO methods but not the full consumer commonMain consumeStream helper. Actual consumer resolves all four classpaths and then fails test Kotlin compilation at line34 before any test task/XML. The helper only calls the public file.source(context); call that same API directly in both fixtures, preserving every method/assertion and compatibility. Do not add a fake production consumeStream API or copy unrelated21-module consumer source.',
 'locations':[{'path':test_path,'lines':'34','symbol':'boundaryAndLargeStreamsPreserveAllBytes'},{'path':helper_path,'lines':'40','symbol':'consumeStream'}],
 'limits':['Metadata bytes and candidate JARs are not uploaded; independently correlated original staging/static/binding/resolution report hashes, not a re-read of raw Maven descriptors or JARs.','This is a partial Core/IO resolution pass, not consumer runtime/complete21-root/native/ABI/legal/dependency/release certification.','Known cached producer candidate groups absent; no OS sandbox or detached daemon/descendant cleanup attestation.'],
 'issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,'review_script_sha256':sha(Path(__file__))}
(OUT/'raw').mkdir(parents=True)
for n in ('run-final.json','jobs-final.json','artifacts-final.json','collection.json'):shutil.copyfile(TMP/n,OUT/n)
(OUT/'raw'/f'{ART}.zip').write_bytes(raw);shutil.copyfile(Path(__file__),OUT/'lead-review.py')
with (OUT/'lead-independent-review.json').open('x') as f:json.dump(review,f,indent=2,sort_keys=True);f.write('\n')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.rglob('*')) if p.is_file()))
print(json.dumps({k:review[k] for k in ('run_id','evidence_integrity_passed','source_input_count','producer_execution','consumer_execution','independent_classpath_count','actual_consumer_methods_verified','actual_xml_reports')},indent=2))
