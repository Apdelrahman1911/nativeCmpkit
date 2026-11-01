# SPDX-License-Identifier: Apache-2.0
"""Missing-only route/source/XML guards. Synthetic checks are not Foundation acceptance."""
from collections import Counter
import copy
from pathlib import Path
import re
import tempfile
import time
import unittest

import ios_ui_application as app
import library_tests as r
import workflow_matrix as matrix
from test_android_webview_request_state import body_after
import test_ios_picker_batch_focus as batch


PHOTO_DELEGATE_SOURCE = "calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/PhotoPickerDelegate.kt"
PHOTO_LAUNCHER_SOURCE = "calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt"


def _kotlin_tokens(source):
    """Lexical source witnesses only: nested comments and literals cannot supply code tokens."""
    def comment_end(index):
        if source.startswith("//", index):
            end = source.find("\n", index + 2)
            return len(source) if end < 0 else end
        depth, index = 1, index + 2
        while index < len(source) and depth:
            if source.startswith("/*", index): depth += 1; index += 2
            elif source.startswith("*/", index): depth -= 1; index += 2
            else: index += 1
        if depth: raise ValueError("Unclosed Kotlin source comment")
        return index

    def literal_end(index):
        raw = source.startswith('"""', index)
        quote = '"""' if raw else source[index]
        index += len(quote)
        while index < len(source):
            if not raw and source[index] == "\\": index += 2
            elif source.startswith(quote, index): return index + len(quote)
            elif quote != "'" and source.startswith("${", index):
                # Kotlin templates can themselves contain quoted literals/comments.
                depth, index = 1, index + 2
                while index < len(source) and depth:
                    if source.startswith(("//", "/*"), index): index = comment_end(index)
                    elif source[index] in "\"'": index = literal_end(index)
                    elif source[index] == "{": depth += 1; index += 1
                    elif source[index] == "}": depth -= 1; index += 1
                    else: index += 1
                if depth: raise ValueError("Unclosed Kotlin source template")
            else: index += 1
        raise ValueError("Unclosed Kotlin source literal")

    tokens, index = [], 0
    while index < len(source):
        if source[index].isspace(): index += 1
        elif source.startswith(("//", "/*"), index): index = comment_end(index)
        elif source[index] in "\"'":
            end = literal_end(index)
            tokens.append(source[index:end]); index = end
        else:
            match = re.match(r"[A-Za-z_][A-Za-z_0-9]*|[0-9][A-Za-z_0-9]*|===|!==|==|!=|\|\||&&|->|::|\?\.|\?:|\+=|.",
                             source[index:])
            tokens.append(match.group()); index += len(match.group())
    return tokens


def _kotlin_positions(tokens, fragment):
    wanted = _kotlin_tokens(fragment)
    return [index for index in range(len(tokens) - len(wanted) + 1)
            if tokens[index:index + len(wanted)] == wanted]


def _kotlin_block(tokens, anchor):
    matches = _kotlin_positions(tokens, anchor)
    if len(matches) != 1:
        raise ValueError("Require one exact executable owning source declaration")
    start = matches[0] + len(_kotlin_tokens(anchor))
    if start >= len(tokens) or tokens[start] != "{":
        raise ValueError("The complete owning source signature must immediately open its block")
    depth = 1
    for index in range(start + 1, len(tokens)):
        if tokens[index] == "{": depth += 1
        elif tokens[index] == "}": depth -= 1
        if depth == 0: return tokens[start + 1:index]
    raise ValueError("Unclosed executable owning Kotlin source block")


