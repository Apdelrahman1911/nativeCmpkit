"""Owning source-fixture recovery only; no accepted8/9 test replay or native work."""
import ast
import hashlib
from pathlib import Path
import tempfile
import unittest

import library_tests as lt

ROOT = Path(__file__).resolve().parents[2]
GUARD = "scripts/ci/test_ios_share_owned_root_barriers.py"
FOCUS = "scripts/ci/test_ios_share_presentation_focus.py"
GUARD_SHA256 = '71467292fa2d21fb68615aea5dc4f4f17f291cfe550b2939200b5343f1287f24'
FOCUS_SHA256 = "edcc6f136b1d786358dc547946680b9f4ea8d82af339ca31213cfa47d72bfb6f"


_GUARD_COMPILER_REPAIR_172 = {'after_sha256': '7f06ae1ecaf0beacd2ffbe24f95c6baa1d4b764b28a2023eb1ae4153dba0407b', 'before': 'def _read_sources():\n    return {relative: _support_before_fixture_repair169(relative, (ROOT / relative).read_bytes().decode("utf-8"))\n            for relative in (*_SPEC["changed_paths"], *_SPEC["support_paths"])}', 'after': '_COMPILER_SOURCE_REPAIRS_172 = {\'calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/IosSharePresentationOwnershipTest.kt\': {\'before_sha256\': \'0ca8ef9a5b0c3cfd8922c40a248058efe4f521e560b2752267d2048ce54ec0a6\', \'after_sha256\': \'250b536388c872d6fd975ad009ca47a750575df28b1eb0d1981ba6d124d63b9d\', \'fragments\': [{\'before\': \'import kotlinx.coroutines.Dispatchers\\n\', \'after\': \'import kotlinx.coroutines.Dispatchers\\nimport kotlinx.coroutines.IO\\n\'}, {\'before\': \'assertEquals((1..index + 1).map { it to ShareOutcome.Completed }, deliveries)\', \'after\': \'assertEquals<List<Pair<Int, ShareOutcome>>>((1..index + 1).map { it to ShareOutcome.Completed }, deliveries)\'}, {\'before\': \'assertEquals((1..3).map { it to ShareOutcome.Completed }, deliveries)\', \'after\': \'assertEquals<List<Pair<Int, ShareOutcome>>>((1..3).map { it to ShareOutcome.Completed }, deliveries)\'}]}, \'calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/internal/NativeShareApplicationHost.kt\': {\'before_sha256\': \'f6917c04e5f9a39ec8a74a1953c67a82d27c7cb02f27cb69287534a84106754d\', \'after_sha256\': \'e2b6affcea3a3a34b9d1b95f5d60e5d492efbca55f8a02ab38ac459cf23fb953\', \'fragments\': [{\'before\': \'import platform.UIKit.UIWindow\\n\', \'after\': \'import platform.UIKit.UIWindow\\nimport platform.UIKit.transitionCoordinator\\n\'}]}}\n\n\ndef _source_before_compiler_repair172(relative, text):\n    """Only exact missing-import/type-inference repairs reconstruct the reviewed fixture."""\n    if relative not in _COMPILER_SOURCE_REPAIRS_172:\n        return text\n    binding = _COMPILER_SOURCE_REPAIRS_172[relative]\n    if _sha256(text) != binding["after_sha256"]:\n        raise ValueError("Exact owning compiler fixture repair is required")\n    for fragment in reversed(binding["fragments"]):\n        if text.count(fragment["after"]) != 1:\n            raise ValueError("Exact unique compiler inverse is required")\n        text = text.replace(fragment["after"], fragment["before"], 1)\n    if _sha256(text) != binding["before_sha256"]:\n        raise ValueError("Compiler inverse changed the reviewed native assertion bytes")\n    return text\n\n\ndef _read_sources():\n    return {relative: _support_before_fixture_repair169(relative,\n                _source_before_compiler_repair172(relative, (ROOT / relative).read_bytes().decode("utf-8")))\n            for relative in (*_SPEC["changed_paths"], *_SPEC["support_paths"])}'}


