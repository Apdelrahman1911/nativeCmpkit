"""Bound four reviewed original issues; preserve descriptions/labels; exact readback.

Default is read-only. --apply only posts an attributed additive resolution and
patches state/state_reason after a single POST readback. Never rewrites bodies,
labels, timestamps, historical findings or upstream. No bulk synchronizer.
"""
from pathlib import Path
import argparse,datetime as dt,gzip,hashlib,json,subprocess
ROOT=Path('/root/projects/nativeCmpKit')
REPO='Apdelrahman1911/nativeCmpkit';REF='development/preview-hardening'
SHA='8ab82a3fa41caad34cd7fb7a2d3722bfc25e3838';MAIN='94d2492e99d5cbc060409d94d9f88febd06222d5'
BASE=Path('/dev/shm/nativecmpkit-issue-closures-20261027-001')
ACCEPT='docs/development/evidence/closure-review-20261027-001/lead-original-acceptance-review.json'
PREFLIGHT='docs/development/evidence/ci-preflight-20261027-019/lead-review.json'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
OUT=BASE/('apply' if args.apply else 'dry-run');OUT.mkdir(parents=True,exist_ok=False)
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,x):
 with (OUT/name).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def read(path,name,paginate=False):
 cmd=['gh','api','repos/'+REPO+'/'+path]
 if paginate:cmd+=['--paginate','--slurp']
 r=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=120)
 (OUT/(name+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==0,'Read-only destination readback failed; no implicit retry'
 suffix='.json.gz' if len(r.stdout)>100000 else '.json'
 (OUT/(name+suffix)).write_bytes(gzip.compress(r.stdout,mtime=0) if suffix.endswith('.gz') else r.stdout)
 value=json.loads(r.stdout)
 if paginate:
  assert isinstance(value,list) and all(isinstance(page,list) for page in value)
  return [item for page in value for item in page]
 return value
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
review=json.loads((ROOT/ACCEPT).read_bytes());preflight=json.loads((ROOT/PREFLIGHT).read_bytes())
assert preflight['passed'] and preflight['commands']==23 and preflight['python_tooling_methods']==1137
assert review['source_inputs_held_during_review'] and review['immutable_runtime_revision']=='6eb7c66eb01b390353100c63882cd102846c7b8d'
assert [(f['id'],f['issue_number']) for f in review['findings_accepted_for_scoped_closure']]==[('NAV-001',15),('NAV-002',16),('UI-033',136),('NAV-017',155)]
for path,digest in review['scoped_current_inputs_matching_immutable_runtime'].items():
 assert sha((ROOT/path).read_bytes())==digest,path
solutions={
 'NAV-001':('Navigation stored only route strings and dispatched static graph schemas, losing visit-specific payloads.','The controller now stores unique entries with copied portable argument values; destination resolution validates missing/null/type/default values before mutation, dispatches per-entry values and saves/restores IDs and payloads. Unsupported values fail predictably.','calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHostController.kt','navigateWithValues / saveState / restoreState; NavDestination.resolveArguments; AdaptiveNavHost'),
 'NAV-002':('SaveableStateProvider and popped-state cleanup were keyed by route strings, conflating repeated visits.','Composition/saveable providers and cleanup now use persisted unique entry IDs. Duplicate and same-frame pop/revisit state is independent, and restored duplicates pop independently.','calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt','AdaptiveNavHost / ForgetPoppedEntries; AdaptiveNavHostController entry/saver ownership'),
 'UI-033':('Discrete semantic snapping initialized its distance search with the negative target value, so no absolute distance could qualify.','A shared SliderValueDomain snaps numerically with a nonnegative normalized distance; SliderInput applies it to actual semantics and completes only a changed value. Negative ranges/ties/endpoints are handled without allocating tick arrays for input.','calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/slider/SliderValueDomain.kt','SliderValueDomain.snap; SliderInput.setProgress'),
 'NAV-017':('Both showcase share actions opened a dialog falsely claiming a clipboard operation that never happened.','The demonstration explicitly reports "This is an action preview. No link was copied or shared." Both original taps remain preview-only; no hidden clipboard or native sharing was added.','sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ShowcaseScreen.kt','both share actions / showShareDialog result'),
}
current={};comments={};bodies={}
for finding in review['findings_accepted_for_scoped_closure']:
 ident=finding['id'];n=finding['issue_number'];issue=read('issues/'+str(n),'issue-'+str(n)+'-before')
 old=json.loads((ROOT/'docs/development/evidence/closure-review-20261027-001'/('issue-'+str(n)+'-before.json')).read_bytes())
 assert preserve(issue)==preserve(old),'Manual title/body/label change requires rereview, no mutation'
 assert issue['state']=='open' and 'pull_request' not in issue
 assert sha(issue['body'].encode())==finding['issue_body_sha256_before']
 assert sha(issue['title'].encode())==finding['issue_title_sha256_before']
 assert sorted(label['name'] for label in issue['labels'])==finding['issue_labels_before']
 marker='<!-- nativecmpkit-resolution:'+ident+':20261027-original-acceptance -->'
 comments[n]=read('issues/'+str(n)+'/comments?per_page=100','issue-'+str(n)+'-comments-before',True)
 assert not any(marker in (c.get('body') or '') for c in comments[n]),'Existing marker must be reconciled; no duplicate POST'
 root,repair,source,symbols=solutions[ident]
 body=marker+'\n## Verified resolution — original '+ident+' acceptance\n\n'
 body+='**Root cause:** '+root+'\n\n**Repair:** '+repair+'\n\n'
 body+='**Affected implementation:** [`'+source+'`](https://github.com/'+REPO+'/blob/'+SHA+'/'+source+') — '+symbols+'.\n\n'
 body+='### Original required checks reviewed\n'
 for row in finding['requirements_review']:
  body+='- **'+row['requirement']+'** — '+row['status']+'.'
  methods=row.get('executed_methods',[])
  if methods:body+=' Methods: '+', '.join('`'+m['class']+'.'+m['method']+'`' for m in methods)+'.'
  if row.get('explanation'):body+=' '+row['explanation']
  body+='\n'
 body+='\n[Verbatim original-requirement/source/Git/XML review](https://github.com/'+REPO+'/blob/'+SHA+'/'+ACCEPT+') at immutable evidence commit `'+SHA+'`. '
 if ident.startswith('NAV-0') and ident!='NAV-017':
  body+='Owning navigation source/test/build bytes match `6eb7c66eb01b390353100c63882cd102846c7b8d`: Linux51/51 + Android-host37/37 ([40414284598](https://github.com/'+REPO+'/actions/runs/40414284598)); macOS51/51 + iOS39/39 ([40415332643](https://github.com/'+REPO+'/actions/runs/40415332643)). These178 target executions reuse51 source methods. The historical Apple run failed elsewhere; only the passed navigation scope is accepted. '
  if ident=='NAV-002':body+='Both original upstream [Calf #542](https://github.com/MohamedRejeb/Calf/issues/542) test bodies are retained byte-identically and passing. '
 elif ident=='UI-033':
  body+='Unchanged owning implementation/tests pass12 actual Compose slider interaction methods and8 numeric-domain methods on each Linux/macOS desktop in those immutable runs, including semantic `setProgress(-0.7) -> -0.5` with exactly one completion. '
 else:
  body+='The six current source-contract guards pass. This issue concerns the illustrative sample claim, not proof of native library sharing; the original clipboard test is conditional and inapplicable because copying is not implemented. '
 body+='\n\n[Current staged preflight](https://github.com/'+REPO+'/blob/'+SHA+'/'+PREFLIGHT+') passes23/23 commands,1,137 overlapping Python executions, strict documentation/actionlint and both whitespace checks; it executes zero new library/native/packaged methods.\n\n'
 body+='**Compatibility / limits:** '+finding['compatibility']+' Original issue description, labels, upstream discussion and previous remaining notes are preserved. This closes only the original specific defect after required-scope review; minimum-platform/device/native-stack integration, whole-library API/ABI, full packaged consumers, dependency trust, legal/native-payload and all other issue/release gates remain independent and are not waived. No package, release, deployment or Pages publication.\n'
 bodies[n]=body;save('issue-'+str(n)+'-planned-comment.json',{'body':body,'marker':marker});current[n]=issue
save('preflight.json',{'passed':True,'observed_utc':utc(),'source_revision':SHA,'main_preserved':MAIN,'issues':[15,16,136,155],'all_original_bodies_titles_labels_unchanged':True,'duplicate_resolution_markers':0,'dry_run':not args.apply,'publication_performed':False})
results=[]
if args.apply:
 for finding in review['findings_accepted_for_scoped_closure']:
  ident=finding['id'];n=finding['issue_number'];marker='<!-- nativecmpkit-resolution:'+ident+':20261027-original-acceptance -->'
  fresh=read('issues/'+str(n),'issue-'+str(n)+'-immediate-before')
  assert preserve(fresh)==preserve(current[n]) and fresh['state']=='open'
  status=mutate('issues/'+str(n)+'/comments','POST','issue-'+str(n)+'-comment',{'body':bodies[n]})
  after_comments=read('issues/'+str(n)+'/comments?per_page=100','issue-'+str(n)+'-comments-after',True)
  found=[c for c in after_comments if marker in (c.get('body') or '')]
  assert len(found)==1 and found[0]['body']==bodies[n],'Uncertain/rejected POST; no automatic retry/close before readback'
  response=json.loads((OUT/('issue-'+str(n)+'-comment.stdout')).read_bytes()) if status==0 else None
  if response:assert response['id']==found[0]['id']
  seen=read('issues/'+str(n)+'/comments/'+str(found[0]['id']),'issue-'+str(n)+'-comment-readback')
  assert seen['body']==bodies[n] and seen['id']==found[0]['id']
  before_close=read('issues/'+str(n),'issue-'+str(n)+'-before-close')
  assert preserve(before_close)==preserve(current[n]) and before_close['state']=='open'
  patched=mutate('issues/'+str(n),'PATCH','issue-'+str(n)+'-close',{'state':'closed','state_reason':'completed'})
  final=read('issues/'+str(n),'issue-'+str(n)+'-after')
  assert final['state']=='closed' and final['state_reason']=='completed' and preserve(final)==preserve(current[n])
  final_comment=read('issues/'+str(n)+'/comments/'+str(seen['id']),'issue-'+str(n)+'-final-comment')
  assert final_comment['body']==bodies[n] and final_comment['id']==seen['id']
  row={'id':ident,'number':n,'url':final['html_url'],'state':final['state'],'state_reason':final['state_reason'],'closed_at':final['closed_at'],'comment_id':seen['id'],'comment_url':seen['html_url'],'body_title_labels_unchanged':True,'comment_sha256':sha(bodies[n].encode()),'comment_POST_invocations':1,'state_PATCH_invocations':1,'POST_exit_code':status,'PATCH_exit_code':patched,'exact_readback_verified':True}
  results.append(row);print(json.dumps(row),flush=True)
assert read('branches/main','main-after')['commit']['sha']==MAIN
assert read('branches/'+REF,'development-after')['commit']['sha']==SHA
local()
save('receipt.json',{'passed':True,'started_utc':started,'finished_utc':utc(),'source_revision':SHA,'main_preserved':MAIN,'dry_run':not args.apply,'results':results,'issues_closed':len(results),'comments_posted':len(results),'other_issues_mutated':False,'settings_changed':False,'publishing_deployment_release_or_Pages':False,'release_readiness_certified':False,'scope':'Only four independently reviewed original findings. Each technical body/title/label is unchanged, additive resolution posted once with exact readback, state alone changed to closed/completed and rechecked. Original gates and failed evidence remain. No blanket module/CI/release certification.'})
(OUT/'driver.py').write_bytes(Path(__file__).read_bytes())
(OUT/'SHA256SUMS').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(OUT.iterdir()) if p.is_file()))
print(json.dumps({'passed':True,'dry_run':not args.apply,'issues_closed':len(results),'receipt':str(OUT/'receipt.json')},indent=2))
