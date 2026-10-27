from pathlib import Path
import json,os,sys
sys.path.insert(0,'/root/projects/nativeCmpKit/scripts/dependencies')
import integrity as d
os.environ['JAVA_HOME']='/usr/lib/jvm/java-17-openjdk-amd64'
result=d.run(Path('/dev/shm/nativecmpkit-owned-daemon-timeout-red-20261027/project'),entry_root='.',run_id='bootstrap',mode='bootstrap',timeout=20,reserve_mib=8192,gradle_home=Path('/opt/gradle/gradle-9.7.1'),fresh_cache=True)
Path('/dev/shm/nativecmpkit-owned-daemon-timeout-red-20261027/old-controller-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