_GUARD_SHARE188_OBSERVATION = {'before_sha256': '7f06ae1ecaf0beacd2ffbe24f95c6baa1d4b764b28a2023eb1ae4153dba0407b', 'after_sha256': '08fa3b3ce8e3fa2bb3d6c5c799a8466e95864f8025ab498dd7af6ceddead9384', 'fragments': [{'id': 'exact-host-addendum-before-original-169-172-owning-admission', 'before': 'def _read_sources():\n    return {relative: _support_before_fixture_repair169(relative,\n                _source_before_compiler_repair172(relative, (ROOT / relative).read_bytes().decode("utf-8")))\n            for relative in (*_SPEC["changed_paths"], *_SPEC["support_paths"])}', 'after': '_SHARE188_OBSERVATION = {\'path\': \'calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/internal/NativeShareApplicationHost.kt\', \'before_sha256\': \'e2b6affcea3a3a34b9d1b95f5d60e5d492efbca55f8a02ab38ac459cf23fb953\', \'after_sha256\': \'d3dc78ba45e1047eb7d6a85005dc3a08443ded38432c78d28d5c65e1c85d3a17\', \'fragments\': [{\'id\': \'per-root-optional-observer\', \'before\': \'    private val nativeWork = mutableListOf<OwnedNativePresentation>()\\n\', \'after\': \'    private val nativeWork = mutableListOf<OwnedNativePresentation>()\\n    private var terminalInputObservation: ShareTerminalInputObservation? = null\\n\', \'before_fragment_sha256\': \'164d40eefa77f462207431473819ecde7f228c240c504565dbf0bb0d25ece62c\', \'after_fragment_sha256\': \'aa03293d7e13f9e426bd7b9e4de917a0c79c50b8e70d12b85c0eb0c125be3132\'}, {\'id\': \'exact-native-arguments-opt-in\', \'before\': \'            window = requireOwnedApplicationWindow()\\n\', \'after\': \'            window = requireOwnedApplicationWindow()\\n            terminalInputObservation = ShareTerminalInputObservation.forExactArguments(applicationArguments)\\n\', \'before_fragment_sha256\': \'c81bfec28b582e33c9dc74d983fea724d60a1c0f59846b2b3fad5bd11a1cee31\', \'after_fragment_sha256\': \'ea834a56306c9721c1c165e2530e1188022f92e039828f617e04c6bf3562bb8c\'}, {\'id\': \'marker-after-existing-real-acknowledgement\', \'before\': \'        checkNotNull(nativeWork.singleOrNull { sameNativeObject(it.controller, native) }) {\\n            "Refuse an unregistered native dismissal acknowledgement"\\n        }.dismissalCompleted()\\n\', \'after\': \'        val work = checkNotNull(nativeWork.singleOrNull { sameNativeObject(it.controller, native) }) {\\n            "Refuse an unregistered native dismissal acknowledgement"\\n        }\\n        work.dismissalCompleted()\\n        terminalInputObservation?.dismissalAcknowledged(work.request)\\n\', \'before_fragment_sha256\': \'1ce61a9550483b54346f790afe2aeedf891d1a3dcda277e5ccfedb11188bd45f\', \'after_fragment_sha256\': \'2ca65d52c721d9a51aa7d42b728568b34572cd424917ae8b3f0612b8d1f9f188\'}, {\'id\': \'delegate-after-actual-request-retention\', \'before\': \'                nativeWork += OwnedNativePresentation(request.controller, request)\\n\', \'after\': \'                nativeWork += OwnedNativePresentation(request.controller, request)\\n                terminalInputObservation?.capture(lease.owner, request)\\n\', \'before_fragment_sha256\': \'a2707ed1d7c42e3bd40eb71ec4c76e32cf38fbb691be7ec71b1d66ef08c2a0f6\', \'after_fragment_sha256\': \'e599f96e638ed039128b97d1b7eefc8a0d86293a75b07c51ea0fa3c2b1669614\'}, {\'id\': \'nonmasking-failure-only-emitter\', \'before\': \'    internal fun close() {\\n\', \'after\': \'    internal fun emitActivityTerminalFailureObservation() {\\n        try { onApplicationMain { terminalInputObservation?.emitFailure() } }\\n        catch (_: Throwable) { /* Observation cannot replace the original assertion/refusal. */ }\\n    }\\n\\n    internal fun close() {\\n\', \'before_fragment_sha256\': \'312700c85943cb7e29280c5c9e5e721c7b06bca138242ba499bd5e3f242201d1\', \'after_fragment_sha256\': \'96f7201d18d53fb1bb5dc5b11cd664bc4ad63bab4ec1c41ef7eb5b1557a46151\'}, {\'id\': \'observer-teardown-inside-existing-all-barriers\', \'before\': \'                // Only actual owner/native/root barriers release these test-only retaining leases.\\n                closed = true\\n\', \'after\': \'                // Only actual owner/native/root barriers release these test-only retaining leases.\\n                terminalInputObservation?.closeAfterVerifiedTeardown()\\n                terminalInputObservation = null\\n                closed = true\\n\', \'before_fragment_sha256\': \'9d6b48115952d14453d35416a0fb8fa44a4539a581150c9c98befa95753f9db5\', \'after_fragment_sha256\': \'e4616d0098f50affeaf9fcb81790bee3c82b23f80ea987737908a7423eaf9ba9\'}, {\'id\': \'preserve-exact-primary-and-original-cleanup\', \'before\': \'    try { host.block() } catch (error: Throwable) { failure = error; throw error } finally {\\n\', \'after\': \'    try { host.block() } catch (error: Throwable) {\\n        failure = error\\n        host.emitActivityTerminalFailureObservation()\\n        throw error\\n    } finally {\\n\', \'before_fragment_sha256\': \'0c82773a17445cf1e115ad8e7f72dafa3cb1725c9a2ae355329db07772d61656\', \'after_fragment_sha256\': \'4c57aa04c03c92ed6cb622c64dd91014b79882731a6feeb17ca70409c346c0e1\'}]}\n\n\ndef _source_before_share188_observation(relative, text):\n    """Only the exact per-request observation may reconstruct retained Share172 source."""\n    if relative != _SHARE188_OBSERVATION["path"]:\n        return text\n    if _sha256(text) != _SHARE188_OBSERVATION["after_sha256"]:\n        raise ValueError("Exact Share188 observation host postimage is required")\n    for fragment in reversed(_SHARE188_OBSERVATION["fragments"]):\n        if (hashlib.sha256(fragment["before"].encode()).hexdigest() != fragment["before_fragment_sha256"] or\n                hashlib.sha256(fragment["after"].encode()).hexdigest() != fragment["after_fragment_sha256"] or\n                text.count(fragment["after"]) != 1):\n            raise ValueError("Exact unique Share188 host inverse is required")\n        text = text.replace(fragment["after"], fragment["before"], 1)\n    if _sha256(text) != _SHARE188_OBSERVATION["before_sha256"]:\n        raise ValueError("Share188 inverse changed original host assertions or lease bytes")\n    return text\n\n\ndef _read_sources():\n    return {relative: _support_before_fixture_repair169(relative,\n                _source_before_compiler_repair172(relative,\n                    _source_before_share188_observation(relative, (ROOT / relative).read_bytes().decode("utf-8"))))\n            for relative in (*_SPEC["changed_paths"], *_SPEC["support_paths"])}', 'before_fragment_sha256': '0e632998c6dc5047fb14ec9a41061efc2fe0e3dc82ed58cdaf00397af4e56c23', 'after_fragment_sha256': '650407bec444124720f50a47c1bfbe382a6e61f31402c521c603c42903f9b302'}]}


