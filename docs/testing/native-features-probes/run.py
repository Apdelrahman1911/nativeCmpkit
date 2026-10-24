#!/usr/bin/env python3
"""Small, offline-capable audit probes; NOT a native/Compose integration suite.

Source excerpts come from the preserved audit baseline by default. --rev WORKTREE
reads the working tree for Kotlin/Node excerpts; browser primitives always mirror
the baseline DOM operations, not a compiled library. Kotlin probes replace UI
plumbing with explicit doubles; browser probes use an isolated disposable profile.
No application data, credentials, external pages, or package publishing are involved.
"""
from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading

BASELINE = "af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6"
ROOT = Path(__file__).resolve().parents[3]
COMMON = "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/"
DESKTOP = "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/"


def source(path: str, revision: str) -> str:
    if revision == "WORKTREE":
        return (ROOT / path).read_text()
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT, text=True)


def block(text: str, marker: str) -> str:
    start = text.index(marker)
    first = text.index("{", start)
    depth = 1
    for pos in range(first + 1, len(text)):
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
            if depth == 0:
                return text[start:pos + 1]
    raise ValueError(f"Unterminated source block: {marker}")


def kotlin_probe(revision: str, directory: Path) -> dict:
    cache = Path(os.environ.get("GRADLE_USER_HOME", str(Path.home() / ".gradle"))) / "caches/modules-2/files-2.1"

    def jar(group: str, artifact: str, version: str) -> str:
        matches = sorted((cache / group / artifact / version).glob("*/*.jar"))
        if not matches:
            raise FileNotFoundError(f"Cached dependency missing: {group}:{artifact}:{version}")
        return str(matches[0])

    versions = [
        ("org.jetbrains.kotlin", "kotlin-compiler-embeddable", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-build-tools-api", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-stdlib", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-script-runtime", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-reflect", "1.6.10"),
        ("org.jetbrains.kotlin", "kotlin-daemon-embeddable", "2.4.20"),
        ("org.jetbrains.kotlinx", "kotlinx-coroutines-core-jvm", "1.8.0"),
        ("org.jetbrains", "annotations", "23.0.0"),
    ]
    try:
        jars = [jar(*spec) for spec in versions]
    except FileNotFoundError as exc:
        return {"status": "skipped", "reason": str(exc)}
    common = source(COMMON + "WebView.kt", revision)
    desktop = source(DESKTOP + "WebView.desktop.kt", revision)
    cookies = source(DESKTOP + "CookieManager.desktop.kt", revision)
    cookie_model = source(COMMON + "Cookie.kt", revision)
    navigator = block(common, "public class WebViewNavigator(")
    handler = block(desktop, "internal suspend fun WebViewNavigator.handleNavigationEvents(")
    # Cookie's data class has no body, so it is copied as a whole source file.
    header = """
package com.mohamedrejeb.calf.ui.web
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.first
import java.net.CookieHandler
import java.net.HttpCookie
import java.net.URI
import kotlin.reflect.KProperty
// Compose state and the FX queue are doubles. No native WebView is instantiated.
class ProbeState<T>(var value: T)
fun <T> mutableStateOf(value: T) = ProbeState(value)
operator fun <T> ProbeState<T>.getValue(self: Any?, property: KProperty<*>) = value
operator fun <T> ProbeState<T>.setValue(self: Any?, property: KProperty<*>, value: T) { this.value = value }
object Platform {
    val queue = java.util.ArrayDeque<() -> Unit>()
    fun runLater(action: () -> Unit) { queue.add(action) }
}
class ProbeHistory { var currentIndex = 0; val entries = listOf(0); fun go(delta: Int) {} }
class ProbeWorker { var cancels = 0; fun cancel() { cancels++ } }
// JavaFX19 WebEngine's public API has no stopLoading(); its loadWorker has cancel().
class ProbeEngine {
    val history = ProbeHistory(); val loadWorker = ProbeWorker()
    fun reload() {}; fun loadContent(html: String, mime: String?) {}; fun load(url: String) {}
}
class WebView { val engine = ProbeEngine() }
"""
    driver = r'''
fun main() = runBlocking {
    val scope = CoroutineScope(Job() + Dispatchers.Unconfined)
    val navigator = WebViewNavigator(scope)
    val webView = WebView()
    val listener = scope.launch(start = CoroutineStart.UNDISPATCHED) { navigator.handleNavigationEvents(webView) }
    navigator.stopLoading()
    var steps = 0
    while (steps < 100 && Platform.queue.isNotEmpty()) {
        Platform.queue.removeFirst().invoke()
        steps++
    }
    println("STOP_FEEDBACK steps=$steps queued=${Platform.queue.size} nativeCancels=${webView.engine.loadWorker.cancels}")
    check(steps == 100 && Platform.queue.size == 1 && webView.engine.loadWorker.cancels == 0)
    listener.cancel(); scope.cancel(); Platform.queue.clear()

    val replayScope = CoroutineScope(Job() + Dispatchers.Unconfined)
    val replayNavigator = WebViewNavigator(replayScope)
    replayNavigator.navigateBack()
    val first = replayNavigator.navigationEvents.first()
    val second = replayNavigator.navigationEvents.first()
    println("NAVIGATION_REPLAY first=$first second=$second")
    check(first == WebViewNavigator.NavigationEvent.Back && second == first)
    replayScope.cancel()

    val original = CookieHandler.getDefault()
    try {
        val custom = object : CookieHandler() {
            override fun get(uri: URI, headers: Map<String, List<String>>) = mapOf("Cookie" to listOf("kept=1"))
            override fun put(uri: URI, headers: Map<String, List<String>>) {}
        }
        CookieHandler.setDefault(custom)
        val manager = CookieManager()
        manager.getCookies("https://audit.invalid/")
        val replaced = CookieHandler.getDefault() !== custom
        println("COOKIE_HANDLER_REPLACED $replaced")
        check(replaced)
        manager.setCookie("https://audit.invalid/private/", Cookie("private", "1", path = "/private"))
        val names = manager.getCookies("https://audit.invalid/public/").map { it.name }
        println("COOKIE_PATH publicQuery=$names")
        check("private" in names)
        manager.setCookie("https://audit.invalid/", Cookie("expires", "1", expiresDate = System.currentTimeMillis() + 60000))
        val before = manager.getCookies("https://audit.invalid/").first { it.name == "expires" }.expiresDate!!
        Thread.sleep(1200)
        val after = manager.getCookies("https://audit.invalid/").first { it.name == "expires" }.expiresDate!!
        println("COOKIE_EXPIRY_DRIFT millis=${after - before}")
        check(after - before >= 1000)
    } finally { CookieHandler.setDefault(original) }
    println("KOTLIN_PROBES_CONFIRMED 5")
}
'''
    generated = directory / "kotlin"
    generated.mkdir()
    (generated / "Probe.kt").write_text(header + navigator + "\n" + handler + "\n" + driver)
    (generated / "Cookie.kt").write_text(cookie_model)
    (generated / "CookieManager.kt").write_text(re.sub(r"\bactual\s+", "", cookies))
    cp = os.pathsep.join(jars)
    command = ["java", "-Xmx384m", "-cp", cp, "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler",
               "-no-stdlib", "-no-reflect", "-classpath", cp, "-d", str(generated / "classes")]
    compiled = subprocess.run(command + [str(p) for p in generated.glob("*.kt")], text=True, capture_output=True, timeout=90)
    if compiled.returncode:
        return {"status": "failed", "stage": "compile", "stderr": compiled.stderr}
    executed = subprocess.run(["java", "-cp", str(generated / "classes") + os.pathsep + cp,
                               "com.mohamedrejeb.calf.ui.web.ProbeKt"], text=True, capture_output=True, timeout=20)
    return {"status": "confirmed" if executed.returncode == 0 else "failed",
            "stdout": executed.stdout, "stderr": executed.stderr,
            "excerpts_sha256": {"navigator": hashlib.sha256(navigator.encode()).hexdigest(),
                                 "handler": hashlib.sha256(handler.encode()).hexdigest(),
                                 "cookie_manager": hashlib.sha256(cookies.encode()).hexdigest()},
            "limitations": "Exact Kotlin method bodies; Compose state/FX engine/queue are doubles. No GUI/device exercised. Coroutines 1.8.0 harness, not project dependency resolution."}


