"""Additive review of the eight actual UIImage passes in an overall failed run.

No new native execution, synthesized reports, unknown-cause diagnosis or closure.
The earlier immutable run/archive and its manifests are never overwritten.
"""
from pathlib import Path, PurePosixPath
import datetime as dt
import hashlib
import json
import re
import shutil
import stat
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('/root/projects/nativeCmpKit')
OLD = ROOT / 'docs/development/evidence/github-actions/40507789380'
DEST = ROOT / 'docs/development/evidence/uiimage-partial-scenarios-20261027'
REV = '8ab82a3fa41caad34cd7fb7a2d3722bfc25e3838'
RUN = 40507789380
ARTIFACT = 12737389835
TEST = 'calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/utils/UIImageConversionTest.kt'
BRIDGE = 'calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ImageUtils.kt'
CLASS = 'iosSimulatorArm64ApplicationTest.com.mohamedrejeb.calf.ui.utils.UIImageConversionTest'
REQUIRED = {
    'primaryTransparentAndHalfAlphaPixelsHaveExplicitRgbaChannels': 'Real red/green/blue/transparent/half-alpha channel assertions (tolerance one byte).',
    'halfAlphaCompositesCorrectlyOverBlackAndWhite': 'Real black/white compositing and explicit expected four-channel values.',
    'imageScaleAndDensityRetainLogicalDimensions': '2x/3x UIImage scale, logical24x16 and CGImage pixel dimensions.',
    'nativeVectorPixelsMatchTheRealComposePainter': 'Actual Compose painter/native UIImage pixels,3x/LTR; tolerance3/255 with at most1percent differing pixels.',
    'nativeVectorTintAndRtlMatchTheRealComposePainter': 'Actual Compose painter/native UIImage pixels,2x/RTL, alpha tint and autoMirror; same bounded comparison.',
    'invalidScaleAndDimensionsStopBeforeNativeAllocation': 'Zero/negative/nonfinite/huge inputs rejected; counted native color-space attempts remain zero for invalid bitmap scale.',
    'eachAllocationFailureReleasesAllEarlierNativeObjects': 'Injected single native failure, real preceding allocations, explicit created/released balance.',
    'exceptionAfterSnapshotStillReleasesImageContextAndColorSpace': 'Preserved injected exception and real color-space/context/image release-call balance.',
}
INTERRUPTED = 'returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected'


def sha(payload):
    return hashlib.sha256(payload if isinstance(payload, bytes) else payload.read_bytes()).hexdigest()


def document(payload):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            assert key not in value, 'Duplicate JSON key'
            value[key] = item
        return value
    return json.loads(payload, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


assert not DEST.exists()
run = document((OLD / 'run-final.json').read_bytes())
assert run['id'] == RUN and run['head_sha'] == REV
assert run['repository']['full_name'] == 'Apdelrahman1911/nativeCmpkit'
assert run['status'] == 'completed' and run['conclusion'] == 'failure' and run['run_attempt'] == 1
arts = document((OLD / 'artifacts-final.json').read_bytes())['artifacts']
assert len(arts) == 1
art = arts[0]
raw = OLD / f'raw/{ARTIFACT}.zip'
assert art['id'] == ARTIFACT and art['workflow_run']['head_sha'] == REV and art['workflow_run']['id'] == RUN
assert raw.stat().st_size == art['size_in_bytes'] and 'sha256:' + sha(raw) == art['digest']
bindings = {}
for row in subprocess.check_output(['git', 'ls-tree', '-rz', REV], cwd=ROOT).split(b'\0'):
    if row:
        metadata, name = row.split(b'\t', 1)
        bindings[name.decode()] = metadata.decode().split()


def blob(name):
    mode, kind, oid = bindings[name]
    assert kind == 'blob' and mode in {'100644', '100755'}
    return subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)


