"""Review the additive docs/archive delta and four executed checks; no native or suite rerun."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt,gzip,hashlib,json,shutil
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent;OUT=ROOT/'docs/development/evidence/postfreeze031-links-20261027';CHECKS=BASE/'checks'
assert not OUT.exists()
r=json.loads((CHECKS/'checks.json').read_bytes());assert r['passed'] and r['commands_completed']==r['commands_requested']==4 and r['python_unittest_executions']==0 and not r['changed_inputs']
before=(CHECKS/'inputs-before.json').read_bytes();after=(CHECKS/'inputs-after.json').read_bytes();assert before==after
prior=json.loads(gzip.decompress((ROOT/'docs/development/evidence/ci-preflight-20261027-031/inputs-before.json.gz').read_bytes()))
current=json.loads(after);changed=sorted(p for p in set(prior)|set(current) if prior.get(p)!=current.get(p))
assert changed and all(p in {'AGENTS.md','docs/development/native-io-verification.md'} or p.startswith('docs/development/evidence/ci-preflight-20261027-031/') for p in changed)
for row in r['results']:
 assert hashlib.sha256((CHECKS/row['log']).read_bytes()).hexdigest()==row['log_sha256'] and row['execution']['exit_code']==0
class Ids(HTMLParser):
 def __init__(self):super().__init__();self.ids=set()
 def handle_starttag(self,t,a):
  for k,v in a:
   if k=='id':self.ids.add(v)
expected=json.loads((ROOT/'docs/development/evidence/ci-preflight-20261027-031/lead-final-recount.json').read_bytes())['actual_document_output_checks'];outputs=[]
for row in expected:
 data=(BASE/'site'/row['path']).read_bytes();p=Ids();p.feed(data.decode());assert row['actual_anchor_verified'] in p.ids
 outputs.append({'path':row['path'],'actual_anchor_verified':row['actual_anchor_verified'],'sha256':hashlib.sha256(data).hexdigest()})
assert len(outputs)==66 and len({x['path'] for x in outputs})==25
OUT.mkdir()
for p in CHECKS.iterdir():
 if p.name in ('inputs-before.json','inputs-after.json'):(OUT/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
 else:shutil.copyfile(p,OUT/p.name)
shutil.copyfile(BASE/'driver.py',OUT/'driver.py');shutil.copyfile(Path(__file__),OUT/'lead-review.py')
review={'passed':True,'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':r['source_revision'],'commands':4,'python_tooling_methods':0,'source_input_count':r['source_input_count'],'source_and_staged_index_held':True,'actual_document_output_checks':outputs,'output_anchor_count':len(outputs),'unique_output_files':len({x['path'] for x in outputs}),'all_other_executable_test_and_workflow_inputs_unchanged':True,'exact_additive_changes_after_preflight031':changed,'earlier_full_preflight_methods_not_repeated':1297,'lightweight_resource_policy':r['lightweight_resource_policy'],'library_native_device_or_packaged_consumer_methods_executed':0,'publication_performed':False,'release_readiness_certified':False,'archive_is_additive_after_execution_not_self_certified':True,'scope':'Four actual held current index/strict docs/both whitespace checks, zero repeated Python/library methods.66 actual anchors/25 HTML files; only the full-preflight archive and two additive context links differ from preflight031. All executable inputs remain unchanged. This archive is additive, not self-certification or native/consumer/dependency-trust/API-ABI/legal/release evidence.'}
(OUT/'review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(OUT.iterdir()) if p.is_file()))
print(json.dumps({'passed':True,'commands':4,'source_input_count':r['source_input_count'],'actual_anchors':len(outputs),'actual_targets':review['unique_output_files']},indent=2))
