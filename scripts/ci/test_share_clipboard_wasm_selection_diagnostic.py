"""Four genuinely new source/Node diagnostic controls; no native acceptance.

The model evaluates only the exact new reporter and marker-lifecycle function
against synthetic closure state and restore/boot stubs. It never imports the
accepted17 test module, evaluates its old model, registers a test callback, loads
a compiled/Wasm module, opens a listener/browser or accesses a clipboard.
Descriptor shape is not origin authentication; same-bit forgery is observable
only as the same bits, so the controls explicitly retain that limitation.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

import share_clipboard_wasm_selection_diagnostic as contract


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = "calf-share/karma.config.d/nativecmpkit-clipboard-fixture.js"
OLD_GUARD = "scripts/ci/test_share_clipboard_wasm_recovery.py"
NATIVE_PINS = {
    "calf-share/src/webTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardEnvironmentAcceptanceTest.kt":
        "10bf06a15f4d840779aa494122d42c24ed6bbd76ec6926d72eedf982c7cebc60",
    "calf-share/src/jsTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardNativeHarness.js.kt":
        "9d33398d366466f41a3d4a46198a7c8e02e3c23fbfd73af1216aa6b0915ebc05",
    "calf-share/src/wasmJsTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardNativeHarness.wasmJs.kt":
        "b24a367d8c3e45e896559f1ce7a44d627c8825023ebfd9e9f66c6eb34c64ba59",
}
OLD_GUARD_METHOD_SHA256 = "506687292d6a8e03086323c971357b4dd2fb382bb503146a12c2e5bcb784defb"
ACCEPTED_MODEL_LITERAL_SHA256 = "54753dcb2ec5b4962a14f9dfeb059d08b2668a8548efb9a65c4027c5eb4fb2ab"
OLD_GUARD_LOOP = (
    "        for (start, end), digest in blocks.items():\n"
    "            self.assertEqual(digest, hashlib.sha256(source[source.index(start):source.index(end)].rstrip().encode()).hexdigest())\n"
)
QUALIFIED_GUARD_LOOP = (
    "        for (start, end), digest in blocks.items():\n"
    "            block = source[source.index(start):source.index(end)].rstrip()\n"
    "            if start == \"  function childBootstrap(\":\n"
    "                block = original_js_child_bootstrap_from_diagnostic(block)\n"
    "            self.assertEqual(digest, hashlib.sha256(block.encode()).hexdigest())\n"
)


PRESERVED_SPANS = (('    // Accepted JS selection/order/URLs/types remain byte-for-byte below; no Wasm fallback.\n', '\n  function childLoad(scripts) {', '905cfa4a1573a3298000a1eb912d11ccb43e39b5967d6dd376ed3dcb6a94a57b'), ('\n  function childLoad(scripts) {', '\n  function wasmChildBootstrap() {', 'ad2d5b310a4c9871df0f1eabb5e507931d7353ce13957af17155679d2b859569'), ('\n    const stack = [];\n', '\n    const sendFailure = error => {', '1acc3744f186389403ea99b460e164e0f20eee4bbd4b33e209ad2657fb235ac0'), ('\n    window.__nativecmpkitClipboardBoot = async () => {', '\n    window.__nativecmpkitClipboardLoadFailure = sendFailure;', '4cdfce3d11ec0a3424a22c042de6e48ddc8764effd0a869357ed3542af3f3b29'), ('\n  function childBootstrap(token, mode, method, parentOrigin, klass) {', '\n    const stack = [];\n', '716dcf769c55723e41794d6319eb4ed9cd7b86dfdd8dc10c032f529f627f019a'))
ORIGINAL_SELECTION_GUARD = "if (typeof selected !== 'function' || selections !== 1 || invocations !== 0) throw new Error('Exact emitted native test method is missing/reused');"
ORIGINAL_SELECTION_GUARD_SHA256 = '75ee5d407fe5137cbf4fa53cd5dde040716b7e8762578c7d253fe9f7754dacc7'
NATIVE_METHODS = ('actualDeniedClipboardPermissionRejectsOneTrustedGestureWriteWithoutSuccess', 'directTrustedGesturePreservesActivationAndCompletesOneActualOwnedTextWrite', 'genuinelyInsecureHttpContextHasNoClipboardApiAndReportsUnavailable', 'secureContextWithAbsentClipboardApiReportsUnavailableWithoutPlatformCalls')


DIAGNOSTIC_MODEL = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[1], 'utf8');
const mode = process.argv[2];
const category = 'Exact emitted native test method is missing/reused';
const publicCategory = 'Exact emitted native test method is missing?reused';
const identity = 'explicitly-synthetic-fixed-identity';
const origin = 'http://explicitly-synthetic.invalid';
const reporterStart = '    const sendFailure = error => {';
const reporterEnd = '    window.__nativecmpkitClipboardBoot = async () => {';
const wasmStart = '  function wasmChildBootstrap() {';
const wasmEnd = '  const reply =';
assert.equal(source.indexOf(reporterStart), source.lastIndexOf(reporterStart));
assert.equal(source.indexOf(wasmStart), source.lastIndexOf(wasmStart));
const reporter = source.slice(source.indexOf(reporterStart), source.indexOf(reporterEnd));
const wasm = source.slice(source.indexOf(wasmStart), source.indexOf(wasmEnd)).trim();
const valid = {value: true, writable: false, enumerable: false, configurable: true};
const prefix = 'failed|' + identity + '|Error:';

// Only the changed reporter is evaluated in this deliberately manufactured
// closure. No registration adapter, suite, selected function or browser runs.
function realm(selected, selections, invocations, descriptor) {
  const output = [];
  const h = {};
  if (descriptor) Object.defineProperty(h, 'wasmSelectionDiagnostic', descriptor);
  const context = vm.createContext({
    selected, selections, invocations, h, identity, parentOrigin: origin,
    parent: {postMessage(message, target) { assert.equal(target, origin); output.push(message); }}
  });
  const send = vm.runInContext(reporter + '\nsendFailure', context);
  const error = vm.runInContext('new Error(' + JSON.stringify(category) + ')', context);
  const messageDescriptor = Object.getOwnPropertyDescriptor(error, 'message');
  return {context, h, output, send, error, messageDescriptor};
}
function unchangedError(c) {
  const same = c.error;
  c.send(c.error);
  assert.equal(c.error, same);
  assert.equal(c.error.message, category);
  assert.equal(c.error.name, 'Error');
  assert.deepEqual(Object.getOwnPropertyDescriptor(c.error, 'message'), c.messageDescriptor);
  assert.equal(c.output.length, 1);
  assert.equal(c.output.some(value => value.startsWith('done|') || value.startsWith('ready|')), false);
}
const observedCount = value => Number.isSafeInteger(value) && value >= 0 && value <= 16 ? String(value) : 'outside';
const expected = (selected, selections, invocations) =>
  prefix + publicCategory + ' (wasm selectedType=' + typeof selected +
  ' selections=' + observedCount(selections) + ' invocations=' + observedCount(invocations) + ')';

// Existing loader populations are not manufactured or run. These exact original
// loader predicates are held as static preconditions: ready once, unfailed,
// current window/h/boot/restore identities. Callbacks below are source stubs.
function markerState(options = {}) {
  const failures = [], events = [];
  let restoreCalls = 0, bootCalls = 0, markerGetterCalls = 0;
  let markerDeleteAttempted = false, hookDeleteAttempted = false;
  const nativeTarget = {cleaned: false};
  const native = new Proxy(nativeTarget, {
    deleteProperty(object, key) {
      if (key === 'wasmSelectionDiagnostic') {
        events.push('delete-marker');
        markerDeleteAttempted = true;
        if (options.preventMarkerDelete) return false;
        const removed = Reflect.deleteProperty(object, key);
        if (options.inheritedMarkerOnReadback) {
          Object.setPrototypeOf(object, Object.create(null, {wasmSelectionDiagnostic: valid}));
        }
        return removed;
      }
      return Reflect.deleteProperty(object, key);
    },
    has(object, key) {
      if (key === 'wasmSelectionDiagnostic' && markerDeleteAttempted) events.push('readback-marker');
      return Reflect.has(object, key);
    },
    set(object, key, value) {
      if (key === 'restore' && options.captureReferenceRestoration) events.push('set-restore-reference');
      return Reflect.set(object, key, value);
    }
  });
  if (options.preexistingOwn) Object.defineProperty(native, 'wasmSelectionDiagnostic', valid);
  if (options.preexistingInherited) Object.setPrototypeOf(nativeTarget, Object.create(null, {wasmSelectionDiagnostic: valid}));
  const preexisting = Object.getOwnPropertyDescriptor(native, 'wasmSelectionDiagnostic');
  const preexistingPrototype = Object.getPrototypeOf(nativeTarget);
  const boot = () => { bootCalls++; throw new Error('A supplied callback must not execute in marker controls'); };
  let window;
  const restore = () => {
    restoreCalls++;
    events.push('original-restore-enter');
    assert.deepEqual(Object.getOwnPropertyDescriptor(native, 'wasmSelectionDiagnostic'), valid);
    assert.equal('__karma__' in window, true);
    if (options.restoreError) throw options.restoreError;
    if (!options.notCleaned) native.cleaned = true;
    events.push('original-restore-return');
    return !options.returnFalse;
  };
  native.restore = restore;
  const windowTarget = {
    __nativecmpkitClipboardNative: native,
    __nativecmpkitClipboardBoot: boot,
    __nativecmpkitClipboardLoadFailure: error => failures.push(error.message)
  };
  window = new Proxy(windowTarget, {
    deleteProperty(object, key) {
      if (key === '__karma__') {
        events.push('delete-loader-hook');
        hookDeleteAttempted = true;
        assert.equal(native.cleaned, true);
        assert.deepEqual(Object.getOwnPropertyDescriptor(native, 'wasmSelectionDiagnostic'), valid);
        if (options.preventHookDelete) return false;
        const removed = Reflect.deleteProperty(object, key);
        if (options.inheritedHookOnReadback) Object.setPrototypeOf(object, {__karma__: 'fixed-synthetic-inherited-hook'});
        return removed;
      }
      return Reflect.deleteProperty(object, key);
    },
    has(object, key) {
      if (key === '__karma__' && hookDeleteAttempted) events.push('readback-loader-hook');
      return Reflect.has(object, key);
    },
    set(object, key, value) {
      if (key === '__nativecmpkitClipboardBoot' && options.captureReferenceRestoration) events.push('set-boot-reference');
      return Reflect.set(object, key, value);
    }
  });
  const context = vm.createContext({window});
  vm.runInContext('(' + wasm + ')', context)();
  // This single explicit readiness input supplies the unchanged static loader
  // precondition. Duplicate/error/registration/old once populations are absent.
  if (options.ready && window.__karma__) window.__karma__.loaded();
  events.length = 0;
  return {native, window, boot, restore, failures, events, preexisting, preexistingPrototype,
          setMarkerGetter() {
            Object.defineProperty(native, 'wasmSelectionDiagnostic', {
              get() { markerGetterCalls++; throw new Error('Marker getter must never execute'); }, configurable: true
            });
          },
          counts: () => ({restoreCalls, bootCalls, markerGetterCalls})};
}

(async () => {
  if (mode === 'bounded-reporter-gates') {
    const without = realm(undefined, 0, 0);
    unchangedError(without);
    assert.deepEqual(without.output, [prefix + publicCategory]);
    let callbackCalls = 0, coercions = 0;
    const callback = () => { callbackCalls++; throw new Error('Selected must never execute'); };
    const sideEffectBearing = {
      [Symbol.toPrimitive]() { coercions++; throw new Error('Count must never coerce'); },
      valueOf() { coercions++; throw new Error('Count must never coerce'); },
      toString() { coercions++; throw new Error('Count must never coerce'); }
    };
    const types = [undefined, null, {}, callback, false, 3, 1n,
                   'PRIVATE_SYNTHETIC_SELECTED_VALUE', Symbol('PRIVATE_SYNTHETIC_SYMBOL')];
    assert.deepEqual([...new Set(types.map(value => typeof value))].sort(),
      ['bigint', 'boolean', 'function', 'number', 'object', 'string', 'symbol', 'undefined']);
    const counts = [...Array.from({length: 17}, (_, n) => n),
      -1, -0, 17, 0.5, NaN, Infinity, -Infinity, Number.MAX_SAFE_INTEGER,
      Number.MAX_SAFE_INTEGER + 1, 'PRIVATE_SYNTHETIC_COUNT', true, null, undefined,
      1n, Symbol('PRIVATE_SYNTHETIC_COUNT_SYMBOL'), sideEffectBearing, new Number(1)];
    for (const selected of types) {
      const c = realm(selected, 0, 0, valid);
      unchangedError(c);
      assert.equal(c.output[0], expected(selected, 0, 0));
      assert.equal(c.output[0].includes('PRIVATE_SYNTHETIC'), false);
      assert.ok(c.output[0].slice(prefix.length).length <= 160);
    }
    for (const count of counts) for (const axis of ['selections', 'invocations']) {
      const a = axis === 'selections' ? count : 0;
      const b = axis === 'invocations' ? count : 0;
      const c = realm(undefined, a, b, valid);
      unchangedError(c);
      assert.equal(c.output[0], expected(undefined, a, b));
      assert.equal(c.output[0].includes('PRIVATE_SYNTHETIC'), false);
      assert.ok(c.output[0].slice(prefix.length).length <= 160);
    }
    const functionOneZero = realm(callback, 1, 0, valid);
    unchangedError(functionOneZero);
    assert.equal(functionOneZero.output[0], expected(callback, 1, 0));
    assert.equal(callbackCalls, 0);
    assert.equal(coercions, 0);
    const wrong = [
      {value: false, configurable: true}, {value: true, writable: true, configurable: true},
      {value: true, enumerable: true, configurable: true}, {value: true, configurable: false},
      {get() { throw new Error('Marker accessor must not execute'); }, configurable: true}
    ];
    for (const descriptor of wrong) {
      const c = realm(undefined, 0, 0, descriptor);
      unchangedError(c);
      assert.deepEqual(c.output, [prefix + publicCategory]);
    }
    const inherited = realm(undefined, 0, 0);
    Object.setPrototypeOf(inherited.h, Object.create(null, {wasmSelectionDiagnostic: valid}));
    unchangedError(inherited);
    assert.deepEqual(inherited.output, [prefix + publicCategory]);
    const unrelated = realm(undefined, 0, 0, valid);
    const other = vm.runInContext("new Error('Different fixed synthetic assertion')", unrelated.context);
    unrelated.send(other);
    assert.deepEqual(unrelated.output, [prefix + 'Different fixed synthetic assertion']);
    const shaped = realm(undefined, 0, 0, valid);
    shaped.send({name: 'Error', message: category});
    assert.deepEqual(shaped.output, [prefix + publicCategory]);
    const foreign = realm(undefined, 0, 0, valid);
    foreign.send(new Error(category));
    assert.deepEqual(foreign.output, [prefix + publicCategory]);
    const replacement = realm(undefined, 0, 0, valid);
    const before = Object.getOwnPropertyDescriptor(replacement.h, 'wasmSelectionDiagnostic');
    delete replacement.h.wasmSelectionDiagnostic;
    Object.defineProperty(replacement.h, 'wasmSelectionDiagnostic', {...valid});
    assert.deepEqual(Object.getOwnPropertyDescriptor(replacement.h, 'wasmSelectionDiagnostic'), before);
    unchangedError(replacement);
    assert.deepEqual(replacement.output, [expected(undefined, 0, 0)]);
    // Same-bit replacement passes shape checks: no exclusive-origin,
    // authenticity, cryptography, adapter or actual registration claim.
    const legacy = realm(undefined, 0, 0, valid);
    const long = vm.runInContext('new Error(' + JSON.stringify('x/'.repeat(200)) + ')', legacy.context);
    long.name = 'N/'.repeat(80);
    legacy.send(long);
    assert.deepEqual(legacy.output, ['failed|' + identity + '|' + 'N?'.repeat(20) + ':' + 'x?'.repeat(80)]);
    assert.equal(long.message, 'x/'.repeat(200));
    assert.equal(long.name, 'N/'.repeat(80));
  } else if (mode === 'new-marker-admission-readiness') {
    for (const flags of [{preexistingOwn: true}, {preexistingInherited: true}]) {
      const c = markerState(flags);
      assert.deepEqual(c.failures, ['Owning Wasm loader setup refused']);
      assert.deepEqual(Object.getOwnPropertyDescriptor(c.native, 'wasmSelectionDiagnostic'), c.preexisting);
      assert.equal(Object.getPrototypeOf(c.native), c.preexistingPrototype);
      assert.equal('wasmSelectionDiagnostic' in c.native, true);
      assert.equal('__karma__' in c.window, false);
      assert.equal(c.native.restore, c.restore);
      assert.deepEqual(c.counts(), {restoreCalls: 0, bootCalls: 0, markerGetterCalls: 0});
    }
    const installed = markerState();
    assert.deepEqual(Object.getOwnPropertyDescriptor(installed.native, 'wasmSelectionDiagnostic'), valid);
    assert.deepEqual(installed.counts(), {restoreCalls: 0, bootCalls: 0, markerGetterCalls: 0});
    const changes = [
      c => { delete c.native.wasmSelectionDiagnostic; },
      c => { Object.defineProperty(c.native, 'wasmSelectionDiagnostic', {value: false, configurable: true}); },
      c => { Object.defineProperty(c.native, 'wasmSelectionDiagnostic', {value: true, writable: true, configurable: true}); },
      c => { Object.defineProperty(c.native, 'wasmSelectionDiagnostic', {value: true, enumerable: true, configurable: true}); },
      c => { Object.defineProperty(c.native, 'wasmSelectionDiagnostic', {value: true, configurable: false}); },
      c => { c.setMarkerGetter(); },
      c => {
        delete c.native.wasmSelectionDiagnostic;
        Object.setPrototypeOf(c.native, Object.create(null, {wasmSelectionDiagnostic: valid}));
      }
    ];
    for (const change of changes) {
      const c = markerState({ready: true});
      change(c);
      await assert.rejects(c.window.__nativecmpkitClipboardBoot(), /Exact emitted Wasm test registration failed\/reused/);
      assert.deepEqual(c.counts(), {restoreCalls: 0, bootCalls: 0, markerGetterCalls: 0});
      assert.equal('__karma__' in c.window, true);
    }
  } else if (mode === 'new-marker-cleanup-readback') {
    const good = markerState({ready: true, captureReferenceRestoration: true});
    assert.equal(good.native.restore(), true);
    assert.deepEqual(good.events, [
      'original-restore-enter', 'original-restore-return', 'delete-loader-hook',
      'readback-loader-hook', 'delete-marker', 'readback-marker',
      'set-boot-reference', 'set-restore-reference'
    ]);
    assert.equal(good.native.cleaned, true);
    assert.equal('__karma__' in good.window, false);
    assert.equal('wasmSelectionDiagnostic' in good.native, false);
    assert.equal(good.window.__nativecmpkitClipboardBoot, good.boot);
    assert.equal(good.native.restore, good.restore);
    assert.deepEqual(good.counts(), {restoreCalls: 1, bootCalls: 0, markerGetterCalls: 0});
    // Do not call restore again: the old accepted once population is excluded.
    for (const options of [{returnFalse: true}, {notCleaned: true}]) {
      const c = markerState({...options, ready: true, captureReferenceRestoration: true});
      assert.throws(() => c.native.restore(), /Owning Wasm native restoration failed/);
      assert.equal('wasmSelectionDiagnostic' in c.native, true);
      assert.equal('__karma__' in c.window, true);
      assert.equal(c.events.includes('delete-marker'), false);
      assert.equal(c.events.includes('set-boot-reference'), false);
      assert.equal(c.events.includes('set-restore-reference'), false);
      assert.deepEqual(c.counts(), {restoreCalls: 1, bootCalls: 0, markerGetterCalls: 0});
    }
    const error = new Error('fixed-synthetic-native-restoration-error');
    const thrown = markerState({ready: true, restoreError: error});
    assert.throws(() => thrown.native.restore(), candidate => candidate === error);
    assert.equal('wasmSelectionDiagnostic' in thrown.native, true);
    assert.equal('__karma__' in thrown.window, true);
    assert.equal(thrown.events.includes('delete-marker'), false);
    for (const options of [{preventHookDelete: true}, {inheritedHookOnReadback: true}]) {
      const c = markerState({...options, ready: true, captureReferenceRestoration: true});
      assert.throws(() => c.native.restore(), /Owning Wasm loader hook removal failed/);
      assert.equal('wasmSelectionDiagnostic' in c.native, true);
      assert.equal('__karma__' in c.window, true);
      assert.equal(c.events.includes('delete-marker'), false);
      assert.equal(c.events.includes('set-boot-reference'), false);
      assert.equal(c.events.includes('set-restore-reference'), false);
    }
    for (const options of [{preventMarkerDelete: true}, {inheritedMarkerOnReadback: true}]) {
      const c = markerState({...options, ready: true, captureReferenceRestoration: true});
      assert.throws(() => c.native.restore(), /Owning Wasm selection diagnostic removal failed/);
      assert.equal(c.native.cleaned, true);
      assert.equal('__karma__' in c.window, false);
      assert.equal('wasmSelectionDiagnostic' in c.native, true);
      assert.equal(c.events.includes('delete-marker'), true);
      assert.equal(c.events.includes('set-boot-reference'), false);
      assert.equal(c.events.includes('set-restore-reference'), false);
      assert.notEqual(c.window.__nativecmpkitClipboardBoot, c.boot);
      assert.notEqual(c.native.restore, c.restore);
      assert.deepEqual(c.counts(), {restoreCalls: 1, bootCalls: 0, markerGetterCalls: 0});
    }
  } else {
    throw new Error('Unknown genuinely new diagnostic control mode');
  }
  process.stdout.write(JSON.stringify({mode, newOnly: true, nativeCallbackExecutions: 0}));
})().catch(error => {
  process.stderr.write(String(error && error.stack || error));
  process.exitCode = 1;
});
"""


