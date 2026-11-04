#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""NEW bounded socket/protocol controls. These are never native WebView executions."""
import contextlib
import copy
import errno
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import re
import socket
import sys
import time
import unittest
from urllib.parse import urlsplit

SOURCE = Path(__file__).with_name("webview_content_policy_fixture.py")
spec = importlib.util.spec_from_file_location("new_webview_content_policy_fixture", SOURCE)
fixture_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fixture_module
spec.loader.exec_module(fixture_module)
Fixture = fixture_module.OwnedContentPolicyFixture
Refusal = fixture_module.FixtureRefusal
PID = 612


def assert_owned_peer_closed(case, peer):
    """Only EOF or this platform's exact connection-reset closure shape is valid."""
    try:
        case.assertEqual(b"", peer.recv(1))
    except ConnectionResetError as failure:
        case.assertEqual(errno.ECONNRESET, failure.errno)


def round_trip(url, method="GET", body=None, headers=None):
    parsed = urlsplit(url)
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=4)
    try:
        connection.request(method, parsed.path, body, headers or {})
        reply = connection.getresponse()
        return reply.status, dict(reply.getheaders()), reply.read()
    finally:
        connection.close()


def control(fixture, action, expected=200):
    code, _, body = round_trip(fixture.control_url(action))
    if code != expected:
        raise AssertionError("Unexpected bounded owned control status")
    if expected != 200:
        return {}
    result = {}
    for line in body.decode("ascii").splitlines():
        if not re.fullmatch(r"[a-z_]+=[0-9]{1,10}", line):
            raise AssertionError("Non-numeric fixture control")
        key, value = line.split("=")
        if key in result:
            raise AssertionError("Duplicate fixture control")
        result[key] = int(value)
    return result


def open_method(fixture, method):
    return control(fixture, f"open/{method}/{PID}")


def stats(fixture, method, stage):
    deadline = time.monotonic() + 4
    while True:
        observed = control(fixture, f"stats/{method}/{stage}/{PID}")
        if observed["pending"] == 0:
            return observed
        if time.monotonic() >= deadline:
            raise AssertionError("Owned stage failed to drain")
        time.sleep(0.005)