def require_provider_arrival_boundary(source, delegate_source, launcher_source):
    """Source-qualify the shared lazy gate; never Photos extraction or native acceptance."""
    delegate = _kotlin_block(_kotlin_tokens(delegate_source), """
        internal class PhotoPickerDelegate(
            private val session: IosDialogSession,
            private val onPicked: (List<() -> NSItemProvider>) -> Unit,
            private val onCancelled: () -> Unit,
        ) : NSObject(), PHPickerViewControllerDelegateProtocol, UIAdaptivePresentationControllerDelegateProtocol
    """)
    for signature, expected in (
        ("override fun picker(picker: PHPickerViewController, didFinishPicking: List<*>)", """
            finishProviderSources(picker) {
                didFinishPicking.filterIsInstance<PHPickerResult>().map { result -> { result.itemProvider } }
            }
        """),
        ("internal fun pickerProviders(picker: PHPickerViewController, providers: List<NSItemProvider>,)", """
            finishProviderSources(picker) { providers.map { provider -> { provider } } }
        """),
        ("private fun finishProviderSources(picker: PHPickerViewController, sources: () -> List<() -> NSItemProvider>,)", """
            if (picker != session.controller || !session.claimResult()) return
            onPicked(sources())
        """),
    ):
        if _kotlin_block(delegate, signature) != _kotlin_tokens(expected):
            raise ValueError("Native and controlled lazy arrivals must share controller-before-claim, then traversal")
    if len(_kotlin_positions(delegate, "finishProviderSources")) != 3 or len(_kotlin_positions(delegate, "onPicked(")) != 1:
        raise ValueError("No separate or private production arrival may bypass the shared owning gate")

    launcher = _kotlin_tokens(launcher_source)
    staging = _kotlin_block(launcher, "fun stageAndDeliver(stage: suspend (MutableList<KmpFile>) -> Unit)")
    if staging != _kotlin_tokens("""
        session.job = scope.launch {
            val owned = mutableListOf<KmpFile>()
            var transferred = false
            try {
                val failure = try {
                    withContext(Dispatchers.IO) { stage(owned) }
                    currentCoroutineContext().ensureActive()
                    if (session.cancelled) throw CancellationException("Picker disposed")
                    null
                } catch (cancelled: CancellationException) { throw cancelled }
                catch (error: Exception) {
                    if (error is FilePickerException) error else FilePickerException("Could not read picked files", error)
                }
                owner.end(session)
                session.awaitFinished()
                currentCoroutineContext().ensureActive()
                if (session.cancelled) throw CancellationException("Picker disposed")
                if (failure != null) currentOnError(failure)
                else {
                    transferred = true
                    currentOnResult(owned.toList())
                }
            } finally {
                if (!transferred) owned.forEach { it.releaseTemporaryCopy() }
                owner.end(session)
            }
        }
    """):
        raise ValueError("Keep the existing IO staging/owner/cancellation/transfer/cleanup path")
    picked = _kotlin_block(launcher, "val delegate = PhotoPickerDelegate(session, onPicked =")
    if picked != _kotlin_tokens("""
        results ->
        val picked = results.limitedTo(launchMode)
        session.requestDismissal()
        stageAndDeliver { files ->
            for (result in picked) {
                currentCoroutineContext().ensureActive()
                val file = result().loadFileRepresentationForTypeIdentifierSuspend(launchType)
                    ?: throw FilePickerException("A selected photo/video could not be copied")
                files += file
            }
        }
    """):
        raise ValueError("Limit before staging and invoke each supplier only after ensureActive inside existing IO staging")

    tokens = _kotlin_tokens(source)
    method = _kotlin_block(tokens, "@Test fun " + r.IOS_PICKER_PROVIDER_CANCELLATION_METHODS[0] +
                           "() = runApplicationUiTest")
    installed = """
        val picker = runOnIdle { assertIs<PHPickerViewController>(parent.presentedViewController) }
        val delegate = runOnIdle { assertIs<PhotoPickerDelegate>(picker.delegate) }
        val providers = listOf(first.provider, pending.provider)
        runOnIdle {
            assertTrue(sameNativeObject(providers[0], first.provider))
            assertTrue(sameNativeObject(providers[1], pending.provider))
            delegate.pickerProviders(picker, providers)
        }
    """
    if len(_kotlin_positions(method, installed)) != 1:
        raise ValueError("Require the actual installed typed owning delegate and identical registered native providers")
    arrivals = _kotlin_positions(method, "delegate.pickerProviders(picker, providers)")
    if len(arrivals) != 3 or method.count("pickerProviders") != 3 or method.count("delegate") != 5:
        raise ValueError("Only initial, duplicate and post-disposal arrivals through the installed delegate are allowed")
    boundaries = ("runOnIdle { included.value = false }", "pending.completeCancelledTransport()",
                  "pending.heldCompletionReturned.value == 1")
    positions = [_kotlin_positions(method, fragment) for fragment in boundaries]
    if any(len(matches) != 1 for matches in positions) or not (
            arrivals[0] < arrivals[1] < positions[0][0] < positions[1][0] < positions[2][0] < arrivals[2]):
        raise ValueError("Duplicate precedes public disposal; post-disposal arrival follows distinct producer and native client acknowledgements")
    forbidden = ("PHPickerResult", "OwnedProviderResult", "PhotoPickerDelegate", "IosDialogSession", "IosDialogOwner",
                 "finishProviderSources", "claimResult", "onPicked", "stageAndDeliver", "stagePickedUrls",
                 "loadFileRepresentationForTypeIdentifierSuspend", "createPHPickerViewController",
                 "suspendCancellableCoroutine", "resume", "setValue", "setValueForKey", "valueForKey", "forKey",
                 "objc_msgSend", "method_setImplementation", "method_exchangeImplementations",
                 "NSClassFromString", "NSSelectorFromString", "performSelector")
    # The sole PhotoPickerDelegate token in C3 is its checked installed native type.
    if tokens.count("PhotoPickerDelegate") != 1 or any(token in tokens for token in forbidden if token != "PhotoPickerDelegate"):
        raise ValueError("No unavailable/fake result construction, new owner, private arrival or ObjC/KVC bypass")
    if any(token.startswith('"') and "${" in token for token in method):
        raise ValueError("Controlled arrival witness code cannot be hidden inside a Kotlin string template")
    if any(token in method for token in ("loadFileRepresentationForTypeIdentifier", "registerFileRepresentationForTypeIdentifier")):
        raise ValueError("The C3 arrival must use the public launcher's native loader, not a direct test invocation")


