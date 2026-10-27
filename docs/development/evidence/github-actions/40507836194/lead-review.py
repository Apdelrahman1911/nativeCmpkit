"""Independently review actual seven-method Core/IO packaged-consumer success at immutable Git."""
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,importlib.util,json,re,shutil,stat,subprocess,sys,tempfile,zipfile
ROOT=Path('/root/projects/nativeCmpKit');TMP=Path(__file__).parent;OUT=TMP/'review-archive'
REV='8ab82a3fa41caad34cd7fb7a2d3722bfc25e3838';REPO='Apdelrahman1911/nativeCmpkit';RUN=40507836194;JOB=122201976847;ART=12736236898

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
assert run['status']=='completed' and run['conclusion']=='success' and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening'
job=next(j for j in jobs if j['id']==JOB);assert job['name']=='consumer-core-io' and job['conclusion']=='success'
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
 exact|={'tests/consumer/verify_artifacts.py','tests/consumer/gradle.properties','docs/migration/identity.json','tests/consumer/build.gradle.kts','tests/consumer/settings.gradle.kts',
 'tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt','tests/consumer/src/commonMain/kotlin/nativecmpkit/consumer/PublicApiConsumer.kt','LICENSE','NOTICE','THIRD_PARTY_NOTICES.md'}
 for name in records:
  if (name in exact or any(name.startswith(p) for p in prefixes) or (name.startswith('sample/') and Path(name).name in keys.PROJECT_FILES)) and not set(PurePosixPath(name).parts[:-1])&lt.IGNORED_INPUT_DIRS:materialize(name)
 inputs=c.inputs(view)
 with zipfile.ZipFile(TMP/f'{ART}.zip') as z:
  infos=z.infolist();names=[i.filename for i in infos]
  assert len(names)==len(set(names))==19 and sum(i.file_size for i in infos)<64*1024**2
  for i in infos:
   p=PurePosixPath(i.filename)
   assert not p.is_absolute() and not {'.','..'}&set(p.parts) and '\\' not in i.filename
   assert not i.is_dir() and not i.flag_bits&1 and i.filename.endswith(('.json','.xml')) and i.file_size<=lt.MAX_REPORT_BYTES
   assert stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG)
  def get(n):return doc(z.read(n))
  base='ci-consumer/core-io-desktop/';receipt=get(base+'receipt.json');runtime=get(base+'runtime-before.json')
  assert len(inputs)==receipt['source_input_count']==742
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
  assert child['phase']=='independent-packaged-consumer' and child['execution']['exit_code']==0 and not child['execution'].get('stop_reason')
  runner_root=Path(producer['command'][0]).parent;consumer=runner_root/'build/ci-consumer/core-io-desktop/independent-consumer'
  assert (producer['command'],child['command'])==c.commands(runner_root,consumer)
  tasks=sorted(f':calf-{m}:publish{pub}PublicationToNativecmpkitVerificationRepository' for m in ('core','io') for pub in ('KotlinMultiplatform','Desktop'))
  assert receipt['actual_publication_task_markers']==tasks
  staged=get(base+'staging-before.json');assert get(base+'staging-after.json')==staged
  for n,value in staged.items():
   parts=PurePosixPath(n).parts;assert tuple(parts[:len(c.GROUP.split('.'))])==tuple(c.GROUP.split('.')) and parts[len(c.GROUP.split('.'))] in c.COORDINATES
   assert set(value)=={'bytes','sha256'} and type(value['bytes']) is int and re.fullmatch('[0-9a-f]{64}',value['sha256'])
  report=get(base+'static-packages.json');report_static=report;c.static_contract(report)
  assert report['check_count']==len(report['checks'])==312 and len({r['name'] for r in report['checks']})==312 and all(r['passed'] is True for r in report['checks'])
  assert len(report['artifact_files'])==20 and all(staged[r['path']]=={k:r[k] for k in ('bytes','sha256')} for r in report['artifact_files'])
  bindings=get(base+'module-file-bindings.json')
  for module,b in bindings.items():
   assert module in {root+'-desktop' for root in c.ROOTS} and b['declared_file_name']==module.replace('nativecmpkit-','calf-',1)+'-'+c.VERSION+'.jar'
   assert b['declared_file_url']==module+'-'+c.VERSION+'.jar' and b['metadata_file']==b['staged_file'].removesuffix('.jar')+'.module'
   assert staged[b['staged_file']]=={k:b[k] for k in ('bytes','sha256')} and staged[b['metadata_file']]['sha256']==b['metadata_sha256']
  resolution=get(base+'resolution.json');review=c.resolution_contract(resolution,staged,bindings)
  assert review['classpath_count']==4 and len(review['candidate_artifact_rows'])==8 and review['all_resolved_artifact_rows']==109
  recorded_resolution=receipt['resolution_review']
  assert set(recorded_resolution)=={'path','sha256',*review}
  assert recorded_resolution['path']=='independent-consumer/build/reports/partial-consumer-resolution.json'
  assert re.fullmatch('[0-9a-f]{64}',recorded_resolution['sha256'])
  assert {k:recorded_resolution[k] for k in review}==review
  # Immutable controller fresh_resolution hashes Gradle's JsonOutput bytes;
  # write then archives a different Python sorted/indented serialization.
  # Recheck every parsed binding, and identify both byte scopes separately.
  assert z.read(base+'resolution.json')==(json.dumps(resolution,indent=2,sort_keys=True)+'\n').encode()
  archived_resolution_sha256=sha(z.read(base+'resolution.json'))
  caches={n:get(base+'producer-cache-'+n+'.json') for n in ('before','after')}
  assert all(x['candidate_payload_group_absent'] is True and not any(x['candidate_group_paths_present'].values()) for x in caches.values())
  assert all(receipt['cache_containment'][k] is True for k in ('consumer_home_fresh_and_not_cached','candidate_payload_group_absent_before','candidate_payload_group_absent_after'))
  assert receipt['cache_containment']['consumer_gradle_home']!=receipt['cache_containment']['producer_gradle_home']
  assert receipt['owned_lock_removed'] is True and receipt['actual_consumer_methods_verified']==7 and 'consumer_tests' in receipt
  assert receipt['passed'] is True and 'error' not in receipt
  runtime_after=get(base+'runtime-after.json')
  assert all(runtime_after.get(k)==runtime.get(k) for k in ('source_revision','source_tree_dirty','host','java','rust','android_platform','compiler_runtime_fingerprint'))
  assert receipt['free_bytes_before']>=8192*1024**2 and receipt['free_bytes_after']>=8192*1024**2
  outcomes=get(base+'test-outcomes.json');assert outcomes==receipt['consumer_tests']
  xmls=[n for n in names if n.endswith('.xml')];assert len(xmls)==2
  cases=[]
  for report in outcomes['reports']:
   payload=z.read(base+report['path']);assert sha(payload)==report['sha256']
   parsed=lt.junit_cases(payload);assert all(report[k]==v for k,v in lt.case_counts(parsed).items());cases.extend(parsed)
  assert set(xmls)=={base+r['path'] for r in outcomes['reports']}
  assert len(cases)==len({(case['classname'],case['name']) for case in cases})==7
  assert {(case['classname'],case['name']) for case in cases}==c.EXPECTED_CASES
  order=lambda case:(case['classname'],case['name'])
  assert sorted(cases,key=order)==sorted(outcomes['testcases'],key=order)
  assert outcomes['totals']==lt.case_counts(cases)=={'tests':7,'failures':0,'errors':0,'skipped':0,'passed':7,'executed':7,'not_applicable':0,'unexpected_skipped':0}
  assert outcomes['fresh_task_marker']=='NATIVECMPKIT_PARTIAL_CONSUMER_TEST task=:test gradle=9.7.1 java=17'
  pom_checks={root+suffix+':pom-display-name' for root in c.ROOTS for suffix in ('','-desktop')}
  assert pom_checks <= {row['name'] for row in report_static['checks'] if row['passed'] is True}

  assert all(receipt[k] is False for k in ('packages_published','release_created','release_readiness_certified','ordinary_dependency_trust_certified'))
