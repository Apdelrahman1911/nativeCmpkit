"""Changed Windows checkout/recovery controls only; ZERO native/runtime builds."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class NativeLockWindowsWorkflowTest(unittest.TestCase):
    def text(self): return (ROOT / ".github/workflows/build-native-libs.yml").read_text()

    def test_both_native_profiles_set_exact_bytes_and_longpaths_before_checkout(self):
        text = self.text()
        for name, end in (("native-lock-reproducibility", "native-lock-windows-source"),
                          ("native-lock-windows-source", "picker-jni-macos-domain")):
            block = text.split("\n  " + name + ":\n", 1)[1].split("\n  " + end + ":\n", 1)[0]
            self.assertLess(block.index("    env:\n"), block.index("uses: actions/checkout"))
            for value in ("GIT_CONFIG_COUNT: '2'", "GIT_CONFIG_KEY_0: core.autocrlf",
                          "GIT_CONFIG_VALUE_0: 'false'", "GIT_CONFIG_KEY_1: core.longpaths",
                          "GIT_CONFIG_VALUE_1: 'true'", "persist-credentials: false"):
                self.assertIn(value, block)
            self.assertNotIn("git config --global", block)

    def test_recovery_selects_only_actual_windows_with_original_controller_and_reports(self):
        text = self.text()
        block = text.split("\n  native-lock-windows-source:\n", 1)[1].split("\n  picker-jni-macos-domain:\n", 1)[0]
        for value in ("inputs.profile == 'native-lock-windows-source'", "needs: native-lock-tooling",
                      "runs-on: windows-2025", "toolchain: '1.98.0'", "shell: bash",
                      "python scripts/ci/native_lock_reproducibility.py --platform windows-x64",
                      "if: always()", "*.json"):
            self.assertIn(value, block)
        for forbidden in ("matrix:", "macos-", "ubuntu-", "setup-java", "gradlew", "cargo test",
                          "actions/cache", ".private.log", "packages: write", "contents: write"):
            self.assertNotIn(forbidden, block)
        self.assertIn("permissions:\n  contents: read", text)

    def test_changed_tooling_guards_do_not_replay_accepted_controller_or_host_suites(self):
        text = self.text()
        block = text.split("\n  native-lock-tooling:\n", 1)[1].split("\n  native-lock-reproducibility:\n", 1)[0]
        old = block.split("- name: Important cache/source/refusal/controller tests", 1)[1].split("- name: Changed checkout", 1)[0]
        self.assertIn("if: inputs.profile == 'native-lock-reproducibility'", old)
        changed = block.split("- name: Changed checkout", 1)[1]
        self.assertIn("if: inputs.profile == 'native-lock-windows-source'", changed)
        self.assertIn("test_native_lock_windows_workflow.py", changed)
        self.assertNotIn("test_native_lock_reproducibility.py", changed)


if __name__ == "__main__": unittest.main()
