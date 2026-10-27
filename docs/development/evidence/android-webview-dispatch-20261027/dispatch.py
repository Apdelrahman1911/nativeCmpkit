from pathlib import Path
import datetime as dt,json,subprocess,sys,time
root=Path('/root/projects/nativeCmpKit');out=Path(__file__).parent;repo='Apdelrahman1911/nativeCmpkit';ref='development/preview-hardening';sha='4fb7d886d533610c7e4bf55535ea980ff050a144';main='94d2492e99d5cbc060409d94d9f88febd06222d5'
def get(path,name):
 run=subprocess.run(['gh','api','repos/'+repo+'/'+path],cwd=root,capture_output=True,timeout=90)
 (out/(name+'.json')).write_bytes(run.stdout);(out/(name+'.stderr')).write_bytes(run.stderr)
 assert run.returncode==0,'Read failed; reconcile rather than repeating a mutation'
 return json.loads(run.stdout)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==sha
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root)
assert subprocess.check_output(['git','remote','get-url','origin'],cwd=root,text=True).strip()=='https://github.com/'+repo+'.git'
assert get('branches/main','main-before')['commit']['sha']==main
assert get('actions/permissions','actions-permissions')=={'enabled':True,'allowed_actions':'all','sha_pinning_required':False}
assert get('actions/permissions/workflow','workflow-permissions')=={'default_workflow_permissions':'read','can_approve_pull_request_reviews':False}
workflow=get('actions/workflows/gradle.yml','workflow');assert workflow['state']=='active'
for status in ('in_progress','queued'):
 assert get('actions/runs?status='+status+'&per_page=100',status)['total_count']==0,'Observe existing work, do not redispatch'
sys.path.insert(0,str(root/'scripts/ci'));import library_tests as lt;import workflow_matrix as wm
inputs=lt.snapshot_inputs(root);assert len(inputs)==734 and lt.input_digest(inputs)=='f28ef3e916bf8814aa25d3f5b749ecbc63ad189e36882387538298dec35f51e0'
assert wm.matrix('android-webview')['include']==[{'slot':'android-device-api35','suite':'android-device','runner':'ubuntu-24.04','arch':'x64','python':'python3','emulator-api':'35','test-modules':'calf-webview'}]
source=(root/'.github/workflows/gradle.yml').read_text();assert 'permissions:\n  contents: read' in source and 'persist-credentials: false' in source
assert not any(value in source for value in ('packages: write','deployments: write','id-token: write'))
assert get('branches/'+ref,'branch-before-dispatch')['commit']['sha']==sha
before=get('actions/workflows/gradle.yml/runs?per_page=100','runs-before');known={run['id'] for run in before['workflow_runs']}
payload={'ref':ref,'inputs':{'profile':'android-webview'}};(out/'payload.json').write_text(json.dumps(payload,indent=2)+'\n')
started=dt.datetime.now(dt.timezone.utc).isoformat()
request=subprocess.run(['gh','api','repos/'+repo+'/actions/workflows/gradle.yml/dispatches','--method','POST','--input',str(out/'payload.json')],cwd=root,capture_output=True,timeout=90)
(out/'request.stdout').write_bytes(request.stdout);(out/'request.stderr').write_bytes(request.stderr)
(out/'request.json').write_text(json.dumps({'POST_invocations':1,'exit_code':request.returncode,'started_utc':started,'automatic_retry':False},indent=2)+'\n')
# Readback even after an uncertain POST. Never issue a second mutation automatically.
found=None
for attempt in range(12):
 after=get('actions/workflows/gradle.yml/runs?per_page=100','runs-after-'+str(attempt))
 rows=[r for r in after['workflow_runs'] if r['id'] not in known and r['head_sha']==sha and r['head_branch']==ref and r['event']=='workflow_dispatch']
 assert len(rows)<=1
 if rows: found=rows[0];break
 time.sleep(8)
assert found is not None,'Reconcile missing readback, never duplicate POST'
assert get('branches/main','main-after')['commit']['sha']==main
assert get('branches/'+ref,'branch-after-dispatch')['commit']['sha']==sha
receipt={'observed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'source_revision':sha,'main_preserved':main,'run_id':found['id'],'run_url':found['html_url'],'run_attempt':found['run_attempt'],'profile':'android-webview','source_input_count':len(inputs),'source_digest':lt.input_digest(inputs),'authored_methods':25,'required_native_cases':1,'selected_library_jobs':1,'POST_invocations':1,'push_invocations':0,'status':found['status'],'conclusion':found['conclusion'],'settings_issues_or_publishing_mutated':False,'scope':'One focused actual Android WebView/Compose history suite. New owning URL/interception fixture has only compile evidence; execute on API35 enforcing emulator, not a sample/Robolectric. Pending actual results; no blanket issue/ABI/release acceptance or repeat of successful unrelated suites.'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
