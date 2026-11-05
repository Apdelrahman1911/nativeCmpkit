"""One NEW essential registered-profile source control; no native/test replay."""
import hashlib
import json
from pathlib import Path
import unittest

import picker_awt_generation as r
import picker_awt_preparation as p

BASE_CHOICES = 'options: [all, picker-jni-macos-domain, native-lock-reproducibility, native-lock-windows-source, picker-jni-actual-jvm2, picker-awt-generation]'
CURRENT_CHOICES = 'options: [all, picker-jni-macos-domain, native-lock-reproducibility, native-lock-windows-source, picker-jni-actual-jvm2, picker-awt-generation, picker-awt-preparation]'
ADDED_JOB = "\n  picker-awt-preparation:\n    if: github.repository == 'Apdelrahman1911/nativeCmpkit' && github.event_name == 'workflow_dispatch' && inputs.profile == 'picker-awt-preparation'\n    runs-on: macos-26\n    timeout-minutes: 15\n    defaults:\n      run:\n        shell: bash\n    steps:\n      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803\n        with:\n          persist-credentials: false\n      - uses: dtolnay/rust-toolchain@b725eda525362e7cf34af9a7243cac1e3f01a7ec\n        with:\n          toolchain: '1.98.0'\n      - uses: actions/setup-java@b6effb05e454b25005698d916606bdc6ffcbf961\n        with:\n          distribution: temurin\n          java-version: '17'\n          verify-signature: true\n          overwrite-settings: false\n      - name: Standard owned preparation once, zero inventory or native tests or accepted controls\n        run: python3 -B scripts/ci/picker_awt_preparation.py --output build/ci-verification/picker-awt-preparation\n      - name: Preserve only five allowlisted JSON receipts, including failed preparation observations\n        if: always()\n        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9\n        with:\n          name: picker-awt-preparation-evidence\n          retention-days: 7\n          if-no-files-found: error\n          path: |\n            build/ci-verification/picker-awt-preparation/receipt.json\n            build/ci-verification/picker-awt-preparation/inputs-before.json\n            build/ci-verification/picker-awt-preparation/inputs-after.json\n            build/ci-verification/picker-awt-preparation/runtime-before.json\n            build/ci-verification/picker-awt-preparation/runtime-after.json\n"
WORKFLOW_SHA = '26edb07e55079f72f8637b3d69f56ab4b202df2baa143b1d8a133c3cc187a838'


class PickerAwtPreparationRegistration(unittest.TestCase):
    def test_registered_manual_profile_is_additive_readonly_native0_with_original_jobs_and_five_JSON(self):
        source = (r.library.ROOT / r.shared.WORKFLOW).read_bytes()
        self.assertEqual(WORKFLOW_SHA, hashlib.sha256(source).hexdigest())
        workflow = source.decode("utf-8")
        self.assertEqual(1, workflow.count(CURRENT_CHOICES))
        self.assertTrue(workflow.endswith(ADDED_JOB))
        inverse = workflow[:-len(ADDED_JOB)].replace(CURRENT_CHOICES, BASE_CHOICES, 1)
        self.assertEqual("928effd23198df7be507ee9d64525f734518381228b4928d767a0f6a200e524f", hashlib.sha256(inverse.encode()).hexdigest())
        # The sole registration change is one option and one appended job. This
        # proves every preexisting job/action/upload/runtime body is unchanged.
        self.assertEqual(".github/workflows/build-native-libs.yml", r.shared.WORKFLOW)
        self.assertEqual(1, workflow.count("\n  picker-awt-preparation:"))
        job = workflow.split("\n  picker-awt-preparation:", 1)[1]
        for required in ("github.repository == 'Apdelrahman1911/nativeCmpkit'", "github.event_name == 'workflow_dispatch'",
                         "inputs.profile == 'picker-awt-preparation'", "runs-on: macos-26", "timeout-minutes: 15",
                         "persist-credentials: false", "toolchain: '1.98.0'", "distribution: temurin", "java-version: '17'",
                         "verify-signature: true", "overwrite-settings: false", "if: always()", "retention-days: 7",
                         "python3 -B scripts/ci/picker_awt_preparation.py --output build/ci-verification/picker-awt-preparation"):
            self.assertIn(required, job)
        self.assertIn("permissions:\n  contents: read", workflow)
        uploads = job.split("          path: |\n", 1)[1].splitlines()
        self.assertEqual(["            build/ci-verification/picker-awt-preparation/" + name for name in r.PUBLIC_FILES], uploads)
        for forbidden in ("unittest", "test_picker_", "matrix:", "gradlew", "cargo test", "--focus", "*.json", "*.log", "**",
                          "private/", ".dylib", "target/", "printenv", "set -x", "write-all", "packages: write", "actions: write"):
            self.assertNotIn(forbidden, job)
        self.assertEqual(600, r.shared.NATIVE_BUDGET_SECONDS)
        self.assertEqual((":calf-file-picker:desktopProcessResources", ":calf-file-picker:writeNativeTestRuntimeClasspath",
                          ":calf-file-picker:verifyNativeResources"), r.PREPARE_TASKS)
        pinned = {
            "scripts/ci/picker_awt_generation.py": "de9267e000a83a32c8a2c4cd69e231d8d2dd7d625b8f4b77e173852cd5e410a5",
            "scripts/ci/picker_awt_preparation.py": "131773363c830a4f2c807c4ed4e3d14ce6fb88e3ad5b101d13cbeb405632e9d9",
            "scripts/ci/picker_awt_prepare_failure.py": "86cab04a4d41d6c3be8b39e2bb26547e372d1b031bf5d0c8dbb64a4b119d0e7f",
            ".github/workflows/picker-awt-preparation.yml": "236205c4b61b1f36fd86f81eb5f11b037bc3187b714f3ef2806aed8e58e78344",
        }
        for relative, expected in pinned.items():
            self.assertEqual(expected, hashlib.sha256((r.library.ROOT / relative).read_bytes()).hexdigest())
        # Standalone proposal stays unchanged/unregistered; actual request uses
        # the registered profile above, not a default-branch/main modification.
        self.assertEqual(".github/workflows/picker-awt-preparation.yml", p.WORKFLOW)
        self.assertEqual(1, ADDED_JOB.count("scripts/ci/picker_awt_preparation.py"))


if __name__ == "__main__":
    unittest.main()
