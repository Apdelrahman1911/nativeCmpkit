"""Archive explicitly scoped local metadata generation without publishing or certifying packages."""
from pathlib import Path
import datetime as dt, hashlib, json, re, sys, xml.etree.ElementTree as E
ROOT=Path('/root/projects/nativeCmpKit');name=sys.argv[1]
assert name in ('io-metadata-observation-002','io-metadata-observation-003')
BASE=ROOT/'build'/name;DEST=ROOT/'docs/development/evidence'/name
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests
assert not DEST.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def data(p,x):put(p,(json.dumps(x,indent=2,sort_keys=True)+'\n').encode())
run=json.loads((BASE/'run/receipt.json').read_text());dry=json.loads((BASE/'dry-run/receipt.json').read_text())
assert dry['execution']['exit_code']==0
before=json.loads((BASE/'run/inputs-before.json').read_text());after=json.loads((BASE/'run/inputs-after.json').read_text())
assert before==after==library_tests.snapshot_inputs(ROOT)
assert not run['changed_inputs'] and not dry['changed_inputs']
log=(BASE/'run/gradle.log').read_text();assert sha(BASE/'run/gradle.log')==run['raw_log_sha256']
failed=re.findall(r"^Execution failed for task '([^']+)'",log,re.M)
misses=sorted(set(re.findall(r'No cached version of ([A-Za-z0-9_.:+-]+) available for offline mode',log)))
DEST.mkdir(parents=True);bindings=[]
for phase in ('dry-run','run'):
 for filename in ('receipt.json','inputs-before.json','inputs-after.json','runtime.json','launcher-script.py'):
  p=BASE/phase/filename;d=DEST/phase/filename;put(d,p.read_bytes());bindings.append({'source':str(p.relative_to(ROOT)),'archive':str(d.relative_to(ROOT)),'sha256':sha(d)})
 lines=(BASE/phase/'gradle.log').read_text(errors='replace').splitlines()
 selected=[l for l in lines if l.startswith(('> Task ', ':calf-', ':kotlin', 'Execution failed for task','FAILURE:','BUILD ')) or re.match(r'^\s*> (?:Could not|Error while|Failed to calculate|No cached)',l) or re.match(r'^\d+ actionable tasks:',l)]
 put(DEST/phase/'gradle.sanitized.log',('\n'.join(selected)+'\n').encode())
for filename in ('lead-graph-review.json','pre-generation-output-observation.json'):
 p=BASE/filename;put(DEST/filename,p.read_bytes());bindings.append({'source':str(p.relative_to(ROOT)),'archive':str((DEST/filename).relative_to(ROOT)),'sha256':sha(p)})
start=dt.datetime.fromisoformat(run['started_utc']).timestamp();end=dt.datetime.fromisoformat(run['finished_utc']).timestamp()
outputs=[];ns={'m':'http://maven.apache.org/POM/4.0.0'}
for publication in ('kotlinMultiplatform','desktop','android','js','wasmJs'):
 pub=publication[0].upper()+publication[1:]
 for filename,kind in (('pom-default.xml','PomFile'),('module.json','MetadataFile')):
  p=ROOT/'calf-io/build/publications'/publication/filename;task=':calf-io:generate'+kind+'For'+pub+'Publication'
  row={'path':str(p.relative_to(ROOT)),'publication':publication,'task':task,'requested':task in run['requested_tasks'],'exists':p.is_file(),'fresh_in_run':False}
  if p.is_file():
   payload=p.read_bytes();d=DEST/'observed-outputs'/publication/filename;put(d,payload)
   row.update({'archive':str(d.relative_to(ROOT)),'sha256':sha(p),'bytes':len(payload),'mtime_utc':dt.datetime.fromtimestamp(p.stat().st_mtime,dt.timezone.utc).isoformat(),'fresh_in_run':start-1<=p.stat().st_mtime<=end+1})
   if filename.endswith('.xml'):
    assert b'<!DOCTYPE' not in payload and b'<!ENTITY' not in payload
    tree=E.fromstring(payload)
    row['coordinates']={k:tree.findtext('m:'+k,namespaces=ns) for k in ('groupId','artifactId','version')}
    row['dependencies']=[{k:x.findtext('m:'+k,namespaces=ns) for k in ('groupId','artifactId','version','scope')} for x in tree.findall('m:dependencies/m:dependency',ns)]
   else:
    m=json.loads(payload)
    row.update({'format_version':m.get('formatVersion'),'component':m.get('component'),'variants':m.get('variants',[])})
  outputs.append(row)
subset_pass=run['execution']['exit_code']==0 and all(o['fresh_in_run'] for o in outputs if o['requested'])
assert not any(o['fresh_in_run'] for o in outputs if not o['requested'])
assert all(not o['exists'] for o in outputs if o['publication']=='kotlinMultiplatform' and o['path'].endswith('module.json'))
if name.endswith('002'):
 assert run['execution']['exit_code']==1 and failed==[':calf-io:extractAndroidMainAnnotations'] and misses==['com.android.tools.lint:lint-gradle:32.4.0']
 assert sum(o['fresh_in_run'] for o in outputs)==3
record={'schema_version':1,'collected_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'Explicit target-subset source-bound offline IO POM/.module generation. A dry-run is graph evidence; failed prerequisites and stale/missing outputs remain separate. No artifact staging, distribution, consumer or full-KMP/ABI equivalence claim.','source_revision':run['source_revision'],'dirty_worktree':True,'dry_run_execution':dry['execution'],'execution':run['execution'],'requested_tasks':run['requested_tasks'],'requested_task_count':len(run['requested_tasks']),'dry_run_graph_count':len(dry['observed_dry_run_graph']),'selected_input_count':len(after),'selected_inputs_unchanged':True,'failed_tasks':failed,'uncached_coordinates':misses,'observed_outputs':outputs,'archives':bindings,'raw_logs':[{'path':str((BASE/p/'gradle.log').relative_to(ROOT)),'sha256':sha(BASE/p/'gradle.log'),'archived':False} for p in ('dry-run','run')],'library_or_consumer_testcases_executed':0,'requested_subset_generation_passed':subset_pass,'full_kmp_metadata_gate_passed':False,'release_readiness_certified':False,'collector_sha256':sha(Path(__file__)),'limitations':['No dependency acquisition, task exclusion, check disabling, online retry, staging, signing, registry, release or Pages operation.','Failed root metadata observation001 remains unresolved. Later target-subset success, if any, cannot change that failure or the missing root .module. Android failure002 remains unresolved.','There is no pre-switch .module baseline. Fresh target outputs do not establish dependency neutrality, ABI equivalence, complete publication notices or consumer/legal clearance.','Local source is held dirty at the base commit, not an immutable release candidate. POM boilerplate mentioning publication does not mean artifacts were published.','Module file references require separate read-only hash/content inspection of actual local outputs; metadata generation alone does not prove package payload completeness.']}
data(DEST/'archive.json',record);put(DEST/'collector.py',Path(__file__).read_bytes())
files=sorted(p for p in DEST.rglob('*') if p.is_file());put(DEST/'SHA256SUMS',''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in files).encode())
assert library_tests.snapshot_inputs(ROOT)==after
print(json.dumps({'archive':str(DEST.relative_to(ROOT)),'archive_sha256':sha(DEST/'archive.json'),'bound_files':len(files),'fresh_outputs':sum(o['fresh_in_run'] for o in outputs),'subset_pass':subset_pass,'full_kmp_metadata_gate_passed':False},indent=2))
