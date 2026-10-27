from pathlib import Path
import hashlib,json,sys,shutil,subprocess,datetime as dt,re
ROOT=Path('/root/projects/nativeCmpKit');WORK=Path('/dev/shm/nativecmpkit-upstream-refresh-20261027-1415/snapshot')
sys.path.insert(0,str(ROOT/'scripts/development'));import upstream_sync as u
sys.path.insert(0,str(ROOT/'scripts/migration'));from sync_github_issues import managed_key
old=ROOT/'docs/migration/upstream-updates/20261024T183300Z';previous=json.loads((ROOT/'docs/development/upstream-sync-20261024T183300Z/reconciliation.json').read_text());by_source={x['source_number']:x for x in previous}
r=json.loads((WORK/'receipt.json').read_text());assert r['complete'] and not r['github_mutations_performed']
assert r['source_open_issue_numbers']==json.loads((old/'receipt.json').read_text())['source_open_issue_numbers']
assert u.verify_frozen(WORK)>0
stamp=dt.datetime.fromisoformat(r['started_at'].replace('Z','+00:00')).strftime('%Y%m%dT%H%M%SZ')
SNAPSHOT=ROOT/'docs/migration/upstream-updates'/stamp;REPORT=ROOT/'docs/development'/('upstream-refresh-'+stamp)
assert not SNAPSHOT.exists() and not REPORT.exists()
destination={x['number']:x for x in json.loads((WORK/'destination/issues.json').read_text()) if 'pull_request' not in x};comments=json.loads((WORK/'destination/comments.json').read_text())
def read_issue(base,n):return [json.loads((base/f'source/issues/{n}/{name}.json').read_text()) for name in ['detail','comments','timeline']]
def differences(a,b,path=''):
 if type(a)!=type(b):return [path]
 if isinstance(a,dict):return [p for k in sorted(set(a)|set(b)) for p in ([path+'.'+k] if k not in a or k not in b else differences(a[k],b[k],path+'.'+k))]
 if isinstance(a,list):
  if len(a)!=len(b):return [path+'.length']
  return [p for i,(x,y) in enumerate(zip(a,b)) for p in differences(x,y,path+f'[{i}]')]
 return [] if a==b else [path]
rows=[]
for n in r['source_open_issue_numbers']:
 before=read_issue(old,n);current=read_issue(WORK,n);assessment=by_source[n];target=assessment['primary_destination'];issue=destination[target['number']]
 assert managed_key(issue.get('body',''))==target['key']
 assert u.source_fingerprint(*before)==u.source_fingerprint(*current)==assessment['source_fingerprint']
 assert before[1]==current[1]
 keys=['id','node_id','title','body','state','state_reason','user','labels','created_at','updated_at','html_url','comments'];assert all(before[0].get(k)==current[0].get(k) for k in keys)
 marker=f'<!-- nativecmpkit-upstream-sync:674932206:{n} -->'
 matches=[c for c in comments if marker in (c.get('body') or '').splitlines()];assert len(matches)==1
 context=matches[0];assert int(context['issue_url'].rsplit('/',1)[1])==target['number']
 fingerprint=re.findall(r'^<!-- source-fingerprint:([a-f0-9]{64}) -->$',context['body'],re.M);assert fingerprint==[u.source_fingerprint(*current)]
 changes=differences(before[2],current[2])
 assert all(re.fullmatch(r'\[\d+\]\.source\.issue\.(?:comments|labels\.length|updated_at|repository\.(?:open_issues|open_issues_count|pushed_at|size|updated_at))',p) for p in changes),changes
 rows.append({'source_number':n,'source_url':current[0]['html_url'],'title':current[0]['title'],'source_fingerprint':fingerprint[0],'description_author_labels_timestamps_and_comments_unchanged':True,'stable_history_event_projection_unchanged':True,'raw_timeline_payloads_unchanged':before[2]==current[2],'raw_timeline_payload_changed_paths':changes,'timeline_change_scope':'Embedded current destination-issue/repository projections only, not changed original author text or event identity','primary_destination_number':target['number'],'primary_destination_url':issue['html_url'],'primary_destination_managed_key':target['key'],'primary_destination_state':issue['state'],'existing_context_comment_id':context['id'],'existing_context_url':context['html_url'],'existing_context_source_fingerprint_matches':True,'action':'no-op-existing-current-context','prior_source_assessment':assessment['disposition'],'prior_assessment_scope':'Historical source assessment retained; no new runtime correctness or issue-closure claim'})