def guard_before_share188_observation(raw):
    """Only exact host-observation admission reconstructs the unchanged settings NEW2 guard."""
    if hashlib.sha256(raw).hexdigest() != _GUARD_SHARE188_OBSERVATION["after_sha256"]:
        raise ValueError("Exact Share188-composed owning guard is required")
    for fragment in reversed(_GUARD_SHARE188_OBSERVATION["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or raw.count(after) != 1):
            raise ValueError("Exact unique Share188 owning-guard inverse is required")
        raw = raw.replace(after, before, 1)
    if hashlib.sha256(raw).hexdigest() != _GUARD_SHARE188_OBSERVATION["before_sha256"]:
        raise ValueError("Share188 owning-guard inverse changed accepted settings controls")
    return raw


def guard_before_compiler_repair172(raw):
    """Exact disjoint compiler admission addition; original NEW2 bindings stay unchanged."""
    if hashlib.sha256(raw).hexdigest() != _GUARD_COMPILER_REPAIR_172["after_sha256"]:
        raise ValueError("Exact compiler-composed guard image required")
    before = _GUARD_COMPILER_REPAIR_172["before"].encode()
    after = _GUARD_COMPILER_REPAIR_172["after"].encode()
    if raw.count(after) != 1:
        raise ValueError("Exact unique compiler guard inverse required")
    historical = raw.replace(after, before, 1)
    if hashlib.sha256(historical).hexdigest() != GUARD_SHA256:
        raise ValueError("Disjoint compiler addition changed original NEW2 guard helpers")
    return historical


def selected_inverse():
    raw = guard_before_compiler_repair172(guard_before_share188_observation((ROOT / GUARD).read_bytes()))
    if hashlib.sha256(raw).hexdigest() != GUARD_SHA256:
        raise ValueError("Exact owning guard correction bytes required")
    tree = ast.parse(raw)
    names = {"_FOCUS_FIXTURE_REPAIRED_SHA256", "_FOCUS_FIXTURE_BEFORE", "_FOCUS_FIXTURE_AFTER", "FOCUS_GUARD", "_SPEC"}
    nodes = [n for n in tree.body
             if isinstance(n, ast.FunctionDef) and n.name in {"_sha256", "_support_before_fixture_repair169"}
             or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets)]
    namespace = {"hashlib": hashlib}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<only-owning-fixture-inverse>", "exec"), namespace)
    return namespace


class ShareSettingsFixtureRecoveryTests(unittest.TestCase):
    def test_fixture_matches_the_literal_repository_include_contract_without_parser_relaxation(self):
        source = (ROOT / FOCUS).read_bytes()
        self.assertEqual(FOCUS_SHA256, hashlib.sha256(source).hexdigest())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "calf-share").mkdir()
            (root / "calf-share/build.gradle.kts").write_text("// synthetic\n")
            settings = root / "settings.gradle.kts"
            settings.write_text('include(":calf-share")\n')
            with self.assertRaisesRegex(ValueError, "literal settings include block"):
                lt.projects(root)
            settings.write_text('include(\n    ":calf-share",\n)\n')
            self.assertEqual({"calf-share": ":calf-share"}, lt.projects(root))

    def test_support_inverse_admits_only_the_exact_owning_repair_and_rejects_drift(self):
        namespace = selected_inverse()
        inverse = namespace["_support_before_fixture_repair169"]
        source = (ROOT / FOCUS).read_text()
        historical = inverse(FOCUS, source)
        expected = namespace["_SPEC"]["support_sha256"][FOCUS]
        self.assertEqual(expected, hashlib.sha256(historical.encode()).hexdigest())
        for changed in (historical, source + "\n", source.replace(namespace["_FOCUS_FIXTURE_AFTER"], "", 1),
                        source + namespace["_FOCUS_FIXTURE_AFTER"]):
            with self.subTest(shape=len(changed)), self.assertRaises(ValueError):
                inverse(FOCUS, changed)
        self.assertEqual("unchanged", inverse("other-support", "unchanged"))
