"""Recount held lightweight preflight and actual generated documentation, without rerunning suites."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt,gzip,hashlib,json,shutil,sys
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent;CHECKS=BASE/'checks';OUT=ROOT/'docs/development/evidence/ci-preflight-20261027-031'
assert not OUT.exists()
r=json.loads((CHECKS/'checks.json').read_bytes());assert r['passed'] and r['commands_completed']==r['commands_requested']==23 and r['python_unittest_executions']==1297 and r['changed_inputs']==[]
assert r['staged_index_sha256_before']==r['staged_index_sha256_after']
before=(CHECKS/'inputs-before.json').read_bytes();after=(CHECKS/'inputs-after.json').read_bytes();assert before==after
for row in r['results']:
 assert hashlib.sha256((CHECKS/row['log']).read_bytes()).hexdigest()==row['log_sha256']
 assert row['execution']['exit_code']==0 and not row['execution'].get('stop_reason')
class Ids(HTMLParser):
 def __init__(self):super().__init__();self.ids=set()
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k=='id':self.ids.add(v)
old=json.loads((ROOT/'docs/development/evidence/ci-preflight-20261027-030/lead-review.json').read_bytes())['actual_document_output_checks']
expect=[(x['path'],x['actual_anchor_verified']) for x in old]
expect += [('development/native-io-verification/index.html',x) for x in ['nativecmpkit-ios-io-and-coil-verification','current-evidence-and-containment','source-owned-foundation-copy','actual-stream-and-coil-ownership','regression-matrix','preserved-execution-history','efficient-next-verification']]
expect += [('development/IO/index.html','current-native-copy-and-lifecycle-verification')]
outputs=[]
for path,anchor in expect:
 p=BASE/'site'/path;data=p.read_bytes();parser=Ids();parser.feed(data.decode());assert anchor in parser.ids,(path,anchor)
 outputs.append({'path':path,'actual_anchor_verified':anchor,'sha256':hashlib.sha256(data).hexdigest()})
assert len(outputs)==66 and len({x['path'] for x in outputs})==24
OUT.mkdir()
for p in CHECKS.iterdir():
 if p.name in ('inputs-before.json','inputs-after.json'):(OUT/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
 else:shutil.copyfile(p,OUT/p.name)
shutil.copyfile(BASE/'driver.py',OUT/'driver.py');shutil.copyfile(Path(__file__),OUT/'lead-review.py')
review={'passed':True,'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':r['source_revision'],'commands':23,'python_tooling_methods':1297,'414_ci_and11_focused_io_methods_overlap_full_preflight':True,'source_and_staged_index_held':True,'source_input_count':r['source_input_count'],'actual_document_output_checks':outputs,'output_anchor_count':66,'unique_output_files':24,'lightweight_resource_policy':r['lightweight_resource_policy'],'archive_is_additive_after_execution_not_self_certified':True,'local_heavy_build_capacity_certified':False,'library_native_device_or_packaged_consumer_methods_executed':0,'publication_performed':False,'release_readiness_certified':False,'scope':'23 actual held lightweight commands with1297 overlapping Python methods, strict MkDocs/actionlint/history/audit/current index/both whitespace guards;66 actual anchors/24 new HTML outputs. No runtime/native/packaged consumer or publication run. Later archive/context links are additive, not circular certification of themselves or an immutable release candidate.'}
(OUT/'lead-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(OUT.iterdir()) if p.is_file()))
print(json.dumps({k:review[k] for k in ['passed','source_input_count','python_tooling_methods','output_anchor_count','unique_output_files']},indent=2))