class WebViewContentPolicyFixtureTest(unittest.TestCase):
    def test_authenticated_initial_page_requires_exact_dummy_wire_values(self):
        with Fixture(methods=("headers",)) as fixture:
            open_method(fixture, "headers")
            self.assertEqual(403, round_trip(fixture.url("headers", "navigator-initial"))[0])
            observed = stats(fixture, "headers", "navigator-initial")
            self.assertEqual((1, 0, 0, 0), tuple(observed[key] for key in ("get", "page", "main_initial", "main_authorization")))

    def test_finite_stage_and_counter_registry_has_no_arbitrary_or_legacy_alias(self):
        self.assertEqual(("restore", "replay", "headers", "resources", "unsupported"), tuple(fixture_module.STAGES))
        self.assertEqual(6, len(fixture_module.STAGES["restore"]))
        self.assertEqual(12, len(fixture_module.STAGES["headers"]))
        self.assertEqual(4, len(fixture_module.STAGES["resources"]))
        self.assertEqual(20, len(fixture_module.COUNTERS))
        self.assertEqual(len(set(fixture_module.COUNTERS)), len(fixture_module.COUNTERS))

    def test_bad_nonce_and_nonfinite_selection_refuse_without_acquiring_threads(self):
        for token in ("", "0" * 31, "g" * 32, "0" * 33):
            with self.assertRaises(Refusal):
                Fixture(token=token)
        for methods in ((), ("restore", "restore"), ("all",), ("native",)):
            with self.assertRaises(Refusal):
                Fixture(methods=methods)

    def test_fresh_nonsecret_nonces_and_two_actual_ports_are_distinct(self):
        with Fixture(methods=("restore",)) as first, Fixture(methods=("restore",)) as second:
            self.assertNotEqual(first.environment["NATIVECMPKIT_WEBVIEW_CONTENT_TOKEN"], second.environment["NATIVECMPKIT_WEBVIEW_CONTENT_TOKEN"])
            self.assertNotEqual(first.port(0), first.port(1))
            self.assertEqual(4, len({first.port(0), first.port(1), second.port(0), second.port(1)}))

    def test_unclaimed_or_foreign_content_is_not_an_admitted_request(self):
        with Fixture(methods=("restore",)) as fixture:
            self.assertEqual(409, round_trip(fixture.url("restore", "url"))[0])
            open_method(fixture, "restore")
            foreign = fixture.url("restore", "url").replace(fixture.environment["NATIVECMPKIT_WEBVIEW_CONTENT_TOKEN"], "a" * 32)
            self.assertEqual(409, round_trip(foreign)[0])
            self.assertEqual(0, stats(fixture, "restore", "url")["get"])

    def test_exact_process_claim_is_once_and_wrong_pid_cannot_read_or_complete(self):
        with Fixture(methods=("restore",)) as fixture:
            self.assertEqual({"opened": 1, "pid": PID}, open_method(fixture, "restore"))
            control(fixture, f"open/restore/{PID}", 409)
            control(fixture, "stats/restore/url/613", 409)
            control(fixture, "done/restore/613", 409)
            control(fixture, "open/restore/0", 409)
            self.assertFalse(fixture.receipt()["methods"]["restore"]["done"])

    def test_control_is_get_only_on_first_owned_origin(self):
        with Fixture(methods=("restore",)) as fixture:
            url = fixture.control_url(f"open/restore/{PID}")
            second = url.replace(f":{fixture.port(0)}/", f":{fixture.port(1)}/")
            self.assertEqual(409, round_trip(second)[0])
            self.assertEqual(409, round_trip(url, "POST", b"")[0])
            self.assertFalse(fixture.receipt()["methods"]["restore"]["claimed"])

    def test_actual_get_document_counts_exclude_control_and_contain_authored_unicode(self):
        with Fixture(methods=("restore",)) as fixture:
            open_method(fixture, "restore")
            status, headers, body = round_trip(fixture.url("restore", "url"))
            self.assertEqual(200, status)
            self.assertIn("no-store", headers["Cache-Control"])
            self.assertIn(b"<title>restore-url-1</title>", body)
            self.assertIn(fixture_module.UNICODE_TEXT.encode("utf-8"), body)
            observed = stats(fixture, "restore", "url")
            self.assertEqual((1, 1, 1, 0), tuple(observed[key] for key in ("get", "page", "closed", "pending")))
            self.assertGreater(observed["response_bytes"], len(body))
            self.assertEqual(set(fixture_module.COUNTERS), set(observed))

    def test_actual_get_replay_has_two_distinct_server_generations(self):
        with Fixture(methods=("replay",)) as fixture:
            open_method(fixture, "replay")
            first = round_trip(fixture.url("replay", "get"))[2]
            second = round_trip(fixture.url("replay", "get"))[2]
            self.assertIn(b"replay-get-1", first)
            self.assertIn(b"replay-get-2", second)
            self.assertEqual(2, stats(fixture, "replay", "get")["page"])

    def test_one_time_fixture_refuses_a_real_second_get_not_a_token_string_heuristic(self):
        with Fixture(methods=("replay",)) as fixture:
            open_method(fixture, "replay")
            url = fixture.url("replay", "one-time")
            self.assertEqual(200, round_trip(url)[0])
            self.assertEqual(409, round_trip(url)[0])
            observed = stats(fixture, "replay", "one-time")
            self.assertEqual((2, 1), (observed["get"], observed["page"]))
            self.assertEqual(0, observed["post"])

    def test_genuine_bounded_form_post_and_get_to_post_only_result_are_distinct(self):
        with Fixture(methods=("replay",)) as fixture:
            open_method(fixture, "replay")
            form = round_trip(fixture.url("replay", "form"))[2]
            self.assertIn(b'method="post"', form)
            self.assertEqual(405, round_trip(fixture.url("replay", "posted"))[0])
            status, _, body = round_trip(fixture.url("replay", "posted"), "POST", fixture_module.FORM_BODY,
                                         {"Content-Type": "application/x-www-form-urlencoded"})
            self.assertEqual(200, status)
            self.assertIn(b"replay-posted-1", body)
            observed = stats(fixture, "replay", "posted")
            self.assertEqual((1, 1, 1), (observed["get"], observed["post"], observed["page"]))

    def test_wrong_form_body_refuses_before_incrementing_content_counts(self):
        with Fixture(methods=("replay",)) as fixture:
            open_method(fixture, "replay")
            self.assertEqual(409, round_trip(fixture.url("replay", "posted"), "POST", b"other=form")[0])
            self.assertEqual(0, stats(fixture, "replay", "posted")["post"])

    def test_real_same_and_cross_origin_302_locations_are_owned_not_guessed(self):
        with Fixture(methods=("headers",)) as fixture:
            open_method(fixture, "headers")
            for entry in ("state", "navigator"):
                for name, origin in (("same", 0), ("cross", 1)):
                    stage = f"{entry}-{name}"
                    status, headers, _ = round_trip(fixture.url("headers", stage))
                    self.assertEqual(302, status)
                    self.assertEqual(fixture.url("headers", stage + "-final", origin), headers["Location"])
                    self.assertEqual(200, round_trip(headers["Location"])[0])
                    self.assertEqual(1, stats(fixture, "headers", stage)["redirect"])
                    self.assertEqual(1, stats(fixture, "headers", stage + "-final")["page"])

    def test_initial_dummy_header_facts_come_from_actual_wire_and_dom_generation(self):
        with Fixture(methods=("headers",)) as fixture:
            open_method(fixture, "headers")
            token = fixture.environment["NATIVECMPKIT_WEBVIEW_CONTENT_TOKEN"]
            headers = {"X-NativeCmpKit-Initial": f"fixture-only-{token}", "Authorization": f"NativeCmpKitFixture {token}"}
            status, _, body = round_trip(fixture.url("headers", "state-initial"), headers=headers)
            self.assertEqual(200, status)
            self.assertIn(b"headers-state-initial-1-h1-a1", body)
            observed = stats(fixture, "headers", "state-initial")
            self.assertEqual((1, 1, 0, 0), tuple(observed[key] for key in
                             ("main_initial", "main_authorization", "unexpected_initial", "unexpected_authorization")))

    def test_unknown_dummy_values_are_counted_not_exported_or_treated_as_authenticated(self):
        with Fixture(methods=("headers",)) as fixture:
            open_method(fixture, "headers")
            status, _, body = round_trip(fixture.url("headers", "state-initial"),
                                    headers={"X-NativeCmpKit-Initial": "wrong", "Authorization": "unknown"})
            self.assertEqual(403, status)
            self.assertNotIn(b"<title>", body)
            observed = stats(fixture, "headers", "state-initial")
            self.assertEqual(0, observed["page"])
            self.assertEqual((0, 0, 1, 1), tuple(observed[key] for key in
                             ("main_initial", "main_authorization", "unexpected_initial", "unexpected_authorization")))
            self.assertNotIn("unknown", json.dumps(fixture.receipt()))

    def test_actual_relative_script_style_and_image_gets_have_separate_counts(self):
        with Fixture(methods=("resources",)) as fixture:
            open_method(fixture, "resources")
            base = fixture.url("resources", "state-utf8", kind="base")
            for asset, counter in fixture_module.ASSETS.items():
                status, _, body = round_trip(base + asset)
                self.assertEqual(200, status)
                self.assertTrue(body)
                if counter == "script":
                    self.assertIn(fixture_module.RESOURCE_TEXT.encode("utf-8"), body)
                    self.assertIn(b"data-policy-script", body)
            observed = stats(fixture, "resources", "state-utf8")
            self.assertEqual((3, 0, 1, 1, 1, 3), tuple(observed[key] for key in
                             ("get", "page", "script", "style", "image", "closed")))

    def test_finite_stage_overflow_is_visible_and_cannot_inflate_accepted_counts(self):
        with Fixture(methods=("restore",)) as fixture:
            open_method(fixture, "restore")
            for _ in range(fixture_module.MAX_STAGE_REQUESTS):
                self.assertEqual(200, round_trip(fixture.url("restore", "url"))[0])
            self.assertEqual(409, round_trip(fixture.url("restore", "url"))[0])
            self.assertEqual(fixture_module.MAX_STAGE_REQUESTS, stats(fixture, "restore", "url")["get"])
            with self.assertRaises(AssertionError):
                fixture.require_complete()

    def test_receipt_has_only_fixed_names_and_numeric_facts_no_nonce_pid_url_or_headers(self):
        with Fixture(methods=("restore",)) as fixture:
            open_method(fixture, "restore")
            round_trip(fixture.url("restore", "url"))
            stats(fixture, "restore", "url")
            receipt = json.dumps(fixture.receipt())
            for forbidden in (fixture.environment["NATIVECMPKIT_WEBVIEW_CONTENT_TOKEN"], "http://", "Authorization", '"pid"', "body", "environment"):
                self.assertNotIn(forbidden, receipt)
            self.assertFalse(fixture.receipt()["methods"]["restore"]["done"])

    def test_done_is_exact_new_selection_and_late_request_is_refused_not_hidden(self):
        with Fixture(methods=("restore", "replay")) as fixture:
            for method in fixture.methods:
                open_method(fixture, method)
                control(fixture, f"done/{method}/{PID}")
            fixture.require_complete()  # protocol only; no native or test acceptance claim
            self.assertEqual(409, round_trip(fixture.url("restore", "url"))[0])
            with self.assertRaises(AssertionError):
                fixture.require_complete()
            self.assertEqual(0, fixture.receipt()["methods"]["restore"]["stages"]["url"]["get"])

    def test_bounded_raw_header_duplicate_chunked_and_oversize_body_refuse(self):
        with Fixture(methods=("restore",)) as fixture:
            open_method(fixture, "restore")
            path = urlsplit(fixture.url("restore", "url")).path.encode()
            suffixes = (b"Host: localhost\r\nHost: duplicate\r\n\r\n",
                        b"Transfer-Encoding: chunked\r\n\r\n",
                        b"Content-Length: 513\r\n\r\n",
                        b"Bad Name: value\r\n\r\n")
            for suffix in suffixes:
                with socket.create_connection(("127.0.0.1", fixture.port(0)), timeout=4) as peer:
                    peer.sendall(b"GET " + path + b" HTTP/1.1\r\n" + suffix)
                    self.assertTrue(peer.recv(4096).startswith(b"HTTP/1.1 409"))
            self.assertEqual(0, stats(fixture, "restore", "url")["get"])

    def test_record_encoder_rejects_duplicate_domain_bad_types_and_overflow(self):
        self.assertEqual(b"opened=1\npid=612\n", fixture_module.records({"opened": 1, "pid": PID}))
        for values in ({"not-safe": 1}, {"opened": True}, {"opened": -1}, {"opened": 2**31}, {"opened": "1"}):
            with self.assertRaises(Refusal):
                fixture_module.records(values)

    def test_cleanup_closes_only_own_listeners_and_partial_socket_leases(self):
        foreign = socket.socket()
        try:
            foreign.bind(("127.0.0.1", 0))
            foreign.listen(1)
            with Fixture(methods=("restore",)) as fixture:
                with socket.create_connection(("127.0.0.1", fixture.port(0)), timeout=4) as peer:
                    peer.sendall(b"GET /incomplete")
                    deadline = time.monotonic() + 2
                    while fixture.receipt()["owned_sockets"] != 1 and time.monotonic() < deadline:
                        time.sleep(0.005)
                    self.assertEqual(1, fixture.receipt()["owned_sockets"], "The partial socket must actually be owned")
                    fixture.close()
                    fixture.close()  # idempotent only after actual own cleanup
                    self.assertTrue(fixture.receipt()["closed"])
                    self.assertEqual(0, fixture.receipt()["owned_sockets"])
                    self.assertTrue(all(listener.fileno() == -1 for listener in fixture._listeners))
                    self.assertTrue(all(not thread.is_alive() for thread in fixture._threads))
                    self.assertNotEqual(-1, foreign.fileno())
                    assert_owned_peer_closed(self, peer)
        finally:
            foreign.close()

    def test_first_cleanup_error_retains_failure_but_later_listener_and_workers_still_close(self):
        fixture = Fixture(methods=("restore",))
        first = fixture._listeners[0]

        class ClosingFailure:
            def close(self):
                first.close()
                raise RuntimeError("Controlled own close refusal")

        fixture._listeners[0] = ClosingFailure()
        with self.assertRaises(AssertionError):
            fixture.close()
        self.assertEqual(-1, first.fileno())
        self.assertEqual(-1, fixture._listeners[1].fileno())
        self.assertTrue(all(not thread.is_alive() for thread in fixture._threads))


