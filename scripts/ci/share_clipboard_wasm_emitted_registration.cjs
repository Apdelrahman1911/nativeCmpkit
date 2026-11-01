// SPDX-License-Identifier: Apache-2.0
// NEW-only real emitted Kotlin/Wasm registration integration. NEVER native acceptance.
// Explicitly invoked by the lead in one fresh Node process per red/green cell;
// not auto-discovered/replayed by unittest or part of an ordinary native suite.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createRequire } = require('node:module');
const { createHash } = require('node:crypto');
const assert = require('node:assert/strict');
const { performance } = require('node:perf_hooks');

const BINDING_SHA256 = '0ecc52de878065b884d6797e5ea50a581a5cd3642a653c38f075974a7a050a84';
const OLD_FIXTURE_SHA256 = '347953a8c9596091c3923a37f564b51a7cd7f6488169718222ffe7c6c99e53c8';
const NEW_FIXTURE_SHA256 = 'e2f95d99ff2dd89fa95bd4de8fbedf9f3b60748284fed87ae6fe2ab3d2278a89';
const CLASS = 'com.mohamedrejeb.calf.share.WebClipboardEnvironmentAcceptanceTest';
const METHODS = Object.freeze([
  'secureContextWithAbsentClipboardApiReportsUnavailableWithoutPlatformCalls',
  'genuinelyInsecureHttpContextHasNoClipboardApiAndReportsUnavailable',
  'actualDeniedClipboardPermissionRejectsOneTrustedGestureWriteWithoutSuccess',
  'directTrustedGesturePreservesActivationAndCompletesOneActualOwnedTextWrite'
]);
const CHOSEN = METHODS[1]; // Observe one exact selector choice plus all four genuine declarations, no bodies.
const ORIGIN = 'https://nativecmpkit-new-emitted-registration.invalid';
const FRAMEWORK_NAMES = Object.freeze(['Mocha', 'mocha', 'before', 'after', 'beforeEach', 'afterEach', 'run',
  'describe', 'context', 'xdescribe', 'xcontext', 'it', 'specify', 'xit', 'xspecify']);
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const sha1 = bytes => createHash('sha1').update(bytes).digest('hex');
const held = new Map();
let disposeOwnedTimers = () => {};
function readHeld(file, expected) {
  const stat = fs.lstatSync(file);
  assert.equal(stat.isFile(), true, 'Only a regular private custody file may load');
  assert.equal(stat.isSymbolicLink(), false);
  const bytes = fs.readFileSync(file);
  assert.equal(sha256(bytes), expected);
  held.set(file, { digest: expected, dev: stat.dev, ino: stat.ino, size: stat.size, mtimeMs: stat.mtimeMs });
  return bytes;
}
function assertHeld() {
  for (const [file, before] of held) {
    const stat = fs.lstatSync(file);
    assert.deepEqual({ digest: sha256(fs.readFileSync(file)), dev: stat.dev, ino: stat.ino,
      size: stat.size, mtimeMs: stat.mtimeMs }, before, 'Exact before/after byte and file identities are required');
  }
}
function cut(source, start, end) {
  assert.equal(source.indexOf(start), source.lastIndexOf(start));
  const left = source.indexOf(start);
  assert.notEqual(left, -1);
  const right = source.indexOf(end, left + start.length);
  assert.ok(right > left);
  return source.slice(left, right).trim();
}

