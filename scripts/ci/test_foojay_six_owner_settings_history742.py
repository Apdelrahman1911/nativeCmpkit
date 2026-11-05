# SPDX-License-Identifier: Apache-2.0
"""NEW finite Foojay/settings-history source controls, not dependency trust or native evidence.

All six original settings fixture pins remain sealed. Seven named owner contexts
include both joint CI175 and producer190 views. Historical bytes are compared,
never executed or admitted as current. Missing/changed-doc controls use only
fresh owned SPEC+doc roots, not copied946/ROOT trees or mocked admission.
"""
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import ci_source_recovery740_742 as recovery
import android_camera_callback_native_focus as callback
import ci668_outer_source_projection as outer
import macos_share_ci668_composition as joint
import producer698_source_fixture_recovery as producer
import tooling_recovery671_source_projection as tooling
import webview_content_policy_source_projection as content

ROOT = Path(os.environ.get("FOOJAY_SETTINGS_SOURCE_REVIEW_TREE", recovery.ROOT)).resolve()
SETTINGS = "settings.gradle.kts"
DOC = "docs/testing/installed-jdk17-prerequisite.md"
SPEC = "scripts/ci/fixtures/ci-source-recovery740-742-source-inverse.json"
OLD_SETTINGS_SHA256 = "773bee85a4fba6c19262dfd1bf4eca80726b1378dcba79d526ac1a515aa60f7c"
CURRENT_SETTINGS_SHA256 = "f46255ba97080b1b117e85cfc563d957e30d8f9ff2ff7c327fffd6c59d286bc9"
DOC_SHA256 = "7be847de00c744b0174d65090b62e6769309cc2eafa579f17794cdf92eea2959"
OLD_SETTINGS = b'// Modified for nativeCmpkit migration (2026-10-24); legacy project paths preserve source compatibility.\nrootProject.name = "NativeCmpKit"\n\npluginManagement {\n    includeBuild("convention-plugins")\n    repositories {\n        google {\n            mavenContent {\n                releasesOnly()\n            }\n        }\n        mavenCentral()\n        gradlePluginPortal()\n    }\n}\n\ndependencyResolutionManagement {\n    @Suppress("UnstableApiUsage")\n    repositories {\n        google()\n        mavenCentral()\n    }\n}\n\nplugins {\n    id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"\n}\n\ninclude(\n    // Artifact modules\n    ":calf-core",\n    ":calf-ui",\n    ":calf-webview",\n    ":calf-cupertino-icons",\n    ":calf-navigation",\n    ":calf-io",\n    ":calf-file-picker",\n    ":calf-file-picker-coil",\n    ":calf-permissions",\n    ":calf-permissions:core",\n    ":calf-permissions:camera",\n    ":calf-permissions:gallery",\n    ":calf-permissions:location",\n    ":calf-permissions:background-location",\n    ":calf-permissions:bluetooth",\n    ":calf-permissions:contacts",\n    ":calf-permissions:calendar",\n    ":calf-permissions:notifications",\n    ":calf-permissions:wifi",\n    ":calf-permissions:microphone",\n    ":calf-geo",\n    ":calf-maps",\n    ":calf-camera-picker",\n    ":calf-share",\n    // Sample modules\n    ":sample:android",\n    ":sample:desktop",\n    ":sample:web-js",\n    ":sample:web-wasm",\n    ":sample:common",\n)\n\n// Rename projects to keep published artifact names unchanged\nproject(":calf-permissions:core").name = "calf-permissions-core"\nproject(":calf-permissions:camera").name = "calf-permissions-camera"\nproject(":calf-permissions:gallery").name = "calf-permissions-gallery"\nproject(":calf-permissions:location").name = "calf-permissions-location"\nproject(":calf-permissions:background-location").name = "calf-permissions-background-location"\nproject(":calf-permissions:bluetooth").name = "calf-permissions-bluetooth"\nproject(":calf-permissions:contacts").name = "calf-permissions-contacts"\nproject(":calf-permissions:calendar").name = "calf-permissions-calendar"\nproject(":calf-permissions:notifications").name = "calf-permissions-notifications"\nproject(":calf-permissions:wifi").name = "calf-permissions-wifi"\nproject(":calf-permissions:microphone").name = "calf-permissions-microphone"\n\nenableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")\nenableFeaturePreview("STABLE_CONFIGURATION_CACHE")\n'
CURRENT_SETTINGS = b'// Modified for nativeCmpkit migration (2026-10-24); legacy project paths preserve source compatibility.\nrootProject.name = "NativeCmpKit"\n\npluginManagement {\n    includeBuild("convention-plugins")\n    repositories {\n        google {\n            mavenContent {\n                releasesOnly()\n            }\n        }\n        mavenCentral()\n        gradlePluginPortal()\n    }\n}\n\ndependencyResolutionManagement {\n    @Suppress("UnstableApiUsage")\n    repositories {\n        google()\n        mavenCentral()\n    }\n}\n\n// Verification requires an explicitly installed JDK17, not a remote JVM resolver.\n// See docs/testing/installed-jdk17-prerequisite.md.\n\ninclude(\n    // Artifact modules\n    ":calf-core",\n    ":calf-ui",\n    ":calf-webview",\n    ":calf-cupertino-icons",\n    ":calf-navigation",\n    ":calf-io",\n    ":calf-file-picker",\n    ":calf-file-picker-coil",\n    ":calf-permissions",\n    ":calf-permissions:core",\n    ":calf-permissions:camera",\n    ":calf-permissions:gallery",\n    ":calf-permissions:location",\n    ":calf-permissions:background-location",\n    ":calf-permissions:bluetooth",\n    ":calf-permissions:contacts",\n    ":calf-permissions:calendar",\n    ":calf-permissions:notifications",\n    ":calf-permissions:wifi",\n    ":calf-permissions:microphone",\n    ":calf-geo",\n    ":calf-maps",\n    ":calf-camera-picker",\n    ":calf-share",\n    // Sample modules\n    ":sample:android",\n    ":sample:desktop",\n    ":sample:web-js",\n    ":sample:web-wasm",\n    ":sample:common",\n)\n\n// Rename projects to keep published artifact names unchanged\nproject(":calf-permissions:core").name = "calf-permissions-core"\nproject(":calf-permissions:camera").name = "calf-permissions-camera"\nproject(":calf-permissions:gallery").name = "calf-permissions-gallery"\nproject(":calf-permissions:location").name = "calf-permissions-location"\nproject(":calf-permissions:background-location").name = "calf-permissions-background-location"\nproject(":calf-permissions:bluetooth").name = "calf-permissions-bluetooth"\nproject(":calf-permissions:contacts").name = "calf-permissions-contacts"\nproject(":calf-permissions:calendar").name = "calf-permissions-calendar"\nproject(":calf-permissions:notifications").name = "calf-permissions-notifications"\nproject(":calf-permissions:wifi").name = "calf-permissions-wifi"\nproject(":calf-permissions:microphone").name = "calf-permissions-microphone"\n\nenableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")\nenableFeaturePreview("STABLE_CONFIGURATION_CACHE")\n'
BEFORE_FRAGMENT = b'plugins {\n    id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"\n}\n\n'
AFTER_FRAGMENT = b'// Verification requires an explicitly installed JDK17, not a remote JVM resolver.\n// See docs/testing/installed-jdk17-prerequisite.md.\n\n'
HISTORICAL_FIXTURES = (('android-camera-callback672-source-inverse.json', 32261, '1c14d6fcb7dc49716de3688169c9280fde51f62564d1593a6a95707f85f19f7a', [('immutable_inputs', 'settings.gradle.kts')]), ('ci668-outer-source-inverse.json', 91426, 'bbfdb2454182ce8c1fc90e793c3552e49f317b35437b61fcd3e8743b86f9d86e', [('unchanged_inputs', 'settings.gradle.kts')]), ('macos-share-ci668-composition.json', 518906, '06d04d038b06c00e5aafb9b7defdf39ae069f3df305e4dbc84198bc8ed178a24', [('raw_inputs', 'settings.gradle.kts'), ('predecessor_inputs', 'final_ci175', 'settings.gradle.kts'), ('predecessor_inputs', 'producer676_raw190', 'settings.gradle.kts')]), ('producer698-source-fixture-recovery.json', 58981, '64538883def9615a5c92060dcdc121404165b23278666c947e016b8eb67145d8', [('original_ci668_inputs', 'settings.gradle.kts')]), ('tooling-recovery671-source-inverse.json', 114673, '9def6c416e199237600bdcdc2a16a3fd22dc2158796e1116f999b8681c96a110', [('unchanged_inputs', 'settings.gradle.kts')]), ('webview-content-policy-routing-source-inverse.json', 57992, 'c44400087570740d3248704c2165c3222229f2c05ff1a2a3840dbda9aa04b916', [('unchanged_inputs', 'settings.gradle.kts')]))


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def owner_contexts():
    # Existing public raw calls receive the original RAW argument. In particular,
    # do not pre-peel settings before a nested joint/tooling current admission.
    return (
        ("callback672", callback.current_source_before_callback672, callback.peel_callback672_for_history),
        ("CI668", outer.current_source_before_ci668, outer.peel_ci668_for_history),
        ("joint-CI175", lambda relative, payload: joint.current_source_in_view(relative, payload, joint.CI_VIEW, ROOT),
                       lambda relative, payload: joint.peel_for_history(relative, payload, joint.CI_VIEW, ROOT)),
        ("joint-producer190", lambda relative, payload: joint.current_source_in_view(relative, payload, joint.PRODUCER_VIEW, ROOT),
                             lambda relative, payload: joint.peel_for_history(relative, payload, joint.PRODUCER_VIEW, ROOT)),
        ("producer698", producer.current_source_before_producer698, producer.peel_producer698_for_history),
        ("tooling671", tooling.current_source_before_tooling671, tooling.peel_tooling671_for_history),
        ("WebView-content", content.current_source_before_content_policy, content.peel_content_policy_for_history),
    )


