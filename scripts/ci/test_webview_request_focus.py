"""Finite #64 request-state guards. Synthetic tooling, never native browser results."""
from collections import Counter
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from xml.etree import ElementTree as ET

import library_tests as lt
import workflow_matrix as matrix

FOCUS = "webview-browser-request-state"
PROFILE = "webview-request-state"
CLASS = "com.mohamedrejeb.calf.ui.web.BrowserWebViewRequestAcceptanceTest"
SOURCE = "calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserWebViewRequestAcceptanceTest.kt"
FIXTURE = "calf-webview/karma.config.d/nativecmpkit-request-fixture.js"
PRODUCTION = "calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt"
METHODS = (
    "rejectedOptionsRetryAndNativeReloadResetErrorsAndRequestedMetadata",
    "realRedirectReloadAndOwnedNativeStopHaveDistinctRequestAndTerminalMetadata",
    "repeatedActualTransportRefusalsCannotRetainOldMetadataOrErrorsDuringRecovery",
)

# Built-in Node HTTP tooling only; exact owned loopback listener and resource cleanup.
HTTP_FIXTURE_REGRESSION = r'''
// Tooling-only HTTP regression. No browser, Gradle, external listener or service.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const vm = require('node:vm');

async function main() {
  const config = {};
  const timers = new Set();
  const later = (callback, milliseconds) => {
    const timer = setTimeout(() => { timers.delete(timer); callback(); }, milliseconds);
    timers.add(timer);
    return timer;
  };
  const cancel = timer => { timers.delete(timer); clearTimeout(timer); };
  vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), {
    config, URL, Map, Promise, setTimeout: later, clearTimeout: cancel
  }, { timeout: 1000 });
  const factory = config.plugins.at(-1)['middleware:nativecmpkit-request-fixture'];
  assert.equal(factory[0], 'factory');
  const middleware = factory[1]();
  const sockets = new Set();
  const requests = new Set();
  const closedResources = [];
  const server = http.createServer((request, response) => {
    closedResources.push(new Promise(resolve => response.once('close', resolve)));
    try { middleware(request, response, () => { response.writeHead(404); response.end(); }); }
    catch (error) { response.destroy(error); }
  });
  server.on('connection', socket => {
    sockets.add(socket);
    closedResources.push(new Promise(resolve => socket.once('close', () => {
      sockets.delete(socket); resolve();
    })));
  });
  const observations = {};
  let primary;
  let port;
  let clientRequests = 0;
  const start = (action, token, stage, handle, reject) => {
    clientRequests++;
    const request = http.get({ hostname: '127.0.0.1', port, agent: false,
      path: '/nativecmpkit-request-fixture/' + action + '?token=' + token + '&stage=' + stage }, handle);
    requests.add(request);
    closedResources.push(new Promise(resolve => request.once('close', () => {
      requests.delete(request); resolve();
    })));
    request.once('error', reject);
    request.setTimeout(2000, () => request.destroy(new Error('Owned HTTP request timed out')));
    return request;
  };
  const command = (action, token, stage = 'budget-hold') => new Promise((resolve, reject) => {
    const request = start(action, token, stage, response => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', data => {
        body += data;
        if (Buffer.byteLength(body) > 8192) request.destroy(new Error('Oversized control response'));
      });
      response.once('error', reject);
      response.once('end', () => {
        try {
          const begin = body.indexOf('parent.postMessage(');
          const end = body.indexOf(', "*")', begin);
          assert.ok(begin >= 0 && end > begin, 'Missing actual HTTP control receipt');
          resolve({ status: response.statusCode, message: JSON.parse(body.slice(begin + 19, end)) });
        } catch (error) { reject(error); }
      });
    }, reject);
  });
  const hold = token => new Promise((resolve, reject) => {
    const request = start('hold', token, 'budget-hold', response => {
      let body = '';
      let closed;
      const terminal = new Promise(done => { closed = done; });
      response.once('close', closed);
      response.once('error', () => {}); // The close command must genuinely abort this response.
      response.setEncoding('utf8');
      response.on('data', data => {
        body += data;
        if (Buffer.byteLength(body) > 8192) request.destroy(new Error('Oversized held response'));
        if (body.includes('held|' + token + '|budget-hold')) {
          resolve({ response, terminal });
        }
      });
      response.once('end', () => reject(new Error('Held response completed without owned release')));
    }, reject);
  });
  try {
    await new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(0, '127.0.0.1', resolve);
    });
    const address = server.address();
    assert.equal(address.address, '127.0.0.1');
    assert.ok(address.port > 0);
    port = address.port;
    const token = 'ownedbudget';
    assert.deepEqual(await command('open', token), { status: 200, message: 'opened|' + token });
    const pending = await hold(token);
    for (let index = 0; index < 127; index++) {
      const receipt = await command('receipt', token);
      assert.equal(receipt.status, 200, 'All in-budget observations remain readable');
      assert.ok(receipt.message.includes('budget-hold,0,1,0,0,0,0,0,0,1'));
    }
    observations.workBudget = 128;
    const exhausted = await command('receipt', token);
    observations.exhaustedStatus = exhausted.status;
    assert.equal(exhausted.status, 409, 'The work budget must still refuse extra observations');
    const close = await command('close', token);
    observations.closeStatus = close.status;
    assert.deepEqual(close, { status: 200, message: 'closed|' + token + '|0' },
      'Owned cleanup must remain available after work-budget exhaustion');
    await pending.terminal;
    observations.heldResponseAborted = pending.response.aborted;
    assert.equal(pending.response.aborted, true, 'The owned held response really closed before completion');
    assert.deepEqual(await command('open', token), { status: 200, message: 'opened|' + token },
      'Exact token reuse proves the old session was deleted');
    const collision = await command('open', token);
    assert.deepEqual(collision, { status: 409, message: 'open-refused|' + token });
    const stillOwned = await command('receipt', token);
    assert.equal(stillOwned.status, 200, 'A refused open does not change the existing owner');
    assert.deepEqual(await command('close', token), { status: 200, message: 'closed|' + token + '|0' });
    observations.exactSessionReopenedAndClosed = true;
  } catch (error) { primary = error; }
  finally {
    for (const request of requests) request.destroy();
    for (const socket of sockets) socket.destroy();
    await new Promise(resolve => server.close(resolve));
    await Promise.all(closedResources);
    observations.harnessCleanup = { serverClosed: !server.listening, sockets: sockets.size,
      requests: requests.size, timers: timers.size };
    try {
      assert.deepEqual(observations.harnessCleanup,
        { serverClosed: true, sockets: 0, requests: 0, timers: 0 }, 'Every owned harness resource is released');
    } catch (error) { if (!primary) primary = error; else primary.message += '; ' + error.message; }
  }
  process.stdout.write(JSON.stringify({ status: primary ? 'failed' : 'passed', clientRequests, ...observations }) + '\n');
  if (primary) throw primary;
}
main().catch(error => { process.stderr.write(error.message + '\n'); process.exitCode = 1; });
'''


