"""Actual root Android test compilation in owned tmpfs; never instrumented tests."""
from pathlib import Path
import json, os, shutil, subprocess, sys, tempfile

ROOT = Path('/root/projects/nativeCmpKit')
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests as lt

assert len(sys.argv) == 2 and sys.argv[1] in {'red', 'green'}
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
if stage == 'red':
    owned = Path(tempfile.mkdtemp(prefix='nativecmpkit-owned-webview-compile-', dir='/dev/shm'))
    lt.write_json(OUT / 'owned.json', {'path': str(owned)})
    project = owned / 'project'
    project.mkdir()
    names = set(inputs)
    # These files are evaluated by the real build, but are not production/test source.
    for prefix in ['scripts/dependencies', 'licenses']:
        names.update(p.relative_to(ROOT).as_posix() for p in lt.source_files(ROOT, prefix))
    names.update(n for n in ['LICENSE', 'THIRD_PARTY_NOTICES.md'] if (ROOT / n).is_file())
    for name in sorted(names):
        target = project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    home = owned / 'gradle-home'
    (home / 'caches').mkdir(parents=True)
    (home / 'wrapper').symlink_to('/root/.gradle/wrapper', target_is_directory=True)
    (home / 'caches/modules-2').symlink_to('/root/.gradle/caches/modules-2', target_is_directory=True)
else:
    owned = Path(json.loads((OUT / 'owned.json').read_text())['path'])
    assert owned.is_relative_to(Path('/dev/shm')) and owned.name.startswith('nativecmpkit-owned-webview-compile-')
    project = owned / 'project'
    assert project.is_dir() and not owned.is_symlink() and not project.is_symlink()
    # Deliberately refresh changed source/build inputs only, retaining successful
    # same-project dependency/transformation outputs; never restore test XML.
    for name in inputs:
        if not (project / name).is_file() or lt.sha256(project / name) != inputs[name]:
            target = project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
    home = owned / 'gradle-home'

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
           ':calf-webview:compileAndroidDeviceTest']
execution = lt.execute(project, command, destination / 'compile.log', 900, 8192, env=environment)
after = lt.snapshot_inputs(ROOT)
copied_after = lt.snapshot_inputs(project)
lt.write_json(destination / 'library-inputs-after.json', after)
lt.write_json(destination / 'copied-inputs-after.json', copied_after)
lt.write_json(destination / 'receipt.json', {
    'recorded_utc': lt.utc_now(), 'source_revision': lt.git_revision(ROOT), 'command': command,
    'execution': execution, 'java_version': version, 'java_executable_sha256': lt.sha256(java),
    'driver_sha256': lt.sha256(Path(__file__)), 'compile_log_sha256': lt.sha256(destination / 'compile.log'),
    'source_inputs_held': inputs == after, 'copied_inputs_held': inputs == copied_after,
    'selected_input_count': len(inputs), 'selected_inputs_sha256': lt.input_digest(inputs),
    'host_disk_reserve_maintained_at_completion': shutil.disk_usage(ROOT).free >= 8192 * 1024**2,
    'library_or_device_tests_executed': 0, 'release_readiness_certified': False,
    'scope': 'Actual Gradle9.7.1/JDK17/Kotlin2.4.20/AGP9.4.0 root Android-device test compilation from copied byte-identical library/build inputs in owned tmpfs, offline. Does not reveal an unavailable historical hosted error or execute instrumented/library methods.',
})
print(json.dumps({'stage': stage, 'execution': execution, 'held': inputs == after == copied_after, 'library_or_device_tests_executed': 0}), flush=True)
