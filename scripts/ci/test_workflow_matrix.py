import unittest

import workflow_matrix as m


class WorkflowMatrixTests(unittest.TestCase):
    def test_all_has_exact_ten_distinct_slots(self):
        rows = m.matrix("all")["include"]
        self.assertEqual(10, len(rows))
        self.assertEqual(10, len({row["slot"] for row in rows}))
        self.assertEqual({"desktop", "android-host", "ios", "js", "wasm"}, {row["suite"] for row in rows})

    def test_incremental_profiles_cover_all_without_repeating_slots(self):
        slots = [row["slot"] for profile in ("core", "browser", "apple", "windows", "extended")
                 for row in m.matrix(profile)["include"]]
        self.assertEqual(len(slots), len(set(slots)))
        self.assertEqual(set(m.PROFILES["all"]), set(slots))

    def test_core_is_bounded_and_not_an_android_device_claim(self):
        self.assertEqual(["desktop", "android-host"], [row["suite"] for row in m.matrix("core")["include"]])

    def test_tooling_selects_no_library_execution(self):
        self.assertEqual({"include": []}, m.matrix("tooling"))

    def test_both_macos_hosts_require_real_native_ui(self):
        rows = [row for row in m.matrix("all")["include"] if row["suite"] == "desktop" and row["runner"].startswith("macos")]
        self.assertEqual({"arm64", "x64"}, {row["arch"] for row in rows})
        self.assertTrue(all(row["native-ui"] == "true" for row in rows))

    def test_ios_never_silently_substitutes_intel_or_ipad_for_iphone(self):
        rows = [row for row in m.matrix("all")["include"] if row["suite"] == "ios"]
        self.assertEqual({"iphone", "ipad"}, {row["simulator-kind"] for row in rows})
        self.assertTrue(all(row["arch"] == "arm64" and row["runner"] == "macos-26" for row in rows))

    def test_unknown_or_shell_shaped_profiles_are_rejected(self):
        for profile in ("", "Core", "all; echo unsafe", "${{ inputs.runner }}", "self-hosted"):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                m.matrix(profile)

    def test_callers_cannot_mutate_future_matrix_results(self):
        selected = m.matrix("core")
        selected["include"][0]["runner"] = "self-hosted"
        self.assertEqual("ubuntu-24.04", m.matrix("core")["include"][0]["runner"])


if __name__ == "__main__":
    unittest.main()