class WebViewRequestFocusTests(unittest.TestCase):
    def plan(self, suite="js", root=lt.ROOT):
        return lt.plan(root, suite, only_modules=("calf-webview",), focus=FOCUS)

    def source_root(self, directory):
        root = Path(directory).resolve()
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        build = root / "calf-webview/build.gradle.kts"
        build.parent.mkdir()
        build.write_text("// Explicitly synthetic discovery root; never built\n")
        for relative in (SOURCE, FIXTURE):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((lt.ROOT / relative).read_bytes())
        return root

    def identities(self, suite):
        target = "js" if suite == "js" else "wasmJs"
        return [{"classname": lt.SUITES[suite][0] + "." + CLASS,
                 "name": method + "[" + target + ", browser, ChromeHeadless synthetic-tooling]"}
                for method in METHODS]

    def collect(self, suite, cases=None, outcome="", stale=False, duplicate=False, markers=1):
        plan = self.plan(suite)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected, = plan["expected"]
            folder = root / selected["report_directory"]
            folder.mkdir(parents=True)
            xml = ET.Element("testsuite")
            for case in self.identities(suite) if cases is None else cases:
                node = ET.SubElement(xml, "testcase", **case)
                if outcome:
                    ET.SubElement(node, outcome)
            path = folder / "TEST-explicitly-synthetic.xml"
            path.write_bytes(ET.tostring(xml))
            if duplicate:
                (folder / "TEST-duplicate.xml").write_bytes(path.read_bytes())
            now = time.time_ns()
            if stale:
                os.utime(path, ns=(now - 20_000_000_000, now - 20_000_000_000))
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({selected["task"]: markers}), host_system="Linux")

    def test_exact_three_method_browser_plan_preserves_all_slots_and_existing_profiles(self):
        rows = matrix.matrix(PROFILE)["include"]
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in rows])
        self.assertTrue(all(row["test-modules"] == "calf-webview" and row["test-focus"] == FOCUS for row in rows))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        # Eight ordinary hosts remain inventory metadata, not executable default coverage.
        inventory = ('calf-io', 'calf-file-picker', 'calf-geo', 'calf-webview', 'calf-ui', 'calf-navigation', 'calf-share', 'calf-camera-picker')
        self.assertEqual(8, len(inventory))
        self.assertEqual((*inventory, "calf-permissions/core"), lt.MINIMUM_MODULES["android-device"])
        with self.assertRaises(ValueError) as refused:
            lt.plan(lt.ROOT, "android-device")
        self.assertIn(str(refused.exception), (
            'Unfiltered Android discovery requires a qualified remote IO fixture route; full aggregate is blocked',
            'Enabled API35-only callback requires exact finite Camera selection; unrestricted Camera/all discovery refuses before host work',
        ))
        # An unrelated explicit subset cannot admit the unfiltered Camera/IO domains.
        unrelated = ('calf-file-picker', 'calf-geo', 'calf-webview', 'calf-ui', 'calf-navigation', 'calf-share')
        plan = lt.plan(lt.ROOT, "android-device", minimum_modules=unrelated, only_modules=unrelated)
        self.assertEqual(list(unrelated), [item["module"] for item in plan["expected"]])
        self.assertEqual(list(unrelated), plan["explicit_module_subset"])
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-permissions/core"], plan["finite_only_device_modules_not_requested"])
        self.assertEqual(["calf-camera-picker", "calf-io", "calf-permissions/core"],
                         plan["test_bearing_modules_not_requested"])
        for suite in ("js", "wasm"):
            plan = self.plan(suite)
            selected, = plan["expected"]
            self.assertTrue(lt.validate_test_focus(plan))
            self.assertFalse(plan["complete_suite_requested"])
            self.assertEqual(CLASS, selected["test_filter"])
            self.assertEqual([{"classname": CLASS, "name": method} for method in METHODS], selected["required_testcases"])
            self.assertEqual(FIXTURE, selected["browser_http_fixture"])
            command = lt.gradle_command(suite, plan)
            self.assertEqual(CLASS, command[command.index("--tests") + 1])
            self.assertEqual(1, command.count("--tests"))
            self.assertNotIn("publish", " ".join(command))
        for profile in ("all", "browser", "webview-browser", "webview-wasm", "core", "android-device"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))

    def test_readonly_cli_and_validation_reject_wrong_suite_module_filter_fixture_and_full_claim(self):
        for suite in ("js", "wasm"):
            command = [sys.executable, "-B", str(lt.ROOT / "scripts/ci/library_tests.py"), "plan",
                       "--suite", suite, "--module", "calf-webview", "--focus", FOCUS]
            result = subprocess.run(command, cwd=lt.ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(self.plan(suite), json.loads(result.stdout))
            for key, value in (("module", "calf-ui"), ("task", ":calf-webview:publish"), ("test_filter", "*"),
                               ("required_testcases", []), ("test_source_files", []), ("browser_http_fixture", "foreign.js")):
                plan = self.plan(suite)
                plan["expected"][0][key] = value
                with self.assertRaises(ValueError):
                    lt.validate_test_focus(plan)
            plan = self.plan(suite)
            plan["complete_suite_requested"] = True
            with self.assertRaises(ValueError):
                lt.validate_test_focus(plan)
        for suite, modules in (("ios", ("calf-webview",)), ("desktop", ("calf-webview",)),
                               ("android-host", ("calf-webview",)), ("js", None), ("wasm", ("calf-io",)),
                               ("js", ("calf-webview", "calf-ui"))):
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=FOCUS)

    def test_changed_missing_ignored_and_symlinked_native_source_fixture_cannot_reduce_selection(self):
        for suite in ("js", "wasm"):
            with tempfile.TemporaryDirectory() as directory:
                root = self.source_root(directory)
                self.assertTrue(lt.validate_test_focus(self.plan(suite, root)))
                path = root / SOURCE
                original = path.read_text()
                for changed in (original.replace(METHODS[0], "wrongMethod", 1), original + "\n@Test fun extra() {}\n",
                                original.replace("@Test", "@Ignore @Test", 1), original.replace("@Test", "@IgnoredTest", 1)):
                    path.write_text(changed)
                    with self.assertRaises(ValueError):
                        self.plan(suite, root)
                path.write_text(original)
                before = lt.snapshot_inputs(root)
                fixture = root / FIXTURE
                fixture.write_text(fixture.read_text() + "\n// Explicit synthetic mutation\n")
                self.assertNotEqual(before[FIXTURE], lt.snapshot_inputs(root)[FIXTURE])
                fixture.unlink()
                with self.assertRaises(ValueError):
                    self.plan(suite, root)
                fixture.symlink_to(root / SOURCE)
                with self.assertRaises(ValueError):
                    self.plan(suite, root)
                with self.assertRaises(ValueError):
                    lt.snapshot_inputs(root)

    def test_exact_fresh_target_xml_is_required_and_missing_foreign_or_duplicate_methods_stay_red(self):
        for suite in ("js", "wasm"):
            result = self.collect(suite)
            self.assertEqual([], result["errors"], result["errors"])
            self.assertEqual(3, result["totals"]["passed"])
            self.assertTrue(all(case["source"] == SOURCE for case in result["modules"][0]["native_scenarios"]))
            cases = self.identities(suite)
            variants = [[], cases[:-1], cases * 2, self.identities("wasm" if suite == "js" else "js")]
            for key, value in (("classname", "Foreign.AcceptanceTest"), ("name", "unrelated")):
                changed = copy.deepcopy(cases)
                changed[0][key] = value
                variants.append(changed)
            for changed in variants:
                self.assertTrue(self.collect(suite, cases=changed)["errors"])
            for changed in ({"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"},
                            {"stale": True}, {"duplicate": True}, {"markers": 0}, {"markers": 2}):
                self.assertTrue(self.collect(suite, **changed)["errors"])

    def test_workflow_adds_only_exact_serial_profile_with_unchanged_readonly_boundaries(self):
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        options = re.search(r"options: \[([^\n]+)\]", workflow).group(1)
        self.assertIn(PROFILE, {option.strip() for option in options.split(",")})
        serial = re.search(r"^      max-parallel: \$\{\{ \((.+)\) && 1 \|\| 2 \}\}$", workflow, re.M)
        self.assertIsNotNone(serial)
        self.assertCountEqual(["inputs.profile == '" + profile + "'" for profile in (
            "navigation-geo-matrix", "browser-coil-io", "picker-saver-state", "webview-content-transitions", PROFILE, "webview-offline-destination", "share-clipboard-native")],
            serial.group(1).split(" || "))
        self.assertIn("|| inputs.profile == 'webview-content-transitions' || inputs.profile == 'share-clipboard-native') && 1 || 2 }}", workflow,
                      "Retain serial1/default2 and the exact approved clipboard addition")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("packages: write", workflow)

    def test_native_methods_use_public_compose_and_actual_http_transport_events_and_cleanup(self):
        source = (lt.ROOT / SOURCE).read_text()
        for phrase in ("ComposeViewport", "WebView(", "state.content = WebContent.Url", "navigator.reload()",
                       "navigator.stopLoading()", "native.contentWindow?.location?.href", "assertLoading(state, original",
                       "redirected.location", "holdCancelled == 1", "abortClosed == it[stage].abort",
                       "native.contentDocument == null", "message.isTrusted", "event.isTrusted", "message.source",
                       "message.origin == fixture.origin", "NonCancellable", "primary.addSuppressed(error)", "composeWindow.dispose()"):
            self.assertIn(phrase, source)
        for phrase in ("dispatchEvent(", "BrowserWebViewOwner(", "@Ignore", "assumeTrue(", "assumeFalse("):
            self.assertNotIn(phrase, source)
        self.assertNotRegex(source, r"(?m)^import\s+[^\n]*\bsample\.")

    def test_owned_middleware_is_bounded_and_preserves_transport_refusals_instead_of_fabricating_errors(self):
        fixture = (lt.ROOT / FIXTURE).read_text()
        for phrase in ("sessions.size >= 32", "session.stages.size >= 16", "session.pending.size >= 4",
                       "session.requests > 128", "middleware.$inject = []", "response.destroy()",
                       "response.once('close'", "lease.response.destroy()", "session.pending.get(stage) === lease",
                       "session.location = response.getHeader('Location')", "response.writeHead(302)",
                       "counts.expired++", "sessions.delete(token)", "session.pending.size !== 0"):
            self.assertIn(phrase, fixture)
        for phrase in ("require(", "child_process", "fetch(", "https://", "file://", "Access-Control-Allow-Origin"):
            self.assertNotIn(phrase, fixture)
        self.assertEqual(1, fixture.count("$inject"))
        self.assertLess(fixture.index("middleware.$inject = [];"), fixture.index("config.plugins ="))

    def test_reload_begins_readable_native_location_before_native_reload(self):
        source = (lt.ROOT / PRODUCTION).read_text()
        branch = source.split("WebViewNavigator.NavigationEvent.Reload -> {", 1)[1].split("WebViewNavigator.NavigationEvent.StopLoading", 1)[0]
        self.assertNotIn("state.beginRequest(state.requestedUrl)", branch)
        self.assertIn("state.beginRequest(frame.contentWindow?.location?.href)", branch)
        self.assertLess(branch.index("state.beginRequest(frame.contentWindow?.location?.href)"),
                        branch.index("frame.contentWindow?.location?.reload()"))
        self.assertIn("catch (_: Throwable) { load(lastContent) }", branch)


    def test_actual_loopback_http_cleanup_survives_work_budget_exhaustion(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "The owned HTTP fixture regression requires Node; it is never a browser result")
        result = subprocess.run([node, "-e", HTTP_FIXTURE_REGRESSION, str(lt.ROOT / FIXTURE)],
                                cwd=lt.ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual("passed", receipt["status"])
        self.assertEqual(128, receipt["workBudget"])
        self.assertEqual(409, receipt["exhaustedStatus"])
        self.assertEqual(200, receipt["closeStatus"])
        self.assertTrue(receipt["heldResponseAborted"])
        self.assertTrue(receipt["exactSessionReopenedAndClosed"])
        self.assertEqual({"serverClosed": True, "sockets": 0, "requests": 0, "timers": 0}, receipt["harnessCleanup"])
        self.assertLessEqual(receipt["clientRequests"], 140)

    def test_refused_open_has_no_cleanup_lease_and_exact_receipts_own_acquire_release(self):
        source = (lt.ROOT / SOURCE).read_text()
        fixture = source.split("private class Fixture {", 1)[1].split("private suspend fun roundTrip", 1)[0]
        self.assertIn("private var leaseAcquired = false", fixture)
        acquire = fixture.split("suspend fun open()", 1)[1].split("suspend fun close()", 1)[0]
        release = fixture.split("suspend fun close()", 1)[1].split("suspend fun release", 1)[0]
        self.assertLess(acquire.index('assertEquals("opened|$token", roundTrip("open", "receipt"))'),
                        acquire.index("leaseAcquired = true"))
        self.assertLess(release.index("if (!leaseAcquired) return"), release.index('roundTrip("close", "receipt")'))
        self.assertLess(release.index('assertEquals("closed|$token|0", roundTrip("close", "receipt"))'),
                        release.index("leaseAcquired = false"))

    def test_receipt_polling_has_a_finite_cap_below_the_session_work_budget(self):
        source = (lt.ROOT / SOURCE).read_text()
        wait = source.split("suspend fun awaitReceipt(", 1)[1].split("private suspend fun roundTrip", 1)[0]
        cap = re.search(r"repeat\((\d+)\)", wait)
        pause = re.search(r"delay\((\d+)\)", wait)
        self.assertIsNotNone(cap, "Receipt waits need a finite attempt cap independent of elapsed time")
        self.assertIsNotNone(pause)
        self.assertLessEqual(2 * int(cap.group(1)) + 16, 128, "Two waits and fixed controls fit the work budget")
        self.assertGreaterEqual(int(pause.group(1)), 500)
        self.assertIn("withTimeout(15_000)", wait)
        self.assertIn("return@withTimeout current", wait)
        self.assertIn('error("The owned HTTP receipt did not settle', wait)


if __name__ == "__main__":
    unittest.main()
