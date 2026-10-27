from pathlib import Path
import datetime as dt, hashlib, json, os, re, subprocess, time
out=Path(__file__).resolve().parent; os.environ['TMPDIR']=str(out)
paths=['scripts/ci/test_workflow_matrix.py','scripts/ci/workflow_matrix.py','.github/workflows/gradle.yml']
snapshot=lambda:{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
before=snapshot(); command=['python3','-B','-m','unittest','discover','-s','scripts/ci','-p','test_workflow_matrix.py','-v']; start=time.monotonic()
r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90); (out/'red002.log').write_bytes(r.stdout)
assert before==snapshot() and r.returncode==1 and b'Ran 15 tests' in r.stdout and b'errors=2' in r.stdout
record={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'command':command,'execution':{'exit_code':r.returncode,'elapsed_seconds':round(time.monotonic()-start,3)},'methods':int(re.findall(rb'^Ran (\d+) tests in ',r.stdout,re.M)[-1]),'expected_errors':2,'held_source_hashes':before,'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'log_sha256':hashlib.sha256(r.stdout).hexdigest(),'scope':'Executed finite-matrix Python regression red; no hosted/browser/library test executed and no release or issue gate passed.'}
(out/'red002.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
