#!/usr/bin/env python3
"""Bounded passive real locked crate versus reported public tree correspondence.

No subprocess, network, archive extraction, build, code execution or legal admission.
This recovery raises only the ad hoc research per-member read bound from 1 to 2 MiB
because the cached public source tree reports two 1.65/1.67 MiB library members.
It does not alter any checked-in collector/supplement/staging/publication bound.
"""
from pathlib import Path
import json, tarfile, hashlib, time, stat, tomllib, io
BASE=Path('/root/nativecmpkit-native-reviews-20261101/agent606-genuine-stage-prerequisites')
OUT=BASE/'winapi-origin606'
TREE_BYTES=(OUT/'source-tree-0.3.6.json').read_bytes()
SOURCE=json.loads(TREE_BYTES)
TREE={record['path']:record for record in SOURCE['tree']}
METADATA_BYTES=(BASE/'metadata-current606/calf-file-picker.json').read_bytes()
METADATA=json.loads(METADATA_BYTES)
CACHE=Path('/root/.cargo/registry/cache/index.crates.io-1949cf8c6b5b557f')
RECOVERY=OUT/'recovery1'
RECOVERY.mkdir(exist_ok=False)
fields=lambda value:[value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns,value.st_nlink,value.st_mode]
results=[]
for name,prefix in [('winapi-i686-pc-windows-gnu','i686'),('winapi-x86_64-pc-windows-gnu','x86_64')]:
    package=next(p for p in METADATA['packages'] if p['name']==name)
    identity=name+'-'+package['version']; path=CACHE/(identity+'.crate')
    before=path.lstat()
    assert stat.S_ISREG(before.st_mode) and not path.is_symlink() and before.st_size<=16*1024*1024
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==package['checksum']
    started=time.monotonic(); records=[]; normalized=None; seen=set()
    proofs=RECOVERY/identity
    proofs.mkdir()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        count=0; total=0
        for member in archive:
            count+=1; total+=member.size
            assert count<=3000 and total<=64*1024*1024 and member.isfile() and not member.islnk() and not member.issym() and 0<=member.size<=2*1024*1024,member.name
            assert member.name.startswith(identity+'/') and '\\' not in member.name
            relative=member.name[len(identity)+1:]
            assert relative and '..' not in Path(relative).parts and not relative.startswith('/') and relative not in seen
            seen.add(relative)
            with archive.extractfile(member) as stream: payload=stream.read(member.size+1)
            assert len(payload)==member.size
            sha256=hashlib.sha256(payload).hexdigest()
            oid=hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
            if relative=='Cargo.toml':
                normalized={'path':relative,'bytes':len(payload),'sha256':sha256,'git_blob_oid':oid,'explanation':'Cargo registry normalized manifest, no direct Git source blob asserted'}
                normalized_package=tomllib.loads(payload.decode())['package']
                assert all(normalized_package[key]==package[key] for key in ('name','version','license'))
                assert normalized_package['repository']=='https://github.com/retep998/winapi-rs'
            else:
                source_path=prefix+'/'+('Cargo.toml' if relative=='Cargo.toml.orig' else relative)
                entry=TREE.get(source_path)
                same=entry is not None and entry['type']=='blob' and entry['mode']=='100644' and entry.get('size')==len(payload) and entry['sha']==oid
                records.append({'crate_path':relative,'source_path':source_path,'bytes':len(payload),'sha256':sha256,'git_blob_oid':oid,'source_blob_oid':entry.get('sha') if entry else None,'exact_source_match':same})
            if not relative.startswith('lib/'):
                target=proofs/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(payload)
    assert fields(path.lstat())==fields(before)
    result={'package':package,'archive_bytes':before.st_size,'archive_checksum_matches_locked':True,'archive_stat_before_equals_after':True,'crate_vcs_info_absent':'.cargo_vcs_info.json' not in seen,'archive_member_count':count,'archive_uncompressed_bytes':total,'git_correspondence_compared_members':len(records),'git_correspondence_matches':sum(r['exact_source_match'] for r in records),'git_correspondence_mismatches':sum(not r['exact_source_match'] for r in records),'source_revision':SOURCE['sha'],'source_tree_response_sha256':hashlib.sha256(TREE_BYTES).hexdigest(),'metadata_sha256':hashlib.sha256(METADATA_BYTES).hexdigest(),'source_package_path':prefix,'normalized_manifest':normalized,'payload_files':records,'wall_seconds':time.monotonic()-started,'source_authenticity_certified':False,'license_obligations_reviewed':False}
    (RECOVERY/(identity+'-correspondence.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='payload_files'},sort_keys=True))
    print('first mismatches',[r for r in records if not r['exact_source_match']][:4])
    results.append({key:value for key,value in result.items() if key!='payload_files'})
assert (OUT/'source-tree-0.3.6.json').read_bytes()==TREE_BYTES
assert (BASE/'metadata-current606/calf-file-picker.json').read_bytes()==METADATA_BYTES
(RECOVERY/'correspondence-summary.json').write_text(json.dumps({'scope':'ONE passive complete real archive payload versus immutable reported public Git tree comparison; normalized registry manifest separated; not signature/authenticity/material/legal admission','results':results},indent=2,sort_keys=True)+'\n')