def node_probe(revision: str, directory: Path) -> dict:
    if not shutil.which("node"):
        return {"status": "skipped", "reason": "Node not installed"}
    text = source("calf-share/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt", revision)
    literal = re.search(r'@JsFun\("(function\(text\) \{ navigator\.clipboard\.writeText\(text\); \})"\)', text)
    if not literal:
        return {"status": "changed", "reason": "Baseline clipboard function no longer present"}
    js = r'''
const vm = require('node:vm');
const outcomes = [];
let unhandled = false;
process.once('unhandledRejection', () => { unhandled = true; });
const fn = vm.runInNewContext('(' + LITERAL + ')', {
  navigator: { clipboard: { writeText: () => Promise.reject(new Error('NotAllowedError')) } }
});
// Exact fallback control flow from ShareLauncher.web.kt:69-73: call, then Success.
try { fn('probe'); outcomes.push('Success'); } catch (_) { outcomes.push('Unavailable'); }
setImmediate(() => {
  console.log(JSON.stringify({outcomes, unhandledRejection: unhandled}));
  if (outcomes[0] !== 'Success' || !unhandled) process.exitCode = 1;
});
'''.replace("LITERAL", json.dumps(literal.group(1)))
    path = directory / "clipboard.cjs"
    path.write_text(js)
    result = subprocess.run(["node", str(path)], capture_output=True, text=True, timeout=10)
    return {"status": "confirmed" if result.returncode == 0 else "failed", "stdout": result.stdout,
            "limitations": "Exact Wasm @JsFun clipboard body, mocked rejected browser promise; wrapper fallback control flow mirrored."}


