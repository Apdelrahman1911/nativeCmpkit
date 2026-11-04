#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""NEW cookie-only native HTTP(S) fixture. Source/model controls are NOT native acceptance.

The owning controller provides fresh DNS aliases, ephemeral matching certificate
material and actual process/application custody. This module never edits hosts,
system/simulator trust, ATS or production settings. Loopback requests use normal
DNS/TLS and expose only fixed count vectors; raw Cookie/Host bytes are not logged.
"""
from __future__ import annotations

import concurrent.futures
import copy
import dataclasses
import hashlib
import json
from pathlib import Path
import plistlib
import re
import socket
import ssl
import threading
import time

from webview_content_policy_fixture import FixtureRefusal, Request, read_request


SPEC_SHA256 = "7b675f4ac252be68dd2c690be90d9c97555308305bf479cdbcaf6914158d16ad"
TOKEN = re.compile(r"[0-9a-f]{32}\Z")
PID = re.compile(r"[1-9][0-9]{0,9}\Z")
UUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")
SELECTORS = {
    "desktop": "com.mohamedrejeb.calf.ui.web.DesktopCookieWireAcceptanceTest.realJavaFxScopedCookieHeadersKeepNativeMultiplicityAcrossHttpAndTrustedHttps",
    "ios": "com.mohamedrejeb.calf.ui.web.IosCookieWireAcceptanceTest.realWkScopedCookieHeadersKeepNativeMultiplicityAcrossHttpAndTrustedHttps",
}
COMMON_SOURCES = (
    "scripts/ci/cookie_native_wire_fixture.py",
    "scripts/ci/cookie_wire_material.py",
    "scripts/ci/fixtures/cookie-wire-v1.json",
    "calf-webview/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/web/CookieWireContract.kt",
    "calf-webview/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/web/NativeCookieWireScenario.kt",
    "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieRules.kt",
    "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/Cookie.kt",
    "gradle/libs.versions.toml",
)
PLATFORM_SOURCES = {
    "desktop": (
        "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt",
        "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopCookieWireAcceptanceTest.kt",
        "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopCookieWireFixture.kt",
    ),
    "ios": (
        "calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt",
        "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosCookieWireAcceptanceTest.kt",
        "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosCookieWireFixture.kt",
    ),
}


def digest(path: Path, limit: int = 2**30) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise FixtureRefusal("Missing exact regular owned input file")
    result = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(65536):
            result.update(block)
    return result.hexdigest()


def load_specification(path: Path) -> dict:
    if not path.is_absolute() or path.name != "cookie-wire-v1.json" or digest(path, 8192) != SPEC_SHA256:
        raise FixtureRefusal("Missing exact reviewed cookie-wire specification")
    return json.loads(path.read_text(encoding="utf-8"))


def observed_vector(spec: dict, token: str, raw: str) -> list[int]:
    """Count every ACTUAL inbound occurrence; never reduce same-name/path pairs to a map."""
    if not TOKEN.fullmatch(token) or not isinstance(raw, str):
        raise FixtureRefusal("Unreviewed owned cookie header domain")
    try: header_bytes = raw.encode("ascii")
    except UnicodeError: raise FixtureRefusal("Unreviewed owned cookie header byte") from None
    if len(header_bytes) > 8192:
        raise FixtureRefusal("Unreviewed owned cookie header domain")
    counts = [0] * len(spec["groups"])
    own = f"nativecmpkit_{token}_"
    for part in raw.split(";"):
        name, equal, value = part.strip().partition("=")
        if not equal or not name.startswith(own):
            continue
        identity = [name.removeprefix(own), value]
        if identity not in spec["groups"]:
            raise FixtureRefusal("Unexpected owned cookie identity or value")
        index = spec["groups"].index(identity)
        counts[index] += 1
        if counts[index] > 3:
            raise FixtureRefusal("Owned cookie occurrence budget exceeded")
    return counts


def set_cookie(spec: dict, token: str, root_host: str, item: dict, remove: bool = False) -> str:
    if not TOKEN.fullmatch(token) or root_host != f"r{token}.nativecmpkit.test":
        raise FixtureRefusal("Unowned native cookie definition")
    name, value = spec["groups"][item["group"]]
    header = f"nativecmpkit_{token}_{name}={'' if remove else value}; Path={spec['namespace']}{token}/{item['path']}"
    if item.get("domain"):
        header += f"; Domain=.{root_host}"
    if remove or item.get("past"):
        header += "; Expires=Thu, 01 Jan 1970 00:00:00 GMT"
    elif item.get("future"):
        header += "; Expires=Fri, 01 Jan 2100 00:00:00 GMT"
    if item.get("http_only"):
        header += "; HttpOnly"
    if item.get("secure"):
        header += "; Secure"
    return header


def http_response(body: str, cookies: tuple[str, ...] = (), html: bool = False, status: int = 200) -> bytes:
    payload = body.encode("ascii")
    if len(payload) > 2048 or len(cookies) > 16 or any("\r" in item or "\n" in item for item in cookies):
        raise FixtureRefusal("Owned response exceeds its fixed budget")
    mime = "text/html; charset=utf-8" if html else "text/plain; charset=ascii"
    header = (f"HTTP/1.1 {status} Fixture\r\nContent-Type: {mime}\r\nContent-Length: {len(payload)}\r\n"
              "Connection: close\r\nCache-Control: no-store, no-cache, max-age=0\r\n")
    return (header + "".join(f"Set-Cookie: {item}\r\n" for item in cookies) + "\r\n").encode("ascii") + payload


def native_page(spec: dict, token: str, stage: str, number: int, vector: list[int]) -> str:
    """Only numeric wire/actual document-cookie observations leave the native document."""
    groups = json.dumps(spec["groups"], separators=(",", ":"))
    prefix = json.dumps(f"nativecmpkit_{token}_")
    script = ("(function(){var groups=" + groups + ",prefix=" + prefix + ",counts=groups.map(function(){return 0;});"
              "var refused=false;document.cookie.split(';').forEach(function(part){var text=part.trim(),at=text.indexOf('=');"
              "if(at<=0||text.slice(0,at).indexOf(prefix)!==0)return;var suffix=text.slice(prefix.length,at),value=text.slice(at+1);"
              "var i=groups.findIndex(function(pair){return pair[0]===suffix&&pair[1]===value;});"
              "if(i<0)refused=true;else if(++counts[i]>3)refused=true;});"
              "document.getElementById('cookie-visible').textContent=refused?'refused':counts.join(',');})();")
    return (f"<!doctype html><meta charset='utf-8'><link rel='icon' href='data:,'><title>cookie-{stage}-{number}</title>"
            f"<p id='cookie-wire'>{','.join(map(str, vector))}</p><p id='cookie-visible'></p><script>{script}</script>")


@dataclasses.dataclass(frozen=True)
class CookieReply:
    payload: bytes
    stage: str | None = None


class CookieWireProtocol:
    """Pure finite protocol; construction and model controls allocate NO sockets/keys/trust."""
    def __init__(self, spec: dict, token: str, http_port: int, https_port: int, clock=time.monotonic):
        if not TOKEN.fullmatch(token) or type(http_port) is not int or type(https_port) is not int or not (
                0 < http_port <= 65535 and 0 < https_port <= 65535 and http_port != https_port):
            raise FixtureRefusal("Missing exact owned native cookie endpoints")
        self.spec, self.token, self.clock = spec, token, clock
        self.root_host = f"r{token}.nativecmpkit.test"
        self.ports = (http_port, https_port)
        self.prefix = f"{spec['namespace']}{token}/"
        self.bound = False
        self.process: int | None = None
        self.started: float | None = None
        self.done = self.seeded = self.logout = False
        self.error = self.calls = self.pending = 0
        self.stages = {self.stage(page, subhost, secure): {"requests": 0, "closed": 0, "vectors": []}
                       for secure in (False, True) for subhost, pages in ((False, spec["paths"]), (True, ("foo", "public")))
                       for page in pages}

    @staticmethod
    def stage(page: str, subhost: bool, secure: bool) -> str:
        return f"{'https' if secure else 'http'}-{'sub' if subhost else 'root'}-{page.replace('/', '-')}"

    def route(self, request: Request, secure: bool) -> CookieReply:
        self.calls += 1
        if not self.bound or self.done or self.calls > 128 or (self.started is not None and self.clock() - self.started >= 180):
            raise FixtureRefusal("Native cookie lifetime, binding or replay admission refused")
        if request.method != "GET" or request.body or not request.path.startswith(self.prefix):
            raise FixtureRefusal("Unowned native cookie method or route")
        host = request.headers.get("host", "")
        parts = request.path.removeprefix(self.prefix).split("/")
        port = self.ports[int(secure)]
        if parts[0] == "control":
            if secure or host not in (f"localhost:{port}", f"127.0.0.1:{port}") or len(parts) != 3 or not PID.fullmatch(parts[2]):
                raise FixtureRefusal("Missing exact loopback native process control")
            action, pid = parts[1], int(parts[2])
            if pid >= 2**31:
                raise FixtureRefusal("Native process claim exceeds canonical PID domain")
            if action == "open":
                if self.process is not None:
                    raise FixtureRefusal("Never replay an owned native cookie process")
                self.process, self.started = pid, self.clock()
            elif self.process != pid:
                raise FixtureRefusal("Foreign native cookie process claim")
            elif action == "done":
                if self.error or self.pending or not self.seeded or not self.logout or any(
                        row["requests"] != (6 if stage == "https-root-foo-child" else 2) or row["closed"] != row["requests"]
                        for stage, row in self.stages.items()):
                    raise FixtureRefusal("Actual native cookie stages were incomplete or failed")
                self.done = True
            elif action != "stats":
                raise FixtureRefusal("Unknown finite native cookie control")
            body = f"{action}=1\npid={pid}\nfixture_error={self.error}\npending={self.pending}\n"
            return CookieReply(http_response(body))
        if self.process is None or "origin" in request.headers:
            raise FixtureRefusal("Unclaimed native cookie page or foreign Origin")
        if host not in (f"{self.root_host}:{port}", f"sub.{self.root_host}:{port}"):
            raise FixtureRefusal("Native Host does not match the actual owned endpoint")
        subhost = host.startswith("sub.")
        page = "/".join(parts)
        if page in ("seed", "logout"):
            if not secure or subhost or (page == "seed" and self.seeded) or (page == "logout" and (not self.seeded or self.logout)):
                raise FixtureRefusal("Seed/logout must be one actual owned TLS-root request")
            if page == "seed":
                self.seeded = True
            else:
                self.logout = True
            cookies = tuple(set_cookie(self.spec, self.token, self.root_host, entry, page == "logout")
                            for entry in self.spec["cookies"] if page == "logout" or not entry.get("managed"))
            return CookieReply(http_response(native_page(self.spec, self.token, page, 1, [0] * 12), cookies, html=True))
        stage = self.stage(page, subhost, secure)
        if not self.seeded or stage not in self.stages or self.stages[stage]["requests"] >= 6:
            raise FixtureRefusal("Unreviewed or repeated native cookie page stage")
        vector = observed_vector(self.spec, self.token, request.headers.get("cookie", ""))
        row = self.stages[stage]
        row["requests"] += 1
        row["vectors"].append(vector)
        self.pending += 1
        return CookieReply(http_response(native_page(self.spec, self.token, stage, row["requests"], vector), html=True), stage)

    def finish(self, stage: str | None, success: bool) -> None:
        if not success:
            self.error += 1
        if stage is not None:
            if stage not in self.stages or self.pending <= 0 or self.stages[stage]["closed"] >= self.stages[stage]["requests"]:
                raise FixtureRefusal("Native response ownership was released twice or not admitted")
            self.stages[stage]["closed"] += 1
            self.pending -= 1


@dataclasses.dataclass(eq=False)
class PeerLease:
    peer: socket.socket


class OwnedCookieNativeWireFixture:
    """The lead owns startup/binding/trust; this lease owns ONLY its two listeners and accepted peers/workers."""
    def __init__(self, *, root: Path, token: str, certificate: Path, private_key: Path, trust_anchor: Path):
        if not TOKEN.fullmatch(token):
            raise FixtureRefusal("A fresh 128-bit native cookie nonce is required")
        self.root, self.token = root.resolve(), token
        self.spec = load_specification(self.root / "scripts/ci/fixtures/cookie-wire-v1.json")
        material_paths = (certificate, private_key, trust_anchor)
        if (any(not path.is_absolute() or path.is_relative_to(self.root) for path in material_paths) or
                len({path.parent for path in material_paths}) != 1 or
                not private_key.parent.name.startswith(f"nativecmpkit-cookie-wire-{token}-") or
                [path.name for path in material_paths] != ["server.pem", "server.key", "ca.pem"]):
            raise FixtureRefusal("Native cookie material must remain in one exact uncommitted ephemeral directory")
        self.certificate, self.private_key, self.trust_anchor = certificate, private_key, trust_anchor
        self.material_hashes = {"certificate_sha256": digest(certificate, 16384), "trust_anchor_sha256": digest(trust_anchor, 16384)}
        digest(private_key, 16384)  # Checked but never exported, retained, or read into a receipt.
        self._lock = threading.RLock()
        self._closing = threading.Event()
        self._closed = self._workers_terminated = False
        self._listeners: list[socket.socket] = []
        self._threads: list[threading.Thread] = []
        self._peers: set[PeerLease] = set()
        self._workers: concurrent.futures.ThreadPoolExecutor | None = None
        self._admission = threading.BoundedSemaphore(8)
        self._failure: BaseException | None = None
        self._accepted = self._refusals = 0
        self._binding: dict | None = None
        self._environment_issued = False
        self.protocol: CookieWireProtocol | None = None

    def start(self) -> None:
        if self.protocol is not None or self._closing.is_set():
            raise FixtureRefusal("Never replay an owned native listener startup")
        # Actual DNS lookup only at owning runtime startup, never model construction.
        for host in self.hosts:
            answers = socket.getaddrinfo(host, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
            if not answers or {answer[4][0] for answer in answers} != {"127.0.0.1"}:
                raise FixtureRefusal("Owned cookie DNS aliases must resolve only to their loopback lease")
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        tls.load_cert_chain(str(self.certificate), str(self.private_key))
        self._workers = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="owned-native-cookie")
        try:
            for _ in range(2):
                listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._listeners.append(listener)
                listener.bind(("127.0.0.1", 0)); listener.listen(8); listener.settimeout(0.1)
            self.protocol = CookieWireProtocol(self.spec, self.token, *(listener.getsockname()[1] for listener in self._listeners))
            for secure, listener in enumerate(self._listeners):
                thread = threading.Thread(target=self._accept, args=(listener, bool(secure), tls), daemon=True,
                                          name=f"owned-native-cookie-{'https' if secure else 'http'}")
                self._threads.append(thread); thread.start()
        except BaseException as primary:
            try: self.close()
            except BaseException as cleanup: primary.add_note(f"Independent cookie startup cleanup failed: {type(cleanup).__name__}")
            raise

    @property
    def hosts(self) -> tuple[str, str]:
        root = f"r{self.token}.nativecmpkit.test"
        return root, f"sub.{root}"

    @property
    def ats_domains(self) -> dict:
        # Exact test-only exceptions, no global arbitrary-load or includes-subdomains switch.
        return {host: {"NSExceptionAllowsInsecureHTTPLoads": True, "NSIncludesSubdomains": False} for host in self.hosts}

    def bind_native(self, *, platform: str, binary: Path, plist: Path | None = None,
                    bundle_id: str | None = None, simulator_id: str | None = None) -> None:
        if platform not in SELECTORS or self.protocol is None or self._binding is not None or self._accepted:
            raise FixtureRefusal("Missing finite original native cookie binding")
        inputs = {name: digest(self.root / name) for name in (*COMMON_SOURCES, *PLATFORM_SOURCES[platform])}
        binding = {"platform": platform, "selector": SELECTORS[platform], "binary_sha256": digest(binary), "inputs": inputs}
        if platform == "ios":
            if (plist is None or simulator_id is None or not UUID.fullmatch(simulator_id) or bundle_id is None or
                    not re.fullmatch(r"io\.github\.apdelrahman1911\.nativecmpkit\.verification\.ui\.r[0-9a-f]{12}\.t[0-9a-f]{32}", bundle_id)):
                raise FixtureRefusal("Missing actual owned cookie application/simulator identity")
            plist_hash = digest(plist, 16384)
            document = plistlib.loads(plist.read_bytes())
            ats = document.get("NSAppTransportSecurity")
            if (document.get("CFBundleIdentifier") != bundle_id or not isinstance(ats, dict) or
                    ats != {"NSAllowsLocalNetworking": True, "NSExceptionDomains": self.ats_domains}):
                raise FixtureRefusal("Cookie ATS must contain only local networking and the exact two owned domains")
            binding.update({"plist_sha256": plist_hash, "bundle_id": bundle_id, "simulator_id_sha256": hashlib.sha256(simulator_id.encode("ascii")).hexdigest()})
        elif any(value is not None for value in (plist, bundle_id, simulator_id)):
            raise FixtureRefusal("Desktop cookie binding must not borrow an Apple application")
        self._binding = binding

    def launch_environment(self) -> dict[str, str]:
        if self._binding is None or self.protocol is None or self._environment_issued or self._accepted:
            raise FixtureRefusal("Native cookie handoff requires a fresh bound original invocation")
        self._environment_issued = True
        self.protocol.bound = True
        result = {"NATIVECMPKIT_COOKIE_WIRE_TOKEN": self.token, "NATIVECMPKIT_COOKIE_WIRE_HOST": self.hosts[0],
                  "NATIVECMPKIT_COOKIE_WIRE_HTTP_PORT": str(self.protocol.ports[0]),
                  "NATIVECMPKIT_COOKIE_WIRE_HTTPS_PORT": str(self.protocol.ports[1]),
                  "NATIVECMPKIT_COOKIE_WIRE_SELECTOR": self._binding["selector"]}
        if self._binding["platform"] == "desktop":
            result.update({"NATIVECMPKIT_COOKIE_WIRE_CA": str(self.trust_anchor),
                           "NATIVECMPKIT_COOKIE_WIRE_CA_SHA256": self.material_hashes["trust_anchor_sha256"]})
        return result  # Private process-local handoff, never an evidence/log/notification record.

    def _accept(self, listener: socket.socket, secure: bool, tls: ssl.SSLContext) -> None:
        while not self._closing.is_set():
            try: peer, address = listener.accept()
            except socket.timeout: continue
            except OSError as error:
                if not self._closing.is_set(): self._fail(error)
                return
            with self._lock:
                self._accepted += 1
                allowed = address[0] == "127.0.0.1" and self._accepted <= 128 and self._admission.acquire(blocking=False)
                if not allowed:
                    self._refusals += 1; peer.close(); self._fail(FixtureRefusal("Owned cookie socket admission refused")); continue
                lease = PeerLease(peer); self._peers.add(lease)
            try:
                assert self._workers is not None
                self._workers.submit(self._respond, lease, secure, tls)
            except BaseException as error:
                with self._lock: self._peers.discard(lease)
                peer.close(); self._admission.release(); self._fail(error)

    def _respond(self, lease: PeerLease, secure: bool, tls: ssl.SSLContext) -> None:
        reply: CookieReply | None = None
        success = False
        try:
            lease.peer.settimeout(3.0)
            if secure:
                with self._lock:
                    # Handshake occurs OUTSIDE the lock; cleanup still owns the wrapped peer.
                    lease.peer = tls.wrap_socket(lease.peer, server_side=True, do_handshake_on_connect=False)
                lease.peer.do_handshake()
            request = read_request(lease.peer)
            with self._lock:
                assert self.protocol is not None
                reply = self.protocol.route(request, secure)
            lease.peer.sendall(reply.payload)
            success = True
        except BaseException as error:
            if not self._closing.is_set(): self._fail(error)
            try: lease.peer.sendall(http_response("cookie-native-refused", status=409))
            except OSError: pass
        finally:
            try:
                lease.peer.close()
            except BaseException as error:
                success = False; self._fail(error)
            with self._lock:
                if self.protocol is not None and reply is not None:
                    try: self.protocol.finish(reply.stage, success)
                    except BaseException as error: self._fail(error)
                self._peers.discard(lease)
            self._admission.release()

    def _fail(self, error: BaseException) -> None:
        with self._lock:
            if self._failure is None: self._failure = error
            if self.protocol is not None: self.protocol.error += 1

    def close(self) -> None:
        if self._closed:
            if self._failure is not None: raise FixtureRefusal("Owned cookie fixture retained its original failure") from self._failure
            return
        self._closed = True; self._closing.set()
        errors: list[BaseException] = []
        def stage(action) -> None:
            try: action()
            except BaseException as error: errors.append(error)
        for listener in self._listeners: stage(listener.close)
        with self._lock: peers = list(self._peers)
        for lease in peers:
            def dispose(lease=lease):
                try: lease.peer.shutdown(socket.SHUT_RDWR)
                except OSError: pass  # Close below is independent and mandatory; not a native success verdict.
                lease.peer.close()
            stage(dispose)
        for thread in self._threads:
            stage(lambda thread=thread: thread.join(5.0))
            if thread.is_alive(): errors.append(FixtureRefusal("Owned cookie accept thread remains alive"))
        if self._workers is not None:
            # All accepted peers have a bounded read/handshake and were closed above;
            # wait until every actually admitted worker releases its own socket lease.
            stage(lambda: self._workers.shutdown(wait=True, cancel_futures=False))
        self._workers_terminated = not self._peers and all(not thread.is_alive() for thread in self._threads)
        if not self._workers_terminated: errors.append(FixtureRefusal("Owned cookie workers or peers remain live"))
        if self._failure is not None: errors.insert(0, self._failure)
        if errors:
            self._failure = errors[0]
            failure = FixtureRefusal("Independent owned cookie fixture cleanup retained a failure")
            for error in errors: failure.add_note(type(error).__name__)
            # The original remains held privately. Public cleanup errors never
            # interpolate raw request/handshake exceptions or their byte payloads.
            raise failure from None

    def receipt(self) -> dict:
        if self.protocol is None:
            raise FixtureRefusal("No actual native cookie fixture was started")
        with self._lock:
            return {"schema_version": 1, "kind": "owned-native-cookie-wire-v1", "specification_sha256": SPEC_SHA256,
                    "nonce_sha256": hashlib.sha256(self.token.encode("ascii")).hexdigest(),
                    "process_sha256": (hashlib.sha256(str(self.protocol.process).encode("ascii")).hexdigest()
                                       if self.protocol.process is not None else None),
                    "binding": copy.deepcopy(self._binding), "material": dict(self.material_hashes),
                    "environment_process_local_once": self._environment_issued,
                    "accepted_connections": self._accepted, "refusals": self._refusals, "fixture_error": self.protocol.error,
                    "native_done": self.protocol.done, "pending": self.protocol.pending, "stages": copy.deepcopy(self.protocol.stages),
                    "cleanup": {"closed": self._closed, "listeners_closed": all(listener.fileno() == -1 for listener in self._listeners),
                                "owned_peers_remaining": len(self._peers), "workers_terminated": self._workers_terminated,
                                "failure_retained": self._failure is not None}}

    def assert_complete(self) -> None:
        if (self.protocol is None or not self.protocol.done or self.protocol.error or self._refusals or
                self._failure is not None or not self._closed or not self._workers_terminated or self._peers or
                any(listener.fileno() != -1 for listener in self._listeners)):
            raise FixtureRefusal("Native cookie completion requires original methods, all actual stages and independent owned cleanup")
        if self._binding is None or any(digest(self.root / name) != value for name, value in self._binding["inputs"].items()):
            raise FixtureRefusal("Original native cookie source inputs changed during the actual invocation")
