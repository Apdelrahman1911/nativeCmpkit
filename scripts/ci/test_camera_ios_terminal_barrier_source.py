# SPDX-License-Identifier: Apache-2.0
"""NEW narrow Camera terminal/barrier source controls; no Kotlin/UIKit execution.

These inspect comment/string-free owning source and callback boundaries. They
cannot prove UIKit timing, presentation success, GC, image IO or device behavior.
The first execution must precede the two-gap production repair.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
OWNER = "calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt"


def kotlin_code(source):
    """Mask nested comments and quoted strings without turning them into code."""
    masked = list(source)
    index = 0
    while index < len(source):
        start = index
        if source.startswith("//", index):
            end = source.find("\n", index)
            index = len(source) if end < 0 else end
        elif source.startswith("/*", index):
            index += 2
            depth = 1
            while index < len(source) and depth:
                if source.startswith("/*", index):
                    depth += 1
                    index += 2
                elif source.startswith("*/", index):
                    depth -= 1
                    index += 2
                else:
                    index += 1
            if depth:
                raise AssertionError("Unterminated owning-source block comment")
        elif source.startswith('"""', index):
            end = source.find('"""', index + 3)
            if end < 0:
                raise AssertionError("Unterminated owning-source raw string")
            index = end + 3
        elif source[index] in ('"', "'"):
            quote = source[index]
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                elif source[index] == quote:
                    index += 1
                    break
                else:
                    index += 1
            else:
                raise AssertionError("Unterminated owning-source quoted string")
        else:
            index += 1
            continue
        for position in range(start, index):
            if masked[position] != "\n":
                masked[position] = " "
    return "".join(masked)


def block(code, anchor):
    matches = list(re.finditer(anchor, code))
    if len(matches) != 1:
        raise AssertionError("Expected exactly one owning code boundary: " + anchor)
    start = matches[0].end() - 1 if code[matches[0].end() - 1] == "{" else code.find("{", matches[0].end())
    if start < 0:
        raise AssertionError("Missing owning code block: " + anchor)
    depth = 1
    for end in range(start + 1, len(code)):
        depth += (code[end] == "{") - (code[end] == "}")
        if depth == 0:
            return code[start + 1:end]
    raise AssertionError("Unterminated owning code block: " + anchor)


class CameraIosTerminalBarrierSourceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = kotlin_code((ROOT / OWNER).read_text())

    def test_cancel_claims_terminal_input_before_async_finish(self):
        cancel = block(self.code, r"override\s+fun\s+imagePickerControllerDidCancel\([^)]*\)")
        claim = re.search(r"request\.processing\s*=\s*true", cancel)
        self.assertIsNotNone(claim, "Cancellation must claim its input before asynchronous native teardown can admit a duplicate")
        self.assertRegex(cancel[:claim.start()], r"if\s*\(active\s*!==\s*request\s*\|\|\s*request\.processing\)\s*return")
        finish = re.search(r"finish\(request,\s*CameraPickerResult\.Cancelled\)", cancel)
        self.assertIsNotNone(finish)
        self.assertLess(claim.start(), finish.start())

    def test_missing_original_claims_terminal_input_before_failure_finish(self):
        picked = block(self.code, r"override\s+fun\s+imagePickerController\([^)]*\)")
        claim = re.search(r"request\.processing\s*=\s*true", picked)
        missing = re.search(r"if\s*\(image\s*==\s*null\)", picked)
        self.assertIsNotNone(claim)
        self.assertIsNotNone(missing)
        self.assertLess(claim.start(), missing.start(), "A missing-original-image terminal must also be claimed before finish schedules dismissal")
        self.assertRegex(picked[:claim.start()], r"if\s*\(active\s*!==\s*request\s*\|\|\s*request\.processing\)\s*return")

    def test_official_presentation_completion_records_and_advances_owned_barrier(self):
        presentation = block(self.code, r"viewController\.presentViewController\(picker,\s*true\)\s*\{")
        observed = re.search(r"request\.presentationCompleted\s*=\s*true", presentation)
        advanced = re.search(r"advanceDismissal\(request\)", presentation)
        self.assertIsNotNone(observed, "UIKit's actual presentation completion must be recorded, not the void-call return or a nil backlink")
        self.assertIsNotNone(advanced)
        self.assertLess(observed.start(), advanced.start())
        self.assertEqual(1, len(re.findall(r"request\.presentationCompleted\s*=\s*true", self.code)), "Only the official UIKit callback may acknowledge presentation")

    def test_disposal_queues_teardown_without_releasing_native_request_early(self):
        disposal = block(self.code, r"fun\s+dispose\(\)\s*=\s*onCameraMain")
        self.assertNotRegex(disposal, r"request\??\.\s*(?:picker|delegate)\s*=\s*null",
            "Disposal cannot clear the retained picker/delegate before the owned native completion")
        self.assertNotIn("dismissViewControllerAnimated", disposal)
        self.assertRegex(disposal, r"dismissOwned\(it,\s*false\)")
        self.assertIn("active = null", disposal)
        self.assertIn("scope.cancel()", disposal)
        self.assertRegex(disposal, r"request\?\.job\?\.cancel\(\)")

    def test_one_owned_dismissal_waits_for_presentation_and_releases_only_at_completion(self):
        advance = block(self.code, r"private\s+fun\s+advanceDismissal\(request:\s*Request\)")
        guard = re.search(r"if\s*\(!request\.presentationCompleted\s*\|\|\s*request\.dismissalStarted\)\s*return", advance)
        start = re.search(r"request\.dismissalStarted\s*=\s*true", advance)
        native = re.search(r"picker\.dismissViewControllerAnimated\(request\.dismissAnimated\)\s*\{", advance)
        self.assertIsNotNone(guard)
        self.assertIsNotNone(start)
        self.assertIsNotNone(native)
        self.assertLess(guard.start(), start.start())
        self.assertLess(start.start(), native.start(), "The native dismissal must be claimed before the call, even if completion is synchronous")
        self.assertNotRegex(advance[:native.start()], r"request\.(?:picker|delegate)\s*=\s*null")
        completion = block(advance, r"picker\.dismissViewControllerAnimated\(request\.dismissAnimated\)\s*\{")
        invoke = re.search(r"complete\?\.invoke\(\)", completion)
        self.assertIsNotNone(invoke)
        for field in ("picker", "delegate", "afterDismissal"):
            cleared = re.search(r"request\." + field + r"\s*=\s*null", completion)
            self.assertIsNotNone(cleared)
            self.assertLess(cleared.start(), invoke.start(), "Clear only this request before invoking application/encoding continuation")
        self.assertEqual(1, len(re.findall(r"\.dismissViewControllerAnimated\(", self.code)), "Every owning Camera native dismissal must cross the same barrier")


if __name__ == "__main__":
    unittest.main()
