import unittest

import workflow_matrix as m


class WorkflowMatrixTests(unittest.TestCase):
    def test_all_has_exact_eleven_distinct_slots_including_native_android(self):
        rows = m.matrix("all")["include"]
        self.assertEqual(11, len(rows))
        self.assertEqual(11, len({row["slot"] for row in rows}))
        self.assertEqual({"desktop", "android-host", "android-device", "ios", "js", "wasm"}, {row["suite"] for row in rows})

    def test_incremental_profiles_cover_all_without_repeating_slots(self):
        slots = [row["slot"] for profile in ("core", "browser", "apple", "windows", "extended", "android-device")
                 for row in m.matrix(profile)["include"]]
        self.assertEqual(len(slots), len(set(slots)))
        self.assertEqual(set(m.PROFILES["all"]), set(slots))

    def test_core_is_bounded_and_not_an_android_device_claim(self):
        self.assertEqual(["desktop", "android-host"], [row["suite"] for row in m.matrix("core")["include"]])

    def test_native_android_has_one_fixed_api_abi_and_runner_not_user_input(self):
        rows = m.matrix("android-device")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("android-device", rows[0]["suite"])
        self.assertEqual("ubuntu-24.04", rows[0]["runner"])
        self.assertEqual("x64", rows[0]["arch"])
        self.assertEqual("35", rows[0]["emulator-api"])

    def test_android_webview_diagnostic_does_not_repeat_passing_io_or_known_picker_failure(self):
        rows = m.matrix("android-webview")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("android-device-api35", rows[0]["slot"])
        self.assertEqual("android-device", rows[0]["suite"])
        self.assertEqual("calf-webview", rows[0]["test-modules"])
        self.assertNotIn("test-modules", m.matrix("android-device")["include"][0])

    def test_tooling_selects_no_library_execution(self):
        self.assertEqual({"include": []}, m.matrix("tooling"))

    def test_partial_consumer_selects_no_duplicate_library_or_other_host_suites(self):
        self.assertEqual({"include": []}, m.matrix("consumer-core-io"))
        self.assertNotIn("consumer-core-io", m.MODULE_SUBSETS)

    def test_targeted_native_profiles_do_not_repeat_successful_other_hosts(self):
        self.assertEqual(["ios-iphone"], [row["slot"] for row in m.matrix("ios")["include"]])
        self.assertEqual("calf-ui", m.matrix("ios-ui")["include"][0]["test-modules"])
        cache = m.matrix("windows-cache")["include"]
        self.assertEqual(1, len(cache))
        self.assertEqual("desktop-windows-x64", cache[0]["slot"])
        self.assertEqual("calf-file-picker,calf-share", cache[0]["test-modules"])

    def test_windows_share_loader_recovery_never_repeats_the_accepted_picker_or_other_hosts(self):
        rows = m.matrix("windows-share-loader")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("desktop-windows-x64", rows[0]["slot"])
        self.assertEqual("calf-share", rows[0]["test-modules"])
        rows[0]["test-modules"] = "calf-file-picker"
        self.assertEqual("calf-share", m.matrix("windows-share-loader")["include"][0]["test-modules"])
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_windows_share_boundaries_are_five_fixed_methods_not_unrelated_bridge_replay(self):
        rows = m.matrix("windows-share-boundaries")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("desktop-windows-x64", rows[0]["slot"])
        self.assertEqual("calf-share", rows[0]["test-modules"])
        self.assertEqual("native-share-boundaries", rows[0]["test-focus"])
        for profile in ("all", "windows-cache", "windows-share-loader"):
            self.assertTrue(all("test-focus" not in r for r in m.matrix(profile)["include"]))
        rows[0]["test-focus"] = "arbitrary"
        self.assertEqual("native-share-boundaries", m.matrix("windows-share-boundaries")["include"][0]["test-focus"])

    def test_browser_picker_acceptance_runs_only_both_changed_browser_targets(self):
        rows = m.matrix("browser-picker")["include"]
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in rows])
        self.assertTrue(all(row["test-modules"] == "calf-file-picker" for row in rows))
        rows[0]["test-modules"] = "calf-io"
        self.assertEqual("calf-file-picker", m.matrix("browser-picker")["include"][0]["test-modules"])
        for profile in ("browser", "all"):
            self.assertTrue(all("test-modules" not in row for row in m.matrix(profile)["include"]))
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_public_browser_webview_acceptance_does_not_repeat_other_modules_or_native_hosts(self):
        rows = m.matrix("webview-browser")["include"]
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in rows])
        self.assertEqual(["js", "wasm"], [row["suite"] for row in rows])
        self.assertTrue(all(row["test-modules"] == "calf-webview" for row in rows))
        rows[0]["test-modules"] = "calf-share"
        self.assertEqual("calf-webview", m.matrix("webview-browser")["include"][0]["test-modules"])
        self.assertEqual("calf-webview", m.matrix("webview-desktop")["include"][0]["test-modules"])
        for profile in ("browser", "all"):
            self.assertTrue(all("test-modules" not in row for row in m.matrix(profile)["include"]))
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_browser_share_callback_scope_does_not_replay_unchanged_android_or_other_libraries(self):
        rows = m.matrix("share-browser")["include"]
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in rows])
        self.assertTrue(all(row["test-modules"] == "calf-share" for row in rows))
        rows[0]["test-modules"] = "calf-webview"
        self.assertEqual("calf-share", m.matrix("share-browser")["include"][0]["test-modules"])
        self.assertTrue(all("test-modules" not in row for row in m.matrix("browser")["include"]))
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_navigation_geo_profile_requests_only_the_two_browser_slots(self):
        rows = m.matrix("navigation-geo")["include"]
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in rows])
        self.assertEqual(["js", "wasm"], [row["suite"] for row in rows])
        self.assertTrue(all(row["test-modules"] == "calf-navigation,calf-geo" for row in rows))
        self.assertTrue(all(row["runner"] == "ubuntu-24.04" for row in rows))

    def test_jvm_navigation_probe_does_not_repeat_unchanged_browser_native_or_geo_suites(self):
        rows = m.matrix("navigation-desktop")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("desktop-linux-x64", rows[0]["slot"])
        self.assertEqual("desktop", rows[0]["suite"])
        self.assertEqual("ubuntu-24.04", rows[0]["runner"])
        self.assertEqual("calf-navigation", rows[0]["test-modules"])

    def test_desktop_data_safety_runs_only_the_changed_owners_on_three_os_families(self):
        rows = m.matrix("desktop-data-safety")["include"]
        self.assertEqual(["desktop-linux-x64", "desktop-macos-arm64", "desktop-windows-x64"], [r["slot"] for r in rows])
        self.assertTrue(all(r["suite"] == "desktop" and r["test-modules"] == "calf-file-picker,calf-share" for r in rows))
        rows[0]["test-modules"] = "calf-ui"
        self.assertEqual("calf-file-picker,calf-share", m.matrix("desktop-data-safety")["include"][0]["test-modules"])
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_android_resource_safety_is_a_single_host_owner_subset_not_a_device_claim(self):
        rows = m.matrix("android-resource-safety")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("android-host", rows[0]["slot"])
        self.assertEqual("android-host", rows[0]["suite"])
        self.assertEqual("calf-io,calf-file-picker-coil", rows[0]["test-modules"])
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_android_coil_fixture_repair_does_not_replay_the_unchanged_io_suite(self):
        rows = m.matrix("android-coil-resource")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("android-host", rows[0]["slot"])
        self.assertEqual("calf-file-picker-coil", rows[0]["test-modules"])
        self.assertEqual("calf-io,calf-file-picker-coil", m.matrix("android-resource-safety")["include"][0]["test-modules"])
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_android_permission_alias_acceptance_runs_only_the_changed_core_host(self):
        rows = m.matrix("android-permission-alias")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("android-host", rows[0]["slot"])
        self.assertEqual("android-host", rows[0]["suite"])
        self.assertEqual("calf-permissions/core", rows[0]["test-modules"])
        rows[0]["test-modules"] = "calf-io"
        self.assertEqual("calf-permissions/core", m.matrix("android-permission-alias")["include"][0]["test-modules"])
        self.assertEqual(11, len(m.matrix("all")["include"]))
        self.assertTrue(all("test-modules" not in row for row in m.matrix("all")["include"]))

    def test_jvm_navigation_subset_cannot_mutate_full_or_future_profiles(self):
        selected = m.matrix("navigation-desktop")
        selected["include"][0]["test-modules"] = "calf-ui"
        self.assertEqual("calf-navigation", m.matrix("navigation-desktop")["include"][0]["test-modules"])
        for profile in ("core", "browser", "apple", "all"):
            self.assertTrue(all("test-modules" not in row for row in m.matrix(profile)["include"]))
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_navigation_geo_subset_never_reduces_complete_browser_or_all_coverage(self):
        selected = m.matrix("navigation-geo")
        selected["include"][0]["test-modules"] = "calf-io"
        self.assertEqual("calf-navigation,calf-geo", m.matrix("navigation-geo")["include"][0]["test-modules"])
        for profile in ("browser", "all"):
            self.assertTrue(all("test-modules" not in row for row in m.matrix(profile)["include"]))
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_changed_navigation_geo_tests_get_all_four_required_runtimes_without_unrelated_suites(self):
        rows = m.matrix("navigation-geo-matrix")["include"]
        self.assertEqual(["desktop-linux-x64", "browser-js", "browser-wasm", "ios-iphone"],
                         [row["slot"] for row in rows])
        self.assertEqual({"desktop", "js", "wasm", "ios"}, {row["suite"] for row in rows})
        self.assertTrue(all(row["test-modules"] == "calf-navigation,calf-geo" for row in rows))
        self.assertNotIn("consumer-core-io", {row["slot"] for row in rows})
        self.assertTrue(all(row["suite"] != "android-device" for row in rows))
        for profile in ("core", "browser", "apple", "all"):
            self.assertTrue(all("test-modules" not in row for row in m.matrix(profile)["include"]))

    def test_new_matrix_does_not_mutate_the_browser_only_continuation(self):
        selected = m.matrix("navigation-geo-matrix")
        selected["include"][0]["test-modules"] = "calf-ui"
        self.assertEqual("calf-navigation,calf-geo", m.matrix("navigation-geo-matrix")["include"][0]["test-modules"])
        self.assertEqual(["browser-js", "browser-wasm"],
                         [row["slot"] for row in m.matrix("navigation-geo")["include"]])

    def test_complete_profiles_never_silently_select_a_module_subset(self):
        for profile in set(m.PROFILES) - set(m.MODULE_SUBSETS):
            for row in m.matrix(profile)["include"]:
                with self.subTest(profile=profile, slot=row["slot"]):
                    self.assertNotIn("test-modules", row)

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