def require_provider_witnesses(source, *, delegate_source=None, launcher_source=None):
    """Protect causal/public/native boundaries without pinning unrelated source formatting."""
    require_provider_arrival_boundary(
        source,
        (r.ROOT / PHOTO_DELEGATE_SOURCE).read_text() if delegate_source is None else delegate_source,
        (r.ROOT / PHOTO_LAUNCHER_SOURCE).read_text() if launcher_source is None else launcher_source,
    )
    tokens = _kotlin_tokens(source)
    witness_signature = "private class WitnessedNativeItemProvider : NSItemProvider()"
    expected_witness = """private class WitnessedNativeItemProvider : NSItemProvider() {
    val loadRequests = AtomicInt(0)
    val clientEntered = AtomicInt(0)
    val clientReturned = AtomicInt(0)
    private val lock = NSLock()
    private var cleanupStarted = false
    private var actualProgress: NSProgress? = null
    override fun loadFileRepresentationForTypeIdentifier(
        typeIdentifier: String, completionHandler: (NSURL?, NSError?) -> Unit,
    ): NSProgress {
        protect {
            check(!cleanupStarted) { "A closed fixture must not begin another native request" }
            loadRequests.incrementOwned()
        }
        val progress = super.loadFileRepresentationForTypeIdentifier(typeIdentifier) { url, error ->
            protect { clientEntered.incrementOwned() }
            try { completionHandler(url, error) } finally {
                protect { clientReturned.incrementOwned() }
            }
        }
        protect { actualProgress = progress }
        return progress
    }
    // A snapshot before the explicit producer call, not a causal/payload classification.
    fun clientCounts(): List<Int> = protect {
        listOf(clientEntered.value, clientReturned.value)
    }
    fun cancelForCleanup() {
        val progress = protect { cleanupStarted = true; actualProgress }
        progress?.cancel()
    }
    private fun <T> protect(action: () -> T): T { lock.lock(); try { return action() } finally { lock.unlock() } }
}"""
    if (_kotlin_block(tokens, witness_signature) !=
            _kotlin_block(_kotlin_tokens(expected_witness), witness_signature)):
        raise ValueError("Require genuine super/progress/unchanged callback entry-exit and a locked descriptive client snapshot")
    complete_signature = "fun completeCancelledTransport()"
    expected_completion = """    fun completeCancelledTransport() {
        check(cancelled.value == 1) { "Observe native child cancellation before completing its transport" }
        check(closedHandles.value == 2) { "Observe both native producer handle closes before completing its transport" }
        check(!manager.fileExistsAtPath(partialPath))
        val handler = protect {
            check(holdAfterFirstChunk && !cleanupStarted) { "Only the held live producer may acknowledge this completion" }
            val pending = assertNotNull(completion)
            check(heldCompletionIssued.compareAndSet(0, 1)) { "A held producer completion must not be issued twice" }
            completion = null
            pending
        }
        // This is the actual registered Foundation producer completion. Its normal
        // return is not a client callback, a late URL, or an NSError-identity witness.
        handler.invoke(null, false, cancellationError())
        check(heldCompletionReturned.compareAndSet(0, 1)) { "A held producer completion must not return twice" }
    }"""
    if (_kotlin_block(tokens, complete_signature) !=
            _kotlin_block(_kotlin_tokens(expected_completion), complete_signature)):
        raise ValueError("Only the held real registered producer handler may be consumed once, invoked outside its lock, and acknowledge normal return")
    for name, references in (("heldCompletionIssued", 4), ("heldCompletionReturned", 5)):
        if (len(_kotlin_positions(tokens, "val " + name + " = AtomicInt(0)")) != 1 or
                len(_kotlin_positions(tokens, name)) != references):
            raise ValueError("Registered producer acknowledgements are initialized once and cannot be forged or supplied by native client counters")
    cancelled = body_after(source, "progress.cancellationHandler =")
    if ("cancelled.compareAndSet(0, 1)" not in cancelled or
            "protect { closeHandlesLocked(); removePartialLocked() }" not in cancelled):
        raise ValueError("The actual cooperative producer cancellation must close its handles before removing partial output")
    method = body_after(source, "@Test fun " + r.IOS_PICKER_PROVIDER_CANCELLATION_METHODS[0])
    steps = ("delegate.pickerProviders(picker, providers)", "pending.firstChunkCopied.value == 1",
             "ownedDescriptorCounts(pending.sourceIdentity, partialIdentity)",
             "runOnIdle { included.value = false }", "pending.cancelled.value == 1 && pending.closedHandles.value == 2",
             "assertEquals(0, pending.heldCompletionIssued.value)", "assertEquals(0, pending.heldCompletionReturned.value)",
             "val clientBeforeHeldCompletion = pending.provider.clientCounts()", "pending.completeCancelledTransport()",
             "pending.provider.clientReturned.value == 1 &&\n                pending.heldCompletionReturned.value == 1",
             "retained.launch()")
    if any(token not in method for token in steps) or (
            [method.index(token) for token in steps] != sorted(method.index(token) for token in steps)):
        raise ValueError("Real in-flight native copy and public disposal/cleanup precede separate producer and actual native client acknowledgement")
    method_tokens = _kotlin_block(tokens, "@Test fun " + r.IOS_PICKER_PROVIDER_CANCELLATION_METHODS[0] +
                                  "() = runApplicationUiTest")
    for fragment in (
        "waitForNative { pending.provider.clientReturned.value == 1 && pending.heldCompletionReturned.value == 1 }",
        "assertEquals(1, pending.provider.clientEntered.value)",
        "assertEquals(1, pending.provider.clientReturned.value)",
        "assertEquals(1, pending.heldCompletionIssued.value)",
        "assertEquals(1, pending.heldCompletionReturned.value)",
    ):
        if len(_kotlin_positions(method_tokens, fragment)) != 1:
            raise ValueError("Both actual native callback entry-exit and real registered producer normal return remain required")
    for forbidden in ("pending.close()", "pending.provider.cancelForCleanup()",
                      "first.close()", "first.provider.cancelForCleanup()",
                      "pending.provider.clientEntered.value =", "pending.provider.clientReturned.value ="):
        if _kotlin_positions(method_tokens, forbidden):
            raise ValueError("Cleanup-only cancellation and manually supplied client counts are never C3 native evidence")
    required = ("val providers = listOf(first.provider, pending.provider)", "registerFileRepresentationForTypeIdentifier(",
                "NSItemProviderRepresentationVisibilityOwnProcess", "progress.cancellationHandler =",
                "progress.cancellable = true", "NSFileHandle.fileHandleForReadingAtPath(sourcePath)",
                "NSFileHandle.fileHandleForWritingAtPath(partialPath)", "readDataOfLength(65_536uL)",
                "progress.completedUnitCount = chunk.length.toLong()", "closeHandlesLocked(); removePartialLocked()",
                "assertTrue(delivered.isEmpty()); assertTrue(errors.isEmpty())", "assertEquals(before, pickerDirectories())",
                "ownedDescriptorCounts(pending.sourceIdentity, partialIdentity, stagedIdentity)",
                "assertContentEquals(bytes, KmpFile(NSURL.fileURLWithPath(pending.sourcePath)).readByteArray())",
                "check(provider.loadRequests.value == 1 && provider.clientEntered.value == 1)",
                "if (callbackAcknowledged) clean {", "getdtablesize()", "fstat(fd, observed.ptr)")
    if any(token not in source for token in required):
        raise ValueError("Missing genuine native producer/progress/descriptor/staging/source/cleanup witness")
    if re.search(r"\b(?:assumeTrue|assumeFalse|presentationCompleted|resume|Robolectric|mockk|Mockito)\s*\(", source):
        raise ValueError("No fake admission, continuation, mock or skipped native witness")


