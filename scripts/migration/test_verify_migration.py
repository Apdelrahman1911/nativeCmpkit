"""Offline source-remote safety checks; no Git/GitHub mutation or network calls."""
import unittest
from unittest.mock import call, patch

import verify_migration as module


class UpstreamPushSafetyTests(unittest.TestCase):
    def test_fresh_clone_without_upstream_passes_without_url_lookup(self):
        with patch.object(module, "command", return_value="origin\n") as command:
            safe, detail = module.upstream_push_safety()
        self.assertTrue(safe)
        self.assertIn("No local upstream", detail)
        command.assert_called_once_with("git", "remote")

    def test_existing_explicit_interlock_passes(self):
        with patch.object(module, "command", side_effect=["origin\nupstream\n", "DISABLED_READ_ONLY_UPSTREAM\n"]) as command:
            safe, detail = module.upstream_push_safety()
        self.assertTrue(safe)
        self.assertIn("Every configured upstream push URL is disabled", detail)
        self.assertEqual(command.call_args_list, [call("git", "remote"), call("git", "remote", "get-url", "--push", "--all", "upstream")])

    def test_second_unsafe_push_url_is_not_hidden_by_first_interlock(self):
        url = "https://example.invalid/source.git"
        with patch.object(module, "command", side_effect=["origin\nupstream\n", "DISABLED_READ_ONLY_UPSTREAM\n" + url + "\n"]):
            safe, detail = module.upstream_push_safety()
        self.assertFalse(safe)
        self.assertNotIn(url, detail)

    def test_multiple_interlocked_push_urls_pass(self):
        with patch.object(module, "command", side_effect=["upstream\n", "DISABLED_READ_ONLY_UPSTREAM\nDISABLED_READ_ONLY_UPSTREAM\n"]):
            safe, _ = module.upstream_push_safety()
        self.assertTrue(safe)

    def test_empty_push_url_list_does_not_vacuously_pass(self):
        with patch.object(module, "command", side_effect=["upstream\n", ""]):
            safe, _ = module.upstream_push_safety()
        self.assertFalse(safe)

    def test_configured_unsafe_upstream_fails_without_echoing_url(self):
        url = "https://example.invalid/source.git"
        with patch.object(module, "command", side_effect=["upstream\norigin\n", url + "\n"]):
            safe, detail = module.upstream_push_safety()
        self.assertFalse(safe)
        self.assertNotIn(url, detail)
        self.assertIn("URL omitted", detail)

    def test_lookup_failure_is_not_silently_accepted(self):
        with patch.object(module, "command", side_effect=["origin\nupstream\n", RuntimeError("lookup failed")]):
            with self.assertRaisesRegex(RuntimeError, "lookup failed"):
                module.upstream_push_safety()


if __name__ == "__main__":
    unittest.main()
