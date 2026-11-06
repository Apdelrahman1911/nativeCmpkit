"""Important source/collector regressions; not a Gradle or Robolectric execution."""
import contextlib
import io
import os
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / '.github/workflows/android-camera-lifecycle-host.yml'
CLASS = 'com.mohamedrejeb.calf.camerapicker.AndroidCameraLifecycleTest'
METHODS = (
    'nonFinishingRestorationThenCallbackSwapDeliversOneReadableResultToCurrentOwner',
    'nonFinishingRestorationThenCallbackSwapCancelsOnlyOwnedOutputAndSuppressesOldCallbacks',
)


def workflow():
    descriptor = os.open(WORKFLOW, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME)
    try:
        size = os.fstat(descriptor).st_size
        if size > 16384:
            raise ValueError('Bounded owning workflow required')
        return os.read(descriptor, size + 1).decode('utf-8')
    finally:
        os.close(descriptor)


def collector():
    selected = workflow().split(
        '- name: Require exactly the two declared methods in fresh passing JUnit XML', 1
    )[1]
    source = selected.split("python3 -B - <<'PYTHON'\n", 1)[1].split('          PYTHON\n', 1)[0]
    return compile(textwrap.dedent(source), '<owning-new2-collector>', 'exec')


def xml(methods=METHODS, **attributes):
    values = {'tests': '2', 'failures': '0', 'errors': '0', 'skipped': '0'}
    values.update(attributes)
    header = ' '.join(f'{name}="{value}"' for name, value in values.items())
    cases = ''.join(f'<testcase classname="{CLASS}" name="{method}"/>' for method in methods)
    return f'<testsuite {header}>{cases}</testsuite>'.encode()


class AndroidCameraHostJUnitReportBinding740Tests(unittest.TestCase):
    def run_collector(self, payload, filename=None):
        with tempfile.TemporaryDirectory(prefix='nativecmpkit-new2-xml-') as name:
            root = Path(name)
            (root / 'junit').mkdir(mode=0o700)
            if payload is not None:
                (root / 'junit' / (filename or f'TEST-{CLASS}.xml')).write_bytes(payload)
            output = io.StringIO()
            with patch.dict(os.environ, {'HOST_NEW2_ROOT': str(root)}), contextlib.redirect_stdout(output):
                exec(collector(), {'__name__': '__main__'})
            return output.getvalue()

    def test_late_graph_binding_requires_exact_test_and_finalizes_before_execution(self):
        source = workflow()
        self.assertNotIn('gradle.beforeProject', source)
        self.assertEqual(1, source.count('gradle.taskGraph.whenReady { graph ->'))
        self.assertIn("graph.allTasks.find { it.path == ':calf-camera-picker:testAndroidHostTest' }", source)
        self.assertIn('if (!(task instanceof Test))', source)
        for property_name in ('required', 'outputLocation'):
            setter = source.index(f'task.reports.junitXml.{property_name}.set(')
            finalizer = source.index(f'task.reports.junitXml.{property_name}.finalizeValue()')
            self.assertLess(setter, finalizer)
        self.assertIn("new File(System.getenv('HOST_NEW2_ROOT'), 'junit')", source)
        self.assertIn('NATIVECMPKIT_HOST_NEW2_JUNIT task=', source)

    def test_only_two_methods_and_fresh_no_match_failure_contract_remain(self):
        source = workflow()
        selectors = [line.strip() for line in source.splitlines() if line.strip().startswith('--tests ')]
        self.assertEqual(2, len(selectors))
        for method, selector in zip(METHODS, selectors):
            self.assertIn(f"'{CLASS}.{method}'", selector)
        for unchanged in (
            'task.outputs.upToDateWhen { false }',
            "task.outputs.doNotCacheIf('Fresh actual AndroidCameraLifecycle NEW2 execution') { true }",
            'task.filter.setFailOnNoMatchingTests(true)',
            'task.ignoreFailures = false',
            '--max-workers=2 --build-cache',
        ):
            self.assertIn(unchanged, source)

    def test_fresh_exact_two_case_xml_is_accepted_without_device_claim(self):
        self.assertEqual(
            'Verified exactly two fresh Robolectric host regressions; device/native C1 remains unverified.\n',
            self.run_collector(xml()),
        )

    def test_absent_or_foreign_report_never_becomes_empty_success(self):
        for payload, filename in ((None, None), (xml(), 'TEST-Foreign.xml')):
            with self.subTest(filename=filename), self.assertRaises(SystemExit):
                self.run_collector(payload, filename)

    def test_duplicate_foreign_and_wrong_count_cases_are_refused(self):
        for payload in (xml((METHODS[0], METHODS[0])), xml((METHODS[0], 'foreign')), xml(tests='1')):
            with self.subTest(payload=payload), self.assertRaises(SystemExit):
                self.run_collector(payload)

    def test_failure_error_skip_attributes_and_nodes_remain_refusals(self):
        for key in ('failures', 'errors', 'skipped'):
            with self.subTest(attribute=key), self.assertRaises(SystemExit):
                self.run_collector(xml(**{key: '1'}))
        for node in ('failure', 'error', 'skipped'):
            payload = xml().replace(b'</testsuite>', f'<{node}/></testsuite>'.encode())
            with self.subTest(node=node), self.assertRaises(SystemExit):
                self.run_collector(payload)

    def test_dtd_and_entity_declarations_are_never_junit_evidence(self):
        payload = b'<!DOCTYPE testsuite [<!ENTITY injected "data">]>' + xml()
        with self.assertRaisesRegex(ValueError, 'DTD/entity'):
            self.run_collector(payload)

    def test_upload_only_owned_fresh_xml_and_read_only_permissions(self):
        source = workflow()
        self.assertIn('permissions:\n  contents: read\n', source)
        self.assertIn('persist-credentials: false', source)
        self.assertIn('if-no-files-found: error', source)
        self.assertIn('path: ${{ runner.temp }}/android-camera-lifecycle-host-new2/junit/*.xml', source)
        self.assertNotIn('publish', source.lower())
        self.assertNotIn('contents: write', source)

    def test_new09_graph_hook_always_uses_fresh_configuration(self):
        source = workflow()
        self.assertEqual(1, source.count('--no-configuration-cache'))
        self.assertIn('./gradlew --no-daemon --no-configuration-cache --console=plain', source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
