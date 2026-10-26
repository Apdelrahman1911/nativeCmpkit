from pathlib import Path
import datetime as dt, hashlib, json, subprocess, sys
ROOT=Path('/root/projects/nativeCmpKit'); OUT=ROOT/'docs/development/evidence/remote-preflight-20261026-002'
sys.path.insert(0,str(ROOT/'scripts/migration'));from github_json import json_pages
assert not OUT.exists(); OUT.mkdir(parents=True)
def put(name,x):
    with (OUT/name).open('x') as f: json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
requests=[]
def get(name,endpoint,paginate=False):
    args=['gh','api','--method','GET',endpoint]
    if paginate: args.append('--paginate')
    r=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
    requests.append({'name':name,'endpoint':endpoint,'method':'GET','exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest()})
    if r.returncode: raise RuntimeError('Read-only API observation failed: '+name)
    pages=json_pages(r.stdout.decode())
    if paginate:
        assert all(isinstance(page,list) for page in pages)
        value=[row for page in pages for row in page]
    else:
        assert len(pages)==1;value=pages[0]
    (OUT/(name+'.raw.json')).write_bytes(r.stdout)
    return value
started=dt.datetime.now(dt.timezone.utc).isoformat()
upstream=get('upstream-open','repos/MohamedRejeb/Calf/issues?state=open&per_page=100',True)
issues=[i for i in upstream if 'pull_request' not in i]; prs=[i for i in upstream if 'pull_request' in i]
baseline=json.loads((ROOT/'docs/migration/upstream-updates/20261024T183300Z/source/open-issues.json').read_bytes())
old={i['number']:i for i in baseline};fresh={i['number']:i for i in issues}
keys=['number','id','title','body','user','created_at','updated_at','state','comments']
changes=[]
for n in sorted(set(old)|set(fresh)):
    if n not in old or n not in fresh: changes.append({'number':n,'presence_changed':True});continue
    a,b=old[n],fresh[n]
    delta=[k for k in keys if a.get(k)!=b.get(k)]
    if {l['name'] for l in a['labels']}!={l['name'] for l in b['labels']}:delta.append('labels')
    if delta:changes.append({'number':n,'changed_fields':delta})
controls=get('actions-permissions','repos/Apdelrahman1911/nativeCmpkit/actions/permissions')
permissions=get('workflow-permissions','repos/Apdelrahman1911/nativeCmpkit/actions/permissions/workflow')
workflows=get('workflows','repos/Apdelrahman1911/nativeCmpkit/actions/workflows?per_page=100')
runs=get('recent-runs','repos/Apdelrahman1911/nativeCmpkit/actions/runs?per_page=100')
pages=get('pages','repos/Apdelrahman1911/nativeCmpkit/pages')
main=get('main','repos/Apdelrahman1911/nativeCmpkit/git/ref/heads/main')
releases=get('releases','repos/Apdelrahman1911/nativeCmpkit/releases?per_page=100',True)
assert not changes and len(issues)==16
assert controls=={'enabled':True,'allowed_actions':'all','sha_pinning_required':False}
assert permissions=={'default_workflow_permissions':'read','can_approve_pull_request_reviews':False}
assert main['object']['sha']=='94d2492e99d5cbc060409d94d9f88febd06222d5'
active=[{'id':w['id'],'path':w['path'],'state':w['state']} for w in workflows['workflows']]
assert {w['path'] for w in active}=={'.github/workflows/gradle.yml','.github/workflows/build-native-libs.yml'}
incomplete=[{'id':r['id'],'status':r['status'],'head_sha':r['head_sha'],'html_url':r['html_url']} for r in runs['workflow_runs'] if r['status']!='completed']
assert not incomplete and pages['status'] is None and pages['build_type']=='workflow' and not releases
put('observation.json',{'started_utc':started,'finished_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision_observed_locally':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_tree_dirty':True,'upstream_actual_open_issues':len(issues),'upstream_open_prs_excluded':len(prs),'upstream_description_author_timestamp_label_comment_count_changes_since_sync':changes,'baseline_sync':'docs/migration/upstream-updates/20261024T183300Z/','issue_sync_requires_new_mutation':False,'actions_permissions':controls,'workflow_permissions':permissions,'main_sha':main['object']['sha'],'workflows':active,'incomplete_runs_in_returned_100_run_page':incomplete,'github_release_count':len(releases),'pages':{'status':pages['status'],'build_type':pages['build_type']},'requests':requests,'publication_performed':False,'release_gate_cleared':False,'limitations':['Issue detail/description/comment counts/updated timestamps match the synchronized snapshot; comments/timeline were not all re-exported during this check.','Public HTTP Pages and package registries were not freshly enumerated.','Readback is a timed observation, not a repository guarantee.']})
(OUT/'collector.py').write_bytes(Path(__file__).read_bytes())
(OUT/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.is_file()))
print(json.dumps({'open_upstream_issues':len(issues),'changed':changes,'actions':controls,'incomplete_runs':incomplete,'releases':len(releases),'archive':str(OUT.relative_to(ROOT))},indent=2))
