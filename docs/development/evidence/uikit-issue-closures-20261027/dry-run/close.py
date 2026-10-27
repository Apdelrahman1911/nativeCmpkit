"""Default read-only original UI-015/UI-022 closure after exact pushed evidence.

Only two additive resolution comments and state-only issue closures are allowed.
Preserve original title/body/labels/history and reconcile uncertain responses,
never repeat a POST/PATCH or infer closure from source or a CI badge alone.
"""
from pathlib import Path
import argparse,datetime as dt,gzip,hashlib,json,subprocess
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent
REPO='Apdelrahman1911/nativeCmpkit';REF='development/preview-hardening'
SHA='70114ff3d579af291c4a3028181efc7d884e23a9';MAIN='94d2492e99d5cbc060409d94d9f88febd06222d5'
RUNTIME='ea79ab8cf30132b4b37985f175d00287382ddca8'
ACCEPT='docs/development/evidence/uikit-original-acceptance-20261027/lead-original-acceptance-review.json'
PREFLIGHT='docs/development/evidence/ci-preflight-20261027-025/lead-review.json'
LINKS='docs/development/evidence/postfreeze025-links-20261027/review.json'
RUN_REVIEW='docs/development/evidence/github-actions/40540209480/lead-independent-review.json'
FINDINGS={'UI-022':(128,'UI-native.json'),'UI-015':(160,'UI-native.json')}
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
OUT=BASE/('apply' if args.apply else 'dry-run');OUT.mkdir(exist_ok=False)
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(name,x):
 with (OUT/name).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def read(endpoint,name,paginate=False):
 command=['gh','api','repos/'+REPO+'/'+endpoint]
 if paginate:command+=['--paginate']
 r=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=120)
 (OUT/(name+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==0,'Read-only GitHub observation failed; preserve, no automatic retry'
 raw=r.stdout;p=OUT/(name+'.json')
 if len(raw)>100000:p=p.with_suffix('.json.gz');p.write_bytes(gzip.compress(raw,mtime=0))
 else:p.write_bytes(raw)
 if not paginate:return json.loads(raw)
 text=raw.decode();decoder=json.JSONDecoder();position=0;pages=[]
 while position<len(text):
  while position<len(text) and text[position].isspace():position+=1
  if position==len(text):break
  page,position=decoder.raw_decode(text,position);assert isinstance(page,list);pages.append(page)
 items=[i for page in pages for i in page]
 assert len({i['id'] for i in items})==len(items),'Duplicate paginated GitHub identities'
 return items

def mutate(endpoint,method,name,payload):
 save(name+'-payload.json',payload);start=utc()
 try:
  r=subprocess.run(['gh','api','repos/'+REPO+'/'+endpoint,'--method',method,'--input',str(OUT/(name+'-payload.json'))],cwd=ROOT,capture_output=True,timeout=120);status=r.returncode
  (OUT/(name+'.stdout')).write_bytes(r.stdout);(OUT/(name+'.stderr')).write_bytes(r.stderr)
 except subprocess.TimeoutExpired as e:
  (OUT/(name+'.stdout')).write_bytes(e.stdout or b'');(OUT/(name+'.stderr')).write_bytes(e.stderr or b'');status=None
 save(name+'-request.json',{'endpoint':'repos/'+REPO+'/'+endpoint,'method':method,'invocations':1,
                         'started_utc':start,'finished_utc':utc(),'exit_code':status,'automatic_retry':False})
 return status

def preserve(issue):return {'title':issue['title'],'body':issue['body'],'labels':sorted(issue['labels'],key=lambda l:l['id'])}
def local():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==SHA
 assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==REF
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
 assert subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip()=='https://github.com/'+REPO+'.git'
local();started=utc()
assert read('branches/'+REF,'development-before')['commit']['sha']==SHA
assert read('branches/main','main-before')['commit']['sha']==MAIN
assert read('pages','pages-before')['status'] is None
assert read('releases?per_page=100','releases-before')==[]
for name in (ACCEPT,PREFLIGHT,LINKS,RUN_REVIEW):assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',SHA+':'+name],cwd=ROOT)
review=json.loads((ROOT/ACCEPT).read_bytes());preflight=json.loads((ROOT/PREFLIGHT).read_bytes());links=json.loads((ROOT/LINKS).read_bytes());run=json.loads((ROOT/RUN_REVIEW).read_bytes())
assert preflight['passed'] and preflight['commands']==23 and preflight['python_tooling_methods']==1225
assert links['passed'] and links['all_other_executable_test_and_workflow_inputs_unchanged']
assert review['evidence_integrity_passed'] and review['source_revision']==RUNTIME and review['immutable_run_id']==40540209480
assert run['evidence_integrity_passed'] and run['source_revision']==RUNTIME and run['totals']['tests']==run['totals']['passed']==123 and run['actual_xml_reports']==25
assert run['mandatory_application_methods_passed']==16 and run['application_transport_passed'] and run['application_completion']=={'runner_exit':0,'worker_terminated':True}
for name,digest in review['owning_current_source_hashes_identical_to_runtime'].items():assert sha((ROOT/name).read_bytes())==digest,name
planned=[]
for fid,(number,filename) in FINDINGS.items():
 item=next(i for i in review['findings_accepted_for_scoped_closure'] if i['id']==fid)
 assert item['issue_number']==number and item['accepted_for_original_scoped_closure']
 assert all(r['status']=='passed-original-scoped-native-runtime' and r['executed_methods'] and all(m['status']=='passed' for m in r['executed_methods']) for r in item['requirements_review'])
 ledger=json.loads((ROOT/'docs/development/resolutions'/filename).read_bytes());entry=next(x for x in ledger if x['id']==fid)
 assert entry['status']=='verified' and entry['remaining']==[]
 issue=read('issues/'+str(number),f'issue-{number}-before')
 original=json.loads((ROOT/f'docs/development/evidence/uikit-original-acceptance-20261027/issue-{number}-before.json').read_bytes())
 assert preserve(issue)==preserve(original) and issue['state']=='open' and 'pull_request' not in issue
 assert sha(issue['body'].encode())==item['issue_body_sha256_before'] and issue['title']==item['issue_title_before']
 assert sorted(l['name'] for l in issue['labels'])==item['issue_labels_before']
 marker='<!-- nativecmpkit-resolution:'+fid+':20261027-current-native-original-acceptance -->'
 comments=read('issues/'+str(number)+'/comments?per_page=100',f'comments-{number}-before',True)
 assert not any(marker in (c.get('body') or '') for c in comments),'Existing resolution marker: reconcile, never duplicate POST'
 body=(BASE/(fid+'-comment.md')).read_text();assert body.startswith(marker)
 for name in (ACCEPT,PREFLIGHT,LINKS,RUN_REVIEW):assert 'https://github.com/'+REPO+'/blob/'+SHA+'/'+name in body
 save(f'planned-{number}-comment.json',{'body':body,'marker':marker})
 planned.append({'id':fid,'number':number,'issue':issue,'marker':marker,'body':body})
save('preflight.json',{'passed':True,'source_revision':SHA,'runtime_revision':RUNTIME,'main_preserved':MAIN,'dry_run':not args.apply,
 'original_issue_bodies_titles_labels_unchanged':True,'planned_issues':[p['number'] for p in planned],'duplicate_markers':0,'publication_performed':False})
results=[]
if args.apply:
 for p in planned:
  fid,number,marker,body=p['id'],p['number'],p['marker'],p['body']
  fresh=read('issues/'+str(number),f'issue-{number}-immediate-before');assert preserve(fresh)==preserve(p['issue']) and fresh['state']=='open'
  post=mutate('issues/'+str(number)+'/comments','POST',f'comment-{number}',{'body':body})
  comments=read('issues/'+str(number)+'/comments?per_page=100',f'comments-{number}-after',True)
  found=[c for c in comments if marker in (c.get('body') or '')];assert len(found)==1 and found[0]['body']==body,'Uncertain/rejected POST: no duplicate attempt/closure'
  comment=read('issues/comments/'+str(found[0]['id']),f'comment-{number}-readback');assert comment['body']==body and comment['id']==found[0]['id']
  if post==0:assert json.loads((OUT/f'comment-{number}.stdout').read_bytes())['id']==comment['id']
  before_close=read('issues/'+str(number),f'issue-{number}-before-close');assert before_close['state']=='open' and preserve(before_close)==preserve(p['issue'])
  patch=mutate('issues/'+str(number),'PATCH',f'close-{number}',{'state':'closed','state_reason':'completed'})
  final=read('issues/'+str(number),f'issue-{number}-after');assert final['state']=='closed' and final['state_reason']=='completed' and preserve(final)==preserve(p['issue'])
  final_comment=read('issues/comments/'+str(comment['id']),f'comment-{number}-final-readback');assert final_comment['body']==body and final_comment['id']==comment['id']
  result={'id':fid,'number':number,'url':final['html_url'],'state':final['state'],'state_reason':final['state_reason'],'closed_at':final['closed_at'],
          'comment_id':comment['id'],'comment_url':comment['html_url'],'comment_sha256':sha(body.encode()),
          'comment_POST_invocations':1,'state_PATCH_invocations':1,'POST_exit_code':post,'PATCH_exit_code':patch,
          'exact_readback_verified':True,'body_title_labels_unchanged':True}
  results.append(result);print(json.dumps(result),flush=True)
assert read('branches/main','main-after')['commit']['sha']==MAIN
assert read('branches/'+REF,'development-after')['commit']['sha']==SHA
local();save('receipt.json',{'passed':True,'dry_run':not args.apply,'started_utc':started,'finished_utc':utc(),
 'source_revision':SHA,'runtime_revision':RUNTIME,'main_preserved':MAIN,'results':results,'issues_closed':len(results),'comments_posted':len(results),
 'settings_mutated':False,'other_issues_mutated':False,'publishing_deployment_release_or_Pages':False,'release_readiness_certified':False,
 'scope':'Original UI-015/UI-022 only, current-native immutable requirement mapping/pushed evidence and exact additive-comment/state-only closure readback. Original body/title/labels/history preserved. No broader module/native-device/consumer/ABI/legal/dependency/security or release clearance.'})
for name in ['close.py',*[fid+'-comment.md' for fid in FINDINGS]]:shutil=None;(OUT/name).write_bytes((BASE/name).read_bytes())
(OUT/'SHA256SUMS').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(OUT.iterdir()) if p.is_file()))
print(json.dumps({'passed':True,'dry_run':not args.apply,'issues_closed':len(results),'receipt':str(OUT/'receipt.json')},indent=2))
