"""Owning source/synthetic extension for live known-navigation weak identity.

No native Foundation, WebKit, NSError, compilation or actual callback-order proof.
The prior phase model remains exact; this extension models the new bookkeeping.
"""
import gc
from pathlib import Path
import unittest
import weakref

import test_ios_webview_current_request_metadata as phase

ROOT = Path(__file__).resolve().parents[2]


class SyntheticAllocation:
    """An opaque weak-referenceable stand-in, never a native object or address."""


class SyntheticNativeWeakMembership:
    """Synthetic identity/weak-lifetime behavior, not NSHashTable execution."""
    def __init__(self):
        self.references = []

    def prune(self):
        self.references = [reference for reference in self.references if reference() is not None]

    def contains(self, navigation):
        self.prune()
        return navigation is not None and any(
            reference() is navigation.allocation for reference in self.references)

    def add(self, navigation):
        if navigation is not None and not self.contains(navigation):
            self.references.append(weakref.ref(navigation.allocation))

    def clear(self):
        self.references.clear()

    def count(self):
        self.prune()
        return len(self.references)


class WeakKnownNavigationModel(phase.SourceLinkedModel):
    """Refine only binding/start/release bookkeeping; retain phase/KVO semantics."""
    def __init__(self, view):
        super().__init__(view)
        self.known = SyntheticNativeWeakMembership()

    def bind(self, view, ticket, navigation):
        if not self.owns(view) or navigation is None:
            return
        self.known.add(navigation)
        super().bind(view, ticket, navigation)

    def start(self, view, navigation):
        if not self.owns(view) or navigation is None:
            return
        previous = self.request
        if not phase.same_retained(previous.navigation if previous else None, navigation) and (
                self.known.contains(navigation) or
                phase.same_retained(previous.superseded if previous else None, navigation)):
            return
        if previous is not None and phase.same_retained(previous.navigation, navigation):
            if previous.phase != "AwaitingStart" or previous.stopped:
                return
            ticket = previous
        elif previous is not None and previous.navigation is None and previous.phase == "AwaitingStart":
            if previous.stopped:
                return
            previous.navigation = navigation
            ticket = previous
        else:
            ticket = phase.SyntheticRequest(
                navigation=navigation,
                superseded=(previous.navigation or previous.superseded) if previous else None)
            self.request = ticket
        self.known.add(navigation)
        ticket.phase = "Provisional"
        self.reset(view.url if view.url is not None else self.requested)

    def release(self, view):
        if self.owns(view):
            self.known.clear()
        super().release(view)


class IosKnownNavigationWeakIdentitySourceTests(unittest.TestCase):
    def source(self):
        return (ROOT / phase.IOS).read_text()

    def test_native_weak_pointer_membership_preserves_owner_null_and_reentrant_binding_gates(self):
        source = self.source()
        for symbol in ("NSHashTable", "NSPointerFunctionsWeakMemory", "NSPointerFunctionsObjectPointerPersonality"):
            self.assertIn("import platform.Foundation." + symbol, source)
        self.assertIn("private val knownIosNavigations = NSHashTable(\n"
                      "        options = NSPointerFunctionsWeakMemory or NSPointerFunctionsObjectPointerPersonality,\n"
                      "        capacity = 0uL,\n    )", source)
        binding = phase.block(source, "internal fun bindIosNavigation")
        self.assertIn("if (!hasSameNativeWebView(webView, view) || navigation == null) return", binding)
        self.assertLess(binding.index("navigation == null"), binding.index("knownIosNavigations.addObject(navigation)"))
        self.assertLess(binding.index("knownIosNavigations.addObject(navigation)"), binding.index("if (iosRequest !== request) return"))
        self.assertLess(binding.index("if (iosRequest !== request) return"), binding.index("if (request.navigation == null) request.navigation = navigation"))
        self.assertNotIn("request.phase =", binding)

    def test_three_issued_source_requires_current_match_before_known_live_start_refusal(self):
        start = phase.block(self.source(), "private fun beginIosNavigation")
        self.assertIn("if (navigation == null) return", start)
        refusal = "if (!hasSameNativeNavigation(previous?.navigation, navigation) &&\n" \
                  "            (knownIosNavigations.containsObject(navigation) ||\n" \
                  "                hasSameNativeNavigation(previous?.supersededNavigation, navigation))) return"
        self.assertIn(refusal, start,
                      "A→B→C must retain current C against any still-live previously issued/observed A")
        self.assertLess(start.index(refusal), start.index("val request = when"))
        self.assertLess(start.index("knownIosNavigations.addObject(navigation)"), start.index("request.phase = IosWebViewRequestPhase.Provisional"))
        self.assertLess(start.index("knownIosNavigations.addObject(navigation)"), start.index("beginRequest(view.URL?.absoluteString ?: requestedUrl)"))
        self.assertIn("else -> IosWebViewRequest(", start,
                      "Unseen genuine native starts remain adoptable during active loads")
        self.assertNotIn("previous.phase", start[:start.index("val request = when")])

    def test_owned_final_release_clears_weak_keys_without_new_strong_history_or_addresses(self):
        source = self.source()
        clearing = phase.block(source, "internal fun clearIosRequestMetadata")
        self.assertEqual("knownIosNavigations.removeAllObjects()\n        iosRequest = null", clearing.strip())
        self.assertEqual(1, source.count("knownIosNavigations.removeAllObjects()"))
        self.assertEqual(1, source.count("state.clearIosRequestMetadata()"))
        release = phase.block(source, "private fun releaseIosWebView")
        self.assertIn("if (hasSameNativeWebView(state.webView, view)) {\n                state.clearIosRequestMetadata()", release)
        for forbidden in ("mutableListOf<WKNavigation", "mutableSetOf<WKNavigation", "MutableMap<WKNavigation", ".rawValue", ".toLong()"):
            self.assertNotIn(forbidden, source)
        for retained in ("onDispose,", "observer?.stopObserving(view)", "view.navigationDelegate = null", "view.stopLoading()", "view.removeFromSuperview()"):
            self.assertIn(retained, release)
        self.assertIn("WebViewNavigator.NavigationEvent.Back -> if (webView.canGoBack) webView.goBack()", source)
        self.assertIn("WebViewNavigator.NavigationEvent.Forward -> if (webView.canGoForward) webView.goForward()", source)


