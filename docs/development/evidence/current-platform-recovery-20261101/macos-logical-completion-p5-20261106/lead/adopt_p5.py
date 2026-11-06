import os,sys,types,json,hashlib,ast,collections
PREVIOUS='/root/nativecmpkit-source-proposals-20261105/lead-resume-R11-P5-20261106-rh98k8cp'
HERE='/root/nativecmpkit-source-proposals-20261105/lead-resume-P6-tooling-startup-20261106-61q2z79j'
fd=os.open(PREVIOUS+'/safeio.py',os.O_RDONLY|os.O_NOATIME|os.O_NOFOLLOW)
try:data=os.read(fd,16384)
finally:os.close(fd)
s=types.ModuleType('safeio');exec(compile(data,PREVIOUS+'/safeio.py','exec'),s.__dict__)
m,manifest_pin=s.obj(HERE+'/mac-p5-only-failed2/PREFLIGHT-MANIFEST.json')
result,result_pin=s.obj(HERE+'/mac-p5-only-failed2/FAILED2-ONCE-RESULT.json')
lead,lead_pin=s.obj(HERE+'/LEAD-FAILED2-REVIEW.json')
review,review_pin=s.obj(sys.argv[1])
assert review_pin['sha256']==sys.argv[2]
assert result['passed'] and result['custody']=={'source_pins':38,'proposal_pins':5,'model_pins':38}
assert result['child_exit']==0 and result['capture_eof'] and result['child_group_absent'] and result['owned_runtime_removed']
assert result['summary']['tests']==2 and result['summary']['errors']==result['summary']['failures']==result['summary']['skips']==0
spans,spans_pin=s.obj(m['spans']['path']);assert spans_pin==m['spans'] and len(spans)==20
originals={};postimages={}
for rel,pin in m['source_pins'].items():
    originals[rel],actual=s.read(pin['path']);assert actual==pin,(rel,'original custody')
for rel,pin in m['proposal_pins'].items():
    postimages[rel],actual=s.read(pin['path']);assert actual==pin,(rel,'proposal custody')
assert len(postimages)==5 and {x['path'] for x in spans}==set(postimages)
for rel,payload in postimages.items():
    forward=originals[rel].decode();operations=[x for x in spans if x['path']==rel]
    for x in operations:
        assert forward.count(x['before'])==1,(rel,x['label'],'forward')
        forward=forward.replace(x['before'],x['after'],1)
    assert forward.encode()==payload,rel
    inverse=payload.decode()
    for x in reversed(operations):
        assert inverse.count(x['after'])==1,(rel,x['label'],'inverse')
        inverse=inverse.replace(x['after'],x['before'],1)
    assert inverse.encode()==originals[rel],rel
    ast.parse(payload)
out=HERE+'/mac-p5-adoption';os.mkdir(out,0o700)
s.write_once(out+'/ADOPTION-RESERVATION.json',json.dumps({'original_sources':m['source_pins'],'postimages':m['proposal_pins'],'manifest':manifest_pin,'result':result_pin,'lead_review':lead_pin,'independent_review':review_pin,'spans':spans_pin,'existing_writes':5,'additions':0,'ROOT_writes':0,'forward_inverse_exact':20},sort_keys=True,indent=2).encode()+b'\n')
adopted={}
for index,rel in enumerate(sorted(postimages),1):
    pin=m['source_pins'][rel];payload=postimages[rel]
    fd=os.open(pin['path'],os.O_RDWR|os.O_NOFOLLOW|os.O_NOATIME)
    try:
        assert s.identity(os.fstat(fd))==pin['stat'],(rel,'prewrite descriptor custody')
        offset=0
        while offset<len(payload):
            n=os.pwrite(fd,payload[offset:],offset);assert n>0;offset+=n
        os.ftruncate(fd,len(payload));os.fsync(fd)
        after=s.identity(os.fstat(fd))
        assert all(after[k]==pin['stat'][k] for k in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_atime_ns'))
    finally:os.close(fd)
    actual_data,actual=s.read(pin['path'])
    assert actual_data==payload and actual['stat']==after
    adopted[rel]=actual
    s.write_once(out+f'/ADOPTED-{index:02d}.json',json.dumps({'path':rel,'before':pin,'after':actual,'write_once':True,'mode_inode_atime_preserved':True},sort_keys=True,indent=2).encode()+b'\n')
held={}
for rel,pin in m['source_pins'].items():
    actual_data,actual=s.read(pin['path']);assert actual==adopted.get(rel,pin)
    assert actual_data==(postimages[rel] if rel in postimages else originals[rel])
    held[rel]=actual
receipt={'adopted':adopted,'full38_after':held,'existing_writes':5,'additions':0,'unchanged_originals':33,'forward_inverse_spans':20,'modes_inodes_atimes_preserved':True,'original_failed8_retained':True,'only_failed2_passed':True,'six_source_results_reused_not_replayed':True,'ROOT_writes':0,'Git_mutations':0,'native_compiler_consumer_issue_acceptance':False,'publication':False}
s.write_once(out+'/ADOPTION-ONCE-RESULT.json',json.dumps(receipt,sort_keys=True,indent=2).encode()+b'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('adopted','full38_after')},sort_keys=True,indent=2))
