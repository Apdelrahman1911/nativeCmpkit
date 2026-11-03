# SPDX-License-Identifier: Apache-2.0
"""Task-request source controls, not native lifecycle or Gradle executions."""
from pathlib import Path
import re
import unittest

import library_tests as library

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = "scripts/ci/ios_modal_focused_compile.init.gradle.kts"
TASK = ":calf-ui:iosSimulatorArm64ApplicationTest"
COMPILER = ":calf-ui:compileTestKotlinIosSimulatorArm64"


def requests(source):
    match = re.search(
        r'val applicationRequest = listOf\("([^"\n]+)"\) \+ listOf\(\n(.*?)\n'
        r'    \)\.flatMap \{ method -> listOf\("--tests", "([^"\n]+)\.\$method"\) \}',
        source, re.S,
    )
    if match is None:
        raise ValueError("Exact finite Kotlin request declaration is required")
    task, body, classname = match.groups()
    methods = tuple(re.findall(r'^        "([A-Za-z][A-Za-z0-9]+)",$', body, re.M))
    if body != "\n".join('        "' + method + '",' for method in methods):
        raise ValueError("Unreviewed native request declaration")
    return [task] + [argument for method in methods for argument in ("--tests", classname + "." + method)]


class IosModalFocusedRequestsTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / SCRIPT).read_text()
        self.request = requests(self.source)

    def test_actual_filtered_request_matches_only_the_three_authored_methods(self):
        expected = [TASK] + [argument for method in library.IOS_MODAL_LIFECYCLE_METHODS
                            for argument in ("--tests", library.IOS_MODAL_LIFECYCLE_CLASS + "." + method)]
        self.assertEqual(expected, self.request)
        self.assertEqual(7, len(self.request))
        self.assertIn("        applicationRequest,\n", self.source)
        self.assertIn("check(gradle.startParameter.taskNames in permittedTasks)", self.source)

    def test_extra_duplicate_wildcard_reordered_missing_and_other_tasks_are_not_admitted(self):
        admitted = {(COMPILER,), (TASK,), tuple(self.request)}
        wrong = [self.request + ["--tests", "*"], self.request[:-2],
                 self.request + self.request[-2:], self.request[:1] + self.request[3:] + self.request[1:3],
                 [TASK, "--tests", library.IOS_MODAL_LIFECYCLE_CLASS + ".*"],
                 [":calf-ui:publish"], [COMPILER, "--tests", "*"],
                 self.request + [":calf-ui:desktopTest"], ["iosSimulatorArm64ApplicationTest"],
                 self.request[:-1] + ["foreign.Test.case"]]
        for candidate in wrong:
            with self.subTest(candidate=candidate):
                self.assertNotIn(tuple(candidate), admitted)

    def test_standalone_compilation_remains_a_separate_exact_request(self):
        self.assertIn('listOf("' + COMPILER + '")', self.source)
        self.assertIn('listOf("' + TASK + '")', self.source)
        self.assertNotIn(COMPILER, self.request)

    def test_included_builds_return_before_any_task_or_source_admission(self):
        scoped = self.source.index('rootProject.findProject(":calf-ui") ?: return@projectsEvaluated')
        self.assertLess(scoped, self.source.index("val applicationRequest"))
        self.assertLess(scoped, self.source.index("check(gradle.startParameter.taskNames"))

    def test_gate_remains_before_exact_source_admission_without_argument_normalization(self):
        self.assertLess(self.source.index("check(gradle.startParameter.taskNames in permittedTasks)"),
                        self.source.index("val paths = listOf("))
        for forbidden in ("taskNames.filter", "taskNames.toSet", "taskNames.distinct", "ignoreFailures", "setTaskNames"):
            self.assertNotIn(forbidden, self.source)

    def test_live_gradle_command_delivers_the_exact_admitted_request(self):
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_LIFECYCLE_FOCUS)
        command = library.gradle_command("ios", plan, "726D52AF-426A-408A-974D-CA8B9BE8A479")
        self.assertEqual(self.request, command[command.index(TASK):])
        self.assertEqual(1, command.count(SCRIPT))


if __name__ == "__main__":
    unittest.main()
