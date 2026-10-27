"""Separate bounded source/docs checks, NOT a replacement full preflight or heavy build."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt,gzip,hashlib,json,os,shutil,signal,subprocess,time
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent
DOCS=str(ROOT/'build/docs-verification/locked-002/venv/bin/python')
assert os.environ.get('TMPDIR')==str(BASE) and not (BASE/'review.json').exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT,timeout=30).decode().split('\0')
 files={}
 for name in sorted(set(names)-{''}):
  p=ROOT/name
  if p.is_symlink():files[name]={'kind':'symlink','target_sha256':hashlib.sha256(os.readlink(p).encode()).hexdigest()}
  elif p.is_file():
   before=p.stat();h=sha(p);after=p.stat()
   assert (before.st_size,before.st_mtime_ns,before.st_ctime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns,after.st_ino)
   files[name]={'kind':'regular','sha256':h,'bytes':before.st_size}
  elif not p.exists():files[name]={'kind':'deleted'}
  else:raise ValueError('Unreviewed nonregular input')
 return files
def stage():return hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT,timeout=30)).hexdigest()
def stop(p):
 if p.poll() is not None:return
 try:os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:p.wait(timeout=5)
 except subprocess.TimeoutExpired:
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  p.wait(timeout=10)
before=snapshot();index=stage();revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();root_free=shutil.disk_usage(ROOT).free
commands=[('resolution-index',['/usr/bin/python3','-B','scripts/development/validate_resolutions.py','--check']),('staged-whitespace',['git','diff','--cached','--check']),('worktree-whitespace',['git','diff','--check']),('strict-docs',[DOCS,'-B','-m','mkdocs','build','--strict','--site-dir',str(BASE/'site')])]
rows=[]
for name,command in commands:
 log=BASE/(name+'.log');tick=time.monotonic();reason=None
 assert command[0] in {'/usr/bin/python3','git',DOCS}
 with log.open('x') as stream:
  p=subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   while p.poll() is None:
    if time.monotonic()-tick>300:reason='source/docs deadline'
    elif log.stat().st_size>8*1024**2:reason='source/docs log bound'
    elif shutil.disk_usage(BASE).free<2*1024**3:reason='owned tmpfs reserve'
    if reason:stop(p);break
    time.sleep(0.1)
  except BaseException:stop(p);raise
 row={'name':name,'command':command,'exit_code':p.returncode,'stop_reason':reason,'elapsed_seconds':round(time.monotonic()-tick,3),'log':log.name,'log_sha256':sha(log)};rows.append(row)
 print(json.dumps(row),flush=True)
 if p.returncode or reason:break
after=snapshot();assert before==after and index==stage()
assert len(rows)==4 and all(row['exit_code']==0 and row['stop_reason'] is None for row in rows)
full=json.loads((ROOT/'docs/development/evidence/native-license-checkout-20261027/consumer003.json').read_bytes())
assert full['passed'] and full['test_methods']==205
for name,binding in full['source_inputs_after'].items():
 if name.startswith('original-red-probe/'):continue
 assert sha(ROOT/name)==binding['sha256']
class Ids(HTMLParser):
 def __init__(self):super().__init__();self.ids=set()
 def handle_starttag(self,tag,attrs):self.ids.update(v for k,v in attrs if k=='id')
prior=json.loads((ROOT/'docs/development/evidence/ci-preflight-20261027-026/lead-review.json').read_bytes())
requested=[(r['path'],r['actual_anchor_verified']) for r in prior['actual_document_output_checks']]
requested.extend(('development/native-license-supplements/index.html',a) for a in ['owning-contract-and-implementation','executed-regression-and-tooling-verification','byte-preserving-checkout-policy-and-preserved-preflight-failure','fresh-real-collection-and-independent-inspection','issue-state-next-verification-and-release-boundary'])
requested.append(('development/checkpoint-navigation-verified-20261027/index.html','additive-nav-005-exact-closure-observation'))
outputs=[]
for path,anchor in requested:
 p=BASE/'site'/path;parser=Ids();parser.feed(p.read_text());assert anchor in parser.ids,(path,anchor)
 outputs.append({'path':path,'anchor':anchor,'sha256':sha(p)})
assert len(outputs)==52 and len({row['path'] for row in outputs})==20
record={'passed':True,'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':revision,'dirty_worktree':True,'source_stage_input_count':len(before),'source_and_stage_held':True,'commands':rows,'actual_output_anchors':outputs,'unchanged_source_held_python205_receipt_rechecked_not_rerun':True,'root_free_before':root_free,'root_free_after':shutil.disk_usage(ROOT).free,'owned_tmpfs_reserve_bytes':2*1024**3,'full_preflight027_and028_remain_failed':True,'8GiB_local_heavy_build_guard_not_lowered':True,'zero_new_native_library_consumer_Gradle_or_publication_execution':True,'scope':'Four separate bounded lightweight source/docs checks at below-reserve measured host capacity, outputs only in owned tmpfs. Not a full23-command preflight, a resource-policy waiver, new205 methods, immutable candidate or legal/security/release pass; complete verification requires hosted CI.'}
(BASE/'review.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
for name,data in [('inputs-before.json.gz',before),('inputs-after.json.gz',after)]:
 (BASE/name).write_bytes(gzip.compress((json.dumps(data,indent=2,sort_keys=True)+'\n').encode(),mtime=0))
print(json.dumps({'passed':True,'source_stage_inputs':len(before),'anchors':len(outputs),'actual_html_files':20,'not_full_preflight':True},indent=2),flush=True)
