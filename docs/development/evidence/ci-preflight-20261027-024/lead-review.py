"""Lead independently recounts logs, index/source hold, capacity and actual HTML anchors."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt,gzip,hashlib,json,os,re,shutil,subprocess
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path('/dev/shm/nativecmpkit-preflight-20261027-024');OUT=BASE/'checks'
DEST=ROOT/'docs/development/evidence/ci-preflight-20261027-024'
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
  s=log.read_text();matches=re.findall(r'^Ran (\d+) tests? in [^\n]+$',s,re.M)
  assert len(matches)==1,row['name']
  counts[row['name']]=int(matches[0])
  assert counts[row['name']]==row['unittest_count'] and row['unittest_summary_ok'] and re.search(r'^OK$',s,re.M)
  assert not re.search(r'^(FAILED|ERROR: |FAIL: )',s,re.M)
assert sum(counts.values())==record['python_unittest_executions'] and len(counts)==12
names={row['name'] for row in record['results']}
assert {'cached-diff-whitespace','diff-whitespace','mkdocs-strict','actionlint'} <= names
policy=record['lightweight_resource_policy']
assert policy['root_free_before']>=8*1024**3 and policy['root_free_after']>=8*1024**3
assert policy['heavy_build8GiB_guard_lowered'] is False
assert policy['root_free_before']-policy['root_free_after']<=policy['maximum_root_decrease_bytes']
assert policy['tmpfs_free_after']>=policy['owned_tmpfs_minimum_free_bytes']
outputs=[]
for relative,anchor in [
 ('development/checkpoint-consumer-uikit-20261027/index.html','explicitly-partial-independent-coreio-consumer'),
 ('development/checkpoint-consumer-uikit-20261027/index.html','actual-partial-staging-failure-and-exact-root-build-repair'),
 ('development/native-ui-application-host/index.html','actual-worker-execution-strict-plist-failure-and-owning-manifest-repair'),
 ('development/release-readiness/index.html','gate-ledger'),
 ('development/index.html','working-indexes'),
 ('testing/index.html','explicitly-partial-packaged-coreio-verification'),
 ('development/checkpoint-resource-native-20261027/index.html','real-detached-daemon-leak-and-owning-controlled-fixture-repair'),
 ('development/dependency-lock-witness-20261027/index.html','actual007-complete-selected-runtime-witness'),
 ('decisions/0007-owned-gradle-fixture-processes/index.html','decision'),
 ('development/checkpoint-consumer-metadata-alert-20261027/index.html','actual-uikit-delegate-crash'),
 ('development/checkpoint-consumer-metadata-alert-20261027/index.html','conditional-cache-export-risk-and-owning-boundary'),
 ('development/checkpoint-consumer-metadata-alert-20261027/index.html','efficient-verification-cache-policy'),
 ('development/checkpoint-identity-closures-20261027/index.html','owner-requested-name'),
 ('development/checkpoint-identity-closures-20261027/index.html','owning-fixture-repairs-not-a-silent-green'),
 ('development/checkpoint-identity-closures-20261027/index.html','four-original-findings-accepted-for-scoped-closure'),
 ('decisions/0008-library-display-name/index.html','decision'),
 ('decisions/0008-library-display-name/index.html','verification-and-consequences'),
 ('development/checkpoint-gc-diagnostics-navgeo-20261027/index.html','current-scope-and-verified-issue-state'),
 ('development/checkpoint-gc-diagnostics-navgeo-20261027/index.html','actual-independent-coreio-consumer-success'),
 ('development/checkpoint-gc-diagnostics-navgeo-20261027/index.html','owning-failure-diagnostics-not-a-production-fix'),
 ('development/checkpoint-gc-diagnostics-navgeo-20261027/index.html','android-minimum-policy-and-release-gates'),
 ('development/checkpoint-ci-cache-selection-20261027/index.html','current-closure-and-containment-state'),
 ('development/checkpoint-ci-cache-selection-20261027/index.html','four-runtime-cache-failure-no-library-execution'),
 ('development/checkpoint-ci-cache-selection-20261027/index.html','owning-selection-contract-and-regression-evidence'),
 ('development/checkpoint-ci-cache-selection-20261027/index.html','separate-uikit-setup-failure-and-unchanged-job-retry'),
 ('development/checkpoint-ci-cache-selection-20261027/index.html','next-verification-and-release-boundaries'),
 ('development/checkpoint-native-ui-runtime-20261027/index.html','reviewed-immutable-uikit-runtime-pass'),
 ('development/checkpoint-native-ui-runtime-20261027/index.html','current-small-owning-repair-not-yet-native-verified'),
 ('development/checkpoint-native-ui-runtime-20261027/index.html','additive-completed-navigation-observation'),
 ('development/checkpoint-navigation-geo-acceptance-20261027/index.html','completed-run-and-independent-review'),
 ('development/checkpoint-navigation-geo-acceptance-20261027/index.html','original-issue-acceptance'),
 ('development/checkpoint-navigation-geo-acceptance-20261027/index.html','cache-repair-actually-exercised'),
 ('development/checkpoint-navigation-geo-acceptance-20261027/index.html','current-boundaries-and-next-verification'),
 ('development/checkpoint-navigation-geo-acceptance-20261027/index.html','exact-issue-closure-and-current-uikit-dispatch'),
 ('development/checkpoint-navigation-work-20261027/index.html','actual-library-workallocation-tests-not-a-timing-promise'),
 ('development/checkpoint-navigation-work-20261027/index.html','original-acceptance-and-efficient-next-ci')]:
 p=BASE/'site'/relative;assert p.is_file(),relative
 parser=Anchors();parser.feed(p.read_text());assert anchor in parser.anchors,(relative,anchor)
 outputs.append({'path':relative,'sha256':sha(p),'actual_anchor_verified':anchor})
assert len(outputs)==36 and len({x['path'] for x in outputs})==16
assert not DEST.exists();DEST.mkdir()
for name in ['checks.json',*[row['log'] for row in record['results']]]:
 shutil.copyfile(OUT/name,DEST/name);assert sha(OUT/name)==sha(DEST/name)
shutil.copyfile(BASE/'driver.py',DEST/'driver.py');shutil.copyfile(Path(__file__),DEST/'lead-review.py')
compressed=[]
for name in ['inputs-before.json','inputs-after.json']:
 payload=(OUT/name).read_bytes();z=gzip.compress(payload,mtime=0);p=DEST/(name+'.gz');p.write_bytes(z)
 assert gzip.decompress(p.read_bytes())==payload
 compressed.append({'path':p.name,'gzip_bytes':len(z),'gzip_sha256':sha(p),'uncompressed_bytes':len(payload),'uncompressed_sha256':hashlib.sha256(payload).hexdigest()})
held(before)
assert record['staged_index_sha256_after']==hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)).hexdigest()
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':record['source_revision'],
 'source_input_count':len(before),'all_captured_source_bytes_held_during_run_and_before_and_after_archive':True,
 'staged_index_held_before_and_after_archive':True,'both_staged_and_worktree_whitespace_checks_passed':True,
 'commands':len(record['results']),'python_tooling_methods':sum(counts.values()),'python_tooling_counts':counts,
 'actual_document_output_checks':outputs,'output_anchor_count':len(outputs),'unique_output_files':len({x['path'] for x in outputs}),
 'compressed_input_maps':compressed,'lightweight_resource_policy':policy,
 'library_native_device_or_packaged_consumer_methods_executed':0,'publication_performed':False,'release_readiness_certified':False,
 'archive_is_additive_after_execution_not_self_certified':True,
 'scope':'Source/stage-held finite lightweight preflight. Python counts are recounted from actual logs and overlap prior runs. Strict MkDocs/actionlint/history/index/generator and36 anchors across16 actual HTML files verified. Measured root capacity before/after exceeds8GiB; no heavy-build guard lowered or Gradle/compiler/native/consumer run. Lossless archive follows the freeze and does not circularly certify later source/commit/security/release.'}
save(DEST/'lead-review.json',review)
(DEST/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in sorted(DEST.rglob('*')) if p.is_file()))
print(json.dumps({'passed':True,'commands':len(record['results']),'Python_methods':sum(counts.values()),'source_inputs':len(before),'output_anchors':len(outputs),'unique_output_files':len({x['path'] for x in outputs}),'archive':str(DEST),'root_free_bytes':shutil.disk_usage(ROOT).free},indent=2))
