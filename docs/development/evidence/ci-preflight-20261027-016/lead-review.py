"""Lead independently rechecks original logs/source/index/output before lossless archiving."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt,gzip,hashlib,json,os,re,shutil,subprocess
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path('/dev/shm/nativecmpkit-preflight-20261027-016');OUT=BASE/'checks'
DEST=ROOT/'docs/development/evidence/ci-preflight-20261027-016'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def held(inputs):
 for name,row in inputs.items():
  p=ROOT/name
  if row['kind']=='regular':assert p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],name
  elif row['kind']=='deleted':assert not p.exists(),name
  elif row['kind']=='symlink':assert p.is_symlink() and hashlib.sha256(os.readlink(p).encode()).hexdigest()==row['target_sha256'],name
  else:raise AssertionError('Unknown input kind')
class Anchors(HTMLParser):
 def __init__(self):super().__init__();self.anchors=set()
 def handle_starttag(self,tag,attrs):self.anchors.update(v for k,v in attrs if k=='id')
record=json.loads((OUT/'checks.json').read_bytes())
before=json.loads((OUT/'inputs-before.json').read_bytes());after=json.loads((OUT/'inputs-after.json').read_bytes())
assert record['passed'] and record['commands_requested']==record['commands_completed']==len(record['results'])==23
assert before==after and not record['changed_inputs'] and len(before)==record['source_input_count']
assert record['driver_sha256']==sha(BASE/'driver.py')
assert record['source_revision']==record['source_revision_after']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert record['staged_index_sha256_before']==record['staged_index_sha256_after']==hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)).hexdigest()
held(before)
counts={}
for row in record['results']:
 assert row['execution']['exit_code']==0 and not row['execution'].get('stop_reason'),row['name']
 log=OUT/row['log'];assert sha(log)==row['log_sha256']
 if row['unittest_count'] is not None:
  text=log.read_text()
  counts[row['name']]=int(re.findall(r'^Ran (\d+) tests? in [^\n]+$',text,re.M)[-1])
  assert counts[row['name']]==row['unittest_count'] and row['unittest_summary_ok'] and re.search(r'^OK(?: \([^\n]*\))?$',text,re.M)
assert sum(counts.values())==record['python_unittest_executions']==1078
outputs=[]
for relative,anchor in [
 ('development/checkpoint-consumer-uikit-20261027/index.html','explicitly-partial-independent-coreio-consumer'),
 ('development/native-ui-application-host/index.html','actual-worker-execution-strict-plist-failure-and-owning-manifest-repair'),
 ('development/release-readiness/index.html','gate-ledger'),
 ('development/index.html','working-indexes'),
 ('testing/index.html','explicitly-partial-packaged-coreio-verification'),
 ('development/checkpoint-resource-native-20261027/index.html','real-detached-daemon-leak-and-owning-controlled-fixture-repair'),
 ('development/dependency-lock-witness-20261027/index.html','actual007-complete-selected-runtime-witness'),
 ('decisions/0007-owned-gradle-fixture-processes/index.html','decision')]:
 p=BASE/'site'/relative;assert p.is_file(),relative
 parser=Anchors();parser.feed(p.read_text())
 assert anchor in parser.anchors,(relative,anchor,sorted(parser.anchors))
 outputs.append({'path':relative,'sha256':sha(p),'actual_anchor_verified':anchor})
assert not DEST.exists();DEST.mkdir()
for name in ['checks.json',*[row['log'] for row in record['results']]]:
 shutil.copyfile(OUT/name,DEST/name);assert sha(OUT/name)==sha(DEST/name)
shutil.copyfile(BASE/'driver.py',DEST/'driver.py')
shutil.copyfile(Path(__file__),DEST/'lead-review.py')
compressed=[]
for name in ['inputs-before.json','inputs-after.json']:
 payload=(OUT/name).read_bytes();z=gzip.compress(payload,mtime=0);p=DEST/(name+'.gz');p.write_bytes(z)
 assert gzip.decompress(p.read_bytes())==payload
 compressed.append({'path':p.name,'gzip_bytes':len(z),'gzip_sha256':sha(p),'uncompressed_bytes':len(payload),'uncompressed_sha256':hashlib.sha256(payload).hexdigest()})
held(before)
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':record['source_revision'],
 'source_input_count':len(before),'all_captured_source_bytes_held_during_run_and_before_and_after_archive':True,
 'staged_index_held_before_archive':True,'both_staged_and_worktree_whitespace_checks_passed':True,
 'commands':23,'python_tooling_methods':1078,'python_tooling_counts':counts,'actual_document_output_checks':outputs,
 'compressed_input_maps':compressed,'lightweight_resource_policy':record['lightweight_resource_policy'],
 'library_native_device_or_packaged_consumer_methods_executed':0,'publication_performed':False,'release_readiness_certified':False,
 'archive_is_additive_after_execution_not_self_certified':True,
 'scope':'Source/stage-held finite lightweight preflight.1078 Python methods overlap prior scoped runs; strict MkDocs/actionlint/history/index/generator and eight actual HTML anchors verified. Root remains below heavy-build8GiB reserve; no build guard lowered, no Gradle/compiler/native/consumer run. Lossless input/log archive follows freeze, not circular verification of future source/commit/security/release.'}
save(DEST/'lead-review.json',review)
sums=''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in sorted(DEST.rglob('*')) if p.is_file())
(DEST/'SHA256SUMS').write_text(sums)
print(json.dumps({'passed':True,'commands':23,'Python_methods':1078,'source_inputs':len(before),'output_anchors':len(outputs),'archive':str(DEST),'root_free_bytes':shutil.disk_usage(ROOT).free},indent=2))
