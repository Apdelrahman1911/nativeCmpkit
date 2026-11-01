"""New-only #82 Wasm loader source controls. No browser/native/SDK acceptance.

The Node model has no listener, browser, DOM, clipboard, Wasm engine, compiler,
network or dependency import. It executes exact fixture functions against explicit
synthetic objects and the pinned KGP2.4.20 loader body's documented interface.
"""
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

import library_tests as lt
import workflow_matrix as matrix

PROFILE = "share-clipboard-native-wasm"
FOCUS = "web-share-clipboard-native-contexts"
FIXTURE = "calf-share/karma.config.d/nativecmpkit-clipboard-fixture.js"
SOURCE = "calf-share/src/webTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardEnvironmentAcceptanceTest.kt"
JS_HELPER = "calf-share/src/jsTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardNativeHarness.js.kt"
WASM_HELPER = "calf-share/src/wasmJsTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardNativeHarness.wasmJs.kt"
CLASS = "com.mohamedrejeb.calf.share.WebClipboardEnvironmentAcceptanceTest"
METHODS = (
    "secureContextWithAbsentClipboardApiReportsUnavailableWithoutPlatformCalls",
    "genuinelyInsecureHttpContextHasNoClipboardApiAndReportsUnavailable",
    "actualDeniedClipboardPermissionRejectsOneTrustedGestureWriteWithoutSuccess",
    "directTrustedGesturePreservesActivationAndCompletesOneActualOwnedTextWrite",
)
# Exact approved max-parallel expression is intentionally unchanged. A single
# Wasm-only matrix row reserves exactly one library job without a redundant tail.
SERIAL = "${{ (inputs.profile == 'navigation-geo-matrix' || inputs.profile == 'browser-coil-io' || inputs.profile == 'picker-saver-state' || inputs.profile == 'webview-offline-destination' || inputs.profile == 'webview-request-state' || inputs.profile == 'webview-content-transitions' || inputs.profile == 'share-clipboard-native') && 1 || 2 }}"
UNCHANGED_SOURCE_SHA256 = {
    SOURCE: "10bf06a15f4d840779aa494122d42c24ed6bbd76ec6926d72eedf982c7cebc60",
    JS_HELPER: "9d33398d366466f41a3d4a46198a7c8e02e3c23fbfd73af1216aa6b0915ebc05",
    WASM_HELPER: "b24a367d8c3e45e896559f1ce7a44d627c8825023ebfd9e9f66c6eb34c64ba59",
}