class ShareClipboardWasmSelectionDiagnosticTests(unittest.TestCase):
    def source(self):
        return (ROOT / FIXTURE).read_text()

    def model(self, mode):
        # The qualified complete source is a gate, not a new whole-CI hash pin.
        self.assertEqual(contract.QUALIFIED_FIXTURE_SHA256,
                         hashlib.sha256((ROOT / FIXTURE).read_bytes()).hexdigest())
        node = shutil.which("node")
        self.assertIsNotNone(node, "New pure diagnostic controls need Node, not a browser")
        environment = os.environ.copy()
        environment.pop("NODE_OPTIONS", None)
        environment.pop("NODE_PATH", None)
        result = subprocess.run(
            [node, "--no-addons", "-e", DIAGNOSTIC_MODEL, str(ROOT / FIXTURE), mode],
            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(0, result.returncode, mode + ": " + result.stdout + result.stderr)
        self.assertEqual({"mode": mode, "newOnly": True, "nativeCallbackExecutions": 0},
                         json.loads(result.stdout))

    def test_exact_reporter_projection_preserves_original_guards_and_refuses_any_other_delta(self):
        source = self.source()
        restored = contract.original_fixture_from_diagnostic(source)
        self.assertEqual(contract.ORIGINAL_FIXTURE_SHA256, hashlib.sha256(restored.encode()).hexdigest())
        # Exact five new deltas commute in both full orders and all ten pairs.
        # Old controls/models are not imported, discovered, or invoked.
        def apply(text, deltas):
            for before, after in deltas:
                self.assertEqual(1, text.count(before))
                text = text.replace(before, after, 1)
            return text
        self.assertEqual(source, apply(restored, contract.DIAGNOSTIC_DELTAS))
        self.assertEqual(source, apply(restored, reversed(contract.DIAGNOSTIC_DELTAS)))
        for left in range(len(contract.DIAGNOSTIC_DELTAS)):
            for right in range(left + 1, len(contract.DIAGNOSTIC_DELTAS)):
                a, b = contract.DIAGNOSTIC_DELTAS[left], contract.DIAGNOSTIC_DELTAS[right]
                self.assertEqual(apply(restored, (a, b)), apply(restored, (b, a)))
        for start, end, digest in PRESERVED_SPANS:
            self.assertEqual(1, source.count(start))
            self.assertEqual(1, source.count(end))
            before = restored[restored.index(start):restored.index(end)]
            after = source[source.index(start):source.index(end)]
            self.assertEqual(before, after)
            self.assertEqual(digest, hashlib.sha256(after.encode()).hexdigest())
        self.assertEqual(1, source.count(ORIGINAL_SELECTION_GUARD))
        self.assertEqual(ORIGINAL_SELECTION_GUARD_SHA256,
                         hashlib.sha256(ORIGINAL_SELECTION_GUARD.encode()).hexdigest())
        start, end = "  function childBootstrap(", "  const isWasmPackage ="
        block = source[source.index(start):source.index(end)].rstrip()
        old = contract.original_js_child_bootstrap_from_diagnostic(block)
        self.assertEqual(contract.ACCEPTED_CHILD_BOOTSTRAP_SHA256, hashlib.sha256(old.encode()).hexdigest())
        before, after = contract.DIAGNOSTIC_DELTAS[0]
        for changed in (
            old,
            block + after,
            block.replace("selections !== 1", "selections < 1", 1),
            block.replace("invocations !== 0", "invocations < 0", 1),
            block.replace("await selected();", "selected();", 1),
            block.replace("marker.writable === false", "marker.writable === true", 1),
            block.replace(".slice(0, 160)", ".slice(0, 161)", 1),
            block.replace(after, before, 1),
        ):
            self.assertNotEqual(block, changed)
            with self.assertRaises(ValueError):
                contract.original_js_child_bootstrap_from_diagnostic(changed)
        for changed in (
            source.replace("restore() !== true", "restore() !== false", 1),
            source.replace("delete h.wasmSelectionDiagnostic;", "", 1),
            source.replace("if ('wasmSelectionDiagnostic' in h)", "if (false)", 1),
        ):
            self.assertNotEqual(source, changed)
            with self.assertRaises(ValueError):
                contract.original_fixture_from_diagnostic(changed)
        # Read only: the accepted method/model module is NEVER imported or run.
        guard = (ROOT / OLD_GUARD).read_text()
        tree = ast.parse(guard)
        method = next(
            item for cls in tree.body
            if isinstance(cls, ast.ClassDef) and cls.name == "ShareClipboardWasmRecoveryTests"
            for item in cls.body if isinstance(item, ast.FunctionDef)
            and item.name == "test_accepted_js_recipe_functions_and_modeled_output_are_byte_preserved"
        )
        text = ast.get_source_segment(guard, method)
        self.assertEqual(1, text.count(QUALIFIED_GUARD_LOOP))
        reconstructed = text.replace(QUALIFIED_GUARD_LOOP, OLD_GUARD_LOOP, 1)
        self.assertEqual(OLD_GUARD_METHOD_SHA256, hashlib.sha256(reconstructed.encode()).hexdigest())
        modeled = next(
            item.value for item in tree.body if isinstance(item, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "MODELED_FIXTURE" for target in item.targets)
        )
        self.assertIsInstance(modeled, ast.Constant)
        self.assertEqual(ACCEPTED_MODEL_LITERAL_SHA256, hashlib.sha256(modeled.value.encode()).hexdigest())
        library = ast.parse((ROOT / "scripts/ci/library_tests.py").read_text())
        pin = next(
            item.value for item in library.body if isinstance(item, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "SHARE_CLIPBOARD_NATIVE_FIXTURE_SHA256"
                    for target in item.targets)
        )
        self.assertEqual(contract.QUALIFIED_FIXTURE_SHA256, ast.literal_eval(pin))
        for relative, digest in NATIVE_PINS.items():
            content = (ROOT / relative).read_bytes()
            self.assertEqual(digest, hashlib.sha256(content).hexdigest())
            if relative.endswith("WebClipboardEnvironmentAcceptanceTest.kt"):
                for name in NATIVE_METHODS:
                    self.assertEqual(1, content.decode().count("@Test fun " + name + "("))

    def test_bounded_reporter_requires_exact_marker_and_error_without_changing_legacy_envelope(self):
        self.model("bounded-reporter-gates")

    def test_new_marker_admission_and_descriptor_refusals_precede_supplied_callback(self):
        self.model("new-marker-admission-readiness")

    def test_new_marker_cleanup_requires_original_restoration_and_both_absence_readbacks(self):
        self.model("new-marker-cleanup-readback")


if __name__ == "__main__":
    unittest.main()
