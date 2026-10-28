"""Review old actual Android callback outcomes against unchanged relevant inputs; zero new tests."""
from pathlib import Path
import datetime as dt, hashlib, json, subprocess, sys, zipfile, xml.etree.ElementTree as E
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).parent
BASE=ROOT/'docs/development/evidence/github-actions/40414284598';RUN=40414284598
arts=json.loads((BASE/'artifacts-final.json').read_text())['artifacts'];art=next(a for a in arts if a['name']=='library-evidence-android-host');p=BASE/'raw'/(str(art['id'])+'.zip')
run=json.loads((BASE/'run-final.json').read_text());assert run['id']==RUN and run['conclusion']=='success' and run['status']=='completed' and run['run_attempt']==1
assert 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()==art['digest'] and p.stat().st_size==art['size_in_bytes']
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
with zipfile.ZipFile(p) as a:
 b='build/ci-verification/android-host/';rec=json.loads(a.read(b+'receipt.json'));before=json.loads(a.read(b+'inputs-before.json'));after=json.loads(a.read(b+'inputs-after.json'))
 assert before==after and len(before)==695 and rec['source_revision']==run['head_sha'] and rec['execution']['exit_code']==0 and rec['passed'] and not rec['source_tree_dirty'] and not rec['changed_inputs']
 # Only callback and actual Android launch-error contracts are reused. Desktop edits
 # and distribution/IO/provider/device gates are not certified by this review.
 prefixes=('calf-share/src/commonMain/','calf-share/src/androidMain/','calf-share/src/commonTest/','calf-share/src/androidHostTest/','calf-core/src/commonMain/','calf-core/src/androidMain/')
 relevant={n:h for n,h in before.items() if n.startswith(prefixes) or n in ('calf-share/build.gradle.kts','gradle/libs.versions.toml')}
 assert relevant and any('AndroidShareTest.kt' in n for n in relevant)
 current=lt.snapshot_inputs(ROOT);assert relevant=={n:current[n] for n in relevant}
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
 for n,h in relevant.items():assert hashlib.sha256(subprocess.check_output(['git','show',head+':'+n],cwd=ROOT)).hexdigest()==h,n
 m=next(m for m in rec['modules'] if m['module']=='calf-share');assert m['executed']==m['passed']==16 and not (m['failures'] or m['errors'] or m['skipped'])
 reports=[];cases=[]
 for r in m['reports']:
  data=a.read(r['path']);assert hashlib.sha256(data).hexdigest()==r['sha256'] and b'<!DOCTYPE' not in data and b'<!ENTITY' not in data
  cs=E.fromstring(data).findall('.//testcase');assert all(not any(e.tag in ('failure','error','skipped') for e in c) for c in cs);cases+=cs;reports.append({'path':r['path'],'sha256':r['sha256'],'passed':len(cs)})
 assert len(cases)==16 and len(reports)==2
 actual={(c.get('classname'),c.get('name').split('[')[0]) for c in cases};assert len(actual)==16
 required=['throwingApplicationResultCallbackIsNotReclassifiedOrInvokedTwice','platformLaunchFailureIsOneFailureInsteadOfACompletedShare']
 for method in required:assert ('com.mohamedrejeb.calf.share.AndroidShareTest',method) in actual
 source=(ROOT/'calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt').read_text();assert 'val result = launchAndroidShare(context, content, options)\n    onResult(result)' in source
 test=(ROOT/'calf-share/src/androidHostTest/kotlin/com/mohamedrejeb/calf/share/AndroidShareTest.kt').read_text();assert 'throw ActivityNotFoundException("no chooser")' in test and 'assertSame(expected, thrown)' in test and 'assertEquals(1, calls)' in test and 'results.single()' in test
review={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,'finding':'NATIVE-032','source_revision_reused':run['head_sha'],'current_revision_relevant_inputs_matched':head,'run_id':RUN,'run_url':run['html_url'],'reused_actual_executions':16,'fresh_executions':0,'important_Android_methods':required,'reports':reports,'original_before_after_input_count':len(before),'original_before_after_unchanged':True,'relevant_input_count':len(relevant),'relevant_input_hashes':relevant,'relevant_files_match_current_own_Git_blobs':True,'scope':'Actual production Android callback/ActivityNotFoundException under Robolectric/API34. No actual chooser/recipient grants, physical device, process recreation, IO/resource/provenance/consumer/API-ABI/release certification. Other target changes are not certified. New JS/Wasm share/clipboard fulfilled+rejected callback cases still require runtime.','packages_releases_deployments_published':False}
(OUT/'android-reuse-review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({k:review[k] for k in ('passed','reused_actual_executions','fresh_executions','relevant_input_count','important_Android_methods')},indent=2))
