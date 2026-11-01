"""Owning init-source guards only; not Gradle, TLS, rendering or native outcomes."""
import hashlib
from pathlib import Path
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ci/desktop-security.init.gradle.kts"
ORIGINAL_INNER_SHA256 = "2776dc5587f6b621bd0289742e026f15a6d2ecfc7fb1131a2ed540aeaf6d3014"
OPEN = 'gradle.settingsEvaluated {\n    if (rootProject.name == "NativeCmpKit") {\n'
CLOSE = '    }\n}\n'


def exact_owned_inner(source):
    """Only the exact owning-root envelope may surround the retained listener."""
    if source.count(OPEN) != 1 or not source.endswith(CLOSE):
        raise ValueError("The security observer must be scoped to the exact owning root")
    prefix, body = source.split(OPEN)
    body = body[:-len(CLOSE)]
    if any(line and not line.startswith("        ") for line in body.splitlines()):
        raise ValueError("No unscoped observer actions outside the owning root")
    original = prefix + textwrap.dedent(body)
    if hashlib.sha256(original.encode()).hexdigest() != ORIGINAL_INNER_SHA256:
        raise ValueError("All exact focus, setup and listener criteria must remain intact")
    return original


class DesktopSecurityOwnedRootGuards(unittest.TestCase):
    def test_security_init_is_owned_root_only_and_retains_exact_inner_observation(self):
        original = exact_owned_inner(SCRIPT.read_text())
        self.assertIn('?: error("Security observation requires the exact explicit finite focus")', original)
        self.assertIn('check(maxParallelForks == 1 && forkEvery == 1L)', original)

    def test_wrong_root_unscoped_or_changed_focus_and_worker_criteria_are_refused(self):
        source = SCRIPT.read_text()
        for old, new in (
            ('rootProject.name == "NativeCmpKit"', 'rootProject.name != "NativeCmpKit"'),
            ('rootProject.name == "NativeCmpKit"', 'true'),
            ('forkEvery == 1L', 'forkEvery >= 1L'),
            ('maxParallelForks == 1', 'maxParallelForks >= 1'),
            ('Unknown finite Desktop security observation focus', 'fallback'),
        ):
            with self.subTest(changed_owning_criterion=old), self.assertRaises(ValueError):
                exact_owned_inner(source.replace(old, new, 1))
        with self.assertRaises(ValueError):
            exact_owned_inner(source + 'println("unscoped")\n')


if __name__ == "__main__":
    unittest.main()
