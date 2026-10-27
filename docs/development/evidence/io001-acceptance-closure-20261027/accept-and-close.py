from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

root=Path('/root/projects/nativeCmpKit')
out=Path(__file__).parent
repo='Apdelrahman1911/nativeCmpkit'
revision='fc73dd47cf35085e6f9e2b964ae126eefe2be246'
marker='<!-- nativecmpkit-resolution:IO-001:40587910531 -->'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def api(name,endpoint,method='GET',payload=None):
    command=['gh','api',endpoint,'--method',method]
    if payload is not None: command+=['--input','-']
    run=subprocess.run(command,input=json.dumps(payload).encode() if payload is not None else None,capture_output=True)
    (out/(name+'.json')).write_bytes(run.stdout)
    (out/(name+'.stderr')).write_bytes(run.stderr)
    if run.returncode: raise RuntimeError(f'{method} {endpoint} failed; inspect saved result before any retry')
    return json.loads(run.stdout)

review_path=root/'docs/development/evidence/github-actions/40587910531/lead-independent-review.json'
review=json.loads(review_path.read_bytes())
assert review['evidence_integrity_passed'] and review['source_revision']==revision
assert review['totals']['passed']==review['totals']['executed']==47
assert review['totals']['failures']==review['totals']['errors']==review['totals']['skipped']==0
assert review['actual_xml_reports']==8 and len(review['mandatory_native_cases'])==22
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==revision
baseline_path='docs/audit/findings/IO.json'
baseline=(root/baseline_path).read_bytes()
assert baseline==subprocess.check_output(['git','show','94d2492e99d5cbc060409d94d9f88febd06222d5:'+baseline_path],cwd=root)
finding=next(f for f in json.loads(baseline) if f['id']=='IO-001')
required=['Zero-byte valid file','One-byte and binary round trips','Length helper at Int.MAX_VALUE and Int.MAX_VALUE+1 without huge allocations','Missing/unreadable file errors','ASan/native guarded-buffer integration where supported','Coil error propagation']
assert finding['required_tests']==required
rows=[('NativeReadSafetyTest',['readsARealEmptyNSDataFileWithoutAddressOfZero']),
      ('NativeReadSafetyTest',['readsARealOneByteNSDataFile','realNativeMemcpyAndStreamHaveIdenticalBinaryBytes']),
      ('NativeGuardedCopyTest',['nativeLengthBoundaryRejectsUnrepresentableCountsWithoutAllocation']),
      ('NativeReadSafetyTest',['missingFileIsNotEmptyOrAFile','unreadableFileIsNotSilentlyConvertedToEmptyData']),
      ('NativeGuardedCopyTest',['emptyFoundationDataNeedsNoPointer','validatedFoundationCopyDoesNotCrossSourceOrDestinationGuardPages','tooSmallGuardedDestinationIsRejectedBeforeAnyNativeWrite','positiveLengthNeedsANonNullDestination']),
      ('NativeKmpFileFetcherTest',['missingAndUnreadableFilesPropagateThroughActualCoilRequests','actualCoilDecoderCancellationClosesTransferredNativeSource','actualCoilDecoderFailureClosesTransferredNativeSource'])]
acceptance=[]
for required_test,(cls,methods) in zip(required,rows,strict=True):
    accepted=[]
    for method in methods:
        matches=[case for case in review['actual_cases'] if case['classname'].endswith('.'+cls) and case['name']==method+'[iosSimulatorArm64]']
        assert len(matches)==1 and matches[0]['status']=='passed'
        accepted+=matches
    acceptance.append({'original_requirement':required_test,'status':'accepted','actual_passing_cases':accepted})
