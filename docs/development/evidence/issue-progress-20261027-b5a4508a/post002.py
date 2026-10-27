"""One additive evidence-bound progress comment; never changes issue state/body/labels."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
R=Path('/root/projects/nativeCmpKit');O=Path(__file__).resolve().parent/'attempt-2';O.mkdir(exist_ok=False);REPO='Apdelrahman1911/nativeCmpkit';SHA='b5a4508a8d28f9937c456db2895b4ae09c4a9343';issue=40
mark='<!-- nativecmpkit-progress:BUILD-007:20261027-b5a4508a-owned-cleanup -->'
link='https://github.com/'+REPO+'/blob/'+SHA+'/'
body=mark+'''\n## Contained, scoped resource-ownership progress — 2026-10-27

The additive implementation/evidence is now preserved at immutable `'''+SHA+'''` on `development/preview-hardening`; `main` remains at its issue-sync checkpoint. This is **not issue closure or release readiness**.

- The real 20s timeout reproduction retained a separately validated detached Gradle daemon after the old controller returned. The probe's later cleanup was not controller success. [Original red]('''+link+'''docs/development/evidence/build/dependency-fixtures/owned-daemon-timeout-red-20261027/lead-review.json).
- The owning controlled-fixture repair passes **five actual installed Gradle9.7.1/JDK17 Linux invocations**: normal8.860s, timeout20.880s, SIGINT7.625s, SIGTERM7.220s and TERM-resistant/KILL25.393s. Owning controllers—not external probes—stop/reap exact verified client/daemon leases and restore pidfd/directory/signal/subreaper state. All15 recorded PIDs were absent on independent review. [92-member original archive/source/runtime review]('''+link+'''docs/development/evidence/build/dependency-fixtures/owned-daemon-cleanup-20261027/lead-independent-review.json).
- **380/380 dependency Python methods** pass (171core/148observer/61owner). These are tooling tests, not library/native/consumer tests. [ADR0007]('''+link+'''docs/decisions/0007-owned-gradle-fixture-processes.md) limits the helper to a dedicated controlled single-root Linux installed-Gradle scope; the passive observer gains no process control.
- A later new-file/staged EOF whitespace failure and the lead shell's local commit continuation are preserved, not amended or hidden. Explicit successor010 keeps009 immutable; the complete parser AST/eight owning implementation inputs are unchanged. The five actual009 cases **are not recounted as fresh010 executions**. [Correction/red]('''+link+'''docs/development/evidence/staged-preflight-new-file-red-20261027/receipt.json).
- Corrective held preflight015 passes23 commands/1014 overlapping Python methods, both cached/worktree whitespace checks, strict local MkDocs/actionlint and six output anchors.15,420 inputs remain held. Four additive-document checks pass separately; neither archived receipt circularly certifies a later commit. [Preflight review]('''+link+'''docs/development/evidence/ci-preflight-20261027-015/lead-review.json).

**Remaining acceptance:** ordinary root/convention/composite graph locks/checksums, complete script/tool/cache/tamper scenarios, independent full advisory/license/provenance review, ordinary wrappers/other hosts/arbitrary descendants/controller-SIGKILL cleanup, and applicable consumer/native/platform gates. The issue remains **unresolved/open**; its original technical body, labels and acceptance scope are preserved. Actions remain enabled/all/no mandatory SHA pinning with read-only verification; no package, release, snapshot or deployment is authorized by these results.
'''
def call(args):return subprocess.check_output(['gh','api',*args],cwd=R,timeout=90)
def get(path,name):
 b=call([path]);(O/(name+'.json')).write_bytes(b);return json.loads(b)
assert get('repos/'+REPO+'/git/ref/heads/development/preview-hardening','development')['object']['sha']==SHA
before=get('repos/'+REPO+'/issues/'+str(issue),'issue-before');assert before['state']=='open'
comments=[]
for page in range(1,101):
    current=get('repos/'+REPO+'/issues/'+str(issue)+'/comments?per_page=100&page='+str(page),'comments-page-'+str(page))
    assert isinstance(current,list)
    comments.extend(current)
    if len(current)<100:break
else:raise ValueError('Comments pagination limit exceeded; do not post')
(O/'comments-before.json').write_text(json.dumps(comments,indent=2)+'\n');existing=[v for v in comments if mark in v.get('body','')]
assert len(existing)<=1
(O/'intended-comment.md').write_text(body)
if existing:
 posted=existing[0];assert posted['body']==body;did_post=False
else:
 payload=O/'payload.json';payload.write_text(json.dumps({'body':body})+'\n')
 # Exactly one POST. On uncertain failure, leave evidence and reconcile via GET;
 # never blindly retry or alter the issue body to imitate success.
 b=call(['--method','POST','repos/'+REPO+'/issues/'+str(issue)+'/comments','--input',str(payload)])
 (O/'posted-response.json').write_bytes(b);posted=json.loads(b);did_post=True
read=get('repos/'+REPO+'/issues/comments/'+str(posted['id']),'comment-readback');assert read['body']==body
assert read['user']['login']=='Apdelrahman1911'
after=get('repos/'+REPO+'/issues/'+str(issue),'issue-after');assert before['body']==after['body'] and before['state']==after['state'] and [x['name'] for x in before['labels']]==[x['name'] for x in after['labels']]
r={'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'repository':REPO,'source_revision':SHA,'finding':'BUILD-007','issue_number':issue,'comment_id':read['id'],'comment_url':read['html_url'],'marker':mark,'posted_once':did_post,'readback_verified':True,'body_sha256':hashlib.sha256(body.encode()).hexdigest(),'issue_body_labels_state_preserved':True,'issue_closed':False,'release_readiness_certified':False,'publication_performed':False}
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
