"""Twelve NEW-only source/inverse controls for actual Wasm framework wiring.

No old test module/model is imported or executed, no adapter is manufactured and
no framework/native/Wasm/browser callback runs here. Genuine emitted registration
is a separate explicit fresh-process probe against held real emitted assets.
These source checks cannot certify that integration, native functionality or an
issue closure. The old models remain historical exact-source projections only.
"""
import ast
import hashlib
from pathlib import Path
import unittest

import share_clipboard_wasm_framework_recovery as framework

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = "calf-share/karma.config.d/nativecmpkit-clipboard-fixture.js"
NATIVE_PINS = {
    "calf-share/src/webTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardEnvironmentAcceptanceTest.kt":
        "10bf06a15f4d840779aa494122d42c24ed6bbd76ec6926d72eedf982c7cebc60",
    "calf-share/src/jsTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardNativeHarness.js.kt":
        "9d33398d366466f41a3d4a46198a7c8e02e3c23fbfd73af1216aa6b0915ebc05",
    "calf-share/src/wasmJsTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardNativeHarness.wasmJs.kt":
        "b24a367d8c3e45e896559f1ce7a44d627c8825023ebfd9e9f66c6eb34c64ba59",
}
FRAMEWORK_NAMES = ("Mocha", "mocha", "before", "after", "beforeEach", "afterEach", "run",
                   "describe", "context", "xdescribe", "xcontext", "it", "specify", "xit", "xspecify")
SELECTION = "if (typeof selected !== 'function' || selections !== 1 || invocations !== 0) throw new Error('Exact emitted native test method is missing/reused');"
PROBE = "scripts/ci/share_clipboard_wasm_emitted_registration.cjs"
PROBE_SHA256 = "e850e6837d373d62e8b726c63bb223e0f45a64525ac075f1e525390b9ed816eb"


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def span(source, start, end):
    if source.count(start) != 1:
        raise ValueError("Exactly one held source function required")
    left = source.index(start)
    right = source.index(end, left + len(start))
    return source[left:right].rstrip()


