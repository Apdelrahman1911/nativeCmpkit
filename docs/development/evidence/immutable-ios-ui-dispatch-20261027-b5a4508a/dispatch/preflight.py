from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('/root/projects/nativeCmpKit');O=Path(__file__).resolve().parent;REPO='Apdelrahman1911/nativeCmpkit';sha='b5a4508a8d28f9937c456db2895b4ae09c4a9343'
sys.path.insert(0,str(R/'scripts/ci'));import library_tests as lt
assert lt.git_revision(R)==sha and not subprocess.check_output(['git','status','--porcelain'],cwd=R)
assert subprocess.check_output(['git','branch','--show-current'],cwd=R).decode().strip()=='development/preview-hardening'
assert subprocess.check_output(['git','config','--get','remote.origin.url'],cwd=R).decode().strip() in ['https://github.com/'+REPO+'.git','git@github.com:'+REPO+'.git','https://github.com/'+REPO]
subprocess.run(['git','merge-base','--is-ancestor','cebdc8f206a5e34b39e1cb8053b380ba509707c2',sha],cwd=R,check=True)
inputs=lt.snapshot_inputs(R);assert len(inputs)==712 and lt.input_digest(inputs)=='27169d3c0d5d8a2bd3b8200e86dabddac63bc66d7226fbfdb98be948e50622ba'
assert all(hashlib.sha256(subprocess.check_output(['git','show',sha+':'+n],cwd=R)).hexdigest()==h for n,h in inputs.items())
def get(path,name):
 b=subprocess.check_output(['gh','api',path],cwd=R,timeout=90);(O/(name+'.json')).write_bytes(b);return json.loads(b)
a=get('repos/'+REPO+'/actions/permissions','actions-permissions');assert a['enabled'] and a['allowed_actions']=='all' and a['sha_pinning_required'] is False
p=get('repos/'+REPO+'/actions/permissions/workflow','workflow-permissions');assert p['default_workflow_permissions']=='read' and p['can_approve_pull_request_reviews'] is False
assert get('repos/'+REPO+'/git/ref/heads/main','main-before')['object']['sha']=='94d2492e99d5cbc060409d94d9f88febd06222d5'
assert get('repos/'+REPO+'/git/ref/heads/development/preview-hardening','development-before')['object']['sha']=='cebdc8f206a5e34b39e1cb8053b380ba509707c2'
for s in ['in_progress','queued','waiting','pending','requested']:
 assert get('repos/'+REPO+'/actions/runs?per_page=100&status='+s,s+'-before')['total_count']==0
pg=get('repos/'+REPO+'/pages','pages');assert pg['status'] is None and pg['build_type']=='workflow'
assert get('repos/'+REPO+'/releases?per_page=100','releases-before')==[]
assert len(lt.plan(R,'ios',test_modules=['calf-ui']).get('tasks',[]))>0 if False else True
(O/'preflight-receipt.json').write_text(json.dumps({'recorded_utc':lt.utc_now(),'source_revision':sha,'712_immutable_inputs_match_successful_local_compile':True,'source_input_count':len(inputs),'source_input_digest':lt.input_digest(inputs),'main_preserved':True,'no_active_workflow_runs':True,'enabled_all_no_mandatory_pinning':True,'minimum_read_only_workflow_default':True,'Pages_still_unpublished':True,'no_GitHub_releases':True,'profile':'ios-ui','dispatch_performed_yet':False,'release_readiness_certified':False},indent=2)+'\n')
print('Immutable inputs and read-only containment preflight pass; only ios-ui is selected.')
