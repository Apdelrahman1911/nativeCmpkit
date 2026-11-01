"""New/affected #64 source guards only. Every HTTP/socket/JUnit witness below is explicitly synthetic."""
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from xml.etree import ElementTree as ET

import library_tests as lt
import workflow_matrix as matrix

FOCUS = "webview-browser-offline-destination"
PROFILE = "webview-offline-destination"
SOURCE = "calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserWebViewOfflineDestinationAcceptanceTest.kt"
FIXTURE = "calf-webview/karma.config.d/nativecmpkit-offline-fixture.js"
CLASS = "com.mohamedrejeb.calf.ui.web.BrowserWebViewOfflineDestinationAcceptanceTest"
METHOD = "previouslyReachableOwnedDestinationBecomesOfflineWithoutStoppingKarmaOrRetainingRequestState"

# Pure in-memory Node VM model. require(node:http/net) is intercepted: NO listener, socket, network or browser is used.
MODELED_FIXTURE = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const EventEmitter = require('node:events').EventEmitter;
const mode = process.argv[2];
const timers = new Set();
const servers = [];
const probes = [];
const controlPort = 19876;
let nextPort = 46177;
const tick = async () => { for (let index = 0; index < 80; index++) await Promise.resolve(); };
const later = (callback, milliseconds) => { const timer = { callback, milliseconds }; timers.add(timer); return timer; };
const cancel = timer => timers.delete(timer);
const fire = milliseconds => {
  for (const timer of Array.from(timers)) if (timer.milliseconds === milliseconds) {
    timers.delete(timer); timer.callback();
  }
};
class Socket extends EventEmitter {
  constructor() { super(); this.destroyed = false; }
  setTimeout(milliseconds, callback) { this.timeout = { milliseconds, callback }; }
  destroy() { if (!this.destroyed) { this.destroyed = true; Promise.resolve().then(() => this.emit('close')); } }
}
class Response extends EventEmitter {
  constructor(socket) { super(); this.socket = socket; this.destroyed = false; this.writableEnded = false; this.writableFinished = false; }
  writeHead(status, headers) { this.status = status; this.headers = headers; }
  end(body = '') {
    this.body = body; this.writableEnded = true; this.writableFinished = true;
    Promise.resolve().then(() => { this.emit('close'); if (this.socket) this.socket.destroy(); });
    if (this.complete) this.complete();
  }
}
class Server extends EventEmitter {
  constructor(handler) { super(); this.handler = handler; this.listening = false; this.closeCalls = 0; }
  listen(port, host, callback) {
    assert.equal(port, 0); assert.equal(host, '127.0.0.1');
    this.listening = true; this.actual = { address: mode === 'wrong-listen-address' ? '127.0.0.2' : host, port: nextPort++ };
    Promise.resolve().then(callback);
  }
  address() { return this.listening ? this.actual : null; }
  close(callback) {
    this.closeCalls++;
    if (mode !== 'listener-retained') this.listening = false;
    if (mode !== 'missing-close-callback') Promise.resolve().then(() => callback());
  }
}
const config = {};
const emitter = new EventEmitter();
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), {
  config, URL, Map, Set, Promise, setTimeout: later, clearTimeout: cancel,
  require(name) {
    if (name === 'node:http') return { createServer(options, handler) {
      assert.equal(options.maxHeaderSize, 8192); const server = new Server(handler); servers.push(server); return server;
    } };
    if (name === 'node:net') return { createConnection(target) {
      assert.equal(target.host, '127.0.0.1');
      assert.ok(servers.some(server => server.actual.port === target.port && !server.listening), 'Only the previously leased closed destination');
      const socket = new Socket(); probes.push({ target, socket });
      Promise.resolve().then(() => {
        if (mode === 'unexpected-listener') socket.emit('connect');
        else if (mode === 'probe-timeout') return;
        else {
          if (mode !== 'missing-connect-error') socket.emit('error', { code: 'ECONNREFUSED', syscall: 'connect',
            address: '127.0.0.1', port: target.port + (mode === 'wrong-probe-port' ? 1 : 0) });
          socket.destroy();
        }
      });
      return socket;
    } };
    throw new Error('Forbidden real module/network in a synthetic source guard');
  }
}, { timeout: 1000 });
const factory = config.plugins.at(-1)['middleware:nativecmpkit-offline-fixture'];
assert.equal(factory[0], 'factory'); assert.deepEqual(Array.from(factory[1].$inject), ['emitter']);
const middleware = factory[1](emitter);
const token = 'syntheticowned';
const send = async (action, port, owner = token) => {
  const response = new Response();
  middleware({ method: 'GET', socket: { localPort: controlPort },
    url: '/nativecmpkit-offline-fixture/' + action + '?token=' + owner + (port ? '&port=' + port : '') }, response,
    () => { throw new Error('Owned control route unexpectedly delegated'); });
  await tick();
  if (!response.writableEnded) { fire(1000); await tick(); }
  if (!response.writableEnded) { fire(2000); await tick(); }
  assert.equal(response.writableEnded, true, 'The bounded modeled control operation must settle');
  const begin = response.body.indexOf('parent.postMessage('), end = response.body.indexOf(', "*")', begin);
  return { status: response.status, message: JSON.parse(response.body.slice(begin + 19, end)) };
};
const finish = async () => {
  let result;
  emitter.emit('exit', code => { result = code; });
  await tick(); fire(1000); await tick(); fire(2000); await tick();
  assert.notEqual(result, undefined, 'Modeled Karma exit callback must remain bounded');
  return result;
};
async function main() {
  const opened = await send('open');
  if (mode === 'wrong-listen-address') {
    assert.equal(opened.status, 503, 'Bad native listener identity cannot grant an open lease');
    assert.equal(servers[0].listening, false, 'A refused identity still cleans up its exact owned server object');
    assert.equal(probes.length, 0, 'No unaccepted/guessed port may be probed');
    await finish();
  } else {
    const fields = opened.message.split('|');
    assert.equal(opened.status, 200); assert.equal(fields[0], 'opened'); assert.equal(fields[1], token);
    const port = Number(fields[2]); assert.equal(port, servers[0].actual.port);
    const collision = await send('open'); assert.equal(collision.status, 409);
    assert.equal(servers.length, 1, 'Refused open never creates or closes a competing lease');
    const wrong = await send('close', port + 1); assert.equal(wrong.status, 409);
    assert.equal(servers[0].closeCalls, 0, 'A wrong-port client has no cleanup authority');
    const prerequisite = await send('offline', port); assert.equal(prerequisite.status, 409);
    assert.equal(servers[0].closeCalls, 0, 'No offline relabelling of an initially unused port');
    const socket = new Socket(), page = new Response(socket);
    servers[0].emit('connection', socket);
    servers[0].handler({ method: 'GET', headers: { host: '127.0.0.1:' + port },
      url: '/nativecmpkit-offline-destination/' + token + '/page' }, page);
    await tick(); assert.equal(page.status, 200); assert.ok(page.body.includes('online|' + token + '|' + port));
    const online = await send('receipt', port); assert.equal(online.status, 200);
    assert.ok(online.message.includes('|1|1|0|0|1|0|0|not-requested|'));
    const offline = await send('offline', port);
    if (mode === 'valid') {
      assert.equal(offline.status, 200); assert.ok(offline.message.includes('|1|1|0|0|0|1|1|ECONNREFUSED|'));
      const after = await send('receipt', port); assert.equal(after.status, 200);
      assert.ok(after.message.includes('|1|1|0|0|0|1|1|ECONNREFUSED|'), 'Karma remains live after destination-only close');
      for (let index = 0; index < 60; index++) await send('receipt', port);
      assert.equal((await send('receipt', port)).status, 409, '64-work budget is not waived');
      assert.deepEqual(await send('close', port), { status: 200, message: 'closed|' + token + '|' + port + '|0' },
        'Owned cleanup is still available after exhaustion');
      assert.equal(servers[0].closeCalls, 1, 'The exact listener close is latched once');
      assert.equal((await send('receipt', port)).status, 409, 'The owned session was actually deleted');
      assert.equal(await finish(), 0); assert.equal(timers.size, 0);
      assert.ok(probes.length >= 3 && probes.every(probe => probe.target.port === port && probe.socket.destroyed));
    } else {
      assert.equal(offline.status, 503, 'Unknown/retained/listening/mismatched native absence remains a refusal');
      assert.equal(servers[0].closeCalls, 1, 'Do not repeat guessed listener closure on failure');
      assert.notEqual(await finish(), 0, 'Unknown owned cleanup cannot be reported successful');
      assert.ok(probes.every(probe => probe.socket.destroyed), 'Only owned observation sockets are released');
    }
  }
  process.stdout.write(JSON.stringify({ kind: 'pure-synthetic-source-model', mode, passed: true,
    real_network_requests: 0, real_listeners: 0, browser_executions: 0 }) + '\n');
}
main().catch(error => { process.stderr.write(error.message + '\n'); process.exitCode = 1; });
'''


class BrowserOfflineDestinationFocusTests(unittest.TestCase):
    def source_root(self, directory):
        root = Path(directory)
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        build = root / "calf-webview/build.gradle.kts"
        build.parent.mkdir()
        build.write_text("// Explicitly synthetic discovery root; never built\n")
        for relative in (SOURCE, FIXTURE):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((lt.ROOT / relative).read_bytes())
        return root

    def plan(self, root, suite="js"):
        return lt.plan(root, suite, only_modules=("calf-webview",), focus=FOCUS)

    def cases(self, suite="js"):
        target = "js" if suite == "js" else "wasmJs"
        return [{"classname": lt.SUITES[suite][0] + "." + CLASS,
                 "name": METHOD + "[" + target + ", browser, ChromeHeadless synthetic-tooling]"}]

    def collect(self, plan, cases=None, outcome="", stale=False, duplicate=False, markers=1):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected, = plan["expected"]
            folder = root / selected["report_directory"]
            folder.mkdir(parents=True)
            xml = ET.Element("testsuite")
            for case in self.cases(plan["suite"]) if cases is None else cases:
                node = ET.SubElement(xml, "testcase", **case)
                if outcome: ET.SubElement(node, outcome)
            path = folder / "TEST-explicitly-synthetic.xml"
            path.write_bytes(ET.tostring(xml))
            if duplicate: (folder / "TEST-duplicate.xml").write_bytes(path.read_bytes())
            now = time.time_ns()
            if stale: os.utime(path, ns=(now - 20_000_000_000,) * 2)
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({selected["task"]: markers}), host_system="Linux")

    def test_new_source_bound_single_method_selects_only_js_and_wasm_not_accepted_requests(self):
        rows = matrix.matrix(PROFILE)["include"]
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in rows])
        self.assertTrue(all(row["test-modules"] == "calf-webview" and row["test-focus"] == FOCUS for row in rows))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        old = matrix.matrix("webview-request-state")["include"]
        self.assertTrue(all(row["test-focus"] == "webview-browser-request-state" for row in old))
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_root(directory)
            for suite in ("js", "wasm"):
                plan = self.plan(root, suite); selected, = plan["expected"]
                self.assertTrue(lt.validate_test_focus(plan)); self.assertFalse(plan["complete_suite_requested"])
                self.assertEqual(CLASS + "." + METHOD, selected["test_filter"])
                self.assertEqual([{"classname": CLASS, "name": METHOD}], selected["required_testcases"])
                self.assertEqual([SOURCE, FIXTURE], selected["test_source_files"])
                self.assertEqual({relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
                                  for relative in (SOURCE, FIXTURE)}, selected["test_source_sha256"])
                command = lt.gradle_command(suite, plan)
                self.assertEqual(1, command.count("--tests")); self.assertEqual(CLASS + "." + METHOD, command[command.index("--tests") + 1])
                self.assertNotIn(lt.WEBVIEW_REQUEST_CLASS, command)
                self.assertNotIn(lt.WEBVIEW_CONTENT_CLASS, command)

    def test_wrong_suite_scope_source_fixture_plan_fields_or_unreviewed_content_stays_red(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_root(directory)
            for suite in ("ios", "desktop", "android-host", "android-device"):
                with self.assertRaises(ValueError): self.plan(root, suite)
            for suite in ("js", "wasm"):
                for modules in (None, ("calf-ui",), ("calf-webview", "calf-ui")):
                    with self.assertRaises(ValueError): lt.plan(root, suite, only_modules=modules, focus=FOCUS)
                for key, value in (("test_filter", CLASS), ("required_testcases", []), ("test_source_files", []),
                                   ("test_source_sha256", {}), ("browser_http_fixture", "foreign.js"), ("task", ":calf-webview:publish")):
                    plan = self.plan(root, suite); plan["expected"][0][key] = value
                    with self.assertRaises(ValueError): lt.validate_test_focus(plan)
                plan = self.plan(root, suite); plan["complete_suite_requested"] = True
                with self.assertRaises(ValueError): lt.validate_test_focus(plan)
            for relative in (SOURCE, FIXTURE):
                path = root / relative; original = path.read_bytes()
                path.write_bytes(original + b"\n// Synthetic unreviewed edit\n")
                with self.assertRaises(ValueError): self.plan(root)
                path.unlink()
                with self.assertRaises((ValueError, FileNotFoundError)): self.plan(root)
                target = root / (FIXTURE if relative == SOURCE else SOURCE)
                path.symlink_to(target)
                with self.assertRaises(ValueError): self.plan(root)
                path.unlink(); path.write_bytes(original)

    def test_exact_fresh_one_target_xml_rejects_missing_foreign_accepted_duplicate_or_failed_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_root(directory)
            for suite in ("js", "wasm"):
                plan = self.plan(root, suite)
                result = self.collect(plan)
                self.assertEqual([], result["errors"], result["errors"]); self.assertEqual(1, result["totals"]["passed"])
                cases = self.cases(suite)
                accepted = [{"classname": lt.SUITES[suite][0] + "." + lt.WEBVIEW_REQUEST_CLASS,
                             "name": lt.WEBVIEW_REQUEST_METHODS[0] + cases[0]["name"][len(METHOD):]}]
                for changed in ([], cases * 2, self.cases("wasm" if suite == "js" else "js"), accepted, cases + accepted):
                    self.assertTrue(self.collect(plan, cases=changed)["errors"])
                for changed in ({"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"},
                                {"stale": True}, {"duplicate": True}, {"markers": 0}, {"markers": 2}):
                    self.assertTrue(self.collect(plan, **changed)["errors"])

    def test_native_method_requires_actual_online_then_same_destination_absence_callbacks_and_recovery(self):
        source = (lt.ROOT / SOURCE).read_text()
        self.assertEqual([METHOD], re.findall(r"@Test\s+fun\s+(\w+)\s*\(", source))
        for phrase in ("ComposeViewport", "WebView(", "navigator.loadUrl(destination)", "mounted.awaitOnlinePage()",
                       "val online = fixture.awaitOnlineReceipt()", "val offline = fixture.offline()", "offline.assertAbsent()",
                       "afterFailure.assertAbsent()", "recovered.assertAbsent()", "mounted.terminalEvents > terminalsBefore",
                       "native.contentDocument == null", "native.getAttribute(\"src\")", "assertFalse(native.hasAttribute(\"srcdoc\"))",
                       "event.isTrusted", "message.isTrusted", "message.source ===", "message.origin == fixture.destinationOrigin",
                       "message.origin == controlOrigin", "nativeErrors == errorsBefore", "state.errorsForCurrentRequest.isEmpty()",
                       "afterFailure.controls > offline.controls", "assertEquals(online.pages, afterFailure.pages)",
                       "NonCancellable", "primary.addSuppressed(error)", "state.iframe == null", "composeWindow.dispose()"):
            self.assertIn(phrase, source)
        self.assertEqual(2, source.count("navigator.loadUrl(destination)"))
        self.assertLess(source.index("mounted.awaitOnlinePage()"), source.index("fixture.offline()"))
        self.assertLess(source.index("fixture.offline()"), source.index("val terminalsBefore"))
        for forbidden in ("dispatchEvent(", "new Event(", "BrowserWebViewOwner(", "browserListenerProbe", "@Ignore", "assumeTrue("):
            self.assertNotIn(forbidden, source)
        self.assertNotRegex(source, r"state\.(?:errorsForCurrentRequest|pageTitle|loadingState|lastLoadedUrl)\s*=(?!=)")

    def test_fixture_uses_exact_owned_listener_native_close_and_error_proof_not_global_or_synthetic_offline(self):
        source = (lt.ROOT / FIXTURE).read_text()
        self.assertEqual(["node:http", "node:net"], re.findall(r"require\('([^']+)'\)", source))
        for phrase in ("session.server.listen(0, host", "session.server.close(error =>", "session.closeObserved = true",
                       "session.server.address() !== null", "sessions.get(session.token) !== session", "error.code === 'ECONNREFUSED'",
                       "error.syscall === 'connect'", "error.address === host && error.port === session.port", "probe.once('close'",
                       "if (refused && !connected && !timedOut)", "session.sockets.size !== 0", "session.responses.size !== 0",
                       "session.pages !== 1 || session.completed !== 1", "String(session.port) !== port", "action !== 'close'",
                       "session.controls > 64", "sessions.size >= 4", "middleware.$inject = ['emitter']", "emitter.on('exit'",
                       "sessions.delete(token)", "session.closeRequested = true", "session.started.then", "session.timers.size !== 0"):
            self.assertIn(phrase, source)
        for forbidden in ("child_process", "process.kill", "webServer.close", "socketServer.close", "dns.", "setOffline", "iptables",
                          "ip route", "networksetup", "Access-Control-Allow-Origin", "ERR_CONNECTION_REFUSED", "response.destroy()"):
            self.assertNotIn(forbidden, source)

    def test_workflow_adds_only_new_two_target_serial_profile_with_old_tail_and_readonly_boundaries(self):
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        options = re.search(r"options: \[([^\n]+)\]", workflow).group(1)
        self.assertEqual(1, [option.strip() for option in options.split(",")].count(PROFILE))
        serial = re.search(r"^      max-parallel: \$\{\{ \((.+)\) && 1 \|\| 2 \}\}$", workflow, re.M)
        self.assertIsNotNone(serial)
        self.assertCountEqual(["inputs.profile == '" + profile + "'" for profile in (
            "navigation-geo-matrix", "browser-coil-io", "picker-saver-state", "webview-request-state", "webview-content-transitions", PROFILE, "share-clipboard-native")],
            serial.group(1).split(" || "))
        self.assertIn("inputs.profile == 'webview-request-state' || inputs.profile == 'webview-content-transitions' || inputs.profile == 'share-clipboard-native') && 1 || 2 }}", workflow)
        self.assertIn("permissions:\n  contents: read", workflow); self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("packages: write", workflow)

    def modeled(self, mode):
        node = shutil.which("node")
        self.assertIsNotNone(node, "The new pure source model requires Node, never a real listener/browser")
        result = subprocess.run([node, "-e", MODELED_FIXTURE, str(lt.ROOT / FIXTURE), mode],
                                cwd=lt.ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, mode + ": " + result.stdout + result.stderr)
        document = json.loads(result.stdout)
        self.assertEqual("pure-synthetic-source-model", document["kind"])
        self.assertEqual(0, document["real_network_requests"]); self.assertEqual(0, document["real_listeners"])
        self.assertEqual(0, document["browser_executions"])

    def test_pure_modeled_protocol_preserves_reachability_prerequisite_exact_lease_and_exhausted_cleanup(self):
        self.modeled("valid")

    def test_pure_modeled_missing_or_unknown_native_absence_refuses_without_touching_a_foreign_listener(self):
        for mode in ("missing-close-callback", "listener-retained", "unexpected-listener", "missing-connect-error", "wrong-probe-port", "probe-timeout"):
            with self.subTest(mode=mode): self.modeled(mode)

    def test_pure_modeled_wrong_listen_identity_refuses_and_closes_only_the_created_server(self):
        self.modeled("wrong-listen-address")


if __name__ == "__main__":
    unittest.main()