log=(TMP/'job-log.log').read_bytes();lines=[re.sub(r'^\d{4}-\d{2}-\d{2}T\S+Z ','',s) for s in log.decode('utf-8-sig').splitlines()]
expected_marker='NATIVECMPKIT_PARTIAL_CONSUMER_TEST task=:test gradle=9.7.1 java=17'
assert not any(line.startswith(expected_marker) for line in lines)
assert any('actual_consumer_methods_verified' in line and '"actual_consumer_methods_verified": 7' in line for line in lines)
assert 'need(markers == {expected: 1},' in blob('scripts/ci/core_io_consumer.py').decode()
assert not any("Unresolved reference 'consumeStream'" in line for line in lines)
stage_markers=[line for line in lines if line.startswith('NATIVECMPKIT_PARTIAL_STAGE ')]
assert len(stage_markers)==0  # child logs are not forwarded/uploaded on success
assert 'need(len(markers) == 4 and set(markers) == expected_tasks,' in blob('scripts/ci/core_io_consumer.py').decode()
test_path=c.FIXTURE+'/'+c.FIXTURE_FILES[-1]
full_test_path='tests/consumer/src/desktopTest/kotlin/nativecmpkit/consumer/PublishedIoConsumerTest.kt'
assert blob(test_path)==blob(full_test_path) and 'file.source(PlatformContext.INSTANCE).buffered().use {' in blob(test_path).decode()
origin_path=c.FIXTURE+'/src/test/kotlin/nativecmpkit/consumer/PublishedArtifactOriginTest.kt'
origin_source=blob(origin_path).decode();fixture_build=blob(c.FIXTURE+'/build.gradle.kts').decode()
for text in ('type.protectionDomain.codeSource?.location','Files.isRegularFile(jar)','Files.newInputStream(jar)','System.getProperty("nativecmpkit.expected.$root.name")','System.getProperty("nativecmpkit.expected.$root.sha256")'):
 assert text in origin_source,text
