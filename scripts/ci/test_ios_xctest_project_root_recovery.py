# SPDX-License-Identifier: Apache-2.0
"""NEW common-path control only; simulated compiler refusal, ZERO Swift/native."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock,patch

import hashlib
import ios_modal_worker_source_projection as history
import native_ui_input as native
import native_ui_input_startup as startup
from test_native_ui_input import TOKEN,AUTH,DEVICE,BUNDLE,HASH,no_native

ROOT = Path(__file__).resolve().parents[2]

class XCTestProjectRootRecoveryControls(unittest.TestCase):
    def test_additive_one_line_inverse_keeps_the_six23_original_bindings_and_current_admission_strict(self):
        binding = history.XCTEST_PROJECT_SCOPE
        self.assertEqual(native.SOURCE, binding['source'])
        current = (ROOT / native.SOURCE).read_bytes()
        previous = history.source_before_xctest_project_scope(native.SOURCE, current, current=True)
        self.assertEqual(binding['before_sha256'], hashlib.sha256(previous).hexdigest())
        self.assertEqual(binding['after_sha256'], hashlib.sha256(current).hexdigest())
        self.assertEqual(current, previous.replace(binding['before'].encode(), binding['after'].encode(), 1))
        self.assertEqual(previous, history.source_before_xctest_project_scope(native.SOURCE, previous))
        original = history.source_before_modal_worker(native.SOURCE, current)
        self.assertEqual(history._bindings()[native.SOURCE]['before_sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(original, history.source_before_modal_worker(native.SOURCE, original))
        self.assertEqual(original, history.current_source_before_modal_worker(native.SOURCE, current))
        self.assertEqual(6, len(history._bindings()))
        self.assertEqual(23, sum(len(b['fragments']) for b in history._bindings().values()))
        self.assertEqual('8a1f2c4b0f418b9aab96f9d3c8f615acff5efce31fe457886204559fd2448d48',
                         hashlib.sha256(history.SPEC_PATH.read_bytes()).hexdigest())
        for payload in (previous, original, current + b'\n', current[:-1], b'', b'foreign', None, bytearray(current)):
            with self.subTest(kind=type(payload).__name__), self.assertRaises(ValueError):
                history.current_source_before_modal_worker(native.SOURCE, payload)

    def test_both_startup_routes_use_their_own_prepared_project_and_preserve_compiler_refusal(self):
        for standalone in (False,True):
            with self.subTest(standalone=standalone), tempfile.TemporaryDirectory(prefix='explicitly-synthetic-xctest-project-root-') as folder:
                root=Path(folder)
                for relative in (native.SOURCE,native.SWIFT,native.PROJECT,native.SCHEME,native.NATIVE):
                    target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target)
                with patch.object(native.secrets,'token_hex',return_value=AUTH):
                    driver=(startup.StartupDriver(root,DEVICE,BUNDLE,TOKEN,no_native) if standalone else
                            native.InputDriver(root,DEVICE,BUNDLE,TOKEN,no_native,HASH,HASH))
                driver._prepare_project()
                compiler=Mock();compiler.wait.return_value=1;compiler.poll.return_value=1
                try:
                    with patch.object(native.subprocess,'Popen',return_value=compiler) as popen:
                        with self.assertRaisesRegex(RuntimeError,'runner compilation failed'):
                            driver._start_runner()
                        popen.assert_called_once()
                        args=popen.call_args.args[0]
                        self.assertEqual(str(driver.scratch/'project/NativeCmpKitInput.xcodeproj'),args[args.index('-project')+1])
                        self.assertEqual('build-for-testing',args[1])
                        self.assertEqual([compiler],driver.processes)
                        self.assertEqual(1,driver.receipt['build']['exit_code'])
                        self.assertNotIn('runner_ready',driver.receipt)
                        self.assertFalse(driver.receipt['verified'])
                finally:
                    if driver.log is not None and not driver.log.closed:
                        driver.log.write(b'explicitly synthetic refused compiler boundary\n');driver.log.flush()
                    driver.close()
                    self.assertFalse(driver.receipt['verified'])
