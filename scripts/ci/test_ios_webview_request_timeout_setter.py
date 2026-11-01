"""New source-only regression for the exact Foundation timeout compiler repair.

Same-version passive Foundation metadata exports the explicit mutable-request
setTimeoutInterval(NSTimeInterval /* Double */): Unit while its inherited
NSURLRequest timeoutInterval is val. This does not compile or execute Kotlin,
Foundation, Apple SDKs, HTTP/TLS, Workers, UIKit or the native methods.
Only the one setter spelling and the two mechanical source pins may differ
from the failed preimage; every other existing fixture/guard byte is frozen.
"""
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
NATIVE = "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewRequestAcceptanceTest.kt"
DNS_GUARD = "scripts/ci/test_ios_webview_request_dns_focus.py"
BOUNDARY_GUARD = "scripts/ci/test_ios_webview_request_callback_boundary.py"
BASE_NATIVE_SHA256 = "569716cf0524d25b1b3c2712dbe040c0ec82cfe3db24f6dac3775e5ec15bd857"
BASE_DNS_GUARD_SHA256 = "1e62ccfc0c22296d2490b1af5be0dd0267845ad766ad993e197f2bf1299b487e"
BASE_BOUNDARY_GUARD_SHA256 = "0229f3de1d266239ddc208fbbd6b273f10b42fa434d13bcc730e7ac2d9e1533f"
BASE_OUTSIDE_HELPER_SHA256 = "caed126d24aa87b2308dee1aac4f1af1b2a91cc3f1605bcb87dcbbde4768bb14"
HELPER_SHA256 = "5b6123f2a968ccd06e4ca3ec2725a5c1e3666cd212a49a8aa28e3012fb73e6bd"
OLD_LINE = b"                timeoutInterval = 2.0\n"
NEW_LINE = b"                setTimeoutInterval(2.0)\n"
EXACT_REQUEST = (
    b"            val request = NSMutableURLRequest().apply {\n"
    b"                setURL(assertNotNull(NSURL.URLWithString(controlBase + action)))\n"
    + NEW_LINE + b"            }\n"
)
HELPER_START = b"    private fun NativeApplicationUiTest.evaluate(state: WebViewState, script: String): JavascriptResult {"
HELPER_END = b"    private class Stage("


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require_exact_timeout_repair(source, dns_guard, boundary_guard):
    if source.count(EXACT_REQUEST) != 1 or source.count(NEW_LINE) != 1 or OLD_LINE in source:
        raise ValueError("Exactly the existing mutable request needs its explicit 2-second Foundation setter")
    preimage = source.replace(NEW_LINE, OLD_LINE, 1)
    if digest(preimage) != BASE_NATIVE_SHA256:
        raise ValueError("Native methods, Worker, control bounds, response/errors and cleanup must be byte-exact")
    source_pin = digest(source)
    pin_matches = re.findall(
        b'"' + re.escape(NATIVE.encode()) + rb'":\s*"([0-9a-f]{64})"', dns_guard)
    if pin_matches != [source_pin.encode()] or dns_guard.count(source_pin.encode()) != 1:
        raise ValueError("The combined route must bind exactly the owning repaired native source")
    if digest(dns_guard.replace(source_pin.encode(), BASE_NATIVE_SHA256.encode(), 1)) != BASE_DNS_GUARD_SHA256:
        raise ValueError("Only the owning native-source pin may change in the combined route guard")
    if source.count(HELPER_START) != 1:
        raise ValueError("The existing async helper boundary must remain exact")
    start = source.index(HELPER_START)
    end = source.index(HELPER_END, start)
    helper = source[start:end].rstrip(b"\n") + b"\n"
    if source.count(helper) != 1 or digest(helper) != HELPER_SHA256:
        raise ValueError("The async callback main/once/result helper must remain byte-exact")
    outside_pin = digest(source.replace(helper, b"", 1))
    outside_matches = re.findall(rb'^OUTSIDE_HELPER_SHA256 = "([0-9a-f]{64})"$', boundary_guard, re.M)
    helper_matches = re.findall(rb'^HELPER_SHA256 = "([0-9a-f]{64})"$', boundary_guard, re.M)
    if outside_matches != [outside_pin.encode()] or helper_matches != [HELPER_SHA256.encode()]:
        raise ValueError("Only the outside-helper source pin needs mechanical rebasing")
    if boundary_guard.count(outside_pin.encode()) != 1:
        raise ValueError("The rebased outside-helper pin must occur exactly once")
    if digest(boundary_guard.replace(outside_pin.encode(), BASE_OUTSIDE_HELPER_SHA256.encode(), 1)) != BASE_BOUNDARY_GUARD_SHA256:
        raise ValueError("No callback assertion, helper identity or cleanup guard may change")
    return {"native_sha256": source_pin, "outside_helper_sha256": outside_pin,
            "async_helper_sha256": digest(helper)}