MODELED_FIXTURE = r"""
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[1], 'utf8');
const mode = process.argv[2];
const klass = 'com.mohamedrejeb.calf.share.WebClipboardEnvironmentAcceptanceTest';
const method = 'genuinelyInsecureHttpContextHasNoClipboardApiAndReportsUnavailable';
const token = 'a'.repeat(30), origin = 'http://localhost:9876';
const cut = (start, end) => source.slice(source.indexOf(start), source.indexOf(end, source.indexOf(start)));
// Exact pure karma-webpack5.0.1 entry-key source behavior; not an npm/runtime import.
const hash = s => { let h = 0xdeadbeef; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 2654435761); return (h ^ (h >>> 16)) >>> 0; };
const modeledRequire = name => { assert.equal(name, 'karma-webpack/lib/utils/hash'); return {hash}; };
const select = vm.runInNewContext(cut('  const isWasmPackage =', '  function childLoad(') + '\nscriptUrls', {path, require: modeledRequire});
const oldSelect = vm.runInNewContext(String.raw`  const scriptUrls = async (filesPromise, basePath) => {
    const files = await filesPromise;
    const chosen = files.included.filter(file => {
      const original = path.basename(file.originalPath || file.path);
      return ['runtime.js', 'commons.js'].includes(original) || /^(NativeCmpKit|nativeCmpkit)-calf-share-test\.m?js$/.test(original);
    });
    if (chosen.length !== 3 || chosen.filter(file => /-calf-share-test\.m?js$/.test(path.basename(file.originalPath || file.path))).length !== 1 ||
        !chosen.some(file => path.basename(file.originalPath || file.path) === 'runtime.js') ||
        !chosen.some(file => path.basename(file.originalPath || file.path) === 'commons.js') ||
        chosen.some(file => file.isUrl || typeof file.path !== 'string' || file.path.includes('\0'))) throw new Error('Exact emitted Karma bundle inputs are missing');
    return chosen.map(file => ({
      url: (file.path.startsWith(basePath) ? '/base' + file.path.slice(basePath.length) : '/absolute' + file.path) + '?' + file.sha,
      type: file.type === 'module' ? 'module' : 'text/javascript'
    }));
  };
` + '\nscriptUrls', {path});
const canonical = value => JSON.parse(JSON.stringify(value));
const packagePath = kind => '/explicitly-synthetic/NativeCmpKit/build/' + kind + '/packages/NativeCmpKit-calf-share-test';
function files(kind = 'wasm') {
  const base = packagePath(kind), output = '/explicitly-synthetic/_karma_webpack_owned';
  const make = (originalPath, filePath = originalPath) => ({originalPath, path: filePath, isUrl: false, sha: 'a'.repeat(40)});
  const entry = kind === 'wasm' ? make(base + '/static/load.mjs', 'load.' + hash(base + '/static/load.mjs') + '.js') :
    make(base + '/kotlin/NativeCmpKit-calf-share-test.js', 'NativeCmpKit-calf-share-test.' + hash(base + '/kotlin/NativeCmpKit-calf-share-test.js') + '.js');
  const included = [make(output + '/runtime.js'), make(output + '/commons.js'), entry,
    make('/explicitly-synthetic/tooling/kotlin-test-karma-runner.js', 'kotlin-test-karma-runner.1.js')];
  return {base, included, served: included.slice()};
}
const flush = () => new Promise(resolve => setImmediate(resolve));
const bootstrapSource = cut('  function childBootstrap(', '  const isWasmPackage =').trim();
const wasmSource = cut('  function wasmChildBootstrap(', '  const reply =').trim();
const loadSource = cut('  function childLoad(', '  function wasmChildBootstrap(').trim();
// Pinned KGP2.4.20 createLoadWasm template: only its static import is represented
// by injected synthetic exports. No compiled test/Wasm module is loaded/executed.
const loaderTemplate = `import * as exports from "../kotlin/NativeCmpKit-calf-share-test.mjs"
try {
    const startUnitTests = "startUnitTests"
    exports[startUnitTests]?.()
    window.__karma__.loaded();
} catch (e) {
    window.__karma__.error("Problem with loading", void 0, void 0, void 0, e)
}`;
const loaderBody = loaderTemplate.slice(loaderTemplate.indexOf('\n') + 1);
function child(options = {}) {
  const messages = [], listeners = new Set(), scripts = [];
  let startCalls = 0, bodyCalls = 0, acceptedCalls = 0;
  const window = {isSecureContext: false,
    addEventListener: (event, handler) => { listeners.add(handler); },
    removeEventListener: (event, handler) => { if (options.restoreFails) throw new Error('private-restoration-error'); listeners.delete(handler); }};
  const context = vm.createContext({window, navigator: {}, parent: {postMessage: (message, target) => { assert.equal(target, origin); messages.push(message); }},
    document: {createElement: () => ({}), head: {appendChild: script => { scripts.push(script); queueMicrotask(() => options.scriptFails ? script.onerror() : script.onload()); }}}});
  const base = vm.runInContext('(' + bootstrapSource + ')', context);
  base(token, 'insecure', method, origin, klass);
  const originalBoot = window.__nativecmpkitClipboardBoot, originalRestore = window.__nativecmpkitClipboardNative.restore;
  const foreign = {loaded() {}, error() {}};
  if (options.preexisting) window.__karma__ = foreign;
  vm.runInContext('(' + wasmSource + ')', context)();
  const register = () => {
    startCalls++;
    if (options.registrationError) throw new Error('private-loader-body-must-not-escape');
    const adapter = window.kotlinTest.adapterTransformer();
    const declare = index => index === klass.split('.').length ? (() => {
      adapter.test('acceptedPromiseOnlyMethodMustNotExecute', false, () => { acceptedCalls++; throw new Error('Accepted synthetic callback was invoked'); });
      adapter.test(method, false, async () => {
        bodyCalls++;
        if (options.bodyWait) await options.bodyWait;
        if (options.replaced) window.__karma__ = foreign;
        window.__nativecmpkitClipboardNative.restore();
      });
    })() : adapter.suite(klass.split('.')[index], false, () => declare(index + 1));
    declare(0);
  };
  context.exports = options.noExport ? {} : {startUnitTests: register};
  return {context, window, messages, listeners, scripts, foreign, originalBoot, originalRestore,
    counts: () => ({startCalls, bodyCalls, acceptedCalls}),
    start: () => vm.runInContext('(' + loadSource + ')', context)([{url: '/explicitly-synthetic/runtime.js', type: 'text/javascript'},
      {url: '/explicitly-synthetic/commons.js', type: 'text/javascript'}, {url: '/absoluteload.1.js', type: 'text/javascript', wasmLoader: true}]),
    register: () => vm.runInContext(loaderBody, context)};
}
function refused(c) {
  assert.equal(c.messages.some(message => message.startsWith('done|')), false);
  assert.equal(c.messages.some(message => message.startsWith('failed|')), true);
  assert.equal(c.counts().acceptedCalls, 0);
}
(async () => {
  if (mode === 'shape' || mode === 'shape-refusals' || mode === 'js-recipe') {
    if (mode === 'js-recipe') {
      const f = files('js');
      assert.deepEqual(canonical(await select(Promise.resolve(f), f.base)), canonical(await oldSelect(Promise.resolve(f), f.base)));
      assert.equal((await select(Promise.resolve(f), f.base)).some(entry => 'wasmLoader' in entry), false);
    } else if (mode === 'shape') {
      const f = files();
      await assert.rejects(oldSelect(Promise.resolve(f), f.base));
      const urls = canonical(await select(Promise.resolve(f), f.base));
      assert.equal(urls.length, 3);
      assert.deepEqual(urls.map(entry => entry.type), ['text/javascript', 'text/javascript', 'text/javascript']);
      assert.deepEqual(urls.map(entry => entry.wasmLoader === true), [false, false, true]);
      assert.equal(urls[2].url, '/absoluteload.' + hash(f.base + '/static/load.mjs') + '.js?' + 'a'.repeat(40));
      // Exact pinned Karma source_files.composeUrl operation strips /absolute,
      // resolving this URL back to the relative path in the served File object.
      const requested = urls[2].url.replace('/', '/').replace(/\?.*$/, '').replace(/^\/absolute/, '').replace(/^\/base/, f.base);
      assert.equal(requested, f.included[2].path);
      assert.equal(f.served.some(file => file.path === requested), true);
    } else {
      const variants = [
        f => { f.included.splice(2, 1); },
        f => { f.included.push(f.included[2]); },
        f => { f.included[2].originalPath = f.base + '/kotlin/NativeCmpKit-calf-share-test.mjs'; },
        f => { f.included[2].originalPath = '/foreign/static/load.mjs'; },
        f => { f.included[2].path = 'load.' + ((hash(f.base + '/static/load.mjs') + 1) >>> 0) + '.js'; },
        f => { f.included[2].path = f.base + '/static/load.mjs'; },
        f => { f.included[2].isUrl = true; },
        f => { f.included[2].path = 'load.1.js\0'; },
        f => { f.included[2].sha = ''; },
        f => { f.included[2].type = 'module'; },
        f => { f.served = f.served.filter(file => file !== f.included[2]); },
        f => { f.included.reverse(); },
        f => { f.included[0].originalPath = f.included[0].path = 'runtime.js'; },
        f => { f.base = '/foreign/build/wasm/packages/foreign-calf-share-test'; },
        f => { f.base += '/.'; },
        f => { f.included[2].originalPath = 7; },
      ];
      for (const mutate of variants) { const f = files(); mutate(f); await assert.rejects(select(Promise.resolve(f), f.base)); }
    }
    return;
  }
  const options = {noExport: mode === 'no-export', registrationError: mode === 'registration-error',
    preexisting: mode === 'preexisting', replaced: mode === 'replaced', scriptFails: mode === 'script-failure', restoreFails: mode === 'restore-failure'};
  let finish;
  if (mode === 'late-duplicate') options.bodyWait = new Promise(resolve => { finish = resolve; });
  const c = child(options);
  c.start();
  await flush();
  assert.equal(c.counts().bodyCalls, 0, 'script.onload must not begin the native method before the actual KGP completion interface');
  if (mode === 'script-failure') { refused(c); assert.equal(c.counts().startCalls, 0); return; }
  c.register();
  if (mode === 'duplicate') c.window.__karma__.loaded();
  if (mode === 'late-error') c.window.__karma__.error('private-error-body-must-not-escape');
  if (mode === 'late-duplicate') {
    await flush();
    assert.equal(c.counts().bodyCalls, 1);
    c.window.__karma__.loaded();
    finish();
  }
  await flush(); await flush();
  if (['no-export', 'registration-error', 'duplicate', 'late-error', 'late-duplicate', 'preexisting', 'replaced', 'restore-failure'].includes(mode)) {
    refused(c);
    if (['registration-error', 'late-error', 'preexisting'].includes(mode)) assert.equal(c.messages.some(message => message.includes('private-')), false);
    if (['preexisting', 'replaced'].includes(mode)) assert.equal(c.window.__karma__, c.foreign, 'Never delete/replace the foreign refused hook');
    return;
  }
  assert.ok(mode === 'handshake' || mode === 'once');
  assert.deepEqual(c.counts(), {startCalls: 1, bodyCalls: 1, acceptedCalls: 0});
  assert.deepEqual(c.messages, ['ready|' + token + '|insecure|' + method, 'done|' + token + '|insecure|' + method + '|passed|0|1']);
  assert.equal('__karma__' in c.window, false);
  assert.equal(c.window.__nativecmpkitClipboardBoot, c.originalBoot);
  assert.equal(c.window.__nativecmpkitClipboardNative.restore, c.originalRestore);
  assert.equal(c.listeners.size, 0);
  if (mode === 'once') {
    await c.window.__nativecmpkitClipboardBoot();
    assert.equal(c.counts().bodyCalls, 1);
    assert.equal(c.messages.filter(message => message.startsWith('done|')).length, 1);
    assert.equal(c.messages[c.messages.length - 1].startsWith('failed|'), true);
  }
})().catch(error => { process.stderr.write(String(error)); process.exitCode = 1; });
"""


