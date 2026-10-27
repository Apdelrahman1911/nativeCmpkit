"""Read same-input immutable MIME regressions, then close only IO-016. No reruns/publication."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,xml.etree.ElementTree as ET,zipfile
root=Path('/root/projects/nativeCmpKit');out=Path(__file__).parent
repo='Apdelrahman1911/nativeCmpkit';run_id=40568592687;issue_id=148
marker='<!-- nativecmpkit-resolution:IO-016:40568592687 -->'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=root)
def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def save(name,data):(out/name).write_text(json.dumps(data,indent=2)+'\n')
def api(name,endpoint,method='GET',body=None):
 cmd=['gh','api','repos/'+repo+'/'+endpoint,'--method',method]
 if body is not None:cmd+=['--input','-']
 r=subprocess.run(cmd,input=json.dumps(body).encode() if body is not None else None,capture_output=True,timeout=90)
 (out/(name+'.json')).write_bytes(r.stdout)
 if r.stderr:(out/(name+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==0,'API failure: review saved response before any retry/mutation'
 return json.loads(r.stdout)
current=git('rev-parse','HEAD').decode().strip()
base=root/'docs/development/evidence/github-actions/40568592687'
review=json.loads((base/'lead-independent-review.json').read_bytes())
assert review['evidence_integrity_passed'] and review['run_id']==run_id and review['run_conclusion']=='success'
revision=review['source_revision'];slot=review['runtime_slots'][0]
assert len(review['runtime_slots'])==1 and slot['job_conclusion']=='success'
paths=['calf-file-picker/src/commonMain','calf-file-picker/src/commonTest','calf-file-picker/src/desktopMain','calf-file-picker/src/desktopTest','calf-file-picker/build.gradle.kts','calf-io/src/commonMain','calf-io/src/nonAndroidMain','calf-io/src/desktopMain','calf-io/build.gradle.kts','calf-core/src/commonMain','calf-core/src/nonAndroidMain','calf-core/src/desktopMain','calf-core/build.gradle.kts','convention-plugins','gradle','gradle.properties','gradlew','gradlew.bat','build.gradle.kts','settings.gradle.kts']
assert not git('diff','--name-only',revision,current,'--',*paths).strip(),'Affected source/dependencies changed: cannot reuse'
current_paths=git('ls-tree','-r','--name-only',current,'--',*paths).decode().splitlines()
hashes={p:sha((root/p).read_bytes()) for p in current_paths}
assert all(sha(git('show',current+':'+p))==digest for p,digest in hashes.items())
p=base/'raw'/str(slot['artifact_id']);p=p.with_suffix('.zip')
assert 'sha256:'+sha(p.read_bytes())==slot['artifact_digest']
artifacts=json.loads((base/'artifacts-final.json').read_bytes())['artifacts']
a=next(a for a in artifacts if a['id']==slot['artifact_id']);assert a['digest']==slot['artifact_digest'] and a['workflow_run']['head_sha']==revision
with zipfile.ZipFile(p) as z:
 receipt=json.loads(z.read('build/ci-verification/desktop-windows-x64/receipt.json'))
 before=json.loads(z.read('build/ci-verification/desktop-windows-x64/inputs-before.json'))
 after=json.loads(z.read('build/ci-verification/desktop-windows-x64/inputs-after.json'))
 assert before==after and not receipt['changed_inputs'] and not receipt['source_tree_dirty']
 assert receipt['source_revision']==receipt['source_revision_after']==revision and receipt['passed']
 assert receipt['execution']['exit_code']==0 and receipt['task_execution_markers'][':calf-file-picker:desktopTest']==1
 assert ':calf-file-picker:desktopTest' in receipt['command']
 held={p:d for p,d in hashes.items() if p in before};assert len(held)>=60
 assert all(before[p]==digest for p,digest in held.items())
 reports=[];cases=[]
 for n in z.namelist():
  if n.startswith('calf-file-picker/') and n.endswith('.xml') and ('MimeTypesTest' in n or 'MimeFilterRegressionTest' in n):
   raw=z.read(n);assert b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper()
   t=ET.fromstring(raw);assert all(int(t.attrib[k])==0 for k in ['failures','errors','skipped'])
   started=dt.datetime.fromisoformat(receipt['started_at_utc']);finished=dt.datetime.fromisoformat(receipt['finished_at_utc'])
   time=dt.datetime.fromisoformat(t.attrib['timestamp'].replace('Z','+00:00'));assert started<=time<=finished
   reports.append({'path':n,'sha256':sha(raw),'timestamp':t.attrib['timestamp']})
   for c in t.iter('testcase'):
    assert not any(c.find(k) is not None for k in ['failure','error','skipped'])
    cases.append({'classname':c.attrib['classname'],'name':c.attrib['name'],'seconds':c.attrib['time'],'status':'passed'})
 assert len(reports)==2 and len(cases)==9 and len({(c['classname'],c['name']) for c in cases})==9
finding=next(f for f in json.loads((root/'docs/audit/findings/IO.json').read_bytes()) if f['id']=='IO-016')
assert len(finding['required_tests'])==5
methods=[['protocolCaseFoldingDoesNotDependOnTurkishDefaultLocale'],['commaListsIgnoreOptionalWhitespaceAndWildcardEqualsScalarForExactPatterns'],['testFind','testFindWithWildcards','commaListsIgnoreOptionalWhitespaceAndWildcardEqualsScalarForExactPatterns','wildcardEscapesEmptyPatternsAndTrailingEscapesKeepTheirContract'],['adversarialWildcardDoesNotUseRecursiveExponentialSuffixExploration'],['retainedRegistrationIsSynchronizedWithTheReverseIndex']]
criteria=[]
for requirement,row in zip(finding['required_tests'],methods,strict=True):
 matched=[]
 for method in row:
  matches=[c for c in cases if c['name']==method+'[desktop]'];assert len(matches)==1;matched+=matches
 criteria.append({'original_requirement':requirement,'status':'accepted','actual_cases':matched})
source=(root/'calf-file-picker/src/desktopMain/kotlin/jodd/net/MimeTypes.kt').read_text()
assert 'Locale.getDefault()' not in source and 'Locale.ROOT' in source and ".split(',').map(String::trim)" in source
assert source.count('@Synchronized')==4 and 'reverseIndex[it].orEmpty()' in source
wildcard=(root/'calf-file-picker/src/desktopMain/kotlin/jodd/util/Wildcard.kt').read_text();assert 'while (input < string.length)' in wildcard and 'starInput' in wildcard
acceptance={'reviewed_utc':stamp(),'finding':'IO-016','current_revision':current,'tested_revision':revision,'run_id':run_id,'original_five_criteria_accepted':True,'criteria':criteria,'actual_cases_reviewed':9,'fresh_XML_in_original_execution':reports,'command':receipt['command'],'original_execution':receipt['execution'],'current_same_affected_inputs':hashes,'current_same_held_input_count':len(held),'reuse':'Previously executed immutable Windows XML, re-reviewed with identical affected source/tests/resources/dependencies. Zero new executions.','source_review':'Protocol Locale.ROOT, comma/trim/filter once, synchronized lookups/registration/reverse rebuild and iterative nonrecursive wildcard fallback. Jodd copyright retained.','limits':['Adversarial 50,000-character cases complete; no measured speedup/CPU/allocation claim or general input/latency guarantee.','Production resource is processed into the library-test classpath; this is not packaged Maven/ABI/legal/full-consumer acceptance, which remains independent.','Old desktop runtime omits during-test Android SDK metadata; MIME uses the inspected JDK/Windows source/resources, not Android SDK. No during-test SDK equality claim.','IO-015 actual native-filter policy/visibility remains open; this does not waive any release/security gate.'],'release_readiness_certified':False,'publication_performed':False}
save('acceptance.json',acceptance)
print('Reviewed9/9 MIME cases; all5 original IO-016 criteria accepted with unchanged affected inputs.',flush=True)
issue=api('issue-before','issues/'+str(issue_id));assert issue['state']=='open' and '<!-- nativecmpkit-item:audit:IO-016 -->' in issue['body']
assert all(req in issue['body'] for req in finding['required_tests'])
comments=api('comments-before','issues/'+str(issue_id)+'/comments?per_page=100');assert len(comments)<100 and not any(marker in c['body'] for c in comments)
body=f'''{marker}
## Verified resolution — IO-016

The owning MIME helpers now use `Locale.ROOT`, split on comma and trim/filter once, look up scalar filters through a reverse MIME index, synchronize retained registration/reads/rebuilds, and use iterative wildcard matching rather than recursive exponential suffix exploration. Jodd notices and existing API/module/package identities are retained.

**All five original acceptance criteria reviewed and passed:** Turkish `TIFF`/`IMAGE/PNG`; zero/multiple-space comma lists; scalar/wildcard equivalence and escaping; 50,000-character adversarial success/failure patterns; and 40 concurrent retained registrations with consistent forward/reverse lookup.

[Immutable Windows run{run_id}](https://github.com/{repo}/actions/runs/{run_id}) at `{revision}`: **9/9 relevant MIME methods**, two fresh XML (picker47/47 overall), Gradle exit0. The artifact digest, original fresh timestamps/test-task execution and all nine named outcomes were reviewed again. Current affected production/tests/resources/Gradle/dependency inputs are byte-identical to the tested revision. These existing results are reused explicitly; no new execution or repeated unchanged suite is claimed.

Closing directly after source/result review. Adversarial completion is not a measured CPU/allocation speedup or unrestricted latency guarantee. Library-test classpath resources are not a verified packaged Maven consumer/legal/ABI gate. IO-015 native-dialog filter visibility, other independent consumer/dependency/security/release gates remain open; historical during-test Android SDK scope is not certified. No package/release/deployment published. Original issue body/title/labels/history preserved.
'''
(out/'comment.md').write_text(body)
posted=api('comment-post','issues/'+str(issue_id)+'/comments','POST',{'body':body});assert posted['body']==body
closed=api('issue-patch','issues/'+str(issue_id),'PATCH',{'state':'closed','state_reason':'completed'});assert closed['state']=='closed'
after=api('issue-after','issues/'+str(issue_id));comment=api('comment-after','issues/comments/'+str(posted['id']))
assert after['state']=='closed' and comment['body']==body
assert after['body']==issue['body'] and after['title']==issue['title'] and sorted(l['name'] for l in after['labels'])==sorted(l['name'] for l in issue['labels'])
save('closure.json',{'reviewed_utc':stamp(),'passed':True,'finding':'IO-016','issue_number':issue_id,'state':'closed','closed_at':after['closed_at'],'comment_id':posted['id'],'comment_url':posted['html_url'],'original_body_title_labels_preserved':True,'POST_invocations':1,'PATCH_invocations':1,'new_test_executions':0,'all_five_original_criteria_accepted':True,'source_revision':current,'tested_revision':revision,'publication_performed':False,'release_readiness_certified':False})
print(json.dumps({'issue':issue_id,'state':after['state'],'comment_url':posted['html_url'],'criteria':5,'methods':9}),flush=True)
