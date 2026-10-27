"""Inspect additive archive/two docs only, actual output and staged source hold."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt,gzip,hashlib,json,os,re,shutil,signal,subprocess,time
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent
PREFLIGHT=ROOT/'docs/development/evidence/ci-preflight-20261027-023'
PYTHON='/usr/bin/python3';DOCS=str(ROOT/'build/docs-verification/locked-002/venv/bin/python')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 result={}
 raw=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT,timeout=30)
 for name in sorted(set(raw.decode().split('\0'))-{''}):
  p=ROOT/name
  if p.is_symlink():result[name]={'kind':'symlink','target_sha256':hashlib.sha256(os.readlink(p).encode()).hexdigest()}
  elif p.is_file():result[name]={'kind':'regular','sha256':sha(p),'bytes':p.stat().st_size}
  elif not p.exists():result[name]={'kind':'deleted'}
  else:raise AssertionError('Nonregular input')
 return result
def stage():return hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)).hexdigest()
def save(name,x):
 with (BASE/name).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
before=json.loads(gzip.decompress((PREFLIGHT/'inputs-before.json.gz').read_bytes()))
assert before==json.loads(gzip.decompress((PREFLIGHT/'inputs-after.json.gz').read_bytes()))
prior=json.loads((PREFLIGHT/'lead-review.json').read_bytes());assert prior['passed'] and prior['python_tooling_methods']==1223 and prior['commands']==23
allowed=json.loads((BASE/'allowed-docs.json').read_bytes())
for name in allowed:assert sha(BASE/'old-docs'/name)==before[name]['sha256']
current=snapshot();changed=sorted(n for n in before if before[n]!=current.get(n));added=sorted(set(current)-set(before))
expected=sorted(p.relative_to(ROOT).as_posix() for p in PREFLIGHT.rglob('*') if p.is_file())
assert changed==sorted(allowed) and added==expected
for name in expected:
 assert not (ROOT/name).is_symlink() and current[name]['kind']=='regular'
for line in (PREFLIGHT/'SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1);assert sha(PREFLIGHT/name)==digest
assert (ROOT/'docs/development/checkpoint-navigation-geo-acceptance-20261027.md').read_bytes().startswith((BASE/'old-docs/docs/development/checkpoint-navigation-geo-acceptance-20261027.md').read_bytes())
old=(BASE/'old-docs/AGENTS.md').read_bytes();new=(ROOT/'AGENTS.md').read_bytes();marker=b'The [staged source-held preflight023]'
start=new.index(marker);end=new.index(b'Current [cache-selection/setup-failure checkpoint]',start)
assert new[:start]+new[end:]==old
old_ui=(BASE/'old-docs/docs/development/checkpoint-native-ui-runtime-20261027.md').read_bytes()
new_ui=(ROOT/'docs/development/checkpoint-native-ui-runtime-20261027.md').read_bytes()
old_fragment=b'closed issues. Still **nine readback-verified closures** (#15/#16/#41/#42/#123/\n#136/#146/#155/#171); no new closure here. Original164 findings/requirements and'
new_fragment=b'closed issues. Still **nine readback-verified closures**\n(#15/#16/#41/#42/#123/#136/#146/#155/#171); no new closure here. Original164 findings/requirements and'
assert old_ui.count(old_fragment)==1 and new_ui==old_ui.replace(old_fragment,new_fragment)
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();index=stage();root_free=shutil.disk_usage(ROOT).free
assert root_free>=8*1024**3 and shutil.disk_usage(BASE).free>=2*1024**3
commands=[('resolution-index',[PYTHON,'-B','scripts/development/validate_resolutions.py','--check']),('staged-whitespace',['git','diff','--cached','--check']),('worktree-whitespace',['git','diff','--check']),('strict-docs',[DOCS,'-B','-m','mkdocs','build','--strict','--site-dir',str(BASE/'site')])]
results=[]
def stop(p):
 if p.poll() is not None:return
 try:os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:p.wait(timeout=5)
 except subprocess.TimeoutExpired:
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  p.wait(timeout=10)
for name,command in commands:
 assert command[0] in {PYTHON,DOCS,'git'}
 log=BASE/(name+'.log');started=time.monotonic();reason=None
 with log.open('x') as output:
  p=subprocess.Popen(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   while p.poll() is None:
    if time.monotonic()-started>300:reason='finite deadline'
    elif log.stat().st_size>8*1024**2:reason='log bound'
    elif shutil.disk_usage(BASE).free<2*1024**3:reason='owned tmpfs reserve'
    elif shutil.disk_usage(ROOT).free<root_free-128*1024**2:reason='lightweight root-write bound'
    if reason:stop(p);break
    time.sleep(0.1)
  except BaseException:stop(p);raise
 row={'name':name,'command':command,'exit_code':p.returncode,'stop_reason':reason,'elapsed_seconds':round(time.monotonic()-started,3),'log':log.name,'sha256':sha(log)};results.append(row)
 print(json.dumps(row),flush=True)
 if p.returncode or reason:break
assert len(results)==4 and all(r['exit_code']==0 and r['stop_reason'] is None for r in results)
assert current==snapshot() and index==stage() and revision==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
class Anchors(HTMLParser):
 def __init__(self):super().__init__();self.values=set()
 def handle_starttag(self,tag,attrs):self.values.update(v for k,v in attrs if k=='id')
outputs=[]
for old in prior['actual_document_output_checks']:
 p=BASE/'site'/old['path'];assert p.is_file();parser=Anchors();parser.feed(p.read_text());assert old['actual_anchor_verified'] in parser.values
 outputs.append({'path':old['path'],'anchor':old['actual_anchor_verified'],'sha256':sha(p)})
assert len(outputs)==33 and len({x['path'] for x in outputs})==15
save('review.json',{'passed':True,'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':revision,'old_preflight_inputs':len(before),'current_captured_inputs':len(current),'changed_prior_inputs':changed,'additive_archive_files':expected,'additive_archive_count':len(expected),'all_other_executable_test_and_workflow_inputs_unchanged':True,'source_and_staged_index_held':True,'checks':results,'actual_output_anchors':outputs,'zero_library_native_Gradle_consumer_or_cache_action_executions':True,'release_readiness_certified':False,'publication_performed':False,'root_free_before':root_free,'root_free_after':shutil.disk_usage(ROOT).free,'scope':'Only two additive documentation updates, one exact accidental-heading formatting repair and the lossless preflight archive follow the prior17211-input freeze. All other captured/executable/test/workflow bytes unchanged. Four bounded lightweight checks and33 anchors/15 actual HTML outputs pass; not circular certification of the next immutable commit, runtime/dependency trust or release.'})
print(json.dumps({'passed':True,'archive_files':len(expected),'captured_inputs':len(current),'anchors':len(outputs),'review':str(BASE/'review.json')},indent=2),flush=True)
