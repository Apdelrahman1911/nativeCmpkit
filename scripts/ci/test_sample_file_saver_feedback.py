"""NEW-only sample source wiring guards, not library/native/browser acceptance.

The production legacy saver adapter stays deliberately unchanged. The separate
Kotlin common/desktop tests exercise the exact sample event-to-feedback mapping;
no source guard below claims an actual browser download or filesystem save.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = "sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/FileSaverScreen.kt"
COMMON_TEST = "sample/common/src/commonTest/kotlin/com/mohamedrejeb/calf/sample/screens/SampleFileSaverFeedbackTest.kt"
DESKTOP_TEST = "sample/common/src/desktopTest/kotlin/com/mohamedrejeb/calf/sample/screens/SampleFileSaverSavedFeedbackTest.kt"
LEGACY_WEB_SAVER = "calf-file-picker/src/webMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.web.kt"


class SampleFileSaverFeedbackSourceTests(unittest.TestCase):
    def test_actual_sample_callback_copies_all_structured_feedback_fields_and_does_not_wait_on_legacy_result(self):
        source = (ROOT / SAMPLE).read_text()
        for fragment in ("val saverLauncher = rememberFileSaverEventLauncher(", "onEvent = { event ->",
                         "val feedback = event.toSampleSaverFeedback()", "isSaving = feedback.isSaving",
                         "saveFailed = feedback.failed", "saveMessage = feedback.message",
                         "is FileSaverEvent.Saved ->", "FileSaverEvent.Cancelled ->",
                         "is FileSaverEvent.DownloadStarted ->", "is FileSaverEvent.Failed ->",
                         "Download requested: $fileName. Check your browser's downloads."):
            self.assertIn(fragment, source)
        self.assertNotIn("rememberFileSaverLauncher", source)
        mapping = source.split("internal fun FileSaverEvent.toSampleSaverFeedback()", 1)[1].split("/** Bounded sample", 1)[0]
        self.assertEqual(4, mapping.count("SampleSaverFeedback("))
        self.assertNotIn("SampleSaverFeedback(true", mapping)
        self.assertNotIn("error.message", mapping)

    def test_new_mapping_tests_are_sample_only_and_the_library_download_adapter_remains_truthful(self):
        legacy = (ROOT / LEGACY_WEB_SAVER).read_text()
        self.assertIn("is FileSaverEvent.DownloadStarted -> Unit // Historical API has no truthful destination result.", legacy)
        self.assertIn("FileSaverEvent.DownloadStarted(name)", legacy)
        common_test = (ROOT / COMMON_TEST).read_text()
        desktop_test = (ROOT / DESKTOP_TEST).read_text()
        self.assertEqual(4, common_test.count("@Test fun "))
        self.assertEqual(1, desktop_test.count("@Test fun "))
        self.assertIn("downloadStartedLeavesWaitingWithoutClaimingSavedOrCancelled", common_test)
        self.assertIn("cancellationLeavesWaitingButDoesNotBecomeAFailure", common_test)
        self.assertIn("failureLeavesWaitingAndDoesNotExposeTheDiagnosticMessage", common_test)
        self.assertIn("laterDownloadRequestClearsEarlierFailureAndKeepsItsLiteralSuggestedName", common_test)
        self.assertIn("onlyASavedEventClaimsSavedAndClearsTheWaitingState", desktop_test)
        for sample_test in (common_test, desktop_test):
            self.assertIn(".toSampleSaverFeedback()", sample_test)
            self.assertNotIn("runApplicationUiTest", sample_test)
            self.assertNotIn("UIActivityViewController", sample_test)
            self.assertNotIn("writeBytes", sample_test)


if __name__ == "__main__":
    unittest.main()
