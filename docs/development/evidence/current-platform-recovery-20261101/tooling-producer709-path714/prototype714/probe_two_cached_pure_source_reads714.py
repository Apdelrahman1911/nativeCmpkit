import cProfile,json,sys,time,hashlib
from functools import lru_cache
from pathlib import Path
sys.path.insert(0,"scripts/ci")
import macos_share_ci668_composition as joint
import macos_share_appkit_only_source_projection as appkit
from android_external328_source_projection import current_source_for_history
@lru_cache(maxsize=512)
def pure_parts(relative):
 return appkit._path(relative)
def pure_identity(relative,payload):
 appkit.need(type(relative) is str,"unsafe-AppKit-source-identity")
 pure_parts(relative)
 joint.need(type(payload) is bytes and 0 < len(payload) <= joint.MAX_SOURCE,"bounded-complete-share-CI-source-operands-required")
joint._identity=pure_identity
raw=Path("scripts/ci/library_tests.py").read_bytes()
p=cProfile.Profile(); began=time.monotonic(); p.enable()
for _ in range(2):
 result=current_source_for_history("scripts/ci/library_tests.py",raw)
p.disable(); p.dump_stats(sys.argv[1])
print(json.dumps({"calls":2,"elapsed_seconds":time.monotonic()-began,"input_bytes":len(raw),"input_sha256":hashlib.sha256(raw).hexdigest(),"result_bytes":len(result),"result_sha256":hashlib.sha256(result).hexdigest(),"pure_cache_info":pure_parts.cache_info()._asdict(),"production_source_or_unit_tests_modified_or_replayed":0}))