for path,digest in review['reviewed_current_IO_Coil_source_hashes'].items(): assert sha((root/path).read_bytes())==digest
copy=(root/'calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/NativeDataCopy.kt').read_text()
read=(root/'calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt').read_text()
assert 'memcpy' not in read and 'return data.toCheckedByteArray()' in read
assert copy.index('val size = checkedByteArraySize(length)') < copy.index('if (size == 0)') < copy.index('return ByteArray(size)')
assert 'getBytes(destination, length = count.toULong())' in copy
ledger=next(f for f in json.loads((root/'docs/development/resolutions/IO.json').read_text()) if f['id']=='IO-001')
accepted={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'finding':'IO-001','issue_number':4,'source_revision':revision,'run_id':40587910531,'run_url':review['run_url'],'original_finding_sha256':sha(baseline),'review_sha256':sha(review_path.read_bytes()),'all_six_original_requirements_accepted':True,'criteria':acceptance,'prior_remaining_preserved':ledger['remaining'],'scope_limits':['Native guarded-buffer alternative accepted; not an ASan run.','Actual local Foundation/Coil/owned descriptor integration on iPhone simulator, not physical-device or external-provider grants.','Separate picker/UI/security-scope/device/minimum-platform/legal/dependency/provenance/consumer/API-ABI/release gates remain under IO-005/IO-007/IO-008 and the release-readiness index.','Prior KLIB/no-runtime, browser/host and old failed observations remain historical; no result is relabeled.'],'publication_performed':False,'release_readiness_certified':False}
(out/'original-acceptance.json').write_text(json.dumps(accepted,indent=2)+'\n')
print('All six original IO-001 criteria accepted against exact immutable runtime reports.',flush=True)
issue=api('issue-preflight','repos/'+repo+'/issues/4')
assert issue['number']==4 and issue['state']=='open' and '<!-- nativecmpkit-item:audit:IO-001 -->' in issue['body']
assert all(test in issue['body'] for test in required)
comments=api('comments-preflight','repos/'+repo+'/issues/4/comments?per_page=100')
assert len(comments)<100 and not any(marker in c['body'] for c in comments)
main=api('main-before','repos/'+repo+'/git/ref/heads/main')
assert main['object']['sha']=='94d2492e99d5cbc060409d94d9f88febd06222d5'
body=f'''{marker}
## Verified resolution — IO-001

The underlying iOS allocation/copy mismatch and empty-buffer pointer access are fixed at `{revision}`. Length is validated before allocation/pinning; empty data returns without an element pointer; receiver-owned `NSData.getBytes` copies only the checked count. Failed native reads throw instead of reporting an empty-success value. Existing public signatures/packages are retained; the bounded streaming overload is additive.

**Reviewed execution:** [run 40587910531]({review['run_url']}), immutable revision above, iPhone/iOS simulator on arm64 macOS. **47/47 actual library executions (IO40/Coil7), eight fresh XML reports; zero failures/errors/skips.** All 22 mandatory native scenarios executed. Exact Git inputs, task execution, XML hashes/timestamps and SDK/runtime correspondence were independently reviewed.

All six original acceptance criteria pass:
- Zero-byte valid file: actual Foundation empty-file read.
- One-byte/binary round trips: actual Foundation and real streaming reads with signed/binary bytes.
- `Int.MAX_VALUE` / `+1`: shared checked-length helper executed natively, without giant allocations.
- Missing/unreadable errors: actual missing path and owned chmod-unreadable file; restored file remains readable.
- Native guarded-buffer integration: real Darwin mmap/mprotect source/destination guard pages and rejected undersized/null buffers. This is the specified native guarded-buffer alternative, **not an ASan run**.
- Coil propagation: actual ImageLoader missing/unreadable errors and actual decoder failure/cancellation after transfer, with real source descriptor closure.

Closing this finding now that its required tests and source review pass. Physical-device/external-provider grants, separate picker/native-parent/security-scope issues, legal/dependency/provenance, full/minimum consumers and API/ABI remain independent open release gates. No package, release or deployment was published. Original finding/body/labels and historical evidence are retained.
'''
(out/'comment.md').write_text(body)
posted=api('comment-post','repos/'+repo+'/issues/4/comments','POST',{'body':body})
assert posted['body']==body
closed=api('issue-patch','repos/'+repo+'/issues/4','PATCH',{'state':'closed','state_reason':'completed'})
assert closed['state']=='closed'
current=api('issue-readback','repos/'+repo+'/issues/4')
comment=api('comment-readback','repos/'+repo+'/issues/comments/'+str(posted['id']))
after_comments=api('comments-readback','repos/'+repo+'/issues/4/comments?per_page=100')
assert current['state']=='closed' and current['state_reason']=='completed'
assert all(current[k]==issue[k] for k in ('body','title'))
assert sorted(x['name'] for x in current['labels'])==sorted(x['name'] for x in issue['labels'])
assert comment['body']==body and sum(marker in x['body'] for x in after_comments)==1
assert all(any(x['id']==old['id'] and x['body']==old['body'] for x in after_comments) for old in comments)
closed_issues=api('closed-issues-readback','repos/'+repo+'/issues?state=closed&per_page=100')
assert len(closed_issues)<100
numbers=sorted(x['number'] for x in closed_issues if 'pull_request' not in x)
assert numbers==[4,15,16,41,42,91,93,94,123,128,136,146,155,156,160,171]
final={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'finding':'IO-001','issue_number':4,'state':current['state'],'closed_at':current['closed_at'],'comment_id':posted['id'],'comment_url':posted['html_url'],'comment_sha256':sha(body.encode()),'POST_invocations':1,'PATCH_invocations':1,'original_body_title_labels_and_prior_comments_preserved':True,'all_six_original_requirements_accepted':True,'source_revision':revision,'run_id':40587910531,'new_issue_closures':1,'total_closed':len(numbers),'all_current_closed_numbers':numbers,'publication_performed':False,'release_readiness_certified':False}
(out/'closure-readback.json').write_text(json.dumps(final,indent=2)+'\n')
print(json.dumps(final,indent=2))
