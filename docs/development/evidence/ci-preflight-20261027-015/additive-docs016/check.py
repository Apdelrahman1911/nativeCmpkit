"""Final additive documentation/index/staged whitespace check, not native testing."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib, json, shutil, sys
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
OUT=ROOT/'docs/development/evidence/ci-preflight-20261027-015/additive-docs016';assert not OUT.exists()
selected=['AGENTS.md','mkdocs.yml','docs/development/checkpoint-resource-native-20261027.md','docs/testing/README.md','docs/development/resolutions/BUILD.json','docs/development/status.json','docs/development/status.md','scripts/development/validate_resolutions.py']
before={n:lt.sha256(ROOT/n) for n in selected};library=lt.snapshot_inputs(ROOT)
assert len(library)==712 and lt.input_digest(library)=='27169d3c0d5d8a2bd3b8200e86dabddac63bc66d7226fbfdb98be948e50622ba'
commands=[('resolution',['python3','-B','scripts/development/validate_resolutions.py','--check'],90),('strict',[str(ROOT/'build/docs-verification/locked-002/venv/bin/python'),'-B','-m','mkdocs','build','--strict','--site-dir',str(BASE/'site')],180),('cached',['git','diff','--cached','--check'],60),('worktree',['git','diff','--check'],60)]
results=[]
for name,argv,limit in commands:
 log=BASE/(name+'.log');r=lt.execute(ROOT,argv,log,limit,8192)
 results.append({'name':name,'command':argv,'execution':r,'log':log.name,'log_sha256':lt.sha256(log)})
 assert r['exit_code']==0 and not r.get('stop_reason'),r
assert before=={n:lt.sha256(ROOT/n) for n in selected} and library==lt.snapshot_inputs(ROOT)
class Ids(HTMLParser):
 def __init__(self):super().__init__();self.ids=set()
 def handle_starttag(self,tag,attrs):self.ids.update(v for k,v in attrs if k=='id')
html=[]
for n,a in [('development/checkpoint-resource-native-20261027/index.html','corrective-source-held-preflight015'),('testing/index.html','exact-native-ownership-and-controlled-gradle-cleanup-follow-up')]:
 p=BASE/'site'/n;q=Ids();q.feed(p.read_text());assert a in q.ids;html.append({'path':n,'actual_anchor_verified':a,'sha256':lt.sha256(p)})
OUT.mkdir()
for name,_,_ in commands:shutil.copyfile(BASE/(name+'.log'),OUT/(name+'.log'))
shutil.copyfile(Path(__file__),OUT/'check.py')
r={'recorded_utc':lt.utc_now(),'source_revision':lt.git_revision(ROOT),'dirty_source_held':True,'commands':results,'passed':True,'selected_additive_inputs_held':before,'library_build_inputs_unchanged_from_successful_compile':{'count':712,'sha256':lt.input_digest(library)},'actual_HTML_anchor_checks':html,'full_preflight_reference':'docs/development/evidence/ci-preflight-20261027-015/lead-review.json','library_native_device_or_strict_packaged_consumer_methods_executed':0,'release_readiness_certified':False,'root_free_bytes':shutil.disk_usage(ROOT).free,'reserve_bytes':8192*1024**2,'scope':'Final additive docs/index and both staged/worktree whitespace only; full015 Python methods reused at their original freeze, not rerun/circularly certified. All712 library/build inputs still exactly match successful corrected UIKit KLIB compilation; zero new Apple or cleanup Gradle execution.'}
assert r['root_free_bytes']>=r['reserve_bytes']
(OUT/'receipt.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
(OUT/'SHA256SUMS').write_text(''.join(f'{lt.sha256(p)}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps({'passed':True,'commands':len(results),'library_inputs':len(library),'root_free_bytes':r['root_free_bytes']}))
