import json,zipfile,hashlib,sys,subprocess,datetime
from pathlib import Path
root=Path('/root/projects/nativeCmpKit');sys.path.insert(0,str(root/'scripts/ci'));import library_tests as lib
out=Path('/dev/shm/nativecmpkit-ios-picker-batch-important-20261029/github-ci001');prior=root/'docs/development/evidence/github-actions/40587910531';review=json.loads((prior/'lead-independent-review.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
assert review['evidence_integrity_passed'] and review['source_revision']=='fc73dd47cf35085e6f9e2b964ae126eefe2be246'
p=prior/'raw/12773633261.zip'
with zipfile.ZipFile(p) as z:
 rec=json.loads(z.read('build/ci-verification/ios-iphone/receipt.json'));inputs=json.loads(z.read('build/ci-verification/ios-iphone/inputs-before.json'));assert inputs==json.loads(z.read('build/ci-verification/ios-iphone/inputs-after.json'))
 owners={n:h for n,h in review['reviewed_current_IO_Coil_source_hashes'].items() if n.startswith('calf-io/src/') and '/android' not in n}
 assert all(sha((root/n).read_bytes())==h for n,h in owners.items())
 assert sha((root/'gradle/libs.versions.toml').read_bytes())==inputs['gradle/libs.versions.toml']
 old=subprocess.check_output(['git','show',rec['source_revision']+':calf-io/build.gradle.kts'],cwd=root,text=True);current=(root/'calf-io/build.gradle.kts').read_text()
 current_block='        // W3C File is part of the public KmpFile constructor/property and extension API.\n        api(libs.kotlinx.browser)'
 assert current.replace(current_block,'        implementation(libs.kotlinx.browser)')==old
 reused=[]
 requested={'com.mohamedrejeb.calf.io.KmpFilePathTest':None,'com.mohamedrejeb.calf.io.KmpFileMetadataTest':{'fromUriStringReadsBackToUriString','fromUriStringAcceptsAPlainPath','fromUriStringRejectsWhatIsNotAFile'},'com.mohamedrejeb.calf.io.NativeReadSafetyTest':{'aNonFileUrlWithTheSamePathCannotReadOrDescribeALocalFile','aNonFileUrlCannotDescribeALocalDirectoryOrDeleteAnOriginal'}}
 for module in rec['modules']:
  if module['module']!='calf-io':continue
  for r in module['reports']:
   raw=z.read(r['path']);assert sha(raw)==r['sha256']
   for c in lib.junit_cases(raw):
    name=c['classname'].removeprefix('iosSimulatorArm64Test.');method=c['name'].removesuffix('[iosSimulatorArm64]')
    if name in requested and (requested[name] is None or method in requested[name]):
     assert c['status']=='passed';reused.append({**c,'source_revision':rec['source_revision'],'prior_report':r['path'],'original_sha256':r['sha256']})
 assert len(reused)==12
 result={'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prior_native_revision':rec['source_revision'],'prior_native_run':40587910531,'prior_workflow_was_success':True,'unchanged_owning_IO_nonAndroid_sources_reviewed':len(owners),'exact_versions_unchanged':True,'IO_build_difference':'Only webMain kotlinx.browser implementation→api plus its disclosure comment. Independently reversible byte comparison; not an all-build-byte equality claim. Android resources, desktop native test classpath and publication metadata policy changes do not alter these iOS source/target functions.','accepted_methods_not_reexecuted_or_counted_fresh':12,'reused_methods':reused,'scope':'Seven native path/name methods, three URI restoration methods and two actual Foundation non-file/local-path isolation methods reused at unchanged production/test/native dependency versions. No unrelated Coil/bounds/memory methods counted.'}
 (out/'metadata-native-unchanged-reuse.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS prior native metadata12 reused;',len(owners),'non-Android IO source hashes and exact native versions unchanged; web-only build difference disclosed')
