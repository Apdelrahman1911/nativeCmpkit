from pathlib import Path
import ast,difflib,hashlib,json,stat,os,time
R=Path('/root/nativecmpkit-worktrees/android-permission-lifecycle');P=Path('/root/nativecmpkit-source-proposals-20261104/android-permission-lifecycle-api35-ygaa_ud4')
first=json.loads((P/'NEW-SOURCE-FIRST23.json').read_text());origin=json.loads((P/'PREIMAGES.json').read_text())
existing=list(origin['existing']); testfile='scripts/ci/test_android_permission_lifecycle_source.py'
new=[testfile,'scripts/ci/android_permission_lifecycle.py','scripts/ci/android_permission_lifecycle_contract.py',
*[f'calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/{n}.kt' for n in ('OwnedPermissionLifecycle','PermissionLifecycleSystemUi','AndroidPermissionLifecycleDeviceTest')],
*[f'tests/consumer/android-permission-lifecycle/{s}' for s in ('settings.gradle.kts','build.gradle.kts','gradle.properties','src/main/AndroidManifest.xml')],
*[f'tests/consumer/android-permission-lifecycle/src/main/kotlin/io/github/apdelrahman1911/nativecmpkit/verification/permissionlifecycle/{n}.kt' for n in ('PermissionLifecycleActivity','PermissionLifecycleService')]]
rows=[];forward=[];inverse=[];F=P/'frozen';V=P/'private-apply';F.mkdir(exist_ok=False);V.mkdir(exist_ok=False)
for relative in existing:
 before=(P/'preimages'/relative).read_bytes();after=(R/relative).read_bytes()
 assert hashlib.sha256(before).hexdigest()==origin['existing'][relative]['before_sha256']
 assert hashlib.sha256(after).hexdigest()==first['after_inputs'][relative]['sha256']
 a,b=before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True)
 groups=list(difflib.SequenceMatcher(None,a,b,autojunk=False).get_grouped_opcodes(6));fragments=[]
 for index,group in enumerate(groups):
  ai,aj=group[0][1],group[-1][2];bi,bj=group[0][3],group[-1][4]
  pre=''.join(a[ai:aj]);post=''.join(b[bi:bj]);assert pre!=post
  assert before.decode().count(pre)==1,(relative,index,'old duplicate');assert after.decode().count(post)==1,(relative,index,'new duplicate')
  fragments.append({'id':f'{relative}:{index+1}','before':pre,'after':post,'before_line':ai+1,'after_line':bi+1})
 patched=before.decode()
 for frag in fragments:
  assert patched.count(frag['before'])==1;patched=patched.replace(frag['before'],frag['after'],1)
 assert patched.encode()==after
 reverted=patched
 for frag in reversed(fragments):
  assert reverted.count(frag['after'])==1;reverted=reverted.replace(frag['after'],frag['before'],1)
 assert reverted.encode()==before
 path=V/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(patched.encode());os.chmod(path,int(origin['existing'][relative]['before_mode'],8))
 destination=F/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(after);os.chmod(destination,stat.S_IMODE((R/relative).stat().st_mode))
 row={'path':relative,'kind':'existing','before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),
 'before_bytes':len(before),'after_bytes':len(after),'worktree_reference_mode':origin['existing'][relative]['before_mode'],
 'integration_mode_policy':'Preserve canonical ROOT existing mode; do not copy sparse worktree umask077 mode blindly. Refuse unexpected source bytes.',
 'fragments':fragments}
 rows.append(row);forward.extend(frag['id'] for frag in fragments);inverse.extend(frag['id'] for frag in reversed(fragments))
for relative in new:
 data=(R/relative).read_bytes();assert hashlib.sha256(data).hexdigest()==first['after_inputs'][relative]['sha256']
 assert stat.S_IMODE((R/relative).stat().st_mode)==0o644
 for home in (F,V):
  destination=home/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data);os.chmod(destination,0o644)
 rows.append({'path':relative,'kind':'addition','after_sha256':hashlib.sha256(data).hexdigest(),'after_bytes':len(data),'required_mode':'0o644','source':'frozen/'+relative})
for rel in new+existing:
 assert (V/rel).read_bytes()==(R/rel).read_bytes()
# Parse NEW Python files and the two touched controller/planner/matrix files without imports/execution.
python_paths=[p for p in existing+new if p.endswith('.py')]
for rel in python_paths: ast.parse((F/rel).read_text(),filename=rel)
manifest={'schema_version':1,'provided_base_head':origin['provided_base_head'],'source_only':True,
'changed_paths':rows,'existing_count':len(existing),'addition_count':len(new),'exact_fragment_count':len(forward),
'forward_fragment_order':forward,'inverse_fragment_order':inverse,'private_apply_exact':True,'private_inverse_exact':True,
'parsed_python_only':python_paths,'frozen_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
'compiler_native_planner_controller_Git_network_ROOT_mutation_executed':False,
'acceptance_scope':'NEW source-only controls and reversible byte recipe only; no native/compilation/API-ABI/consumer/security/release/issue-closure inference.'}
(P/'PATCH.json').write_text(json.dumps(manifest,indent=2)+'\n')
# The observed finite map is private evidence, not a global ROOT/source/compiler inventory.
(P/'FROZEN-MAP.json').write_text(json.dumps(first['after_inputs'],indent=2)+'\n')
(P/'NEW-CONTROLS.txt').write_text('\n'.join(n.name for n in ast.walk(ast.parse((F/testfile).read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'))+'\n')
(P/'PASSIVE-RECIPE-VALIDATION.json').write_text(json.dumps({'files':18,'exact_reversible_fragments':len(forward),'new_files_0644':12,'existing_sparse_modes_held':6,
 'all_frozen_bytes_equal_first23_map':True,'only_python_AST_parse_no_candidate_imports':python_paths,'private_copy_forward_inverse_equal':True,
 'git_commands':0,'native_compiler_planner_controller_network_ROOT_mutations':0},indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ('provided_base_head','existing_count','addition_count','exact_fragment_count','private_apply_exact','private_inverse_exact','frozen_at_utc')},indent=2))
