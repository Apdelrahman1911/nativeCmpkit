"""Source-bound local strict MkDocs rerun after the owning link correction."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import datetime as dt,hashlib,json,os,re,subprocess,sys
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/docs-link-repair-001';SITE=OUT/'site'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests
DOCS=ROOT/'build/docs-verification/locked-002/venv/bin/python'
assert not SITE.exists() and not (OUT/'docs.json').exists()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def snapshot():
 files={}
 raw=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT)
 for n in sorted(set(raw.decode().split('\0'))-{''}):
  p=ROOT/n
  if p.is_symlink():files[n]={'kind':'symlink','target_sha256':hashlib.sha256(os.readlink(p).encode()).hexdigest()}
  elif p.is_file():files[n]={'kind':'regular','sha256':sha(p),'bytes':p.stat().st_size}
  elif not p.exists():files[n]={'kind':'deleted'}
  else:raise ValueError('Nonregular input')
 return files
def put(n,x):
 with (OUT/n).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
class Html(HTMLParser):
 def __init__(self):super().__init__();self.hrefs=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if 'id' in d:self.ids.add(d['id'])
  if tag=='a' and 'href' in d:self.hrefs.append(d['href'])
def parse(p):
 h=Html();h.feed(p.read_text());return h
before=snapshot();put('docs-inputs-before.json',before);revision=library_tests.git_revision(ROOT)
cmd=[str(DOCS),'-B','-m','mkdocs','build','--strict','--site-dir',str(SITE)]
start=dt.datetime.now(dt.timezone.utc).isoformat();execution=library_tests.execute(ROOT,cmd,OUT/'mkdocs-strict.log',300,8192);end=dt.datetime.now(dt.timezone.utc).isoformat()
log=(OUT/'mkdocs-strict.log').read_text(errors='replace');checks=[]
if execution['exit_code']==0:
 for page,relative in [('development/status/index.html','migration/issue-map.json'),('development/status/index.html','roadmap/backlog.json'),('development/upstream-status/index.html','migration/issue-map.json')]:
  p=SITE/page;target=(SITE/relative).resolve();links=[]
  for href in parse(p).hrefs:
   u=urlsplit(href)
   if not u.scheme and not u.netloc and (p.parent/unquote(u.path)).resolve()==target:links.append(href)
  checks.append({'page':page,'target':relative,'matching_hrefs':links,'passed':bool(links) and target.is_file()})
 anchor='current-source-acquisition-proposal-not-scheduled-or-executed';target=SITE/'development/build007-implementation-plan/index.html';ids=parse(target).ids
 for page in ['development/BUILD/index.html','development/dependency-integrity/index.html']:
  p=SITE/page;links=[]
  for href in parse(p).hrefs:
   u=urlsplit(href);candidate=(p.parent/unquote(u.path)).resolve()
   if candidate.is_dir():candidate=candidate/'index.html'
   if not u.scheme and not u.netloc and candidate==target.resolve() and u.fragment==anchor:links.append(href)
  checks.append({'page':page,'target':'development/build007-implementation-plan/index.html#'+anchor,'matching_hrefs':links,'passed':bool(links) and anchor in ids})
after=snapshot();put('docs-inputs-after.json',after)
changes=sorted(p for p in before.keys()|after.keys() if before.get(p)!=after.get(p))
record={'schema_version':1,'started_utc':start,'finished_utc':end,'source_revision':revision,'source_revision_after':library_tests.git_revision(ROOT),'dirty_worktree':True,'command':cmd,'execution':execution,'input_count':len(before),'changed_inputs':changes,'log_sha256':sha(OUT/'mkdocs-strict.log'),'driver_sha256':sha(Path(__file__)),'python_executable_sha256':sha(DOCS),'generated_target_checks':checks,'warning_lines':[l for l in log.splitlines() if re.match(r'^(WARNING|ERROR)\s+-',l)],'unresolved_anchor_lines':[l for l in log.splitlines() if 'does not contain an anchor' in l],'passed':execution['exit_code']==0 and len(checks)==5 and all(c['passed'] for c in checks) and not changes and library_tests.git_revision(ROOT)==revision,'scope':'Local strict documentation build and five concrete generated file/anchor checks. No library tests, network publication, deployment, test-suppression or MkDocs policy relaxation. Original tooling005 failure remains failed.'}
put('docs.json',record)
print(json.dumps({k:record[k] for k in ['execution','input_count','changed_inputs','generated_target_checks','warning_lines','unresolved_anchor_lines','passed']},indent=2))
sys.exit(0 if record['passed'] else 1)
