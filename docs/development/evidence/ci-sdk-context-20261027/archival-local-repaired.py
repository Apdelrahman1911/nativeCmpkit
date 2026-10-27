"""Additive finite evidence archival after independent reviews; no GitHub mutation."""
from pathlib import Path
import datetime as dt, gzip, hashlib, json, re, shutil, subprocess, sys, zipfile
ROOT=Path('/root/projects/nativeCmpKit'); E=ROOT/'docs/development/evidence'; B=Path('/dev/shm')
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests as lt
SELF=Path(__file__).parent
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='c9ffacde892cfecd3d2784b22dbad7731490c6fc'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def put(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def cp(p,d):
    d.parent.mkdir(parents=True,exist_ok=True);
    if d.exists():
        assert d.is_file() and not d.is_symlink() and sha(p)==sha(d);return
    shutil.copyfile(p,d);assert sha(p)==sha(d)
def sums(d):
    (d/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(d).as_posix()}\n' for p in sorted(d.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
def compress(p,d):
    d.parent.mkdir(parents=True,exist_ok=True);
    if not d.exists():d.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
    assert d.is_file() and not d.is_symlink() and gzip.decompress(d.read_bytes())==p.read_bytes()
archived=[]
# Real Compose control failure and green actual complete host class; dirty diagnostics.
source=B/'nativecmpkit-navigation-empty-stack-20261027';dest=E/'navigation-empty-stack-20261027'
assert dest.is_dir() and not dest.is_symlink();cp(source/'run.py',dest/'run.py');reviews=[]
HOST='calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt'
FIXTURE='calf-navigation/src/desktopTest/kotlin/com/mohamedrejeb/calf/navigation/AdaptiveNavHostStateTest.kt'
for mode in ('control001','green002'):
    run=source/mode;before=load(run/'inputs-before.json');after=load(run/'inputs-after.json');cb=load(run/'copy-executed-before.json');ca=load(run/'copy-executed-after.json');r=load(run/'receipt.json')
    assert before==after and cb==ca and len(before)==len(cb)==726
    changes=[n for n in before if cb[n]!=before[n]];assert changes==([HOST] if mode=='control001' else [])
    assert r['root_inputs_held'] and r['executed_copy_inputs_held'] and r['root_inputs_sha256']==lt.input_digest(before) and r['copy_inputs_sha256']==lt.input_digest(cb)
    assert not r['execution'].get('stop_reason') and r['execution']['exit_code']==(1 if mode=='control001' else 0)
    assert sha(run/'test.log')==r['log_sha256'] and sha(source/'run.py')==r['driver_sha256']
    assert sha(ROOT/HOST)==sha(run/'host-original.kt')=='8b8c95c0159576ccb70c62293a0a6301dde8f75d212e5bc3f22532f832a31355'
    assert sha(ROOT/FIXTURE)==sha(run/'fixture.kt')==before[FIXTURE]
    if mode=='control001':
        assert (run/'host-original.kt').read_bytes().replace(b'LaunchedEffect(navController, startDestination)',b'LaunchedEffect(Unit)')==(run/'host-control.kt').read_bytes()
    cases=[]
    for row in r['collector']['modules'][0]['reports']:
        p=run/'reports'/row['path'];assert sha(p)==row['sha256'];cases+=lt.junit_cases(p.read_bytes())
    counts=lt.case_counts(cases);assert counts==r['test_counts']
    assert counts['executed']==(1 if mode=='control001' else 12) and counts['failures']==(1 if mode=='control001' else 0) and counts['passed']==(0 if mode=='control001' else 12)
    assert counts['errors']==counts['skipped']==0 and lt.execution_markers(run/'test.log')=={':calf-navigation:desktopTest':1}
    assert any(c['name']=='changing start route initializes an explicitly emptied stack at the same host[desktop]' for c in cases)
    target=dest/mode;target.mkdir(exist_ok=True)
    for p in run.rglob('*'):
        if p.is_file():
            rel=p.relative_to(run)
            if p.name in ('inputs-before.json','inputs-after.json','copy-executed-before.json','copy-executed-after.json'):compress(p,target/(str(rel)+'.gz'))
            else:cp(p,target/rel)
    reviews.append({'mode':mode,'execution':r['execution'],'input_count':726,'captured_inputs_held':True,'explicit_copy_source_changes':changes,'test_counts':counts,'actual_testcase_identities':cases,'reports':r['collector']['modules'][0]['reports']})
put(dest/'lead-review.json',{'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed_review':True,'source_revision':'c9ffacde892cfecd3d2784b22dbad7731490c6fc','dirty_worktree_diagnostics':True,'runs':reviews,'original_production_host_unmodified':True,'scope':'Control mutates only copied effect key; one actual test fails at missing detail UI assertion. Restored real production host passes12/12 complete class methods under Xvfb. No immutable candidate/other-runtime/library-wide or release acceptance; NAV-006 remains open until exact required immutable review.'})
cp(SELF/'archive-red001.py',dest/'archival-red001.py');cp(SELF/'archive-red001.json',dest/'archival-red001.json')
(dest/'README.md').write_text('# NAV-006 empty/nonempty start policy regression\n\nOne real Compose control failure and12/12 complete host-class green methods; copied726 inputs held. The repository production host is unchanged. These dirty-source diagnostics finish local criterion coverage, not immutable issue acceptance or other-platform proof. Source-bound reports, logs, quarantined prior XML and compressed maps are retained.\n')
cp(SELF/'archive.py',dest/'archival-driver.py');cp(SELF/'archive-local-repaired.py',dest/'archival-local-repaired.py');sums(dest);archived.append(dest.relative_to(ROOT).as_posix())
# Focused synthetic SDK scope fix red/green and explicitly non-source-held full403.
source=B/'nativecmpkit-ci-sdk-context-20261027';dest=E/'ci-sdk-context-20261027'
assert not dest.exists();dest.mkdir();red=load(source/'red001.json');green=load(source/'green001.json')
assert red['exit_code']==1 and green['exit_code']==0 and green['python_methods']==3
assert green['inputs_before']==green['inputs_after'] and all(sha(ROOT/name)==h for name,h in green['inputs_before'].items())
assert sha(source/'red001.log')==red['log_sha256'] and sha(source/'green001.log')==green['log_sha256']
assert re.search(r'^Ran 403 tests in ',(source/'ci-all-green001.log').read_text(),re.M) and re.search(r'^OK$',(source/'ci-all-green001.log').read_text(),re.M)
for p in source.iterdir():
    if p.is_file():cp(p,dest/p.name)
put(dest/'lead-review.json',{'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'synthetic_focused_methods_passed':3,'full_CI_Python_methods_passed':403,'focused3_overlap_full403':True,'focused_three_input_maps_held':True,'full403_run_has_no_independent_complete_input_freeze':True,'new_immutable_hosted_execution_required':True,'red_missing_sdk_scope_suites':['desktop','js','wasm','ios'],'scope':'Runner preparation/abort/lock-cleanup fixture evidence, zero actual Gradle/SDK/native/library executions. Request Android official SDK for all configured suites, retain OS/browser/device arguments and fail before Gradle/quarantine on missing capture. Hosted setup/test SDK fingerprint correspondence still unverified for this edit.'})
(dest/'README.md').write_text('# CI SDK receipt scope repair\n\nActual historical Windows run exposed omitted Android SDK metadata in desktop/browser/iOS library-run capture. Three focused synthetic methods first fail four suite requests, then pass; full403 CI Python methods pass with focused3 overlapping. Focused3 have a three-file before/after binding; the earlier full403 run does not independently freeze every input. No hosted SDK equality/native/library pass until new immutable CI. No workflow permissions/action/publishing policy changed.\n')
cp(SELF/'archive.py',dest/'archival-driver.py');cp(SELF/'archive-local-repaired.py',dest/'archival-local-repaired.py');sums(dest);archived.append(dest.relative_to(ROOT).as_posix())
put(SELF/'archive-result.json',{'archived':archived,'publication_performed':False,'lead_closed_issues':0,'root_free_bytes_after':shutil.disk_usage(ROOT).free,'tmpfs_free_bytes_after':shutil.disk_usage(B).free})
print(json.dumps(load(SELF/'archive-result.json'),indent=2))
