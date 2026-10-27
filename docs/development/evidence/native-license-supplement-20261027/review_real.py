"""Independent raw-byte and original-material review plus actual fail-closed notice inspection."""
from pathlib import Path
import datetime as dt, hashlib, io, json, sys, tarfile, zipfile
ROOT=Path('/root/projects/nativeCmpKit')
BASE=Path('/dev/shm/nativecmpkit-license-supplement-work-20261027')
OUT=BASE/'real001'
OLD=ROOT/'docs/development/evidence/native-license-material-20261024T193225Z'
CACHE=Path('/root/.cargo/registry/cache/index.crates.io-1949cf8c6b5b557f')
ENTRY=ROOT/'licenses/native-dependency-supplements/jni-sys-macros-0.4.1'
assert not (OUT/'lead-independent-review.json').exists()
def sha(payload):return hashlib.sha256(payload).hexdigest()
def jread(p):return json.loads(p.read_bytes())
def git_blob(payload):return hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
# The prior archive is never changed/extracted/executed. Recheck its own
# observed-byte manifest, not an authenticity assertion or legal sign-off.
old_count=0
for row in (OLD/'SHA256SUMS').read_text().splitlines():
 digest,name=row.split('  ',1);p=OLD/name
 assert p.is_file() and not p.is_symlink() and sha(p.read_bytes())==digest
 old_count+=1
provenance=jread(OLD/'verified-vcs-provenance.json')
original=next(record for record in provenance['crate_links'] if record['crate']=='jni-sys-macros-0.4.1')
catalog_raw=(ENTRY/'manifest.json').read_bytes();catalog=json.loads(catalog_raw)
assert original['commit']==catalog['revision'] and original['repository']==catalog['repository']
assert original['crate_sha256']==catalog['package']['checksum'] and original['path_in_vcs']==catalog['path_in_vcs']
records={r['path'].split('jni-sys-macros-0.4.1/',1)[-1]:r for r in original['crate_members']}
license_records={Path(r['path']).name:r for r in original['legal_files']}
vcs_records={'Cargo.toml':original['workspace_cargo_toml'],'jni-sys-macros/Cargo.toml':original['vcs_cargo_toml']}
for group,mapping in [('crate_files',records),('vcs_files',vcs_records),('license_files',license_records)]:
 for record in catalog[group]:
  payload=(ENTRY/record['catalog_path']).read_bytes();old_record=mapping[record['path']]
  assert len(payload)==record['bytes']==old_record['bytes'] and sha(payload)==record['sha256']==old_record['sha256']
  assert payload==(OLD/old_record['path']).read_bytes()
  if group!='crate_files':assert git_blob(payload)==record['git_blob_oid']==old_record['git_blob_oid']
# Single captured checksum-bound JNI archive, read-only tar access and independent
# manifest bytes. No collector/helper fallback routine is used here.
jni_raw=(CACHE/'jni-sys-macros-0.4.1.crate').read_bytes()
assert sha(jni_raw)==catalog['package']['checksum']
with tarfile.open(fileobj=io.BytesIO(jni_raw),mode='r:gz') as tar:
 for record in catalog['crate_files']:
  member=tar.getmember('jni-sys-macros-0.4.1/'+record['path'])
  assert member.isfile() and member.size==record['bytes']
  with tar.extractfile(member) as stream:payload=stream.read(record['bytes']+1)
  assert payload==(ENTRY/record['catalog_path']).read_bytes()
