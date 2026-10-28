from pathlib import Path
import datetime as dt, hashlib,json,re,subprocess,sys
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
cmd=json.loads((OUT/'command.json').read_text());bounded=json.loads((OUT/'actual-gradle.log.result.json').read_text());outcomes=json.loads((OUT/'fresh-outcomes.json').read_text());before=json.loads((OUT/'inputs-before.json').read_text());after=json.loads((OUT/'inputs-after.json').read_text());sha=cmd['source_revision']
assert sha=='fe75ac86da6bb22f6c02a7fcadf8334184b10b7f'
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
classes={'com.mohamedrejeb.calf.ui.button.CupertinoIndicationTest': ['releaseThenRepressKeepsTheNewPressHighlighted','cancellingOneOfTwoPressesDoesNotClearTheOther','actualIndicationNodeDetachesWithPendingReleaseAndReattachesWithoutStaleWork'], 'com.mohamedrejeb.calf.ui.cupertino.CupertinoActivityIndicatorDrawingTest':['transparentCallerColorPaintsNoPixels','halfAlphaIsAnOpacityBoundAcrossTheWholeAnimationCycle','firstInactiveSpokeIsNotPaintedTwice','publicIndicatorPreservesSemanticsOpacityAndEightFramesAcrossItsActualCycle']}
reports=ROOT/'calf-ui/build/test-results/desktopTest';cases=[];evidence=[]
files=sorted(reports.glob('TEST-*.xml'));assert len(files)==len(outcomes['reports'])==2
for f in files:
 assert not f.is_symlink() and f.stat().st_nlink==1 and start<=f.stat().st_mtime<=end
 data=f.read_bytes();found=lt.junit_cases(data);assert all(i['status']=='passed' for i in found)
 original=next(i for i in outcomes['reports'] if i['file']==f.name);assert original['is_fresh'] and original['sha256']==hashlib.sha256(data).hexdigest() and original['cases']==found
 cases+=found;evidence.append({'path':f.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'actual_cases':len(found),'fresh':True,'mtime_utc':dt.datetime.fromtimestamp(f.stat().st_mtime,dt.timezone.utc).isoformat()})
assert set((i['classname'],i['name']) for i in cases)==set((c,m+'[desktop]') for c,methods in classes.items() for m in methods)
assert len(cases)==7 and lt.case_counts(cases)['passed']==7
# Independently read all original finding criteria. Only UI-044 is ready for
# direct closure here; exact20ms additional UI-043 verification runs separately.
f=json.loads((ROOT/'docs/audit/findings/UI.json').read_text());original=next(i for i in f if i['id']=='UI-044')
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'finding':'UI-044','source_revision':sha,'verification_id':'ui-important-20261028-online002','command':cmd['command'],'command_exit_code':0,'elapsed_seconds':bounded['elapsed_seconds'],'source_inputs_verified_from_exact_Git_blobs':len(before),'source_unchanged':True,'reports':evidence,'actual_cases':cases,'totals':lt.case_counts(cases),'selected_UI044_methods':4,'selected_UI043_methods':3,'daemon_runtime':dict(zip(['gradle','java','vendor','os','arch'],markers[0])),'original_acceptance':[{'criterion':original['required_tests'][0],'accepted':True,'evidence':'Three real production CanvasDrawScope methods cover transparent/all eight half-alpha frames/eight unique spoke pixels; composed public indicator also compares every pixel of its actual rendered half-alpha output to the production painter on white.'},{'criterion':original['required_tests'][1],'accepted':True,'evidence':'Actual public CupertinoActivityIndicator with controlled clock samples all eight frames plus the one-second restart; all80x80 RGBA pixels agree within2/255, no differing pixels. Indeterminate progress semantics is retained at every snapshot and after dynamic transparent-color replacement.'}],'root_fix':'Exactly eight unique angles; multiply input alpha by per-spoke intensity; public one-second transition and progress semantics unchanged. This continuation verifies earlier production implementation and changes tests only.','scope_limits':['Linux/JVM actual Compose/Skia rendering under Xvfb; not UIKit UIActivityIndicator, native touch/VoiceOver/TalkBack or other OS/branch certification.','Seven fresh executions from seven authored methods; no stale reports or unrelated suite replay.','No dependency/legal/native payload/ABI/full consumer/security/release gate certified.'],'raw_log_sha256':hashlib.sha256((OUT/'actual-gradle.log').read_bytes()).hexdigest(),'raw_log_committed':False,'issues_closed_by_review':0,'packages_releases_deployments_published':False}
(OUT/'important-result-review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({k:review[k] for k in ['passed','finding','source_revision','totals','daemon_runtime','original_acceptance']},indent=2))
