# SPDX-License-Identifier: Apache-2.0
"""NEW offline inventory/identity controls; synthetic JSON is not native evidence."""
from __future__ import annotations

import copy
import json
import unittest

import ios_adaptive_controls_runtime as adaptive
import runtime_context as existing

PREFIX = "com.apple.CoreSimulator.SimRuntime."
TYPE = "com.apple.CoreSimulator.SimDeviceType."
OLD = PREFIX + "iOS-18-6"
NEW = PREFIX + "iOS-26-4"
OLD_ID = "00000000-0000-4000-8000-000000000001"
NEW_ID = "00000000-0000-4000-8000-000000000002"


def documents():
    def device(udid, kind):
        return {"udid": udid, "deviceTypeIdentifier": TYPE + kind, "state": "Shutdown",
                "isAvailable": True, "name": "private user-assigned device name", "dataPath": "/private/device/path"}
    def runtime(identifier, version, build):
        return {"identifier": identifier, "version": version, "buildversion": build,
                "isAvailable": True, "bundlePath": "/private/runtime/path"}
    return ({"devices": {OLD: [device(OLD_ID, "iPhone-16")], NEW: [device(NEW_ID, "iPhone-Air")]}},
            {"runtimes": [runtime(OLD, "18.6", "22G86"), runtime(NEW, "26.4.1", "23E254a")]})


def select(devices, runtimes, focus, **kwargs):
    return adaptive.select_iphone_json(json.dumps(devices), json.dumps(runtimes), focus, **kwargs)


