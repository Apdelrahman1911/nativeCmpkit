# SPDX-License-Identifier: Apache-2.0
"""Four explicit predecessor views above adopted producer676 + Cookie609 + Share607.

Current admission is a complete raw-input check before any named view. Ancestor
arithmetic never executes restored code, revives JNI, changes AppKit readiness,
certifies a native result, or searches for an arbitrary historical layer.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import os
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
OWNER = "scripts/ci/macos_share_ci668_composition.py"
SPEC = "scripts/ci/fixtures/macos-share-ci668-composition.json"
SPEC_SHA256 = "948725f58171aa6571439ae15f16977c19c090a6664532377ecbcdfc42abd020"
CI_VIEW = "final_ci175"
SHARE_VIEW = "share607"
COOKIE_VIEW = "cookie609_raw40"
PRODUCER_VIEW = "producer676_raw190"
VIEWS = frozenset({CI_VIEW, COOKIE_VIEW, SHARE_VIEW, PRODUCER_VIEW})
COOKIE_OWNER = "scripts/ci/cookie_ci668_outer_source_projection.py"
COOKIE_OWNER_ANCESTOR_SHA256 = "974efdeed8185ddcdf281ae0236b51e31175dec0b89626e46e06a2c1c53b702b"
COOKIE_CI_OWNER_SHA256 = "48d545009b317fed2b77cf3f39976087bf3f00886866d1e0940ec56df1ee0860"
COOKIE_SPEC = "scripts/ci/fixtures/cookie-ci668-outer-source-inverse.json"
COOKIE_SPEC_SHA256 = "9ee4fec400669dfc4fd772989873527ae223d7fa344c454550cc4dfebc97410b"
COOKIE609_SPEC_SHA256 = "513d2c6e55cf67c5aa0a8aacfb73f799f4acc509c9b03523a2b43c7f6d0f1efb"
NEW_COOKIE_CONTROL = "scripts/ci/tests/test_cookie_ci668_outer_scope609.py"
OWNING_COOKIE_CONTROL = "scripts/ci/tests/test_cookie_common_jdk_scope681.py"
CALLBACK_INIT = "scripts/ci/fresh-tests.init.gradle.kts"
COOKIE_COMMON_SPEC = "scripts/ci/fixtures/cookie-common-jdk-source-inverse.json"
COOKIE_COMMON_SPEC_SHA256 = "9445b6e7835fe81bec5b22f033f8e1c207dd639ff4d6b75df47ee51078e38a90"
CALLBACK_SPEC = "scripts/ci/fixtures/android-camera-callback672-source-inverse.json"
CALLBACK_SPEC_SHA256 = "1c14d6fcb7dc49716de3688169c9280fde51f62564d1593a6a95707f85f19f7a"
COOKIE40_MAP_SHA256 = "3729bb770a2935e021c2a62f48b3fbdbb6ab3dc7c25b34211122fcc6d2812c9e"
NONCURRENT_SIBLING_BINDING_SHA256 = "f499625345a5ea875a4a8a6a8acb0d51ed9d2377f1e13778dc1a4149889169b8"
CI_SPEC = "scripts/ci/fixtures/ci668-outer-source-inverse.json"
CI_SPEC_SHA256 = "bbfdb2454182ce8c1fc90e793c3552e49f317b35437b61fcd3e8743b86f9d86e"
CI_OWNER = "scripts/ci/ci668_outer_source_projection.py"
CI_OWNER_ANCESTOR_SHA256 = "57ea22a07713ee542a14f8d57338767f57e6cab4e2133a14b8096f9269e18337"
PRODUCER_OWNER = "scripts/ci/producer698_source_fixture_recovery.py"
PRODUCER_OWNER_ANCESTOR_SHA256 = "d6439ebba4db1dcaacbac6d54130d0398c88d5cd0c475cfc205f8744eeb47089"
PRODUCER_SPEC = "scripts/ci/fixtures/producer698-source-fixture-recovery.json"
PRODUCER_SPEC_SHA256 = "64538883def9615a5c92060dcdc121404165b23278666c947e016b8eb67145d8"
PRODUCER190_MAP_SHA256 = "5b5fcc6b2e4325cc5036b33a35d0aff7f768a67905140c6bfdb26a76cf8a1ebf"
PRODUCER_CONTROL = "scripts/ci/test_producer698_batch_source_fixture_recovery.py"
OFFLINE = "scripts/ci/offline_tooling_reuse.py"
UI_SPLIT_CONTROL = "scripts/ci/test_ios_ui_split664_native_routing.py"
CI_CONTROL = "scripts/ci/test_ci668_outer_source_projection.py"
SHARE_SPEC = "scripts/ci/fixtures/macos-share-appkit-only-source-inverse.json"
SHARE_SPEC_SHA256 = "fb8de8c2c61e2263d1d1221fa168877d077f251043d91b5ba05df4a40d6362f7"
SHARE_OWNER = "scripts/ci/macos_share_appkit_only_source_projection.py"
SHARE_OWNER_ANCESTOR_SHA256 = "3bf246246e1734d8670672d5fe05c471298feba8209b5e14c0fa33e4908e7182"
OBSERVATION_SPEC = "scripts/ci/fixtures/macos-share-key-wait-observation-source-inverse.json"
OBSERVATION_SPEC_SHA256 = "dd5872cb1a7e23beb064dfcad7ef10544e0b547d734498b564dd73ae5ee3a0e6"
WORKFLOW = ".github/workflows/gradle.yml"
LIBRARY = "scripts/ci/library_tests.py"
NEW_CONTROL = "scripts/ci/test_macos_share_ci668_composition.py"
NEW_DOC = "docs/testing/macos-share-ci668-composition.md"
BUDGET707_CONTROL = "scripts/ci/test_offline_tooling_scope_observation707.py"
FAILURE711_HELPER = "scripts/ci/offline_tooling_failure_evidence711.py"
FAILURE711_CONTROL = "scripts/ci/test_offline_tooling_failure_evidence711.py"
FAILURE711_BINDING_SHA256 = "572bfaf2348bc3431f029e580f6d97eadfab77ad1c43c0e24bcfd15fc9f1969b"
FAILURE711_CURRENT_SHA256 = "58f08f3fcda1e490743a8d28f7881473a28f5fcd1a3127abfffce35d6e7b2cb5"
FAILURE711_ADDITION_ENDPOINTS = {
    FAILURE711_HELPER: {"sha256": "3bcb54e114807b6ffd4c2337367407354412312b1adecaba356ad57cdb5ccd28", "bytes": 3590},
    FAILURE711_CONTROL: {"sha256": "c82a70f4890b4a7d2bddfa60ef2273dfb4a41c9005871234282363e745fed14f", "bytes": 15313},
}
ADDED_INPUTS = frozenset({NEW_CONTROL, NEW_DOC, BUDGET707_CONTROL,
                          FAILURE711_HELPER, FAILURE711_CONTROL})
BOUND_FRAGMENT_COUNTS = {'.github/workflows/gradle.yml': 1,
 'scripts/ci/ci668_outer_source_projection.py': 7,
 'scripts/ci/cookie_ci668_outer_source_projection.py': 8,
 'scripts/ci/fixtures/cookie-ci668-outer-source-inverse.json': 4,
 'scripts/ci/macos_share_appkit_only_source_projection.py': 5,
 'scripts/ci/offline_tooling_provenance.py': 1,
 'scripts/ci/offline_tooling_reuse.py': 4,
 'scripts/ci/producer698_source_fixture_recovery.py': 6,
 'scripts/ci/test_ci668_outer_source_projection.py': 2,
 'scripts/ci/test_macos_share_appkit_only_route607.py': 1,
 'scripts/ci/test_offline_tooling_failure_inventory.py': 3,
 'scripts/ci/test_producer698_batch_source_fixture_recovery.py': 4,
 'scripts/ci/tests/test_cookie_ci668_outer_scope609.py': 2}
HISTORICAL_DERIVATIVE_FRAGMENT_COUNTS = {'scripts/ci/ci668_outer_source_projection.py': 7,
 'scripts/ci/cookie_ci668_outer_source_projection.py': 8,
 'scripts/ci/fixtures/cookie-ci668-outer-source-inverse.json': 4,
 'scripts/ci/macos_share_appkit_only_source_projection.py': 5,
 'scripts/ci/producer698_source_fixture_recovery.py': 6,
 'scripts/ci/test_ci668_outer_source_projection.py': 2,
 'scripts/ci/test_macos_share_appkit_only_route607.py': 1,
 'scripts/ci/test_producer698_batch_source_fixture_recovery.py': 4,
 'scripts/ci/tests/test_cookie_ci668_outer_scope609.py': 2}
BUDGET707_FRAGMENT_COUNTS = {'.github/workflows/gradle.yml': 1,
 'scripts/ci/offline_tooling_provenance.py': 1,
 'scripts/ci/offline_tooling_reuse.py': 4}
BUDGET707_BINDING_SHA256 = {'.github/workflows/gradle.yml': '561d011ab9cbd29d57504167aef3433a562ba0a63f2078024112b198aa38a4f9',
 'scripts/ci/offline_tooling_provenance.py': 'd52df568f2e8effd35a83047875756eecd17e5ae3ff4d0e7b43f9f486e143e20',
 'scripts/ci/offline_tooling_reuse.py': '699f0e797495b5fd0d742ca5096359ae63e41b001cf70f4de744091e57e5249c'}
BUDGET707_CURRENT_SHA256 = {'.github/workflows/gradle.yml': '7c9af733acf8ac35aad36012870a9ba2895a36646d04743dbf709b911d6d1566',
 'scripts/ci/offline_tooling_provenance.py': 'dc4811e34272e4b67e1abfb82b9cf0bc9d79a7bf01a9cfad205eb0f007b3f63a',
 'scripts/ci/offline_tooling_reuse.py': '6a4c6509ce1c205f590456789c63fe99b475dc0e83242e751aef08e274fa087c'}
MAX_SOURCE = 4 * 1024 * 1024
MAX_SPEC = 512 * 1024
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
SCOPE = 'Exact joint282 raw source, exact711 diagnostic transition then unchanged707 prelude then CI175/Cookie40/Share36/producer190 named ancestry; ZERO native/compiler/producer-reuse/consumer/security/issue/release acceptance'
CURRENT_REFUSAL = "An old or unknown image cannot replace exact current final CI668 source"
PREDECESSOR_CUSTODY = {'CI175_map_sha256': '281ba98ae69e597f41f1c417c142878791c0931bce7542b280ba0bd8315cfe4e',
 'CI200_import_map_sha256': 'dcefd6b81ea2d7e1c51819df4fe9b1977aae3c5655f1031e199d3bc9bca0f212',
 'JNI_execution_revived': False,
 'accepted_joint264_FIRST13_execution_seal_sha256': '71cd1b6abae77f2f71a51a0f4836ddab866d2c988db73e8d57030eb3a0261d29',
 'accepted_joint264_source_map_sha256': '6bbb65c800811d36703d018381aa3bd15178348a6c5709cb26fabc9fa35f4dfa',
 'budget707_exact_source_manifest_sha256': '64ece24b01b68bb81f9b7297681a2b0b1a8848b6bb0396a4baf97bf26a8e9f6c',
 'budget707_new_control_sha256': '128e215ccbe2077b8089930fea4f0bb3f989208f645f1f047d079b8b15d7d496',
 'budget707_original_context_disposal_order_preserved': True,
 'budget707_provisional339_never_adopted': True,
 'budget707_runtime_or_reuse_accepted': False,
 'budget707_source_proposal_adopted': False,
 'budget707_three_exact_transitions_six_fragments': True,
 'cookie_successor_handoff_sha256': '44aef1039d72d7e446870304844e01aa3a4c89dbae23409ed789459097e1fec7',
 'cookie_successor_source_seal_sha256': 'fccc7141b2a10d9e8dba1cfde7c35df089d192921f2e07365ab38b4abfe6187a',
 'future_diagnostics_binding_owner': '676/610 adopted source leaves at2ee; exact new joint279 source '
                                     'proposal is not adopted or executed',
 'future_diagnostics_endpoints_adopted': True,
 'independent694610_endpoint_seal_sha256': '514bf59bceb3deb2ae49636e3124ab0f0d4a14eae42bbe241024d6f38ca4c68d',
 'inventory708_current_control_sha256': '6c9db9a3b50b03a16aafe9065221151619361ecf797cbba4a4951e317913b4cb',
 'inventory708_exact_owner_transition_sha256': 'ae172b0df72074755865399ce29e65b87a528783b106a6dad97f40357f4981b4',
 'inventory708_original190_control_sha256': 'c15d05979c26976f07e8a71e0002d0ca394b0633b8c3467cf2c8e700771ecab9',
 'joint279_source_proposal_adopted': False,
 'lead689_mode_endpoint_sha256': 'efde899174a969c7dd9a4df3d53376aed6196632c4a99f1d6a51e0e19ea74048',
 'lead_current_head': '2ee751a203f488249839873bfe6590edd73b65ea',
 'lead_current_tree': '13c1e99a619170990d34280c7c75bc3f1fc3f356',
 'lead_frozen_head': '97b3013e033ce64b6cc3d5dd3bf24bfbe405cb68',
 'lead_full_tracked34230_compact_inputs_sha256': 'b6eab2e85300e2a162b690e5bf26be7e876b0220eb5543c6d4d24dbcb0c3ec96',
 'native_cause_verified': False,
 'original_missing_terminal_receipt_retained': True,
 'original_uncaptured_console_retained': True,
 'producer676_exact_recipe_sha256': 'efaba1cd2b12de4b2abb1d6182bc52d3c57d6642dc40bc7bdabd65fd83ca238b',
 'producer676_original190_map_sha256': '5b5fcc6b2e4325cc5036b33a35d0aff7f768a67905140c6bfdb26a76cf8a1ebf',
 'producer_or_reuse_runtime_accepted': False,
 'separate607_independent_seal_sha256': 'cd53ec3177886aada78f141f0f29c237e6027f5762c194b69fe86c6aaedf8fbf',
 'separate607_packet_sha256': '32b60ee8cff7d6cea93ffd65906fa082cbfbd0b6c4ddef7628a0cc14a035970d',
 'separate609_packet_sha256': '7a1d599ee6b1d79e215fb2dea1d1802bcd49ac2373e870be908517c5248133b3',
 'standalone_share_CI_guard_not_adopted_sha256': '02e1313db3b3aa1592b5fd9f05f9c1b62c057306f5b0b6c69993f44cb823bdc5',
 'standalone_share_independent_and_joint_acceptance_granted': False,
 'standalone_share_source_map_sha256': '0e0d4d2e31755ab01313a7dda20f0094f5df810faaa50ab6dfa9c0828e7f59f2',
 'standalone_share_source_seal_sha256': '09932c1445e56fb568b00edab2b9a4016452758ef0f29c8d21968d77f6a85d7b'}
IMPORT_CLOSURE24 = {'docs/testing/cookie-common-jdk4-routing.md': '4ec0dbd2165fd140a9988d13f89b28abc5c35a6d3c01753d8e72a5af40d9d5d2', 'docs/testing/cookie-wire-acceptance.md': 'b1cb9b5c80e2bb3ea2cde574ff2a8d9fca1609ff95e43816e70f23f03d8ccc82', 'scripts/ci/android_camera_home_baseline.py': 'e710e5f1c7d048b0b32e00f2a261443f6dcbd24aa51ec1fc46bfbe27ab47e3b5', 'scripts/ci/android_device_batch_plan.py': '40d4bfda3ee2b019fead6a3e14be9df633857d12b4219d520021a2bfaac6fc60', 'scripts/ci/android_kvm_timeline.py': '488442a673d07f0a92bfffc31adcdeac3cf7de11568662fa6b6925eee7c1149b', 'scripts/ci/android_permission_demo.py': '3d15995ed7c76393cec609ee6413280e25043d72285f17302e005f0960efa381', 'scripts/ci/android_storage_compatibility_plan.py': '30e15959121e93decd9893477a584f31a9962f0d76f90fa67be643e2d6eaffa3', 'scripts/ci/android_storage_probe.py': '60543145c8f45e43187c6867f54cc70a1220d300ae849afaab998b3eaa8bd2c0', 'scripts/ci/android_webview_heap.py': '009bceca07d11686f4129a819e38c9ab1b3d1d485735e45a971864ef70e505bd', 'scripts/ci/apple_crash_diagnostics.py': 'abf2982668843acdd3a60f6d424224c7880f8d6550edcbb8b1b83a00ddb27c0e', 'scripts/ci/camera_ios_ownership_native_focus.py': '550b103e29c7716805e6665ff8f3be239def8149f096eaff3bf533b823c4f1d5', 'scripts/ci/daemon_jvm.py': 'b0a33a3340426c992d721028791bc64aa64e430022b4d609f5903d4105899d60', 'scripts/ci/desktop_media_context.py': '5e4ed80627ea61238d1645b32f8b776f7535b5df1c05cef57d94717da448c857', 'scripts/ci/desktop_security_plan.py': '0c5edc0b953d0324118e89f0a7af104656aaafd81f60bef1a14b41363b7e6f33', 'scripts/ci/ios_calendar_native_focus.py': 'a7b9e1b74a970403b00f4c349ff41b88d1ee7e71d23a93da0ab8eaf58e4dbce7', 'scripts/ci/macos_share_native_focus.py': 'd8e68383f8851b5cf4070d490e19ea04274a155cc7ee0d0dc7ec49b23ac3a4d1', 'scripts/ci/native_test_policy.py': 'a3647391cf429ec6bab833e1d4643d915ac422d46b7cde0bd5ec3474c0b76dd5', 'scripts/ci/picker_dialog_context.py': '99ae670ed09c253cdef3e630df33463e04d68e498b5bfab9bd7237ccb36f1e4e', 'scripts/ci/secure_alert_input_plan.py': '23cdbe576bcdb105944ff18a03143b5cce806704a7a4d033223a6bc85bfdae86', 'scripts/ci/simulator_appearance.py': 'c921910bcda00f46bc6ba9d4f43e2a7c9b97f2a67a3b8bf1a9a326838cec6f29', 'scripts/ci/test_daemon_jvm.py': '1a3fcbbaf17deabfd091ee3b7ade6d36d9794864f848cc18b7c7dcc0bb36901c', 'scripts/ci/test_ios_ui_application.py': 'cd1cdc299e2d8bc7a1fbd24cda60086fa13888fc2d8207ad5946a7b26e6b92ac', 'scripts/ci/test_ios_ui_related_native_focus.py': '36d395e8d564f76a446b7495532bd489f46e0cad5cb7312c7a61c99509ab8c42', 'scripts/ci/test_ios_ui_related_native_wiring.py': '8633759ebb37c23f3b6141271ef9ee7a398d5be9d3c69b9f7eb0edadbd05dde4'}


def need(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


@lru_cache(maxsize=512)
def _cached_source_path_parts(relative):
    """Only immutable successful path grammar, never filesystem/manifest custody.

    The caller rejects nonexact/empty/oversized keys before cache hashing. Invalid
    grammar raises unchanged and is not cached; concurrent misses may repeat this
    pure validation. Every file, dependency, root and payload check stays fresh.
    """
    from macos_share_appkit_only_source_projection import _path
    return _path(relative)


def _identity(relative, payload):
    need(type(relative) is str and 0 < len(relative) <= 4096,
         "unsafe-AppKit-source-identity")
    _cached_source_path_parts(relative)
    need(type(payload) is bytes and 0 < len(payload) <= MAX_SOURCE,
         "bounded-complete-share-CI-source-operands-required")


def _descriptor_source_io_supported():
    """POSIX parent descriptors are not a Windows source-admission prerequisite."""
    return (os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW") and
            os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd)


def _portable_ordinary(root, relative, maximum):
    """Bounded owned file FD plus before/after path-parent custody on every host.

    Platforms without POSIX dir_fd primitives use file descriptor identity, not a
    writable/symlink hint. This does not qualify an AppKit runtime or native host.
    """
    import macos_share_appkit_only_source_projection as source
    need(type(root) is type(Path()) and root.is_absolute() and root == root.resolve(strict=True),
         "ordinary-canonical-share-CI-source-root-required")
    need(type(maximum) is int and 0 < maximum <= MAX_SOURCE, "bounded-share-CI-source-read-required")
    parts = source._path(relative)
    parents = []
    path = root
    for component in (None, *parts[:-1]):
        if component is not None:
            path = path / component
        metadata = path.lstat()
        need(stat.S_ISDIR(metadata.st_mode) and path.absolute() == path.resolve(strict=True),
             "ordinary-unaliased-share-CI-source-parent-required")
        parents.append((path, source.directory_identity(metadata)))
    file = path / parts[-1]
    need(file.absolute() == file.resolve(strict=True) and file.resolve(strict=True).is_relative_to(root),
         "confined-unaliased-share-CI-source-file-required")
    before = file.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= maximum,
         "bounded-ordinary-unaliased-share-CI-source-file-required")
    descriptors, primary = [], None
    try:
        descriptor = os.open(file, os.O_RDONLY | getattr(os, "O_BINARY", 0))
        descriptors.append(descriptor)
        need(source._identity(before) == source._identity(os.fstat(descriptor)),
             "share-CI-source-file-replaced-before-read")
        chunks, total = [], 0
        while True:
            chunk = os.read(descriptor, min(131072, maximum + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            need(total <= maximum, "share-CI-source-read-bound-exceeded")
        payload = b"".join(chunks)
        need(source._identity(before) == source._identity(os.fstat(descriptor)) == source._identity(file.lstat()) and
             len(payload) == before.st_size and file.absolute() == file.resolve(strict=True),
             "share-CI-source-file-or-path-custody-changed-during-read")
        for parent, identity in parents:
            current = parent.lstat()
            need(stat.S_ISDIR(current.st_mode) and parent.absolute() == parent.resolve(strict=True) and
                 source.directory_identity(current) == identity,
                 "share-CI-source-parent-custody-changed-during-read")
        return payload, {"device": before.st_dev, "inode": before.st_ino, "mode": before.st_mode,
                         "size": len(payload), "mtime_ns": before.st_mtime_ns, "sha256": sha(payload)}
    except BaseException as error:
        primary = error
        raise
    finally:
        source.close_owned(descriptors, primary)


def _ordinary(root, relative, maximum=MAX_SOURCE):
    if _descriptor_source_io_supported():
        from macos_share_appkit_only_source_projection import ordinary_bytes
        return ordinary_bytes(root, relative, maximum)
    return _portable_ordinary(root, relative, maximum)


def _json(payload):
    from macos_share_appkit_only_source_projection import json_bytes
    need(type(payload) is bytes and 0 < len(payload) <= MAX_SPEC,
         "bounded-complete-share-CI-manifest-required")
    return json_bytes(payload)


def _sealed_predecessor_hashes(root, document):
    def spec(relative, expected):
        raw = _ordinary(root, relative, MAX_SPEC)[0]
        need(sha(raw) == expected, "unchanged-share-CI-predecessor-manifest-required")
        return _json(raw)
    ci = spec(CI_SPEC, CI_SPEC_SHA256)
    share = spec(SHARE_SPEC, SHARE_SPEC_SHA256)
    spec(OBSERVATION_SPEC, OBSERVATION_SPEC_SHA256)
    spec(COOKIE_SPEC, COOKIE_SPEC_SHA256)
    cookie = document["named_cookie609_manifest"]
    import json
    old_cookie_literal = (json.dumps(cookie, indent=2, sort_keys=True) + "\n").encode()
    need(sha(old_cookie_literal) == COOKIE609_SPEC_SHA256,
         "exact-named-accepted-Cookie609-manifest-literal-required")
    spec(COOKIE_COMMON_SPEC, COOKIE_COMMON_SPEC_SHA256)
    spec(CALLBACK_SPEC, CALLBACK_SPEC_SHA256)
    ci_hashes = ({name: row["after_sha256"] for name, row in ci["bindings"].items()} |
                 ci["added_inputs"] | ci["unchanged_inputs"] |
                 {CI_SPEC: CI_SPEC_SHA256, CI_OWNER: CI_OWNER_ANCESTOR_SHA256})
    share_hashes = ({name: row["after_sha256"] for name, row in share["bindings"].items()} |
                    share["added_inputs"] | share["unchanged_inputs"] |
                    {SHARE_SPEC: SHARE_SPEC_SHA256, SHARE_OWNER: SHARE_OWNER_ANCESTOR_SHA256})
    cookie_hashes = (cookie["accepted_cookie_inputs"] |
                     {name: row["after_sha256"] for name, row in cookie["bindings"].items()} |
                     cookie["new_inputs"] |
                     {"scripts/ci/tests/test_cookie_common_jdk_scope681.py": cookie["cookie681_control_binding"]["after_sha256"],
                      "scripts/ci/fresh-tests.init.gradle.kts": cookie["callback672_init_binding"]["after_sha256"],
                      CI_SPEC: CI_SPEC_SHA256, CALLBACK_SPEC: CALLBACK_SPEC_SHA256,
                      COOKIE_SPEC: COOKIE609_SPEC_SHA256, COOKIE_OWNER: COOKIE_OWNER_ANCESTOR_SHA256})
    import json
    canonical_cookie40 = (json.dumps(cookie_hashes, indent=2, sort_keys=True) + "\n").encode()
    need(sha(canonical_cookie40) == COOKIE40_MAP_SHA256 and
         cookie_hashes[CI_OWNER] == COOKIE_CI_OWNER_SHA256,
         "exact-sealed-original-Cookie40-map-required")
    need(len(ci_hashes) == 175 and len(cookie_hashes) == 40 and len(share_hashes) == 36,
         "exact-CI175-Cookie40-and-separate-Share36-predecessors-required")
    producer = spec(PRODUCER_SPEC, PRODUCER_SPEC_SHA256)
    need(producer["original_ci668_inputs"] == ci_hashes and
         len(producer["bindings"]) == 12 and
         sum(len(row["fragments"]) for row in producer["bindings"].values()) == 27,
         "original-producer645-twelve27-and-CI175-pins-required")
    producer_hashes = (producer["original_ci668_inputs"] |
                       {name: row["after_sha256"] for name, row in producer["bindings"].items()} |
                       producer["added_inputs"] |
                       {PRODUCER_SPEC: PRODUCER_SPEC_SHA256,
                        PRODUCER_OWNER: PRODUCER_OWNER_ANCESTOR_SHA256})
    canonical_producer190 = (json.dumps(producer_hashes, indent=2, sort_keys=True) + "\n").encode()
    need(len(producer_hashes) == 190 and sha(canonical_producer190) == PRODUCER190_MAP_SHA256,
         "exact-named-original-producer676-raw190-required")
    return {CI_VIEW: ci_hashes, COOKIE_VIEW: cookie_hashes, SHARE_VIEW: share_hashes,
            PRODUCER_VIEW: producer_hashes}


def _endpoint(row):
    need(type(row) is dict and set(row) == {"sha256", "bytes"} and
         type(row["sha256"]) is str and DIGEST.fullmatch(row["sha256"]) is not None and
         type(row["bytes"]) is int and 0 < row["bytes"] <= MAX_SOURCE,
         "exact-share-CI-complete-endpoint-required")


def _binding(row, count=None):
    need(type(row) is dict and set(row) == {
         "before_sha256", "after_sha256", "before_bytes", "after_bytes", "fragments"} and
         all(type(row[key]) is str and DIGEST.fullmatch(row[key]) is not None
             for key in ("before_sha256", "after_sha256")) and
         all(type(row[key]) is int and 0 < row[key] <= MAX_SOURCE
             for key in ("before_bytes", "after_bytes")) and
         type(row["fragments"]) is list and 0 < len(row["fragments"]) <= 16 and
         (count is None or len(row["fragments"]) == count),
         "finite-exact-share-CI-reversible-binding-required")
    for fragment in row["fragments"]:
        need(type(fragment) is dict and set(fragment) == {
             "before", "after", "before_fragment_sha256", "after_fragment_sha256"} and
             all(type(fragment[key]) is str and 0 < len(fragment[key].encode()) <= MAX_SOURCE
                 for key in fragment) and fragment["before"] != fragment["after"] and
             all(DIGEST.fullmatch(fragment[key]) is not None
                 for key in ("before_fragment_sha256", "after_fragment_sha256")),
             "exact-share-CI-unique-fragment-identities-required")
        need(sha(fragment["before"].encode()) == fragment["before_fragment_sha256"] and
             sha(fragment["after"].encode()) == fragment["after_fragment_sha256"],
             "complete-share-CI-fragment-hashes-required")


def _failure711_binding(document):
    """One separately sealed6a4->58f diagnostic transition, never a707 repin."""
    need(type(document) is dict and type(document.get("failure711_bindings")) is dict and
         set(document["failure711_bindings"]) == {OFFLINE},
         "exact711-one-path-diagnostic-transition-required")
    row = document["failure711_bindings"][OFFLINE]
    _binding(row, 2)
    import json
    encoded = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
    need(sha(encoded) == FAILURE711_BINDING_SHA256 and
         row["before_sha256"] == BUDGET707_CURRENT_SHA256[OFFLINE] and
         row["after_sha256"] == FAILURE711_CURRENT_SHA256,
         "exact711-two-original-diagnostic-fragments-before-unchanged707-required")
    return row


def _shape(document, root=ROOT):
    need(type(document) is dict and set(document) == {
         "schema_version", "scope", "predecessor_custody", "predecessor_inputs", "raw_inputs",
         "derivative_bindings", "failure711_bindings", "views", "noncurrent_sibling_bindings",
         "named_cookie609_manifest", "own_guard"} and
         type(document["schema_version"]) is int and document["schema_version"] == 1 and
         document["scope"] == SCOPE and document["predecessor_custody"] == PREDECESSOR_CUSTODY and
         all(type(document["predecessor_custody"].get(key)) is bool for key in (
             "original_missing_terminal_receipt_retained", "original_uncaptured_console_retained",
             "native_cause_verified", "JNI_execution_revived",
             "standalone_share_independent_and_joint_acceptance_granted", "future_diagnostics_endpoints_adopted",
             "joint279_source_proposal_adopted", "producer_or_reuse_runtime_accepted",
             "budget707_original_context_disposal_order_preserved", "budget707_three_exact_transitions_six_fragments",
             "budget707_source_proposal_adopted", "budget707_runtime_or_reuse_accepted",
             "budget707_provisional339_never_adopted")) and
         type(document["predecessor_inputs"]) is dict and set(document["predecessor_inputs"]) == VIEWS and
         type(document["raw_inputs"]) is dict and type(document["derivative_bindings"]) is dict and
         set(document["derivative_bindings"]) == set(BOUND_FRAGMENT_COUNTS) and
         type(document["views"]) is dict and set(document["views"]) == VIEWS,
         "finite-four-named-joint-source-views-required")
    failure711 = _failure711_binding(document)
    need(document["raw_inputs"].get(OFFLINE) == {"sha256": failure711["after_sha256"],
         "bytes": failure711["after_bytes"]}, "actual711-endpoint-never-projected707-current-required")
    for relative, endpoint in FAILURE711_ADDITION_ENDPOINTS.items():
        need(document["raw_inputs"].get(relative) == endpoint,
             "exact-two-new711-source-input-endpoints-required")
    ancestors = _sealed_predecessor_hashes(root, document)
    for view in VIEWS:
        inputs = document["predecessor_inputs"][view]
        need(type(inputs) is dict and set(inputs) == set(ancestors[view]),
             "complete-distinct-share-CI-predecessor-inputs-required")
        for relative, row in inputs.items():
            _identity(relative, b"source-identity-only")
            _endpoint(row)
            need(row["sha256"] == ancestors[view][relative], "sealed-share-CI-ancestor-identity-required")
    # Resolve the five real ancestor conflicts by owning identity, not union order.
    owning = {WORKFLOW: CI_VIEW, LIBRARY: SHARE_VIEW, CI_OWNER: CI_VIEW,
              "calf-webview/build.gradle.kts": COOKIE_VIEW,
              "scripts/ci/ios_ui_application.py": COOKIE_VIEW}
    base = {}
    conflicts = set()
    for view in (CI_VIEW, COOKIE_VIEW, SHARE_VIEW):
        for relative, digest in ancestors[view].items():
            if relative in base and base[relative] != digest:
                conflicts.add(relative)
            base[relative] = digest
    need(conflicts == set(owning), "exact-five-owning-ancestor-conflicts-required")
    for relative, view in owning.items():
        base[relative] = ancestors[view][relative]
    need(not set(base) & set(IMPORT_CLOSURE24), "disjoint-joint-import-closure-required")
    base.update(IMPORT_CLOSURE24)
    need(len(base) == 260, "exact-historical-three-view-import260-required")
    producer = ancestors[PRODUCER_VIEW]
    producer_conflicts = {name for name in set(base) & set(producer) if base[name] != producer[name]}
    need(producer_conflicts == {CI_OWNER, LIBRARY, "calf-webview/build.gradle.kts",
         "scripts/ci/ios_ui_application.py", OFFLINE, UI_SPLIT_CONTROL, CI_CONTROL},
         "exact-seven-producer-Cookie-Share-source-conflicts-required")
    base.update(producer)
    # Explicit owning decisions, never a union-order overlay or blanket repin.
    for relative, view in {CI_OWNER: CI_VIEW, LIBRARY: SHARE_VIEW,
            "calf-webview/build.gradle.kts": COOKIE_VIEW,
            "scripts/ci/ios_ui_application.py": COOKIE_VIEW,
            OFFLINE: PRODUCER_VIEW, UI_SPLIT_CONTROL: PRODUCER_VIEW,
            CI_CONTROL: PRODUCER_VIEW}.items():
        base[relative] = ancestors[view][relative]
    need(len(base) == 275 and set(document["raw_inputs"]) == set(base) | ADDED_INPUTS,
         "complete-finite-joint-raw280-plus-owner-spec-required")
    for relative, row in document["raw_inputs"].items():
        _identity(relative, b"source-identity-only")
        _endpoint(row)
        if relative in base and relative not in BOUND_FRAGMENT_COUNTS:
            need(row["sha256"] == base[relative], "unchanged-share-CI-full-raw-input-required")
    for relative, row in document["derivative_bindings"].items():
        _binding(row, BOUND_FRAGMENT_COUNTS[relative])
        raw = document["raw_inputs"][relative]
        if relative == OFFLINE:
            raw = {"sha256": failure711["before_sha256"], "bytes": failure711["before_bytes"]}
        need(row["before_sha256"] == base[relative] and row["after_sha256"] == raw["sha256"] and
             row["after_bytes"] == raw["bytes"], "complete-share-CI-descendant-custody-required")
        if relative in BUDGET707_FRAGMENT_COUNTS:
            import json
            encoded = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
            need(sha(encoded) == BUDGET707_BINDING_SHA256[relative] and
                 row["after_sha256"] == BUDGET707_CURRENT_SHA256[relative],
                 "exact-lead707-three-path-six-fragment-source-prelude-required")
    for view in VIEWS:
        rows = document["views"][view]
        # Finite707 prelude is stored ONCE, not repeated into every ancestor.
        # These named rows start only after that exact original-raw qualification.
        effective = {relative: (document["derivative_bindings"][relative]["before_sha256"]
                      if relative in BUDGET707_FRAGMENT_COUNTS else document["raw_inputs"][relative]["sha256"])
                     for relative in ancestors[view]}
        changed = {relative for relative, digest in ancestors[view].items() if effective[relative] != digest}
        need(type(rows) is dict and set(rows) == changed,
             "every-changed-input-in-its-explicit-share-CI-view-required")
        for relative, row in rows.items():
            _binding(row)
            raw, ancestor = document["raw_inputs"][relative], document["predecessor_inputs"][view][relative]
            if relative in BUDGET707_FRAGMENT_COUNTS:
                prelude = document["derivative_bindings"][relative]
                raw = {"sha256": prelude["before_sha256"], "bytes": prelude["before_bytes"]}
            need((row["before_sha256"], row["before_bytes"]) == (raw["sha256"], raw["bytes"]) and
                 (row["after_sha256"], row["after_bytes"]) == (ancestor["sha256"], ancestor["bytes"]),
                 "named-share-CI-view-starts-only-after-exact707-prelude-and-ends-at-sealed-ancestor")
    siblings = document["noncurrent_sibling_bindings"]
    need(type(siblings) is dict and set(siblings) == {CI_OWNER},
         "only-explicit-noncurrent-Share-CI-sibling-is-recorded")
    _binding(siblings[CI_OWNER], 7)
    import json
    encoded_sibling = (json.dumps(siblings[CI_OWNER], indent=2, sort_keys=True) + "\n").encode()
    need(sha(encoded_sibling) == NONCURRENT_SIBLING_BINDING_SHA256 and
         siblings[CI_OWNER]["before_sha256"] == CI_OWNER_ANCESTOR_SHA256 and
         siblings[CI_OWNER]["after_sha256"] == PREDECESSOR_CUSTODY["standalone_share_CI_guard_not_adopted_sha256"],
         "exact-noncurrent-sibling-data-never-a-raw-or-history-view")
    own = document["own_guard"]
    need(type(own) is dict and set(own) == {"template_sha256", "bytes"} and
         type(own["template_sha256"]) is str and DIGEST.fullmatch(own["template_sha256"]) is not None and
         type(own["bytes"]) is int and 0 < own["bytes"] <= MAX_SOURCE,
         "exact-share-CI-own-guard-template-required")
    return document


def _document(root=ROOT):
    raw = _ordinary(root, SPEC, MAX_SPEC)[0]
    need(sha(raw) == SPEC_SHA256, "exact-share-CI-latest-manifest-required")
    return _shape(_json(raw), root)


def _own_payload(payload, document):
    needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
    template = ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode()
    need(type(payload) is bytes and len(payload) == document["own_guard"]["bytes"] and
         payload.count(needle) == 1 and
         sha(payload.replace(needle, template, 1)) == document["own_guard"]["template_sha256"],
         "complete-share-CI-latest-own-guard-required")
    return sha(payload)


def _raw_payload(relative, payload, document):
    _identity(relative, payload)
    if relative == OWNER:
        _own_payload(payload, document)
    elif relative == SPEC:
        need(sha(payload) == SPEC_SHA256, CURRENT_REFUSAL)
    else:
        row = document["raw_inputs"].get(relative)
        need(row is not None and sha(payload) == row["sha256"] and len(payload) == row["bytes"],
             CURRENT_REFUSAL)


def _inverse_to_ancestor(payload, row):
    """One exact latest-to-ancestor inverse with complete reverse-forward custody."""
    _binding(row)
    need(type(payload) is bytes and sha(payload) == row["before_sha256"] and len(payload) == row["before_bytes"],
         "complete-share-CI-latest-view-source-required")
    restored = payload
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        need(restored.count(before) == 1, "unique-share-CI-view-inverse-fragment-required")
        restored = restored.replace(before, after, 1)
    need(sha(restored) == row["after_sha256"] and len(restored) == row["after_bytes"],
         "complete-share-CI-declared-view-ancestor-required")
    forward = restored
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        need(forward.count(after) == 1, "unique-share-CI-view-forward-fragment-required")
        forward = forward.replace(after, before, 1)
    need(forward == payload, "complete-share-CI-view-roundtrip-required")
    return restored


def _failure711_to_budget707(payload, document):
    """Exact two-fragment711 inverse only; source data, not current admission."""
    row = _failure711_binding(document)
    inverse = {"before_sha256": row["after_sha256"], "before_bytes": row["after_bytes"],
               "after_sha256": row["before_sha256"], "after_bytes": row["before_bytes"],
               "fragments": [{"before": f["after"], "after": f["before"],
                              "before_fragment_sha256": f["after_fragment_sha256"],
                              "after_fragment_sha256": f["before_fragment_sha256"]}
                             for f in reversed(row["fragments"])]}
    return _inverse_to_ancestor(payload, inverse)


def _budget707_in_named_domain(view, relative, payload, document):
    """One finite exact707 inverse, before a named domain's unchanged old pins.

    Cookie40 has no budget leaf; new707 controls are never historical domains.
    No source is imported/executed, no layer is searched, no inverse is readmitted.
    """
    if relative not in BUDGET707_FRAGMENT_COUNTS or relative not in document["predecessor_inputs"][view]:
        return payload
    row = document["derivative_bindings"][relative]
    _binding(row, BUDGET707_FRAGMENT_COUNTS[relative])
    inverse = {"before_sha256": row["after_sha256"], "before_bytes": row["after_bytes"],
               "after_sha256": row["before_sha256"], "after_bytes": row["before_bytes"],
               "fragments": [{"before": f["after"], "after": f["before"],
                              "before_fragment_sha256": f["after_fragment_sha256"],
                              "after_fragment_sha256": f["before_fragment_sha256"]}
                             for f in reversed(row["fragments"])]}
    return _inverse_to_ancestor(payload, inverse)


def peel_budget707_for_history(relative, payload, root=ROOT):
    """Exact711->707->2ee data; other707 leaves unchanged, no175/190/9bd.

    One repository transition manifest is read. Pass-through is not admission;
    no old source becomes current and no source/native/result code is executed.
    """
    _identity(relative, payload)
    if relative not in BUDGET707_FRAGMENT_COUNTS:
        return payload
    raw = _ordinary(root, SPEC, MAX_SPEC)[0]
    need(sha(raw) == SPEC_SHA256, "exact707-transition-manifest-required")
    document = _json(raw)
    need(type(document) is dict and type(document.get("derivative_bindings")) is dict,
         "exact707-transition-dictionary-required")
    row = document["derivative_bindings"].get(relative)
    _binding(row, BUDGET707_FRAGMENT_COUNTS[relative])
    import json
    encoded = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
    need(sha(encoded) == BUDGET707_BINDING_SHA256[relative] and
         row["after_sha256"] == BUDGET707_CURRENT_SHA256[relative],
         "exact707-three-path-six-fragment-transition-required")
    if relative == OFFLINE:
        failure711 = _failure711_binding(document)
        if sha(payload) != failure711["after_sha256"] or len(payload) != failure711["after_bytes"]:
            return payload  # Old6a4 is data, not a new711 descendant or layer search.
        payload = _failure711_to_budget707(payload, document)
    if sha(payload) != row["after_sha256"] or len(payload) != row["after_bytes"]:
        return payload  # Data only, not old-current admission or a layer search.
    inverse = {"before_sha256": row["after_sha256"], "before_bytes": row["after_bytes"],
               "after_sha256": row["before_sha256"], "after_bytes": row["before_bytes"],
               "fragments": [{"before": f["after"], "after": f["before"],
                              "before_fragment_sha256": f["after_fragment_sha256"],
                              "after_fragment_sha256": f["before_fragment_sha256"]}
                             for f in reversed(row["fragments"])]}
    return _inverse_to_ancestor(payload, inverse)


def _view(view, relative, payload, document):
    need(type(view) is str and view in VIEWS, "only-four-explicit-joint-source-views-defined")
    if relative == OFFLINE and relative in document["predecessor_inputs"][view]:
        payload = _failure711_to_budget707(payload, document)
    payload = _budget707_in_named_domain(view, relative, payload, document)
    row = document["views"][view].get(relative)
    return payload if row is None else _inverse_to_ancestor(payload, row)


def current_source_in_view(relative, payload, view, root=ROOT):
    """Single strict latest raw ingress, then the explicitly named owning ancestor."""
    document = _document(root)
    _raw_payload(relative, payload, document)
    return _view(view, relative, payload, document)


def peel_for_history(relative, payload, view, root=ROOT):
    """Only exact declared latest descendants peel; pass-through is NOT admission."""
    _identity(relative, payload)
    document = _document(root)
    need(type(view) is str and view in VIEWS, "only-four-explicit-joint-source-views-defined")
    # Sealed source comparisons are explicit; generic history must NEVER
    # peel either Cookie control source or callback-init bytes.
    if relative in {NEW_COOKIE_CONTROL, OWNING_COOKIE_CONTROL, CALLBACK_INIT, BUDGET707_CONTROL,
                    FAILURE711_HELPER, FAILURE711_CONTROL}:
        return payload
    if relative == OFFLINE and relative in document["predecessor_inputs"][view]:
        failure711 = _failure711_binding(document)
        if sha(payload) == failure711["after_sha256"] and len(payload) == failure711["after_bytes"]:
            return _view(view, relative, payload, document)
        return payload  # Never readmit old707/2ee/named images into the new711 chain.
    if relative in BUDGET707_FRAGMENT_COUNTS and relative in document["predecessor_inputs"][view]:
        budget = document["derivative_bindings"][relative]
        if sha(payload) == budget["after_sha256"] and len(payload) == budget["after_bytes"]:
            return _view(view, relative, payload, document)
        return payload  # Never treat an old2ee inverse as current707 or search its older layers.
    row = document["views"][view].get(relative)
    if row is not None and sha(payload) == row["before_sha256"] and len(payload) == row["before_bytes"]:
        return _inverse_to_ancestor(payload, row)
    return payload  # No generic layer search, old-as-current admission, or restored execution.


def predecessor_input_hashes(view, root=ROOT):
    """Named historical metadata only; NEVER returned as actual raw current hashes."""
    need(type(view) is str and view in VIEWS, "only-four-explicit-joint-source-views-defined")
    return {name: row["sha256"] for name, row in _document(root)["predecessor_inputs"][view].items()}


def validate_current_sources(root=ROOT):
    """Whole finite joint282 raw custody and all named inverses; ZERO code execution."""
    document = _document(root)
    identities = {}
    for relative, row in document["raw_inputs"].items():
        raw, identity = _ordinary(root, relative)
        _raw_payload(relative, raw, document)
        identities[relative] = identity
    raw, identities[OWNER] = _ordinary(root, OWNER)
    _own_payload(raw, document)
    raw, identities[SPEC] = _ordinary(root, SPEC, MAX_SPEC)
    need(sha(raw) == SPEC_SHA256, "exact-share-CI-manifest-held-through-validation-required")
    for view in VIEWS:
        for relative, ancestor in document["predecessor_inputs"][view].items():
            raw = _ordinary(root, relative)[0]
            if sha(raw) != ancestor["sha256"]:
                restored = _view(view, relative, raw, document)
                need((sha(restored), len(restored)) == (ancestor["sha256"], ancestor["bytes"]),
                     "complete-budget707-and-named-ancestor-custody-required")
    for relative, identity in identities.items():
        maximum = MAX_SPEC if relative == SPEC else MAX_SOURCE
        need(_ordinary(root, relative, maximum)[1] == identity,
             "whole-share-CI-current-input-custody-changed-during-validation")
    return True


def current_input_hashes(root=ROOT):
    """Actual complete joint282 map; no named predecessor is relabelled current."""
    validate_current_sources(root)
    document = _document(root)
    owner = _own_payload(_ordinary(root, OWNER)[0], document)
    return ({name: row["sha256"] for name, row in document["raw_inputs"].items()} |
            {SPEC: SPEC_SHA256, OWNER: owner})


def fixture_inputs(root=ROOT):
    """Finite latest source/import/control custody only, not a native test selector."""
    return set(_document(root)["raw_inputs"]) | {OWNER, SPEC}
