"""New source-linked synthetic iOS request controls, not Kotlin/Apple/native execution.

The model uses opaque synthetic retained objects, never real native pointers, callbacks,
NSError values, TLS, DNS or a WebKit process. Native acceptance is a separate gate.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
IOS = "calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt"
IDENTITY = "calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/NativeWebViewIdentity.ios.kt"
PINS = {
    "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt": "36891159184df5bcd03b724b81070698c878022796a5b563994c58591c763791",
    "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebViewContracts.kt": "4a87aa4a7a17252f817f8bdc9b8de8fcda62fb6093bfed624db0bc5c6875647f",
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewRequestAcceptanceTest.kt": "594eb2139ad98961b06edcf0d6d9dc36efaa3dcad394e3b3ea458db75476aacf",
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewProvisionalDnsAcceptanceTest.kt": "25efe05ca6ce4cc2f027dc74eaf22a3a74cd4213d315940be9b64bdf7f0fe594",
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/IosWebViewLifecycleAcceptanceTest.kt": "49c98aa532e14a75e1b3c09b5404727b426e3c4b859ab16f4af5a4fe9979a381",
    "calf-webview/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/web/internal/NativeObjectIdentity.kt": "f8a5b13a21a0b3adcea5e5c27def54a03ad486574a552e6439a71852f0ba4b42",
}


def block(source, marker):
    start = source.index("{", source.index(marker))
    depth = 0
    for index in range(start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1:index]
    raise AssertionError("Unbalanced selected source block")


@dataclass(eq=False)
class SyntheticRetainedObject:
    allocation: object


def same_retained(first, second):
    return first is not None and second is not None and first.allocation is second.allocation


@dataclass(eq=False)
class SyntheticView(SyntheticRetainedObject):
    url: str | None = "synthetic:old"
    title: str | None = "synthetic old title"
    native_loading: bool = False


@dataclass(eq=False)
class SyntheticRequest:
    navigation: SyntheticRetainedObject | None = None
    superseded: SyntheticRetainedObject | None = None
    phase: str = "AwaitingStart"
    stopped: bool = False


class SourceLinkedModel:
    """Deliberately only an abstract model of the selected production transitions."""
    def __init__(self, view):
        self.owner = view
        self.request = None
        self.requested = None
        self.final = None
        self.title = None
        self.errors = []
        self.loading = "Initializing"

    def owns(self, view):
        return same_retained(self.owner, view)

    def prepare(self):
        previous = self.request
        self.request = SyntheticRequest(superseded=(previous.navigation or previous.superseded) if previous else None)
        return self.request

    def reset(self, url):
        self.requested, self.final, self.title, self.errors, self.loading = url, None, None, [], "Loading"

    def load(self, view, url, navigation, error=None, navigator_only=False):
        if not self.owns(view) or navigator_only:
            return None
        ticket = self.prepare()
        self.reset(url)
        if error is not None:
            self.errors, self.loading = [error], "Finished"
            ticket.phase = "FinishedUncommitted"
        else:
            self.bind(view, ticket, navigation)
        return ticket

    def bind(self, view, ticket, navigation):
        if not self.owns(view) or self.request is not ticket or navigation is None:
            return
        if ticket.navigation is None:
            ticket.navigation = navigation

    def start(self, view, navigation):
        if not self.owns(view) or navigation is None:
            return
        previous = self.request
        if same_retained(previous.superseded if previous else None, navigation):
            return
        if previous is not None and same_retained(previous.navigation, navigation):
            if previous.phase != "AwaitingStart" or previous.stopped:
                return
            ticket = previous
        elif previous is not None and previous.navigation is None and previous.phase == "AwaitingStart":
            if previous.stopped:
                return
            previous.navigation = navigation
            ticket = previous
        else:
            ticket = SyntheticRequest(navigation=navigation, superseded=(previous.navigation or previous.superseded) if previous else None)
            self.request = ticket
        ticket.phase = "Provisional"
        self.reset(view.url if view.url is not None else self.requested)

    def current(self, navigation):
        return self.request if self.request is not None and same_retained(self.request.navigation, navigation) else None

    def commit(self, view, navigation):
        if not self.owns(view):
            return
        ticket = self.current(navigation)
        if ticket is None or ticket.phase != "Provisional" or ticket.stopped:
            return
        ticket.phase = "Committed"
        self.loading, self.final, self.title = "Loading", view.url, view.title

    def finish(self, view, navigation):
        if not self.owns(view):
            return
        if navigation is None:
            if self.request is None:
                self.loading = "Finished"
            return
        ticket = self.current(navigation)
        if ticket is None:
            return
        if ticket.phase == "Committed":
            ticket.phase = "FinishedCommitted"
            self.final, self.title = view.url, view.title
        elif ticket.phase in ("AwaitingStart", "Provisional"):
            ticket.phase = "FinishedUncommitted"
        else:
            return
        self.loading = "Finished"

    def fail(self, view, navigation, error):
        if not self.owns(view):
            return
        ticket = self.current(navigation)
        if ticket is None:
            return
        if ticket.phase == "Committed":
            ticket.phase = "FinishedCommitted"
        elif ticket.phase in ("AwaitingStart", "Provisional"):
            ticket.phase = "FinishedUncommitted"
        else:
            return
        self.loading, self.errors = "Finished", self.errors + [error]

    def stop(self, view):
        if not self.owns(view):
            return
        if self.request is not None and self.request.phase in ("AwaitingStart", "Provisional"):
            self.request.stopped = True

    def kvo(self, view, key):
        if not self.owns(view):
            return
        if key == "loading":
            if view.native_loading:
                if self.request is not None and self.request.phase == "FinishedCommitted":
                    self.request.phase = "SuspendedCommitted"
                self.loading = "Loading"
            else:
                self.loading = "Finished"
        elif key in ("URL", "title"):
            if self.request is not None and self.request.phase in ("Committed", "FinishedCommitted") and not view.native_loading:
                if key == "URL":
                    self.final = view.url
                else:
                    self.title = view.title

    def reload(self, view, navigation):
        if not self.owns(view):
            return
        ticket = self.prepare()
        self.reset(view.url if view.url is not None else self.requested)
        self.bind(view, ticket, navigation)

    def release(self, view):
        if self.owns(view):
            self.request, self.owner, self.loading = None, None, "Finished"

    def snapshot(self):
        return self.requested, self.final, self.title, tuple(self.errors), self.loading


class IosCurrentRequestMetadataSourceTests(unittest.TestCase):
    def source(self):
        return (ROOT / IOS).read_text()

    def test_new_source_regression_requires_url_and_title_kvo_commit_gate(self):
        source = self.source()
        for key, assignment in (("title", "state.pageTitle = webView.title"), ("URL", "state.lastLoadedUrl = webView.URL?.absoluteString")):
            selected = block(source, f'"{key}" ->')
            self.assertIn(f"if (state.canPublishIosPageMetadata(webView)) {assignment}", selected,
                          "Old/provisional native metadata cannot be published as a current committed document")

    def test_source_live_identity_transition_and_noncommit_paths_are_bound(self):
        source = self.source()
        identity = (ROOT / IDENTITY).read_text()
        self.assertIn("internal fun hasSameNativeNavigation(first: WKNavigation?, second: WKNavigation?)", identity)
        self.assertEqual(2, identity.count("first != null && second != null && first.objcPtr() == second.objcPtr()"))
        for forbidden in ("first === second", "first == second", ".rawValue", "toLong()"):
            self.assertNotIn(forbidden, identity)
        phases = block(source, "internal enum class IosWebViewRequestPhase")
        self.assertEqual({"AwaitingStart", "Provisional", "Committed", "FinishedCommitted", "FinishedUncommitted", "SuspendedCommitted"},
                         {p.strip() for p in phases.split(",") if p.strip()})
        gate = block(source, "internal fun canPublishIosPageMetadata")
        for required in ("hasSameNativeWebView(webView, view)", "!view.loading", "IosWebViewRequestPhase.Committed", "IosWebViewRequestPhase.FinishedCommitted"):
            self.assertIn(required, gate)
        binding = block(source, "internal fun bindIosNavigation")
        self.assertIn("if (!hasSameNativeWebView(webView, view) || navigation == null) return", binding)
        self.assertIn("if (iosRequest !== request) return", binding)
        self.assertLess(binding.index("navigation == null"), binding.index("knownIosNavigations.addObject(navigation)"))
        self.assertLess(binding.index("knownIosNavigations.addObject(navigation)"), binding.index("if (iosRequest !== request) return"))
        self.assertLess(binding.index("if (iosRequest !== request) return"), binding.index("if (request.navigation == null) request.navigation = navigation"))
        self.assertIn("if (request.navigation == null) request.navigation = navigation", binding)
        self.assertNotIn("request.phase =", binding)
        start = block(source, "private fun beginIosNavigation")
        for required in ("if (navigation == null) return", "hasSameNativeNavigation(previous?.supersededNavigation, navigation)",
                         "hasSameNativeNavigation(previous.navigation, navigation)", "previous.stoppedBeforeCommit", "beginRequest(view.URL?.absoluteString ?: requestedUrl)"):
            self.assertIn(required, start)
        commit = block(source, "override fun webView(webView: WKWebView, didCommitNavigation:")
        self.assertLess(commit.index("requestFor(didCommitNavigation)"), commit.index("lastLoadedUrl ="))
        self.assertIn("request.phase != IosWebViewRequestPhase.Provisional || request.stoppedBeforeCommit", commit)
        failure = block(source, "private fun failIosNavigation")
        self.assertIn("requestFor(navigation) ?: return", failure)
        self.assertIn("code = withError.code.toInt()", failure)
        self.assertIn("description = withError.localizedDescription", failure)
        self.assertNotIn("lastLoadedUrl =", failure)
        self.assertNotIn("pageTitle =", failure)
        finish = block(source, "override fun webView(webView: WKWebView, didFinishNavigation:")
        self.assertIn("if (iosRequest == null) loadingState = LoadingState.Finished", finish)
        self.assertIn("requestFor(didFinishNavigation) ?: return", finish)
        self.assertIn("IosWebViewRequestPhase.Committed ->", finish)
        self.assertIn("IosWebViewRequestPhase.FinishedUncommitted", finish)

    def test_source_content_reload_stop_history_and_cleanup_preserve_boundaries(self):
        source = self.source()
        content = block(source, "private fun loadIosContent")
        self.assertLess(content.index("if (content == WebContent.NavigatorOnly) return"), content.index("prepareIosRequest()"))
        self.assertLess(content.index("prepareIosRequest()"), content.index("acceptContent(content, WebContentPlatform.Ios)"))
        self.assertEqual(3, content.count("state.rejectIosRequest(iosRequest)"))
        self.assertIn("state.bindIosNavigation(view, iosRequest, view.loadRequest(request))", content)
        self.assertIn("state.bindIosNavigation(view, iosRequest, view.loadHTMLString(content.data, baseUrl))", content)
        self.assertIn("WebViewNavigator.NavigationEvent.Back -> if (webView.canGoBack) webView.goBack()", source)
        self.assertIn("WebViewNavigator.NavigationEvent.Forward -> if (webView.canGoForward) webView.goForward()", source)
        reload = block(source, "WebViewNavigator.NavigationEvent.Reload ->")
        self.assertIn("state.beginRequest(webView.URL?.absoluteString ?: state.requestedUrl)", reload)
        self.assertIn("state.bindIosNavigation(webView, request, webView.reload())", reload)
        self.assertNotIn("state.content", reload)
        stop = block(source, "WebViewNavigator.NavigationEvent.StopLoading ->")
        self.assertLess(stop.index("state.stopIosRequestBeforeCommit()"), stop.index("webView.stopLoading()"))
        self.assertNotIn("WebViewError", stop)
        release = block(source, "private fun releaseIosWebView")
        for original in ("onDispose,", "observer?.stopObserving(view)", "view.navigationDelegate = null", "view.stopLoading()", "view.removeFromSuperview()"):
            self.assertIn(original, release)
        self.assertIn("if (hasSameNativeWebView(state.webView, view)) {\n                state.clearIosRequestMetadata()", release)
        for callback in ("didFinishNavigation", "didStartProvisionalNavigation", "didCommitNavigation", "didFailNavigation", "didFailProvisionalNavigation"):
            selected = block(source, "override fun webView(webView: WKWebView, " + callback + ":") if callback != "didFailProvisionalNavigation" else block(source, "didFailProvisionalNavigation: WKNavigation?,")
            self.assertIn("if (!hasSameNativeWebView(this.webView, webView)) return", selected)
        observer = block(source, "override fun observeValueForKeyPath")
        self.assertIn("if (!hasSameNativeWebView(state.webView, webView)) return", observer)
        self.assertIn("state.noteIosNativeLoading()", observer)

    def test_original_common_api_and_all_native_method_bodies_remain_byte_identical(self):
        for relative, expected in PINS.items():
            with self.subTest(path=relative):
                self.assertEqual(expected, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())


class IosCurrentRequestMetadataSyntheticTests(unittest.TestCase):
    def fixture(self):
        view = SyntheticView(object())
        state = SourceLinkedModel(view)
        return view, state

    def navigation(self):
        return SyntheticRetainedObject(object())

    def committed(self):
        view, state = self.fixture()
        navigation = self.navigation()
        state.load(view, "synthetic:old", navigation)
        state.start(view, navigation)
        state.commit(view, navigation)
        state.finish(view, navigation)
        return view, state, navigation

    def kvo_metadata(self, state, view):
        state.kvo(view, "URL")
        state.kvo(view, "title")

    def test_live_wrappers_foreign_and_null_never_create_an_owner_or_commit(self):
        view, state = self.fixture()
        bridged = SyntheticView(view.allocation)
        foreign = SyntheticView(object())
        self.assertTrue(same_retained(view, bridged)); self.assertFalse(same_retained(None, None))
        state.loading = "Loading"
        state.finish(foreign, None); self.assertEqual("Loading", state.loading)
        state.finish(bridged, None); self.assertEqual("Finished", state.loading)
        self.kvo_metadata(state, bridged)
        self.assertEqual((None, None), (state.final, state.title))
        state.load(view, "synthetic:request", self.navigation())
        snapshot = state.snapshot()
        state.start(foreign, self.navigation()); state.commit(foreign, self.navigation())
        state.finish(foreign, None); state.fail(foreign, self.navigation(), (-91, "synthetic"))
        self.kvo_metadata(state, foreign)
        self.assertEqual(snapshot, state.snapshot())

    def test_owned_dispatch_blocks_retained_metadata_even_before_native_start(self):
        view, state, old = self.committed()
        ticket = state.load(view, "synthetic:pending", self.navigation())
        for loading in (False, True, False):
            view.native_loading = loading
            self.kvo_metadata(state, view)
            self.assertEqual((None, None), (state.final, state.title))
        state.commit(view, old); state.finish(view, old); state.fail(view, old, (-81, "old"))
        self.assertEqual([], state.errors); self.assertIs(ticket, state.request)

    def test_current_commit_finish_and_idle_same_document_metadata_are_not_disabled(self):
        view, state = self.fixture(); navigation = self.navigation()
        state.load(view, "synthetic:entry", navigation)
        view.url, view.title, view.native_loading = "synthetic:redirect-final", "synthetic final", True
        state.start(view, navigation); self.kvo_metadata(state, view)
        self.assertEqual((None, None), (state.final, state.title))
        state.commit(view, SyntheticRetainedObject(navigation.allocation))
        self.assertEqual((view.url, view.title), (state.final, state.title))
        view.native_loading = False; state.finish(view, navigation)
        requested = state.requested
        view.url, view.title = "synthetic:arbitrary-history-path#fragment", "synthetic JS title"
        self.kvo_metadata(state, view)
        self.assertEqual((view.url, view.title), (state.final, state.title))
        self.assertEqual(requested, state.requested)

    def test_provisional_and_failed_intervals_never_publish_retained_url_or_title(self):
        view, state, _ = self.committed(); navigation = self.navigation()
        state.load(view, "synthetic:tls", navigation)
        view.url = "synthetic:tls"; state.start(view, navigation)
        for loading in (True, False):
            view.native_loading = loading; self.kvo_metadata(state, view)
            self.assertEqual((None, None), (state.final, state.title))
        state.fail(view, navigation, (-1200, "synthetic injected error; not TLS evidence"))
        view.url, view.title = "synthetic:old", "synthetic retained title"
        state.kvo(view, "loading"); self.kvo_metadata(state, view)
        self.assertEqual((None, None), (state.final, state.title))
        self.assertEqual([-1200], [code for code, _ in state.errors])
        self.assertEqual("Finished", state.loading)

    def test_real_start_authority_retains_prior_error_until_start_then_resets_once(self):
        view, state, _ = self.committed()
        first, second = self.navigation(), self.navigation()
        view.url, view.native_loading = "synthetic:first-link", True
        state.kvo(view, "loading"); state.start(view, first)
        state.fail(view, first, (-17, "synthetic prior")); prior = list(state.errors)
        view.url = "synthetic:second-link"; state.kvo(view, "loading")
        self.assertEqual(prior, state.errors)
        self.kvo_metadata(state, view); self.assertEqual(prior, state.errors)
        state.start(view, second)
        self.assertEqual(("synthetic:second-link", None, None, ()), state.snapshot()[:4])
        state.errors.append((-18, "synthetic current")); state.start(view, second)
        self.assertEqual([(-18, "synthetic current")], state.errors)

    def test_superseded_terminal_callbacks_and_retained_predecessor_start_are_ignored(self):
        view, state, old = self.committed(); newer = self.navigation()
        state.load(view, "synthetic:newer", newer)
        view.url = "synthetic:newer"; state.start(view, newer)
        snapshot = state.snapshot(); ticket = state.request
        for callback in (lambda: state.start(view, old), lambda: state.commit(view, old),
                         lambda: state.finish(view, old), lambda: state.fail(view, old, (-44, "synthetic stale"))):
            callback(); self.assertEqual(snapshot, state.snapshot()); self.assertIs(ticket, state.request)
        state.commit(view, newer); self.assertEqual("synthetic:newer", state.final)

    def test_returned_binding_cannot_reopen_an_advanced_or_replaced_request(self):
        view, state = self.fixture(); navigation = self.navigation()
        ticket = state.prepare(); state.reset("synthetic:issued")
        state.start(view, navigation); state.commit(view, navigation); state.finish(view, navigation)
        state.bind(view, ticket, navigation)
        self.assertEqual("FinishedCommitted", state.request.phase)
        newer = self.navigation(); view.url = "synthetic:new-native-link"; state.start(view, newer)
        current = state.request
        state.bind(view, ticket, navigation); self.assertIs(current, state.request)
        self.assertTrue(same_retained(newer, state.request.navigation))
        state.bind(view, current, None); self.assertTrue(same_retained(newer, state.request.navigation))

    def test_unsupported_and_invalid_inputs_keep_old_dom_metadata_blocked_without_native_replacement(self):
        for error in ((-2, "synthetic unsupported encoding"), (-1, "Invalid URL"), (-1, "Invalid base URL")):
            with self.subTest(error=error):
                view, state, old = self.committed()
                state.load(view, None, None, error=error)
                self.kvo_metadata(state, view); state.start(view, old); state.finish(view, old)
                state.fail(view, old, (-77, "synthetic old"))
                self.assertEqual([error], state.errors)
                self.assertEqual((None, None), (state.final, state.title))
                self.assertEqual("synthetic:old", view.url)
                self.assertEqual("FinishedUncommitted", state.request.phase)

    def test_navigator_only_and_idle_history_noops_preserve_committed_same_document_witness(self):
        view, state, _ = self.committed(); ticket = state.request; snapshot = state.snapshot()
        state.load(view, None, None, navigator_only=True)
        self.assertIs(ticket, state.request); self.assertEqual(snapshot, state.snapshot())
        # Same-document Back/Forward has no invented provisional start or common reset.
        view.url, view.title = "synthetic:history-entry#hash", "synthetic history title"
        self.kvo_metadata(state, view)
        self.assertIs(ticket, state.request); self.assertEqual((view.url, view.title), (state.final, state.title))

    def test_reload_uses_native_current_url_not_stale_declarative_content_and_resets_refusal(self):
        view, state, _ = self.committed(); navigation = self.navigation()
        state.load(view, None, None, error=(-2, "synthetic unsupported"))
        self.assertEqual([(-2, "synthetic unsupported")], state.errors)
        state.reload(view, navigation)
        self.assertEqual("synthetic:old", state.requested)
        self.assertEqual((None, None, ()), (state.final, state.title, tuple(state.errors)))
        state.start(view, navigation); state.commit(view, navigation); state.finish(view, navigation)
        self.assertEqual("synthetic:old", state.final)

    def test_stop_precommit_keeps_real_identity_for_one_actual_error_but_cannot_commit(self):
        view, state, _ = self.committed(); navigation = self.navigation()
        state.load(view, "synthetic:held", navigation); view.url = "synthetic:held"
        state.start(view, navigation); state.stop(view)
        self.assertEqual([], state.errors)
        state.commit(view, navigation); self.kvo_metadata(state, view)
        self.assertEqual((None, None), (state.final, state.title))
        error = (-999, "synthetic injected cancellation; not native EOF evidence")
        state.fail(view, navigation, error); state.fail(view, navigation, error)
        self.assertEqual([error], state.errors)
        state.finish(view, navigation); self.assertEqual((None, None), (state.final, state.title))

    def test_stop_before_start_and_postcommit_do_not_manufacture_a_new_request_or_error(self):
        view, state = self.fixture(); navigation = self.navigation()
        ticket = state.load(view, "synthetic:pending", navigation); state.stop(view)
        state.start(view, navigation); state.commit(view, navigation)
        self.assertEqual("AwaitingStart", ticket.phase); self.assertEqual([], state.errors)
        state.fail(view, navigation, (-999, "synthetic cancellation"))
        newer = self.navigation(); state.load(view, "synthetic:recovery", newer)
        view.url = "synthetic:recovery"; state.start(view, newer); state.commit(view, newer)
        state.stop(view); self.assertEqual("synthetic:recovery", state.final)
        state.fail(view, newer, (-999, "synthetic postcommit cancellation"))
        self.assertEqual("FinishedCommitted", state.request.phase)
        self.assertEqual("synthetic:recovery", state.final)

    def test_native_loading_before_start_revokes_only_kvo_not_prior_errors_and_false_loading_is_not_commit(self):
        view, state, _ = self.committed(); state.errors = [(-41, "synthetic preceding error")]
        snapshot = state.snapshot(); view.native_loading = True; state.kvo(view, "loading")
        view.url, view.title = "synthetic:provisional", "synthetic old title changed"
        self.kvo_metadata(state, view)
        self.assertEqual(snapshot[:4], state.snapshot()[:4])
        view.native_loading = False; state.kvo(view, "loading"); self.kvo_metadata(state, view)
        self.assertEqual(snapshot[:4], state.snapshot()[:4])
        navigation = self.navigation(); state.start(view, navigation)
        self.assertEqual((None, None, ()), (state.final, state.title, tuple(state.errors)))

    def test_finish_without_commit_and_nil_inputs_never_certify_current_metadata(self):
        for phase in ("AwaitingStart", "Provisional"):
            with self.subTest(phase=phase):
                view, state = self.fixture(); navigation = self.navigation()
                state.load(view, "synthetic:pending", navigation)
                if phase == "Provisional":
                    state.start(view, navigation)
                snapshot = state.snapshot(); state.start(view, None); state.commit(view, None)
                state.finish(view, None); state.fail(view, None, (-42, "synthetic nil"))
                self.assertEqual(snapshot, state.snapshot())
                state.finish(view, navigation); self.kvo_metadata(state, view)
                self.assertEqual((None, None, ()), (state.final, state.title, tuple(state.errors)))
                self.assertEqual("FinishedUncommitted", state.request.phase)

    def test_release_remount_and_late_binding_drop_native_identities_only_for_the_current_owner(self):
        view, state, old = self.committed(); ticket = state.request
        foreign = SyntheticView(object()); state.release(foreign); self.assertIs(ticket, state.request)
        state.release(view); self.assertIsNone(state.request); self.assertIsNone(state.owner)
        remount = SyntheticView(object()); state.owner = remount
        newer = self.navigation(); current = state.load(remount, "synthetic:remount", newer)
        snapshot = state.snapshot()
        state.bind(view, ticket, old); state.commit(view, old); state.finish(view, old)
        state.fail(view, old, (-43, "synthetic released")); self.kvo_metadata(state, view)
        self.assertIs(current, state.request); self.assertEqual(snapshot, state.snapshot())

    def test_repeated_refusals_keep_one_predecessor_reference_without_accumulating_a_log(self):
        view, state, old = self.committed()
        for _ in range(8):
            state.load(view, None, None, error=(-2, "synthetic unsupported"))
            self.assertIsNone(state.request.navigation)
            self.assertTrue(same_retained(state.request.superseded, old))
            self.assertEqual({"navigation", "superseded", "phase", "stopped"}, set(vars(state.request)))
        state.start(view, old); self.assertEqual([(-2, "synthetic unsupported")], state.errors)


if __name__ == "__main__":
    unittest.main()