class IosWebViewRequestTimeoutSetterTests(unittest.TestCase):
    def inputs(self):
        return tuple((ROOT / name).read_bytes() for name in (NATIVE, DNS_GUARD, BOUNDARY_GUARD))

    def mutate(self, data, old, new):
        self.assertEqual(1, data.count(old), "Each new refusal model must target one exact frozen fact")
        return data.replace(old, new, 1)

    def test_explicit_setter_is_the_only_fixture_change_and_two_pins_are_mechanically_rebased(self):
        try:
            facts = require_exact_timeout_repair(*self.inputs())
        except ValueError as refusal:
            self.fail(str(refusal))
        self.assertNotEqual(BASE_NATIVE_SHA256, facts["native_sha256"])
        self.assertNotEqual(BASE_OUTSIDE_HELPER_SHA256, facts["outside_helper_sha256"])
        self.assertEqual(HELPER_SHA256, facts["async_helper_sha256"])

    def test_readonly_assignment_missing_double_setter_and_changed_timeout_are_refused(self):
        source, dns_guard, boundary_guard = self.inputs()
        variants = (OLD_LINE, b"", NEW_LINE + NEW_LINE,
                    NEW_LINE.replace(b"2.0", b"0.0"), NEW_LINE.replace(b"2.0", b"20.0"),
                    NEW_LINE.replace(b"2.0", b"2"), NEW_LINE.replace(b"setTimeoutInterval", b"setCachePolicy"))
        for index, replacement in enumerate(variants):
            with self.subTest(variant=index):
                mutant = self.mutate(source, NEW_LINE, replacement)
                with self.assertRaises(ValueError):
                    require_exact_timeout_repair(mutant, dns_guard, boundary_guard)

    def test_native_methods_worker_bounds_response_errors_and_cleanup_mutations_are_refused(self):
        source, dns_guard, boundary_guard = self.inputs()
        variants = (
            (b'assertEquals(7 * transport["alert"], transport["response_bytes"])',
             b'assertEquals(0, transport["response_bytes"])'),
            (b'it["client_cancelled"] == 1 && it["pending"] == 0 && it["closed"] == 1',
             b'it["pending"] == 0'),
            (b'assertTrue(failure.value == null,', b'assertTrue(true,'),
            (b'assertEquals(200L, (response.value as? NSHTTPURLResponse)?.statusCode)',
             b'assertEquals(204L, (response.value as? NSHTTPURLResponse)?.statusCode)'),
            (b'body.length in 1uL..2048uL', b'body.length in 0uL..4096uL'),
            (b'assertFalse(NSThread.isMainThread, "Never block UIApplicationMain with fixture control")',
             b'assertTrue(NSThread.isMainThread, "Never block UIApplicationMain with fixture control")'),
            (b'NSURLConnection.sendSynchronousRequest(request, response.ptr, failure.ptr)',
             b'NSURLConnection.sendSynchronousRequest(request, response.ptr, null)'),
            (b'Regex("[0-9a-f]{32}")', b'Regex("[0-9a-f]{1,32}")'),
            (b'value in 1..65535', b'value in 0..65535'),
            (b'NSProcessInfo.processInfo.systemUptime + 10.0', b'NSProcessInfo.processInfo.systemUptime + 20.0'),
            (b'usleep(50_000u)', b'usleep(500_000u)'),
            (b'try { block(scope) } finally { scope.cancel() }', b'block(scope)'),
        )
        for index, (old, new) in enumerate(variants):
            with self.subTest(variant=index):
                mutant = self.mutate(source, old, new)
                with self.assertRaises(ValueError):
                    require_exact_timeout_repair(mutant, dns_guard, boundary_guard)

    def test_stale_pins_other_identities_and_existing_guard_weakening_are_refused(self):
        source, dns_guard, boundary_guard = self.inputs()
        source_pin = digest(source).encode()
        start = source.index(HELPER_START)
        end = source.index(HELPER_END, start)
        helper = source[start:end].rstrip(b"\n") + b"\n"
        outside_pin = digest(source.replace(helper, b"", 1)).encode()
        dns_variants = (
            (source_pin, BASE_NATIVE_SHA256.encode()),
            (b'25efe05ca6ce4cc2f027dc74eaf22a3a74cd4213d315940be9b64bdf7f0fe594', b'0' * 64),
            (b'a5b4780ab39822a4ee261c07d434bacb9ce9fe72943c1924eeaddcbbeb1e17a7', b'0' * 64),
            (b'self.assertEqual(pin, lt.sha256(lt.ROOT / source), "Existing native/fixture bytes must remain unchanged")',
             b'self.assertTrue(True)'),
        )
        boundary_variants = (
            (outside_pin, BASE_OUTSIDE_HELPER_SHA256.encode()),
            (HELPER_SHA256.encode(), b'0' * 64),
            (b'self.assertIn("assertEquals(1, calls)", checking)',
             b'self.assertIn("assertEquals(2, calls)", checking)'),
            (b'self.assertIn("prior.addSuppressed(cleanup)", host)', b'self.assertTrue(True)'),
        )
        for index, (old, new) in enumerate(dns_variants):
            with self.subTest(guard="dns", variant=index):
                mutant = self.mutate(dns_guard, old, new)
                with self.assertRaises(ValueError):
                    require_exact_timeout_repair(source, mutant, boundary_guard)
        for index, (old, new) in enumerate(boundary_variants):
            with self.subTest(guard="boundary", variant=index):
                mutant = self.mutate(boundary_guard, old, new)
                with self.assertRaises(ValueError):
                    require_exact_timeout_repair(source, dns_guard, mutant)


if __name__ == "__main__":
    unittest.main()
