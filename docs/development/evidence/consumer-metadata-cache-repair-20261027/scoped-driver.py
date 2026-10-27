"""Frozen scoped synthetic regressions only; actual DSL/native runs remain separate."""
from pathlib import Path
import datetime as dt,hashlib,json,re,shutil,subprocess,sys,time
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).resolve().parent;OUT=BASE/'final-scoped'
assert not OUT.exists();OUT.mkdir()
sys.path.insert(0,str(ROOT/'scripts/ci'));import core_io_consumer as c
extra=['.github/workflows/gradle.yml','tests/consumer/test_core_io_fixture_contract.py']
def inputs():
 values=c.inputs(ROOT)
 values.update({name:c.lt.sha256(ROOT/name) for name in extra})
 return dict(sorted(values.items()))
def dump(name,value):(OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
before=inputs();dump('inputs-before.json',before)
commands=[('core-io',['python3','-B','-m','unittest','discover','-s','scripts/ci','-p','test_core_io_*.py','-v'],55),
 ('dependency-keys',['python3','-B','-m','unittest','discover','-s','scripts/ci','-p','test_dependency_cache_inputs.py','-v'],9),
 ('workflow-source',['python3','-B','-m','unittest','discover','-s','scripts/ci','-p','test_workflow_source.py','-v'],12),
 ('native-delegate',['python3','-B','-m','unittest','discover','-s','scripts/ci','-p','test_native_alert_delegate_contract.py','-v'],7),
 ('ios-receipts',['python3','-B','-m','unittest','discover','-s','scripts/ci','-p','test_ios_application_receipts.py','-v'],26),
 ('fixture-source',['python3','-B','-m','unittest','discover','-s','tests/consumer','-p','test_core_io_fixture_contract.py','-v'],15),
 ('actionlint',['/tmp/nativecmpkit-actionlint-1.7.12/actionlint','.github/workflows/gradle.yml','.github/workflows/build-native-libs.yml'],None)]
results=[]
for name,command,count in commands:
 start=time.monotonic();log=OUT/(name+'.log')
 with log.open('xb') as stream:run=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
 text=log.read_text();actual=int(re.findall(r'^Ran (\d+) tests? in ',text,re.M)[-1]) if count is not None else None
 assert run.returncode==0 and actual==count and (count is None or re.search(r'^OK$',text,re.M)),name
 results.append({'name':name,'command':command,'exit_code':run.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'Python_methods':actual,'log_sha256':c.lt.sha256(log)})
after=inputs();dump('inputs-after.json',after);assert before==after
selected=['scripts/ci/core_io_consumer.py','scripts/ci/test_core_io_consumer.py','scripts/ci/test_core_io_metadata_cache.py',
 'scripts/ci/dependency_cache_inputs.py','scripts/ci/test_dependency_cache_inputs.py','scripts/ci/test_workflow_source.py',
 'tests/consumer/io-desktop/build.gradle.kts','tests/consumer/io-desktop/README.md','tests/consumer/build.gradle.kts',
 'tests/consumer/test_core_io_fixture_contract.py','.github/workflows/gradle.yml']
for name in selected:
 p=OUT/'green-source'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p);assert c.lt.sha256(p)==before[name]
dump('receipt.json',{'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':c.lt.git_revision(ROOT),'dirty_worktree':True,'source_input_count':len(before),'source_inputs_sha256':c.lt.input_digest(before),'source_inputs_held':before==after,'commands':results,'Python_methods':sum(count or 0 for _,_,count in commands),'library_native_or_consumer_methods_executed':0,'release_readiness_certified':False,'scope':'124 scoped synthetic/lexical Python methods and actionlint only. Counts overlap earlier53/55,9,12,13/15,7/26 runs. No Gradle, UIKit, packaged consumers or ordinary trust attestation.'})
print(json.dumps({'passed':True,'source_inputs':len(before),'Python_methods':124,'commands':len(results)},indent=2))