class AdaptiveRuntimeInventoryControls(unittest.TestCase):
    def test_both_focuses_choose_their_actual_available_band_and_preserve_full_patch_build(self):
        devices, runtimes = documents()
        before = copy.deepcopy((devices, runtimes))
        for focus, udid, version, build in zip(adaptive.FOCUSES, (OLD_ID, NEW_ID), ("18.6", "26.4.1"), ("22G86", "23E254a")):
            result = select(devices, runtimes, focus)
            self.assertEqual(udid, result["udid"])
            self.assertEqual(version, result["runtime_version"])
            self.assertEqual(build, result["runtime_build"])
            self.assertEqual(adaptive.SIMULATOR_FIELDS, set(result))
            self.assertTrue(adaptive.validate_selected(result, focus))
        self.assertEqual(before, (devices, runtimes))

    def test_missing_requested_band_refuses_instead_of_using_latest_other_band_or_booted_device(self):
        for focus, removed in zip(adaptive.FOCUSES, (OLD, NEW)):
            devices, runtimes = documents()
            del devices["devices"][removed]
            runtimes["runtimes"] = [row for row in runtimes["runtimes"] if row["identifier"] != removed]
            next(iter(devices["devices"].values()))[0]["state"] = "Booted"
            with self.subTest(focus=focus), self.assertRaisesRegex(ValueError, "No actually available iPhone"):
                select(devices, runtimes, focus)

    def test_unavailable_runtime_and_device_each_refuse_even_when_the_other_is_available(self):
        for focus, identifier in zip(adaptive.FOCUSES, (OLD, NEW)):
            for target in ("runtime", "device"):
                devices, runtimes = documents()
                row = devices["devices"][identifier][0] if target == "device" else next(
                    row for row in runtimes["runtimes"] if row["identifier"] == identifier)
                row["isAvailable"] = False
                with self.subTest(focus=focus, target=target), self.assertRaises(ValueError):
                    select(devices, runtimes, focus)

    def test_truthy_or_missing_availability_never_replaces_exact_booleans(self):
        for target in ("device", "runtime"):
            for value in (1, 0, "true", "false", None, [], {}):
                devices, runtimes = documents()
                row = devices["devices"][OLD][0] if target == "device" else runtimes["runtimes"][0]
                row["isAvailable"] = value
                with self.subTest(target=target, value=value), self.assertRaises(ValueError):
                    select(devices, runtimes, adaptive.FOCUSES[0])
            devices, runtimes = documents()
            row = devices["devices"][OLD][0] if target == "device" else runtimes["runtimes"][0]
            del row["isAvailable"]
            with self.assertRaises(ValueError):
                select(devices, runtimes, adaptive.FOCUSES[0])

    def test_explicit_device_cannot_fall_back_when_absent_wrong_band_or_unavailable(self):
        devices, runtimes = documents()
        for udid in (NEW_ID, "00000000-0000-4000-8000-000000000099"):
            with self.subTest(udid=udid), self.assertRaises(ValueError):
                select(devices, runtimes, adaptive.FOCUSES[0], udid=udid)
        devices["devices"][OLD][0]["isAvailable"] = False
        with self.assertRaises(ValueError):
            select(devices, runtimes, adaptive.FOCUSES[0], udid=OLD_ID)

    def test_explicit_device_identity_matches_case_insensitively_without_rewriting_actual_output(self):
        devices, runtimes = documents()
        actual = "A0000000-0000-4000-8000-000000000001"
        devices["devices"][OLD][0]["udid"] = actual
        result = select(devices, runtimes, adaptive.FOCUSES[0], udid=actual.lower())
        self.assertEqual(actual, result["udid"])
        self.assertTrue(adaptive.validate_selected(result, adaptive.FOCUSES[0], udid=actual.lower()))

    def test_latest_selection_is_numeric_within_each_band_and_explicit_older_identity_still_wins(self):
        for focus, version, identifier, build in (
            (adaptive.FOCUSES[0], "18.10", PREFIX + "iOS-18-10", "22H77"),
            (adaptive.FOCUSES[1], "26.10", PREFIX + "iOS-26-10", "23H77"),
        ):
            devices, runtimes = documents()
            original = OLD if focus == adaptive.FOCUSES[0] else NEW
            original_id = devices["devices"][original][0]["udid"]
            added_id = "00000000-0000-4000-8000-000000000003"
            added = copy.deepcopy(devices["devices"][original][0])
            added.update(udid=added_id, state="Shutdown")
            devices["devices"][original][0]["state"] = "Booted"
            devices["devices"][identifier] = [added]
            runtimes["runtimes"].append({"identifier": identifier, "version": version,
                "buildversion": build, "isAvailable": True})
            with self.subTest(focus=focus):
                self.assertEqual(added_id, select(devices, runtimes, focus)["udid"])
                self.assertEqual(original_id, select(devices, runtimes, focus, udid=original_id)["udid"])
                runtimes["runtimes"].reverse()
                devices["devices"] = dict(reversed(list(devices["devices"].items())))
                self.assertEqual(added_id, select(devices, runtimes, focus)["udid"])

    def test_only_iphones_on_matching_ios_runtime_can_be_selected(self):
        for kind in ("iPad-Air", "Apple-TV-1080p", "iPhoneish-16", "iPhone", "iPhone--16"):
            devices, runtimes = documents()
            devices["devices"][OLD][0]["deviceTypeIdentifier"] = TYPE + kind
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                select(devices, runtimes, adaptive.FOCUSES[0])
        devices, runtimes = documents()
        rows = devices["devices"].pop(OLD)
        devices["devices"][PREFIX + "tvOS-18-6"] = rows
        runtimes["runtimes"][0]["identifier"] = PREFIX + "tvOS-18-6"
        with self.assertRaises(ValueError):
            select(devices, runtimes, adaptive.FOCUSES[0])

    def test_device_group_without_its_actual_runtime_and_partial_inventory_roots_refuse(self):
        devices, runtimes = documents()
        runtimes["runtimes"] = runtimes["runtimes"][1:]
        with self.assertRaisesRegex(ValueError, "Every device group"):
            select(devices, runtimes, adaptive.FOCUSES[0])
        for device_doc, runtime_doc in (({}, documents()[1]), ({"devices": []}, documents()[1]),
                                       (documents()[0], {}), (documents()[0], {"runtimes": {}}),
                                       ({"devices": {}, "selected": {}}, documents()[1])):
            with self.subTest(device_doc=device_doc), self.assertRaises(ValueError):
                select(device_doc, runtime_doc, adaptive.FOCUSES[0])

    def test_duplicate_runtime_or_case_aliased_device_identity_refuses_without_arbitrary_choice(self):
        devices, runtimes = documents()
        runtimes["runtimes"].append(copy.deepcopy(runtimes["runtimes"][0]))
        with self.assertRaises(ValueError):
            select(devices, runtimes, adaptive.FOCUSES[0])
        devices, runtimes = documents()
        devices["devices"][OLD][0]["udid"] = "A0000000-0000-4000-8000-000000000001"
        duplicate = copy.deepcopy(devices["devices"][OLD][0]); duplicate["udid"] = duplicate["udid"].lower()
        devices["devices"][NEW].append(duplicate)
        with self.assertRaises(ValueError):
            select(devices, runtimes, adaptive.FOCUSES[0])

    def test_malformed_versions_nonpositive_overflow_case_or_build_never_become_an_os_branch(self):
        for key, value in (("version", "0.0"), ("version", "018.6"), ("version", "18.06"),
                           ("version", "18.6 "), ("version", "18.6-invalid"), ("version", "18.6.0.1"),
                           ("version", "2147483648.0"), ("version", True), ("version", None),
                           ("buildversion", None), ("buildversion", ""), ("buildversion", "23F77/private"),
                           ("buildversion", 23), ("identifier", PREFIX + "ios-18-6"),
                           ("identifier", PREFIX + "iOS-018-6"), ("identifier", PREFIX + "iOS18-6")):
            devices, runtimes = documents()
            row = runtimes["runtimes"][0]
            if key == "identifier":
                devices["devices"][value] = devices["devices"].pop(OLD)
            row[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                select(devices, runtimes, adaptive.FOCUSES[0])

    def test_identifier_major_minor_and_full_patch_prefix_mismatches_are_refused(self):
        for identifier, version in ((OLD, "26.6"), (OLD, "18.5"),
                                    (PREFIX + "iOS-18-6-1", "18.6"),
                                    (PREFIX + "iOS-18-6-1", "18.6.2")):
            devices, runtimes = documents()
            devices["devices"][identifier] = devices["devices"].pop(OLD)
            runtimes["runtimes"][0].update(identifier=identifier, version=version)
            with self.subTest(identifier=identifier, version=version), self.assertRaises(ValueError):
                select(devices, runtimes, adaptive.FOCUSES[0])

    def test_unknown_focus_empty_bad_or_zero_explicit_udid_is_not_an_automatic_selection(self):
        devices, runtimes = documents()
        for focus in (None, "", [], True, "ui-native-popover-phone-portrait", "ui-native-adaptive-unreviewed"):
            with self.subTest(focus=focus), self.assertRaises(ValueError):
                select(devices, runtimes, focus)
        for udid in ("", "booted", [], 1, "00000000-0000-0000-0000-000000000000"):
            with self.subTest(udid=udid), self.assertRaises(ValueError):
                select(devices, runtimes, adaptive.FOCUSES[0], udid=udid)

    def test_duplicate_json_fields_invalid_utf8_trailing_data_and_nonstandard_constants_refuse(self):
        good_devices, good_runtimes = map(json.dumps, documents())
        malformed = ('{"devices":{},"devices":{}}', good_devices.replace('"isAvailable": true', '"isAvailable": true,"isAvailable": true', 1),
                     good_devices + "\n{}", good_devices + " warning", b"\xff", "{", "[]", "null",
                     good_devices.replace('"isAvailable": true', '"isAvailable": NaN', 1))
        for payload in malformed:
            with self.subTest(payload=str(payload)[:50]), self.assertRaises(ValueError):
                adaptive.select_iphone_json(payload, good_runtimes, adaptive.FOCUSES[0])
        with self.assertRaises(ValueError):
            adaptive.select_iphone_json(good_devices, '{"runtimes":[],"runtimes":[]}', adaptive.FOCUSES[0])

    def test_raw_inventory_and_row_budgets_nonordinary_records_and_device_states_are_bounded(self):
        devices, runtimes = documents()
        for payload in (b"", bytearray(json.dumps(devices).encode()), {},
                        b" " * (adaptive.MAX_INVENTORY_BYTES + 1)):
            with self.subTest(kind=type(payload).__name__), self.assertRaises(ValueError):
                adaptive.select_iphone_json(payload, json.dumps(runtimes), adaptive.FOCUSES[0])
        for role in ("runtime", "device"):
            for row in (None, [], "record"):
                devices, runtimes = documents()
                if role == "runtime": runtimes["runtimes"][0] = row
                else: devices["devices"][OLD][0] = row
                with self.subTest(role=role, row=row), self.assertRaises(ValueError):
                    select(devices, runtimes, adaptive.FOCUSES[0])
        devices, runtimes = documents(); runtimes["runtimes"] *= adaptive.MAX_RUNTIMES + 1
        with self.assertRaises(ValueError): select(devices, runtimes, adaptive.FOCUSES[0])
        devices, runtimes = documents(); devices["devices"][OLD] *= adaptive.MAX_DEVICES + 1
        with self.assertRaises(ValueError): select(devices, runtimes, adaptive.FOCUSES[0])
        for state in ("Booting", "Creating", None, True, [], {}):
            devices, runtimes = documents(); devices["devices"][OLD][0]["state"] = state
            with self.subTest(state=state), self.assertRaises(ValueError):
                select(devices, runtimes, adaptive.FOCUSES[0])

    def test_selection_is_deterministic_from_complete_inventory_order_and_does_not_prefer_boot_state(self):
        devices, runtimes = documents()
        first = select(devices, runtimes, adaptive.FOCUSES[1])
        devices["devices"][OLD][0]["state"] = "Booted"
        runtimes["runtimes"].reverse()
        devices["devices"] = dict(reversed(list(devices["devices"].items())))
        self.assertEqual(first, select(devices, runtimes, adaptive.FOCUSES[1]))

    def test_default_nonadaptive_simulator_selection_keeps_its_previous_latest_runtime_semantics(self):
        devices, runtimes = documents()
        default = existing.simulator(devices, runtimes, kind="iphone")
        self.assertEqual(NEW_ID, default["udid"])
        self.assertEqual("26.4.1", default["runtime_version"])
        self.assertEqual(OLD_ID, select(devices, runtimes, adaptive.FOCUSES[0])["udid"])
        self.assertEqual(default, existing.simulator(devices, runtimes, kind="iphone"))

    def test_private_device_names_paths_and_unrelated_metadata_do_not_enter_selected_identity(self):
        devices, runtimes = documents()
        result = select(devices, runtimes, adaptive.FOCUSES[0])
        output = json.dumps(result)
        self.assertNotIn("private", output)
        self.assertNotIn("name", result)
        self.assertNotIn("bundlePath", result)
        self.assertEqual(adaptive.SIMULATOR_FIELDS, set(result))


class AdaptiveRuntimeContextControls(unittest.TestCase):
    def context(self, focus):
        devices, runtimes = documents()
        simulator = select(devices, runtimes, focus); simulator["state"] = "Booted"
        return {"schema_version": 1, "host": {"system": "Darwin", "architecture": "arm64"},
                "source_revision": "a" * 40, "source_tree_dirty": False, "simulator": simulator}

    def test_native_boundary_checks_each_fresh_context_without_rewriting_any_prior_capture(self):
        for focus in adaptive.FOCUSES:
            context = self.context(focus); before = copy.deepcopy(context)
            self.assertTrue(adaptive.validate_context(context, focus, udid=context["simulator"]["udid"]))
            self.assertEqual(before, context)
            fresh = copy.deepcopy(context); fresh["simulator"]["state"] = "Shutdown"
            with self.assertRaises(ValueError):
                adaptive.validate_context(fresh, focus, udid=context["simulator"]["udid"])
            self.assertEqual(before, context)

    def test_native_boundary_refuses_wrong_host_dirty_missing_or_nonordinary_source_and_device(self):
        focus = adaptive.FOCUSES[0]
        for key, value in (("schema_version", True), ("schema_version", 2), ("source_revision", "unknown"),
                           ("source_revision", None), ("source_tree_dirty", True), ("source_tree_dirty", 0),
                           ("host", {}), ("host", {"system": "Linux", "architecture": "arm64"}),
                           ("host", {"system": "Darwin", "architecture": "x64"}), ("simulator", None)):
            context = self.context(focus); device = context["simulator"]["udid"]; context[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                adaptive.validate_context(context, focus, udid=device)
        context = self.context(focus)
        for device in ("booted", NEW_ID, None):
            with self.subTest(device=device), self.assertRaises(ValueError):
                adaptive.validate_context(context, focus, udid=device)

    def test_selected_identity_never_fills_missing_runtime_build_fields_or_relabels_wrong_band(self):
        focus = adaptive.FOCUSES[0]
        good = self.context(focus)["simulator"]
        for key in good:
            missing = good.copy(); del missing[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                adaptive.validate_selected(missing, focus)
        for key, value in (("runtime_build", None), ("runtime_version", "26.5"),
                           ("runtime_identifier", PREFIX + "iOS-26-5"), ("device_type", TYPE + "iPad-Air"),
                           ("udid", "booted"), ("state", "Shutdown"), ("state", None),
                           ("state", True), ("state", []), ("state", {})):
            changed = good.copy(); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                adaptive.validate_selected(changed, focus, require_booted=True)
        with self.assertRaises(ValueError): adaptive.validate_selected(good, focus, require_booted=1)
        with self.assertRaises(ValueError): adaptive.validate_selected({**good, "owned": True}, focus)


if __name__ == "__main__":
    unittest.main()
