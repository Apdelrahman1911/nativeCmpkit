"""Archive independently reviewed public evidence, never replay dispatch drivers."""
from pathlib import Path
import datetime as dt, hashlib, json, shutil, subprocess
ROOT=Path('/root/projects/nativeCmpKit');HERE=Path(__file__).parent
REV='769bf7dea1ca69ac23ef74d7f7140303b130657a';MAIN='94d2492e99d5cbc060409d94d9f88febd06222d5';REPO='Apdelrahman1911/nativeCmpkit'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def get(p):return json.loads(p.read_bytes())
SRC=Path('/dev/shm/nativecmpkit-dispatch-769bf7de-20261027')
assert get(SRC/'receipt.json')['POST_invocations']==1 and get(SRC/'receipt.json')['run_id']==40528445496
for name in ('development-after-push.json','development-after-dispatch.json'):
 assert get(SRC/name)['commit']['sha']==REV
for name in ('main-before.json','main-after-push.json','main-after-dispatch.json'):
 assert get(SRC/name)['commit']['sha']==MAIN
assert get(SRC/'payload.json')=={'ref':'development/preview-hardening','inputs':{'profile':'navigation-geo-matrix'}}
request=get(SRC/'request.json')
assert request['endpoint']=='repos/'+REPO+'/actions/workflows/gradle.yml/dispatches' and request['exit_code']==0 and request['invocations']==1 and not request['automatic_retry']
assert get(SRC/'actions-permissions.json')=={'enabled':True,'allowed_actions':'all','sha_pinning_required':False}
assert get(SRC/'workflow-permissions.json')=={'default_workflow_permissions':'read','can_approve_pull_request_reviews':False}
assert get(SRC/'pages-before.json')['status'] is None and get(SRC/'pages-before.json')['build_type']=='workflow'
assert get(SRC/'releases-before.json')==[]
admission=get(SRC/'concurrency-admission.json')
assert admission['maximum_combined_library_jobs']==2 and admission['new_matrix_max_parallel']==1
assert admission['existing_run_ids']==[40522929974] and admission['no_unchanged_UIKit_or_consumer_redispatch']
run=get(SRC/'run-readback.json')
assert run['id']==40528445496 and run['head_sha']==REV and run['repository']['full_name']==REPO and run['run_attempt']==1
assert sha(ROOT/'.github/workflows/gradle.yml')==get(SRC/'preflight.json')['source_sha256']
assert get(SRC/'push.json')['exit_code']==0 and not get(SRC/'push.json')['automatic_retry']
assert b'--force' not in (SRC/'push.log').read_bytes()
OUT=ROOT/'docs/development/evidence/ci-dispatch-769bf7de-20261027'
assert not OUT.exists();shutil.copytree(SRC,OUT)
rows=[]
for p in sorted(SRC.rglob('*')):
 if p.is_file():
  target=OUT/p.relative_to(SRC);assert sha(p)==sha(target)
  rows.append({'path':p.relative_to(SRC).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
assert len(rows)==29
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'evidence_integrity_passed':True,'source_revision':REV,'run_id':40528445496,'single_request_readback_verified':True,'main_preserved':MAIN,'public_dispatch_archive_files':rows,'raw_job_logs_archived':False,'source_revision_is_dispatch_binding_not_runtime_pass':True,'publication_performed':False,'release_readiness_certified':False}
(OUT/'lead-archive-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
shutil.copyfile(Path(__file__),OUT/'archive.py')
for name in ('reviewer-red001.py','reviewer-red001.json'):shutil.copyfile(HERE/name,OUT/name)
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.rglob('*')) if p.is_file()))
UI_SRC=Path('/dev/shm/nativecmpkit-uikit-success-20261027/review-archive')
assert get(UI_SRC/'lead-independent-review.json')['evidence_integrity_passed'] is True
UI_OUT=ROOT/'docs/development/evidence/github-actions/40522929974/attempt-2'
assert not UI_OUT.exists();shutil.copytree(UI_SRC,UI_OUT)
for p in UI_SRC.rglob('*'):
 if p.is_file():assert sha(p)==sha(UI_OUT/p.relative_to(UI_SRC))
print(json.dumps({'dispatch_archive_files':len(rows),'reviewed_iOS_archive_files':len(list(UI_OUT.rglob('*')))-1,'runtime_totals':get(UI_OUT/'lead-independent-review.json')['totals'],'no_GitHub_mutations':True,'packages_releases_deployments':False},indent=2))
