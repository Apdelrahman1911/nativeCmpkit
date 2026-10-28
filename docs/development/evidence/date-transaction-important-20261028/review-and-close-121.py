from pathlib import Path
import datetime,hashlib,json,subprocess,sys
R=Path('/root/projects/nativeCmpKit'); D=Path(__file__).parent
sys.path.insert(0,str(R/'scripts/ci')); import library_tests as lt

def get(*args): return subprocess.check_output(args,cwd=R)
def own_blobs(sha,inputs):
 names=list(inputs)
 raw=get('git','cat-file','--batch',) if False else subprocess.run(['git','cat-file','--batch'],cwd=R,input=''.join(f'{sha}:{p}\n' for p in names).encode(),capture_output=True,check=True).stdout
 pos=0; bad=[]
 for p in names:
  end=raw.index(b'\n',pos); header=raw[pos:end].split(); assert header[1]==b'blob',(sha,p,header)
  n=int(header[2]); start=end+1; blob=raw[start:start+n]; pos=start+n+1
  if hashlib.sha256(blob).hexdigest()!=inputs[p]:bad.append(p)
 assert not bad,(sha,bad)
 return len(names)
paths={
 'local001':D/'local001', 'local002':D/'local002',
 'wasm005':D/'browser005/library-evidence-browser-wasm/build/ci-verification/browser-wasm',
 'android007':D/'android007/library-evidence-android-device-api35/build/ci-verification/android-device-api35/library',
 'js009':D/'js009/artifacts/library-evidence-browser-js/build/ci-verification/browser-js',
}
review=[]; snapshots={}
for key,p in paths.items():
 receipt=json.load(open(p/'receipt.json')); sha=receipt['source_revision']; before=json.load(open(p/'inputs-before.json')); after=json.load(open(p/'inputs-after.json'));assert before==after
 assert receipt.get('source_revision_after',sha)==sha and not receipt.get('source_tree_dirty',False)
 count=own_blobs(sha,before);snapshots[key]=before
 if key.startswith('local'):
  cases=[]
  for report in receipt['reports']:
   b=(p/report['file']).read_bytes(); assert hashlib.sha256(b).hexdigest()==report['sha256'] and report['is_fresh']; c=lt.junit_cases(b);assert c==report['cases']; cases.extend(c)
 else:
  assert receipt['passed'] and not receipt['errors'] and receipt['execution']['exit_code']==0
  assert not receipt['changed_inputs']; assert all(n==1 for n in receipt['task_execution_markers'].values())
  root=p
  while not (root/'calf-ui').is_dir():root=root.parent; assert root!=root.parent
  cases=[]
  for module in receipt['modules']:
   for report in module['reports']:
    b=(root/report['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==report['sha256'];cases.extend(lt.junit_cases(b))
  assert cases==receipt['modules'][0]['testcases']
 counts=lt.case_counts(cases)
 assert counts['passed']=={'local001':6,'local002':2,'wasm005':4,'android007':4,'js009':4}[key]
 assert counts['failures']==(2 if key=='local001' else 0) and not counts['errors'] and not counts['skipped']
 runtime=json.load(open(p/'runtime.json'));assert runtime['source_revision']==sha and not runtime['source_tree_dirty']
 review.append(dict(selection=key,source_revision=sha,own_git_blob_inputs_matched=count,counts=counts,command=receipt['command'],execution=receipt['execution'],xml_cases=cases))
# Production contract and all date state inputs are unchanged across accepted revisions.
production=[p for p in snapshots['js009'] if p.startswith('calf-ui/src/') and '/datepicker/' in p and 'Test/' not in p and '/test/' not in p and ('Main/' in p)]
assert production
for p in production:
 assert len({i[p] for i in snapshots.values()})==1,p
 assert hashlib.sha256((R/p).read_bytes()).hexdigest()==snapshots['js009'][p]
shared='calf-ui/src/materialTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/CompactDateTransactionScenarios.kt'
assert all(snapshots[k][shared]==snapshots['js009'][shared] for k in ('local002','wasm005','android007'))
assert hashlib.sha256((R/shared).read_bytes()).hexdigest()==snapshots['js009'][shared]
diff=get('git','diff','c8b5c614828e3255dcb07836da6301e6347fe401','8120c27ace91a73e73c23a80e808a869bfb6345b','--',shared).decode()
(D/'null-fixture-owning-diff.patch').write_text(diff)
assert 'EditableText' in diff and 'rejectCapturedConfirmAfterRulesTighten' not in diff and 'replaceOwnerAndYearRangeWithoutTransplantingScratchState' not in diff and 'rejectAllDaysThenCancelAndReopenWithRecoveredRules' not in diff
controller=json.load(open(D/'android007/library-evidence-android-device-api35/build/ci-verification/android-device-api35/controller.json'))
assert controller['passed']
run=json.load(open(D/'js009/run-readback.json')); assert run['status']=='completed' and run['conclusion']=='success' and run['head_sha']=='fa125cf388845f22fe26f0b17ce4a9a0d65859c1'
criteria=json.load(open(R/'docs/audit/findings/UI.json'));criteria=next(x for x in criteria if x['id']=='UI-006')['required_tests']
out=dict(reviewed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),original_criteria=criteria,accepted_platform_method_pairs=20,authored_scenarios=4,production_date_inputs_identical_and_current=production,results=review,scope='Actual public Material dialog semantics and event-boundary behavior; Android API35 emulator is not a physical device, host is Robolectric. Browser adapters return native TestResult/Promise; unusually short XML timing is not profiling or broader native proof. No iOS UIKit claim or release/consumer/ABI/security gate certification.',packages_releases_deployments_published=False)
(D/'source-and-acceptance-review.json').write_text(json.dumps(out,indent=2)+'\n')
print('All three original criteria, actual source, runtime and XML accepted; 20 accepted target-method pairs from four authored scenarios.',flush=True)
repo='repos/Apdelrahman1911/nativeCmpkit';before=json.loads(get('gh','api',repo+'/issues/121'));assert before['state']=='open' and '<!-- nativecmpkit-item:audit:UI-006 -->' in before['body']
(D/'issue-121-before-closure.json').write_text(json.dumps(before,indent=2)+'\n')
comment='''<!-- nativecmpkit-resolution:UI-006:date-transaction-fa125cf3 -->
## Verified fix — closing directly after important tests and source/result review

The Material compact picker now owns its scratch transaction by the hoisted state, cancels rather than transplants on replacement, disables forbidden commits, and revalidates the latest rule at the actual confirmation event boundary. Public APIs and the intentional null-selection policy remain unchanged.

All **three original acceptance criteria** pass in four actual public Compose dialog scenarios: March15 → March16 → tighten maximumMarch15 and invoke the previously enabled real confirmation action before recomposition; replacement owner/rules/yearRange; NoDates; and actual editable-input clearing, cancellation, reopening and null confirmation.

- **JS4/4**, fresh XML, zero failures/errors/skips at immutable **fa125cf388845f22fe26f0b17ce4a9a0d65859c1**, [run40652867059](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40652867059), library exit0/340.09s. The owning JS fixture now awaits real Skiko initialization and returns the flattened test Promise; failures are not caught or discarded.
- **Android API35 instrumentation4/4**, fresh XML, library exit0/93.05s at **b6f647b890b46f2409f8fa0797444fc70633eca2**, [run40651576776](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40651576776). Actual emulator, SELinux Enforcing, clean owned shutdown; no forced termination. This is not a physical-device claim.
- **Wasm4/4**, fresh XML at **0f02a0997024d690e9ccd384a7b4079448903afa**, [run40650621351](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40650621351). That whole two-browser run remains failed on its original JS initialization defect; its accepted Wasm result was not replayed.
- **Desktop4/4 and Android-host4/4 accepted** using three unchanged successful cases each at **c8b5c614** plus only the corrected null-input case each at **8120c27a** (fresh1/1 each, exit0/63.02s). The original combined run remains failed3/4 each: the fixture mistakenly tested the merged visible Date label rather than the actual empty editable value. Assertions outside that owning null fixture did not change.

Reviewed actual source, all recorded inputs against their own immutable Git blobs, exact XML identities/counts and runtime/controller receipts. **20 accepted platform-method pairs, four authored scenarios**, not20 unique methods. Browser XML durations are very short; Promise-supporting adapters/actual returned TestResult were source-reviewed, but these timings are not a performance measurement or proof of broader native behavior.

Original failures and technical issue body/labels/upstream references remain preserved. Full iOS/native/minimum-platform, consumer, ABI, dependency/legal/security and release gates remain separate. No packages, releases or deployments were published. Detailed evidence will be committed next, without delaying this direct verified closure.
'''
(D/'issue-121-resolution-comment.md').write_text(comment)
created=json.loads(get('gh','api','--method','POST',repo+'/issues/121/comments','-f','body='+comment)); assert created['body']==comment
(D/'issue-121-comment-readback.json').write_text(json.dumps(created,indent=2)+'\n')
closed=json.loads(get('gh','api','--method','PATCH',repo+'/issues/121','-f','state=closed','-f','state_reason=completed'))
(D/'issue-121-closure-response.json').write_text(json.dumps(closed,indent=2)+'\n')
read=json.loads(get('gh','api',repo+'/issues/121'))
assert read['state']=='closed' and read['state_reason']=='completed'
assert read['body']==before['body'] and read['title']==before['title'] and [x['name'] for x in read['labels']]==[x['name'] for x in before['labels']]
(D/'issue-121-closure-readback.json').write_text(json.dumps(read,indent=2)+'\n')
print('Issue #121 closed/completed and original body/title/labels retained:',read['html_url'],read['closed_at'],flush=True)
