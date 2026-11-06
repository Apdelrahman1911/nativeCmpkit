import os,sys,stat,hashlib,json,builtins,io,importlib.machinery,importlib.util,tempfile,unittest,time
from pathlib import Path
KEYS=("st_dev","st_ino","st_mode","st_nlink","st_uid","st_gid","st_size","st_atime_ns","st_mtime_ns","st_ctime_ns")
def ident(s):return {k:int(getattr(s,k)) for k in KEYS}
def read(path):
 fd=os.open(path,os.O_RDONLY|os.O_NOATIME|os.O_NOFOLLOW)
 try:
  s=ident(os.fstat(fd));assert stat.S_ISREG(s['st_mode']) and s['st_nlink']==1 and s['st_size']<=1048576
  b=b''
  while len(b)<s['st_size']:
   chunk=os.read(fd,min(65536,s['st_size']-len(b)));assert chunk;b+=chunk
  assert not os.read(fd,1) and ident(os.fstat(fd))==s;return b,s
 finally:os.close(fd)
m=json.loads(read(sys.argv[1])[0]);model=m['model'];prefix=model+'/';originals=('/root/projects/nativeCmpKit',m['worktree']);pins=m['model_pins'];tempfile.tempdir=m['tmp']
assert os.getcwd()==model and sys.dont_write_bytecode
rawopen=os.open;rawbuiltin=builtins.open;rawio=io.open

def prohibited(path):
 if not isinstance(path,(str,bytes,os.PathLike)):return
 p=os.path.abspath(os.fsdecode(path))
 if 'test_javafx_ordinary_success_trace.py' in p.split('/'):raise RuntimeError('protected source/copy access refused')
 if any(p==r or p.startswith(r+'/') for r in originals):raise RuntimeError('original worktree/ROOT access refused; finite model only')

def noatime_open(path,flags,mode=0o777,*,dir_fd=None):
 request=path
 if dir_fd is not None and isinstance(path,(str,bytes,os.PathLike)) and not os.path.isabs(os.fsdecode(path)):
  base=os.readlink('/proc/self/fd/'+str(dir_fd));request=base+'/'+os.fsdecode(path)
 prohibited(request)
 if isinstance(request,(str,bytes,os.PathLike)):
  full=os.path.abspath(os.fsdecode(request))
  if full==model or full.startswith(prefix):
   if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):raise RuntimeError('model source write refused')
   flags|=os.O_NOATIME|os.O_NOFOLLOW
 return rawopen(path,flags,mode,dir_fd=dir_fd)
for cap in ('supports_dir_fd','supports_fd','supports_follow_symlinks','supports_effective_ids'):
 if rawopen in getattr(os,cap):getattr(os,cap).add(noatime_open)
os.open=noatime_open

def stream(original):
 def open_(file,mode='r',buffering=-1,encoding=None,errors=None,newline=None,closefd=True,opener=None):
  prohibited(file)
  if isinstance(file,(str,bytes,os.PathLike)) and os.path.abspath(os.fsdecode(file)).startswith(prefix):
   if any(v in mode for v in 'wax+'):raise RuntimeError('model source stream write refused')
   prior=opener
   def opener_(path,flags):return (noatime_open(path,flags) if prior is None else prior(path,flags|os.O_NOATIME|os.O_NOFOLLOW))
   opener=opener_
  return original(file,mode,buffering,encoding,errors,newline,closefd,opener)
 return open_
builtins.open=stream(rawbuiltin);io.open=stream(rawio)
class Source(importlib.machinery.SourceFileLoader):
 def get_code(self,fullname):
  b,s=read(self.path);pin=pins[self.path[len(prefix):]]
  assert s==pin['stat'] and len(b)==pin['size'] and hashlib.sha256(b).hexdigest()==pin['sha256']
  return self.source_to_code(b,self.path)
 def set_data(self,*a,**kw):raise RuntimeError('no source bytecode writes')
class Finder:
 def find_spec(self,fullname,path=None,target=None):
  component=fullname.replace('.','/') if path is None else fullname.rsplit('.',1)[-1]
  for base in (sys.path if path is None else path):
   if not isinstance(base,str):continue
   base=os.path.abspath(base)
   if base!=model and not base.startswith(prefix):continue
   for suffix,package in ((component+'/__init__.py',True),(component+'.py',False)):
    filename=base+'/'+suffix;relative=filename[len(prefix):]
    if relative in pins:
     loader=Source(fullname,filename);return importlib.util.spec_from_file_location(fullname,filename,loader=loader,submodule_search_locations=[os.path.dirname(filename)] if package else None)
  return None
sys.meta_path.insert(0,Finder())
for name in ('stat','lstat'):
 original=getattr(os,name)
 def wrapped(path,*a,_original=original,**kw):prohibited(path);return _original(path,*a,**kw)
 for cap in ('supports_dir_fd','supports_fd','supports_follow_symlinks','supports_effective_ids'):
  if original in getattr(os,cap):getattr(os,cap).add(wrapped)
 setattr(os,name,wrapped)
def audit(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','os.fork','os.forkpty','socket.connect','socket.__new__'):raise RuntimeError('source-only test process/network request refused')
 if event in ('open','os.scandir','os.listdir') and args:prohibited(args[0])
 if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.path.abspath(os.fsdecode(args[0]));mode=args[1] if len(args)>1 else None;flags=args[2] if len(args)>2 else 0
  if p==model or p.startswith(prefix):
   if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (type(flags) is int and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):raise RuntimeError('readonly source model required')
 if event in ('os.remove','os.rmdir','os.rename','os.mkdir','os.chmod','os.chown','os.utime','os.truncate'):
  for p in args[:2]:
   if isinstance(p,(str,bytes,os.PathLike)):
    prohibited(p);p=os.path.abspath(os.fsdecode(p))
    if p==model or p.startswith(prefix):raise RuntimeError('model source mutation refused')
sys.addaudithook(audit);sys.path[:0]=[model+'/scripts/ci',model+'/scripts/native',model]
print('NCK_MAC_P5_IMPORTANT8_BEGIN',flush=True);suite=unittest.TestLoader().loadTestsFromNames(m['selected']);assert suite.countTestCases()==8
start=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(suite)
out={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'successful':result.wasSuccessful(),'suite_elapsed_seconds':time.monotonic()-start,'compiler':0,'native':0}
print('NCK_MAC_P5_IMPORTANT8_END '+json.dumps(out,sort_keys=True),flush=True)
raise SystemExit(0 if result.wasSuccessful() and result.testsRun==8 and not result.skipped else 1)