class IosKnownNavigationWeakIdentitySyntheticTests(unittest.TestCase):
    def navigation(self):
        return phase.SyntheticRetainedObject(SyntheticAllocation())

    def fixture(self):
        view = phase.SyntheticView(SyntheticAllocation())
        return view, WeakKnownNavigationModel(view)

    def committed(self):
        view, state = self.fixture()
        navigation = self.navigation()
        state.load(view, "synthetic:old", navigation)
        state.start(view, navigation)
        state.commit(view, navigation)
        state.finish(view, navigation)
        return view, state, navigation

    def test_three_issued_handles_cannot_re_adopt_first_before_current_start(self):
        view, state = self.fixture()
        first, second, current = (self.navigation() for _ in range(3))
        state.load(view, "synthetic:issued-A", first)
        state.load(view, "synthetic:issued-B", second)
        ticket = state.load(view, "synthetic:issued-C", current)
        snapshot = state.snapshot()
        view.url, view.title = "synthetic:stale-A", "synthetic stale A"
        for callback in (lambda: state.start(view, first), lambda: state.commit(view, first),
                         lambda: state.finish(view, first),
                         lambda: state.fail(view, first, (-81, "synthetic stale error"))):
            callback()
            self.assertIs(ticket, state.request, "Known live A cannot replace the returned current C handle")
            self.assertEqual(snapshot, state.snapshot())
        state.start(view, second)
        self.assertIs(ticket, state.request)
        view.url, view.title = "synthetic:current-C", "synthetic current C"
        state.start(view, phase.SyntheticRetainedObject(current.allocation))
        self.assertIs(ticket, state.request)
        self.assertEqual("Provisional", ticket.phase)
        state.commit(view, current)
        self.assertEqual((view.url, view.title), (state.final, state.title))

    def test_unseen_genuine_native_start_can_replace_every_active_or_terminal_phase(self):
        for selected in ("AwaitingStart", "Provisional", "Committed", "FinishedCommitted", "FinishedUncommitted", "SuspendedCommitted"):
            with self.subTest(phase=selected):
                view, state = self.fixture()
                current, newer = self.navigation(), self.navigation()
                ticket = state.load(view, "synthetic:issued", current)
                if selected != "AwaitingStart":
                    state.start(view, current)
                if selected in ("Committed", "FinishedCommitted", "SuspendedCommitted"):
                    state.commit(view, current)
                if selected in ("FinishedCommitted", "SuspendedCommitted"):
                    state.finish(view, current)
                if selected == "FinishedUncommitted":
                    state.fail(view, current, (-88, "synthetic old failure"))
                if selected == "SuspendedCommitted":
                    view.native_loading = True
                    state.kvo(view, "loading")
                self.assertEqual(selected, ticket.phase)
                view.url = "synthetic:real-new-link-or-history"
                state.start(view, newer)
                self.assertIsNot(ticket, state.request)
                self.assertTrue(phase.same_retained(newer, state.request.navigation))
                self.assertEqual((view.url, None, None, ()), state.snapshot()[:4])
                state.errors.append((-89, "synthetic current marker"))
                state.start(view, phase.SyntheticRetainedObject(newer.allocation))
                self.assertEqual([(-89, "synthetic current marker")], state.errors)

    def test_reentrantly_replaced_issued_return_is_known_without_binding_or_reopening(self):
        view, state = self.fixture()
        first, current = self.navigation(), self.navigation()
        issuing = state.prepare()
        state.reset("synthetic:issuing")
        replacement = state.prepare()
        state.reset("synthetic:replacement")
        state.start(view, current)
        state.commit(view, current)
        snapshot = state.snapshot()
        state.bind(view, issuing, first)
        self.assertIs(replacement, state.request)
        self.assertTrue(state.known.contains(first))
        self.assertTrue(phase.same_retained(current, replacement.navigation))
        state.start(view, first)
        self.assertIs(replacement, state.request)
        self.assertEqual(snapshot, state.snapshot())
        state.bind(view, replacement, current)
        self.assertEqual("Committed", replacement.phase)

    def test_weak_keys_follow_allocation_lifetime_not_wrapper_or_value_equality(self):
        membership = SyntheticNativeWeakMembership()
        navigation = self.navigation()
        bridged = phase.SyntheticRetainedObject(navigation.allocation)
        observed = weakref.ref(navigation.allocation)
        membership.add(navigation)
        membership.add(bridged)
        self.assertEqual(1, membership.count())
        del navigation
        gc.collect()
        self.assertIsNotNone(observed())
        self.assertTrue(membership.contains(bridged))
        del bridged
        gc.collect()
        self.assertIsNone(observed(), "Synthetic weak bookkeeping must not retain an allocation")
        self.assertEqual(0, membership.count())
        class ValueEqualAllocation(SyntheticAllocation):
            def __eq__(self, other):
                return True
            def __hash__(self):
                return 1
        first = phase.SyntheticRetainedObject(ValueEqualAllocation())
        separate = phase.SyntheticRetainedObject(ValueEqualAllocation())
        self.assertEqual(first.allocation, separate.allocation)
        membership.add(first)
        self.assertFalse(membership.contains(separate))
        for _ in range(128):
            temporary = self.navigation()
            membership.add(temporary)
        del temporary
        gc.collect()
        self.assertEqual(1, membership.count())

    def test_null_foreign_and_released_owners_never_add_membership(self):
        view, state = self.fixture()
        foreign = phase.SyntheticView(SyntheticAllocation())
        navigation = self.navigation()
        ticket = state.prepare()
        state.bind(view, ticket, None)
        state.start(view, None)
        state.bind(foreign, ticket, navigation)
        state.start(foreign, navigation)
        self.assertEqual(0, state.known.count())
        self.assertIsNone(ticket.navigation)
        state.release(view)
        state.bind(view, ticket, navigation)
        state.start(view, navigation)
        self.assertEqual(0, state.known.count())
        self.assertIsNone(state.request)

    def test_only_owned_release_clears_keys_and_current_precommit_stop_still_refuses_commit(self):
        view, state = self.fixture()
        navigation = self.navigation()
        ticket = state.load(view, "synthetic:held", navigation)
        state.start(view, navigation)
        state.stop(view)
        state.commit(view, navigation)
        self.assertEqual((None, None), (state.final, state.title))
        state.fail(view, navigation, (-999, "synthetic cancellation, not native evidence"))
        self.assertEqual([-999], [code for code, _ in state.errors])
        state.release(phase.SyntheticView(SyntheticAllocation()))
        self.assertIs(ticket, state.request)
        self.assertTrue(state.known.contains(navigation))
        state.release(phase.SyntheticView(view.allocation))
        self.assertIsNone(state.request)
        self.assertEqual(0, state.known.count())

    def test_unidentified_loading_stop_does_not_poison_a_genuinely_new_native_start(self):
        # KVO has no navigation token. This intentionally does not certify Stop for the
        # unidentified pre-start native interval or guess which future token it stopped.
        view, state, current = self.committed()
        state.errors.append((-92, "synthetic preceding error"))
        view.native_loading = True
        state.kvo(view, "loading")
        ticket = state.request
        self.assertEqual("SuspendedCommitted", ticket.phase)
        state.stop(view)
        self.assertFalse(ticket.stopped)
        self.assertEqual([(-92, "synthetic preceding error")], state.errors)
        newer = self.navigation()
        view.url = "synthetic:genuine-later-link"
        state.start(view, newer)
        self.assertIsNot(ticket, state.request)
        self.assertFalse(state.request.stopped)
        self.assertEqual((view.url, None, None, ()), state.snapshot()[:4])
        state.commit(view, newer)
        self.assertEqual(view.url, state.final)


if __name__ == "__main__":
    unittest.main()