for text in ('nativecmpkit.expected.$suffix.name','nativecmpkit.expected.$suffix.sha256','verifyCandidateResolution'):
 assert text in fixture_build,text
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':RUN,'run_attempt':1,'source_revision':REV,'url':run['html_url'],'run_conclusion':'success','job_id':JOB,'job_url':job['html_url'],
 'evidence_integrity_passed':True,'artifact_id':ART,'artifact_bytes':len(raw),'artifact_digest':art['digest'],'artifact_members':names,
 'source_input_count':len(inputs),'source_inputs_sha256':lt.input_digest(inputs),'all_inputs_reconstructed_from_Git_and_before_after_match':True,
 'independent_fixture_files_matched':len(copied),'producer_execution':producer['execution'],'producer_command':producer['command'],'consumer_execution':child['execution'],'consumer_command':child['command'],
 'actual_publication_task_markers':tasks,'staged_file_count':len(staged),'staged_total_bytes':sum(v['bytes'] for v in staged.values()),'static_checks_passed':312,'static_artifact_hash_bindings':20,
 'independent_classpath_count':4,'resolved_artifact_rows':109,'exact_candidate_rows':8,'metadata_report_hash_bindings':bindings,
 'resolution_bytes':{'original_Gradle_report_recorded_sha256':recorded_resolution['sha256'],'archived_Python_parsed_copy_sha256':archived_resolution_sha256,'original_raw_bytes_uploaded':False,'original_raw_sha256_independently_recomputed':False,'all_archived_parsed_resolution_and_candidate_bindings_independently_recomputed':True},
 'independently_recomputed_dependency_key':cache_key['dependency_inputs_sha256'],'candidate_cached_producer_groups_absent_before_after':True,'consumer_home_fresh_uncached_observed':True,
 'actual_consumer_methods_verified':7,'actual_xml_reports':2,'consumer_totals':outcomes['totals'],'consumer_testcases':cases,'reported_fresh_test_task_marker':outcomes['fresh_task_marker'],'exactly_one_marker_enforced_by_Git_bound_controller':True,'raw_child_marker_counter_independently_recounted':False,'runtime_after_matches':True,'current_POM_display_name_checks':sorted(pom_checks),'runtime':runtime,'bounded_actual_job_diagnostics':{'log_bytes':len(log),'log_sha256':sha(log),'full_log_archived':False},
 'confirmed_result':'The repaired standalone consumer freshly stages four actual Core/IO root+desktop publications, resolves four isolated classpaths and executes all seven mandatory methods in two fresh XML reports, zero skips. The six IO methods use the actual public source API without the excluded helper. The seventh loads PlatformContext/KmpFile from regular resolved JARs and compares exact resolved/staged filenames and SHA256 bytes through the Git-bound fixture assertions. No producer-project/source fallback. Four current NativeCmpKit POM display-name checks pass among312 actual remote static checks. This is Linux/x64 partial consumer verification, not full21-root/native/all-target/API-ABI/legal/dependency/release certification.',
 'locations':[{'path':test_path,'symbol':'six byte-identical public IO consumer methods'},{'path':origin_path,'symbol':'runtimeLibraryClassesComeFromExactStagedDesktopJars'},{'path':c.FIXTURE+'/build.gradle.kts','symbol':'verified resolution and test expected origin properties'}],
 'limits':['The raw producer/consumer logs are not uploaded or forwarded on successful runs; their recorded hashes and marker requirements are source-bound controller evidence, not independently rehashed logs/recounted marker counters. Fresh test XML and every parsed assertion/binding are independently reviewed.','Metadata bytes and candidate JARs are not uploaded; independently correlated original staging/static/binding/parsed-resolution hashes, not a local re-read of raw Maven descriptors or JARs; the real passed origin test independently checks loaded bytes in the builder. Gradle original-resolution SHA is recorded but raw bytes were not uploaded; the archived Python copy has a different serialization and separately recomputed hash.','This is a partial Core/IO resolution pass, not complete21-root/native/ABI/legal/dependency/release certification.','Known cached producer candidate groups absent; no OS sandbox or detached daemon/descendant cleanup attestation.'],
 'issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,'review_script_sha256':sha(Path(__file__))}
(OUT/'raw').mkdir(parents=True)
for n in ('run-final.json','jobs-final.json','artifacts-final.json','collection.json'):shutil.copyfile(TMP/n,OUT/n)
(OUT/'raw'/f'{ART}.zip').write_bytes(raw);shutil.copyfile(Path(__file__),OUT/'lead-review.py')
with (OUT/'lead-independent-review.json').open('x') as f:json.dump(review,f,indent=2,sort_keys=True);f.write('\n')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.rglob('*')) if p.is_file()))
print(json.dumps({k:review[k] for k in ('run_id','evidence_integrity_passed','source_input_count','producer_execution','consumer_execution','independent_classpath_count','actual_consumer_methods_verified','actual_xml_reports')},indent=2))
