#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Test-only, finite HTTP content-policy fixture, independent of accepted request fixtures.

Both listeners and every socket/thread belong to this lease. Only numeric counters
and fixed stage names leave the fixture. The nonce and dummy initial/auth header
values are neither receipts nor logs. Real WebViews must supply all native evidence;
running this fixture or its socket controls does not qualify a native target.
"""
from __future__ import annotations

import concurrent.futures
import contextlib
import dataclasses
import hashlib
import json
from pathlib import Path
import re
import secrets
import socket
import threading
import time
from collections.abc import Iterable


UNICODE_TEXT = "Ελληνικά العربية 漢字 café 🙂"
RESOURCE_TEXT = "ресурс 日本語 café 🙂"
ASSETS = {"probe.js": "script", "probe.css": "style", "probe.svg": "image"}
STAGES = {
    "restore": ("url", "navigator", "redirect", "final", "html-recovery", "null-recovery"),
    "replay": ("get", "one-time", "form", "posted", "safe"),
    "headers": tuple(f"{entry}-{stage}" for entry in ("state", "navigator")
                     for stage in ("initial", "same", "same-final", "cross", "cross-final", "link")),
    "resources": tuple(f"{entry}-{encoding}" for entry in ("state", "navigator")
                       for encoding in ("utf8", "utf8-alias")),
    "unsupported": ("seed", "state-headers", "navigator-headers", "state-base", "navigator-base", "recovery"),
}
COUNTERS = (
    "get", "post", "page", "redirect", "script", "style", "image",
    "main_initial", "main_authorization", "script_initial", "script_authorization",
    "style_initial", "style_authorization", "image_initial", "image_authorization",
    "unexpected_initial", "unexpected_authorization", "response_bytes", "closed", "pending",
)
MAX_HEADERS = 8192
MAX_BODY = 512
MAX_CONNECTIONS = 512
MAX_STAGE_REQUESTS = 12
MAX_CONTROL = 768
FORM_BODY = b"nativecmpkit_form=fixture-only"
TOKEN = re.compile(r"[0-9a-f]{32}\Z")
PID = re.compile(r"[1-9][0-9]{0,9}\Z")
BUNDLE = re.compile(r"io\.github\.apdelrahman1911\.nativecmpkit\.verification\.ui\.r[0-9a-f]{12}\.t[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
IOS_METHODS = ("restore", "replay", "headers", "resources")
SOURCE = "scripts/ci/webview_content_policy_fixture.py"
NATIVE_SOURCE = "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewContentPolicyAcceptanceTest.kt"
NATIVE_HELPER = "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosContentPolicyFixture.kt"


def process_sha256(pid: int) -> str:
    """Bind to the observed canonical process ID without exporting that ID in a receipt."""
    if type(pid) is not int or not 0 < pid < 2**31:
        raise FixtureRefusal("Missing exact owned application process identity")
    return hashlib.sha256(str(pid).encode("ascii")).hexdigest()


class FixtureRefusal(ValueError):
    """A fixed-message bounded protocol refusal, never raw request data."""


@dataclasses.dataclass(frozen=True)
class Request:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes


def read_request(peer: socket.socket) -> Request:
    """Read one bounded HTTP/1.x request, no folding/duplicates/chunked bodies."""
    deadline = time.monotonic() + 3.0
    header = bytearray()
    while not header.endswith(b"\r\n\r\n"):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or len(header) >= MAX_HEADERS:
            raise FixtureRefusal("Owned HTTP header budget exceeded")
        peer.settimeout(remaining)
        part = peer.recv(1)
        if not part:
            raise FixtureRefusal("Owned HTTP header was incomplete")
        header += part
    try:
        lines = header.decode("ascii").split("\r\n")
    except UnicodeError as exc:
        raise FixtureRefusal("Owned HTTP header is not ASCII") from exc
    pieces = lines[0].split(" ")
    if len(pieces) != 3 or pieces[0] not in ("GET", "POST") or pieces[2] not in ("HTTP/1.0", "HTTP/1.1"):
        raise FixtureRefusal("Unsupported owned HTTP request line")
    if not re.fullmatch(r"/[a-zA-Z0-9./-]+", pieces[1]) or ".." in pieces[1]:
        raise FixtureRefusal("Unowned HTTP route syntax")
    headers: dict[str, str] = {}
    for line in lines[1:-2]:
        name, separator, value = line.partition(":")
        name = name.lower()
        if not separator or not re.fullmatch(r"[a-z0-9-]+", name) or name in headers:
            raise FixtureRefusal("Duplicate or invalid owned HTTP header")
        if any(ord(char) < 32 and char != "\t" for char in value):
            raise FixtureRefusal("Unreviewed owned HTTP header byte")
        headers[name] = value.strip()
    if "transfer-encoding" in headers:
        raise FixtureRefusal("Chunked owned fixture ingress is unsupported")
    length_text = headers.get("content-length", "0")
    if not re.fullmatch(r"[0-9]{1,4}", length_text) or int(length_text) > MAX_BODY:
        raise FixtureRefusal("Owned HTTP body budget exceeded")
    length = int(length_text)
    if pieces[0] == "GET" and length:
        raise FixtureRefusal("GET body is outside the finite fixture")
    body = bytearray()
    while len(body) < length:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FixtureRefusal("Owned HTTP body deadline exceeded")
        peer.settimeout(remaining)
        part = peer.recv(length - len(body))
        if not part:
            raise FixtureRefusal("Owned HTTP body was incomplete")
        body += part
    return Request(pieces[0], pieces[1], headers, bytes(body))


def response(status: int, mime: str, body: bytes, location: str | None = None) -> bytes:
    extra = f"Location: {location}\r\n" if location else ""
    return (f"HTTP/1.1 {status} Fixture\r\nContent-Type: {mime}\r\nContent-Length: {len(body)}\r\n"
            f"Connection: close\r\nCache-Control: no-store, no-cache, max-age=0\r\n{extra}\r\n").encode("ascii") + body


def records(values: dict[str, int]) -> bytes:
    if any(not re.fullmatch(r"[a-z_]+", key) or type(value) is not int or not 0 <= value <= 2**31 - 1
           for key, value in values.items()):
        raise FixtureRefusal("Control counters are outside the finite protocol")
    result = "".join(f"{key}={value}\n" for key, value in values.items()).encode("ascii")
    if len(result) > 2048:
        raise FixtureRefusal("Control response budget exceeded")
    return result


class OwnedContentPolicyFixture:
    """Start two independent owned loopback origins, acquire once, close all stages independently."""

    def __init__(self, token: str | None = None, methods: Iterable[str] = ("restore", "replay", "headers", "resources")):
        self._token = secrets.token_hex(16) if token is None else token
        if not TOKEN.fullmatch(self._token):
            raise FixtureRefusal("A fresh 128-bit owned nonce is required")
        self.methods = tuple(methods)
        if not self.methods or len(set(self.methods)) != len(self.methods) or not set(self.methods) <= STAGES.keys():
            raise FixtureRefusal("Unknown finite method selection")
        self._lock = threading.RLock()
        self._counts = {method: {stage: dict.fromkeys(COUNTERS, 0) for stage in STAGES[method]} for method in self.methods}
        self._claims: dict[str, int] = {}
        self._process: int | None = None
        self._binding: dict[str, str] | None = None
        self._launch_environment_issued = False
        self._done: set[str] = set()
        self._listeners: list[socket.socket] = []
        self._threads: list[threading.Thread] = []
        self._sockets: set[socket.socket] = set()
        self._closing = threading.Event()
        self._closed = False
        self._listener_closed: list[bool] = []
        self._workers_terminated = False
        self._cleanup_failed = False
        self._failure: BaseException | None = None
        self._connections = self._control = self._refusals = 0
        self._admission = threading.BoundedSemaphore(16)
        self._workers = concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="owned-content-policy")
        try:
            for origin in range(2):
                listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._listeners.append(listener)
                self._listener_closed.append(False)
                listener.bind(("127.0.0.1", 0))
                listener.listen(16)
                listener.settimeout(0.1)
                thread = threading.Thread(target=self._accept, args=(listener, origin), daemon=True,
                                          name=f"owned-content-policy-origin-{origin}")
                self._threads.append(thread)
                thread.start()
        except BaseException as primary:
            try:
                self.close()
            except BaseException as cleanup:
                primary.add_note(f"Independent fixture cleanup also failed: {type(cleanup).__name__}")
            raise

    @property
    def environment(self) -> dict[str, str]:
        """Private runner-to-own-application handoff, never a receipt or notification."""
        return {"NATIVECMPKIT_WEBVIEW_CONTENT_TOKEN": self._token,
                "NATIVECMPKIT_WEBVIEW_CONTENT_ORIGIN_PORT": str(self.port(0)),
                "NATIVECMPKIT_WEBVIEW_CONTENT_SECOND_PORT": str(self.port(1))}

    @property
    def nonce_sha256(self) -> str:
        return hashlib.sha256(self._token.encode("ascii")).hexdigest()

    def bind_application(self, root: Path, *, bundle_id: str, signed_hash: str, plist_hash: str) -> None:
        """Bind once BEFORE launch to the runner's actual installed-app/source witnesses.

        This does not install, sign or launch an application. The existing owned
        UIApplication transport must supply and independently verify these facts.
        An unbound socket-control lease can never validate as a native receipt.
        """
        if (not isinstance(bundle_id, str) or not BUNDLE.fullmatch(bundle_id) or
                any(not isinstance(value, str) or not HEX64.fullmatch(value) for value in (signed_hash, plist_hash))):
            raise FixtureRefusal("Owned installed application identities are required")
        with self._lock:
            if (self._closed or self._closing.is_set() or self._binding is not None or self._connections or self._claims or
                    self.methods != IOS_METHODS):
                raise FixtureRefusal("Bind exactly one fresh finite native content-policy attempt before any ingress")
            try:
                source_hashes = {name: hashlib.sha256((Path(root) / path).read_bytes()).hexdigest() for name, path in (
                    ("fixture_source_sha256", SOURCE), ("native_source_sha256", NATIVE_SOURCE),
                    ("native_helper_sha256", NATIVE_HELPER))}
            except (OSError, TypeError) as failure:
                raise FixtureRefusal("Missing native content-policy source witnesses") from failure
            self._binding = {"bundle_id": bundle_id, "signed_application_executable_sha256": signed_hash,
                             "application_plist_sha256": plist_hash, **source_hashes}

    def launch_environment(self, inherited: dict[str, str]) -> dict[str, str]:
        """Return one process-local simctl handoff; never mutate inherited/os.environ."""
        if not isinstance(inherited, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in inherited.items()):
            raise FixtureRefusal("A process-local inherited launch environment is required")
        with self._lock:
            if (self._binding is None or self._launch_environment_issued or self._connections or self._claims or
                    self._closed or self._closing.is_set()):
                raise FixtureRefusal("Launch only one prebound fresh native content-policy attempt")
            environment = dict(inherited)
            for name, value in self.environment.items():
                child = "SIMCTL_CHILD_" + name
                if environment.get(child) not in (None, value) or environment.get(name) not in (None, value):
                    raise FixtureRefusal("Inherited content-policy selector conflicts with this owned attempt")
                environment[child] = value
            self._launch_environment_issued = True
            return environment

    def port(self, origin: int) -> int:
        if origin not in (0, 1) or self._closed:
            raise FixtureRefusal("Unknown or closed owned origin")
        return self._listeners[origin].getsockname()[1]

    def url(self, method: str, stage: str, origin: int = 0, kind: str = "page") -> str:
        self._validate_stage(method, stage)
        if kind not in ("page", "base"):
            raise FixtureRefusal("Unknown owned URL kind")
        return f"http://localhost:{self.port(origin)}/{self._token}/{kind}/{method}/{stage}" + ("/" if kind == "base" else "")

    def control_url(self, action: str) -> str:
        if not re.fullmatch(r"[a-z0-9/-]+", action):
            raise FixtureRefusal("Unknown control route syntax")
        return f"http://localhost:{self.port(0)}/{self._token}/control/{action}"

    def _validate_stage(self, method: str, stage: str) -> None:
        if method not in self.methods or stage not in STAGES[method]:
            raise FixtureRefusal("Unknown finite content-policy stage")

    def _record_failure(self, failure: BaseException) -> None:
        with self._lock:
            if self._failure is None:
                self._failure = failure

    def assert_healthy(self) -> None:
        if self._failure is not None:
            raise AssertionError("Owned content-policy fixture failed") from self._failure

    def _accept(self, listener: socket.socket, origin: int) -> None:
        while not self._closing.is_set():
            acquired = False
            peer: socket.socket | None = None
            try:
                peer, _ = listener.accept()
                with self._lock:
                    self._connections += 1
                    if self._connections > MAX_CONNECTIONS:
                        raise FixtureRefusal("Owned connection budget exceeded")
                    self._sockets.add(peer)
                acquired = self._admission.acquire(blocking=False)
                if not acquired:
                    raise FixtureRefusal("Owned concurrent connection budget exceeded")
                self._workers.submit(self._serve, peer, origin)
                peer = None  # the worker now owns both the socket and admission permit
                acquired = False
            except socket.timeout:
                continue
            except BaseException as failure:
                if not self._closing.is_set():
                    self._record_failure(failure)
                if peer is not None:
                    self._close_socket(peer)
                if acquired:
                    self._admission.release()
                if not self._closing.is_set():
                    return

    def _close_socket(self, peer: socket.socket) -> None:
        try:
            peer.close()
            if peer.fileno() != -1:
                raise FixtureRefusal("Owned socket closure was not observed")
            with self._lock:
                self._sockets.discard(peer)
        except BaseException as failure:
            self._record_failure(failure)

    def _serve(self, peer: socket.socket, origin: int) -> None:
        owned: dict[str, int] | None = None
        try:
            request = read_request(peer)
            parts = request.path.strip("/").split("/")
            if len(parts) < 3 or not secrets.compare_digest(parts[0], self._token):
                raise FixtureRefusal("Foreign fixture nonce or path")
            if parts[1] == "control":
                wire = self._control_response(request, parts[2:], origin)
            else:
                wire, owned = self._content_response(request, parts[1:], origin)
            peer.sendall(wire)
            if owned is not None:
                with self._lock:
                    owned["response_bytes"] += len(wire)
        except FixtureRefusal:
            with self._lock:
                self._refusals += 1
            # Refusal is visible HTTP, not an admitted alternate loader or successful page.
            with contextlib.suppress(OSError):
                peer.sendall(response(409, "text/plain", b"Owned finite fixture refusal"))
        except OSError as failure:
            # Cancelling an incomplete owned read during independent shutdown is
            # not a native request result. Socket-close failures remain retained.
            if not self._closing.is_set():
                self._record_failure(failure)
        except BaseException as failure:
            self._record_failure(failure)
        finally:
            self._close_socket(peer)
            if owned is not None:
                with self._lock:
                    owned["pending"] -= 1
                    owned["closed"] += 1
            self._admission.release()

    def _control_response(self, request: Request, parts: list[str], origin: int) -> bytes:
        with self._lock:
            self._control += 1
            if self._control > MAX_CONTROL or origin != 0 or request.method != "GET":
                raise FixtureRefusal("Owned control admission refused")
            if not parts or parts[0] not in ("open", "stats", "done"):
                raise FixtureRefusal("Unknown finite control action")
            if len(parts) not in (3, 4) or not PID.fullmatch(parts[-1]):
                raise FixtureRefusal("Missing exact application process claim")
            action, method, pid = parts[0], parts[1], int(parts[-1])
            process_sha256(pid)  # Numeric control and receipt share the exact canonical PID domain.
            if method not in self.methods:
                raise FixtureRefusal("Unselected content-policy method")
            if action == "open" and len(parts) == 3:
                if method in self._claims or method in self._done:
                    raise FixtureRefusal("Never replay a claimed content-policy method")
                if self._process not in (None, pid):
                    raise FixtureRefusal("Every selected native method must belong to the same application process")
                if self._binding is not None and not self._launch_environment_issued:
                    raise FixtureRefusal("Bound native methods require their own process-local launch handoff")
                self._process = pid
                self._claims[method] = pid
                values = {"opened": 1, "pid": pid}
            else:
                if self._claims.get(method) != pid or method in self._done:
                    raise FixtureRefusal("Foreign or completed process claim")
                if action == "stats" and len(parts) == 4:
                    self._validate_stage(method, parts[2])
                    values = dict(self._counts[method][parts[2]])
                elif action == "done" and len(parts) == 3:
                    if any(stage["pending"] for stage in self._counts[method].values()):
                        raise FixtureRefusal("Owned HTTP work did not drain before method completion")
                    self.assert_healthy()
                    self._done.add(method)
                    values = {"done": 1, "pid": pid}
                else:
                    raise FixtureRefusal("Unknown finite control shape")
            return response(200, "text/plain; charset=ascii", records(values))

    def _content_response(self, request: Request, parts: list[str], origin: int) -> tuple[bytes, dict[str, int]]:
        if len(parts) not in (3, 4) or parts[0] not in ("page", "base"):
            raise FixtureRefusal("Unknown finite owned content route")
        kind, method, stage = parts[:3]
        self._validate_stage(method, stage)
        asset = parts[3] if len(parts) == 4 else None
        if (kind == "base" and asset not in ASSETS) or (kind == "page" and asset is not None):
            raise FixtureRefusal("Unknown finite owned relative asset")
        if request.method == "POST" and not (kind == "page" and method == "replay" and stage == "posted" and request.body == FORM_BODY):
            raise FixtureRefusal("Unsupported owned form submission")
        with self._lock:
            if method not in self._claims or method in self._done:
                raise FixtureRefusal("Unclaimed or completed native content method")
            counts = self._counts[method][stage]
            if counts["get"] + counts["post"] >= MAX_STAGE_REQUESTS:
                raise FixtureRefusal("Owned stage request budget exceeded")
            initial = int(request.headers.get("x-nativecmpkit-initial") == f"fixture-only-{self._token}")
            authorization = int(request.headers.get("authorization") == f"NativeCmpKitFixture {self._token}")
            counts["unexpected_initial"] += int("x-nativecmpkit-initial" in request.headers and not initial)
            counts["unexpected_authorization"] += int("authorization" in request.headers and not authorization)
            counts[request.method.lower()] += 1
            counts["pending"] += 1
            role = ASSETS[asset] if asset else "main"
            counts[f"{role}_initial"] += initial
            counts[f"{role}_authorization"] += authorization
            if asset:
                counts[role] += 1
                body, mime = self._asset(asset, initial, authorization)
                return response(200, mime, body), counts
            if method == "headers" and stage.endswith("-initial") and (not initial or not authorization):
                return response(403, "text/plain", b"Exact dummy fixture authentication is required"), counts
            location: str | None = None
            if method == "restore" and stage == "redirect":
                location = self.url(method, "final", origin)
            elif method == "headers" and stage.endswith(("-same", "-cross")):
                destination = 1 if stage.endswith("-cross") else origin
                location = self.url(method, stage + "-final", destination)
            if location:
                counts["redirect"] += 1
                return response(302, "text/plain", b"", location), counts
            if method == "replay" and stage == "one-time" and counts["get"] > 1:
                return response(409, "text/plain", b"One-time fixture URL was repeated"), counts
            if method == "replay" and stage == "posted" and request.method != "POST":
                return response(405, "text/plain", b"Fixture form result is POST only"), counts
            counts["page"] += 1
            title = f"{method}-{stage}-{counts['page']}"
            if method == "headers":
                title += f"-h{initial}-a{authorization}"
            body = self._page(method, stage, title, origin)
            return response(200, "text/html; charset=utf-8", body), counts

    def _asset(self, asset: str, initial: int, authorization: int) -> tuple[bytes, str]:
        if asset == "probe.js":
            body = ("document.documentElement.setAttribute('data-policy-script'," + json.dumps(f"h{initial}-a{authorization}") + ");"
                    "document.getElementById('relative-resource-text').textContent=" + json.dumps(RESOURCE_TEXT, ensure_ascii=False) + ";")
            return body.encode("utf-8"), "application/javascript; charset=utf-8"
        if asset == "probe.css":
            return b"#policy-document { color: rgb(17, 34, 51); }", "text/css; charset=utf-8"
        return (b'<svg xmlns="http://www.w3.org/2000/svg" width="7" height="9"><rect width="7" height="9" fill="#123"/></svg>',
                "image/svg+xml")

    def _page(self, method: str, stage: str, title: str, origin: int) -> bytes:
        resource = ""
        link = ""
        if method == "headers":
            base = self.url(method, stage, origin, "base")
            resource = (f'<link rel="stylesheet" href="{base}probe.css"><script defer src="{base}probe.js"></script>'
                        f'<img id="relative-image" src="{base}probe.svg">')
            entry = stage.split("-", 1)[0]
            link = f'<a id="policy-link" href="{self.url(method, entry + "-link", origin)}">later link</a>'
        if method == "replay" and stage == "form":
            link = (f'<form id="policy-form" method="post" action="{self.url(method, "posted", origin)}">'
                    '<input name="nativecmpkit_form" value="fixture-only"><button type="submit">submit</button></form>')
        return (f'<!doctype html><meta charset="utf-8"><link rel="icon" href="data:,"><title>{title}</title>'
                f'<p id="policy-document">{UNICODE_TEXT}</p><p id="relative-resource-text"></p>{resource}{link}').encode("utf-8")

    def receipt(self) -> dict:
        """Never includes nonce, URLs, raw PID/environment, bodies or raw headers."""
        with self._lock:
            return {"schema": "nativecmpkit-webview-content-policy-v1", "closed": self._closed,
                    "connections": self._connections, "control_requests": self._control,
                    "refusals": self._refusals, "owned_sockets": len(self._sockets),
                    "fixture_error": self._failure is not None,
                    "nonce_sha256": self.nonce_sha256,
                    "process_sha256": process_sha256(self._process) if self._process is not None else None,
                    "native_binding": ({**self._binding, "launch_environment_process_local_only": self._launch_environment_issued}
                                       if self._binding is not None else None),
                    "cleanup": {"owned_listeners_closed": self._closed and all(self._listener_closed),
                                "owned_sockets_closed": self._closed and not self._sockets,
                                "owned_acceptors_terminated": self._closed and all(not t.is_alive() for t in self._threads),
                                "owned_workers_terminated": self._workers_terminated,
                                "owned_http_drained": self._closed and all(c["pending"] == 0 for stages in self._counts.values() for c in stages.values()),
                                "independent_cleanup_succeeded": self._closed and not self._cleanup_failed},
                    "methods": {method: {"claimed": method in self._claims, "done": method in self._done,
                                         "stages": {stage: dict(counts) for stage, counts in self._counts[method].items()}}
                                for method in self.methods}}

    def require_complete(self) -> None:
        """Protocol-only completion, not an installed-app, native XML or issue acceptance."""
        self.assert_healthy()
        with self._lock:
            if self._refusals or self._done != set(self.methods) or any(c["pending"] for stages in self._counts.values() for c in stages.values()):
                raise AssertionError("The exact new content-policy method selection did not complete")

    def close(self) -> None:
        if self._closed:
            self.assert_healthy()
            return
        self._closing.set()
        failures: list[BaseException] = []

        def independent(action) -> None:
            try:
                action()
            except BaseException as failure:
                failures.append(failure)

        for index, listener in enumerate(self._listeners):
            def close_listener(index=index, listener=listener):
                listener.close()
                if listener.fileno() != -1:
                    raise FixtureRefusal("Owned listener closure was not observed")
                self._listener_closed[index] = True
            independent(close_listener)
        for peer in tuple(self._sockets):
            independent(lambda peer=peer: self._close_socket(peer))
        for thread in self._threads:
            independent(lambda thread=thread: thread.join(4.0))
        def close_workers():
            self._workers.shutdown(wait=True, cancel_futures=False)
            self._workers_terminated = True
        independent(close_workers)
        if any(thread.is_alive() for thread in self._threads) or self._sockets:
            failures.append(AssertionError("Owned content-policy workers or sockets survived cleanup"))
        self._closed = True
        if self._failure is not None:
            failures.insert(0, self._failure)
        if failures:
            self._cleanup_failed = True
            self._record_failure(failures[0])
            primary = AssertionError("Independent owned content-policy cleanup failed")
            for failure in failures:
                primary.add_note(type(failure).__name__)
            raise primary from failures[0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, primary, traceback):
        try:
            self.close()
        except BaseException as cleanup:
            if primary is None:
                raise
            primary.add_note(f"Independent content fixture cleanup also failed: {type(cleanup).__name__}")
        return False


def complete_native_stages(methods: dict) -> bool:
    """Exact iOS wire matrix only; socket controls still provide ZERO native evidence."""
    if not isinstance(methods, dict) or set(methods) != set(IOS_METHODS):
        return False
    main_headers = ("main_initial", "main_authorization")
    asset_headers = tuple(f"{role}_{kind}" for role in ("script", "style", "image") for kind in ("initial", "authorization"))
    expected: dict[str, dict[str, dict[str, int | None]]] = {method: {} for method in IOS_METHODS}

    def stage(method: str, name: str, *, get=1, post=0, page=1, redirect=0, assets=False, initial=0, authorization=0):
        values = dict.fromkeys(COUNTERS, 0)
        values.update(get=get, post=post, page=page, redirect=redirect, closed=get + post,
                      main_initial=initial, main_authorization=authorization, response_bytes=None)
        if assets:
            values.update(script=1, style=1, image=1)
        expected[method][name] = values

    for name in ("url", "navigator", "final"):
        stage("restore", name, get=2, page=2)
    stage("restore", "redirect", page=0, redirect=1)
    for name in ("html-recovery", "null-recovery"):
        stage("restore", name)
    stage("replay", "get", get=2, page=2, initial=1, authorization=1)
    for name in ("one-time", "form", "safe"):
        stage("replay", name)
    stage("replay", "posted", get=0, post=1)
    for entry in ("state", "navigator"):
        stage("headers", f"{entry}-initial", get=4, assets=True, initial=1, authorization=1)
        for route in ("same", "cross"):
            stage("headers", f"{entry}-{route}", page=0, redirect=1, initial=1, authorization=1)
            stage("headers", f"{entry}-{route}-final", get=4, assets=True, initial=None, authorization=None)
        stage("headers", f"{entry}-link", get=4, assets=True)
        for encoding in ("utf8", "utf8-alias"):
            stage("resources", f"{entry}-{encoding}", get=3, page=0, assets=True)
    for method in IOS_METHODS:
        row = methods[method]
        if (not isinstance(row, dict) or set(row) != {"claimed", "done", "stages"} or
                row["claimed"] is not True or row["done"] is not True or
                not isinstance(row["stages"], dict) or set(row["stages"]) != set(STAGES[method])):
            return False
        for name, values in expected[method].items():
            actual = row["stages"][name]
            if (not isinstance(actual, dict) or set(actual) != set(COUNTERS) or
                    any(type(value) is not int or not 0 <= value <= 1024**2 for value in actual.values())):
                return False
            for key, value in values.items():
                if key == "response_bytes":
                    if actual[key] <= 0:
                        return False
                elif value is None:
                    if actual[key] not in (0, 1):
                        return False
                elif actual[key] != value:
                    return False
    # Redirect forwarding is an observed native policy, not an assumed promise;
    # both supported public entry points must report the same actual facts.
    headers = methods["headers"]["stages"]
    for route in ("initial", "same-final", "cross-final", "link"):
        if any(headers[f"state-{route}"][key] != headers[f"navigator-{route}"][key] for key in main_headers + asset_headers):
            return False
    return True


def validate_receipt(document: dict, *, bundle_id: str, signed_hash: str, plist_hash: str,
                     native_pid: int, fixture_hash: str, native_hash: str, helper_hash: str, nonce_hash: str) -> bool:
    """Validate owned transport against REAL caller witnesses, never generate native results.

    The lead's unchanged KGP XML/application/source-map validation is separately
    mandatory. A positive pure/socket control of this function is not that proof.
    """
    try:
        fields = {"schema", "closed", "connections", "control_requests", "refusals", "owned_sockets", "fixture_error",
                  "nonce_sha256", "process_sha256", "native_binding", "cleanup", "methods"}
        identities = (signed_hash, plist_hash, fixture_hash, native_hash, helper_hash, nonce_hash)
        if (not isinstance(document, dict) or set(document) != fields or not isinstance(bundle_id, str) or not BUNDLE.fullmatch(bundle_id) or
                any(not isinstance(value, str) or not HEX64.fullmatch(value) for value in identities)):
            return False
        binding = {"bundle_id": bundle_id, "signed_application_executable_sha256": signed_hash,
                   "application_plist_sha256": plist_hash, "fixture_source_sha256": fixture_hash,
                   "native_source_sha256": native_hash, "native_helper_sha256": helper_hash,
                   "launch_environment_process_local_only": True}
        cleanup = dict.fromkeys(("owned_listeners_closed", "owned_sockets_closed", "owned_acceptors_terminated",
                                 "owned_workers_terminated", "owned_http_drained", "independent_cleanup_succeeded"), True)
        bound = document["native_binding"]
        released = document["cleanup"]
        if (not isinstance(bound, dict) or set(bound) != set(binding) or
                bound["launch_environment_process_local_only"] is not True or
                any(not isinstance(bound[key], str) or bound[key] != value for key, value in binding.items()
                    if key != "launch_environment_process_local_only") or
                not isinstance(released, dict) or set(released) != set(cleanup) or any(value is not True for value in released.values())):
            return False
        return (document["schema"] == "nativecmpkit-webview-content-policy-v1" and document["closed"] is True and
                type(document["connections"]) is int and 0 < document["connections"] <= MAX_CONNECTIONS and
                type(document["control_requests"]) is int and 2 * len(IOS_METHODS) <= document["control_requests"] <= MAX_CONTROL and
                all(type(document[key]) is int and document[key] == 0 for key in ("refusals", "owned_sockets")) and
                document["fixture_error"] is False and document["nonce_sha256"] == nonce_hash and
                document["process_sha256"] == process_sha256(native_pid) and
                complete_native_stages(document["methods"]) and
                document["connections"] == document["control_requests"] + sum(stage["closed"] for method in document["methods"].values() for stage in method["stages"].values()))
    except (ValueError, TypeError, KeyError):
        return False
