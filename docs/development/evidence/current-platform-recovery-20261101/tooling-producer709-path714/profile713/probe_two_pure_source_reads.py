import cProfile,json,sys,time,hashlib
from pathlib import Path
sys.path.insert(0,"scripts/ci")
from android_external328_source_projection import current_source_for_history
raw=Path("scripts/ci/library_tests.py").read_bytes()
p=cProfile.Profile(); began=time.monotonic(); p.enable()
for _ in range(2):
 result=current_source_for_history("scripts/ci/library_tests.py",raw)
p.disable(); p.dump_stats(sys.argv[1])
print(json.dumps({"calls":2,"elapsed_seconds":time.monotonic()-began,"input_bytes":len(raw),"input_sha256":hashlib.sha256(raw).hexdigest(),"result_bytes":len(result),"result_sha256":hashlib.sha256(result).hexdigest(),"tests_native_compiler_network_Git_or_ROOT_writes":0}))