# Import only the independent artifact inspector AFTER raw-byte correspondence.
sys.path.insert(0,str(ROOT/'tests/consumer'))
import verify_artifacts as gate
modules=[];unique_crates={};reviewed_file_bytes=0;all_gap_ids=set()
for module in ('calf-file-picker','calf-share'):
 directory=OUT/module;prefix='META-INF/nativecmpkit/native-dependencies/'+module+'/'
 metadata=jread(OUT/(module+'-metadata.json'));report=jread(directory/prefix/'licenses-report.json')
 oldmeta=jread(OLD/(module+'-metadata.json'));oldreport=jread(OLD/(module+'-licenses-report-corrected.json'))
 assert metadata==oldmeta
 assert metadata['cargo_toml_sha256']==sha((ROOT/module/'native/Cargo.toml').read_bytes())
 assert metadata['cargo_lock_sha256']==sha((ROOT/module/'native/Cargo.lock').read_bytes())
 old_packages={(p['name'],p['version']):p for p in oldreport['packages']}
 expected_gap=[gap for gap in oldreport['gaps'] if gap['package']!='jni-sys-macros-0.4.1']
 assert report['gaps']==expected_gap and len(report['gaps'])==15
 assert report['complete_material_collection'] is False and report['license_obligations_reviewed'] is False
 changed=[];ordinary_files=0
 for package in report['packages']:
  old_package=old_packages[(package['name'],package['version'])]
  identity=package['name']+'-'+package['version']
  if identity=='jni-sys-macros-0.4.1':changed.append(identity)
  else:assert package==old_package
  if package['source_kind']!='crates.io':continue
  archive_payload=(CACHE/(identity+'.crate')).read_bytes()
  assert len(archive_payload)<=256*1024**2 and sha(archive_payload)==package['checksum']
  unique_crates[identity]=package['checksum']
  with tarfile.open(fileobj=io.BytesIO(archive_payload),mode='r:gz') as tar:
   for record in package['files']:
    relative=record['path'][len(prefix+identity+'/'):]
    payload=(directory/record['path']).read_bytes()
    assert len(payload)==record['bytes'] and 0<len(payload)<=1024*1024 and sha(payload)==record['sha256']
    if identity=='jni-sys-macros-0.4.1':
     exact=next(r for r in catalog['license_files'] if r['path']==relative)
     assert payload==(ENTRY/exact['catalog_path']).read_bytes()
     assert record['origin']=={'kind':'pinned-vcs','repository':catalog['repository'],'revision':catalog['revision'],'path':relative,'git_blob_oid':exact['git_blob_oid']}
    else:
     member=tar.getmember(identity+'/'+relative)
     assert member.isfile() and member.size==record['bytes']
     with tar.extractfile(member) as stream:assert stream.read(record['bytes']+1)==payload
     ordinary_files+=1
    reviewed_file_bytes+=len(payload)
 assert changed==['jni-sys-macros-0.4.1']
 all_gap_ids.update(gap['package'] for gap in report['gaps'])
 # Build only an inert byte container from fresh public collection. This is NOT
 # a Maven artifact, JNI binary, or an independently running Kotlin consumer.
 zpath=OUT/(module+'-collected-material.zip');assert not zpath.exists()
 with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED) as archive:
  for path in sorted(directory.rglob('*')):
   if path.is_file():
    info=zipfile.ZipInfo(path.relative_to(directory).as_posix(),date_time=(1980,1,1,0,0,0))
    info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
    archive.writestr(info,path.read_bytes())
 verifier=gate.ArtifactVerifier(ROOT,OUT,'0.1.0-preview.1',targets=['desktop'],native_platforms=['linux-x64'])
 with zipfile.ZipFile(zpath) as archive:
  names=gate.archive_names(archive)
  verifier.native_notices(archive,names,module,'actual-'+module)
 checks=verifier.checks;failures=[c for c in checks if not c['passed']]
 required={'actual-'+module+':native-license-collection-complete'}|{'actual-'+module+':crate-license:'+gap['package'].rsplit('-',1)[0]+'@'+gap['package'].rsplit('-',1)[1]+':text-present' for gap in report['gaps']}
 assert {c['name'] for c in failures}==required
 assert len(failures)==16
 assert all(c['passed'] for c in checks if ':crate-license:jni-sys-macros@0.4.1:' in c['name'])
 (OUT/(module+'-notice-gate-checks.json')).write_text(json.dumps({'passed':False,'checks':checks,'failure_count':len(failures),'scope':'Real collected public license bytes, not a packaged artifact or legal clearance'},indent=2,sort_keys=True)+'\n')
 modules.append({'module':module,'fresh_metadata_same_as_20261024':True,'packages':len(report['packages']),'original_packages_unchanged_except':['jni-sys-macros-0.4.1'],'original_gap_count':len(oldreport['gaps']),'current_gap_count':len(report['gaps']),'ordinary_archive_license_files':ordinary_files,'external_license_files':2,'external_provenance_files':6,'fresh_material_zip_entries':len(names),'fresh_material_zip_sha256':sha(zpath.read_bytes()),'notice_gate_checks':len(checks),'notice_gate_failures':len(failures),'expected_blockers_only':True,'collector_exit_code':1,'complete_material_collection':False,'license_obligations_reviewed':False})
receipt=jread(OUT/'receipt.json');assert receipt['source_held']
for name,binding in jread(OUT/'inputs-after.json').items():assert sha((ROOT/name).read_bytes())==binding['sha256']
full=jread(BASE/'consumer002.json');green=jread(BASE/'descriptorgreen001.json')
assert full['passed'] and full['test_methods']==201 and green['passed'] and green['test_methods']==50
assert set((r['class'],r['method']) for r in green['verbose_outcomes'])<=set((r['class'],r['method']) for r in full['verbose_outcomes'])
review={'passed':True,'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':receipt['source_revision'],'dirty_worktree':True,'independent_original_manifest_checks':old_count,'catalog_files':8,'captured_jni_archive_sha256':sha(jni_raw),'unique_locked_registry_archive_checks':len(unique_crates),'archive_checksums':unique_crates,'reviewed_collected_license_bytes_with_repeated_module_copies':reviewed_file_bytes,'modules':modules,'unique_remaining_gaps':sorted(all_gap_ids),'source_inputs_held':receipt['source_held'],'python_tooling_methods':201,'focused50_all_in_full201':True,'first_fixture_mutation_error_and_real_descriptor_leak_failure_preserved':True,'default_archive_only_unchanged':True,'no_native_build_tests_or_live_notices_installed':True,'package_api_abi_consumers_or_authenticity_certified':False,'aggregate_collection_legal_and_release_gates_passed':False,'scope':'Exact JNI missing license texts/proofs now collected with origin; all other original material and all fifteen shared objc2 gaps unchanged. Raw checksums and observed Git content correspondence are not signatures/authenticity/legal opinions.'}
(OUT/'lead-independent-review.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:review[k] for k in ('passed','unique_locked_registry_archive_checks','modules','unique_remaining_gaps','aggregate_collection_legal_and_release_gates_passed')},indent=2),flush=True)