class IosPickerProviderCancellationFocusTests(unittest.TestCase):
    def arrival_sources(self):
        return ((r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text(),
                (r.ROOT / PHOTO_DELEGATE_SOURCE).read_text(),
                (r.ROOT / PHOTO_LAUNCHER_SOURCE).read_text())

    def plan(self, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-file-picker",),
                      focus=r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS)

    def test_one_missing_method_uses_existing_genuine_app_and_one_canonical_slot(self):
        row, = matrix.matrix("ios-picker-provider-cancellation")["include"]
        self.assertEqual(("ios-iphone", "calf-file-picker", r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS),
                         tuple(row[key] for key in ("slot", "test-modules", "test-focus")))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        item, = plan["expected"]
        self.assertEqual(":calf-file-picker:" + r.IOS_APPLICATION_TASK, item["task"])
        self.assertEqual("genuine-uikit-application", item["native_test_host"])
        self.assertEqual(1, len(item["required_testcases"]))
        self.assertIn(r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE, item["test_source_files"])
        self.assertIsNone(app.profile_debug_entitlements(r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS))

    def test_exact_gradle_and_native_filters_exclude_all_accepted_old_methods(self):
        plan = self.plan()
        item, = plan["expected"]
        selector = r.IOS_PICKER_PROVIDER_CANCELLATION_CLASS + "." + r.IOS_PICKER_PROVIDER_CANCELLATION_METHODS[0]
        self.assertEqual(selector, item["test_filter"])
        self.assertEqual(["--tests", selector], r.gradle_command("ios", plan, simulator=batch.fixtures.DEVICE)[-2:])
        self.assertEqual(r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS,
                         app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + selector]))
        selected = {(case["classname"], case["name"])
                    for case in r.ui_application_focus_identities(r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS)}
        for focus in (r.IOS_PICKER_BOUNDARY_FOCUS, r.IOS_PICKER_RECOVERY_FOCUS, r.IOS_PICKER_ADMISSION_FOCUS):
            old = {(case["classname"], case["name"]) for case in r.ui_application_focus_identities(focus)}
            self.assertFalse(selected & old)

    def test_wrong_suite_module_omission_and_tampered_plan_refuse(self):
        for suite, modules in (("desktop", ("calf-file-picker",)), ("ios", ("calf-ui",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS)
        original = self.plan()
        for key, value in (("native_test_host", "command-line"), ("test_filter", r.IOS_PICKER_PROVIDER_CANCELLATION_CLASS),
                           ("required_testcases", []), ("task", ":calf-file-picker:iosSimulatorArm64Test")):
            changed = copy.deepcopy(original)
            changed["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_test_focus(changed)

    def test_absent_ignored_duplicate_or_extra_method_declarations_refuse(self):
        helper = batch.IosPickerBatchTests("test_one_slot_exact_26_methods_no_replay_or_publishing_tasks")
        self.addCleanup(helper.doCleanups)
        fixture, _, _, _ = helper.fixture()
        source = (r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text()
        target = fixture.write(r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE, source)
        self.assertTrue(r.validate_test_focus(self.plan(fixture.root)))
        for changed in (source.replace("@Test", "@IgnoredTest", 1), source + "\n@Test fun foreign() {}\n",
                        source + "\n@Test fun " + r.IOS_PICKER_PROVIDER_CANCELLATION_METHODS[0] + "() {}\n"):
            target.write_text(changed)
            with self.assertRaises(ValueError): self.plan(fixture.root)
        target.unlink()
        with self.assertRaises((ValueError, FileNotFoundError)): self.plan(fixture.root)

    def test_original_single_xml_identity_is_required_not_old_cases_or_silence(self):
        plan = self.plan()
        item, = plan["expected"]
        identities = item["required_testcases"]
        def collect(cases, outcome="", markers=1, duplicate=False):
            xml = '<testsuite>' + ''.join(
                f'<testcase classname="{c["classname"]}" name="{c["name"]}">{outcome}</testcase>' for c in cases) + '</testsuite>'
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                reports = root / item["report_directory"]
                reports.mkdir(parents=True)
                (reports / "TEST-explicitly-synthetic.xml").write_text(xml)
                if duplicate: (reports / "TEST-duplicate.xml").write_text(xml)
                now = time.time_ns()
                return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                         Counter({item["task"]: markers}), host_system="Darwin")
        self.assertEqual([], collect(identities)["errors"])
        for cases in ([], identities * 2, r.ui_application_focus_identities(r.IOS_PICKER_RECOVERY_FOCUS)):
            with self.subTest(cases=len(cases)): self.assertTrue(collect(cases)["errors"])
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            with self.subTest(outcome=outcome): self.assertTrue(collect(identities, outcome)["errors"])
        self.assertTrue(collect(identities, markers=0)["errors"])
        self.assertTrue(collect(identities, duplicate=True)["errors"])

    def test_source_retains_genuine_native_public_and_causal_acknowledgement_boundaries(self):
        require_provider_witnesses((r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text())

    def test_native_client_and_registered_producer_acknowledgements_cannot_replace_each_other(self):
        source = (r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text()
        require_provider_witnesses(source)  # One corrected-source positive; never native acceptance.
        mutations = (("heldCompletionIssued.compareAndSet(0, 1)", "true"),
                     ("heldCompletionReturned.compareAndSet(0, 1)", "provider.clientReturned.value == 1"),
                     ("handler.invoke(null, false, cancellationError())", "Unit"),
                     ("pending.heldCompletionReturned.value == 1", "pending.provider.clientReturned.value == 1"),
                     ("val heldCompletionReturned = AtomicInt(0)", "val heldCompletionReturned = AtomicInt(1)"),
                     ("assertEquals(1, pending.heldCompletionIssued.value)", "assertEquals(1, pending.provider.clientEntered.value)"))
        for before, after in mutations:
            self.assertEqual(1, source.count(before))
            with self.subTest(removed=before), self.assertRaises(ValueError):
                require_provider_witnesses(source.replace(before, after, 1))

    def test_progress_forwarding_public_disposal_and_resource_cleanup_cannot_be_substituted(self):
        source = (r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text()
        for before, after in (("return progress", "return NSProgress(parent = null, userInfo = null)"),
                              ("completionHandler(url, error)", "completionHandler(null, cancellationError())"),
                              ("runOnIdle { included.value = false }", "pending.close()"),
                              ("closeHandlesLocked(); removePartialLocked()", "removePartialLocked()"),
                              ("if (callbackAcknowledged) clean {", "if (true) clean {")):
            with self.subTest(removed=before), self.assertRaises(ValueError):
                require_provider_witnesses(source.replace(before, after, 1))

    def test_native_and_controlled_entries_share_controller_before_claim_and_one_lazy_gate(self):
        source, delegate, launcher = self.arrival_sources()
        require_provider_arrival_boundary(source, delegate, launcher)
        gate = "if (picker != session.controller || !session.claimResult()) return"
        mutations = ((gate, "if (!session.claimResult() || picker != session.controller) return"),
                     (gate, "if (picker != session.controller && !session.claimResult()) return"),
                     (gate, "if (picker == session.controller || !session.claimResult()) return"),
                     (gate, "if (picker != session.controller) return"),
                     ("onPicked(sources())", "onPicked(emptyList())"),
                     ("private fun finishProviderSources(", "internal fun finishProviderSources("),
                     ("private val onPicked: (List<() -> NSItemProvider>) -> Unit",
                      "private val onPicked: (List<NSItemProvider>) -> Unit"))
        for before, after in mutations:
            self.assertEqual(1, delegate.count(before))
            with self.subTest(shared_gate=before, replacement=after), self.assertRaises(ValueError):
                require_provider_arrival_boundary(source, delegate.replace(before, after, 1), launcher)

    def test_no_native_or_controlled_traversal_or_eager_provider_getter_precedes_the_claim(self):
        source, delegate, launcher = self.arrival_sources()
        native = """        finishProviderSources(picker) {
            didFinishPicking.filterIsInstance<PHPickerResult>().map { result ->
                { result.itemProvider }
            }
        }"""
        controlled = """        finishProviderSources(picker) {
            providers.map { provider -> { provider } }
        }"""
        mutations = ((native, """        val extracted = didFinishPicking.filterIsInstance<PHPickerResult>().map { result ->
            { result.itemProvider }
        }
        finishProviderSources(picker) { extracted }"""),
                     (controlled, """        val extracted = providers.map { provider -> { provider } }
        finishProviderSources(picker) { extracted }"""),
                     ("if (picker != session.controller || !session.claimResult()) return\n        onPicked(sources())",
                      "val arrived = sources()\n        if (picker != session.controller || !session.claimResult()) return\n        onPicked(arrived)"),
                     ("{ result.itemProvider }", "result.itemProvider.let { provider -> { provider } }"),
                     (native, """        if (!session.claimResult()) return
        onPicked(didFinishPicking.filterIsInstance<PHPickerResult>().map { result -> { result.itemProvider } })"""),
                     (controlled, """        if (picker != session.controller) return
        onPicked(providers.map { provider -> { provider } })"""),
                     ("filterIsInstance<PHPickerResult>()", "filterIsInstance<NSItemProvider>()"))
        for before, after in mutations:
            self.assertEqual(1, delegate.count(before))
            with self.subTest(lazy_arrival=before), self.assertRaises(ValueError):
                require_provider_arrival_boundary(source, delegate.replace(before, after, 1), launcher)

    def test_limit_existing_io_staging_and_ensure_active_precede_each_supplier_invocation(self):
        source, delegate, launcher = self.arrival_sources()
        before_load = """currentCoroutineContext().ensureActive()
                                    val file = result().loadFileRepresentationForTypeIdentifierSuspend(launchType)"""
        mutations = (("val picked = results.limitedTo(launchMode)", "val picked = results"),
                     ("val picked = results.limitedTo(launchMode)",
                      "val picked = results.map { source -> source() }.limitedTo(launchMode).map { provider -> { provider } }"),
                     ("withContext(Dispatchers.IO) { stage(owned) }", "withContext(Dispatchers.Main) { stage(owned) }"),
                     ("withContext(Dispatchers.IO) { stage(owned) }", "stage(owned)"),
                     (before_load, """val provider = result()
                                    currentCoroutineContext().ensureActive()
                                    val file = provider.loadFileRepresentationForTypeIdentifierSuspend(launchType)"""),
                     ("val file = result().loadFileRepresentationForTypeIdentifierSuspend(launchType)",
                      "val file = result.itemProvider.loadFileRepresentationForTypeIdentifierSuspend(launchType)"),
                     ("for (result in picked)", "for (result in results)"))
        for before, after in mutations:
            self.assertEqual(1, launcher.count(before))
            with self.subTest(staging_order=before), self.assertRaises(ValueError):
                require_provider_arrival_boundary(source, delegate, launcher.replace(before, after, 1))

    def test_missing_wrong_or_replaced_installed_delegate_and_native_provider_arguments_refuse(self):
        source, delegate, launcher = self.arrival_sources()
        installed = "val delegate = runOnIdle { assertIs<PhotoPickerDelegate>(picker.delegate) }"
        mutations = ((installed, ""),
                     (installed, "val delegate = runOnIdle { assertNotNull(picker.delegate) as PhotoPickerDelegate }"),
                     (installed, "val delegate = runOnIdle { assertIs<PhotoPickerDelegate>(null) }"),
                     ("assertIs<PhotoPickerDelegate>(picker.delegate)", "assertIs<NSObject>(picker.delegate)"),
                     ("assertIs<PHPickerViewController>(parent.presentedViewController)",
                      "assertIs<UIViewController>(parent.presentedViewController)"),
                     ("val providers = listOf(first.provider, pending.provider)", "val providers = listOf(first.provider, first.provider)"),
                     ("val providers = listOf(first.provider, pending.provider)", "val providers = listOf(pending.provider, first.provider)"),
                     ("sameNativeObject(providers[0], first.provider)", "providers[0] == first.provider"))
        for before, after in mutations:
            self.assertEqual(1, source.count(before))
            with self.subTest(installed_argument=before), self.assertRaises(ValueError):
                require_provider_arrival_boundary(source.replace(before, after, 1), delegate, launcher)

    def test_fake_result_construction_private_loader_or_bypassed_arrivals_refuse(self):
        source, delegate, launcher = self.arrival_sources()
        insertion = "            val partialIdentity = pending.partialIdentity()"
        self.assertEqual(1, source.count(insertion))
        bypasses = ("val forged = PHPickerResult()",
                    "val forged = OwnedProviderResult(first.provider)",
                    "val newDelegate = PhotoPickerDelegate(IosDialogSession(), {}, {})",
                    "delegate.finishProviderSources(picker) { providers.map { provider -> { provider } } }",
                    "delegate.onPicked(providers.map { provider -> { provider } })",
                    'pending.provider.loadFileRepresentationForTypeIdentifier("public.image") { _, _ -> }',
                    'picker.setValue(first.provider, forKey = "itemProvider")',
                    "method_exchangeImplementations(null, null)",
                    "delegate.pickerProviders(picker, providers)",
                    'val covert = "${delegate.pickerProviders(picker, providers)}"')
        for bypass in bypasses:
            changed = source.replace(insertion, "            " + bypass + "\n" + insertion, 1)
            with self.subTest(bypassed_arrival=bypass), self.assertRaises(ValueError):
                require_provider_arrival_boundary(changed, delegate, launcher)
        arrival = "delegate.pickerProviders(picker, providers)"
        self.assertEqual(3, source.count(arrival))
        for replacement in ("delegate.picker(picker, emptyList<Any>())",
                            "delegate.pickerProviders(picker, emptyList())"):
            with self.subTest(replaced_arrival=replacement), self.assertRaises(ValueError):
                require_provider_arrival_boundary(source.replace(arrival, replacement, 1), delegate, launcher)
        with self.assertRaises(ValueError):
            require_provider_arrival_boundary(source + "\nprivate class OwnedProviderResult : PHPickerResult()\n", delegate, launcher)

    def test_comments_literals_and_duplicate_source_blocks_cannot_spoof_the_owning_witness(self):
        source, delegate, launcher = self.arrival_sources()
        gate = "if (picker != session.controller || !session.claimResult()) return"
        self.assertEqual(1, delegate.count(gate))
        harmless = delegate.replace(gate, "if (picker /* nested /* } onPicked(fake) */ harmless */ != session.controller || !session.claimResult()) return", 1)
        require_provider_arrival_boundary(source, harmless, launcher)
        for replacement in ("/* " + gate + " */",
                            'val ignored = "' + gate + '"',
                            'val ignored = """' + gate + '"""'):
            with self.subTest(noncode_gate=replacement), self.assertRaises(ValueError):
                require_provider_arrival_boundary(source, delegate.replace(gate, replacement, 1), launcher)
        with self.assertRaises(ValueError):
            require_provider_arrival_boundary(source, delegate + "\n" + delegate, launcher)
        installed = "val delegate = runOnIdle { assertIs<PhotoPickerDelegate>(picker.delegate) }"
        self.assertEqual(1, source.count(installed))
        with self.assertRaises(ValueError):
            require_provider_arrival_boundary(source.replace(installed, "// " + installed, 1), delegate, launcher)


    def test_installed_native_delegate_property_and_three_arrivals_require_exact_five_tokens(self):
        source, delegate, launcher = self.arrival_sources()
        tokens = _kotlin_block(_kotlin_tokens(source), "@Test fun " + r.IOS_PICKER_PROVIDER_CANCELLATION_METHODS[0] +
                               "() = runApplicationUiTest")
        # One local declaration + the actual picker.delegate property + three arrivals.
        self.assertEqual(5, tokens.count("delegate"))
        require_provider_arrival_boundary(source, delegate, launcher)
        insertion = "            val partialIdentity = pending.partialIdentity()"
        self.assertEqual(1, source.count(insertion))
        extra = source.replace(insertion, "            val capturedDelegate = delegate\n" + insertion, 1)
        with self.assertRaises(ValueError):
            require_provider_arrival_boundary(extra, delegate, launcher)
        self.assertEqual(1, source.count("assertIs<PhotoPickerDelegate>(picker.delegate)"))
        missing = source.replace("assertIs<PhotoPickerDelegate>(picker.delegate)",
                                 "assertIs<PhotoPickerDelegate>(null)", 1)
        with self.assertRaises(ValueError):
            require_provider_arrival_boundary(missing, delegate, launcher)


    def test_owned_registered_handler_remains_one_shot_and_is_invoked_outside_its_lock(self):
        source = (r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text()
        mutations = (
            ("check(holdAfterFirstChunk && !cleanupStarted)", "check(holdAfterFirstChunk)"),
            ("val pending = assertNotNull(completion)", "val pending: (NSURL?, Boolean, NSError?) -> Unit = { _, _, _ -> }"),
            ("completion = null\n            pending", "pending"),
            ("handler.invoke(null, false, cancellationError())", "protect { handler.invoke(null, false, cancellationError()) }"),
            ("check(closedHandles.value == 2)", "check(true)"),
        )
        for before, after in mutations:
            self.assertEqual(1, source.count(before))
            with self.subTest(ownership_boundary=before), self.assertRaises(ValueError):
                require_provider_witnesses(source.replace(before, after, 1))

    def test_native_client_snapshot_is_locked_descriptive_and_not_a_zero_callback_arm(self):
        source = (r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text()
        mutations = (
            ("fun clientCounts(): List<Int> = protect {", "fun clientCounts(): List<Int> = run {"),
            ("listOf(clientEntered.value, clientReturned.value)", "listOf(0, 0)"),
            ("listOf(clientEntered.value, clientReturned.value)",
             "check(clientEntered.value == 0 && clientReturned.value == 0); listOf(clientEntered.value, clientReturned.value)"),
            ("private var actualProgress: NSProgress? = null", "private var actualProgress: NSProgress? = null; private var deliberateCancellationError: NSError? = null"),
        )
        for before, after in mutations:
            self.assertEqual(1, source.count(before))
            with self.subTest(descriptive_not_gate=before), self.assertRaises(ValueError):
                require_provider_witnesses(source.replace(before, after, 1))

    def test_both_distinct_acknowledgements_gate_captured_delegate_and_disposed_launcher_checks(self):
        source = (r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text()
        wait = "waitForNative { pending.provider.clientReturned.value == 1 &&\n                pending.heldCompletionReturned.value == 1 }"
        mutations = (
            (wait, "waitForNative { pending.heldCompletionReturned.value == 1 }"),
            (wait, "waitForNative { pending.provider.clientReturned.value == 1 }"),
            ("assertEquals(1, pending.provider.clientReturned.value)", "assertEquals(1, pending.heldCompletionReturned.value)"),
            ("pending.completeCancelledTransport()\n            " + wait,
             wait + "\n            pending.completeCancelledTransport()"),
        )
        for before, after in mutations:
            self.assertEqual(1, source.count(before))
            with self.subTest(distinct_acknowledgement=before), self.assertRaises(ValueError):
                require_provider_witnesses(source.replace(before, after, 1))

    def test_cleanup_or_manual_client_counts_cannot_supply_public_native_cancellation_evidence(self):
        source = (r.ROOT / r.IOS_PICKER_PROVIDER_CANCELLATION_SOURCE).read_text()
        insertion = "            runOnIdle { included.value = false }"
        self.assertEqual(1, source.count(insertion))
        for forged in ("pending.close()", "pending.provider.cancelForCleanup()",
                       "pending.provider.clientEntered.value = 1", "pending.provider.clientReturned.value = 1"):
            with self.subTest(forged_native=forged), self.assertRaises(ValueError):
                require_provider_witnesses(source.replace(insertion, "            " + forged + "\n" + insertion, 1))


if __name__ == "__main__":
    unittest.main()
