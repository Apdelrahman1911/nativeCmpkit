"""Read-only exact-Git/remote static-report addendum; no packages redistributed."""
from pathlib import Path
import datetime as dt
import hashlib, json, subprocess, zipfile
ROOT=Path('/root/projects/nativeCmpKit')
SOURCE=Path('/dev/shm/nativecmpkit-ci-c9ffacde-20261027/40568564791')
REV='c9ffacde892cfecd3d2784b22dbad7731490c6fc'
OUT=Path(__file__).parent/'catalog-addendum.json'
def sha(raw): return hashlib.sha256(raw).hexdigest()
with zipfile.ZipFile(SOURCE/'12764467215.zip') as z:
    report=json.loads(z.read('ci-consumer/core-io-desktop/static-packages.json'))
with zipfile.ZipFile(ROOT/'docs/development/evidence/github-actions/40507836194/raw/12736236898.zip') as z:
    prior=json.loads(z.read('ci-consumer/core-io-desktop/static-packages.json'))
checks={r['name']:r for r in report['checks']}
assert len(checks)==len(report['checks'])==376
old={r['name'] for r in prior['checks']}
assert len(old)==312 and old<=checks.keys()
assert report['success'] and report['failed_check_count']==0
files={}
for name in subprocess.check_output(['git','ls-tree','-rz','--name-only',REV],cwd=ROOT).decode().split('\0'):
    if name.startswith('licenses/native-dependency-supplements/jni-sys-macros-0.4.1/'):
        raw=subprocess.check_output(['git','show',REV+':'+name],cwd=ROOT)
        files[name]=sha(raw)
assert len(files)==8
expected=set()
for coordinate in ('nativecmpkit-core','nativecmpkit-core-desktop','nativecmpkit-io','nativecmpkit-io-desktop'):
    for suffix in ('.jar','-notices.zip'):
        archive=coordinate+'-0.1.0-preview.1'+suffix
        for name in files:
            expected.add(coordinate+':archive:'+archive+':notice:'+name)
assert len(expected)==64 and set(checks)-old==expected
assert all(checks[n]['passed'] is True and checks[n]['detail']=='Complete source notice bytes accompany this coordinate' for n in expected)
review=json.loads((SOURCE/'review-archive/lead-independent-review-with-catalog.json').read_text())
assert review['source_revision']==REV and review['artifact_id']==12764467215
assert review['new_catalog_distribution_scope']['bound_catalog_source_files']==files
assert review['new_catalog_distribution_scope']['exact_new_static_check_identities']==sorted(expected)
result={'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'run_id':40568564791,'source_revision':REV,
'evidence_integrity_passed':True,'static_report_sha256':sha(json.dumps(report,sort_keys=True,separators=(',',':')).encode()),
'all_prior_static_check_identities_retained':312,'new_source_bound_notice_content_checks':64,'total_static_checks_passed':376,
'catalog_files':files,'expected_new_check_identities':sorted(expected),'script_sha256':sha(Path(__file__).read_bytes()),
'packages_published':False,'native_module_supplementation_verified':False,'legal_clearance_certified':False,
'scope':'Independent reconstruction of exact expected static report identities and immutable source hashes. Archived remote controller checked actual staged archive contents. Raw candidate JAR/ZIP artifacts were not uploaded, so this addendum does not independently reopen distribution bytes or clear native modules/obligations/release gates.'}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('run_id','evidence_integrity_passed','all_prior_static_check_identities_retained','new_source_bound_notice_content_checks','total_static_checks_passed')}))
