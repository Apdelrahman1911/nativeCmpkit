"""Owning configuration/evidence regressions; not Gradle or browser executions."""
from pathlib import Path
import json
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class WebNodeEnvironmentTests(unittest.TestCase):
    def test_node_pins_cover_each_project_environment_not_only_the_root_setup(self):
        source = (ROOT / "build.gradle.kts").read_text()
        # KGP2.4.20 NpmProject reads its own project's modern environment.
        # A root-only pin installs24 while Wasm's project convention selects26.
        pattern = (r"allprojects\s*\{\s*"
                   r"plugins\.withType<NodeJsPlugin>\s*\{\s*"
                   r'extensions\.configure<NodeJsEnvSpec>\s*\{\s*version\.set\("24\.16\.0"\)\s*\}\s*\}\s*'
                   r"plugins\.withType<WasmNodeJsPlugin>\s*\{\s*"
                   r'extensions\.configure<WasmNodeJsEnvSpec>\s*\{\s*version\.set\("24\.16\.0"\)\s*\}\s*\}\s*\}')
        self.assertRegex(source, pattern)
        self.assertNotIn("plugins.withType<NodeJsRootPlugin>", source)
        self.assertNotIn("WasmNodeJsRootExtension", source)

    def test_runtime_witness_reads_public_project_and_root_specs_not_system_node(self):
        source = (ROOT / "scripts/ci/sample-platforms.init.gradle.kts").read_text()
        for fragment in ("getEXTENSION_NAME", 'getMethod("getExecutable")', 'getMethod("getVersion")',
                         "listOf(rootProject, task.project)", 'ProcessBuilder(executable, "--version")',
                         'observedVersion == "v24.16.0"', "TaskExecutionListener", "state.failure != null",
                         'StandardOpenOption.CREATE_NEW', '"task-build-'):
            self.assertIn(fragment, source)
        self.assertNotIn('ProcessBuilder("node"', source)
        self.assertNotIn("getDeclaredField", source)
        self.assertNotIn("isAccessible", source)
        self.assertNotIn("System.getenv", source)

    def test_task_observer_covers_every_exact_linux_and_apple_build_without_test_selection(self):
        import sample_platform_verification as sample
        source = (ROOT / "scripts/ci/sample-platforms.init.gradle.kts").read_text()
        block = source.split("val buildTasks = when (mode)", 1)[1].split("fun freshReceipt", 1)[0]
        import re
        paths = re.findall(r'"(:sample:[^"\r\n]+)"', block)
        self.assertEqual(list(sample.BUILD_TASKS["linux"] + sample.BUILD_TASKS["apple"]), paths)
        self.assertFalse(any(path.endswith("Test") or "publish" in path for path in paths))

    def _witnesses(self, root):
        import sample_platform_verification as sample
        output = root / "build/ci-verification/sample-platforms-linux"
        output.mkdir(parents=True)
        for target, project, task in (("js", ":sample:web-js", sample.BUILD_TASKS["linux"][2]),
                                     ("wasm", ":sample:web-wasm", sample.BUILD_TASKS["linux"][4])):
            rows = [{"project": name, "extension": "kotlinNodeJsSpec" if target == "js" else "kotlinWasmNodeJsSpec",
                     "configured_version": "24.16.0", "executable": "/synthetic/node-v24.16.0/bin/node",
                     "executable_sha256": "1" * 64, "version_exit_code": 0, "observed_version": "v24.16.0", "passed": True}
                    for name in (":", project)]
            (output / f"node-webpack-{target}.json").write_text(json.dumps({
                "schema_version": 1, "task": task, "observed_epoch_ms": 1,
                "environments": rows, "test_success_inferred": False}))
        return output

    def test_actual_witness_reader_requires_both_equal_pinned_executables_and_fresh_events(self):
        import sample_platform_verification as sample
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._witnesses(root)
            observed = sample.inspect_web_node_environments(root, started_ns=1_000_000, ended_ns=2_000_000)
            self.assertEqual({"js", "wasm"}, set(observed))
            self.assertTrue(all(row["root_and_project_same_pinned_executable"] for row in observed.values()))
            self.assertTrue(all(row["test_success_inferred"] is False for row in observed.values()))

    def test_missing_wrong_version_project_task_pidless_system_node_or_stale_event_is_rejected(self):
        import sample_platform_verification as sample
        for mutation in ("missing", "version", "configured", "project", "task", "system-node", "binary", "exit", "stale"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                output = self._witnesses(root)
                path = output / "node-webpack-wasm.json"
                data = json.loads(path.read_text())
                if mutation == "missing":
                    path.unlink()
                else:
                    row = data["environments"][1]
                    if mutation == "version": row["observed_version"] = "v26.2.0"
                    if mutation == "configured": row["configured_version"] = "26.2.0"
                    if mutation == "project": row["project"] = ":sample:web-js"
                    if mutation == "task": data["task"] = ":foreign:wasmJsBrowserProductionWebpack"
                    if mutation == "system-node": row["executable"] = "/usr/bin/node"
                    if mutation == "binary": row["executable_sha256"] = "2" * 64
                    if mutation == "exit": row["version_exit_code"] = 1
                    if mutation == "stale": data["observed_epoch_ms"] = 0
                    path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    sample.inspect_web_node_environments(root, started_ns=1_000_000, ended_ns=2_000_000)


if __name__ == "__main__":
    unittest.main()
