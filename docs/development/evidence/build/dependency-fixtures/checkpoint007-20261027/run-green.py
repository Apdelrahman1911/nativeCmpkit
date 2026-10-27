from pathlib import Path
import hashlib,json,os,subprocess,time
ROOT=Path('/root/projects/nativeCmpKit');OUT=Path(__file__).resolve().parent
paths=['README.md','gradle_fixtures.py','integrity.py','integrity_model.py','resolve-graphs.init.gradle','test_integrity.py','runtime_witness.py','runtime-witness.md','test_runtime_witness.py','checkpoint-offline-007.json']
def inputs():return {f'scripts/dependencies/{n}':hashlib.sha256((ROOT/'scripts/dependencies'/n).read_bytes()).hexdigest() for n in paths}
before=inputs();bound=OUT/'inputs-green';bound.mkdir()
for n in paths:(bound/n).write_bytes((ROOT/'scripts/dependencies'/n).read_bytes())
(OUT/'green-inputs-before.json').write_text(json.dumps(before,indent=2,sort_keys=True)+'\n');env=dict(os.environ,TMPDIR='/dev/shm',PYTHONDONTWRITEBYTECODE='1');results=[]
for name,pattern,count in [('core-green','test_integrity.py',168),('witness-green','test_runtime_witness.py',111)]:
 command=['python3','-m','unittest','discover','-s','scripts/dependencies','-p',pattern,'-v'];start=time.monotonic()
 with (OUT/(name+'.log')).open('xb') as log:p=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=30)
 elapsed=round(time.monotonic()-start,3);text=(OUT/(name+'.log')).read_text();assert f'Ran {count} tests in ' in text
 results.append({'command':command,'exit_code':p.returncode,'elapsed_seconds':elapsed,'test_methods':count,'log':name+'.log','log_sha256':hashlib.sha256(text.encode()).hexdigest(),'gradle_java_jcmd_network_or_library_methods_executed':0});assert before==inputs()
(OUT/'green-inputs-after.json').write_text(json.dumps(inputs(),indent=2,sort_keys=True)+'\n');(OUT/'green-execution.json').write_text(json.dumps({'inputs_held':before==inputs(),'results':results,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty_development_tool_snapshot':True},indent=2,sort_keys=True)+'\n')
print(json.dumps(results,indent=2));assert all(r['exit_code']==0 for r in results)
