import argparse, hashlib, json, os, stat, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
PACKET=Path('/root/nativecmpkit-source-proposals-20261104/ci-current-source-ingress730-r1')
ROOT=Path('/root/projects/nativeCmpKit')
FIELDS=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
SEAL_SHA='8c8c3672040e4a7466f63b60ba5d231b1f01589444bfae575ccc7add4dd596e5'
MAX=4*1024**2
completed=[];started_paths=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def identity(s):return {k:getattr(s,k) for k in FIELDS}
def emit(n,d):
 b=(json.dumps(d,sort_keys=True,indent=2)+'\n').encode()
 fd=os.open(HERE/n,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return {'file':n,'bytes':len(b),'sha256':sha(b)}
def read(p):
 if p.resolve(strict=True)!=p:raise ValueError('Input path alias '+str(p))
 s=p.lstat();before=identity(s)
 if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or not 0<=s.st_size<=MAX:raise ValueError('Nonordinary/bounded input '+str(p))
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  if identity(os.fstat(f.fileno()))!=before:raise ValueError('Opened input drift '+str(p))
  b=f.read(MAX+1)
  if identity(os.fstat(f.fileno()))!=before:raise ValueError('Read input drift '+str(p))
 if identity(p.lstat())!=before or len(b)!=s.st_size:raise ValueError('Closed input drift '+str(p))
 return b,{'identity':before,'mode':format(stat.S_IMODE(s.st_mode),'04o'),'bytes':len(b),'sha256':sha(b)}
def require(ok,msg):
 if not ok:raise ValueError(msg)
def receipt(path,wanted):
 b,_=read(Path(path));require(sha(b)==wanted,'Independent receipt changed');return json.loads(b)
ap=argparse.ArgumentParser();ap.add_argument('--source-review',required=True);ap.add_argument('--source-review-sha256',required=True);ap.add_argument('--results-review',required=True);ap.add_argument('--results-review-sha256',required=True)
a=ap.parse_args();started=time.monotonic()
try:
 receipt(a.source_review,a.source_review_sha256);receipt(a.results_review,a.results_review_sha256)
 actual=json.loads(read(Path('/root/nativecmpkit-source-proposals-20261104/lead-final730-important-controls732/ACTUAL-FIRST-RESULT.json'))[0])
 require(actual['outcome']=='passed' and actual['child_exit']==0 and actual['candidate369_and_ROOT365_held'] is True and actual['planned_unique']==23 and actual['source_seal_sha256']==SEAL_SHA,'Original important23 acceptance required')
 sb,_=read(PACKET/'SOURCE-SEAL730.json');require(sha(sb)==SEAL_SHA,'Source seal changed')
 for rel,row in json.loads(sb)['files'].items():
  _,held=read(PACKET/rel);require({k:held[k] for k in ('bytes','sha256','mode')}==row,'Sealed file changed '+rel)
 policy=json.loads(read(PACKET/'ADOPTION-BINDINGS730.json')[0]);original=json.loads(read(PACKET/'ROOT365-PREIMAGE-CUSTODY730.json')[0])
 expected=json.loads(read(PACKET/'FINAL-FINITE369-MAP730.json')[0])
 before_map=original['ROOT_preimages319']|original['dependency_only46'];before={};before_bytes={}
 require(len(before_map)==365 and len(expected)==369 and len(policy['existing7'])==7 and len(policy['additions4'])==4,'Exact population changed')
 for rel,row in before_map.items():
  b,held=read(ROOT/rel);require(held==row,'ROOT preimage source/identity drift '+rel);before[rel]=held;before_bytes[rel]=b
 for rel in policy['additions4']:require(not (ROOT/rel).exists() and not (ROOT/rel).is_symlink(),'Required addition no longer absent '+rel)
 postimages={};fragments=0
 for rel,row in policy['existing7'].items():
  binding=row['binding'];b=before_bytes[rel]
  require((len(b),sha(b))==(binding['before_bytes'],binding['before_sha256']) and before[rel]['mode']==row['before_mode'],'Exact existing preimage refused '+rel)
  for f in binding['fragments']:
   x=f['before'].encode();y=f['after'].encode()
   require(sha(x)==f['before_fragment_sha256'] and sha(y)==f['after_fragment_sha256'] and b.count(x)==1,'Exact fragment mismatch '+rel)
   b=b.replace(x,y,1);fragments+=1
  require((len(b),sha(b))==(binding['after_bytes'],binding['after_sha256']),'Exact folded postimage mismatch '+rel)
  require(b==read(PACKET/'candidate369'/rel)[0],'Folded/candidate postimage differs '+rel)
  require(row['before_mode']==row['after_mode'],'Unexpected mode change requested '+rel)
  postimages[rel]=b
 for rel,row in policy['additions4'].items():
  b,_=read(PACKET/row['postimage']);require((len(b),sha(b))==(row['bytes'],row['sha256']),'Exact addition mismatch '+rel);postimages[rel]=b
 require(fragments==41,'Exact41 fragment count changed')
 emit('BEFORE-CUSTODY.json',{'ROOT365':before,'source_seal_sha256':SEAL_SHA,'exact7_existing4_new41_fragments':True})
 emit('INTENT.json',{'source_review':{'path':a.source_review,'sha256':a.source_review_sha256},'results_review':{'path':a.results_review,'sha256':a.results_review_sha256},'existing7':list(policy['existing7']),'additions4':list(policy['additions4']),'all_unmodified_existing_ROOT_inputs_preserved':True,'Git_GitHub_build_native_network_publishing_mutations':0})
 for rel,row in policy['existing7'].items():
  p=ROOT/rel;b=postimages[rel]
  require(read(p)[1]==before[rel],'Fresh prewrite source/identity drift '+rel)
  fd=os.open(p,os.O_WRONLY|os.O_NOFOLLOW)
  try:
   require(identity(os.fstat(fd))==before[rel]['identity'],'Opened prewrite identity drift '+rel)
   emit('BEGIN-'+p.name+'.json',{'path':rel,'before_sha256':before[rel]['sha256'],'expected_after_sha256':sha(b)});started_paths.append(rel)
   written=0
   while written<len(b):
    n=os.write(fd,b[written:]);require(n>0,'Short write '+rel);written+=n
   os.ftruncate(fd,len(b));os.fsync(fd)
   end=identity(os.fstat(fd));require(identity(p.lstat())==end,'Fresh postwrite descriptor/path drift '+rel)
   require(end['st_dev']==before[rel]['identity']['st_dev'] and end['st_ino']==before[rel]['identity']['st_ino'] and end['st_nlink']==1 and stat.S_ISREG(end['st_mode']) and format(stat.S_IMODE(end['st_mode']),'04o')==row['after_mode'],'Existing identity/mode changed '+rel)
  finally:os.close(fd)
  _,after=read(p);require((after['bytes'],after['sha256'],after['mode'])==(len(b),sha(b),row['after_mode']),'Existing postimage readback refused '+rel)
  completed.append(rel);emit('COMPLETED-'+p.name+'.json',{'path':rel,'after':after})
 for rel,row in policy['additions4'].items():
  p=ROOT/rel;b=postimages[rel];require(p.parent.resolve(strict=True)==p.parent,'Addition parent alias '+rel)
  fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,int(row['after_mode'],8))
  try:
   os.fchmod(fd,int(row['after_mode'],8));started_paths.append(rel)
   written=0
   while written<len(b):
    n=os.write(fd,b[written:]);require(n>0,'Short addition write '+rel);written+=n
   os.fsync(fd);require(identity(p.lstat())==identity(os.fstat(fd)),'Addition descriptor/path drift '+rel)
  finally:os.close(fd)
  _,after=read(p);require((after['bytes'],after['sha256'],after['mode'])==(row['bytes'],row['sha256'],row['after_mode']),'Addition postimage readback refused '+rel)
  completed.append(rel);emit('COMPLETED-'+p.name+'.json',{'path':rel,'after':after})
 after_map={}
 for rel,row in expected.items():
  _,held=read(ROOT/rel);require((held['bytes'],held['sha256'],held['mode'])==(row['bytes'],row['sha256'],row['mode']),'Final369 source map drift '+rel)
  if rel not in postimages:require(held==before[rel],'Unmodified original ROOT identity drift '+rel)
  after_map[rel]=held
 emit('FINAL-ROOT369-CUSTODY.json',after_map)
 result={'outcome':'passed','source_seal_sha256':SEAL_SHA,'completed_exact_paths':completed,'existing_source_writes':7,'exclusive0644_additions':4,'fragments_folded_once':41,'final_physical_source_count':323,'registered_source_count':303,'dependency_only_count':46,'all369_source_bytes_modes_held':True,'unchanged358_original_identities_held':True,'elapsed_seconds':time.monotonic()-started,'native_compiler_consumer_test_issuer_close_Git_GitHub_publication_executions':0}
 emit('FINAL-ADOPTION-RESULT.json',result);print(json.dumps(result),flush=True)
except BaseException as e:
 result={'outcome':'refused','error_type':type(e).__name__,'message':str(e),'completed_paths':completed,'started_paths':started_paths,'never_reapply_completed_paths':True}
 emit('REFUSAL.json',result);print(json.dumps(result),flush=True);raise
