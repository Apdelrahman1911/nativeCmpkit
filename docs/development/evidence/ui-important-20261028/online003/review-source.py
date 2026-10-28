from pathlib import Path
import datetime as dt, hashlib,json,re,subprocess,sys
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
cmd=json.loads((OUT/'command.json').read_text());bounded=json.loads((OUT/'actual-gradle.log.result.json').read_text());outcomes=json.loads((OUT/'fresh-outcomes.json').read_text());before=json.loads((OUT/'inputs-before.json').read_text());after=json.loads((OUT/'inputs-after.json').read_text());sha=cmd['source_revision']
assert sha=='ca349b19a0e53901909cf32bc74e95936b367a1f'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==sha
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
assert before==after==lt.snapshot_inputs(ROOT) and len(before)==745 and cmd['source_digest']==lt.input_digest(before)
p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE);raw,_=p.communicate(''.join(sha+':'+n+'\n' for n in before).encode());assert p.returncode==0;off=0
for n,h in before.items():
 e=raw.index(b'\n',off);head=raw[off:e].split();assert head[1]==b'blob';size=int(head[2]);assert hashlib.sha256(raw[e+1:e+1+size]).hexdigest()==h,n;off=e+size+2
assert off==len(raw)
assert bounded['command']==cmd['command'] and bounded['exit_code']==outcomes['controller_exit_code']==0 and outcomes['source_unchanged']
start=dt.datetime.fromisoformat(bounded['started_utc']).timestamp();end=start+bounded['elapsed_seconds']+.5
log=(OUT/'actual-gradle.log').read_text();markers=re.findall(r'^NATIVECMPKIT_TEST_RUNTIME task=:calf-ui:desktopTest gradle=(\S+) java=(\S+) vendor=(.*?) os=(.*?) arch=(\S+)$',log,re.M);assert len(markers)==1
assert markers[0][0]=='9.7.1' and markers[0][1].startswith('17.') and markers[0][3]=='Linux';assert 'BUILD SUCCESSFUL' in log
classes={'com.mohamedrejeb.calf.ui.button.CupertinoIndicationTest': ['releaseThenRepressKeepsTheNewPressHighlighted','cancellingOneOfTwoPressesDoesNotClearTheOther','actualIndicationNodeDetachesWithPendingReleaseAndReattachesWithoutStaleWork']}
reports=ROOT/'calf-ui/build/test-results/desktopTest';cases=[];evidence=[]
files=sorted(reports.glob('TEST-*.xml'));assert len(files)==len(outcomes['reports'])==1
for f in files:
 assert not f.is_symlink() and f.stat().st_nlink==1 and start<=f.stat().st_mtime<=end
 data=f.read_bytes();found=lt.junit_cases(data);assert all(i['status']=='passed' for i in found)
 original=next(i for i in outcomes['reports'] if i['file']==f.name);assert original['is_fresh'] and original['sha256']==hashlib.sha256(data).hexdigest() and original['cases']==found
 cases+=found;evidence.append({'path':f.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'actual_cases':len(found),'fresh':True,'mtime_utc':dt.datetime.fromtimestamp(f.stat().st_mtime,dt.timezone.utc).isoformat()})
assert set((i['classname'],i['name']) for i in cases)==set((c,m+'[desktop]') for c,methods in classes.items() for m in methods)
assert len(cases)==3 and lt.case_counts(cases)['passed']==3
f=json.loads((ROOT/'docs/audit/findings/UI.json').read_text());original=next(i for i in f if i['id']=='UI-043')
previous=json.loads((OUT.parent/'online002/inputs-before.json').read_text());changed=[n for n in before if before[n]!=previous[n]]
assert changed==['calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/button/CupertinoIndicationTest.kt'] and before.keys()==previous.keys()
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'finding':'UI-043','source_revision':sha,'verification_id':'ui-important-20261028-online003','command':cmd['command'],'command_exit_code':0,'elapsed_seconds':bounded['elapsed_seconds'],'source_inputs_verified_from_exact_Git_blobs':len(before),'source_unchanged':True,'reports':evidence,'actual_cases':cases,'totals':lt.case_counts(cases),'selected_UI043_methods':3,'unrelated_UI044_methods_replayed':0,'previous_UI044_inputs_unchanged':744,'changed_inputs_since_seven_case_pass':changed,'daemon_runtime':dict(zip(['gradle','java','vendor','os','arch'],markers[0])),'original_acceptance':[{'criterion':original['required_tests'][0],'accepted':True,'evidence':'Actual public CupertinoButton composition releases at exactly20ms and represses at exactly40ms on the controlled mainClock. Explicit20/40 clock assertions prevent frame-rounded timing. Pixel snapshot after500ms hold remains translucent/pressed; final release restores the normal red appearance.'},{'criterion':original['required_tests'][1],'accepted':True,'evidence':'Cancelling one of two actual PressInteraction objects retains the second highlight. The actual production IndicationNode collects Release before detach while feedback is pending, truly detaches, reattaches as the same factory-created node, resets its old pixels, ignores the detached stale Cancel, holds the new press beyond700ms without old work clearing it, restores after current Cancel, and detaches again.'}],'root_fix':'New presses cancel the single prior feedback job; matching active presses control final release; onDetach cancels feedback and resets alpha. Same production node/recomposition collector, not a mock renderer or substitute lifecycle. Public APIs/minimum-duration policy unchanged.','scope_limits':['Controlled20/40ms Compose scheduling, not a real-wall-clock minimum-duration or performance benchmark.','Actual Linux/JVM Compose/Skia under Xvfb; injected production interaction objects, not physical touch/assistive/native-device or other OS/branch certification.','Three fresh executions. Previously accepted indicator4 remain unchanged and are not rerun; seven authored method names across ten fresh executions in the two successful attempts, not ten unique tests.','No dependency/legal/native payload/ABI/full consumer/security/release gate certified.'],'raw_log_sha256':hashlib.sha256((OUT/'actual-gradle.log').read_bytes()).hexdigest(),'raw_log_committed':False,'issues_closed_by_review':0,'packages_releases_deployments_published':False}
(OUT/'important-result-review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({k:review[k] for k in ['passed','finding','source_revision','totals','daemon_runtime','original_acceptance']},indent=2))
