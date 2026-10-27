"""Read-only source-held preflight/archive review; no tests, native or packages."""
from pathlib import Path
from html.parser import HTMLParser
import ast, gzip, hashlib, json, os, re, shutil, subprocess, sys
ROOT=Path('/root/projects/nativeCmpKit'); BASE=Path(__file__).resolve().parent; SRC=BASE/'checks'; SITE=BASE/'site'
OUT=ROOT/'docs/development/evidence/ci-preflight-20261027-015'
assert not OUT.exists()
sys.path.insert(0,str(ROOT/'scripts/ci')); import library_tests as lt
checks=json.loads((SRC/'checks.json').read_bytes());before=json.loads((SRC/'inputs-before.json').read_bytes());after=json.loads((SRC/'inputs-after.json').read_bytes())
assert before==after and checks['passed'] and checks['changed_inputs']==[] and checks['commands_requested']==checks['commands_completed']==23
assert checks['source_revision']==checks['source_revision_after']==lt.git_revision(ROOT)
assert checks['python_unittest_executions']==1014 and checks['library_or_native_or_consumer_methods_executed']==0
assert checks['driver_sha256']==lt.sha256(BASE/'driver.py')
def recheck():
 for n,v in before.items():
  p=ROOT/n
  if v['kind']=='regular':assert p.is_file() and not p.is_symlink() and p.stat().st_size==v['bytes'] and lt.sha256(p)==v['sha256']
  elif v['kind']=='deleted':assert not p.exists()
  elif v['kind']=='symlink':assert p.is_symlink() and hashlib.sha256(os.readlink(p).encode()).hexdigest()==v['target_sha256']
  else:raise AssertionError('unknown snapshot entry')
recheck();counts={}
manifest_path=ROOT/'scripts/dependencies/checkpoint-offline-010.json'
manifest=json.loads(manifest_path.read_bytes())
assert lt.sha256(manifest_path)=='68f51a03f624378949c3669ebec4ce78dcb41d27cb76e5c6afd7c31b097185c6'
assert manifest['previous_checkpoint_sha256']==lt.sha256(ROOT/manifest['previous_checkpoint'])=='08a00d96d05d14f8dbb188a6ddbd532a3785a5955907dcbc966e5522c6abaa8e'
assert manifest['checkpoint']=='010' and len(manifest['input_files_sha256'])==10
assert all(lt.sha256(ROOT/n)==h for n,h in manifest['input_files_sha256'].items())
base='a19de305048469ed641896382aec98051f753a81'
parser='scripts/dependencies/gradle_process.py'
original=subprocess.check_output(['git','show',base+':'+parser],cwd=ROOT)
assert ast.dump(ast.parse(original),include_attributes=False)==ast.dump(ast.parse((ROOT/parser).read_bytes()),include_attributes=False)
unchanged=sorted(n for n in manifest['input_files_sha256'] if n not in ['scripts/dependencies/README.md',parser])
assert len(unchanged)==8
assert all((ROOT/n).read_bytes()==subprocess.check_output(['git','show',base+':'+n],cwd=ROOT) for n in unchanged)
checkpoint_binding={'current_manifest_sha256':lt.sha256(manifest_path),'predecessor009_byte_hash_preserved':True,'entire_shared_parser_AST_unchanged_from':base,'eight_owner_fixture_init_core_inputs_unchanged':unchanged,'prior_actual009_invocations_reused_only_at_original_scope':True,'fresh010_Gradle_invocations':0}
assert checks['results'][-2]['name']=='cached-diff-whitespace' and checks['results'][-1]['name']=='diff-whitespace'

for r in checks['results']:
 assert r['execution']['exit_code']==0 and not r['execution'].get('stop_reason') and r['log_sha256']==lt.sha256(SRC/r['log'])
 s=(SRC/r['log']).read_text()
 if r['unittest_count'] is not None:
  assert re.search(r'^Ran '+str(r['unittest_count'])+r' tests? in ',s,re.M) and re.search(r'^OK$',s,re.M)
  cases=re.findall(r'^test_[^\n]+ \.\.\. ok$',s,re.M)
  assert len(cases)==r['unittest_count'];counts[r['name']]=len(cases)