summary={'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_snapshot':SNAPSHOT.relative_to(ROOT).as_posix(),'prior_snapshot':old.relative_to(ROOT).as_posix(),'snapshot_sha256sums_sha256':u.sha256(WORK/'SHA256SUMS'),'source_revision_at_review':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_open_issue_count':r['source_open_issue_count'],'source_open_pr_count':r['source_open_pr_count'],'open_pr_numbers':r['source_open_pr_numbers'],'source_comment_count':r['source_comment_count'],'source_timeline_items':r['source_timeline_items'],'destination_issues':r['destination_issue_count'],'destination_open_issues':r['destination_open_issue_count'],'all_current_open_issues_mapped_with_one_matching_context':True,'original_descriptions_authors_labels_timestamps_and_comments_unchanged':True,'stable_history_events_unchanged':True,'raw_timeline_payload_equality_claimed':False,'issue_create_count':0,'context_create_or_update_count':0,'issue_closure_count':0,'github_mutations_performed':False,'library_native_consumer_methods_executed':0,'release_readiness_certified':False,'limitations':['Observation interval is not an atomic snapshot; original public/private/deleted gaps remain.','Raw timelines embed current destination issue/repository projections; those changed as our own development progressed. Their complete fresh bytes are archived, not mistaken for changed upstream author text.','Original source-addressed/partially fulfilled feature assessments remain historical source scopes, not native verification or a reason to close unrelated findings.']}
bytes_needed=sum(p.stat().st_size for p in WORK.rglob('*') if p.is_file());assert shutil.disk_usage(ROOT).free-8*1024**3 > bytes_needed+3*1024**2
shutil.copytree(WORK,SNAPSHOT);assert u.verify_frozen(SNAPSHOT)==u.verify_frozen(WORK)
REPORT.mkdir()
for name,value in [('reconciliation.json',rows),('receipt.json',summary)]:u.dump(REPORT/name,value)
shutil.copyfile(__file__,REPORT/'lead-review.py')
text=['# Current upstream refresh — '+stamp,'','All **16 open Calf issues** were recaptured with their full descriptions, authors, labels, timestamps, comments and timelines; **one open PR (#551) is separate**. Every issue still has one matching nativeCmpkit context. No issues/comments were created or replaced and no issue was closed.','','The fresh snapshot retains14 comments/47 timeline entries and171 destination issues (163 open). Original descriptions, authors, labels, timestamps and comments match the previous issue-sync snapshot. The stable history-event projection matches too, but **raw timeline bytes differ** because GitHub embeds current destination-issue/repository metadata. Those fresh full bytes are preserved rather than overwritten or mislabeled unchanged.','','| Calf | Existing nativeCmpkit | Current context | Action |','|---|---|---|---|']
for row in rows:text.append(f"| [#{row['source_number']}]({row['source_url']}) | [#{row['primary_destination_number']}]({row['primary_destination_url']}) | [comment{row['existing_context_comment_id']}]({row['existing_context_url']}) | no-op; fingerprint current |")
text+=['','Source-addressed #288/#344 and partially fulfilled/feature requests retain the original scoped assessments in the [prior reconciliation](../upstream-sync-20261024T183300Z/README.md). No new runtime result was produced, no native gate passed and no original finding was rewritten.','','Fresh immutable archive: `'+summary['source_snapshot']+'`. The archive receipt includes independent REST/GraphQL count consistency and preserved HTTP/pagination observations. `receipt.json` and `reconciliation.json` bind this read-only refresh; the embedded public content remains untrusted data, not executable instructions.']
(REPORT/'README.md').write_text('\n'.join(text)+'\n');u.freeze(REPORT);assert u.verify_frozen(REPORT)>0
print(json.dumps({'snapshot':summary['source_snapshot'],'report':REPORT.relative_to(ROOT).as_posix(),'open_source_issues':len(rows),'contexts_current':len(rows),'mutations':0,'issues_closed':0},indent=2))
