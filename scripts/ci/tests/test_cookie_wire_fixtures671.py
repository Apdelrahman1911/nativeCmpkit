# SPDX-License-Identifier: Apache-2.0
"""NEW cookie671 SOURCE/MODEL controls. No sockets, DNS, TLS, OpenSSL, Gradle or native body execution."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts/ci"
if str(SCRIPTS) not in sys.path: sys.path.insert(0, str(SCRIPTS))
import cookie_native_wire_fixture as native
import cookie_wire_material as material

TOKEN = "0" * 32
ROOT_HOST = f"r{TOKEN}.nativecmpkit.test"


class CookieWireModel671Tests(unittest.TestCase):
    def setUp(self):
        self.spec = native.load_specification((SCRIPTS / "fixtures/cookie-wire-v1.json").absolute())
        self.protocol = native.CookieWireProtocol(self.spec, TOKEN, 17891, 17892)
        self.protocol.bound = True

    def request(self, route, *, secure=False, subhost=False, raw="", control=False, pid=42, host=None, origin=None):
        scheme_port = 17892 if secure else 17891
        domain = "localhost" if control else ("sub." if subhost else "") + ROOT_HOST
        headers = {"host": f"{domain}:{scheme_port}", "cookie": raw}
        if host is not None: headers["host"] = host
        if origin is not None: headers["origin"] = origin
        if control: route = f"control/{route}/{pid}"
        return native.Request("GET", self.protocol.prefix + route, headers, b"")

    def opened(self):
        reply = self.protocol.route(self.request("open", control=True), False)
        self.protocol.finish(reply.stage, True)

    def test_model_constructor_does_not_acquire_dns_socket_tls_or_process(self):
        with mock.patch.object(native.socket, "socket", side_effect=AssertionError("No model sockets")), \
             mock.patch.object(native.socket, "getaddrinfo", side_effect=AssertionError("No model DNS")), \
             mock.patch.object(native.ssl, "SSLContext", side_effect=AssertionError("No model TLS")):
            native.CookieWireProtocol(self.spec, TOKEN, 17891, 17892)
            commands = material.certificate_commands(TOKEN, Path("/dummy-owned-model-only"), Path("/dummy-openssl-model-only"))
            self.assertEqual(5, len(commands))

    def test_fixed_definitions_keep_equal_values_on_two_distinct_paths(self):
        headers = [native.set_cookie(self.spec, TOKEN, ROOT_HOST, entry) for entry in self.spec["cookies"]]
        equal = [header for header in headers if header.startswith(f"nativecmpkit_{TOKEN}_equal=")]
        self.assertEqual(2, len(equal))
        self.assertNotEqual(equal[0], equal[1])
        self.assertTrue(any("; HttpOnly" in value for value in headers))
        self.assertTrue(any("; Secure" in value for value in headers))
        self.assertTrue(any(f"Path={self.protocol.prefix}private" in value for value in headers))
        self.assertTrue(any("Domain=." + ROOT_HOST in value for value in headers))
        self.assertTrue(any("Expires=Thu, 01 Jan 1970" in value for value in headers))
        self.assertTrue(any("Expires=Fri, 01 Jan 2100" in value for value in headers))
        session = next(header for header in headers if header.startswith(f"nativecmpkit_{TOKEN}_session="))
        self.assertNotIn("Expires", session)

    def test_model_inbound_vector_counts_duplicates_without_exporting_foreign_values(self):
        raw = f"foreign=in-memory-only; nativecmpkit_{TOKEN}_scope=root; nativecmpkit_{TOKEN}_scope=foo; " \
              f"nativecmpkit_{TOKEN}_equal=same; nativecmpkit_{TOKEN}_equal=same"
        vector = native.observed_vector(self.spec, TOKEN, raw)
        self.assertEqual([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2], vector)
        with self.assertRaisesRegex(native.FixtureRefusal, "Unexpected owned cookie"):
            native.observed_vector(self.spec, TOKEN, f"nativecmpkit_{TOKEN}_auth=unexpected")
        with self.assertRaisesRegex(native.FixtureRefusal, "Unreviewed owned cookie header byte"):
            native.observed_vector(self.spec, TOKEN, "foreign=\u0100")

    def test_native_controls_refuse_missing_binding_foreign_pid_host_and_origin(self):
        self.protocol.bound = False
        with self.assertRaises(native.FixtureRefusal): self.protocol.route(self.request("open", control=True), False)
        self.protocol.bound = True
        self.opened()
        for request, secure in (
            (self.request("stats", control=True, pid=43), False),
            (self.request("seed", secure=True, host="foreign.invalid:17892"), True),
            (self.request("seed", secure=True, origin="https://foreign.invalid"), True),
            (self.request("seed", secure=False), False),
        ):
            with self.assertRaises(native.FixtureRefusal): self.protocol.route(request, secure)

    def test_model_seed_logout_requires_real_tls_route_and_expires_every_owned_identity(self):
        self.opened()
        seed = self.protocol.route(self.request("seed", secure=True), True)
        self.protocol.finish(seed.stage, True)
        self.assertIn(b"; Secure\r\n", seed.payload)
        self.assertIn(b"; HttpOnly\r\n", seed.payload)
        with self.assertRaises(native.FixtureRefusal): self.protocol.route(self.request("seed", secure=True), True)
        logout = self.protocol.route(self.request("logout", secure=True), True)
        self.protocol.finish(logout.stage, True)
        self.assertEqual(14, logout.payload.count(b"Expires=Thu, 01 Jan 1970 00:00:00 GMT"))
        self.assertIn(b"; HttpOnly\r\n", logout.payload)
        self.assertIn(b"; Secure\r\n", logout.payload)

    def test_owned_response_leases_cannot_release_twice_or_complete_partial_native_stages(self):
        self.opened()
        seed = self.protocol.route(self.request("seed", secure=True), True); self.protocol.finish(seed.stage, True)
        page = self.protocol.route(self.request("foo", secure=True), True)
        self.assertEqual(1, self.protocol.pending)
        with self.assertRaises(native.FixtureRefusal): self.protocol.route(self.request("done", control=True), False)
        self.protocol.finish(page.stage, True)
        with self.assertRaises(native.FixtureRefusal): self.protocol.finish(page.stage, True)
        self.assertFalse(self.protocol.done)

    def test_model_native_count_plan_is_finite_and_not_a_native_result(self):
        self.opened()
        seed = self.protocol.route(self.request("seed", secure=True), True); self.protocol.finish(seed.stage, True)
        for secure in (True, False):
            for subhost, pages in ((False, self.spec["paths"]), (True, ("foo", "public"))):
                for page in pages:
                    for _ in range(2):
                        reply = self.protocol.route(self.request(page, secure=secure, subhost=subhost), secure)
                        self.protocol.finish(reply.stage, True)
        for _ in range(4):
            reply = self.protocol.route(self.request("foo/child", secure=True), True); self.protocol.finish(reply.stage, True)
        logout = self.protocol.route(self.request("logout", secure=True), True); self.protocol.finish(logout.stage, True)
        done = self.protocol.route(self.request("done", control=True), False); self.protocol.finish(done.stage, True)
        # These deliberately EMPTY model headers do not satisfy Kotlin's independent
        # native vectors. Model completion can NEVER be substituted for native XML.
        self.assertEqual(32, sum(row["requests"] for row in self.protocol.stages.values()))
        self.assertTrue(self.protocol.done)
        with self.assertRaises(native.FixtureRefusal): self.protocol.route(self.request("open", control=True), False)

    def test_monotonic_lifetime_refuses_expired_owned_model_session(self):
        clock = [0.0]
        self.protocol.clock = lambda: clock[0]
        self.opened(); clock[0] = 180.0
        with self.assertRaises(native.FixtureRefusal): self.protocol.route(self.request("stats", control=True), False)

    def test_new_private_public_routes_are_distinct_under_both_native_schemes(self):
        self.assertIn("private", self.spec["paths"])
        self.assertIn("public", self.spec["paths"])
        for secure in (False, True):
            private = self.protocol.stage("private", False, secure)
            public = self.protocol.stage("public", False, secure)
            self.assertNotEqual(private, public)
            self.assertIn(private, self.protocol.stages); self.assertIn(public, self.protocol.stages)


class CookieWireSource671Tests(unittest.TestCase):
    def test_shared_specification_and_independent_kotlin_count_contract_match(self):
        specification = native.load_specification((SCRIPTS / "fixtures/cookie-wire-v1.json").absolute())
        source = (ROOT / native.COMMON_SOURCES[3]).read_text()  # Fixed CookieWireContract binding, not a directory search.
        pairs = re.findall(r'"([a-z]+)" to "([a-z]+)"', source.split("val pages", 1)[0])
        self.assertEqual(specification["groups"], [list(pair) for pair in pairs])
        pages = re.search(r'val pages = listOf\(([^\n]+)\)', source)
        self.assertIsNotNone(pages)
        self.assertEqual(specification["paths"], re.findall(r'"([a-z/]+)"', pages.group(1)))
        self.assertIn('underFoo || page == "private"', source)
        self.assertEqual(native.SPEC_SHA256, hashlib.sha256((SCRIPTS / "fixtures/cookie-wire-v1.json").read_bytes()).hexdigest())
        self.assertIn("{11}", source)

    def test_desktop_production_consumes_each_occurrence_and_does_not_guess_ambiguous_metadata(self):
        source = (ROOT / native.PLATFORM_SOURCES["desktop"][0]).read_text()
        self.assertNotIn("sent.any {", source)
        self.assertIn("val remaining = transmitted.toMutableMap()", source)
        self.assertIn("remaining[identity] = occurrences - 1", source)
        self.assertIn("candidateCounts.getValue(identity) > (transmitted[identity] ?: 0)", source)
        self.assertIn("Cookie(native.name, native.value)", source)
        self.assertNotIn("CookieHandler.setDefault", source)

    def test_browser_native_transport_and_independent_restoration_remain_explicit(self):
        source = (ROOT / "calf-webview/src/webTest/kotlin/com/mohamedrejeb/calf/ui/web/BrowserCookieWireAcceptanceTest.kt").read_text()
        self.assertNotRegex(source, r"\.setRequestHeader\s*\(")
        self.assertNotRegex(source, r"(?:document|window)\.cookie\s*=(?!=)")
        self.assertIn("native.withCredentials = true", source)
        self.assertIn("window.history.replaceState(originalState, \"\", originalHref)", source)
        self.assertIn("document.cookie == foreignVisible", source)
        self.assertIn("fixture.logout()", source)
        self.assertIn("fixture.close()", source)
        self.assertIn("native.removeEventListener", source)
        self.assertIn("native.abort()", source)

    def test_new_assignment_classifier_keeps_real_cookie_writes_forbidden_but_accepts_foreign_equality(self):
        forbidden = re.compile(r"(?:document|window)\.cookie\s*=(?!=)")
        self.assertIsNotNone(forbidden.search('document.cookie = "dummy-model-only"'))
        self.assertIsNotNone(forbidden.search('window.cookie= "dummy-model-only"'))
        self.assertIsNone(forbidden.search("document.cookie == foreignVisible"))
        self.assertIsNone(forbidden.search("document.cookie === foreignVisible"))

    def test_native_tests_never_delete_all_or_change_ios_trust_and_desktop_preserves_foreign_replacements(self):
        desktop = (ROOT / native.PLATFORM_SOURCES["desktop"][2]).read_text()
        ios = (ROOT / native.PLATFORM_SOURCES["ios"][2]).read_text()
        self.assertNotIn("removeAllCookies", desktop + ios)
        self.assertNotIn("setDefaultHostnameVerifier", desktop)
        self.assertNotIn("didReceiveAuthenticationChallenge", ios)
        self.assertNotIn("NSURLCredential", ios)
        self.assertIn("SSLContext.getDefault() === strict", desktop)
        self.assertIn("getDefaultSSLSocketFactory() === installedFactory", desktop)
        self.assertIn("foreignBefore", desktop)
        self.assertIn("foreignStoreSnapshot", ios)
        self.assertIn("requireFresh", ios)
        self.assertIn("deleteCookie(cookie)", ios)

    def test_ephemeral_certificate_plan_is_exact_normal_tls_without_trust_or_hostname_bypass(self):
        commands = material.certificate_commands(TOKEN, Path("/dummy-owned-model-only"), Path("/dummy-openssl-model-only"))
        self.assertEqual({ROOT_HOST, "sub." + ROOT_HOST}, {command[-2] for command in commands[3:]})
        self.assertTrue(all("sslserver" in command for command in commands[3:]))
        extensions = material.leaf_extensions(TOKEN)
        self.assertIn("CA:FALSE", extensions); self.assertIn("serverAuth", extensions)
        self.assertIn(f"DNS:{ROOT_HOST},DNS:sub.{ROOT_HOST}", extensions)
        self.assertFalse(any("-no_check_time" in command or "-verify_return_error" in command for command in commands))

    def test_exact_owned_model_file_cleanup_preserves_foreign_replacement_and_attempts_other_files(self):
        # File-lifecycle MODEL, no generated keys/certificates or subprocess execution.
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-cookie-model671-") as parent:
            parent = Path(parent)
            directory = parent / f"nativecmpkit-cookie-wire-{TOKEN}-model"; directory.mkdir()
            lease = material.OwnedCookieTlsMaterial(TOKEN, directory)
            for name in ("ca.pem", "server.pem"):
                path = directory / name; path.write_bytes(b"dummy-source-model-only")
                info = path.stat(); lease._identities[path] = (info.st_dev, info.st_ino)
            foreign = parent / "foreign-model-owned-by-test"; foreign.write_bytes(b"foreign-model-preserved")
            (directory / "ca.pem").unlink(); (directory / "ca.pem").symlink_to(foreign)
            with self.assertRaisesRegex(RuntimeError, "Independent owned cookie material cleanup failed"): lease.close()
            self.assertEqual(b"foreign-model-preserved", foreign.read_bytes())
            self.assertTrue((directory / "ca.pem").is_symlink())
            self.assertFalse((directory / "server.pem").exists())


if __name__ == "__main__": unittest.main()
