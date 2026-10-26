"""Additive archive of failed offline IO metadata generation; no build or acquisition."""
from pathlib import Path
import datetime as dt, hashlib, json, re, sys, xml.etree.ElementTree as E
ROOT=Path('/root/projects/nativeCmpKit');BASE=ROOT/'build/io-metadata-observation-001';DEST=ROOT/'docs/development/evidence/io-metadata-observation-001'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests
assert not DEST.exists()

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def data(p,x):put(p,(json.dumps(x,indent=2,sort_keys=True)+'\n').encode())
run=json.loads((BASE/'run/receipt.json').read_text());dry=json.loads((BASE/'dry-run/receipt.json').read_text())
assert run['execution']['exit_code']==1 and dry['execution']['exit_code']==0
before=json.loads((BASE/'run/inputs-before.json').read_text());after=json.loads((BASE/'run/inputs-after.json').read_text())
assert before==after==library_tests.snapshot_inputs(ROOT)
assert not run['changed_inputs'] and not dry['changed_inputs']
log=(BASE/'run/gradle.log').read_text();assert sha(BASE/'run/gradle.log')==run['raw_log_sha256']
missing=re.findall(r'^\s+> Could not download ([^\n]+?) \(([^\n]+?)\): No cached version available for offline mode$',log,re.M)
assert missing and "Execution failed for task ':calf-core:transformCommonMainDependenciesMetadata'" in log
assert len(missing)==len(set(missing))
DEST.mkdir(parents=True)
bindings=[]
for phase in ('dry-run','run'):
 for name in ('receipt.json','inputs-before.json','inputs-after.json','runtime.json','launcher-script.py'):
  p=BASE/phase/name;d=DEST/phase/name;put(d,p.read_bytes());bindings.append({'source':str(p.relative_to(ROOT)),'archive':str(d.relative_to(ROOT)),'sha256':sha(d)})
 lines=(BASE/phase/'gradle.log').read_text(errors='replace').splitlines()
 selected=[l for l in lines if l.startswith(('> Task ', ':calf-', ':kotlin', 'Execution failed for task', '> Could not resolve','FAILURE:','BUILD ')) or re.match(r'^\s+> Could not download ',l) or re.match(r'^\d+ actionable tasks:',l)]
 put(DEST/phase/'gradle.sanitized.log',('\n'.join(selected)+'\n').encode())
for name in ('lead-graph-review.json','pre-generation-output-observation.json'):
 p=BASE/name;put(DEST/name,p.read_bytes());bindings.append({'source':str(p.relative_to(ROOT)),'archive':str((DEST/name).relative_to(ROOT)),'sha256':sha(p)})
start=dt.datetime.fromisoformat(run['started_utc']).timestamp();end=dt.datetime.fromisoformat(run['finished_utc']).timestamp()
outputs=[];ns={'m':'http://maven.apache.org/POM/4.0.0'}
for publication in ('kotlinMultiplatform','desktop','android','js','wasmJs'):
 for filename in ('pom-default.xml','module.json'):
  p=ROOT/'calf-io/build/publications'/publication/filename
  row={'path':str(p.relative_to(ROOT)),'exists':p.is_file(),'fresh_in_run':False}
  if p.is_file():
   payload=p.read_bytes();d=DEST/'observed-outputs'/publication/filename;put(d,payload)
   row.update({'archive':str(d.relative_to(ROOT)),'sha256':sha(p),'bytes':len(payload),'mtime_utc':dt.datetime.fromtimestamp(p.stat().st_mtime,dt.timezone.utc).isoformat(),'fresh_in_run':start-1<=p.stat().st_mtime<=end+1})
   if filename.endswith('.xml'):
    assert b'<!DOCTYPE' not in payload and b'<!ENTITY' not in payload
    tree=E.fromstring(payload)
    row['coordinates']={k:tree.findtext('m:'+k,namespaces=ns) for k in ('groupId','artifactId','version')}
    row['dependencies']=[{k:x.findtext('m:'+k,namespaces=ns) for k in ('groupId','artifactId','version','scope')} for x in tree.findall('m:dependencies/m:dependency',ns)]
  outputs.append(row)
assert sum(o['fresh_in_run'] for o in outputs)==1
fresh=next(o for o in outputs if o['fresh_in_run']);assert fresh['path'].endswith('kotlinMultiplatform/pom-default.xml')
assert all(not o['exists'] for o in outputs if o['path'].endswith('module.json'))
record={'schema_version':1,'collected_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'Failed source-bound offline IO metadata investigation. Dry-run is graph evidence only. Actual failure, uncached prerequisites, stale/missing outputs and the sole fresh root POM are retained; not a complete metadata gate.','source_revision':run['source_revision'],'dirty_worktree':True,'dry_run_execution':dry['execution'],'execution':run['execution'],'requested_task_count':len(run['requested_tasks']),'dry_run_graph_count':len(dry['observed_dry_run_graph']),'selected_input_count':len(after),'selected_inputs_unchanged':True,'failed_task':':calf-core:transformCommonMainDependenciesMetadata','failed_configuration':':calf-core:commonMainResolvableDependenciesMetadata','uncached_artifact_count':len(missing),'uncached_artifacts':[{'filename':n,'coordinates':c} for n,c in missing],'observed_outputs':outputs,'archives':bindings,'raw_logs':[{'path':str((BASE/p/'gradle.log').relative_to(ROOT)),'sha256':sha(BASE/p/'gradle.log'),'archived':False} for p in ('dry-run','run')],'library_or_consumer_testcases_executed':0,'metadata_gate_passed':False,'release_readiness_certified':False,'collector_sha256':sha(Path(__file__)),'limitations':['No dependency acquisition, task exclusion, gate bypass, online retry, staging, signing, registry, release or Pages operation.','A fresh root POM is not .module/resource-variant coverage. The existing desktop POM is stale and must not be used as a pre-switch baseline.','No pre-switch .module baseline exists; dependency neutrality, ABI equivalence, complete notices or legal clearance are not established.','Local source is held dirty at the base commit, not an immutable release candidate. Generated POM boilerplate mentioning publication does not mean artifacts were published.']}
data(DEST/'archive.json',record);put(DEST/'collector.py',Path(__file__).read_bytes())
files=sorted(p for p in DEST.rglob('*') if p.is_file());put(DEST/'SHA256SUMS',''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in files).encode())
assert library_tests.snapshot_inputs(ROOT)==after
print(json.dumps({'archive':str(DEST.relative_to(ROOT)),'archive_sha256':sha(DEST/'archive.json'),'bound_files':len(files),'uncached_artifacts':len(missing),'fresh_outputs':sum(o['fresh_in_run'] for o in outputs),'metadata_gate_passed':False},indent=2))
