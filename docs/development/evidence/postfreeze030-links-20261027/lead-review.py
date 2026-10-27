"""Exact two-context/archival delta review; no additional library/native execution."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt,gzip,hashlib,json,os,shutil,subprocess
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent;CHECKS=BASE/'checks';DEST=ROOT/'docs/development/evidence/postfreeze030-links-20261027'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def doc(p):return json.loads(p.read_bytes())
r=doc(CHECKS/'checks.json');before=doc(CHECKS/'inputs-before.json');after=doc(CHECKS/'inputs-after.json');previous=json.loads(gzip.decompress((ROOT/'docs/development/evidence/ci-preflight-20261027-030/inputs-after.json.gz').read_bytes()))
assert r['passed'] and r['commands_completed']==r['commands_requested']==4 and r['python_unittest_executions']==0
assert before==after and not r['changed_inputs'];changed=sorted(n for n in previous if previous[n]!=before[n]);added=sorted(set(before)-set(previous))
assert changed==['AGENTS.md','docs/development/checkpoint-navhost-verified-20261027.md']
assert added and all(n.startswith('docs/development/evidence/ci-preflight-20261027-030/') for n in added)
assert r['source_revision']==r['source_revision_after']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert r['staged_index_sha256_before']==r['staged_index_sha256_after']==hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)).hexdigest()
for n,v in before.items():
 p=ROOT/n
 if v['kind']=='regular':assert p.is_file() and not p.is_symlink() and sha(p)==v['sha256']
 elif v['kind']=='deleted':assert not p.exists()
 else:assert p.is_symlink() and hashlib.sha256(os.readlink(p).encode()).hexdigest()==v['target_sha256']
for row in r['results']:assert row['execution']['exit_code']==0 and not row['execution'].get('stop_reason') and sha(CHECKS/row['log'])==row['log_sha256']
class P(HTMLParser):
 def __init__(self):super().__init__();self.ids=set();self.h1s=[]
 def handle_starttag(self,t,a):
  v=dict(a).get('id');self.ids.add(v)
  if t=='h1':self.h1s.append(v)
page=BASE/'site/development/checkpoint-navhost-verified-20261027/index.html';p=P();p.feed(page.read_text());assert p.h1s==['nativecmpkit-immutable-nav-006-acceptance-and-complete-sdk-context']
assert 'actual-immutable-navigation-and-sdk-verification' in p.ids and 'every-original-nav-006-criterion' in p.ids
assert 'evidence/ci-preflight-20261027-030/lead-review.json' in page.read_text()
policy=r['lightweight_resource_policy'];assert not policy['heavy_build8GiB_guard_lowered'] and policy['maximum_root_decrease_bytes']==128*1024**2
assert policy['root_free_after']>=policy['root_free_before']-128*1024**2 and policy['tmpfs_free_after']>=2*1024**3
assert not DEST.exists();DEST.mkdir()
for name in ['checks.json',*[v['log'] for v in r['results']]]:shutil.copyfile(CHECKS/name,DEST/name)
for name in ['inputs-before.json','inputs-after.json']:
 raw=(CHECKS/name).read_bytes();target=DEST/(name+'.gz');target.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(target.read_bytes())==raw
shutil.copyfile(BASE/'driver.py',DEST/'driver.py');shutil.copyfile(Path(__file__),DEST/'lead-review.py')
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':r['source_revision'],'captured_source_count':len(before),'source_stage_inputs_held':True,'all_other_executable_test_and_workflow_inputs_unchanged':True,'existing_input_changes':changed,'added_archival_inputs':added,'actual_Markdown_heading_unchanged_verified':True,'new_preflight_anchor_verified':True,'actual_page_sha256':sha(page),'commands_executed':4,'python_library_native_or_consumer_methods_executed':0,'publication_performed':False,'release_readiness_certified':False,'scope':'Separate post-freeze exact context/archive-only delta. Strict MkDocs/resolution index/both whitespace checks pass with inputs/stage held. Actual generated page retains one h1 and exact new receipt link. No previous full preflight claim for these later bytes, no new native/library/platform/consumer/release pass.'}
(DEST/'review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
(DEST/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(DEST.iterdir()) if p.is_file()))
print(json.dumps({'passed':True,'commands':4,'source_input_count':len(before),'context_changes':changed,'archived':str(DEST)}))
