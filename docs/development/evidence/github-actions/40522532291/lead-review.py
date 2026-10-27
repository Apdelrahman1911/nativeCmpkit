"""Independent Git/ZIP/setup-failure review. Read artifacts as data; never execute them."""
from pathlib import Path,PurePosixPath
import datetime as dt,hashlib,json,re,shutil,stat,subprocess,sys,tempfile,zipfile
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent
REV='202059090bbbf896d07d38a3441cf21c8888c63b';REPO='Apdelrahman1911/nativeCmpkit'
def sha(x):return hashlib.sha256(x if isinstance(x,bytes) else x.read_bytes()).hexdigest()
def decode(x):
 def unique(items):
  result={}
  for k,v in items:assert k not in result;result[k]=v
  return result
 return json.loads(x,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
records={}
for r in subprocess.check_output(['git','ls-tree','-rz',REV],cwd=ROOT).split(b'\0'):
 if r:
  meta,n=r.split(b'\t',1);records[n.decode()]=meta.decode().split()
def blob(name):
 mode,kind,oid=records[name];assert mode in {'100644','100755'} and kind=='blob'
 return subprocess.check_output(['git','cat-file','blob',oid],cwd=ROOT)
with tempfile.TemporaryDirectory(prefix='nativecmpkit-setup-failure-review-',dir='/dev/shm') as directory:
 view=Path(directory)
 def materialize(name):
  p=view/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob(name))
 materialize('settings.gradle.kts')
 for name in records:
  if name.startswith('scripts/ci/') or (name.startswith(('calf-','sample/')) and name.endswith('/build.gradle.kts')):materialize(name)
 sys.path.insert(0,str(view/'scripts/ci'))
 import library_tests as lt,dependency_cache_inputs as keys,runtime_context as runtime
 projects=lt.projects(view)
 prefixes=['gradle/','convention-plugins/src/','convention-plugins/gradle/','convention-plugins/.cargo/','.cargo/','kotlin-js-store/']
 prefixes += [p+'/'+n+'/' for p in projects for n in ('gradle','.cargo','native/.cargo')]
 exact=set(lt.ROOT_INPUTS)|set(keys.RECIPE_FILES)|{'convention-plugins/build.gradle.kts','convention-plugins/settings.gradle.kts'}
 for project in set(projects)|{n.split('/')[0]+'/'+n.split('/')[1] for n in records if n.startswith('sample/') and n.count('/')==2 and n.endswith('/build.gradle.kts')}:
  exact|={project+'/'+n for n in keys.PROJECT_FILES}|{project+'/native/'+n for n in ('Cargo.toml','Cargo.lock','build.rs','rust-toolchain.toml')}
 for name in records:
  if (name in exact or any(name.startswith(p) for p in prefixes)) and not set(PurePosixPath(name).parts[:-1])&lt.IGNORED_INPUT_DIRS:materialize(name)
 selected=keys.selected_inputs(view,'libraries')
 workflow=blob('.github/workflows/gradle.yml').decode();assert "matrix.test-modules || 'all'" in workflow
 for run_id,kind in ((40522532291,'navigation-geo-matrix'),(40522929974,'ios-ui')):
  source=BASE/str(run_id);r=decode((source/'run-final.json').read_bytes());jobs=decode((source/'jobs-final.json').read_bytes())['jobs'];artifacts=decode((source/'artifacts-final.json').read_bytes())['artifacts']
  assert r['id']==run_id and r['head_sha']==REV and r['run_attempt']==1 and r['repository']['full_name']==REPO and r['event']=='workflow_dispatch'
  assert r['status']=='completed' and r['conclusion']=='failure'
  assert next(j for j in jobs if j['name']=='tooling')['conclusion']=='success' and next(j for j in jobs if j['name']=='consumer-core-io')['conclusion']=='skipped'
  libraries=[j for j in jobs if j['name'].startswith('library-tests (')]
  assert len(libraries)==len(artifacts)==(4 if kind=='navigation-geo-matrix' else 1)
  rows=[];artifact_reviews=[]
  for artifact in artifacts:
   raw=source/(str(artifact['id'])+'.zip');assert raw.stat().st_size==artifact['size_in_bytes']<=64*1024**2
   assert 'sha256:'+sha(raw)==artifact['digest'] and artifact['workflow_run']['head_sha']==REV and artifact['workflow_run']['id']==run_id and not artifact['expired']
   with zipfile.ZipFile(raw) as z:
    infos=z.infolist();names=[i.filename for i in infos]
    assert len(names)==len(set(names))<=8 and sum(i.file_size for i in infos)<128*1024
    for info in infos:
     p=PurePosixPath(info.filename)
     assert not p.is_absolute() and not {'.','..'}&set(p.parts) and '\\' not in info.filename and not info.is_dir()
     assert not info.flag_bits&1 and stat.S_IFMT(info.external_attr>>16) in (0,stat.S_IFREG) and info.filename.startswith('ci-runtime/') and info.filename.endswith('.json')
    documents={n:decode(z.read(n)) for n in names}
    assert not any(n.endswith('.xml') for n in names)
    if kind=='navigation-geo-matrix':
     assert set(names) in ({'ci-runtime/actual.json','ci-runtime/library-dependencies.json'},{'ci-runtime/actual.json','ci-runtime/library-dependencies.json','ci-runtime/selection.json'})
     context=documents['ci-runtime/actual.json'];dep=documents['ci-runtime/library-dependencies.json']
     assert context['source_revision']==REV and context['source_tree_dirty'] is False and context['java']['major']==17 and context['rust']['release']=='1.98.0'
     assert context['compiler_runtime_fingerprint']==runtime.compiler_runtime_fingerprint(context)
     assert dep['inputs']==selected and len(selected)==dep['dependency_input_count'] and dep['dependency_inputs_sha256']==keys.fingerprint('libraries',selected) and dep['source_revision']==REV
     assert dep['compiled_or_test_results_reused'] is False and dep['ordinary_dependency_trust_certified'] is False
     slot=artifact['name'].removeprefix('library-evidence-').removesuffix('-'+REV)
     expected={'desktop-linux-x64':('desktop','Linux','x64'),'browser-js':('js','Linux','x64'),'browser-wasm':('wasm','Linux','x64'),'ios-iphone':('ios','Darwin','arm64')}
     assert slot in expected and context['host']['system']==expected[slot][1] and context['host']['architecture']==expected[slot][2]
     job=next(j for j in libraries if j['name'].startswith('library-tests ('+slot+','));steps={s['name']:s for s in job['steps']}
     assert job['conclusion']=='failure' and steps['Explicit dependency/compiler/runtime/slot-keyed cache']['conclusion']=='failure'
     assert steps['Fresh actual library suite with strict nonzero receipts']['conclusion']=='skipped' and steps['Source-set-aware expected library tests (never samples)']['conclusion']=='skipped'
     cache_key='nativecmpkit-deps-v2-'+('macOS' if expected[slot][1]=='Darwin' else expected[slot][1])+'-'+('ARM64' if expected[slot][2]=='arm64' else 'X64')+'-'+slot+'-'+expected[slot][0]+'-calf-navigation,calf-geo-'+context['compiler_runtime_fingerprint']+'-'+dep['dependency_inputs_sha256']
     lines=(source/('job-'+str(job['id'])+'-log.log')).read_text().splitlines()
     assert sum('Key Validation Error: '+cache_key+' cannot contain commas.' in line for line in lines)==1
     rows.append({'slot':slot,'job_id':job['id'],'job_url':job['html_url'],'setup_failed_step':'Explicit dependency/compiler/runtime/slot-keyed cache','cache_key':cache_key,'cache_key_reconstructed_from_actual_runtime_and_Git_bound_dependencies':True,'dependency_input_count':len(selected),'actual_runtime':context,'library_gradle_and_plan_steps_skipped':True,'actual_library_testcase_count':0,'actual_xml_reports':0,'confirmed_error_kind':'Actions cache key comma validation'})
    else:
     assert names==['ci-runtime/selection.json']
     context=documents[names[0]];assert context['source_revision']==REV and context['source_tree_dirty'] is False and context['host']=={'architecture':'arm64','python':'3.15.0','system':'Darwin'}
     assert context['simulator']['state']!='Booted' and context['simulator']['device_type'].startswith('com.apple.CoreSimulator.SimDeviceType.iPhone')
     job=libraries[0];steps={s['name']:s for s in job['steps']}
     assert job['id']==122255014242 and job['conclusion']=='failure' and steps['Record actual architecture, compiler, SDK and selected simulator']['conclusion']=='failure'
     assert steps['Fresh actual library suite with strict nonzero receipts']['conclusion']=='skipped' and steps['Explicit dependency/compiler/runtime/slot-keyed cache']['conclusion']=='skipped'
     lines=(source/('job-'+str(job['id'])+'-log.log')).read_text().splitlines()
     assert sum("subprocess.TimeoutExpired: Command '('git', 'status', '--porcelain', '--untracked-files=normal')' timed out after 60 seconds" in line for line in lines)==1
     assert any('Data Migration Failed' in line for line in lines)
     assert 'NATIVECMPKIT_UIKIT_ACTIVE' not in '\n'.join(line for line in lines if not line.lstrip().startswith('#'))
     rows.append({'slot':'ios-iphone','job_id':job['id'],'job_url':job['html_url'],'setup_failed_step':'Record actual architecture, compiler, SDK and selected simulator','selection_context':context,'confirmed_error_kind':'Git status subprocess.TimeoutExpired after60 seconds','simulator_boot_log_also_reports_data_migration_failure':True,'underlying_timeout_or_migration_cause':'unknown; no raw native crash/GC execution exists in this attempt','cache_plan_and_library_steps_skipped':True,'actual_library_testcase_count':0,'actual_xml_reports':0})
    artifact_reviews.append({'id':artifact['id'],'name':artifact['name'],'bytes':raw.stat().st_size,'digest':artifact['digest'],'members':names,'remote_digest_and_safe_data_only_members_verified':True})
  assert len(rows)==len(libraries)
  destination=ROOT/'docs/development/evidence/github-actions'/str(run_id)
  if kind=='ios-ui':destination=destination/'attempt-1'
  assert not destination.exists();(destination/'raw').mkdir(parents=True)
  for name in ('run-final.json','jobs-final.json','artifacts-final.json','collection.json'):shutil.copyfile(source/name,destination/name)
  for artifact in artifacts:shutil.copyfile(source/(str(artifact['id'])+'.zip'),destination/'raw'/(str(artifact['id'])+'.zip'))
  shutil.copyfile(Path(__file__),destination/'lead-review.py')
  locations=[]
  for name,tokens in (('.github/workflows/gradle.yml',("matrix.test-modules || 'all'",'Record actual architecture, compiler, SDK and selected simulator')),('scripts/ci/runtime_context.py',('timeout=60','"source_tree_dirty": bool(command("git", "status"'))):
   for n,line in enumerate(blob(name).decode().splitlines(),1):
    if any(t in line for t in tokens):locations.append({'path':name,'line_at_immutable_revision':n,'code':line.strip()})
  save(destination/'lead-independent-review.json',{'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'evidence_integrity_passed':True,'run_id':run_id,'run_attempt':1,'source_revision':REV,'url':r['html_url'],'run_conclusion':'failure','profile':kind,'workflow_sha256':sha(blob('.github/workflows/gradle.yml')),'library_jobs':rows,'artifacts':artifact_reviews,'locations':locations,'actual_library_tests':0,'actual_XML_reports':0,'native_application_or_GC_execution':False,'source_repairs_runtime_verified':False,'raw_job_logs_not_archived':True,'packages_releases_deployments_Pages_or_issue_mutations':False,'release_readiness_certified':False,'scope':'Completed setup failures, zero library/consumer/Apple methods. Exact immutable Git source/remote ZIP digest/data-only ownership inspected. Four navigation cache key errors independently reproduce literal diagnostics; UIKit separately times out checking Git status after simulator migration output. No native-GC interruption result or underlying timeout cause is inferred.'})
  (destination/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(destination).as_posix()+'\n' for p in sorted(destination.rglob('*')) if p.is_file()))
  print(json.dumps({'archive':str(destination),'profile':kind,'run_conclusion':'failure','actual_library_tests':0,'XML':0,'reviewed_library_jobs':len(rows)},indent=2),flush=True)
