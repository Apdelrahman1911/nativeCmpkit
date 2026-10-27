"""Copy/hash-verify only owned non-executable templates/source-map data; no native caches."""
from pathlib import Path
import hashlib,json,os,shutil,stat,sys
R=Path('/root/projects/nativeCmpKit');O=Path(__file__).resolve().parent;RESERVE=8192*1024**2
sys.path.insert(0,str(R/'scripts/ci'));import library_tests as lt
root_before=shutil.disk_usage(R).free;tmp_before=shutil.disk_usage(O).free
assert tmp_before>=RESERVE
maps=[]
for area in ['calf-ui/build','calf-file-picker/build','calf-webview/build','build/js','build/wasm']:
 for p in (R/area).rglob('*.map'):
  if not p.is_file() or p.is_symlink() or p.stat().st_mode & 0o111:continue
  if p.stat().st_size>16*1024**2:continue
  try:d=json.loads(p.read_bytes())
  except (ValueError,UnicodeDecodeError):continue
  if isinstance(d,dict) and d.get('version')==3 and isinstance(d.get('sources'),list) and isinstance(d.get('mappings'),str):maps.append(p)
assert maps and len(maps)<10_000
plans=[]
for p in sorted(maps):
 n=p.relative_to(R).as_posix();s=p.stat();h=lt.sha256(p);target=O/'source-map-data'/n
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);target.chmod(stat.S_IMODE(s.st_mode))
 assert lt.sha256(p)==h==lt.sha256(target) and (p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns)==(s.st_ino,s.st_size,s.st_mtime_ns)
 plans.append({'root_path':n,'target_path':target.relative_to(O).as_posix(),'bytes':s.st_size,'sha256':h,'mode':stat.S_IMODE(s.st_mode),'original_hard_links':s.st_nlink})
# Preserve every template byte; reject native/binary-executable payloads before moving.
template=R/'build/docs-verification/locked-002/venv/lib/python3.12/site-packages/material/templates'
assert template.is_dir() and not template.is_symlink()
template_files=[]
for p in sorted(template.rglob('*')):
 assert not p.is_symlink()
 if p.is_dir():continue
 assert p.is_file() and p.stat().st_mode & 0o111 == 0
 assert p.suffix.lower() not in {'.so','.dll','.dylib','.exe','.node','.py','.pyc','.pyo','.sh','.bat','.ps1'}
 with p.open('rb') as f:head=f.read(4)
 assert head not in {b'\x7fELF',b'\xcf\xfa\xed\xfe',b'\xfe\xed\xfa\xcf'} and not head.startswith((b'#!',b'MZ'))
 template_files.append({'path':p.relative_to(template).as_posix(),'bytes':p.stat().st_size,'sha256':lt.sha256(p)})
assert template_files
new_template=O/'material-templates';assert not new_template.exists();shutil.copytree(template,new_template)
assert all(lt.sha256(new_template/x['path'])==x['sha256'] and (new_template/x['path']).stat().st_size==x['bytes'] for x in template_files)
assert shutil.disk_usage(O).free>=RESERVE
# Only verified originals under the finite task-owned areas are unlinked.
for x in plans:
 p=R/x['root_path'];t=O/x['target_path'];assert not p.is_symlink() and lt.sha256(p)==x['sha256']==lt.sha256(t)
 p.unlink();p.symlink_to(t)
 assert p.is_symlink() and p.resolve()==t.resolve() and lt.sha256(p)==x['sha256']
assert all(lt.sha256(template/x['path'])==x['sha256'] for x in template_files)
shutil.rmtree(template);template.symlink_to(new_template,target_is_directory=True)
assert template.is_symlink() and all(lt.sha256(template/x['path'])==x['sha256'] for x in template_files)
r={'recorded_utc':lt.utc_now(),'source_revision':lt.git_revision(R),'root_free_before':root_before,'root_free_after':shutil.disk_usage(R).free,'tmpfs_free_before':tmp_before,'tmpfs_free_after':shutil.disk_usage(O).free,'reserve_bytes':RESERVE,'source_maps':plans,'source_map_bytes':sum(x['bytes'] for x in plans),'source_map_files':len(plans),'template_root_path':template.relative_to(R).as_posix(),'template_files':template_files,'template_bytes':sum(x['bytes'] for x in template_files),'native_or_executable_cache_relocated':False,'other_projects_or_shared_dependency_caches_removed':False,'all_selected_bytes_verified_before_copy_before_unlink_and_after_symlink':True,'consumer_or_native_methods_executed':0,'scope':'Local task-owned data relocation only. No executable/native-loading cache is moved. JSON-v3 source maps and Material templates remain byte-available at original paths; no browser/cache equivalence or documentation pass is inferred. Shared dependency cache remains untouched. Local symlinks point to owned tmpfs and are not committed.'}
(O/'receipt.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ['root_free_before','root_free_after','tmpfs_free_after','source_map_files','source_map_bytes','template_bytes']}))