class FoojaySixOwnerSettingsHistoryControls(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack(); self.addCleanup(self.guards.close)
        def forbidden(*args, **kwargs):
            raise AssertionError("Settings source-history controls cannot perform host/native/process/network operations")
        for module, names in ((subprocess, ("Popen", "run", "call", "check_call", "check_output")),
                              (socket, ("socket", "create_connection", "getaddrinfo")),
                              (os, ("system", "kill", "killpg"))):
            for name in names:
                self.guards.enter_context(patch.object(module, name, forbidden))
        self.assertEqual(ROOT, Path(recovery.ROOT).resolve())
        for owner in (callback, outer, joint, producer, tooling, content):
            self.assertEqual(ROOT, Path(owner.ROOT).resolve(), "Real owner modules must share the declared current source checkout")

    def test_six_original_settings_owners_and_two_named_joint_views_preserve_pins_and_roundtrip_current(self):
        self.assertEqual((2423, OLD_SETTINGS_SHA256), (len(OLD_SETTINGS), digest(OLD_SETTINGS)))
        self.assertEqual((2472, CURRENT_SETTINGS_SHA256), (len(CURRENT_SETTINGS), digest(CURRENT_SETTINGS)))
        self.assertEqual(CURRENT_SETTINGS, (ROOT / SETTINGS).read_bytes())
        self.assertEqual((2744, DOC_SHA256), (len((ROOT / DOC).read_bytes()), digest((ROOT / DOC).read_bytes())))
        for name, length, expected_sha, paths in HISTORICAL_FIXTURES:
            with self.subTest(original_manifest=name):
                raw = (ROOT / "scripts/ci/fixtures" / name).read_bytes()
                self.assertEqual((length, expected_sha), (len(raw), digest(raw)))
                document = json.loads(raw)
                for path in paths:
                    row = document
                    for key in path: row = row[key]
                    if isinstance(row, dict): self.assertEqual({"bytes": 2423, "sha256": OLD_SETTINGS_SHA256}, row)
                    else: self.assertEqual(OLD_SETTINGS_SHA256, row)
        self.assertEqual(6, len(HISTORICAL_FIXTURES))
        contexts = owner_contexts(); self.assertEqual(7, len(contexts))
        for name, current, peel in contexts:
            with self.subTest(current_owner=name):
                self.assertEqual(OLD_SETTINGS, current(SETTINGS, CURRENT_SETTINGS))
            with self.subTest(history_owner=name):
                self.assertEqual(OLD_SETTINGS, peel(SETTINGS, CURRENT_SETTINGS))
                # A comparison ancestor may remain data; it is not readmitted current.
                self.assertEqual(OLD_SETTINGS, peel(SETTINGS, OLD_SETTINGS))
        self.assertEqual(1, OLD_SETTINGS.count(BEFORE_FRAGMENT))
        self.assertEqual(1, CURRENT_SETTINGS.count(AFTER_FRAGMENT))
        self.assertEqual(CURRENT_SETTINGS, OLD_SETTINGS.replace(BEFORE_FRAGMENT, AFTER_FRAGMENT, 1))
        self.assertEqual(OLD_SETTINGS, CURRENT_SETTINGS.replace(AFTER_FRAGMENT, BEFORE_FRAGMENT, 1))

    def test_all_six_public_current_owners_refuse_old_settings_even_when_root_contains_verified_after_bytes(self):
        self.assertEqual(CURRENT_SETTINGS, (ROOT / SETTINGS).read_bytes())
        for name, current, _ in owner_contexts():
            with self.subTest(raw_owner=name), self.assertRaises(ValueError):
                current(SETTINGS, OLD_SETTINGS)

    def test_core_settings_complete_bytes_type_identity_and_finite_unlisted_history_do_not_widen_admission(self):
        modified = CURRENT_SETTINGS.replace(b"NativeCmpKit", b"NativeCmpkit", 1)
        self.assertEqual(len(CURRENT_SETTINGS), len(modified)); self.assertNotEqual(CURRENT_SETTINGS, modified)
        displaced = CURRENT_SETTINGS.replace(AFTER_FRAGMENT, b"", 1) + AFTER_FRAGMENT
        self.assertEqual(len(CURRENT_SETTINGS), len(displaced)); self.assertNotEqual(CURRENT_SETTINGS, displaced)
        for label, payload in (("old", OLD_SETTINGS), ("same-size-drift", modified),
                               ("partial", CURRENT_SETTINGS[:-1]), ("append", CURRENT_SETTINGS + b"\n"),
                               ("duplicate-fragment", CURRENT_SETTINGS.replace(AFTER_FRAGMENT, AFTER_FRAGMENT * 2, 1)),
                               ("displaced-fragment", displaced), ("bytearray", bytearray(CURRENT_SETTINGS))):
            with self.subTest(refusal=label), self.assertRaises(ValueError):
                recovery.current_source_before_recovery(SETTINGS, payload, ROOT)
        for relative in (None, [SETTINGS]):
            with self.subTest(foreign_identity=relative), self.assertRaises(ValueError):
                recovery.current_source_before_recovery(relative, CURRENT_SETTINGS, ROOT)
        for payload in (OLD_SETTINGS, modified, CURRENT_SETTINGS[:-1]):
            self.assertEqual(payload, recovery.peel_recovery_for_history(SETTINGS, payload, ROOT))
        foreign = "scripts/ci/unlisted-foojay-settings-history-data.txt"
        self.assertEqual(CURRENT_SETTINGS, recovery.peel_recovery_for_history(foreign, CURRENT_SETTINGS, ROOT))
        self.assertEqual(CURRENT_SETTINGS, recovery.current_source_before_recovery(foreign, CURRENT_SETTINGS, ROOT))

    def test_installed_jdk17_doc_presence_full_bytes_and_ordinary_identity_are_fresh_required_dependencies(self):
        spec_payload = (ROOT / SPEC).read_bytes()
        doc_payload = (ROOT / DOC).read_bytes()
        self.assertEqual((2744, DOC_SHA256), (len(doc_payload), digest(doc_payload)))
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-foojay-doc-context-") as temporary:
            root = Path(temporary)
            spec_path, doc_path = root / SPEC, root / DOC
            for path, payload in ((spec_path, spec_payload), (doc_path, doc_payload)):
                path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                path.write_bytes(payload); path.chmod(0o644)
            # Actual admission first proves SPEC+doc suffice; later refusals therefore
            # cannot be blamed on absent946 unrelated source files or mocked gates.
            self.assertEqual(OLD_SETTINGS, recovery.current_source_before_recovery(SETTINGS, CURRENT_SETTINGS, root))
            doc_path.unlink()
            with self.assertRaises((ValueError, OSError)):
                recovery.current_source_before_recovery(SETTINGS, CURRENT_SETTINGS, root)
            for label, payload in (("same-size-doc-drift", bytes([doc_payload[0] ^ 1]) + doc_payload[1:]),
                                   ("partial-doc", doc_payload[:-1]), ("append-doc", doc_payload + b"\n")):
                doc_path.write_bytes(payload); doc_path.chmod(0o644)
                with self.subTest(doc_refusal=label), self.assertRaises(ValueError):
                    recovery.current_source_before_recovery(SETTINGS, CURRENT_SETTINGS, root)
            doc_path.unlink()
            held = root / "held-exact-doc"; held.write_bytes(doc_payload); held.chmod(0o644)
            doc_path.symlink_to(held)
            with self.assertRaises((ValueError, OSError)):
                recovery.current_source_before_recovery(SETTINGS, CURRENT_SETTINGS, root)
            doc_path.unlink(); os.link(held, doc_path)
            with self.assertRaises((ValueError, OSError)):
                recovery.current_source_before_recovery(SETTINGS, CURRENT_SETTINGS, root)
            doc_path.unlink(); doc_path.write_bytes(doc_payload); doc_path.chmod(0o644)
            self.assertEqual(OLD_SETTINGS, recovery.current_source_before_recovery(SETTINGS, CURRENT_SETTINGS, root))
