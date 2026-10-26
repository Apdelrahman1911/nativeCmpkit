import datetime, hashlib, json, os, subprocess, sys
from pathlib import Path
root=Path('/root/projects/nativeCmpKit'); sys.path.insert(0,str(root/'scripts/ci'))
import library_tests as lt
import runtime_context as rt
out=root/'build/ci-verification/maven-staging-001'
assert not (out/'plan.json').exists()
staged=root/'build/verification-repo'
assert not staged.exists(), 'Do not silently overwrite earlier Maven evidence'
def put(name,value): (out/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
before=lt.snapshot_inputs(root); put('inputs-before.json',before)
context=rt.capture(android_package='android-37.0'); put('runtime.json',context)
command=['./gradlew','stageVerificationPublications','-PnativecmpkitVerification=true','-PnativecmpkitVerificationTargets=desktop','-PnativeCmpkit.version=0.1.0-preview.1','--continue','--no-daemon','--console=plain','--max-workers=2','--no-parallel','--no-configuration-cache','-Pkotlin.compiler.execution.strategy=in-process']
put('plan.json', {'command':command,'source_revision':context['source_revision'],'source_tree_dirty':context['source_tree_dirty'],'scope':'Local-only metadata and desktop staging; no Maven-local or registry publication','target_selection':'desktop','candidate_version':'0.1.0-preview.1','timeout_seconds':600,'reserve_mib':8192,'driver_sha256':lt.sha256(Path(__file__))})
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
p=subprocess.run([sys.executable,str(root/'scripts/audit/run_bounded_build.py'),'--log',str(out/'gradle.log'),'--timeout','600','--reserve-mib','8192','--',*command],cwd=root)
after=lt.snapshot_inputs(root); put('inputs-after.json',after)
files={p.relative_to(staged).as_posix():{'sha256':lt.sha256(p),'size_bytes':p.stat().st_size} for p in staged.rglob('*') if p.is_file()} if staged.exists() else {}
put('staged-files.json',files)
receipt={'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_revision':context['source_revision'],'source_tree_dirty':context['source_tree_dirty'],'guard_exit_code':p.returncode,'changed_inputs':[k for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)],'input_count':len(before),'staged_file_count':len(files),'staged_size_bytes':sum(v['size_bytes'] for v in files.values()),'scope':'Producer-only partial local staging, zero tests; not consumer/ABI/legal/dependency/release certification','packages_published':False,'release_created':False}
put('receipt.json',receipt); print(json.dumps(receipt,indent=2),flush=True)
sys.exit(p.returncode or (2 if before!=after else 0))
