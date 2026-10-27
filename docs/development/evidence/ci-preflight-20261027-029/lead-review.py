"""Read-only lightweight freeze/log/HTML recount followed by lossless additive archive."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt,gzip,hashlib,json,os,re,shutil,subprocess
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent;OUT=BASE/'checks';DEST=ROOT/'docs/development/evidence/ci-preflight-20261027-029'
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
r=json.loads((OUT/'checks.json').read_bytes());before=json.loads((OUT/'inputs-before.json').read_bytes());after=json.loads((OUT/'inputs-after.json').read_bytes())
assert r['passed'] and r['commands_requested']==r['commands_completed']==len(r['results'])==23
assert before==after and not r['changed_inputs'] and len(before)==r['source_input_count']==18317
assert r['driver_sha256']==sha(BASE/'driver.py')
assert r['source_revision']==r['source_revision_after']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert r['staged_index_sha256_before']==r['staged_index_sha256_after']==hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)).hexdigest()
held(before);counts={}
for row in r['results']:
    assert row['execution']['exit_code']==0 and not row['execution'].get('stop_reason'),row['name']
    log=OUT/row['log'];assert sha(log)==row['log_sha256']
    if row['unittest_count'] is not None:
        text=log.read_text();matches=re.findall(r'^Ran (\d+) tests? in [^\n]+$',text,re.M)
        assert len(matches)==1;count=int(matches[0]);counts[row['name']]=count
        assert count==row['unittest_count'] and row['unittest_summary_ok'] and re.search(r'^OK$',text,re.M)
        assert not re.search(r'^(FAILED|ERROR: |FAIL: )',text,re.M)
assert sum(counts.values())==r['python_unittest_executions']==1286 and len(counts)==12
policy=r['lightweight_resource_policy'];assert policy['heavy_build8GiB_guard_lowered'] is False
assert policy['root_free_after']>=policy['root_free_before']-128*1024**2 and policy['maximum_root_decrease_bytes']==128*1024**2
assert policy['owned_tmpfs_minimum_free_bytes']==2*1024**3 and policy['tmpfs_free_after']>=2*1024**3
assert r['library_or_native_or_packaged_consumer_methods_executed']==0
assert not r['hosted_ci_or_publication_performed'] and policy['finite_command_allowlist'] and policy['fail_fast_on_any_nonzero']
# Recheck actual newly built output, never copy old output hashes/outcomes.
previous=json.loads((ROOT/'docs/development/evidence/ci-preflight-20261027-026/lead-review.json').read_bytes())
targets=[(v['path'],v['actual_anchor_verified']) for v in previous['actual_document_output_checks']]
page='development/checkpoint-windows-consumer-nav-20261027/index.html'
targets += [(page,a) for a in ('current-upstream-reconciliation','full-authored-windows-desktop-suite','fresh-independent-coreio-packaged-consumer','nav-006-emptynonempty-start-policy-regression','owning-ci-sdk-receipt-repair','next-verification-and-release-boundaries')]
targets += [('development/upstream-refresh-20261027T193135Z/index.html','current-upstream-refresh-20261027t193135z'),('development/native-license-supplements/index.html','additive-fresh-immutable-packaged-notice-verification')]
outputs=[]
for name,anchor in targets:
    p=BASE/'site'/name;assert p.is_file(),name
    parser=Anchors();parser.feed(p.read_text());assert anchor in parser.anchors,(name,anchor)
    outputs.append({'path':name,'sha256':sha(p),'actual_anchor_verified':anchor})
assert len(outputs)==54 and len({v['path'] for v in outputs})==22
assert not DEST.exists();DEST.mkdir()
for name in ('checks.json',*[row['log'] for row in r['results']]):shutil.copyfile(OUT/name,DEST/name);assert sha(OUT/name)==sha(DEST/name)
shutil.copyfile(BASE/'driver.py',DEST/'driver.py');shutil.copyfile(Path(__file__),DEST/'lead-review.py')
compressed=[]
for name in ('inputs-before.json','inputs-after.json'):
    raw=(OUT/name).read_bytes();p=DEST/(name+'.gz');p.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(p.read_bytes())==raw
    compressed.append({'path':p.name,'gzip_bytes':p.stat().st_size,'gzip_sha256':sha(p),'uncompressed_bytes':len(raw),'uncompressed_sha256':hashlib.sha256(raw).hexdigest()})
held(before);assert r['staged_index_sha256_after']==hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)).hexdigest()
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':r['source_revision'],'source_input_count':len(before),'all_captured_inputs_held_during_run_and_archival':True,'staged_index_held':True,'commands':23,'python_tooling_methods':1286,'python_tooling_counts':counts,'actual_document_output_checks':outputs,'output_anchor_count':54,'unique_output_files':22,'compressed_input_maps':compressed,'lightweight_resource_policy':policy,'local_heavy_build_capacity_certified':False,'library_native_device_or_packaged_consumer_methods_executed':0,'publication_performed':False,'release_readiness_certified':False,'archive_is_additive_after_execution_not_self_certified':True,'scope':'Finite source/stage-held lightweight Python/Git/history/index/generator/strict MkDocs/actionlint evidence.1286 Python methods overlap focused/prior runs, not library/native passes.54 actual anchors across22 generated outputs rechecked. Root capacity remains below8GiB: no heavy local builds; measured128MiB root-decrease/2GiB owned tmpfs guards held. No heavy guard changed. Archive/subsequent documentation deltas do not circularly certify themselves/later commits or release readiness.'}
save(DEST/'lead-review.json',review)
(DEST/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in sorted(DEST.rglob('*')) if p.is_file()))
print(json.dumps({'passed':True,'commands':23,'Python_methods':1286,'held_inputs':18317,'anchors':54,'HTML_outputs':22,'archive':str(DEST),'root_free_bytes':shutil.disk_usage(ROOT).free},indent=2))