with zipfile.ZipFile(raw) as archive:
    infos = archive.infolist()
    assert len(infos) == len({i.filename for i in infos}) <= 64
    assert sum(i.file_size for i in infos) < 64 * 1024**2
    for entry in infos:
        path = PurePosixPath(entry.filename)
        assert not path.is_absolute() and not {'.', '..'} & set(path.parts) and '\\' not in entry.filename
        assert not entry.is_dir() and not entry.flag_bits & 1 and entry.filename.endswith(('.xml', '.json'))
        assert entry.file_size <= 8 * 1024**2 and stat.S_IFMT(entry.external_attr >> 16) in {0, stat.S_IFREG}
    prefix = 'build/ci-verification/ios-iphone/'
    inputs = document(archive.read(prefix + 'inputs-before.json'))
    assert inputs == document(archive.read(prefix + 'inputs-after.json')) and len(inputs) == 720
    for name, digest in inputs.items():
        assert sha(blob(name)) == digest, name
    receipt = document(archive.read(prefix + 'receipt.json'))
    assert receipt['source_revision'] == receipt['source_revision_after'] == REV and receipt['changed_inputs'] == []
    assert receipt['source_tree_dirty'] is False and receipt['execution']['exit_code'] == 1
    assert receipt['task_execution_markers'] == {':calf-ui:iosSimulatorArm64ApplicationTest': 1}
    assert receipt['totals']['passed'] == 120 and receipt['totals']['failures'] == 1 and receipt['totals']['skipped'] == 0
    xml_names = [i.filename for i in infos if i.filename.endswith('UIImageConversionTest.xml')]
    assert len(xml_names) == 1
    report = next(r for r in receipt['modules'][0]['reports'] if r['path'] == xml_names[0])
    payload = archive.read(xml_names[0])
    assert sha(payload) == report['sha256'] and b'<!DOCTYPE' not in payload and b'<!ENTITY' not in payload
    suite = ET.fromstring(payload)
    assert suite.tag == 'testsuite' and suite.attrib['name'] == CLASS
    assert {k: int(suite.attrib[k]) for k in ('tests', 'failures', 'errors', 'skipped')} == {'tests': 9, 'failures': 1, 'errors': 0, 'skipped': 0}
    cases = []
    for case in suite.findall('testcase'):
        assert case.attrib['classname'] == CLASS
        match = re.fullmatch(r'([A-Za-z0-9_]+)\[iosSimulatorArm64\]', case.attrib['name'])
        assert match
        elements = [element for element in case if element.tag in {'failure', 'error', 'skipped'}]
        assert len(elements) <= 1
        status = 'failed' if elements and elements[0].tag == 'failure' else 'error' if elements and elements[0].tag == 'error' else 'skipped' if elements else 'passed'
        row = {'classname': CLASS, 'name': case.attrib['name'], 'method': match[1], 'status': status, 'seconds': case.attrib['time']}
        if elements:
            assert elements[0].attrib == {'message': 'Unknown', 'type': 'Unknown'} and not (elements[0].text or '').strip()
            row['failure'] = {'type': 'Unknown', 'message': 'Unknown', 'assertion_or_crash_stack_inspected': False}
        cases.append(row)
    assert len(cases) == len({c['method'] for c in cases}) == 9
    assert {c['method'] for c in cases if c['status'] == 'passed'} == REQUIRED.keys()
    assert {c['method'] for c in cases if c['status'] != 'passed'} == {INTERRUPTED}
    app_paths = [i.filename for i in infos if '/native-ui-application/' in i.filename and i.filename.endswith('/receipt.json')]
    assert len(app_paths) == 1
    app = document(archive.read(app_paths[0]))
    assert app['transport_passed'] is False and app['application_protocol'] is None and app['error']['phase'] == 'launch-and-real-test-transport'
    assert 'runtime_after' not in app
    assert all(app['cleanup'][k] is True for k in ('owned_app_identity_reverified', 'owned_app_stopped_verified', 'owned_app_absence_verified', 'owned_local_bundle_removed'))

original = blob(TEST)
current = (ROOT / TEST).read_bytes()
reversed_source = current.decode().replace('import platform.Foundation.NSThread\n', '')
reversed_source = re.sub(r'^        // Finite, exact-case transport diagnostics only\. Keep real conversions,\n        // all twenty synchronous main-thread collections and pixel assertions\.\n', '', reversed_source, flags=re.M)
reversed_source = re.sub(r'^\s*println\("NATIVECMPKIT_UIKIT_IMAGE_LIFETIME[^\n]*\n', '', reversed_source, flags=re.M)
reversed_source = reversed_source.replace('repeat(20) { iteration ->\n            val ordinal = iteration + 1\n', 'repeat(20) {\n')
assert reversed_source.encode() == original, 'Exact reverse instrumentation must reproduce the failed immutable test'
assert (ROOT / BRIDGE).read_bytes() == blob(BRIDGE)
source = original.decode()
for method in REQUIRED:
    assert source.count('@Test fun ' + method + '(') == 1
for statement in ['bridge.assertBalanced()', 'assertContentEquals(expected, image.drawRgba())', 'GC.collect()',
                  'repeat(20)', 'super.createColorSpace()', 'super.createContext(', 'super.releaseContext(',
                  'super.releaseImage(', 'super.releaseColorSpace(']:
    assert statement in source, statement

DEST.mkdir()
shutil.copyfile(Path(__file__), DEST / 'lead-review.py')
review = {
    'reviewed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'source_revision': REV, 'run_id': RUN, 'url': run['html_url'], 'run_conclusion': 'failure',
    'evidence_integrity_passed': True, 'artifact_id': ARTIFACT, 'artifact_path': raw.relative_to(ROOT).as_posix(),
    'artifact_sha256': sha(raw), 'all_720_recorded_inputs_bound_to_exact_Git_blobs': True,
    'report_path': xml_names[0], 'report_sha256': sha(payload),
    'reported_native_cases': 9, 'passed_native_cases': 8, 'interrupted_native_cases': 1, 'skipped_cases': 0,
    'testcases': cases, 'source_assertion_scopes': REQUIRED,
    'test_source_sha256_at_runtime': sha(original), 'test_source_sha256_current': sha(current),
    'exact_reverse_diagnostics_reproduces_failed_immutable_test': True,
    'production_bridge_sha256': sha(blob(BRIDGE)), 'production_bridge_unchanged': True,
    'application_transport_passed': False, 'runner_completion_and_post_runtime_missing': True,
    'exact_owned_application_cleanup_passed_separately': True,
    'new_native_executions_by_this_review': 0, 'issues_closed': 0,
    'release_readiness_certified': False, 'packages_published': False,
    'scope': 'Eight individually passing real UIImage methods in an overall failed genuine iPhone26.5 application run. Release-call counters are not a native leak profile. Vector comparisons retain a tolerance and finite fixture, not universal visual equivalence. No native ASan/Instruments/device/minimum-platform/GC-lifetime or full-transport success is implied. Unknown process interruption has no inspected assertion, crash report or established production root cause. No new Apple execution or issue closure.',
    'review_script_sha256': sha(Path(__file__)),
}
with (DEST / 'lead-review.json').open('x') as stream:
    json.dump(review, stream, indent=2, sort_keys=True)
    stream.write('\n')
(DEST / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(DEST.iterdir()) if p.is_file()))
print(json.dumps({k: review[k] for k in ('evidence_integrity_passed', 'passed_native_cases', 'interrupted_native_cases', 'application_transport_passed', 'new_native_executions_by_this_review')}, indent=2))
