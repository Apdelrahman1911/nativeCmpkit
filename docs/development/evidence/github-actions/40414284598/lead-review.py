"""Lead's read-only source/ZIP/XML recount for the contained verification checkpoint.
No network or execution of archived code. Run ID/profile are explicit arguments.
Not a release or platform-behavior certification.
"""
from collections import Counter
import datetime as dt
import hashlib,json,os,re,subprocess,sys,tempfile,zipfile
from pathlib import Path,PurePosixPath
root=Path('/root/projects/nativeCmpKit');sys.path.insert(0,str(root/'scripts/ci'))
import library_tests as lt,native_test_policy as np,workflow_matrix as wm
out=Path(sys.argv[1]);profile=sys.argv[2]
run=json.loads((out/'run-final.json').read_text());jobs=json.loads((out/'jobs-final.json').read_text())['jobs']
artifacts=json.loads((out/'artifacts-final.json').read_text())['artifacts'];revision=run['head_sha']
assert re.fullmatch('[0-9a-f]{40}',revision)
assert run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening'
assert run['repository']['full_name']=='Apdelrahman1911/nativeCmpkit'
assert run['status']=='completed'
# Materialize only inert, commit-bound build/source inputs to independently plan/recount.
records={}
for row in subprocess.check_output(['git','ls-tree','-rz',revision],cwd=root).split(b'\0'):
 if not row:continue
 metadata,name=row.split(b'\t',1);mode,kind,oid=metadata.decode().split();records[name.decode()] = (mode,kind,oid)
def blob(name):
 mode,kind,oid=records[name];assert kind=='blob' and mode in ('100644','100755')
 return subprocess.check_output(['git','cat-file','blob',oid],cwd=root)