class WebViewContentPolicyBindingTest(unittest.TestCase):
    """NEW ownership/schema controls. All application witnesses/PIDs here are SYNTHETIC."""
    bundle = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32
    signed_hash = "c" * 64
    plist_hash = "d" * 64
    root = SOURCE.parents[2]

    def bind(self, fixture):
        fixture.bind_application(self.root, bundle_id=self.bundle, signed_hash=self.signed_hash, plist_hash=self.plist_hash)

    def arguments(self, fixture):
        return {"bundle_id": self.bundle, "signed_hash": self.signed_hash, "plist_hash": self.plist_hash,
                "native_pid": PID, "fixture_hash": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "native_hash": hashlib.sha256((self.root / fixture_module.NATIVE_SOURCE).read_bytes()).hexdigest(),
                "helper_hash": hashlib.sha256((self.root / fixture_module.NATIVE_HELPER).read_bytes()).hexdigest(),
                "nonce_hash": fixture.nonce_sha256}

    def complete_socket_matrix(self, fixture):
        """Real localhost GET/POST controls of the validator, NOT native DOM/application evidence."""
        token = fixture.environment["NATIVECMPKIT_WEBVIEW_CONTENT_TOKEN"]
        headers = {"X-NativeCmpKit-Initial": f"fixture-only-{token}", "Authorization": f"NativeCmpKitFixture {token}"}
        for method in fixture.methods:
            open_method(fixture, method)
            if method == "restore":
                for name in ("url", "navigator", "final"):
                    for _ in range(2):
                        self.assertEqual(200, round_trip(fixture.url(method, name))[0])
                self.assertEqual(302, round_trip(fixture.url(method, "redirect"))[0])
                for name in ("html-recovery", "null-recovery"):
                    self.assertEqual(200, round_trip(fixture.url(method, name))[0])
            elif method == "replay":
                self.assertEqual(200, round_trip(fixture.url(method, "get"), headers=headers)[0])
                self.assertEqual(200, round_trip(fixture.url(method, "get"))[0])
                for name in ("one-time", "form", "safe"):
                    self.assertEqual(200, round_trip(fixture.url(method, name))[0])
                self.assertEqual(200, round_trip(fixture.url(method, "posted"), "POST", fixture_module.FORM_BODY)[0])
            elif method == "headers":
                for entry in ("state", "navigator"):
                    for route in ("initial", "same", "cross", "link"):
                        name = f"{entry}-{route}"
                        if route in ("same", "cross"):
                            self.assertEqual(302, round_trip(fixture.url(method, name), headers=headers)[0])
                            name += "-final"
                        supplied = headers if route in ("initial", "same") else {}
                        origin = 1 if route in ("cross", "link") else 0
                        self.assertEqual(200, round_trip(fixture.url(method, name, origin), headers=supplied)[0])
                        for asset in fixture_module.ASSETS:
                            self.assertEqual(200, round_trip(fixture.url(method, name, origin, "base") + asset)[0])
            elif method == "resources":
                for name in fixture_module.STAGES[method]:
                    for asset in fixture_module.ASSETS:
                        self.assertEqual(200, round_trip(fixture.url(method, name, kind="base") + asset)[0])
            for name in fixture_module.STAGES[method]:
                stats(fixture, method, name)
            control(fixture, f"done/{method}/{PID}")
        fixture.require_complete()

    def test_one_exact_canonical_process_owns_every_selected_method(self):
        with Fixture(methods=("restore", "replay")) as fixture:
            open_method(fixture, "restore")
            control(fixture, "open/replay/613", 409)
            self.assertFalse(fixture.receipt()["methods"]["replay"]["claimed"])
            self.assertEqual({"opened": 1, "pid": PID}, open_method(fixture, "replay"))
            self.assertEqual(fixture_module.process_sha256(PID), fixture.receipt()["process_sha256"])

    def test_pid_digest_and_open_refuse_noncanonical_or_out_of_range_identity(self):
        for value in (True, False, 0, -1, 2**31, "612", None):
            with self.assertRaises(Refusal):
                fixture_module.process_sha256(value)
        with Fixture(methods=("restore",)) as fixture:
            for pid in ("0612", "2147483648", "9999999999", "0"):
                control(fixture, "open/restore/" + pid, 409)
            self.assertFalse(fixture.receipt()["methods"]["restore"]["claimed"])
            self.assertFalse(fixture.receipt()["fixture_error"])

    def test_bind_is_once_before_ingress_and_only_exact_four_new_native_methods(self):
        with Fixture() as fixture:
            self.bind(fixture)
            with self.assertRaises(Refusal):
                self.bind(fixture)
        with Fixture() as fixture:
            open_method(fixture, "restore")
            with self.assertRaises(Refusal):
                self.bind(fixture)
            self.assertIsNone(fixture.receipt()["native_binding"])
        with Fixture(methods=("restore",)) as fixture:
            with self.assertRaises(Refusal):
                self.bind(fixture)

    def test_bind_refuses_missing_actual_source_or_malformed_installed_identity(self):
        with Fixture() as fixture:
            for values in ({"bundle_id": "other.bundle"}, {"signed_hash": "c" * 63}, {"plist_hash": "G" * 64}, {"signed_hash": True}):
                identities = {"bundle_id": self.bundle, "signed_hash": self.signed_hash, "plist_hash": self.plist_hash, **values}
                with self.assertRaises(Refusal):
                    fixture.bind_application(self.root, **identities)
            with self.assertRaises(Refusal):
                fixture.bind_application(self.root / "absent-content-policy-root", bundle_id=self.bundle,
                                         signed_hash=self.signed_hash, plist_hash=self.plist_hash)
            self.assertIsNone(fixture.receipt()["native_binding"])

    def test_process_local_launch_environment_is_once_exact_and_does_not_mutate_inherited(self):
        with Fixture() as fixture:
            self.bind(fixture)
            inherited = {"PATH": "owned-test-path"}
            original = dict(inherited)
            actual = fixture.launch_environment(inherited)
            self.assertEqual(original, inherited)
            self.assertIsNot(actual, inherited)
            self.assertEqual({"SIMCTL_CHILD_" + name: value for name, value in fixture.environment.items()},
                             {name: value for name, value in actual.items() if name.startswith("SIMCTL_CHILD_")})
            with self.assertRaises(Refusal):
                fixture.launch_environment(inherited)
            self.assertIs(True, fixture.receipt()["native_binding"]["launch_environment_process_local_only"])

    def test_launch_refuses_unbound_or_conflicting_plain_and_child_selectors_without_mutation(self):
        with Fixture() as fixture:
            with self.assertRaises(Refusal):
                fixture.launch_environment({})
            self.bind(fixture)
            for name in fixture.environment:
                for key in (name, "SIMCTL_CHILD_" + name):
                    inherited = {key: "different-owned-attempt"}
                    original = dict(inherited)
                    with self.assertRaises(Refusal):
                        fixture.launch_environment(inherited)
                    self.assertEqual(original, inherited)
            for inherited in (None, [], {"SAFE": True}):
                with self.assertRaises(Refusal):
                    fixture.launch_environment(inherited)
            self.assertIs(False, fixture.receipt()["native_binding"]["launch_environment_process_local_only"])

    def test_bound_native_claim_refuses_before_launch_handoff_and_after_closure(self):
        fixture = Fixture()
        try:
            self.bind(fixture)
            control(fixture, f"open/restore/{PID}", 409)
            self.assertFalse(fixture.receipt()["methods"]["restore"]["claimed"])
        finally:
            fixture.close()
        with self.assertRaises(Refusal):
            fixture.launch_environment({})

    def test_protocol_done_without_real_matrix_or_app_binding_never_validates_as_native_receipt(self):
        with Fixture() as fixture:
            for method in fixture.methods:
                open_method(fixture, method)
                control(fixture, f"done/{method}/{PID}")
            fixture.require_complete()  # Only finite transport completion, zero native acceptance.
            arguments = self.arguments(fixture)
        self.assertFalse(fixture_module.validate_receipt(fixture.receipt(), **arguments))

    def test_closed_owned_socket_matrix_and_exact_synthetic_bindings_validate_protocol_only(self):
        with Fixture() as fixture:
            self.bind(fixture)
            fixture.launch_environment({})
            self.complete_socket_matrix(fixture)
            arguments = self.arguments(fixture)
            self.assertFalse(fixture_module.validate_receipt(fixture.receipt(), **arguments))
        document = fixture.receipt()
        self.assertTrue(fixture_module.validate_receipt(document, **arguments))
        self.assertTrue(all(value is True for value in document["cleanup"].values()))
        text = json.dumps(document)
        for raw in (fixture._token, '"pid"', "http://", "fixture-only-", "NativeCmpKitFixture", "owned-test-path"):
            self.assertNotIn(raw, text)
        for key in arguments:
            changed = {**arguments, key: (PID + 1 if key == "native_pid" else "e" * 64)}
            self.assertFalse(fixture_module.validate_receipt(document, **changed), key)
        for key in document:
            changed = copy.deepcopy(document)
            del changed[key]
            self.assertFalse(fixture_module.validate_receipt(changed, **arguments), key)
        for section in ("cleanup", "native_binding"):
            changed = copy.deepcopy(document)
            name = "owned_workers_terminated" if section == "cleanup" else "launch_environment_process_local_only"
            changed[section][name] = 1  # Equality is not strict boolean evidence.
            self.assertFalse(fixture_module.validate_receipt(changed, **arguments), section)
        for key, value in (("refusals", True), ("connections", True), ("closed", 1), ("fixture_error", 0)):
            changed = {**document, key: value}
            self.assertFalse(fixture_module.validate_receipt(changed, **arguments), key)

    def test_exact_native_stage_schema_cannot_admit_missing_assets_replay_wrong_auth_or_parity(self):
        with Fixture() as fixture:
            self.bind(fixture)
            fixture.launch_environment({})
            self.complete_socket_matrix(fixture)
            arguments = self.arguments(fixture)
        document = fixture.receipt()
        alterations = (("restore", "url", "get", 1), ("replay", "posted", "get", 1),
                       ("headers", "state-initial", "main_authorization", 0),
                       ("headers", "state-same-final", "main_initial", 0),
                       ("resources", "state-utf8", "image", 0),
                       ("resources", "navigator-utf8", "pending", 1),
                       ("restore", "navigator", "closed", True),
                       ("headers", "state-link", "script_authorization", 1))
        for method, stage, key, value in alterations:
            changed = copy.deepcopy(document)
            changed["methods"][method]["stages"][stage][key] = value
            self.assertFalse(fixture_module.validate_receipt(changed, **arguments), (method, stage, key))
        changed = copy.deepcopy(document)
        changed["methods"]["restore"]["stages"]["unselected-stage"] = {}
        self.assertFalse(fixture_module.validate_receipt(changed, **arguments))
        changed = copy.deepcopy(document)
        changed["methods"]["restore"]["done"] = 1
        self.assertFalse(fixture_module.validate_receipt(changed, **arguments))


if __name__ == "__main__":
    unittest.main()
