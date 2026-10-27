"""Additive documentation/evidence-only delivery guard after preflight019; no runtime pass."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt,hashlib,json,os,subprocess,time
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path('/dev/shm/nativecmpkit-preflight-20261027-019')
OUT=ROOT/'docs/development/evidence/ci-preflight-20261027-019/delivery-addendum'
DOCS=str(ROOT/'build/docs-verification/locked-002/venv/bin/python')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def index():return hashlib.sha256(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)).hexdigest()
assert not OUT.exists();OUT.mkdir()
before=json.loads((BASE/'checks/inputs-before.json').read_text()); changed=[]
for name,row in before.items():
 if row['kind']=='regular' and sha(ROOT/name)!=row['sha256']:changed.append(name)
assert changed==['AGENTS.md','docs/development/checkpoint-identity-closures-20261027.md']
doc_hashes={p:sha(ROOT/p) for p in changed};stage=index();results=[]
commands=[('resolutions',['/usr/bin/python3','-B','scripts/development/validate_resolutions.py','--check']),
 ('mkdocs-strict',[DOCS,'-B','-m','mkdocs','build','--strict','--site-dir',str(BASE/'delivery-site')]),
 ('actionlint',['/tmp/nativecmpkit-actionlint-1.7.12/actionlint','.github/workflows/gradle.yml','.github/workflows/build-native-libs.yml']),
 ('cached-whitespace',['git','diff','--cached','--check']),('worktree-whitespace',['git','diff','--check'])]
for name,argv in commands:
 start=time.monotonic();log=OUT/(name+'.log')
 with log.open('x') as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=300,env={**os.environ,'TMPDIR':str(BASE)})
 results.append({'name':name,'command':argv,'exit_code':r.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'log_sha256':sha(log)})
 assert r.returncode==0,name
assert index()==stage and {p:sha(ROOT/p) for p in changed}==doc_hashes
for name,row in before.items():
 if row['kind']=='regular' and name not in changed:assert sha(ROOT/name)==row['sha256'],name
class A(HTMLParser):
 def __init__(self):super().__init__();self.ids=set()
 def handle_starttag(self,t,attrs):self.ids.update(v for k,v in attrs if k=='id')
p=BASE/'delivery-site/development/checkpoint-identity-closures-20261027/index.html';a=A();a.feed(p.read_text());assert 'source-held-staged-preflight019' in a.ids
record={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'source_inputs_compared_to_preflight019':len(before),'changed_after_preflight019':changed,'changed_docs_sha256':doc_hashes,'other_captured_inputs_unchanged':True,
 'staged_index_sha256_before_and_after':stage,'checks':results,'new_html_output':{'path':str(p.relative_to(BASE/'delivery-site')),'sha256':sha(p),'anchor':'source-held-staged-preflight019'},
 'native_library_or_packaged_consumer_methods_executed':0,'publication_performed':False,'release_readiness_certified':False,
 'scope':'Additive docs/evidence readback after019; only two documented Markdown additions differ from its captured inputs. The existing1137 test executions remain scoped to their unchanged owning inputs, not rerun here. This addendum follows the stage-held checks; it is not circular certification of later evidence/commit.'}
with (OUT/'receipt.json').open('x') as f:json.dump(record,f,indent=2,sort_keys=True);f.write('\n')
(OUT/'driver.py').write_bytes(Path(__file__).read_bytes())
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.is_file()))
print(json.dumps({'passed':True,'checks':len(results),'changed_inputs':changed,'archive':str(OUT)},indent=2))
