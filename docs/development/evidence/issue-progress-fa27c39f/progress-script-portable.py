from pathlib import Path
import subprocess,json,hashlib,datetime as dt
import sys
sys.path.insert(0, "/root/projects/nativeCmpKit/scripts/migration")
from github_json import json_pages
ROOT=Path('/root/projects/nativeCmpKit');REPO='Apdelrahman1911/nativeCmpkit';SHA='fa27c39fc307b51354d98e0a54a7f6e64e60c4fc';OUT=ROOT/'docs/development/evidence/issue-progress-fa27c39f'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==SHA
assert subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip()=='https://github.com/Apdelrahman1911/nativeCmpkit.git'
assert OUT.is_dir();assert not (OUT/"receipt.json").exists()
def get(path,paginate=False):
 cmd=['gh','api','--method','GET']
 if paginate:cmd+=['--paginate']
 r=subprocess.run(cmd+[path],cwd=ROOT,capture_output=True,timeout=90)
 if r.returncode:raise RuntimeError('Readback failed; do not automatically retry a mutation')
 return json_pages(r.stdout.decode()) if paginate else json.loads(r.stdout)
def put(name,x):
 with (OUT/name).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
link=f'https://github.com/{REPO}/blob/{SHA}/docs/development'
items=[(149,'IO-022'),(86,'NATIVE-031'),(40,'BUILD-007')];receipts=[]
for number,finding in items:
 before=get(f'repos/{REPO}/issues/{number}');assert not before.get('pull_request') and before['state']=='open'
 put(f'issue-{number}-portable-before.json',before)
 marker=f'<!-- nativecmpkit-progress:cache-and-android-fa27c39f:{finding} -->'
 if number in (149,86):
  body=f'''{marker}
### Partial verification: owning Windows ACL/reparse cache repair

The repaired source at `6930e1732d12b36dece44171341a918cdde1234c` passed [Windows run40429039349](https://github.com/{REPO}/actions/runs/40429039349): **77 fresh library executions,77 passed**,14 XML reports (picker47/share30), one exact AppKit-only N/A and **zero unexpected skips**.

[Independent Git/source/ZIP/XML review]({link}/evidence/github-actions/40429039349/lead-independent-review.json) and [paired red/green review]({link}/evidence/github-actions/40429039349/paired-cache-review.json) confirm that all **five originally failed ACL/junction methods pass**, no original test was removed, all other original outcomes are unchanged and six additive cache regressions pass. The prior actual Windows failure and earlier Linux red/25-pass source-held runs remain archived.

The owning implementations now reject foreign owner/POSIX/Windows ACL mutation rights on directories and payloads, reject non-symlink junction/reparse paths and dot segments, explicitly create/read back private new entries, never chmod/repair existing unsafe caches, and preserve verified extraction/fallback/cleanup contracts. Public packages/JNI/native filenames remain unchanged. [Technical scope and residual risks]({link}/native-cache-security.md).

**Keep this issue open.** The original loaded-DLL/multi-process, native-parent/ownership, foreign-owner/read-only/noexec, other-host matrix, late ACL/TOCTOU, provenance/legal/ABI and strict packaged-consumer requirements are not all verified. Hashes are not authenticity, this is not a demonstrated exploit or full release certification, and no package/release/deployment was published.
'''
 else:
  body=f'''{marker}
### Contained CI verification progress, dependency gate still unresolved

The owner-authorized all-actions/no-required-SHA-pinning policy remains in place with read-only verification tokens and no persisted checkout credentials. The held-source [21-command preflight]({link}/evidence/ci-preflight-20261027-003/lead-review.json) passed **812 Python tooling methods**, including132 CI methods, plus strict MkDocs and actionlint. These are not library or dependency-trust passes.

The scoped Windows cache run [40429039349](https://github.com/{REPO}/actions/runs/40429039349) passed77 actual library executions; paired source/ZIP/XML review and limitations are archived.

Android [40425272170](https://github.com/{REPO}/actions/runs/40425272170) remains a reviewed **zero-test failure** despite passed XML/UTP guards and clean owned-emulator shutdown. Actual JDK17/AGP9.4.0/Gradle9.7.1 method invocation reproduces immutable serial-list mutation at `DeviceProviderInstrumentTestTask.java:547`, including when the setter receives a mutable list. The [owning selector repair and evidence]({link}/android-device-selection.md) use AGP's supported child-only `ANDROID_SERIAL` provider contract, reject inherited conflicts before quarantine and require empty target-option lists. The fixed init script compiled/configured; [new immutable Android verification40430738675](https://github.com/{REPO}/actions/runs/40430738675) is running, **not a passing result**.

**Keep BUILD-007 open.** Root/convention resolved-graph locking/artifact+metadata verification, actual runtime-witness completeness, advisory/license/provenance review, native/ABI/consumer and complete target gates remain unsatisfied. No packages, releases or deployments were published and no stable-CI/release certification is asserted.
'''
 pages=get(f'repos/{REPO}/issues/{number}/comments?per_page=100',True);assert len(pages)<=10
 comments=[c for page in pages for c in page];matches=[c for c in comments if marker in (c.get('body') or '')];assert len(matches)<=1
 (OUT/f'issue-{number}-draft.md').write_text(body)
 if matches:
  comment=matches[0];outcome='existing-marker-preserved'
 else:
  payload=OUT/f'issue-{number}-post.json';put(payload.name,{'body':body})
  request_time=dt.datetime.now(dt.timezone.utc).isoformat()
  r=subprocess.run(['gh','api','--method','POST',f'repos/{REPO}/issues/{number}/comments','--input',str(payload)],cwd=ROOT,capture_output=True,timeout=90)
  put(f'issue-{number}-post-attempt.json',{'requested_utc':request_time,'exit_code':r.returncode,'response_sha256':hashlib.sha256(r.stdout).hexdigest(),'retried':False})
  if r.returncode:raise RuntimeError('Post failed/uncertain; reconcile before retry')
  response=json.loads(r.stdout);comment=get(f'repos/{REPO}/issues/comments/{response["id"]}');assert comment['body']==body
  outcome='created-and-exact-readback'
 put(f'issue-{number}-comment-readback.json',comment)
 after=get(f'repos/{REPO}/issues/{number}');put(f'issue-{number}-after.json',after)
 assert before['body']==after['body'] and before['state']==after['state'] and before['title']==after['title']
 assert sorted(l['name'] for l in before['labels'])==sorted(l['name'] for l in after['labels'])
 receipts.append({'issue':number,'finding':finding,'comment_id':comment['id'],'url':comment['html_url'],'outcome':outcome,'body_sha256':hashlib.sha256(comment['body'].encode()).hexdigest(),'issue_body_title_state_labels_unchanged':True,'issue_closed':False})
 print(json.dumps(receipts[-1]),flush=True)
put('receipt.json',{'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':SHA,'comments':receipts,'issues_closed':0,'publication_performed':False})
(OUT/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
