"""Actual source-held root UIKit startup KLIB/model compilation; zero native tests."""
from pathlib import Path
import json, os, shutil, subprocess, sys, tempfile

ROOT = Path('/root/projects/nativeCmpKit')
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests as lt

assert len(sys.argv) == 2 and sys.argv[1] in {'ui', 'android'}
stage = sys.argv[1]
destination = OUT / stage
assert not destination.exists()
destination.mkdir()
assert shutil.disk_usage(ROOT).free >= 8192 * 1024**2
inputs = lt.snapshot_inputs(ROOT)
lt.write_json(destination / 'library-inputs-before.json', inputs)
java = Path('/usr/lib/jvm/java-17-openjdk-amd64/bin/java').resolve()
environment = os.environ.copy()
for key in ['JAVACMD', 'JAVA_OPTS', 'JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS']:
    environment.pop(key, None)
environment.update(JAVA_HOME='/usr/lib/jvm/java-17-openjdk-amd64', PYTHONDONTWRITEBYTECODE='1')
version = subprocess.run([str(java), '-version'], capture_output=True, env=environment, check=True).stderr.decode()
assert 'version "17.' in version
owned = Path(json.loads((ROOT / 'build/android-webview-fixture-compile-20261027-001/owned.json').read_text())['path'])
assert owned.is_relative_to(Path('/dev/shm')) and owned.name.startswith('nativecmpkit-owned-webview-compile-')
project = owned / 'project'
assert project.is_dir() and not owned.is_symlink() and not project.is_symlink()
for name in inputs:
    if not (project / name).is_file() or lt.sha256(project / name) != inputs[name]:
        target = project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
# Retain only current selected source inputs; no selected source was deleted in
# this checkpoint. Old generated outputs are compilation caches, never test XML.
assert set(lt.snapshot_inputs(project)) == set(inputs)
home = owned / 'gradle-home'
shutil.copy2(OUT / 'model.init.gradle', owned / 'model.init.gradle')
lt.write_json(destination / 'copied-inputs-before.json', lt.snapshot_inputs(project))
assert lt.snapshot_inputs(project) == inputs
environment.update(GRADLE_USER_HOME=str(home), TMPDIR=str(owned), KONAN_DATA_DIR=str(owned / 'konan-data'))
sdk = environment.get('ANDROID_HOME') or environment.get('ANDROID_SDK_ROOT')
if not sdk:
    props = (ROOT / 'local.properties').read_text().splitlines()
    matches = [line.split('=', 1)[1] for line in props if line.startswith('sdk.dir=')]
    assert len(matches) == 1
    sdk = matches[0]
assert (Path(sdk) / 'platforms/android-37.0/android.jar').is_file()
environment['ANDROID_HOME'] = sdk
environment['ANDROID_SDK_ROOT'] = sdk
command = [str(ROOT / 'gradlew'), '-p', str(project), '--project-cache-dir', str(owned / 'project-cache'),
           '--offline', '--no-daemon', '--console=plain', '--no-configuration-cache', '--no-parallel',
           '--max-workers=1', '-Dorg.gradle.jvmargs=-Xmx1536m -Dfile.encoding=UTF-8',
           '-Pkotlin.compiler.execution.strategy=in-process', '-Pkotlin.native.jvmArgs=-Xmx1024m',
           '-Pkotlin.native.home=/root/.konan/kotlin-native-prebuilt-linux-x86_64-2.4.20',
           '--stacktrace']
if stage == 'ui':
    command.extend(['--init-script', str(owned / 'model.init.gradle'), ':calf-ui:inspectGenuineUIKitApplicationModel', ':calf-ui:compileTestKotlinIosSimulatorArm64'])
else:
    command.append(':calf-webview:compileAndroidDeviceTest')
execution = lt.execute(project, command, destination / 'compile.log', 900, 8192, env=environment)
after = lt.snapshot_inputs(ROOT)
copied_after = lt.snapshot_inputs(project)
lt.write_json(destination / 'library-inputs-after.json', after)
lt.write_json(destination / 'copied-inputs-after.json', copied_after)
lt.write_json(destination / 'receipt.json', {
    'recorded_utc': lt.utc_now(), 'source_revision': lt.git_revision(ROOT), 'command': command,
    'execution': execution, 'java_version': version, 'java_executable_sha256': lt.sha256(java),
    'driver_sha256': lt.sha256(Path(__file__)), 'compile_log_sha256': lt.sha256(destination / 'compile.log'), 'model_init_sha256': lt.sha256(OUT / 'model.init.gradle'),
    'source_inputs_held': inputs == after, 'copied_inputs_held': inputs == copied_after,
    'selected_input_count': len(inputs), 'selected_inputs_sha256': lt.input_digest(inputs),
    'host_disk_reserve_maintained_at_completion': shutil.disk_usage(ROOT).free >= 8192 * 1024**2,
    'library_or_device_tests_executed': 0, 'release_readiness_certified': False,
    'scope': 'Actual root Gradle/KGP application model and iOS UI-test KLIB or Android WebView fixture compilation from copied byte-identical inputs, offline in owned tmpfs. The same compilation caches are reused; no XML/native test results are restored. No Apple linking, application/device execution, ABI or release certification.',
})
print(json.dumps({'stage': stage, 'execution': execution, 'held': inputs == after == copied_after, 'library_or_device_tests_executed': 0}), flush=True)
