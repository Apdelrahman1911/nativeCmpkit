"""Fresh locked metadata and fail-closed local material collection; no native build/install."""
from pathlib import Path
import datetime as dt, hashlib, json, os, shutil, signal, subprocess, sys, time
ROOT=Path('/root/projects/nativeCmpKit')
BASE=Path('/dev/shm/nativecmpkit-license-supplement-work-20261027')
OUT=BASE/'real001'
CACHE=Path('/root/.cargo/registry/cache/index.crates.io-1949cf8c6b5b557f')
CATALOG=ROOT/'licenses/native-dependency-supplements'
assert not OUT.exists() and CACHE.is_dir() and not CACHE.is_symlink()
assert shutil.disk_usage(ROOT).free>8*1024**3 and shutil.disk_usage(BASE).free>2*1024**3
OUT.mkdir();ENV=os.environ.copy();ENV['PATH']='/root/.cargo/bin:'+ENV.get('PATH','')
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 paths={ROOT/'scripts/native/artifacts.py',ROOT/'rust-toolchain.toml',ROOT/'tests/consumer/collect_native_licenses.py',ROOT/'tests/consumer/native_license_supplements.py',ROOT/'tests/consumer/verify_artifacts.py'}
 paths.update(p for p in CATALOG.rglob('*') if p.is_file())
 for module in ('calf-file-picker','calf-share'):
  paths.update(ROOT/module/'native'/filename for filename in ('Cargo.toml','Cargo.lock'))
 return {p.relative_to(ROOT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)}
def run(label,command):
 start=utc();tick=time.monotonic()
 with (OUT/(label+'.stdout')).open('xb') as out,(OUT/(label+'.stderr')).open('xb') as err:
  process=subprocess.Popen(command,cwd=ROOT,env=ENV,stdout=out,stderr=err,start_new_session=True)
  try:process.wait(timeout=180)
  except BaseException:
   if process.poll() is None:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
   raise
  row={'command':command,'exit_code':process.returncode,'started_utc':start,'finished_utc':utc(),'elapsed_seconds':round(time.monotonic()-tick,3),'stdout_sha256':sha(OUT/(label+'.stdout')),'stderr_sha256':sha(OUT/(label+'.stderr'))}
 return row
before=snapshot();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
(OUT/'inputs-before.json').write_text(json.dumps(before,indent=2,sort_keys=True)+'\n')
root_free=shutil.disk_usage(ROOT).free
rows=[]
for module in ('calf-file-picker','calf-share'):
 meta=OUT/(module+'-metadata.json')
 row=run(module+'-metadata',['/usr/bin/python3','-B','scripts/native/artifacts.py','metadata','--module',module,'--output',str(meta)])
 rows.append({'module':module,'phase':'locked-offline-sanitized-metadata',**row})
 if row['exit_code']!=0:break
 row=run(module+'-collection',['/usr/bin/python3','-B','tests/consumer/collect_native_licenses.py','--metadata',str(meta),'--registry-cache',str(CACHE),'--vcs-supplements',str(CATALOG),'--output',str(OUT/module)])
 report_path=OUT/module/'META-INF/nativecmpkit/native-dependencies'/module/'licenses-report.json'
 report=json.loads(report_path.read_bytes())
 rows.append({'module':module,'phase':'explicit-vcs-material-collection','metadata_sha256':sha(meta),'report_sha256':sha(report_path),'packages':len(report['packages']),'gaps':len(report['gaps']),'complete_material_collection':report['complete_material_collection'],'license_obligations_reviewed':report['license_obligations_reviewed'],**row})
after=snapshot();(OUT/'inputs-after.json').write_text(json.dumps(after,indent=2,sort_keys=True)+'\n')
receipt={'source_revision':head,'dirty_worktree':True,'source_held':before==after,'source_inputs':len(before),'observations':rows,'root_free_before':root_free,'root_free_after':shutil.disk_usage(ROOT).free,'sanitized_metadata_only_exported':True,'no_native_compile_or_runtime':True,'no_live_notice_installation':True,'no_network_or_registry_publication':True,'legal_and_release_gates_cleared':False,'collector_nonzero_exit_preserved':True,'driver_sha256':sha(Path(__file__))}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt,indent=2),flush=True)
assert before==after
assert len(rows)==4 and all(row['exit_code']==0 for row in rows if row['phase']=='locked-offline-sanitized-metadata')
# Collection intentionally fails for unreviewed material. Do not turn this
# verification driver's completion into a collection/legal success claim.
assert all(row['exit_code']==1 and row['gaps']>0 and row['complete_material_collection'] is False and row['license_obligations_reviewed'] is False for row in rows if row['phase']=='explicit-vcs-material-collection')
