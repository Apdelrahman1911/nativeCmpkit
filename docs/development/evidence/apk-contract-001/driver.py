from pathlib import Path
import sys,json,os,hashlib
root=Path.cwd();sys.path.insert(0,str(root/'scripts/ci'))
import library_tests as lt,runtime_context as runtime
out=root/'build/ci-verification/apk-contract-001'
context=runtime.capture(android_package='android-37.0')
before=lt.snapshot_inputs(root);lt.write_json(out/'inputs-before.json',before);lt.write_json(out/'runtime.json',context)
plan=lt.plan(root,'android-device');lt.write_json(out/'plan.json',plan)
common=['./gradlew','--continue','--no-daemon','--no-parallel','--console=plain','--no-configuration-cache','--max-workers=2','-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8','-Pkotlin.compiler.execution.strategy=in-process','--init-script','scripts/ci/fresh-tests.init.gradle.kts','-Pandroid.injected.device.serial=emulator-5588']
commands=[common+[p['project']+':assembleAndroidDeviceTest' for p in plan['expected']],common+['--dry-run']+[p['task'] for p in plan['expected']]]
results=[]
for name,command in zip(['apk-assembly','connected-task-configuration'],commands):
 result=lt.execute(root,command,out/(name+'.log'),900 if name=='apk-assembly' else 180,8192)
 results.append({'stage':name,'command':command,**result})
 if result['exit_code']!=0:break
after=lt.snapshot_inputs(root);lt.write_json(out/'inputs-after.json',after)
changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
artifacts={p.relative_to(root).as_posix():lt.sha256(p) for module in plan['expected'] for p in (root/module['module']/'build/outputs/apk').rglob('*.apk')}
receipt={'source_revision':context['source_revision'],'source_tree_dirty':context['source_tree_dirty'],'runtime':context,'inputs_before_sha256':lt.input_digest(before),'inputs_after_sha256':lt.input_digest(after),'input_count':len(before),'changed_inputs':changed,'commands':results,'apk_outputs':artifacts,'tests_executed':0,'passed_compilation_and_configuration':len(results)==2 and all(r['exit_code']==0 and not r.get('stop_reason') for r in results) and not changed,'scope':'Compile actual library device-test APKs and configure actual AGP tasks only. No emulator/device, native runtime, connected-task doFirst, consumer or release verification.','packages_published':False,'release_readiness_certified':False}
lt.write_json(out/'receipt.json',receipt)
print(json.dumps({k:receipt[k] for k in ('source_revision','source_tree_dirty','input_count','changed_inputs','commands','tests_executed','passed_compilation_and_configuration')},indent=2))
sys.exit(0 if receipt['passed_compilation_and_configuration'] else 1)
