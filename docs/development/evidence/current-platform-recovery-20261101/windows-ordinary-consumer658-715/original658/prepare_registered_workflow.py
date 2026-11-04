#!/usr/bin/env python3
"""External source-only preparation; never import or execute proposal controllers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PACKET = Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-current2ee707-route658')
ROOT = Path('/root/projects/nativeCmpKit')
PROPOSED = PACKET / 'proposed'
PREIMAGE_SHA = '4e3bec6b1ae93414ad1e663d232d2d264ab191908fb9493ff0f787c0278df5e8'

def regular(path):
    first = path.stat(follow_symlinks=False)
    assert path.is_file() and not path.is_symlink() and first.st_nlink == 1 and first.st_size <= 512 * 1024
    value = path.read_bytes()
    second = path.stat(follow_symlinks=False)
    assert (first.st_dev, first.st_ino, first.st_size, first.st_mtime_ns, first.st_ctime_ns) == (second.st_dev, second.st_ino, second.st_size, second.st_mtime_ns, second.st_ctime_ns)
    return value

def sha(value):
    return hashlib.sha256(value).hexdigest()

def new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(value)
    path.chmod(0o600)

def replace_once(value, before, after):
    assert value.count(before) == 1
    return value.replace(before, after, 1)

base = regular(ROOT / '.github/workflows/javafx-library-candidate.yml')
assert sha(base) == PREIMAGE_SHA and base.endswith(b'\n')
assert not (PROPOSED / '.github/workflows/javafx-library-candidate.yml').exists()
standalone_path = PROPOSED / '.github/workflows/javafx-ordinary-maven-consumer.yml'
standalone = regular(standalone_path)
job = standalone.split(b'jobs:\n', 1)[1]
assert job.startswith(b'  ordinary-windows-consumer1:\n')
job = replace_once(job, b"inputs.focus == 'ordinary-windows-consumer1'", b"inputs.platform == 'windows-ordinary-consumer1'")
old_line = b'        options: [linux-arm64, macos-arm64, macos-x64, windows]\n'
new_line = b'        options: [linux-arm64, macos-arm64, macos-x64, windows, windows-ordinary-consumer1]\n'
postimage = replace_once(base, old_line, new_line) + job
original_job = base[base.index(b'  public-stop:\n'):]
new(PACKET / 'retained/javafx-library-candidate.preimage.yml', base)
new(PACKET / 'retained/javafx-ordinary-maven-consumer.standalone-unadopted.yml', standalone)
new(PROPOSED / '.github/workflows/javafx-library-candidate.yml', postimage)
standalone_path.unlink()  # Own unsealed draft only; its exact bytes are retained above.

controller_path = PROPOSED / 'scripts/ci/javafx_ordinary_maven_consumer.py'
controller_before = regular(controller_path)
new(PACKET / 'retained/javafx_ordinary_maven_consumer.before-registered-route.py', controller_before)
source = controller_before.decode('utf-8')
source = replace_once(source, "WORKFLOW = '.github/workflows/javafx-ordinary-maven-consumer.yml'", "WORKFLOW = '.github/workflows/javafx-library-candidate.yml'")
old_binding = '''    need(verifier.get('passed') is True and verifier.get('ordinary_resolution_bytes_bound') is True and
         verifier.get('official_companion_pins_bound') is True and verifier.get('production_pins_required') is True and
         verifier.get('classpath_count') == 4 and verifier.get('classifier') == 'win' and verifier.get('metadata_mode') == mode and
         verifier.get('native_executions') == 0 and verifier.get('publication_ready') is False,
         'Real production-pin graph binding required; synthetic/model reports cannot enter')'''
assert source.count(old_binding) == 1
source = replace_once(source, old_binding, '    bound_resolution(verifier, mode)')
binding_helper = '''def bound_resolution(verifier, mode):
''' + old_binding + '''


'''
source = replace_once(source, 'def fresh_resolution(consumer, output, mode, start, end, private_repository, invoke):\n', binding_helper + 'def fresh_resolution(consumer, output, mode, start, end, private_repository, invoke):\n')
source = replace_once(source, "    path = consumer / f'build/reports/private-javafx-ordinary-resolution-{mode}.json'", "    path = lt.safe_path(consumer, f'build/reports/private-javafx-ordinary-resolution-{mode}.json')")
old_native = '''        current = packaged.read_json(consumer / 'build/reports/private-javafx-ordinary-resolution-module.json')
        write(output / 'native/resolution.json', current)
        need(graph_signature(current) == signatures['module'], 'Native task must hold the exact independently admitted byte graph')
        invoke('post-native-production-pin-graph-binding',
               [sys.executable, '-B', str(ROOT / DEPENDENCY / 'private_web_resolution.py'), '--repository', str(private_repository),
                '--resolution', str(consumer / 'build/reports/private-javafx-ordinary-resolution-module.json')],
               output / 'native/resolution-verifier.log', 180, producer_environment)
'''
new_native = '''        native_resolution_path = lt.safe_path(consumer, 'build/reports/private-javafx-ordinary-resolution-module.json')
        need(start - 2_000_000_000 <= native_resolution_path.stat().st_mtime_ns <= end + 2_000_000_000,
             'Fresh native-task module graph observation required')
        current = packaged.read_json(native_resolution_path)
        write(output / 'native/resolution.json', current)
        need(current.get('metadata_mode') == 'module' and graph_signature(current) == signatures['module'],
             'Native task must hold the exact independently admitted module byte graph')
        invoke('post-native-production-pin-graph-binding',
               [sys.executable, '-B', str(ROOT / DEPENDENCY / 'private_web_resolution.py'), '--repository', str(private_repository),
                '--resolution', str(native_resolution_path)],
               output / 'native/resolution-verifier.log', 180, producer_environment)
        native_binding = json.loads(read(output / 'native/resolution-verifier.log').decode('utf-8'))
        bound_resolution(native_binding, 'module')
        write(output / 'native/resolution-verification.json', native_binding)
'''
source = replace_once(source, old_native, new_native)
controller_after = source.encode('utf-8')
controller_path.write_bytes(controller_after)
controller_path.chmod(0o600)

doc_path = PROPOSED / 'docs/testing/javafx-ordinary-windows-route.md'
new(PACKET / 'retained/javafx-ordinary-windows-route.before-registered-route.md', regular(doc_path))

recipe = {
    'schema': 'nativecmpkit-javafx-registered-file-exact-derivative658-v1',
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'External source-only derivative of the named existing workflow file, not live registration, Git/native execution, dispatch or adoption',
    'destination': '.github/workflows/javafx-library-candidate.yml',
    'destination_action': 'Exact-predecessor derivative; lead integration only',
    'expected_destination_mode': '0644',
    'preimage': {'sha256': sha(base), 'bytes': len(base), 'retained_path': 'retained/javafx-library-candidate.preimage.yml'},
    'postimage': {'sha256': sha(postimage), 'bytes': len(postimage), 'source_path': str(PROPOSED / '.github/workflows/javafx-library-candidate.yml')},
    'fragments': [
        {'kind': 'replace-exact-once', 'preimage': old_line.decode(), 'postimage': new_line.decode()},
        {'kind': 'append-at-exact-predecessor-EOF', 'preimage': '', 'postimage': job.decode()},
    ],
    'old_public_stop_job': {'sha256': sha(original_job), 'bytes': len(original_job), 'accepted_whitelist': ['linux-arm64', 'macos-arm64', 'macos-x64', 'windows'], 'unchanged': True},
    'only_new_choice': 'windows-ordinary-consumer1',
    'only_new_job': 'ordinary-windows-consumer1',
    'new_job_sha256': sha(job),
    'original_registration_trigger_permissions_concurrency_and_existing_job_unchanged': True,
    'live_workflow_id_path_enabled_and_input_metadata_confirmed': False,
    'standalone_alternative': {'path': 'retained/javafx-ordinary-maven-consumer.standalone-unadopted.yml', 'sha256': sha(standalone), 'bytes': len(standalone), 'canonical_or_adoptable_delivery': False},
    'controller_draft_derivative': {'before_sha256': sha(controller_before), 'after_sha256': sha(controller_after), 'changes': ['Existing workflow pathname only', 'Reuse one passive production-resolution receipt predicate before and after native', 'Confined fresh module-mode post-native graph and independent production pin binding']},
    'ROOT_writes': 0, 'Git_queries': 0, 'target_imports': 0, 'test_or_lint_executions': 0, 'native_or_build_or_dispatch_executions': 0,
}
new(PACKET / 'REGISTERED-WORKFLOW-DERIVATIVE658.json', (json.dumps(recipe, indent=2, sort_keys=True) + '\n').encode())
print(json.dumps({'workflow_preimage': recipe['preimage'], 'workflow_postimage': recipe['postimage'], 'old_public_stop_job': recipe['old_public_stop_job'], 'controller_sha256': sha(controller_after)}, sort_keys=True))
