"""Current held exact IO/Coil policy checks; Python fixtures, zero Native execution."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts/ci'))
import library_tests as r
before=r.snapshot_inputs(ROOT);r.write_json(BASE/'tooling002-inputs-before.json',before)
rows=[]
for name,command in [('focused', ['python3','-B','-m','unittest','discover','-s','scripts/ci','-p','test_ios_io_*.py','-v']),('all-ci',['python3','-B','-m','unittest','discover','-s','scripts/ci','-p','test_*.py','-v'])]:
 log=BASE/('tooling002-'+name+'.log')
 with log.open('x') as stream:
  result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=240)
 text=log.read_text();n=re.findall(r'^Ran (\d+) tests? in ',text,re.M)
 row={'name':name,'command':command,'exit_code':result.returncode,'actual_python_methods':int(n[-1]) if n else None,'summary_OK':bool(re.search(r'^OK$',text,re.M)),'log':log.name,'log_sha256':r.sha256(log)}
 rows.append(row)
 if result.returncode:break
finally_inputs=r.snapshot_inputs(ROOT);r.write_json(BASE/'tooling002-inputs-after.json',finally_inputs)
receipt={'source_revision':r.git_revision(ROOT),'dirty_worktree':True,'recorded_utc':r.utc_now(),'source_inputs_held':before==finally_inputs,'source_digest':r.input_digest(before),'source_input_count':len(before),'results':rows,'passed':len(rows)==2 and before==finally_inputs and all(x['exit_code']==0 and x['actual_python_methods'] and x['summary_OK'] for x in rows),'focused_cases_included_in_all_ci':True,'actual_native_or_library_methods_executed':0,'publication_performed':False,'release_readiness_certified':False}
r.write_json(BASE/'tooling002-receipt.json',receipt);print(json.dumps(receipt,indent=2));sys.exit(0 if receipt['passed'] else 1)
