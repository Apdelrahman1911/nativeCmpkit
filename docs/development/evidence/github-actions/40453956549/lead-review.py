"""Read-only initial-attempt review; bounded public log stays in memory only.

Do not substitute a later successful rerun for this preserved early failure.
"""
from pathlib import Path
import datetime as dt, hashlib, json, subprocess, re
OUT=Path(__file__).resolve().parent
RUN=40453956549; REV='be32a7d61bdf025cf1a115aea9ac07c8062f3623'; JOB=122022996018
run=json.loads((OUT/'run-final.json').read_text()); jobs=json.loads((OUT/'jobs-final.json').read_text())['jobs']
assert run['id']==RUN and run['head_sha']==REV and run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1
assert run['repository']['full_name']=='Apdelrahman1911/nativeCmpkit' and run['event']=='workflow_dispatch' and run['head_branch']=='development/preview-hardening'
assert json.loads((OUT/'artifacts-final.json').read_text())=={'artifacts':[],'total_count':0}
assert json.loads((OUT/'dispatch-body.json').read_text())=={'ref':'development/preview-hardening','inputs':{'profile':'ios-ui'}}
dispatch=json.loads((OUT/'dispatch-receipt.json').read_text())
assert dispatch['expected_source_sha']==REV and dispatch['exit_code']==0 and not dispatch['dispatch_retried'] and not dispatch['packages_releases_or_deployments_requested']
assert dispatch['existing_active_run_ids']==[] and dispatch['maximum_combined_runtime_slots']==2
for n in ['branch-before.json','branch-after.json']:assert json.loads((OUT/n).read_text())['object']['sha']==REV
assert json.loads((OUT/'main-after.json').read_text())['object']['sha']=='94d2492e99d5cbc060409d94d9f88febd06222d5'
assert json.loads((OUT/'actions-permissions.json').read_text())=={'enabled':True,'allowed_actions':'all','sha_pinning_required':False}
assert json.loads((OUT/'workflow-permissions.json').read_text())=={'default_workflow_permissions':'read','can_approve_pull_request_reviews':False}
pages=json.loads((OUT/'pages.json').read_text());assert pages['status'] is None and pages['build_type']=='workflow'
job=next(j for j in jobs if j['id']==JOB);assert job['status']=='completed' and job['conclusion']=='failure'
step=next(s for s in job['steps'] if s['number']==5)
assert step['name']=='Install the exact compiler using hosted-runner rustup (no bootstrap script)' and step['conclusion']=='failure'
assert all(s['conclusion']=='skipped' for s in job['steps'] if 6<=s['number']<=14)
assert next(j for j in jobs if j['id']==122022827903)['conclusion']=='success'
raw=subprocess.check_output(['gh','api',f'repos/Apdelrahman1911/nativeCmpkit/actions/jobs/{JOB}/logs'])
assert len(raw)<=2*1024*1024
lines=raw.decode('utf-8-sig',errors='strict').splitlines()
suffix='client error (Connect): dns error: failed to lookup address information: nodename nor servname provided, or not known'
selected=[{'line':i+1,'original_safe_suffix':suffix} for i,s in enumerate(lines)
          if 'https://static.rust-lang.org/dist/channel-rust-1.98.0.toml.sha256' in s and s.endswith(suffix)]
assert len(selected)==1 and not any('NATIVECMPKIT_UIKIT_ACTIVE ' in s or '##teamcity[' in s for s in lines)
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':RUN,'run_attempt':1,'source_revision':REV,'url':run['html_url'],'run_conclusion':'failure','job_id':JOB,'job_url':job['html_url'],'evidence_integrity_passed':True,'artifact_count':0,'uploaded_xml_reports':0,'library_native_or_packaged_consumer_methods_executed':0,'runtime_recorded':False,'pinned_rust_version':'1.98.0','failed_step':step,'bounded_actual_job_diagnostics':{'log_bytes':len(raw),'log_sha256':hashlib.sha256(raw).hexdigest(),'full_log_archived':False,'exact_safe_dns_suffix_observations':selected},'root_cause':'Hosted macOS runner could not resolve static.rust-lang.org during exact Rust1.98.0 installation. It failed before SDK/runtime/cache/planning/application execution; this is not an application delegate regression result. Artifact upload independently fails closed because no evidence files exist.','next_action':'One lead-scheduled failed-job-only rerun of the same immutable source; do not rerun the successful tooling or Android job, change compiler, hide this failure or fabricate test evidence.','scope':'Initial attempt infrastructure failure, zero genuine UIKit tests/activation. Previous actual delegate-initialization failure and test-only repair remain separately archived; no issue/release gate cleared.','issues_closed':0,'packages_published':False,'release_created':False,'release_readiness_certified':False,'review_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT/'lead-independent-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:review[k] for k in ['run_id','run_attempt','evidence_integrity_passed','artifact_count','library_native_or_packaged_consumer_methods_executed','root_cause']},indent=2))
