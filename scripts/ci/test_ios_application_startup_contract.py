"""Test-host source guards, NOT UIKit, Worker, KGP or library executions.

The actual immutable application failure is the runtime red. These guards keep
the owning startup fix from replacing it with a sleep, a weaker identity test,
an eager activation assertion, duplicate workers or an unbounded readiness wait.
"""
from pathlib import Path
import unittest

HOST = Path(__file__).resolve().parents[2] / (
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt")


class IosApplicationStartupContractTests(unittest.TestCase):
    def setUp(self):
        self.source = HOST.read_text()

    def section(self, first, last):
        self.assertIn(first, self.source)
        self.assertIn(last, self.source)
        return self.source.split(first, 1)[1].split(last, 1)[0]

    def test_activation_schedules_main_loop_without_eager_attachment_or_worker(self):
        callback = self.section("override fun applicationDidBecomeActive", "private fun awaitApplicationReadiness")
        self.assertIn("check(NSThread.isMainThread)", callback)
        self.assertIn("if (activationRequested) return", callback)
        self.assertIn("activationRequested = true", callback)
        self.assertIn("NSTimer.scheduledTimerWithTimeInterval", callback)
        self.assertNotIn("requireOwnedApplicationWindow()", callback)
        self.assertNotIn("Worker.start(", callback)
        self.assertNotIn("usleep(", callback)

    def test_pending_readiness_returns_without_admitting_generated_tests(self):
        poll = self.section("private fun pollCompletion()", "fun nativeApplicationMain")
        self.assertIn("check(NSThread.isMainThread)", poll)
        self.assertIn("if (!started)", poll)
        pending = "if (!awaitApplicationReadiness()) return"
        self.assertIn(pending, poll)
        self.assertLess(poll.index(pending), poll.index("startGeneratedTests()"))
        self.assertLess(poll.index("startGeneratedTests()"), poll.index("val pending = runner"))

    def test_readiness_retains_all_actual_native_attachment_predicates(self):
        readiness = self.section("private fun awaitApplicationReadiness", "private fun startGeneratedTests")
        predicate = ("val ready = UIApplication.sharedApplication.applicationState == UIApplicationStateActive &&\n"
                     "            window.isKeyWindow() && !window.hidden && attached === window")
        self.assertIn(predicate, readiness)
        self.assertIn("val attached = window.rootViewController?.view?.window", readiness)
        self.assertIn("if (ready) return true", readiness)
        self.assertNotIn("attached == window) return true", readiness)
        self.assertIn("return false", readiness)
        # The existing owning contract itself is NOT relaxed by startup polling.
        contract = self.section("internal fun requireOwnedApplicationWindow()", "/** Real ComposeUIViewController")
        self.assertIn("window.rootViewController?.view?.window === window", contract)

    def test_startup_timeout_is_bounded_and_distinguishes_false_native_predicates(self):
        readiness = self.section("private fun awaitApplicationReadiness", "private fun startGeneratedTests")
        self.assertIn("NSProcessInfo.processInfo.systemUptime - startedAt >= 10.0", readiness)
        self.assertIn("NATIVECMPKIT_UIKIT_STARTUP_TIMEOUT", readiness)
        for field in ("active=", "key=", "hidden=", "rootAttached=", "rootNativeEqual=", "workerStarted=false"):
            self.assertIn(field, readiness)
        self.assertLess(readiness.index("releaseMainLeases()"), readiness.index("exitProcess(2)"))
        self.assertNotIn("Worker.start(", readiness)

    def test_exactly_once_admission_and_existing_timer_worker_release_are_retained(self):
        admission = self.section("private fun startGeneratedTests", "private fun releaseMainLeases")
        self.assertIn("check(!started && worker == null && runner == null && termination == null)", admission)
        self.assertLess(admission.index("requireOwnedApplicationWindow()"), admission.index("started = true"))
        self.assertLess(admission.index("started = true"), admission.index("Worker.start("))
        self.assertEqual(1, self.source.count("Worker.start("))
        release = self.section("private fun releaseMainLeases", "private fun pollCompletion")
        self.assertIn("timer?.invalidate()", release)
        self.assertLess(release.index("timer?.invalidate()"), release.index("applicationWindow = null"))
        poll = self.section("private fun pollCompletion()", "fun nativeApplicationMain")
        self.assertIn("requestTermination()", poll)
        self.assertLess(poll.index("stopping.result"), poll.index("NATIVECMPKIT_UIKIT_COMPLETED"))


if __name__ == "__main__":
    unittest.main()
