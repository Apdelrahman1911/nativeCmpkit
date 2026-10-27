"""Actual root iOS test KLIB/model compilation in owned tmpfs; no UIKit execution."""
from pathlib import Path
import json, os, shutil, subprocess, sys, tempfile

ROOT = Path('/root/projects/nativeCmpKit')
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts/ci'))
import library_tests as lt

stage = 'desktop-focus'
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
# No UIKit application-model init script is used by this common-test compile.
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
test_plan = lt.plan(project, 'desktop', only_modules=('calf-navigation',))
moved = lt.quarantine_reports(project, destination, test_plan)
command.extend(['--init-script', str(project/'scripts/ci/fresh-tests.init.gradle.kts'), ':calf-navigation:desktopTest', '--tests', 'com.mohamedrejeb.calf.navigation.NavArgumentAndBundleTest.everyDeclaredBuiltInValidatesDefaultsAndRequiredPresenceWithoutInference'])
command = ['xvfb-run', '-a', *command]
import time
started_ns = time.time_ns()
execution = lt.execute(project, command, destination / 'compile.log', 900, 8192, env=environment)
ended_ns = time.time_ns()
counts = lt.collect_reports(project, test_plan, started_ns, ended_ns, lt.execution_markers(destination/'compile.log'), host_system='Linux')
lt.write_json(destination/'test-outcomes.json', counts)
for report in counts['modules'][0]['reports']:
    target=destination/'junit'/Path(report['path']).name
    target.parent.mkdir(exist_ok=True)
    shutil.copy2(project/report['path'], target)
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
    'library_or_device_tests_executed': counts['totals']['executed'], 'test_totals': counts['totals'], 'errors': counts['errors'], 'quarantined_prior_reports': moved, 'test_execution_markers': dict(lt.execution_markers(destination/'compile.log')), 'release_readiness_certified': False,
    'scope': 'Actual filtered library desktop execution of the new declared eleven-built-in default/required/null/type verification method, in a copied byte-identical root with actual production dependencies and no stubs. Fresh test init/no reused XML, strict marker/report time/hash/count collection. This is one table-driven method, not eleven test methods, and a held dirty-source diagnostic, not immutable cross-platform, native/ABI/consumer/release verification.',
})
print(json.dumps({'stage': stage, 'execution': execution, 'held': inputs == after == copied_after, 'library_or_device_tests_executed': counts['totals']['executed'], 'totals': counts['totals'], 'errors': counts['errors']}), flush=True)
assert execution['exit_code'] == 0 and not execution.get('stop_reason') and not counts['errors']
assert counts['totals']['executed'] == counts['totals']['passed'] == 1
assert len(counts['modules'][0]['reports']) == 1
assert inputs == after == copied_after