with tempfile.TemporaryDirectory(prefix='nativecmpkit-source-review-') as temp:
 view=Path(temp)
 def materialize(name):
  p=view/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob(name))
 materialize('settings.gradle.kts')
 for name in records:
  if name.startswith(('calf-','sample/')) and name.endswith('/build.gradle.kts'):materialize(name)
 projects=lt.projects(view)
 prefixes=['gradle/','convention-plugins/','scripts/ci/','scripts/native/','kotlin-js-store/']
 prefixes += [f'{module}/{folder}/' for module in projects for folder in ('src','native','.cargo','gradle')]
 exact=set(lt.ROOT_INPUTS)|{f'{module}/{n}' for module in projects for n in ('build.gradle.kts','gradle.properties','gradle.lockfile')}
 exact|={name for name in records if name.startswith('sample/') and name.count('/')==2 and name.endswith('/build.gradle.kts')}
 for name in records:
  if (name in exact or any(name.startswith(p) for p in prefixes)) and not set(PurePosixPath(name).parts[:-1])&lt.IGNORED_INPUT_DIRS:materialize(name)
 expected_inputs=lt.snapshot_inputs(view)
 reviewed=[]
 for slot in wm.matrix(profile)['include']:
  matching=[a for a in artifacts if a['name']=='library-evidence-'+slot['slot']]
  assert len(matching)==1,'Missing or duplicate selected-slot evidence'
  artifact=matching[0];p=out/'raw'/f"{artifact['id']}.zip";payload=p.read_bytes()
  assert len(payload)<=64*1024*1024 and len(payload)==artifact['size_in_bytes'] and not artifact['expired']
  digest='sha256:'+hashlib.sha256(payload).hexdigest();assert artifact['digest']==digest
  with zipfile.ZipFile(p) as archive:
   members=archive.infolist();assert len(members)<=2000 and sum(i.file_size for i in members)<=64*1024*1024
   names=[i.filename for i in members];assert len(names)==len(set(names))
   for i in members:
    path=PurePosixPath(i.filename)
    assert not path.is_absolute() and not set(path.parts)&{'.','..'} and '\\' not in i.filename
    assert not i.is_dir() and i.file_size<=lt.MAX_REPORT_BYTES and ((i.external_attr>>16)&0o170000)!=0o120000
    assert i.filename.endswith(('.json','.xml')),'Non-evidence payload must not be uploaded'
   def doc(name):return json.loads(archive.read(name))
   base='build/ci-verification/'+slot['slot']+'/'
   receipt=doc(base+'receipt.json');before=doc(base+'inputs-before.json');after=doc(base+'inputs-after.json')
   assert before==after==expected_inputs
   assert receipt['source_revision']==receipt['source_revision_after']==revision and receipt['source_tree_dirty'] is False
   assert not receipt.get('changed_inputs') and not receipt.get('input_capture_error')
   assert receipt['inputs_before_sha256']==receipt['inputs_after_sha256']==lt.input_digest(expected_inputs)
   runtime=doc(base+'runtime.json');assert runtime['source_revision']==revision and not runtime['source_tree_dirty']
   assert receipt['runtime_receipt_sha256']==hashlib.sha256(archive.read(base+'runtime.json')).hexdigest()
   assert runtime['host']['architecture']==slot['arch'] and runtime['java']['major']==17 and runtime['rust']['release']=='1.98.0'
   plan=lt.plan(view,slot['suite']);assert plan==doc(base+'plan.json')==doc('build/ci-plan/plan.json')
   simulator=runtime.get('simulator',{}).get('udid') if slot['suite']=='ios' else None
   command=lt.gradle_command(slot['suite'],plan,simulator,root=view)
   if runtime['host']['system']=='Windows':command[0]='.\\gradlew.bat'
   assert receipt['command']==command
   module_reviews=[]
   for expected in plan['expected']:
    matches=[m for m in receipt['modules'] if m['module']==expected['module']];assert len(matches)==1
    module=matches[0];cases=[];keys=set();xmls=[]
    xml_names=[n for n in names if n.startswith(expected['report_directory']+'/') and PurePosixPath(n).name.startswith('TEST-') and n.endswith('.xml')]
    assert set(xml_names)=={r['path'] for r in module['reports']} and xml_names
    for n in xml_names:
     data=archive.read(n);xml_cases=lt.junit_cases(data);new_keys={(c['classname'],c['name']) for c in xml_cases}
     assert not keys&new_keys;keys|=new_keys;cases+=xml_cases
     recorded=next(r for r in module['reports'] if r['path']==n)
     assert recorded['sha256']==hashlib.sha256(data).hexdigest()
     xmls.append({'path':n,'sha256':recorded['sha256'],'cases':xml_cases})
    scenarios,errors=np.apply(expected['module'],slot['suite'],cases,runtime['host']['system'],slot.get('native-ui')=='true')
    assert not errors, (expected['module'], errors)
    assert sorted(cases,key=lambda c:(c['classname'],c['name']))==sorted(module['testcases'],key=lambda c:(c['classname'],c['name'])), expected['module']
    assert scenarios==module['native_scenarios'], expected['module']
    counts=lt.case_counts(cases)
    assert all(module[k]==v for k,v in counts.items())
    for xml in xmls:
     recorded=next(r for r in module['reports'] if r['path']==xml['path'])
     assert all(recorded[k]==v for k,v in lt.case_counts(xml['cases']).items())
    module_reviews.append({'module':expected['module'],'task':expected['task'],'report_files':len(xml_names),**counts})
   counts={k:sum(m[k] for m in module_reviews) for k in receipt['totals']}
   assert counts==receipt['totals']
   assert receipt['passed']==(receipt['execution']['exit_code']==0 and not receipt['execution'].get('stop_reason') and not receipt['errors'])
   job_matches=[j for j in jobs if j['name'].startswith('library-tests ('+slot['slot']+',')];assert len(job_matches)==1
   job=job_matches[0];assert job['status']=='completed'
   if receipt['passed']:assert job['conclusion']=='success'
   reviewed.append({'slot':slot['slot'],'job_id':job['id'],'job_url':job['html_url'],'job_conclusion':job['conclusion'],'suite':slot['suite'],'passed':receipt['passed'],'artifact_id':artifact['id'],'artifact_digest':digest,'source_input_count':len(expected_inputs),'source_inputs_sha256':lt.input_digest(expected_inputs),'runtime':runtime,'command':command,'execution':receipt['execution'],'totals':counts,'modules':module_reviews,'report_files':sum(m['report_files'] for m in module_reviews),'scope':receipt['scope']})
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':run['id'],'run_attempt':run['run_attempt'],'url':run['html_url'],'profile':profile,'source_revision':revision,'run_conclusion':run['conclusion'],'evidence_integrity_passed':True,'runtime_slots':reviewed,'total_fresh_passed_executions':sum(x['totals']['passed'] for x in reviewed),'total_host_inapplicable_cases':sum(x['totals']['not_applicable'] for x in reviewed),'total_xml_reports':sum(x['report_files'] for x in reviewed),'limits':['Repeated target executions are not distinct test methods.','The archive contains only uploaded reports/JSON, not producer or consumer packages.','Source/XML/ZIP recount does not certify native feature parity, ABI, dependency trust, legal obligations or release readiness.'],'issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,'review_script_sha256':lt.sha256(Path(__file__))}
(out/'lead-independent-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:review[k] for k in ('run_id','source_revision','run_conclusion','total_fresh_passed_executions','total_host_inapplicable_cases','total_xml_reports','evidence_integrity_passed')},indent=2))
