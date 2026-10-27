"""Fixed-destination read-only prepush controls; no GitHub configuration/publishing mutation."""
from pathlib import Path
import datetime as dt,gzip,hashlib,json,subprocess
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent/'remote-prepush';BASE.mkdir()
REPO='Apdelrahman1911/nativeCmpkit';HEAD='cd51e8d626afd3fb7a5688f8b3f5db584a3bd386';MAIN='94d2492e99d5cbc060409d94d9f88febd06222d5'
def get(path,label):
 command=['gh','api','repos/'+REPO+'/'+path,'-H','Cache-Control: no-cache']
 result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=90)
 (BASE/(label+'.json.gz')).write_bytes(gzip.compress(result.stdout,mtime=0));(BASE/(label+'.stderr')).write_bytes(result.stderr)
 assert result.returncode==0,(label,result.returncode)
 return json.loads(result.stdout)
repo=get('','repository');assert repo['full_name']==REPO and not repo['fork']
assert get('branches/main','main')['commit']['sha']==MAIN
assert get('branches/development/preview-hardening','development')['commit']['sha']==HEAD
assert get('releases?per_page=100','releases')==[]
assert get('pages','pages')['status'] is None
settings=get('actions/permissions','actions');assert settings['enabled'] is True and settings['allowed_actions']=='all'
permissions=get('actions/permissions/workflow','workflow-permissions');assert permissions['default_workflow_permissions']=='read' and permissions['can_approve_pull_request_reviews'] is False
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==HEAD
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='development/preview-hardening'
assert subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip()=='https://github.com/'+REPO+'.git'
record={'passed':True,'observed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'repository':REPO,'source_revision':HEAD,'main_preserved':MAIN,'Actions_enabled':True,'allowed_actions':'all','sha_pinning_required_reported':settings.get('sha_pinning_required'),'default_workflow_token':'read','PR_review_approval':False,'current_releases':0,'Pages_status':None,'metadata_read_only':True,'publication_or_settings_mutations':0}
(BASE/'review.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps(record,indent=2),flush=True)
