from pathlib import Path
import hashlib,json,os,subprocess,time,stat,importlib.util
R=Path('/root/nativecmpkit-worktrees/android-permission-lifecycle')
P=Path('/root/nativecmpkit-source-proposals-20261104/android-permission-lifecycle-api35-ygaa_ud4')
existing=json.loads((P/'PREIMAGES.json').read_text())['existing']
new=[
'scripts/ci/android_permission_lifecycle_contract.py', 'scripts/ci/android_permission_lifecycle.py',
'scripts/ci/test_android_permission_lifecycle_source.py',
*[f'calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/{n}.kt' for n in ('OwnedPermissionLifecycle','PermissionLifecycleSystemUi','AndroidPermissionLifecycleDeviceTest')],
*[f'tests/consumer/android-permission-lifecycle/{s}' for s in ('settings.gradle.kts','build.gradle.kts','gradle.properties','src/main/AndroidManifest.xml')],
*[f'tests/consumer/android-permission-lifecycle/src/main/kotlin/io/github/apdelrahman1911/nativecmpkit/verification/permissionlifecycle/{n}.kt' for n in ('PermissionLifecycleActivity','PermissionLifecycleService')]]
for relative in new: os.chmod(R/relative,0o644)
for relative, row in existing.items(): assert oct(stat.S_IMODE((R/relative).stat().st_mode))==row['before_mode'],relative
spec=importlib.util.spec_from_file_location('new_contract_inert_map',R/new[0]);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
files=sorted(set(c.SOURCE_FILES)|set(new)|set(existing))
def capture():
 out={}
 for relative in files:
  p=R/relative;identity=p.lstat();data=p.read_bytes()
  out[relative]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'mode':oct(stat.S_IMODE(identity.st_mode))}
 return out
before=capture()
command=['python3','-B','-m','unittest','-v','scripts.ci.test_android_permission_lifecycle_source']
start=time.monotonic();result=subprocess.run(command,cwd=R,capture_output=True,timeout=60);elapsed=time.monotonic()-start
after=capture()
(P/'NEW-SOURCE-FIRST23.stdout').write_bytes(result.stdout)
(P/'NEW-SOURCE-FIRST23.stderr').write_bytes(result.stderr)
receipt={'provided_base_head':'086224e97cf74c1cc30277b4c6b321867de725df','command':command,'exit_code':result.returncode,'outer_seconds':elapsed,
'before_inputs':before,'after_inputs':after,'held':before==after,'map_scope':'Finite permission-lifecycle source/control+12 NEW paths+6 existing; not ROOT/global/compiler/native/consumer acceptance.',
'prior_NEW14_RED_accepted':0,'new_first_scope':23,'git_commands_executed':0,'compiler_native_controller_planner_network_executed':False,
'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()}
(P/'NEW-SOURCE-FIRST23.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('command','exit_code','outer_seconds','held','new_first_scope')},indent=2))
print(result.stderr.decode(errors='replace')[-2200:])