(async () => {
  const start = performance.now();
  assert.equal(process.argv.length, 6,
    'Usage: node --no-addons share_clipboard_wasm_emitted_registration.cjs <private-packet> <red|green> <fixture-file> --new-only-no-native');
  const packet = path.resolve(process.argv[2]), cell = process.argv[3], fixtureFile = path.resolve(process.argv[4]);
  // One explicit end marker prevents extra implicit arguments/profile selections.
  assert.equal(process.argv[5], '--new-only-no-native');
  assert.ok(cell === 'red' || cell === 'green');
  const binding = JSON.parse(readHeld(path.join(packet, 'EMITTED-ASSET-BINDING.json'), BINDING_SHA256));
  assert.equal(binding.kind, 'NEW-only-local152-real-emitted-registration');
  assert.equal(binding.original_Karma_fileList_acquired, false);
  assert.equal(binding.hosted156_emitted_bytes_available, false);
  const assets = new Map();
  for (const [role, row] of Object.entries(binding.records)) {
    assert.ok(row.copy.startsWith('custody/') && !row.copy.includes('..'));
    const bytes = readHeld(path.join(packet, row.copy), row.sha256);
    assert.equal(bytes.length, row.bytes);
    assert.equal(sha1(bytes), row.sha1);
    assets.set(role, bytes);
  }
  const source = readHeld(fixtureFile, cell === 'red' ? OLD_FIXTURE_SHA256 : NEW_FIXTURE_SHA256).toString('utf8');
  // Resolver authority is the real karma-mocha module context, not a fabricated discovery adapter.
  for (const role of ['framework_plugin', 'webpack_hash', 'mocha']) {
    const row = binding.records[role];
    readHeld(row.source, row.sha256);
  }
  const actualRequire = createRequire(binding.records.framework_plugin.source);
  assert.equal(actualRequire.resolve('karma-mocha'), binding.records.framework_plugin.source);
  assert.equal(path.join(path.dirname(actualRequire.resolve('mocha')), 'mocha.js'), binding.records.mocha.source);
  assert.equal(actualRequire.resolve('karma-webpack/lib/utils/hash'), binding.records.webpack_hash.source);

  const state = { detector: [], transformerGetter: 0, transformerCalls: 0, namespaceGetter: 0,
    realLibraryInstances: 0, realSkikoInstances: 0, realLibraryEngineSuccesses: 0, realSkikoEngineSuccesses: 0, originalNativeBootDelegations: 0,
    safetyBootCalls: 0, nativeInteropCalls: 0, otherTestInteropCalls: 0, navigatorReads: 0,
    appended: [], fetchRoles: [], frameworkRestored: false };
  const suites = [], declarations = [], callbacks = new Set(), listeners = new Map(), timers = new Set();
  disposeOwnedTimers = () => { for (const timer of timers) clearTimeout(timer); timers.clear(); };
  const messages = [], consoleCounts = { log: 0, info: 0, warn: 0, error: 0, debug: 0 };
  let terminalResolve;
  const terminal = new Promise(resolve => { terminalResolve = resolve; });
  let context, nativeHarness, transformerDescriptor, sourceSelector, safetySentinel, falseDetectorSentinel;
  const nativeWebAssembly = WebAssembly;
  assert.equal(typeof nativeWebAssembly.instantiateStreaming, 'function', 'No Wasm fallback/compiler substitute');
  function guardInterop() { state.nativeInteropCalls++; throw safetySentinel; }
  function guardOtherTestInterop() { state.otherTestInteropCalls++; throw safetySentinel; }
  function wrapImport(jsCode, name, observe) {
    const descriptor = Object.getOwnPropertyDescriptor(jsCode, name);
    assert.ok(descriptor && typeof descriptor.value === 'function');
    const actual = descriptor.value;
    Object.defineProperty(jsCode, name, { ...descriptor, value: function(...args) {
      return observe(actual, this, args);
    }});
  }
  const engine = Object.create(Object.getPrototypeOf(nativeWebAssembly), Object.getOwnPropertyDescriptors(nativeWebAssembly));
  Object.defineProperty(engine, 'instantiateStreaming', { ...Object.getOwnPropertyDescriptor(nativeWebAssembly, 'instantiateStreaming'),
    value: async function(response, imports, options) {
      const library = Boolean(imports && imports.js_code && Object.hasOwn(imports.js_code, 'kotlin.test.isJasmine'));
      if (library) {
        assert.equal(++state.realLibraryInstances, 1);
        const jsCode = imports.js_code;
        wrapImport(jsCode, 'kotlin.test.isJasmine', (actual, receiver, args) => {
          const detected = Reflect.apply(actual, receiver, args); // The genuine emitted detector, never return invented true.
          assert.equal(typeof detected, 'boolean');
          state.detector.push(detected);
          if (!detected) throw falseDetectorSentinel; // BEFORE actual unmanaged fallback; no accepted test body may run.
          return detected;
        });
        wrapImport(jsCode, 'kotlin.test.kotlinTestNamespace_$external_prop_getter', (actual, receiver, args) => {
          state.namespaceGetter++;
          const result = Reflect.apply(actual, receiver, args);
          assert.equal(result, context.kotlinTest);
          return result; // Exact emitted namespace, not a replacement.
        });
        wrapImport(jsCode, 'kotlin.test.adapterTransformer_$external_prop_getter', (actual, receiver, args) => {
          state.transformerGetter++;
          const result = Reflect.apply(actual, receiver, args);
          assert.equal(result, transformerDescriptor.value);
          return result; // Exact original transformer object.
        });
        wrapImport(jsCode, 'kotlin.test.__callJsClosure_((Js)->Js)', (actual, receiver, args) => {
          assert.equal(args[0], transformerDescriptor.value);
          state.transformerCalls++;
          const result = Reflect.apply(actual, receiver, args);
          sourceSelector = result;
          return result; // Exact original selector adapter; no alternate selection function.
        });
        wrapImport(jsCode, 'kotlin.test.suite_$external_fun', (actual, receiver, args) => {
          assert.equal(args[0], sourceSelector);
          assert.equal(typeof args[1], 'string');
          suites.push(args[1]);
          try { return Reflect.apply(actual, receiver, args); } // Only the original selector invokes allowed declaration suites.
          finally { suites.pop(); }
        });
        wrapImport(jsCode, 'kotlin.test.test_$external_fun', (actual, receiver, args) => {
          assert.equal(args[0], sourceSelector);
          if (suites.join('.') === CLASS) {
            assert.equal(args[2], false);
            assert.equal(typeof args[3], 'function');
            declarations.push({ name: args[1], callback: args[3] });
            callbacks.add(args[3]);
          }
          return Reflect.apply(actual, receiver, args); // Original callback object and arguments, never invoked here.
        });
        // Any genuine clipboard scenario entry (nativeMode first) is a hard safety failure.
        // Also refuse accepted/foreign harness operations; the original selector excludes them.
        for (const key of Object.keys(jsCode)) {
          if (/^com\.mohamedrejeb\.calf\.share\.native(?:Mode|Value|SecureContext|Activation|ApiAvailable|MaskApi|ObserveWrites|Permission|Arm|Cleanup)$/.test(key) ||
              /^com\.mohamedrejeb\.calf\.share\.js(?:IsClipboardSupported|CopyToClipboard)$/.test(key)) {
            Object.defineProperty(jsCode, key, { ...Object.getOwnPropertyDescriptor(jsCode, key), value: guardInterop });
          } else if (/^com\.mohamedrejeb\.calf\.share\.(?:install|field|file)$/.test(key)) {
            Object.defineProperty(jsCode, key, { ...Object.getOwnPropertyDescriptor(jsCode, key), value: guardOtherTestInterop });
          }
        }
      } else {
        assert.equal(++state.realSkikoInstances, 1, 'Only the real emitted Skiko streaming dependency is admitted');
      }
      // Real engine, original unmodified emitted module bytes, real imports except delegated observation/safety guards.
      const result = await Reflect.apply(nativeWebAssembly.instantiateStreaming, nativeWebAssembly, [response, imports, options]);
      assert.ok(result.instance instanceof nativeWebAssembly.Instance);
      if (library) state.realLibraryEngineSuccesses++; else state.realSkikoEngineSuccesses++;
      return result;
    }
  });
  const scriptRows = [
    ['runtime', binding.records.runtime.source, binding.records.runtime.source],
    ['commons', binding.records.commons.source, binding.records.commons.source],
    ['mocha', binding.records.mocha.source, binding.records.mocha.source],
    ['load', binding.load_entry, binding.records.kgp_load.source]
  ];
  // Constructed transport metadata is explicitly not an acquired original Karma fileList.
  // Actual fixture scriptUrls makes the decision; no selected function/declaration is manufactured.
  const metadata = scriptRows.map(([role, servedPath, originalPath]) => ({
    path: servedPath, originalPath, sha: binding.records[role].sha1, type: 'js', isUrl: false
  }));
  const files = { included: metadata, served: metadata.slice() };
  const scriptUrls = vm.runInNewContext(cut(source, '  const isWasmPackage =', '  function childLoad(') + '\nscriptUrls',
    { path, require: actualRequire });
  const selectedScripts = JSON.parse(JSON.stringify(await scriptUrls(Promise.resolve(files), binding.base_path)));
  assert.equal(selectedScripts.length, cell === 'red' ? 3 : 4);
  const scriptMap = new Map(scriptRows.map(([role, servedPath]) => [
    '/absolute' + servedPath + '?' + binding.records[role].sha1, role
  ]));
  const wasmMap = new Map([
    [ORIGIN + '/absolute' + binding.webpack_dir + '/' + binding.library_asset, 'library_wasm'],
    [ORIGIN + '/absolute' + binding.webpack_dir + '/' + binding.skiko_asset, 'skiko_wasm']
  ]);
  const document = {
    baseURI: ORIGIN + '/nativecmpkit-clipboard-fixture/child?new-only=1', currentScript: null,
    createElement(name) { assert.equal(name, 'script'); return { tagName: 'SCRIPT' }; },
    getElementsByTagName(name) { assert.equal(name, 'script'); return []; },
    head: { appendChild(script) {
      assert.equal(script.type, 'text/javascript');
      const role = scriptMap.get(script.src);
      assert.ok(role, 'Only exact SHA1-bound copied script assets can load');
      state.appended.push(role);
      queueMicrotask(() => {
        const old = document.currentScript;
        document.currentScript = { tagName: 'SCRIPT', src: new URL(script.src, ORIGIN).href };
        try {
          vm.runInContext(assets.get(role).toString('utf8'), context, { filename: 'held-real-emitted-' + role, timeout: 15000 });
          script.onload();
        } catch (error) { script.onerror(error); }
        finally { document.currentScript = old; }
      });
      return script;
    }}
  };
  const navigator = {};
  for (const key of ['clipboard', 'permissions', 'userActivation', 'share', 'canShare']) {
    Object.defineProperty(navigator, key, { configurable: true, get() { state.navigatorReads++; throw safetySentinel; } });
  }
  const sandbox = {
    document, navigator, WebAssembly: engine, URL, Response, TextEncoder, TextDecoder, performance,
    location: { href: document.baseURI, search: '' },
    isSecureContext: false,
    parent: { postMessage(message, origin) {
      assert.equal(origin, ORIGIN);
      assert.equal(typeof message, 'string');
      messages.push(message);
      assert.equal(/^(ready|done|armed)\|/.test(message), false, 'The original native boot or body must never run');
      if (message.startsWith('failed|')) terminalResolve();
    }},
    console: Object.fromEntries(Object.keys(consoleCounts).map(key => [key, () => { consoleCounts[key]++; }])),
    addEventListener(name, callback) { const values = listeners.get(name) || new Set(); values.add(callback); listeners.set(name, values); },
    removeEventListener(name, callback) { assert.equal(listeners.get(name)?.delete(callback), true); },
    setTimeout(callback, delay, ...args) {
      const handle = setTimeout(() => { timers.delete(handle); callback(...args); }, delay);
      timers.add(handle); return handle;
    },
    clearTimeout(handle) { clearTimeout(handle); timers.delete(handle); },
    setInterval() { throw new Error('No interval/resource producer is required for registration'); },
    clearInterval() { throw new Error('No interval/resource producer is owned by registration'); },
    fetch: async function(url, options) {
      const value = typeof url === 'string' ? url : url.href;
      const role = wasmMap.get(value);
      assert.ok(role, 'NO network: only exact copied real Wasm bytes may be transported');
      if (options !== undefined) {
        assert.deepEqual(Object.keys(options), ['credentials']);
        assert.equal(options.credentials, 'same-origin');
      }
      state.fetchRoles.push(role);
      return new Response(assets.get(role), { status: 200, headers: { 'Content-Type': 'application/wasm' } });
    }
  };
  sandbox.window = sandbox; sandbox.self = sandbox; // Genuine emitted global lookup in one fresh isolated realm.
  context = vm.createContext(sandbox);
  safetySentinel = vm.runInContext('new Error("NEW_ONLY_BEFORE_ORIGINAL_NATIVE_BOOT")', context);
  falseDetectorSentinel = vm.runInContext('new Error("NEW_ONLY_FALSE_DETECTOR_BEFORE_UNMANAGED_FALLBACK")', context);
  const bootstrap = vm.runInContext('(' + cut(source, '  function childBootstrap(', '  const isWasmPackage =') + ')', context);
  bootstrap('a'.repeat(30), 'insecure', CHOSEN, ORIGIN, CLASS); // Exact original selector, not a synthetic adapter.
  nativeHarness = context.__nativecmpkitClipboardNative;
  transformerDescriptor = Object.getOwnPropertyDescriptor(context.kotlinTest, 'adapterTransformer');
  assert.ok(transformerDescriptor && typeof transformerDescriptor.value === 'function');
  const originalBoot = context.__nativecmpkitClipboardBoot;
  const originalRestore = nativeHarness.restore;
  assert.equal(typeof originalBoot, 'function');
  // Explicit safety instrumentation stops before the original boot; stored selected callback remains untouched.
  const safetyBoot = async () => { state.safetyBootCalls++; throw safetySentinel; };
  context.__nativecmpkitClipboardBoot = safetyBoot;
  const wasmBootstrap = vm.runInContext('(' + cut(source, '  function wasmChildBootstrap(', '  const reply =') + ')', context);
  wasmBootstrap(selectedScripts);
  if (cell === 'red') {
    const load = vm.runInContext('(' + cut(source, '  function childLoad(', '  function wasmChildBootstrap(') + ')', context);
    load(selectedScripts);
  }
  const terminalTimer = setTimeout(() => terminalResolve('timeout'), 60000);
  let disposition;
  try { disposition = await terminal; } finally { clearTimeout(terminalTimer); }
  assert.notEqual(disposition, 'timeout', 'No blind retry/timeout acceptance');
  // Allow already settled real Skiko initialization/error work to report before freezing counters.
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(state.realLibraryInstances, 1);
  assert.equal(state.realSkikoInstances, 1);
  assert.equal(state.realLibraryEngineSuccesses, 1);
  assert.equal(state.realSkikoEngineSuccesses, 1);
  assert.deepEqual(state.fetchRoles.slice().sort(), ['library_wasm', 'skiko_wasm']);
  assert.equal(state.nativeInteropCalls, 0);
  assert.equal(state.otherTestInteropCalls, 0);
  assert.equal(state.navigatorReads, 0);
  assert.equal(state.originalNativeBootDelegations, 0); // No code path calls originalBoot.
  assert.deepEqual(Object.getOwnPropertyDescriptor(context.kotlinTest, 'adapterTransformer'), transformerDescriptor);
  assert.equal(messages.length, 1);
  assert.equal(suites.length, 0);
  if (cell === 'red') {
    assert.deepEqual(state.detector, [false]);
    assert.equal(state.transformerGetter, 0);
    assert.equal(state.transformerCalls, 0);
    assert.equal(state.namespaceGetter, 0);
    assert.equal(state.safetyBootCalls, 0);
    assert.equal(declarations.length, 0);
    assert.deepEqual(state.appended, ['runtime', 'commons', 'load']);
    assert.equal(FRAMEWORK_NAMES.some(name => name in context), false);
  } else {
    assert.deepEqual(state.detector, [true]);
    assert.equal(state.transformerGetter, 1);
    assert.equal(state.transformerCalls, 1);
    assert.equal(state.namespaceGetter, 1);
    assert.equal(state.safetyBootCalls, 1);
    assert.deepEqual(state.appended, ['runtime', 'commons', 'mocha', 'load']);
    assert.deepEqual(declarations.map(row => row.name), METHODS);
    assert.equal(callbacks.size, 4);
    assert.equal(declarations.filter(row => row.name === CHOSEN).length, 1);
    const mocha = context.mocha;
    assert.equal(mocha instanceof context.Mocha, true);
    assert.equal(mocha.suite.tests.length, 0);
    assert.equal(mocha.suite.suites.length, 0); // Original selector captured callbacks; framework queued/run NONE.
    // Exact real source harness listener cleanup only: no clipboard was touched, no native cleanup acceptance.
    assert.equal(nativeHarness.restore(), true);
    assert.equal(nativeHarness.cleaned, true);
    assert.equal(FRAMEWORK_NAMES.some(name => name in context), false);
    assert.equal('__karma__' in context, false);
    assert.equal('wasmSelectionDiagnostic' in nativeHarness, false);
    assert.equal(nativeHarness.restore, originalRestore);
    assert.equal(context.__nativecmpkitClipboardBoot, safetyBoot);
    assert.equal([...listeners.values()].reduce((sum, values) => sum + values.size, 0), 0);
    state.frameworkRestored = true;
  }
  // Retain all input identities before closing the isolated process resources.
  assertHeld();
  const remainingTimers = timers.size;
  disposeOwnedTimers();
  assert.equal(remainingTimers, 0, 'Registration must not leave a producer/timer behind');
  process.stdout.write(JSON.stringify({ schema: 1, cell, newOnly: true,
    kind: 'genuine-real-emitted-Kotlin-Wasm-registration-NOT-browser-native',
    node: process.version, v8: process.versions.v8, elapsedSeconds: (performance.now() - start) / 1000,
    state, registeredNames: declarations.map(row => row.name), chosenName: CHOSEN,
    callbackIdentitiesPreservedAndNeverInvokedByProbe: true,
    originalPrivateSelectedCounterDirectlyRead: false, originalKarmaFileListAcquired: false,
    frameworkQueuedTests: cell === 'green' ? 0 : null, beforeAfterHeldFiles: held.size,
    consoleCounts, nativeAcceptance: false, issueClosure: false, hosted156CauseProved: false }) + '\n');
})().catch(error => {
  disposeOwnedTimers();
  // Lead retains this fresh failed attempt; never retry/fabricate a registration or turn it into native evidence.
  process.stderr.write(String(error && error.stack || error) + '\n');
  process.exitCode = 1;
});