class ShareClipboardWasmRecoveryTests(unittest.TestCase):
    def model(self, mode):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Pure source model needs Node; never a real browser/listener")
        result = subprocess.run([node, "-e", MODELED_FIXTURE, str(lt.ROOT / FIXTURE), mode],
                                cwd=lt.ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(0, result.returncode, mode + ": " + result.stdout + result.stderr)

    def test_wasm_only_alias_preserves_all11_and_accepted_share_profiles(self):
        rows = matrix.matrix(PROFILE)["include"]
        self.assertEqual(["browser-wasm"], [row["slot"] for row in rows])
        self.assertEqual(["wasm"], [row["suite"] for row in rows])
        self.assertTrue(all(row["test-modules"] == "calf-share" and row["test-focus"] == FOCUS for row in rows))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        for profile in ("share-browser", "share-clipboard-native"):
            accepted = matrix.matrix(profile)["include"]
            self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in accepted])
            self.assertTrue(all(row["test-modules"] == "calf-share" for row in accepted))
            self.assertTrue(all(("test-focus" in row) == (profile == "share-clipboard-native") for row in accepted))

    def test_dispatch_alias_reserves_one_row_without_serial_permission_or_upload_expansion(self):
        source = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        options = [item.strip() for item in re.search(r"options: \[([^\n]+)\]", source).group(1).split(",")]
        self.assertEqual(1, options.count(PROFILE))
        self.assertEqual(set(matrix.PROFILES), set(options))
        self.assertIn("      max-parallel: " + SERIAL, source)
        self.assertEqual(1, len(matrix.matrix(PROFILE)["include"]))
        self.assertIn("permissions:\n  contents: read", source)
        self.assertIn("persist-credentials: false", source)
        self.assertNotIn("packages: write", source)

    def test_changed_fixture_pin_keeps_four_wasm_identities_one_xml_and_no_js_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "settings.gradle.kts").write_text('include(\n    ":calf-share",\n)\n')
            build = root / "calf-share/build.gradle.kts"; build.parent.mkdir()
            build.write_text("// Explicitly synthetic discovery only; never built\n")
            for relative in (FIXTURE, SOURCE, JS_HELPER, WASM_HELPER):
                target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((lt.ROOT / relative).read_bytes())
            plan = lt.plan(root, "wasm", only_modules=("calf-share",), focus=FOCUS)
            case, = plan["expected"]
            self.assertTrue(lt.validate_test_focus(plan))
            self.assertEqual([{"classname": CLASS, "name": name} for name in METHODS], case["required_testcases"])
            self.assertEqual(1, case["required_original_xml"])
            self.assertEqual(lt.share_clipboard_native_sources("wasm"), case["test_source_sha256"])
            self.assertEqual(":calf-share:wasmJsBrowserTest", case["task"])
            command = lt.gradle_command("wasm", plan)
            self.assertEqual(CLASS, command[command.index("--tests") + 1])
            self.assertNotIn(":calf-share:jsBrowserTest", command)
            self.assertFalse(any("WebSharePromiseTest" in item for item in command))

    def test_accepted_js_recipe_functions_and_modeled_output_are_byte_preserved(self):
        source = (lt.ROOT / FIXTURE).read_text()
        blocks = {
            ("  function childBootstrap(", "  const isWasmPackage ="): "b1b0d9d6e0f1cee9c45176872f849f1e23436c668a6c9afc6ed2703ce0608e18",
            ("  function childLoad(", "  function wasmChildBootstrap("): "bab783bb4505bca73a49e02f2ebd5ab547de846c300a2760f0f990b97bbfd013",
        }
        for (start, end), digest in blocks.items():
            self.assertEqual(digest, hashlib.sha256(source[source.index(start):source.index(end)].rstrip().encode()).hexdigest())
        self.model("js-recipe")

    def test_pinned_kgp_loader_shape_is_classic_relative_served_entry_not_raw_test_module(self):
        self.assertIn('kotlin = "2.4.20"', (lt.ROOT / "gradle/libs.versions.toml").read_text())
        self.model("shape")

    def test_missing_duplicate_foreign_url_type_hash_path_and_unserved_loader_shapes_refuse(self):
        self.model("shape-refusals")

    def test_script_onload_waits_for_kgp_registration_then_restores_exact_owned_hooks(self):
        self.model("handshake")

    def test_loaded_without_actual_start_export_refuses_missing_exact_method(self):
        self.model("no-export")

    def test_actual_loader_error_callback_refuses_without_sharing_error_body(self):
        self.model("registration-error")
        self.model("late-error")

    def test_duplicate_loaded_callback_refuses_before_native_invocation(self):
        self.model("duplicate")

    def test_duplicate_loader_signal_during_owned_method_refuses_at_native_cleanup(self):
        self.model("late-duplicate")

    def test_preexisting_loader_hook_blocks_native_fallthrough_and_is_not_mutated(self):
        self.model("preexisting")

    def test_replaced_owned_loader_hook_refuses_cleanup_without_deleting_foreign_identity(self):
        self.model("replaced")

    def test_loader_script_error_and_original_native_restore_error_remain_failures(self):
        self.model("script-failure")
        self.model("restore-failure")

    def test_repeated_boot_cannot_invoke_one_selected_method_twice(self):
        self.model("once")

    def test_native_sources_ownership_cleanup_and_deadlines_are_not_weakened(self):
        source = (lt.ROOT / FIXTURE).read_text()
        for relative, digest in UNCHANGED_SOURCE_SHA256.items():
            self.assertEqual(digest, hashlib.sha256((lt.ROOT / relative).read_bytes()).hexdigest())
        for start, end, digest in [('  function OwnedClipboardHeadless(', '  const jsValue =', '438d8673bfefee21eff1ee8d46665b6211fc4f4987e6ded7117ae6c8d5401dba'), ('  const close = session =>', '  const middleware =', '20064db0c438f0ae5a8b8d623b58a86259089963204f20eb2a5e4dae86df6cd5')]:
            block = source[source.index(start):source.index(end)].rstrip()
            self.assertEqual(digest, hashlib.sha256(block.encode()).hexdigest())
        opened = source[source.index("if (action === 'open')"):source.index("const session = sessions.get(token);")]
        self.assertLess(opened.index("sessions.set(token, session)"), opened.index("await bounded(scriptUrls"))
        for phrase in ("later(60000", "bounded(scriptUrls(filesPromise, basePath), 5000)", "await selected();", "if (primary) throw primary"):
            self.assertIn(phrase, source)
        self.assertIn("withTimeout(30_000)", (lt.ROOT / SOURCE).read_text())
        self.assertIn("withTimeout(10_000)", (lt.ROOT / SOURCE).read_text())

    def test_new_wasm_failure_reply_exposes_only_fixed_phase_and_keeps_js_reply_literal(self):
        source = (lt.ROOT / FIXTURE).read_text()
        self.assertIn("(isWasmPackage(basePath) ? '|' + phase : ''), 503)", source)
        self.assertEqual({"control", "open-owner", "open-origin", "open-scripts", "open-readback", "open-devtools"},
                         set(re.findall(r"phase = '([^']+)'", source)))
        tail = source[source.index("})().catch(() => reply(response, controlOrigin, 'owned-clipboard-fixture-failed'"):source.index("middleware.$inject")]
        for forbidden in ("error.message", "error.stack", "error.name", "JSON.stringify(error)"):
            self.assertNotIn(forbidden, tail)
        self.assertIn("[token, session.mode, session.method, controlOrigin, klass].map(jsValue)", source)
        self.assertIn("entry.wasmLoader === true", source)
        self.assertIn("'</script>' + wasmBoot + '<script>' + load", source)


if __name__ == "__main__":
    unittest.main()