assert sum(counts.values())==1014 and counts['ci']==226 and counts['dependency-owner']==61 and counts['dependency-observer']==148 and counts['dependency-core']==171
class IDs(HTMLParser):
 def __init__(self):super().__init__();self.ids=set()
 def handle_starttag(self,tag,attrs):self.ids.update(v for k,v in attrs if k=='id')
targets=[('development/native-ui-application-host/index.html','exact-native-object-identity-after-the-persistent-startup-timeout'),('development/checkpoint-resource-native-20261027/index.html','real-detached-daemon-leak-and-owning-controlled-fixture-repair'),('development/dependency-lock-witness-20261027/index.html','actual007-complete-selected-runtime-witness'),('testing/index.html','exact-native-ownership-and-controlled-gradle-cleanup-follow-up'),('development/release-readiness/index.html','gate-ledger'),('decisions/0007-owned-gradle-fixture-processes/index.html','decision')]
html=[]
for n,anchor in targets:
 p=SITE/n;assert p.is_file();parser=IDs();parser.feed(p.read_text());assert anchor in parser.ids
 html.append({'path':n,'actual_anchor_verified':anchor,'sha256':lt.sha256(p)})
OUT.mkdir();compressed=[]
for p in sorted(SRC.iterdir()):
 if not p.is_file():raise AssertionError('unexpected preflight child')
 if p.name in ['inputs-before.json','inputs-after.json']:
  raw=p.read_bytes();compressed_raw=gzip.compress(raw,compresslevel=9,mtime=0);target=OUT/(p.name+'.gz');target.write_bytes(compressed_raw);assert gzip.decompress(target.read_bytes())==raw
  compressed.append({'path':target.name,'uncompressed_bytes':len(raw),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),'gzip_bytes':len(compressed_raw),'gzip_sha256':lt.sha256(target)})
 else:
  target=OUT/p.name;target.write_bytes(p.read_bytes());assert target.read_bytes()==p.read_bytes()
(OUT/'driver.py').write_bytes((BASE/'driver.py').read_bytes());(OUT/'review.py').write_bytes(Path(__file__).read_bytes())
recheck()
record={'reviewed_utc':lt.utc_now(),'source_revision':lt.git_revision(ROOT),'dirty_development_snapshot':True,'passed':True,'source_input_count':len(before),'all_captured_inputs_held_during_execution_and_rechecked_before_and_after_archive':True,'archive_is_additive_after_execution_not_self_certified':True,'checkpoint010_binding_review':checkpoint_binding,'both_staged_and_worktree_whitespace_checks_passed':True,'commands':23,'python_tooling_methods':1014,'python_tooling_counts':counts,'actual_document_output_checks':html,'compressed_input_maps':compressed,'reserve_bytes':8192*1024**2,'root_free_bytes_after_archive':shutil.disk_usage(ROOT).free,'library_native_device_or_packaged_consumer_methods_executed':0,'publication_performed':False,'release_readiness_certified':False,'scope':'Source-held full bounded offline tooling/history/migration/audit/index/generator checks and strict local MkDocs/actionlint.1014 Python methods overlap previous scoped runs; none are new Kotlin/native/strict consumer executions.6 actual HTML targets/anchors reviewed. Both staged and worktree whitespace checks pass after intended sources were staged. Ten-input010 manifest bound; complete parser AST/eight core implementations unchanged from local predecessor, not fresh actual010 runtime coverage. Input maps losslessly compressed; this archive and later docs/commit follow the freeze and are not circularly verified.'}
assert record['root_free_bytes_after_archive']>=record['reserve_bytes']
(OUT/'lead-review.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
(OUT/'SHA256SUMS').write_text(''.join(f'{lt.sha256(p)}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps({k:record[k] for k in ['commands','python_tooling_methods','python_tooling_counts','source_input_count','root_free_bytes_after_archive']},indent=2))
