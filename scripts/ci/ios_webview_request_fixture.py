"""Test-only, token-owned localhost transport for genuine library WKWebView tests.

No network starts at import. TLS is deliberately refused with a real fatal alert
AFTER a complete ClientHello; no certificate/private key/trust override exists.
This is NOT DNS/offline certification. No app/SDK/process launch is owned here;
the existing UIKit transport owns that exact app, console PID and cleanup.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler
import hashlib
import os
from pathlib import Path
import re
import select
import socket
import threading
import time
import uuid
from urllib.parse import urlsplit

FOCUS = "webview-ios-native-request-state"
SOURCE = "scripts/ci/ios_webview_request_fixture.py"
NATIVE_SOURCE = "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewRequestAcceptanceTest.kt"
METHOD_KEYS = ("tls", "matrix")
STAGE_SPECS = {
    "tls-prior": ("page", 1), "tls-one": ("tls", 1), "tls-two": ("tls", 1), "tls-recover": ("page", 2),
    "matrix-prior": ("page", 1), "matrix-redirect": ("redirect", 1), "matrix-final": ("page", 1),
    "matrix-hold": ("hold", 1), "matrix-recover": ("page", 1),
}
COUNTERS = ("generation", "arrived", "pending", "closed", "page", "redirect", "hello", "alert", "client_cancelled", "response_bytes", "compat_ccs")
MAX_CONNECTIONS = 32
MAX_WORK = 4096
MAX_STAGE_CONNECTIONS = 32
GATE_SECONDS = 12.0  # Native predicate deadline remains the unchanged10s; expiry is a fixture failure.
JOIN_SECONDS = 3.0
TLS_FATAL_HANDSHAKE_FAILURE = bytes.fromhex("15 03 03 00 02 02 28")
BUNDLE = re.compile(r"io\.github\.apdelrahman1911\.nativecmpkit\.verification\.ui\.r[0-9a-f]{12}\.t[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def parse_route(path: str, token: str) -> tuple[str, str, str]:
    """A finite path parser, not path traversal, URL forwarding or an open proxy."""
    if not isinstance(path, str) or len(path) > 256:
        raise ValueError("Unbounded owned request route")
    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or "%" in path or "\\" in path:
        raise ValueError("Only exact owned relative paths are accepted")
    parts = parsed.path.split("/")
    if len(parts) == 5 and parts[:3] == ["", token, "control"]:
        action, value = parts[3:]
        if ((action == "claim" and re.fullmatch(r"[1-9][0-9]{0,9}", value) and int(value) < 2**31) or
                (action in {"arm", "release", "stats"} and value in STAGE_SPECS) or
                (action == "done" and value in METHOD_KEYS)):
            return "control", action, value
    if len(parts) == 4 and parts[:3] == ["", token, "page"] and parts[3] in STAGE_SPECS:
        return "page", "load", parts[3]
    raise ValueError("Unknown or foreign owned request route")


def client_hello_record(header: bytes, payload: bytes) -> bool:
    """Require a complete bounded TLS handshake/ClientHello record, not a TCP connect."""
    if len(header) != 5 or header[0] != 22 or header[1] != 3 or header[2] not in (1, 2, 3):
        return False
    length = int.from_bytes(header[3:5], "big")
    if not 4 <= length <= 16384 or len(payload) != length or payload[0] != 1:
        return False
    # Complete first ClientHello, not a forged partial/empty handshake frame.
    size = int.from_bytes(payload[1:4], "big")
    if size != length - 4 or size < 41:
        return False
    body = payload[4:]
    if body[:1] != b"\x03":
        return False
    session_size = body[34]
    offset = 35 + session_size
    if session_size > 32 or offset + 2 > len(body):
        return False
    cipher_size = int.from_bytes(body[offset:offset + 2], "big")
    offset += 2 + cipher_size
    if cipher_size < 2 or cipher_size % 2 or offset >= len(body):
        return False
    compression_size = body[offset]
    offset += 1 + compression_size
    if compression_size < 1 or offset > len(body):
        return False
    if offset == len(body):
        return True
    if offset + 2 > len(body):
        return False
    extensions = int.from_bytes(body[offset:offset + 2], "big")
    return offset + 2 + extensions == len(body)



def framed_response_bytes(headers: list[bytes], body: bytes) -> int:
    # BaseHTTPRequestHandler.end_headers appends the final CRLF after the
    # buffered status/header lines. Count that framing byte pair too.
    return sum(map(len, headers)) + 2 + len(body)


def zero_counters() -> dict:
    return dict.fromkeys(COUNTERS, 0)


def complete_stages(stages: dict, method: str) -> bool:
    names = ("tls-prior", "tls-one", "tls-two", "tls-recover") if method == "tls" else (
        "matrix-prior", "matrix-redirect", "matrix-final", "matrix-hold", "matrix-recover")
    if any(name not in stages for name in names):
        return False
    for name in names:
        c = stages[name]
        if (not isinstance(c, dict) or set(c) != set(COUNTERS) or
                any(type(v) is not int or not 0 <= v <= 1024**2 for v in c.values()) or
                c["pending"] != 0 or c["closed"] != c["arrived"] or not 1 <= c["arrived"] <= MAX_STAGE_CONNECTIONS):
            return False
        mode, generations = STAGE_SPECS[name]
        if c["generation"] != generations:
            return False
        if mode == "tls":
            if (c["hello"] != c["arrived"] or c["alert"] != c["hello"] or c["page"] != 0 or
                    c["redirect"] != 0 or c["client_cancelled"] != 0 or c["response_bytes"] != 7 * c["alert"] or
                    c["compat_ccs"] > c["hello"]):
                return False
        elif mode == "hold":
            if (c["arrived"] != 1 or c["client_cancelled"] != 1 or c["response_bytes"] != 0 or
                    any(c[k] for k in ("page", "redirect", "hello", "alert", "compat_ccs"))):
                return False
        elif mode == "page":
            if (c["arrived"] != generations or c["page"] != generations or c["response_bytes"] <= 0 or
                    any(c[k] for k in ("redirect", "hello", "alert", "client_cancelled", "compat_ccs"))):
                return False
        elif mode == "redirect":
            if (c["arrived"] != 1 or c["redirect"] != 1 or c["response_bytes"] <= 0 or
                    any(c[k] for k in ("page", "hello", "alert", "client_cancelled", "compat_ccs"))):
                return False
    return True


class RequestFixture:
    def __init__(self, root: Path, bundle_id: str, signed_hash: str, plist_hash: str):
        if not BUNDLE.fullmatch(bundle_id) or not all(HEX64.fullmatch(v) for v in (signed_hash, plist_hash)):
            raise ValueError("Owned installed application identities are required")
        self.root = root
        self.token = uuid.uuid4().hex
        self.bundle_id, self.signed_hash, self.plist_hash = bundle_id, signed_hash, plist_hash
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.listeners = []
        self.threads = []
        self.connections = set()
        self.stages = {}
        self.gates = {}
        self.active_tls = None
        self.pid = None
        self.claims = 0
        self.completed = set()
        self.errors = set()
        self.work = self.connections_started = self.connections_closed = 0
        self.started = self.closed = False
        self.receipt = {}

    def prepare(self) -> dict:
        if self.started or self.closed:
            raise ValueError("Exactly one fresh owned request fixture is allowed")
        # Register each acquired descriptor immediately, even if a later bind/start fails.
        for _ in range(2):
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listeners.append(listener)
            listener.bind(("127.0.0.1", 0))
            listener.listen(8)
            listener.settimeout(0.1)
            if listener.getsockname()[0] != "127.0.0.1":
                raise ValueError("The fixture must bind only the owned IPv4 loopback")
        self.http_port, self.tls_port = (s.getsockname()[1] for s in self.listeners)
        if self.http_port == self.tls_port:
            raise ValueError("Independent HTTP/TLS ports are required")
        environment = os.environ.copy()
        requested = {"NATIVECMPKIT_WEBVIEW_REQUEST_TOKEN": self.token,
                     "NATIVECMPKIT_WEBVIEW_REQUEST_HTTP_PORT": str(self.http_port),
                     "NATIVECMPKIT_WEBVIEW_REQUEST_TLS_PORT": str(self.tls_port)}
        for name, value in requested.items():
            key = "SIMCTL_CHILD_" + name
            if environment.get(key) not in (None, value):
                raise ValueError("Inherited request-fixture selector conflicts with this owned attempt")
            environment[key] = value
        for listener, tls in zip(self.listeners, (False, True)):
            thread = threading.Thread(target=self._accept, args=(listener, tls), daemon=False)
            self.threads.append(thread)
            thread.start()
        self.started = True
        return environment  # Process-local launch environment only; never mutate os.environ.

    def _error(self, reason: str):
        with self.lock:
            self.errors.add(reason)  # Fixed reason IDs only, no peer/request/NSError text.

    def _charge(self):
        with self.lock:
            self.work += 1
            if self.work > MAX_WORK:
                raise ValueError("Owned request work budget exceeded")

    def _accept(self, listener, tls):
        while not self.stop.is_set():
            try:
                conn, address = listener.accept()
            except socket.timeout:
                continue
            except OSError:
                if not self.stop.is_set(): self._error("listener-refused")
                break
            with self.lock:
                if len(self.connections) >= MAX_CONNECTIONS or self.connections_started >= MAX_WORK:
                    conn.close(); self.errors.add("connection-budget"); continue
                self.connections.add(conn)
                self.connections_started += 1
                thread = threading.Thread(target=self._serve, args=(conn, address, tls), daemon=False)
                self.threads.append(thread)
            try:
                thread.start()
            except RuntimeError:
                self._error("worker-start-refused")
                conn.close()
                with self.lock:
                    self.connections.discard(conn)
                    self.connections_closed += 1

    def _serve(self, conn, address, tls):
        try:
            conn.settimeout(2.0)
            if address[0] != "127.0.0.1":
                raise ValueError("Foreign non-loopback peer")
            if tls:
                self._tls(conn)
            else:
                owner = self
                class Handler(BaseHTTPRequestHandler):
                    protocol_version = "HTTP/1.1"
                    def log_message(self, *args): pass
                    def do_GET(self): owner._http(self)
                    def do_POST(self): owner._error("unreviewed-method"); self.send_error(405)
                Handler(conn, address, self)
        except (OSError, ValueError, RuntimeError):
            if not self.stop.is_set(): self._error("connection-refused")
        finally:
            try:
                conn.close()
            except OSError:
                self._error("connection-close-refused")
            with self.lock:
                self.connections.discard(conn)
                self.connections_closed += 1

    def _snapshot(self, stage):
        with self.lock:
            if stage not in self.stages: raise ValueError("Unknown unarmed stage")
            return dict(self.stages[stage])

    def _control(self, action, value):
        self._charge()
        with self.lock:
            if action == "claim":
                pid = int(value)
                if self.claims >= 2 or self.pid not in (None, pid): raise ValueError("Native request claim identity changed")
                self.pid = pid; self.claims += 1
                return {"pid": pid}
            if self.pid is None: raise ValueError("Native owned PID claim is required")
            if action == "arm":
                mode, limit = STAGE_SPECS[value]
                counters = self.stages.setdefault(value, zero_counters())
                if counters["pending"] or counters["generation"] >= limit:
                    raise ValueError("Refuse active duplicate or excessive stage arm")
                if counters["generation"] and not self.gates[value].is_set():
                    raise ValueError("Prior stage lease was not released")
                if mode == "tls" and self.active_tls is not None and self.stages[self.active_tls]["pending"]:
                    raise ValueError("Another TLS stage is still active")
                counters["generation"] += 1
                self.gates[value] = threading.Event()
                if mode == "tls": self.active_tls = value
                return {"armed": 1}
            if action == "release":
                c = self.stages.get(value)
                if (c is None or c["arrived"] == 0 or self.gates[value].is_set() or
                        STAGE_SPECS[value][0] in {"hold", "redirect"}):
                    raise ValueError("Refuse unknown duplicate or forbidden release")
                self.gates[value].set()
                return {"released": 1}
            if action == "stats": return self._snapshot(value)
            if action == "done":
                if value in self.completed or not complete_stages(self.stages, value):
                    raise ValueError("Native workload has missing transport or cancellation evidence")
                self.completed.add(value)
                return {"done": 1}
        raise ValueError("Unreviewed request control")

    def _arrive(self, stage, expected):
        self._charge()
        with self.lock:
            if (self.pid is None or stage not in self.stages or STAGE_SPECS[stage][0] not in expected or
                    self.stages[stage]["arrived"] >= MAX_STAGE_CONNECTIONS):
                raise ValueError("Unarmed foreign or excessive stage connection")
            c = self.stages[stage]
            c["arrived"] += 1; c["pending"] += 1
            return self.gates[stage], c["generation"]

    def _finish(self, stage):
        with self.lock:
            self.stages[stage]["pending"] -= 1
            self.stages[stage]["closed"] += 1

    def _wait(self, conn, gate, stage, *, tls=False):
        compatibility_ccs = False
        deadline = time.monotonic() + GATE_SECONDS
        while not self.stop.is_set():
            if gate.is_set(): return True
            readable, _, _ = select.select([conn], [], [], 0.01)
            if readable:
                if conn.recv(1, socket.MSG_PEEK) == b"":
                    with self.lock: self.stages[stage]["client_cancelled"] += 1
                    return False  # Actual native client EOF, never host teardown/release.
                if tls and not compatibility_ccs:
                    # TLS1.3 compatibility mode may send one dummy CCS after its
                    # ClientHello (RFC8446 appendixD.4). No arbitrary TLS/data input.
                    record = bytearray()
                    while len(record) < 6:
                        chunk = conn.recv(6 - len(record))
                        if not chunk: raise ValueError("Partial TLS compatibility CCS")
                        record.extend(chunk)
                    if bytes(record) != bytes.fromhex("14 03 03 00 01 01"):
                        raise ValueError("Unreviewed extra TLS record before refusal")
                    compatibility_ccs = True
                    with self.lock: self.stages[stage]["compat_ccs"] += 1
                else:
                    raise ValueError("Unexpected bytes while the owned response is held")
            if time.monotonic() >= deadline:
                raise ValueError("An unreleased native request gate expired")
        return False  # Cleanup is deliberately not counted as client cancellation.

    def _http(self, handler):
        try:
            if len(handler.headers) > 32 or sum(len(k) + len(v) for k, v in handler.headers.items()) > 8192:
                raise ValueError("Unbounded request headers")
            kind, action, stage = parse_route(handler.path, self.token)
            if kind == "control":
                counters = self._control(action, stage)
                body = "".join(f"{k}={v}\n" for k, v in sorted(counters.items())).encode("ascii")
                handler.send_response(200)
                handler.send_header("Content-Type", "text/plain; charset=ascii")
                handler.send_header("Content-Length", str(len(body)))
                handler.send_header("Cache-Control", "no-store")
                handler.send_header("Connection", "close")
                handler.end_headers(); handler.wfile.write(body)
                handler.close_connection = True
                return
            gate, generation = self._arrive(stage, {"page", "redirect", "hold"})
            try:
                mode = STAGE_SPECS[stage][0]
                if mode != "redirect" and not self._wait(handler.connection, gate, stage): return
                if mode == "hold": raise ValueError("Held response must never be manually released")
                if mode == "redirect":
                    body = b""
                    location = f"http://localhost:{self.http_port}/{self.token}/page/matrix-final"
                    handler.send_response(302); handler.send_header("Location", location)
                    key = "redirect"
                else:
                    title = f"{stage}-{generation}"
                    body = ("<!doctype html><meta charset='utf-8'><link rel='icon' href='data:,'>" +
                            f"<title>{title}</title><p id='nativecmpkit-request'>{title}</p>" +
                            f"<a id='nativecmpkit-tls-two' href='https://localhost:{self.tls_port}/{self.token}/page/tls-two'>TLS</a>" +
                            f"<a id='nativecmpkit-redirect' href='http://localhost:{self.http_port}/{self.token}/page/matrix-redirect'>redirect</a>").encode("utf-8")
                    handler.send_response(200); key = "page"
                handler.send_header("Content-Type", "text/html; charset=utf-8")
                handler.send_header("Content-Length", str(len(body)))
                handler.send_header("Cache-Control", "no-store")
                handler.send_header("Connection", "close")
                # Actual header/body bytes are counted, not inferred from the status.
                response_size = framed_response_bytes(handler._headers_buffer, body)
                handler.end_headers(); handler.wfile.write(body); handler.wfile.flush()
                with self.lock:
                    self.stages[stage][key] += 1
                    self.stages[stage]["response_bytes"] += response_size
                handler.close_connection = True
            finally:
                self._finish(stage)
        except (OSError, ValueError, RuntimeError):
            self._error("http-contract-refused")
            handler.close_connection = True
            # Do not serialize error/body/request text into native output.

    def _tls(self, conn):
        with self.lock:
            stage = self.active_tls
            if stage is None: raise ValueError("TLS is not armed by the owned app")
        gate, _ = self._arrive(stage, {"tls"})
        def read_exact(size):
            out = bytearray()
            while len(out) < size:
                chunk = conn.recv(size - len(out))
                if not chunk: raise ValueError("Partial native ClientHello")
                out.extend(chunk)
            return bytes(out)
        try:
            header = read_exact(5)
            size = int.from_bytes(header[3:5], "big")
            if not 4 <= size <= 16384: raise ValueError("Unbounded native ClientHello")
            payload = read_exact(size)
            if not client_hello_record(header, payload): raise ValueError("Actual TLS ClientHello is missing")
            with self.lock: self.stages[stage]["hello"] += 1
            if not self._wait(conn, gate, stage, tls=True): return
            conn.sendall(TLS_FATAL_HANDSHAKE_FAILURE)
            with self.lock:
                self.stages[stage]["alert"] += 1
                self.stages[stage]["response_bytes"] += len(TLS_FATAL_HANDSHAKE_FAILURE)
            # Close only this accepted owned transport; never another process or listener.
            conn.shutdown(socket.SHUT_WR)
        finally:
            self._finish(stage)

    def close(self):
        if self.closed: return
        self.stop.set()
        listeners_closed = True
        for listener in self.listeners:
            try: listener.close()
            except OSError: listeners_closed = False
        # These exact object references were accepted by our listeners. No guessed
        # OS PID/group kill, global server shutdown, DNS or simulator setting exists.
        with self.lock: active = list(self.connections)
        for conn in active:
            try: conn.shutdown(socket.SHUT_RDWR)
            except OSError: pass  # EOF/already-closed sockets still require the owned worker to finish.
        deadline = time.monotonic() + JOIN_SECONDS
        # Acceptors may register a final worker while stop is being observed.
        while True:
            with self.lock: threads = list(self.threads)
            for thread in threads:
                if thread.ident is not None and thread is not threading.current_thread():
                    thread.join(max(0.0, deadline - time.monotonic()))
            with self.lock:
                if len(threads) == len(self.threads): break
            if time.monotonic() >= deadline: break
        with self.lock:
            self.closed = True
            self.receipt = {
                "schema_version": 1, "kind": "owned-localhost-wk-request-transport", "prepared": self.started,
                "bundle_id": self.bundle_id, "signed_application_executable_sha256": self.signed_hash,
                "application_plist_sha256": self.plist_hash,
                "fixture_source_sha256": hashlib.sha256((self.root / SOURCE).read_bytes()).hexdigest(),
                "native_source_sha256": hashlib.sha256((self.root / NATIVE_SOURCE).read_bytes()).hexdigest(),
                "token_sha256": hashlib.sha256(self.token.encode("ascii")).hexdigest(),
                "native_process_id": self.pid, "native_claims": self.claims,
                "work": self.work, "connections_started": self.connections_started, "connections_closed": self.connections_closed,
                "completed_methods": sorted(self.completed), "stages": {k: dict(v) for k, v in self.stages.items()},
                "errors": sorted(self.errors), "local_loopback_only": True,
                "tls_certificate_private_key_or_trust_bypass": False, "dns_or_system_offline_verified": False,
                "cleanup": {"owned_listeners_closed": listeners_closed,
                            "owned_connections_closed": not self.connections and self.connections_started == self.connections_closed,
                            "owned_threads_terminated": all(not t.is_alive() for t in self.threads),
                            "launch_environment_process_local_only": True},
            }


def validate_receipt(document: dict, *, bundle_id: str, signed_hash: str, plist_hash: str,
                     native_pid: int, fixture_hash: str, native_hash: str) -> bool:
    """Cross-check this exact native workload's transport, never generate native results."""
    try:
        d = document
        fields = {"schema_version", "kind", "prepared", "bundle_id", "signed_application_executable_sha256",
                  "application_plist_sha256", "fixture_source_sha256", "native_source_sha256", "token_sha256",
                  "native_process_id", "native_claims", "work", "connections_started", "connections_closed",
                  "completed_methods", "stages", "errors", "local_loopback_only",
                  "tls_certificate_private_key_or_trust_bypass", "dns_or_system_offline_verified", "cleanup"}
        return (isinstance(d, dict) and set(d) == fields and type(d.get("schema_version")) is int and d["schema_version"] == 1 and
                d.get("kind") == "owned-localhost-wk-request-transport" and d.get("prepared") is True and
                d.get("bundle_id") == bundle_id and BUNDLE.fullmatch(bundle_id) is not None and
                d.get("signed_application_executable_sha256") == signed_hash and
                d.get("application_plist_sha256") == plist_hash and
                d.get("fixture_source_sha256") == fixture_hash and d.get("native_source_sha256") == native_hash and
                all(isinstance(v, str) and HEX64.fullmatch(v) for v in (signed_hash, plist_hash, fixture_hash, native_hash, d.get("token_sha256"))) and
                type(native_pid) is int and 0 < native_pid < 2**31 and type(d.get("native_process_id")) is int and d["native_process_id"] == native_pid and
                type(d.get("native_claims")) is int and d["native_claims"] == 2 and
                type(d.get("work")) is int and 0 < d["work"] <= MAX_WORK and
                all(type(d.get(k)) is int and 0 < d[k] <= MAX_WORK for k in ("connections_started", "connections_closed")) and
                d["connections_started"] == d["connections_closed"] and d.get("completed_methods") == sorted(METHOD_KEYS) and
                d.get("errors") == [] and d.get("local_loopback_only") is True and
                d.get("tls_certificate_private_key_or_trust_bypass") is False and d.get("dns_or_system_offline_verified") is False and
                d.get("cleanup") == {"owned_listeners_closed": True, "owned_connections_closed": True,
                                     "owned_threads_terminated": True, "launch_environment_process_local_only": True} and
                isinstance(d.get("stages"), dict) and set(d["stages"]) == set(STAGE_SPECS) and
                all(complete_stages(d["stages"], method) for method in METHOD_KEYS))
    except (ValueError, TypeError, KeyError):
        return False
