"""NEW finite adaptive routing controls only; synthetic outcomes are not native tests."""
import copy
from pathlib import Path
import re
import tempfile
import unittest

import ios_adaptive_controls_native_focus as adaptive

ROOT = Path(__file__).resolve().parents[2]


class AdaptiveNativeFocusTests(unittest.TestCase):
    def cases(self, focus):
        return [{**item, "status": "passed"} for item in adaptive.identities(focus)]

    def simulator(self, version):
        return {"udid": "00000000-0000-4000-8000-000000000001", "state": "Booted",
                "runtime_version": version,
                "runtime_identifier": "com.apple.CoreSimulator.SimRuntime.iOS-" + version.replace(".", "-")}

    def test_each_focus_selects_only_four_unique_methods_on_its_own_actual_os_branch(self):
        populations = []
        for focus in adaptive.FOCUSES:
            selectors = adaptive.selectors(focus)
            populations.append(set(selectors))
            self.assertEqual(4, len(selectors)); self.assertEqual(4, len(set(selectors)))
            self.assertTrue(all("." + adaptive.branch(focus).replace("plus", "") in value for value in selectors))
            request = adaptive.native_request(focus)
            self.assertTrue(adaptive.validate_request(request, focus))
            self.assertEqual(adaptive.TASK, request[0])
            self.assertEqual(4, request.count("--tests"))
            self.assertEqual(",".join(selectors), adaptive.test_filter(focus))
            scenarios, errors = adaptive.outcomes(self.cases(focus), "Darwin", focus)
            self.assertEqual([], errors); self.assertEqual(4, len(scenarios))
            self.assertTrue(all(item["required_on_host"] and item["disposition"] == "required-executed" for item in scenarios))
            self.assertFalse(any("LiquidGlassControlTest" in value for value in selectors))
        self.assertFalse(populations[0] & populations[1])

    def test_unknown_full_compiler_publish_other_modules_and_mixed_branch_requests_are_refused(self):
        for focus in adaptive.FOCUSES:
            good = adaptive.native_request(focus)
            variants = [good[:1], good[:-2], good + good[-2:], [":calf-ui:compileTestKotlinIosSimulatorArm64"],
                        [":calf-ui:publish"], ["check"], [good[0], "--tests", "*"],
                        [good[0].replace("calf-ui", "calf-share"), *good[1:]]]
            mixed = good.copy(); mixed[2] = adaptive.selectors(adaptive.FOCUSES[1 - adaptive.FOCUSES.index(focus)])[0]
            variants.append(mixed)
            for request in variants:
                with self.subTest(focus=focus, request=request), self.assertRaises(ValueError):
                    adaptive.validate_request(request, focus)
        for function in (adaptive.branch, adaptive.focus_spec, adaptive.identities, adaptive.native_request):
            with self.subTest(function=function.__name__), self.assertRaises(ValueError):
                function("ui-native-adaptive-unreviewed")

    def test_source_admission_retains_both_branch_declarations_and_all_six_owned_inputs(self):
        self.assertTrue(adaptive.validate_sources(ROOT, list(adaptive.SOURCES)))
        for missing in adaptive.SOURCES:
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                adaptive.validate_sources(ROOT, [name for name in adaptive.SOURCES if name != missing])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in adaptive.SOURCES:
                path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / name).read_bytes())
            self.assertTrue(adaptive.validate_sources(root))
            original = (root / adaptive.SLIDER_SOURCE).read_text()
            variants = (original.replace(adaptive.SLIDER_METHODS[0], "foreignMethod", 1),
                        original.replace("@Test", "@Ignore @Test", 1), original + "\n@Test fun extra() {}\n",
                        original.replace("matrix(AdaptiveControlBranch.Pre26)", "matrix(AdaptiveControlBranch.IOS26Plus)", 1),
                        original.replace("AdaptiveSlider(", "CupertinoSlider("))
            for source in variants:
                (root / adaptive.SLIDER_SOURCE).write_text(source)
                with self.subTest(change=source[-40:]), self.assertRaises(ValueError):
                    adaptive.validate_sources(root)
            (root / adaptive.SLIDER_SOURCE).write_text(original)
            path = root / adaptive.BRANCH_SOURCE; path.unlink(); path.symlink_to(ROOT / adaptive.BRANCH_SOURCE)
            with self.assertRaises(ValueError):
                adaptive.validate_sources(root)

    def test_wrong_unavailable_malformed_or_non_ios_runtime_is_never_an_old_os_substitute(self):
        for focus, version in zip(adaptive.FOCUSES, ("18.6", "26.5")):
            self.assertTrue(adaptive.validate_runtime(self.simulator(version), focus))
            wrong = "26.5" if focus == adaptive.FOCUSES[0] else "18.6"
            variants = [None, {}, self.simulator(wrong)]
            for key, value in (("state", "Shutdown"), ("runtime_version", "0.0"), ("runtime_version", True),
                               ("runtime_version", "26.5-invalid"), ("udid", "booted"),
                               ("runtime_identifier", "com.apple.CoreSimulator.SimRuntime.tvOS-26-5")):
                item = self.simulator(version); item[key] = value; variants.append(item)
            for simulator in variants:
                with self.subTest(focus=focus, simulator=simulator), self.assertRaises(ValueError):
                    adaptive.validate_runtime(simulator, focus)

    def test_missing_duplicate_foreign_method_task_target_and_other_branch_xml_never_pass(self):
        for focus in adaptive.FOCUSES:
            expected = self.cases(focus)
            variants = [expected[:-1], [*expected, expected[0]], [expected[0]] * 4,
                        self.cases(adaptive.FOCUSES[1 - adaptive.FOCUSES.index(focus)])]
            for key, value in (("classname", adaptive.SLIDER_CLASS),
                               ("classname", "iosSimulatorArm64Test." + adaptive.SLIDER_CLASS),
                               ("name", "foreign[iosSimulatorArm64]"),
                               ("name", adaptive.SLIDER_METHODS[0] + "[iosArm64]")):
                cases = copy.deepcopy(expected); cases[0][key] = value; variants.append(cases)
            for cases in variants:
                with self.subTest(focus=focus, cases=cases):
                    scenarios, errors = adaptive.outcomes(cases, "Darwin", focus)
                    self.assertTrue(errors)
                    self.assertTrue(all(item["disposition"] == "required-not-passed" for item in scenarios))

    def test_failed_skipped_not_applicable_unknown_status_non_apple_and_malformed_xml_cannot_satisfy_native(self):
        for focus in adaptive.FOCUSES:
            for status in ("failed", "error", "skipped", "not-applicable", "", True):
                cases = self.cases(focus); cases[0]["status"] = status
                with self.subTest(focus=focus, status=status):
                    self.assertTrue(adaptive.outcomes(cases, "Darwin", focus)[1])
            for host in ("Linux", "Windows", "", None):
                with self.subTest(host=host):
                    self.assertTrue(adaptive.outcomes(self.cases(focus), host, focus)[1])
            for cases in (None, {}, [None], [{}]):
                with self.subTest(cases=cases):
                    self.assertTrue(adaptive.outcomes(cases, "Darwin", focus)[1])

    def test_distinct_native_init_matches_exact_sources_methods_and_does_not_expand_compile_only_authority(self):
        init = (ROOT / adaptive.INIT_SCRIPT).read_text()
        sources = re.findall(r'"(calf-ui/src/iosTest/kotlin/[^"\n]+\.kt)"', init)
        self.assertEqual(list(adaptive.SOURCES), sources)
        for focus in adaptive.FOCUSES:
            self.assertIn('"' + focus + '" to listOf(', init)
            for selector in adaptive.selectors(focus):
                self.assertIn('prefix + "' + selector.removeprefix(adaptive.PREFIX) + '"', init)
        for fragment in ('gradle.startParameter.taskNames == applicationRequest',
                         'gradleProperty("' + adaptive.FOCUS_PROPERTY + '")',
                         'System.getProperty("os.name") == "Mac OS X"',
                         'nativecmpkitSimulatorDevice', 'getCommonSources', 'common.setFrom(emptyList<Any>())',
                         'actual.files.map { it.canonicalFile }.toSet() == files.toSet()',
                         '"compiler_executions_attested" to 0', '"apple_links_attested" to 0',
                         '"native_tests_executed" to 0'):
            self.assertIn(fragment, init)
        self.assertNotIn('compilation.inputs.property(', init)
        self.assertNotIn('binaries.test', init); self.assertNotIn('dependsOn(', init)
        compiler = (ROOT / "scripts/ci/adaptive_controls_compile.init.gradle.kts").read_text()
        self.assertNotIn("iosSimulatorArm64ApplicationTest", compiler)


if __name__ == "__main__":
    unittest.main()
