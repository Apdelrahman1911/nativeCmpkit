"""Actual configured IO/Coil iOS production/test KLIB compilation; zero Apple executions."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

ROOT = Path('/root/projects/nativeCmpKit')
BASE = Path(__file__).parent
OUT = BASE / 'compile001'
OUT.mkdir(exist_ok=False)
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests as runner

before = runner.snapshot_inputs(ROOT)
runner.write_json(OUT / 'inputs-before.json', before)
environment = os.environ.copy()
for key in ('JAVA_OPTS', 'GRADLE_OPTS', 'JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS'):
    environment.pop(key, None)
environment.update(JAVA_HOME='/usr/lib/jvm/java-17-openjdk-amd64',
                   TMPDIR=str(BASE), PYTHONDONTWRITEBYTECODE='1')
java = Path(environment['JAVA_HOME']) / 'bin/java'
version = subprocess.run([str(java), '-version'], capture_output=True, check=True, env=environment).stderr.decode()
assert 'version "17.' in version
command = ['./gradlew', ':calf-io:compileTestKotlinIosSimulatorArm64',
           ':calf-file-picker-coil:compileTestKotlinIosSimulatorArm64',
           '--offline', '--no-daemon', '--console=plain', '--no-configuration-cache', '--no-parallel',
           '--max-workers=1', '-Dorg.gradle.jvmargs=-Xmx1536m -Dfile.encoding=UTF-8',
           '-Pkotlin.compiler.execution.strategy=in-process', '-Pkotlin.native.jvmArgs=-Xmx1024m',
           '-Pkotlin.native.home=/root/.konan/kotlin-native-prebuilt-linux-x86_64-2.4.20']
assert shutil.disk_usage(BASE).free >= 2 * 1024 ** 3
execution = runner.execute(ROOT, command, OUT / 'compile.log', 900, 8192, env=environment)
after = runner.snapshot_inputs(ROOT)
runner.write_json(OUT / 'inputs-after.json', after)
record = {'recorded_utc': runner.utc_now(), 'source_revision': runner.git_revision(ROOT),
          'dirty_worktree': True, 'command': command, 'execution': execution,
          'java_version': version, 'java_executable_sha256': runner.sha256(java),
          'driver_sha256': runner.sha256(Path(__file__)), 'log_sha256': runner.sha256(OUT / 'compile.log'),
          'source_input_count': len(before), 'source_digest': runner.input_digest(before),
          'source_inputs_held': before == after, 'changed_inputs': sorted(
              name for name in before.keys() | after.keys() if before.get(name) != after.get(name)),
          'root_free_after': shutil.disk_usage(ROOT).free, 'tmpfs_free_after': shutil.disk_usage(BASE).free,
          'disk_reserve_mib': 8192, 'actual_library_or_native_methods_executed': 0,
          'publication_performed': False, 'release_readiness_certified': False,
          'scope': 'Configured exact current-source production/common/iOS-test KLIB typechecking on Linux, '
                   'using pinned KGP/compiler/platform KLIBs and existing offline dependencies. '
                   'No stubs, Apple link/simulator/device execution, ASan, packaged consumers or ABI certification.'}
runner.write_json(OUT / 'receipt.json', record)
print(json.dumps(record, indent=2), flush=True)
sys.exit(0 if execution['exit_code'] == 0 and not execution.get('stop_reason') and before == after else 1)
