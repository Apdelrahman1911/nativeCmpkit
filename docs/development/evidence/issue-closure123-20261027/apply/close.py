"""Only original UI-009, default read-only, one comment and state-only closure."""
from pathlib import Path
import argparse,datetime as dt,gzip,hashlib,json,subprocess
ROOT=Path('/root/projects/nativeCmpKit')
REPO='Apdelrahman1911/nativeCmpkit';REF='development/preview-hardening'
SHA='202059090bbbf896d07d38a3441cf21c8888c63b';MAIN='94d2492e99d5cbc060409d94d9f88febd06222d5'
BASE=Path('/dev/shm/nativecmpkit-issue-closure123-20261027')
ACCEPT='docs/development/evidence/timepicker-original-acceptance-20261027/lead-timepicker-state-acceptance.json'
PREFLIGHT='docs/development/evidence/ci-preflight-20261027-021/lead-review.json'
LINKS='docs/development/evidence/postfreeze021-links-20261027-final/review.json'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
OUT=BASE/('apply' if args.apply else 'dry-run');OUT.mkdir(parents=True,exist_ok=False)
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,x):
 with (OUT/name).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def read(path,name,paginate=False):
 cmd=['gh','api','repos/'+REPO+'/'+path]
 if paginate:cmd+=['--paginate']
 r=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=120)
 (OUT/(name+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==0,'Read-only destination readback failed; no implicit retry'
 suffix='.json.gz' if len(r.stdout)>100000 else '.json'
 (OUT/(name+suffix)).write_bytes(gzip.compress(r.stdout,mtime=0) if suffix.endswith('.gz') else r.stdout)
 if paginate:
  # gh2.45 predates --slurp: --paginate emits a JSON stream, not one array.
  decoder=json.JSONDecoder();text=r.stdout.decode();position=0;pages=[]
  while position<len(text):
   while position<len(text) and text[position].isspace():position+=1
   if position==len(text):break
   page,position=decoder.raw_decode(text,position);assert isinstance(page,list);pages.append(page)
  items=[item for page in pages for item in page]
  assert len({item['id'] for item in items})==len(items),'Duplicate paginated GitHub identities'
  return items
 return json.loads(r.stdout)
def mutate(path,method,name,payload):
 save(name+'-payload.json',payload);started=utc()
 try:
  r=subprocess.run(['gh','api','repos/'+REPO+'/'+path,'--method',method,'--input',str(OUT/(name+'-payload.json'))],cwd=ROOT,capture_output=True,timeout=120)
  (OUT/(name+'.stdout')).write_bytes(r.stdout);(OUT/(name+'.stderr')).write_bytes(r.stderr)
  status=r.returncode
 except subprocess.TimeoutExpired as e:
  (OUT/(name+'.stdout')).write_bytes(e.stdout or b'');(OUT/(name+'.stderr')).write_bytes(e.stderr or b'');status=None
 save(name+'-request.json',{'method':method,'endpoint':'repos/'+REPO+'/'+path,'invocations':1,'started_utc':started,'finished_utc':utc(),'exit_code':status,'automatic_retry':False})
 return status

def preserve(issue):
 return {'title':issue['title'],'body':issue['body'],'labels':sorted(issue['labels'],key=lambda x:x['id'])}

def local():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==SHA
 assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==REF
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
 assert subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip()=='https://github.com/'+REPO+'.git'
 for p in [ACCEPT,PREFLIGHT]:assert (ROOT/p).read_bytes()==subprocess.check_output(['git','show',SHA+':'+p],cwd=ROOT)
local();started=utc()
assert read('branches/'+REF,'development-before')['commit']['sha']==SHA
assert read('branches/main','main-before')['commit']['sha']==MAIN
assert read('pages','pages-before')['status'] is None
assert read('releases?per_page=100','releases-before')==[]
for name in (ACCEPT,PREFLIGHT,LINKS):assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',SHA+':'+name],cwd=ROOT)
review=json.loads((ROOT/ACCEPT).read_bytes());preflight=json.loads((ROOT/PREFLIGHT).read_bytes());links=json.loads((ROOT/LINKS).read_bytes())
assert preflight['passed'] and preflight['commands']==23 and preflight['python_tooling_methods']==1206
assert links['passed'] and links['all_other_executable_test_and_workflow_inputs_unchanged']
assert review['id']=='UI-009' and review['issue_number']==123 and review['owning_inputs_held_during_review']
assert review['immutable_runtime_revision']=='6eb7c66eb01b390353100c63882cd102846c7b8d'
assert {s['slot'] for s in review['reviewed_immutable_runtime_scopes']}=={'desktop-linux-x64','android-host','desktop-macos-arm64','ios-iphone'}
assert all(s['owning_scope_counts']['passed']==s['owning_scope_counts']['executed']==3 and s['owning_scope_counts']['skipped']==0 for s in review['reviewed_immutable_runtime_scopes'])
for name,digest in review['owning_current_input_hashes_identical_to_runtime'].items():assert sha((ROOT/name).read_bytes())==digest,name
ledger=json.loads((ROOT/'docs/development/resolutions/UI-native.json').read_bytes())
assert next(r for r in ledger if r['id']=='UI-009')['status']=='verified'
issue=read('issues/123','issue-before')
original=json.loads((ROOT/'docs/development/evidence/timepicker-original-acceptance-20261027/issue-123-before.json').read_bytes())
assert preserve(issue)==preserve(original) and issue['state']=='open' and 'pull_request' not in issue
assert sha(issue['body'].encode())==review['issue_body_sha256_before'] and sha(issue['title'].encode())==review['issue_title_sha256_before']
assert sorted(l['name'] for l in issue['labels'])==review['issue_labels_before']
marker='<!-- nativecmpkit-resolution:UI-009:20261027-original-acceptance -->'
comments=read('issues/123/comments?per_page=100','comments-before',True)
assert not any(marker in (c.get('body') or '') for c in comments),'Existing marker must be reconciled; no duplicate POST'
text=(BASE/'comment.md').read_text()
assert text.startswith(marker)
for name in (ACCEPT,PREFLIGHT,LINKS):assert 'https://github.com/'+REPO+'/blob/'+SHA+'/'+name in text
save('planned-comment.json',{'body':text,'marker':marker})
save('preflight.json',{'passed':True,'source_revision':SHA,'main_preserved':MAIN,'issue':123,'id':'UI-009','dry_run':not args.apply,'original_body_title_labels_unchanged':True,'duplicate_markers':0,'publication_performed':False})
result=None
if args.apply:
 fresh=read('issues/123','issue-immediate-before');assert preserve(fresh)==preserve(issue) and fresh['state']=='open'
 posted=mutate('issues/123/comments','POST','comment',{'body':text})
 after=read('issues/123/comments?per_page=100','comments-after',True);found=[c for c in after if marker in (c.get('body') or '')]
 assert len(found)==1 and found[0]['body']==text,'Uncertain/rejected POST; no automatic retry/closure'
 comment=read('issues/comments/'+str(found[0]['id']),'comment-readback');assert comment['body']==text and comment['id']==found[0]['id']
 if posted==0:assert json.loads((OUT/'comment.stdout').read_bytes())['id']==comment['id']
 before_close=read('issues/123','issue-before-close');assert preserve(before_close)==preserve(issue) and before_close['state']=='open'
 patched=mutate('issues/123','PATCH','close',{'state':'closed','state_reason':'completed'})
 final=read('issues/123','issue-after');assert final['state']=='closed' and final['state_reason']=='completed' and preserve(final)==preserve(issue)
 final_comment=read('issues/comments/'+str(comment['id']),'comment-final-readback');assert final_comment['body']==text and final_comment['id']==comment['id']
 result={'id':'UI-009','number':123,'url':final['html_url'],'state':final['state'],'state_reason':final['state_reason'],'closed_at':final['closed_at'],'comment_id':comment['id'],'comment_url':comment['html_url'],'comment_sha256':sha(text.encode()),'comment_POST_invocations':1,'state_PATCH_invocations':1,'POST_exit_code':posted,'PATCH_exit_code':patched,'exact_readback_verified':True,'body_title_labels_unchanged':True}
assert read('branches/main','main-after')['commit']['sha']==MAIN
assert read('branches/'+REF,'development-after')['commit']['sha']==SHA
local()
save('receipt.json',{'passed':True,'dry_run':not args.apply,'started_utc':started,'finished_utc':utc(),'source_revision':SHA,'main_preserved':MAIN,'result':result,'issues_closed':int(result is not None),'comments_posted':int(result is not None),'other_issues_mutated':False,'settings_mutated':False,'publishing_deployment_release_or_Pages':False,'release_readiness_certified':False,'scope':'Original UI-009 constructor/Saver defect only. Original technical body/title/labels/history preserved; one additive resolution/state-only closure exactly readback. No broad UI/native/consumer/release clearance.'})
for name in ('close.py','comment.md'):(OUT/name).write_bytes((BASE/name).read_bytes())
(OUT/'SHA256SUMS').write_text(''.join(sha(p.read_bytes())+'  '+p.name+chr(10) for p in sorted(OUT.iterdir()) if p.is_file()))
print(json.dumps({'passed':True,'dry_run':not args.apply,'result':result,'receipt':str(OUT/'receipt.json')},indent=2))