def browser_probe(directory: Path) -> dict:
    chrome = next((shutil.which(name) for name in ("google-chrome", "chromium", "chromium-browser") if shutil.which(name)), None)
    if not chrome:
        return {"status": "skipped", "reason": "Chrome/Chromium not installed"}
    html = r'''<!doctype html><html><body><pre id="result">RUNNING</pre><script>
(async () => {
 const result = {};
 // These DOM operations mirror CookieManager.web.kt and WebView.web.kt, not compiled Kotlin.
 document.cookie = 'expired=1; path=/; expires=' + (Date.now() - 86400000);
 result.invalidExpiresRetainsExpiredCookie = document.cookie.includes('expired=1');
 document.cookie = 'httpOnlyAttempt=1; path=/; HttpOnly';
 result.httpOnlyAttemptRejected = !document.cookie.includes('httpOnlyAttempt=1');
 document.cookie = 'privatePath=1; path=/private';
 for (const part of document.cookie.split(';')) {
   const name = part.trim().split('=')[0];
   document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
 }
 result.rootOnlyDeletionLeavesPathCookie = document.cookie.includes('privatePath=1');
 const frame = document.createElement('iframe');
 frame.setAttribute('sandbox', 'allow-forms allow-popups allow-same-origin');
 frame.srcdoc = '<p id="old">old HTML</p>';
 await new Promise(resolve => {frame.onload=resolve; document.body.appendChild(frame);});
 frame.src = '/target';
 await new Promise(resolve => setTimeout(resolve, 120));
 result.stateUrlLeavesSrcdoc = !!frame.contentDocument.getElementById('old');
 const navigationDone = new Promise(resolve => {frame.onload=resolve;});
 frame.removeAttribute('srcdoc'); frame.src = '/target';
 await navigationDone;
 result.navigatorUrlClearsSrcdoc = !!frame.contentDocument.getElementById('new');
 const active = document.createElement('iframe');
 active.removeAttribute('sandbox'); // javaScriptEnabled=true branch in WebView.web.kt
 active.srcdoc = '<script>parent.document.documentElement.dataset.auditChild="ran"<\/script>';
 await new Promise(resolve => {active.onload=resolve; document.body.appendChild(active);});
 result.unsandboxedSrcdocCanModifyHost = document.documentElement.dataset.auditChild === 'ran';
 document.getElementById('result').textContent = JSON.stringify(result);
})().catch(error => {document.getElementById('result').textContent=JSON.stringify({error:String(error)});});
</script></body></html>'''

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = ("<html><body><p id='new'>new URL</p></body></html>" if self.path.startswith("/target") else html).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                                 "--disable-background-networking", "--no-first-run", "--disable-extensions",
                                 "--user-data-dir=" + str(directory / "chrome-profile"),
                                 "--virtual-time-budget=5000", "--dump-dom",
                                 f"http://127.0.0.1:{server.server_port}/private/probe"],
                                capture_output=True, text=True, timeout=40)
        match = re.search(r'<pre id="result">(.*?)</pre>', result.stdout, re.S)
        payload = json.loads(match.group(1)) if match and match.group(1) != "RUNNING" else {"error": "Probe did not complete"}
        return {"status": "confirmed" if result.returncode == 0 and payload and all(value is True for value in payload.values()) else "failed",
                "results": payload,
                "browser": subprocess.check_output([chrome, "--version"], text=True).strip(),
                "limitations": "Real browser DOM/cookie semantics; library DOM operations mirrored, no Kotlin/Compose JS/Wasm app compiled."}
    finally:
        server.shutdown()
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rev", default=BASELINE)
    parser.add_argument("--only", choices=("kotlin", "node", "browser"))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="nativecmpkit-native-probes-") as temporary:
        directory = Path(temporary)
        results = {"revision": args.rev, "scope": "source-isolation and browser API probes; not integration tests"}
        for name in ("kotlin", "node", "browser"):
            if args.only is not None and args.only != name:
                continue
            results[name] = {"kotlin": lambda: kotlin_probe(args.rev, directory),
                             "node": lambda: node_probe(args.rev, directory),
                             "browser": lambda: browser_probe(directory)}[name]()
        print(json.dumps(results, indent=2))
        return 1 if any(isinstance(value, dict) and value.get("status") == "failed" for value in results.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