def assigned_literal(source, name):
    tree = ast.parse(source)
    found = [node.value for node in tree.body if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    if len(found) != 1:
        raise ValueError("Exactly one source literal required")
    return ast.literal_eval(found[0])


class ShareClipboardWasmFrameworkRecoveryTests(unittest.TestCase):
    def sources(self):
        source = (ROOT / FIXTURE).read_text()
        self.assertEqual(framework.QUALIFIED_FRAMEWORK_FIXTURE_SHA256, digest(source))
        diagnostic = framework.diagnostic_fixture_from_framework(source)
        self.assertEqual(framework.DIAGNOSTIC_FIXTURE_SHA256, digest(diagnostic))
        return source, diagnostic

    def test_new_eight_fragments_inverse_commutes_without_executing_a_framework_or_old_model(self):
        source, original = self.sources()
        self.assertEqual(8, len(framework.FRAMEWORK_DELTAS))
        def apply(text, deltas):
            for before, after in deltas:
                self.assertEqual(1, text.count(before))
                text = text.replace(before, after, 1)
            return text
        self.assertEqual(source, apply(original, framework.FRAMEWORK_DELTAS))
        self.assertEqual(source, apply(original, reversed(framework.FRAMEWORK_DELTAS)))
        for left in range(8):
            for right in range(left + 1, 8):
                a, b = framework.FRAMEWORK_DELTAS[left], framework.FRAMEWORK_DELTAS[right]
                self.assertEqual(apply(original, (a, b)), apply(original, (b, a)))
        self.assertEqual(original, framework.diagnostic_fixture_from_framework(source))

    def test_new_inverse_refuses_each_partial_repair_and_all_nonqualified_native_drift(self):
        source, old = self.sources()
        cases = [old, None, source.encode(), source + "\n"]
        cases += [source.replace(after, before, 1) for before, after in framework.FRAMEWORK_DELTAS]
        cases += [source.replace(before, after, 1) for before, after in (
            ("selections !== 1", "selections < 1"),
            ("invocations !== 0", "invocations < 0"),
            ("await selected();", "selected();"),
            ("frameworkTests.length !== 0", "frameworkTests.length < 0"),
            ("frameworkSuites.length !== 0", "frameworkSuites.length < 0"),
            ("framework.setup('bdd')", "framework.setup('tdd')"),
            ("if (restore() !== true", "if (restore() !== false"),
            ("delete window[name];", "window[name] = undefined;"),
            ("if (name in window)", "if (false)"),
            ("frameworkNames.some(name => name in window)", "false"),
            ("loaded !== 1", "loaded < 1"),
        )]
        for case in cases:
            with self.subTest(category=type(case).__name__):
                with self.assertRaises(ValueError):
                    framework.diagnostic_fixture_from_framework(case)

    def test_accepted_JS_selector_boot_guard_and_loader_bytes_remain_identical(self):
        source, old = self.sources()
        for start, end in (("  function childBootstrap(", "  const isWasmPackage ="),
                           ("  function childLoad(", "  function wasmChildBootstrap(")):
            self.assertEqual(span(source, start, end), span(old, start, end))
        self.assertEqual("46db87a759ac882a71d0611b7ede5734ff0e8c98c0d4e09dc0299041fbf544ca",
                         digest(span(source, "  function childBootstrap(", "  const isWasmPackage =")))
        self.assertEqual("bab783bb4505bca73a49e02f2ebd5ab547de846c300a2760f0f990b97bbfd013",
                         digest(span(source, "  function childLoad(", "  function wasmChildBootstrap(")))
        self.assertEqual(1, source.count(SELECTION))
        child = span(source, "  function childBootstrap(", "  const isWasmPackage =")
        self.assertLess(child.index(SELECTION), child.index("invocations++;"))
        self.assertLess(child.index("invocations++;"), child.index("await selected();"))
        self.assertIn("No callback for any accepted test is ever invoked here.", child)

    def test_real_Mocha_resolution_uses_owning_plugin_context_and_exact_served_asset(self):
        source, _ = self.sources()
        selection = span(source, "  const isWasmPackage =", "  function childLoad(")
        for phrase in (
            "require('node:module').createRequire(require.resolve('karma-mocha'))",
            "path.join(path.dirname(frameworkRequire.resolve('mocha')), 'mocha.js')",
            "chosen[2].originalPath !== mochaPath", "chosen[2].path !== mochaPath",
            "served.originalPath === file.originalPath && served.path === file.path && served.sha === file.sha",
            "!/^[a-f0-9]{40}$/.test(file.sha)", "chosen.length !== 4",
            "chosen[3].originalPath !== loadPath", "chosen[3].path !== entryPath",
        ):
            self.assertIn(phrase, selection)
        self.assertNotIn("kotlin-test-karma-runner", selection)
        self.assertNotIn("adapter.js", selection)
        self.assertNotIn("require('mocha')", selection)

    def test_Wasm_asset_order_has_one_actual_framework_and_one_actual_KGP_entry(self):
        source, _ = self.sources()
        selection = span(source, "  const isWasmPackage =", "  function childLoad(")
        for phrase in (
            "path.basename(chosen[0].originalPath) !== 'runtime.js'",
            "path.basename(chosen[1].originalPath) !== 'commons.js'",
            "...(index === 2 ? { wasmFramework: true } : {})",
            "...(index === 3 ? { wasmLoader: true } : {})",
        ):
            self.assertIn(phrase, selection)
        wasm = span(source, "  function wasmChildBootstrap(", "  const reply =")
        self.assertIn("scripts.length !== 4", wasm)
        self.assertIn("(entry.wasmFramework === true) !== (index === 2)", wasm)
        self.assertIn("(entry.wasmLoader === true) !== (index === 3)", wasm)
        self.assertEqual(1, wasm.count("for (const entry of scripts)"))
        self.assertEqual(1, wasm.count("document.head.appendChild(script)"))
        self.assertLess(wasm.index("document.head.appendChild(script)"), wasm.index("initializeFramework();"))

    def test_preexisting_framework_or_selector_refuses_before_any_emitted_script_load(self):
        source, _ = self.sources()
        wasm = span(source, "  function wasmChildBootstrap(", "  const reply =")
        names_start = wasm.index("const frameworkNames = ") + len("const frameworkNames = ")
        names_end = wasm.index(";", names_start)
        self.assertEqual(list(FRAMEWORK_NAMES), ast.literal_eval(wasm[names_start:names_end]))
        for phrase in (
            "frameworkNames.some(name => name in window)", "'__karma__' in window",
            "'wasmSelectionDiagnostic' in h", "typeof transformer.value !== 'function'",
            "frameworkNames.slice(2).some(name => name in window)",
        ):
            self.assertLess(wasm.index(phrase), wasm.index("load(); // Exactly one owned sequence"))
        refusal = wasm[wasm.index("    } catch (_) {"):]
        self.assertNotIn("boot();", refusal)
        self.assertIn("throw new Error('Owning Wasm loader setup refused')", refusal)

    def test_real_BDD_initialization_and_original_selector_cannot_queue_framework_tests(self):
        source, _ = self.sources()
        wasm = span(source, "  function wasmChildBootstrap(", "  const reply =")
        self.assertEqual(1, wasm.count("framework.setup('bdd')"))
        for phrase in (
            "window.mocha instanceof window.Mocha", "framework.setup('bdd') !== framework",
            "typeof window.describe !== 'function'", "typeof window.it !== 'function'",
            "frameworkSuite.tests !== frameworkTests", "frameworkSuite.suites !== frameworkSuites",
            "frameworkTests.length !== 0", "frameworkSuites.length !== 0",
            "window.kotlinTest !== namespace", "'adapterTransformer'), transformer)",
        ):
            self.assertIn(phrase, wasm)
        for forbidden in ("window.describe =", "window.it =", "mocha.run(", "framework.run(",
                          "adapterTransformer()", "NEW_ONLY", "startUnitTests()"):
            self.assertNotIn(forbidden, wasm)

    def test_loaded_handshake_framework_identity_and_native_boot_order_remain_strict(self):
        source, _ = self.sources()
        wasm = span(source, "  function wasmChildBootstrap(", "  const reply =")
        for phrase in (
            "loaded() { if (++loaded !== 1) failed = true; release(); }",
            "error() { failed = true; release(); }", "failed || loaded !== 1 || !loadFinished",
            "window.__karma__ !== karma", "window.__nativecmpkitClipboardNative !== h",
            "frameworkDescriptors.every", "sameDescriptor(Object.getOwnPropertyDescriptor",
        ):
            self.assertIn(phrase, wasm)
        owned_boot = wasm[wasm.index("const ownedBoot ="):wasm.index("const ownedRestore =")]
        self.assertLess(owned_boot.index("await ready;"), owned_boot.index("assertReady();"))
        self.assertLess(owned_boot.index("assertReady();"), owned_boot.index("await boot();"))
        self.assertEqual(1, owned_boot.count("await boot();"))
        self.assertNotIn("selected", owned_boot.split("//")[0])

    def test_native_restoration_precedes_exact_global_deletions_and_all_absence_readbacks(self):
        source, _ = self.sources()
        wasm = span(source, "  function wasmChildBootstrap(", "  const reply =")
        owned_restore = wasm[wasm.index("const ownedRestore ="):wasm.index("const load = async")]
        points = ["if (h.cleaned) return false;", "assertReady();",
                  "h.restore !== ownedRestore || window.__nativecmpkitClipboardBoot !== ownedBoot",
                  "if (restore() !== true || h.cleaned !== true)", "assertFramework();",
                  "for (const [name, descriptor] of [...frameworkDescriptors].reverse())",
                  "sameDescriptor(Object.getOwnPropertyDescriptor(window, name), descriptor)",
                  "delete window[name];", "if (name in window)",
                  "delete window.__karma__;", "if ('__karma__' in window)",
                  "delete h.wasmSelectionDiagnostic;", "if ('wasmSelectionDiagnostic' in h)",
                  "window.__nativecmpkitClipboardBoot = boot;", "h.restore = restore;"]
        positions = [owned_restore.index(item) for item in points]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("actual.writable === expected.writable", wasm)
        self.assertIn("actual.enumerable === expected.enumerable", wasm)
        self.assertIn("actual.configurable === expected.configurable", wasm)
        self.assertIn("descriptor.configurable !== true", wasm)

    def test_current_JS_HTML_formula_is_equal_and_Wasm_has_no_second_loader(self):
        source, old = self.sources()
        before, after = framework.FRAMEWORK_DELTAS[-2]
        self.assertEqual(1, old.count(before))
        self.assertEqual(1, source.count(after))
        self.assertIn("const load = wasm ? '' : '<script>(' + childLoad.toString()", after)
        self.assertIn("')(' + jsValue(session.scripts) + ');</script>'", after)
        before_tail, after_tail = framework.FRAMEWORK_DELTAS[-1]
        self.assertEqual(1, old.count(before_tail))
        self.assertEqual(1, source.count(after_tail))
        # Algebraic rendering check, not a browser/toString execution or an old model replay.
        for function_source in ("function childLoad(scripts) {}", "function childLoad(scripts) { /* </script> */ }"):
            for scripts_source in ("[]", '[{"url":"/held.js?a","type":"text/javascript"}]'):
                old_load = "(" + function_source + ")(" + scripts_source + ");"
                new_load = "<script>(" + function_source + ")(" + scripts_source + ");</script>"
                self.assertEqual("<script>" + old_load + "</script>", new_load)
        js_comment = "    // Accepted JS selection/order/URLs/types remain byte-for-byte below; no Wasm fallback."
        self.assertEqual(span(source, js_comment, "  function childLoad("), span(old, js_comment, "  function childLoad("))

    def test_native_Kotlin_hooks_deadlines_launch_and_security_bytes_remain_exact(self):
        source, old = self.sources()
        for relative, pin in NATIVE_PINS.items():
            self.assertEqual(pin, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
        for start, end in (("  function OwnedClipboardHeadless(", "  const jsValue ="),
                           ("  const close = session =>", "  const middleware =")):
            self.assertEqual(span(source, start, end), span(old, start, end))
        for phrase in ("bounded(scriptUrls(filesPromise, basePath), 5000)", "later(60000", "if (primary) throw primary"):
            self.assertEqual(source.count(phrase), old.count(phrase))
        self.assertNotIn("--no-sandbox", source)
        library = (ROOT / "scripts/ci/library_tests.py").read_text()
        self.assertEqual(framework.QUALIFIED_FRAMEWORK_FIXTURE_SHA256,
                         assigned_literal(library, "SHARE_CLIPBOARD_NATIVE_FIXTURE_SHA256"))
        self.assertEqual(framework.DIAGNOSTIC_FIXTURE_SHA256,
                         digest(framework.diagnostic_fixture_from_framework(source)))

    def test_NEW_real_emitted_probe_has_no_fabricated_discovery_registration_or_native_success(self):
        source, _ = self.sources()
        probe = (ROOT / PROBE).read_text()
        self.assertEqual(PROBE_SHA256, digest(probe))
        for phrase in (
            "const detected = Reflect.apply(actual, receiver, args)",
            "if (!detected) throw falseDetectorSentinel;",
            "return Reflect.apply(actual, receiver, args); // Original callback object",
            "bootstrap('a'.repeat(30), 'insecure', CHOSEN, ORIGIN, CLASS)",
            "context.__nativecmpkitClipboardBoot = safetyBoot;",
            "callbackIdentitiesPreservedAndNeverInvokedByProbe: true",
            "originalPrivateSelectedCounterDirectlyRead: false",
            "originalKarmaFileListAcquired: false", "nativeAcceptance: false",
            "hosted156CauseProved: false", "assertHeld();",
            "NO network: only exact copied real Wasm bytes",
            "nativeWebAssembly.instantiateStreaming", "realLibraryEngineSuccesses",
            "mocha.suite.tests.length, 0", "mocha.suite.suites.length, 0",
        ):
            self.assertIn(phrase, probe)
        self.assertNotIn("NEW_ONLY", source) # Early-stop sentinels belong ONLY to probe safety, never the repair.
        for forbidden in ("exports.startUnitTests =", "describe = ()", "it = ()", "window.describe =",
                          "window.it =", "adapter.suite(", "adapter.test(", "return true; // detector",
                          "await originalBoot()", "originalBoot();", "callback()", "callback.call(" ):
            self.assertNotIn(forbidden, probe)
        # Read literals only; no accepted test module is imported/discovered/invoked.
        loader_guard = (ROOT / "scripts/ci/test_share_clipboard_wasm_recovery.py").read_text()
        reporter_guard = (ROOT / "scripts/ci/test_share_clipboard_wasm_selection_diagnostic.py").read_text()
        self.assertEqual("54753dcb2ec5b4962a14f9dfeb059d08b2668a8548efb9a65c4027c5eb4fb2ab",
                         digest(assigned_literal(loader_guard, "MODELED_FIXTURE")))
        self.assertEqual(digest(assigned_literal(reporter_guard, "DIAGNOSTIC_MODEL")),
                         "a22d579fe2b455490c4eb705866283b3d097889cfd0d90bfdf51aca3ae9964d6")


if __name__ == "__main__":
    unittest.main()
