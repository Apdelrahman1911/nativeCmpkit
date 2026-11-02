"""Nine NEW Camera197 owned-console grammar controls; no accepted method imports.

Every name/result below is visibly synthetic. No original name or reply is
reconstructed. The lead alone executes these controls once on exact sealed bytes.
This class imports only the exact helper under process/network action guards.
"""
from __future__ import annotations

import ast
from contextlib import ExitStack
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import unittest
from unittest.mock import patch

TREE = Path(os.environ.get("NATIVECMPKIT_CAMERA_CONSOLE_SOURCE_TREE", Path(__file__).absolute().parents[2])).absolute()
HELPER_RELATIVE_PATH = "scripts/ci/android_camera_developer_prerequisite.py"
HELPER_PATH = TREE / HELPER_RELATIVE_PATH
BEFORE_HELPER_SHA256 = 'da07bedb680e9ce36842bbf581f22bf7b3ebf8ab1c5d307b05745069c77bb5a4'
AFTER_HELPER_SHA256 = '0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26'
OLD_CONDITION = '        require(line(self.control("emu", "avd", "name"), 512,\n                     re.escape(self.guest.name.encode()) + rb"\\nOK") == self.guest.name.encode() + b"\\nOK",\n'
NEW_CONDITION = '        require(owned_avd_console_name(self.control("emu", "avd", "name"), self.guest.name)\n                == self.guest.name.encode(),\n'
APPEND_CONSOLE_HELPER = '\n\ndef owned_avd_console_name(result: subprocess.CompletedProcess, expected_name: str) -> bytes:\n    """Exact owned console name/OK framing only; never a general scalar normalization."""\n    require(type(expected_name) is str and\n            re.fullmatch(r"nativecmpkit-api35-[a-f0-9]{12}", expected_name) is not None,\n            "Unknown owned AVD name contract")\n    name = expected_name.encode("ascii")\n    payload = result_bytes(result, 512)\n    require(payload in (name + b"\\nOK\\n", name + b"\\r\\nOK\\r\\n"),\n            "Unknown owned AVD console-name frame")\n    return name\n'
BOUND_SOURCE_BEFORE47 = {'.github/workflows/gradle.yml': '282254f7af66a47f065693f5fd4b30ae0acf8c44ca589fcc9432857ab473ef09', 'calf-camera-picker/build.gradle.kts': 'f074767f7042ac6e07955b361400e672ae43209f99b17986acd27cf5078428c7', 'calf-camera-picker/src/androidDeviceTest/AndroidManifest.xml': 'c24a6c2498dddb660cafd78d31bfc4f4730f8ae34f1c807eff3f17ff6034962b', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraProviderTest.kt': 'e222639ed728465798aa0be937f13dc181c36dfd566db0b2fa9bbdbe67f18532', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt': '357c8545e35d5fa529a6b38b064a86c1724ea2b0a2d2b7ec46d5ff4c3671a7d0', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRestorationVerificationActivity.kt': '8aeb2acf56287c08619c854f4da21c3f0c4f95d7dba19e17ca6ceacff03a0c12', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraVerificationProviders.kt': '09956cd5f88d5c18dff5be3251d9ece6beb679f5c961c3041e1450cf46e96f82', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedAlwaysFinish.kt': '2010803e066ce0de1a34051ed40a50c9bca08f238a6218dcaabb4e7d0a09bee7', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedCameraReceiver.kt': 'a15663164f0b66eccf225a0a24d0af7be77e13c80bc620be501d388224a76a6d', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt': 'a1fb76c6092881a3681ec38002b4820f1d0d8282727a4d18fa89968f6b8c5b50', 'calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt': 'b7094d795bfaa209b254bbf2c549de21a7fff07df636fbb68f4cb1a3baa917a7', 'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRequestStateTest.kt': '0ff1470d93f9580e27b54e499b2dda6843a50c5d7b4f4b5c4cfaca7980c7e841', 'convention-plugins/src/main/kotlin/Android.kt': '204b7b0bb30e33144794ffda1d993f925f670cac87c809155d81fe9f09f7a256', 'scripts/ci/android_camera_developer_prerequisite.py': 'da07bedb680e9ce36842bbf581f22bf7b3ebf8ab1c5d307b05745069c77bb5a4', 'scripts/ci/android_camera_receiver.py': '032ac23053338ec9e839cdae8b3a946a84712ff92a7f821f4972230241eb03a2', 'scripts/ci/android_device_tests.py': 'daac8786b1b034efcad0687a2f3a995c2216ea1a400116f9c592693d5c6395ec', 'scripts/ci/android_kvm_timeline.py': '488442a673d07f0a92bfffc31adcdeac3cf7de11568662fa6b6925eee7c1149b', 'scripts/ci/camera_scalar_failfast_source_projection.py': '3a0f5a01f30e482af2cf3c6953d68a21aa3d824952eaca54556abe06045ccbbb', 'scripts/ci/fixtures/android-camera-scalar-failfast-controller-inverse.json': '9a3479f92b05e1bffda3b408ad9f5833ca655b0c913af813e888209de9b2828c', 'scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json': 'e7b0e9a3e361e39d1732ed33cd5e1d4e51a3e30ed377adf487001b742754c953', 'scripts/ci/fixtures/android-camera-startup-readiness-inverse.json': '43a8963e59a7851e968fbbeeaafa19944956cbc6a6f0b5cb8924a4dba0342e2c', 'scripts/ci/library_tests.py': 'b333567dff6f85bad734077bb44b2f4028035316ee2c3771cbe82b2019d00dfb', 'scripts/ci/run_android_camera_scalar_failfast_new_only.py': '6ce3556e0df614757ede6c469ccc0e12a536b0aa9ce86214234e474fd22fc022', 'scripts/ci/runtime_context.py': 'e23aff04c665dc1041dc9e27db775135223ace15c63a651e17b94a7155731712', 'scripts/ci/sample_platform_verification.py': '6780e5c355d22cf74716b0cb344fc02ee968710db5382d6460c930b99d395ca7', 'scripts/ci/test_android_camera_capture_admission.py': '2bd33a287cc8fd6d85b1c3baa7e3589c175619f2f38e09e62f53bfc872ee1467', 'scripts/ci/test_android_camera_developer_prerequisite.py': '4a78c909420383a59cb453c1ca58ab3c0ca909a08f17201ddc0bcea657a061bb', 'scripts/ci/test_android_camera_documented_data_default.py': '7b5a75da995f4ae7a93035e459728f8046a3082c9df868c6e429ad8423e1cf13', 'scripts/ci/test_android_camera_dont_keep.py': '7c936bf4a071233f19ada5ad02f587c211b7213b1f9008d0dd45418a98ad21a9', 'scripts/ci/test_android_camera_mutable_path_diagnostics.py': 'd527d9177e1cb45f4ce594bb6a97fb777ccd6ef6e1b84e12c117c73959e77de6', 'scripts/ci/test_android_camera_pre_reporter_fail_fast.py': '92d923e23c4fb7366811d9fedc5b949e5fc3043372adc5b75fbefa8d9dac3020', 'scripts/ci/test_android_camera_prerequisite_require_origin.py': 'e93298e1f8fe5f04f718c68ac1d6d95b8a5802b53b76058d989d279a350b00ae', 'scripts/ci/test_android_camera_provider.py': 'd56088155fc7ff4fd61b076b0c45f39ec577d02145103a305c3f4c96b2c45567', 'scripts/ci/test_android_camera_scalar_control_refusal.py': '2bde6d9d02a8c2a3167992e4df024930d5e0bbe731272e6a71693fb8a83088f9', 'scripts/ci/test_android_camera_settings_activity_boundary.py': '9b726a295d3eed6d7a7344f592b11b3ead551651ebd3e5be807c8047a804913d', 'scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py': '09fcbc6e7b9af1e6cac0cfcd3feae048a5d8e3a5d10b49a222b534f2aa0874df', 'scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py': 'bd539b328cdf586cca655b7a34e5006f7417ee21724308f906fa1d5199d4224e', 'scripts/ci/test_android_camera_settings_ui.py': 'b66d63ab003bf8ef57088e8ce7a8d8cb86277e8a486715b8dfdda1fae2035936', 'scripts/ci/test_android_camera_startup_readiness.py': '056711d56c8cdf02866d2d013be34be2e2dc90b6bc197ea7c046c6c488fb5c86', 'scripts/ci/test_android_kvm_timeline.py': '9eab5e2173ca1bb3520028d11bdeefb03dad8a47a43f1872342d5979d5ca7f32', 'scripts/ci/test_runtime_context.py': '6fe2fccaee0680edacbf0ecd69aef29d4cfe1a1253fcae32d0389ff0e7cdd866', 'tests/consumer/android-camera-receiver/build.gradle.kts': '92000d4bad25e57121cb5c100363d44955f0bdef290372bd3da965342f1523f4', 'tests/consumer/android-camera-receiver/settings.gradle.kts': '31507eb3489726a100053c8624e941f2ad0511460a55a4f62edf6a8b9f850c4f', 'tests/consumer/android-camera-receiver/src/main/AndroidManifest.xml': '2e507acb6e0ec0f3fbb3c3bbc7908a5d882277804a68f670e8814160e16fadd5', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraDelayedReceiverActivity.java': '8a5df77d685676fe29842d4231e86d0a8cf7a3bc388ec69ccf95be28c1d59a93', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverActivity.java': '2df3ad3ab2e985fa87483c18f269f3fbcf98d44210cf2c346c955dc60a13c8c9', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverService.java': 'b7e366c37f91208afafd8fe6db1160a6048e740ead8c6cc334101b7a4a353a53'}
BOUND_SOURCE_AFTER47 = {'.github/workflows/gradle.yml': 'ac55aee1f485f78914de5405c517f4a9f8a5a6fed2f7ba88650e2a4fb8401561', 'calf-camera-picker/build.gradle.kts': 'f074767f7042ac6e07955b361400e672ae43209f99b17986acd27cf5078428c7', 'calf-camera-picker/src/androidDeviceTest/AndroidManifest.xml': 'c24a6c2498dddb660cafd78d31bfc4f4730f8ae34f1c807eff3f17ff6034962b', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraProviderTest.kt': 'e222639ed728465798aa0be937f13dc181c36dfd566db0b2fa9bbdbe67f18532', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt': '357c8545e35d5fa529a6b38b064a86c1724ea2b0a2d2b7ec46d5ff4c3671a7d0', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRestorationVerificationActivity.kt': '8aeb2acf56287c08619c854f4da21c3f0c4f95d7dba19e17ca6ceacff03a0c12', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraVerificationProviders.kt': '09956cd5f88d5c18dff5be3251d9ece6beb679f5c961c3041e1450cf46e96f82', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedAlwaysFinish.kt': '2010803e066ce0de1a34051ed40a50c9bca08f238a6218dcaabb4e7d0a09bee7', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedCameraReceiver.kt': 'a15663164f0b66eccf225a0a24d0af7be77e13c80bc620be501d388224a76a6d', 'calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt': 'a1fb76c6092881a3681ec38002b4820f1d0d8282727a4d18fa89968f6b8c5b50', 'calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt': 'b7094d795bfaa209b254bbf2c549de21a7fff07df636fbb68f4cb1a3baa917a7', 'calf-camera-picker/src/commonTest/kotlin/com/mohamedrejeb/calf/camerapicker/CameraRequestStateTest.kt': '0ff1470d93f9580e27b54e499b2dda6843a50c5d7b4f4b5c4cfaca7980c7e841', 'convention-plugins/src/main/kotlin/Android.kt': '204b7b0bb30e33144794ffda1d993f925f670cac87c809155d81fe9f09f7a256', 'scripts/ci/android_camera_developer_prerequisite.py': '0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26', 'scripts/ci/android_camera_receiver.py': '032ac23053338ec9e839cdae8b3a946a84712ff92a7f821f4972230241eb03a2', 'scripts/ci/android_device_tests.py': 'daac8786b1b034efcad0687a2f3a995c2216ea1a400116f9c592693d5c6395ec', 'scripts/ci/android_kvm_timeline.py': '488442a673d07f0a92bfffc31adcdeac3cf7de11568662fa6b6925eee7c1149b', 'scripts/ci/camera_scalar_failfast_source_projection.py': '6858fbd343cefad52b709663fbf5e98bccfa52111c2a1b8fd6eff8d8536cdb12', 'scripts/ci/fixtures/android-camera-scalar-failfast-controller-inverse.json': '9a3479f92b05e1bffda3b408ad9f5833ca655b0c913af813e888209de9b2828c', 'scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json': 'e7b0e9a3e361e39d1732ed33cd5e1d4e51a3e30ed377adf487001b742754c953', 'scripts/ci/fixtures/android-camera-startup-readiness-inverse.json': '43a8963e59a7851e968fbbeeaafa19944956cbc6a6f0b5cb8924a4dba0342e2c', 'scripts/ci/library_tests.py': '5012c3e2be83e62eba8239a0db12104d5f9f7efb3f262abd3b3080012f7afdc2', 'scripts/ci/run_android_camera_scalar_failfast_new_only.py': '6ce3556e0df614757ede6c469ccc0e12a536b0aa9ce86214234e474fd22fc022', 'scripts/ci/runtime_context.py': 'e23aff04c665dc1041dc9e27db775135223ace15c63a651e17b94a7155731712', 'scripts/ci/sample_platform_verification.py': '6780e5c355d22cf74716b0cb344fc02ee968710db5382d6460c930b99d395ca7', 'scripts/ci/test_android_camera_capture_admission.py': '2bd33a287cc8fd6d85b1c3baa7e3589c175619f2f38e09e62f53bfc872ee1467', 'scripts/ci/test_android_camera_developer_prerequisite.py': '4a78c909420383a59cb453c1ca58ab3c0ca909a08f17201ddc0bcea657a061bb', 'scripts/ci/test_android_camera_documented_data_default.py': '7b5a75da995f4ae7a93035e459728f8046a3082c9df868c6e429ad8423e1cf13', 'scripts/ci/test_android_camera_dont_keep.py': '7c936bf4a071233f19ada5ad02f587c211b7213b1f9008d0dd45418a98ad21a9', 'scripts/ci/test_android_camera_mutable_path_diagnostics.py': 'd527d9177e1cb45f4ce594bb6a97fb777ccd6ef6e1b84e12c117c73959e77de6', 'scripts/ci/test_android_camera_pre_reporter_fail_fast.py': '663bf8e7c846519e719ca1da7087feddc7a3f1e7dab65fe3dfad23e7a66c1669', 'scripts/ci/test_android_camera_prerequisite_require_origin.py': 'e93298e1f8fe5f04f718c68ac1d6d95b8a5802b53b76058d989d279a350b00ae', 'scripts/ci/test_android_camera_provider.py': 'd56088155fc7ff4fd61b076b0c45f39ec577d02145103a305c3f4c96b2c45567', 'scripts/ci/test_android_camera_scalar_control_refusal.py': 'e0ca6710cf89cb68ec21e91996ae49ee072e477dfc17b0eb0206794872444ffe', 'scripts/ci/test_android_camera_settings_activity_boundary.py': '9b726a295d3eed6d7a7344f592b11b3ead551651ebd3e5be807c8047a804913d', 'scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py': '9c2ee35603ccc5c30a49fd91d438fa88584386637bb550ab2557d44760d1bbe5', 'scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py': '048b40f6976fc6af2160c9934b39d620bbdac466d912edfbb9e315dfa92f8bf7', 'scripts/ci/test_android_camera_settings_ui.py': 'b66d63ab003bf8ef57088e8ce7a8d8cb86277e8a486715b8dfdda1fae2035936', 'scripts/ci/test_android_camera_startup_readiness.py': '239bbde00bd8deb728119aa2d76395f4e01615ab25092a3fe2a6dd57f8a274bf', 'scripts/ci/test_android_kvm_timeline.py': '9eab5e2173ca1bb3520028d11bdeefb03dad8a47a43f1872342d5979d5ca7f32', 'scripts/ci/test_runtime_context.py': '6fe2fccaee0680edacbf0ecd69aef29d4cfe1a1253fcae32d0389ff0e7cdd866', 'tests/consumer/android-camera-receiver/build.gradle.kts': '92000d4bad25e57121cb5c100363d44955f0bdef290372bd3da965342f1523f4', 'tests/consumer/android-camera-receiver/settings.gradle.kts': '31507eb3489726a100053c8624e941f2ad0511460a55a4f62edf6a8b9f850c4f', 'tests/consumer/android-camera-receiver/src/main/AndroidManifest.xml': '2e507acb6e0ec0f3fbb3c3bbc7908a5d882277804a68f670e8814160e16fadd5', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraDelayedReceiverActivity.java': '8a5df77d685676fe29842d4231e86d0a8cf7a3bc388ec69ccf95be28c1d59a93', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverActivity.java': '2df3ad3ab2e985fa87483c18f269f3fbcf98d44210cf2c346c955dc60a13c8c9', 'tests/consumer/android-camera-receiver/src/main/java/io/github/apdelrahman1911/nativecmpkit/verification/camerareceiver/CameraReceiverService.java': 'b7e366c37f91208afafd8fe6db1160a6048e740ead8c6cc334101b7a4a353a53'}
# Exact Camera205 owning derivatives only; BEFORE47 and FIRST30 remain historical.
CAMERA205_DERIVATIVE_SOURCE_SHA256 = {
    "scripts/ci/camera_scalar_failfast_source_projection.py": "6858fbd343cefad52b709663fbf5e98bccfa52111c2a1b8fd6eff8d8536cdb12",
    "scripts/ci/test_android_camera_pre_reporter_fail_fast.py": "40e8b5450b81a51e45c018d455c7d31fa6b557a82bd809ad2f2472214bdc0676",
    "scripts/ci/test_android_camera_scalar_control_refusal.py": "e0ca6710cf89cb68ec21e91996ae49ee072e477dfc17b0eb0206794872444ffe"
}

# One CI224 FF16 derivative, separate from the retained Camera205 three-leaf literal.
CAMERA224_DERIVATIVE_SOURCE_SHA256 = {
    "scripts/ci/test_android_camera_pre_reporter_fail_fast.py": "663bf8e7c846519e719ca1da7087feddc7a3f1e7dab65fe3dfad23e7a66c1669",
}

# Exact Share188 shared-source derivatives; BEFORE47 and FIRST30 remain historical.
CAMERA205_SHARE188_SHARED_SOURCE_SHA256 = {
    ".github/workflows/gradle.yml": "ac55aee1f485f78914de5405c517f4a9f8a5a6fed2f7ba88650e2a4fb8401561",
    "scripts/ci/library_tests.py": "5012c3e2be83e62eba8239a0db12104d5f9f7efb3f262abd3b3080012f7afdc2"
}

# Exact CI213 readers; original BEFORE47/FIRST30 bytes remain historical.
CAMERA213_DERIVATIVE_SOURCE_SHA256 = {'scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py': '048b40f6976fc6af2160c9934b39d620bbdac466d912edfbb9e315dfa92f8bf7', 'scripts/ci/test_android_camera_startup_readiness.py': '239bbde00bd8deb728119aa2d76395f4e01615ab25092a3fe2a6dd57f8a274bf', 'scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py': '9c2ee35603ccc5c30a49fd91d438fa88584386637bb550ab2557d44760d1bbe5'}

DECLARED_METHODS = ('test_cn01_only_complete_exact_lf_and_crlf_owned_name_ok_frames_pass', 'test_cn02_mixed_truncated_bare_and_internal_cr_frames_refuse', 'test_cn03_extra_rows_whitespace_wrong_ack_and_unsafe_bytes_refuse', 'test_cn04_fixed_bounded_expected_name_and_foreign_owner_refuse', 'test_cn05_original_result_exit_stderr_type_and_512_byte_cap_hold', 'test_cn06_console_admission_never_relaxes_the_original_scalar_gate', 'test_cn07_six_exact_callers_keep_commands_messages_and_public_origins', 'test_cn08_exact_full_source_inverse_refuses_partial_and_displaced_repairs', 'test_cn09_owning194_and_operational_native_bindings_are_not_rebased')
UNCHANGED_FUNCTION_SHA256 = {'result_bytes': 'd36c0b5420175f987c35f4efd8c56777ac6c570c693636c24a1cb3258d9bb30b', 'line': 'b3fd23b8f5681809509bf8fbb39030ff17462ac2ba1fae4ae152c081f3a70f40', 'scalar_query_identity': 'b855d858cd371c9ec740bfb8565b3677b7f8f92a31b7af8995587c927ada6dd0', 'record_scalar_control_refusal': '04da85a23dd34c789ded11ad0ae3ee4290fe810778d8f9f53e155661575cd296', 'OwnedDeveloperPrerequisite.failure': '1a2dac90f3aaf84efb074a44a83e21df57dbc1ec557d9136241e3fe80ef1629e', 'OwnedDeveloperPrerequisite.control': '40cbcb8dd696df307b65544a4b7bdc9cc24761637d437888107084c753c8a0d4', 'OwnedDeveloperPrerequisite.prepare': 'dfce9bd3e379adbf113bbba6495faf798003b35d7e4213ced6e64c812a1e412b', 'OwnedDeveloperPrerequisite.close': 'd4c772243090f842ef7c8da28c74651d0ac300d000647cb63fb9f469a6239085'}
EXPECTED_QUERY_START_LINES = (871, 923, 961, 994, 1188, 1221)
NAME = "nativecmpkit-api35-0123456789ab"  # Synthetic, not the original private owned name.
SOURCE_BYTES = 4 * 1024 * 1024
COUNTERS = {"new_console_parser_calls": 0, "new_scalar_cross_parser_calls": 0,
            "source_admission_refusals": 0, "binding_refusals": 0,
            "existing_accepted_test_methods_selected": 0, "native_invocations": 0}
FORBIDDEN_ACTIONS = []


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def admit_bound_payload(relative, payload):
    require(type(relative) is str and relative in BOUND_SOURCE_AFTER47 and type(payload) is bytes and
            len(payload) <= SOURCE_BYTES and digest(payload) == BOUND_SOURCE_AFTER47[relative],
            "An exact current owning source binding is required")
    return payload


def read_bound_source(relative):
    path = TREE / relative
    current = path.parent
    while True:
        info = current.lstat()
        require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), "No source ancestor symlink is admitted")
        if current == current.parent:
            break
        current = current.parent
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= SOURCE_BYTES,
            "A bounded ordinary unshared source file is required")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        opened = os.fstat(descriptor)
        require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino) and
                opened.st_nlink == 1 and stat.S_ISREG(opened.st_mode), "The source opened identity changed")
        blocks, size = [], 0
        while True:
            block = os.read(descriptor, min(65536, SOURCE_BYTES + 1 - size))
            if not block:
                break
            blocks.append(block)
            size += len(block)
            require(size <= SOURCE_BYTES, "The source exceeds its byte bound")
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    final = path.lstat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) ==
            (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns, final.st_ctime_ns) and
            final.st_nlink == 1 and stat.S_ISREG(final.st_mode), "The exact source changed during readback")
    return admit_bound_payload(relative, b"".join(blocks))


def admit_console_source(source):
    require(type(source) is str and 0 < len(source) <= SOURCE_BYTES, "Exact full console helper source is required")
    try:
        payload = source.encode("utf-8")
    except UnicodeError as error:
        raise ValueError("Exact full console helper source is required") from error
    require(digest(payload) == AFTER_HELPER_SHA256, "The full console helper afterimage changed")
    require(source.endswith(APPEND_CONSOLE_HELPER), "The protocol helper must follow every existing guarded body")
    restored = source.removesuffix(APPEND_CONSOLE_HELPER)
    require(restored.count(NEW_CONDITION) == 6 and OLD_CONDITION not in restored,
            "Only all six exact owning caller substitutions are admitted")
    restored = restored.replace(NEW_CONDITION, OLD_CONDITION, 6)
    require(digest(restored.encode()) == BEFORE_HELPER_SHA256 and restored.count(OLD_CONDITION) == 6 and
            restored.replace(OLD_CONDITION, NEW_CONDITION, 6) + APPEND_CONSOLE_HELPER == source,
            "The exact authored forward placement and inverse must both hold")
    return source


def forbidden(*args, **kwargs):
    FORBIDDEN_ACTIONS.append("forbidden-process-sdk-network-build-or-native-action")
    raise AssertionError("No process, SDK, network, build or native action is admitted")


def action_guards(stack):
    for module, names in (
        (subprocess, ("Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput")),
        (os, ("kill", "killpg", "system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp",
              "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
              "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe")),
        (socket, ("socket", "socketpair", "create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex")),
    ):
        for name in names:
            if hasattr(module, name):
                stack.enter_context(patch.object(module, name, forbidden))


def symbol_node(tree, symbol):
    nodes = tree.body
    found = None
    for component in symbol.split("."):
        matches = [node for node in nodes if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == component]
        require(len(matches) == 1, "An exact unique source symbol is required")
        found = matches[0]
        nodes = found.body
    return found


def symbol_source(source, symbol):
    node = symbol_node(ast.parse(source), symbol)
    return "".join(source.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])


def completed(stdout, stderr=b"", code=0):
    return subprocess.CompletedProcess(["synthetic-owned-console-query"], code, stdout, stderr)


class OwnedAvdConsoleNameNewOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_payloads = {relative: read_bound_source(relative) for relative in BOUND_SOURCE_AFTER47}
        cls.source = admit_console_source(cls.source_payloads[HELPER_RELATIVE_PATH].decode("utf-8"))
        cls.before_source = cls.source.removesuffix(APPEND_CONSOLE_HELPER).replace(NEW_CONDITION, OLD_CONDITION, 6)
        cls.stack = ExitStack()
        cls.addClassCleanup(cls.stack.close)
        cls.stack.enter_context(patch.object(sys, "dont_write_bytecode", True))
        action_guards(cls.stack)
        name = "nativecmpkit_camera197_owned_console_new_helper"
        require(name not in sys.modules, "The new-only helper import must be fresh")
        spec = importlib.util.spec_from_file_location(name, HELPER_PATH)
        helper = importlib.util.module_from_spec(spec)
        sys.modules[name] = helper
        cls.addClassCleanup(sys.modules.pop, name, None)
        spec.loader.exec_module(helper)
        require(Path(helper.__file__).absolute() == HELPER_PATH and helper.__spec__.origin == str(HELPER_PATH),
                "Only the exact owning helper import origin is admitted")
        cls.helper = helper

    @classmethod
    def tearDownClass(cls):
        after = {relative: read_bound_source(relative) for relative in BOUND_SOURCE_AFTER47}
        require(after == cls.source_payloads and not FORBIDDEN_ACTIONS, "A source or forbidden-action invariant changed")

    def parse(self, stdout, *, expected=NAME, stderr=b"", code=0):
        COUNTERS["new_console_parser_calls"] += 1
        return self.helper.owned_avd_console_name(completed(stdout, stderr, code), expected)

    def refuse_frame(self, payload, *, expected=NAME):
        with self.assertRaises(ValueError) as caught:
            self.parse(payload, expected=expected)
        self.assertEqual(caught.exception.args, ("Unknown owned AVD console-name frame",))

    def test_cn01_only_complete_exact_lf_and_crlf_owned_name_ok_frames_pass(self):
        name = NAME.encode()
        for frame in (name + b"\nOK\n", name + b"\r\nOK\r\n"):
            with self.subTest(frame_shape="LF" if b"\r" not in frame else "CRLF"):
                self.assertEqual(self.parse(frame), name)
        self.assertFalse(FORBIDDEN_ACTIONS)

    def test_cn02_mixed_truncated_bare_and_internal_cr_frames_refuse(self):
        name = NAME.encode()
        cases = (b"", name, name + b"\n", name + b"\nOK", name + b"\r\nOK",
                 name + b"\nOK\r\n", name + b"\r\nOK\n", name + b"\rOK\r",
                 name + b"\r\r\nOK\r\n", name + b"\nOK\r", name + b"\r\nOK\r\n\r",
                 name.replace(b"api35", b"api\r35") + b"\nOK\n")
        for index, frame in enumerate(cases):
            with self.subTest(frame_case=index):
                self.refuse_frame(frame)

    def test_cn03_extra_rows_whitespace_wrong_ack_and_unsafe_bytes_refuse(self):
        name = NAME.encode()
        frame = name + b"\nOK\n"
        cases = (b"\n" + frame, frame + b"\n", frame + b"another-row\n", name + b"\n\nOK\n",
                 name + b"\r\n\r\nOK\r\n", b" " + frame, name + b" \nOK\n", name + b"\n OK\n",
                 name + b"\nOK \n", name + b"\nok\n", name + b"\nKO\n", name + b"\nKO: error\n",
                 frame + b"\0", name + b"\nOK\t\n", name + b"\n\x1bOK\n", frame + b"\xff")
        for index, payload in enumerate(cases):
            with self.subTest(frame_case=index):
                self.refuse_frame(payload)

    def test_cn04_fixed_bounded_expected_name_and_foreign_owner_refuse(self):
        frame = NAME.encode() + b"\nOK\n"
        bad_names = (None, NAME.encode(), 35, True, "", "nativecmpkit-api34-0123456789ab",
                     "nativecmpkit-api35-0123456789a", "nativecmpkit-api35-0123456789abc",
                     "nativecmpkit-api35-0123456789AB", " " + NAME, NAME + " ", NAME + "\nOK",
                     NAME + "\r", NAME + "\0", "nativecmpkit-api35-0123456789\u00e9b")
        for index, expected in enumerate(bad_names):
            with self.subTest(name_contract_case=index):
                with self.assertRaises(ValueError) as caught:
                    self.parse(frame, expected=expected)
                self.assertEqual(caught.exception.args, ("Unknown owned AVD name contract",))
        foreign = "nativecmpkit-api35-fedcba987654"
        self.refuse_frame(frame, expected=foreign)
        self.refuse_frame(foreign.encode() + b"\r\nOK\r\n")
        for expected in ("nativecmpkit-api35-000000000000", "nativecmpkit-api35-ffffffffffff"):
            self.assertEqual(self.parse(expected.encode() + b"\r\nOK\r\n", expected=expected), expected.encode())
        class NameSubclass(str):
            pass
        with self.assertRaisesRegex(ValueError, "^Unknown owned AVD name contract$"):
            self.parse(frame, expected=NameSubclass(NAME))

    def test_cn05_original_result_exit_stderr_type_and_512_byte_cap_hold(self):
        frame = NAME.encode() + b"\r\nOK\r\n"
        cases = ((frame, b"", 1), (frame, b"console-error", 0), (frame.decode(), b"", 0),
                 (frame, "", 0), (None, b"", 0), (bytearray(frame), b"", 0),
                 (frame, None, 0), (b"a" * 513, b"", 0))
        for index, (stdout, stderr, code) in enumerate(cases):
            with self.subTest(result_contract_case=index):
                with self.assertRaises(ValueError) as caught:
                    self.parse(stdout, stderr=stderr, code=code)
                self.assertEqual(caught.exception.args, ("Unknown or unbounded explicit control result",))
        self.refuse_frame(frame + b"a" * (512 - len(frame)))
        self.refuse_frame(b"a" * 512)

    def test_cn06_console_admission_never_relaxes_the_original_scalar_gate(self):
        name = NAME.encode()
        console_frame = name + b"\r\nOK\r\n"
        self.assertEqual(self.parse(console_frame), name)
        for payload, pattern in ((console_frame, re.escape(name) + rb"\nOK"), (b"1 \r\n", rb"[01]")):
            with self.subTest(new_cross_parser_obligation=digest(payload)):
                COUNTERS["new_scalar_cross_parser_calls"] += 1
                try:
                    self.helper.line(completed(payload), 512, pattern)
                except ValueError as error:
                    self.assertEqual(error.args, ("Unknown scalar control shape",))
                    self.assertEqual(self.helper.require_call_origin(error),
                                     {"source": "android_camera_developer_prerequisite.py", "symbol": "line", "line": 242})
                else:
                    self.fail("The unchanged scalar parser unexpectedly admitted the new console frame")
        for payload in (b"1\n", b"1\r\n"):
            COUNTERS["new_scalar_cross_parser_calls"] += 1
            self.assertEqual(self.helper.line(completed(payload), 512, rb"[01]"), b"1")

    def test_cn07_six_exact_callers_keep_commands_messages_and_public_origins(self):
        before_tree, after_tree = ast.parse(self.before_source), ast.parse(self.source)
        names = [(node.name, node.lineno, node.end_lineno) for node in before_tree.body
                 if isinstance(node, (ast.FunctionDef, ast.ClassDef))]
        after_names = [(node.name, node.lineno, node.end_lineno) for node in after_tree.body
                       if isinstance(node, (ast.FunctionDef, ast.ClassDef))]
        self.assertEqual(after_names[:-1], names)
        self.assertEqual(after_names[-1], ("owned_avd_console_name", 1729, 1738))
        counts = {"action_guard": 1, "snapshot": 1, "startup_observation": 2, "post_reporter_observation": 2}
        messages = {"action_guard": "Actual AVD ownership changed before action", "snapshot": "Actual AVD name changed",
                    "startup_observation": "Actual AVD ownership changed during initial startup",
                    "post_reporter_observation": "Actual AVD ownership changed during initial startup"}
        lines = []
        for method, count in counts.items():
            node = symbol_node(after_tree, "OwnedDeveloperPrerequisite." + method)
            queries = [item for item in ast.walk(node) if isinstance(item, ast.Call) and
                       isinstance(item.func, ast.Name) and item.func.id == "owned_avd_console_name"]
            self.assertEqual(len(queries), count)
            for query in queries:
                self.assertEqual(len(query.args), 2)
                control, expected = query.args
                self.assertIsInstance(control, ast.Call)
                self.assertEqual(ast.dump(control.func), ast.dump(ast.parse("self.control", mode="eval").body))
                self.assertEqual(tuple(ast.literal_eval(arg) for arg in control.args), ("emu", "avd", "name"))
                self.assertEqual(ast.dump(expected), ast.dump(ast.parse("self.guest.name", mode="eval").body))
                lines.append(query.lineno)
                enclosing = [item for item in ast.walk(node) if isinstance(item, ast.Call) and
                             isinstance(item.func, ast.Name) and item.func.id == "require" and item.lineno == query.lineno]
                self.assertEqual(len(enclosing), 1)
                self.assertEqual(ast.literal_eval(enclosing[0].args[1]), messages[method])
        self.assertEqual(tuple(sorted(lines)), EXPECTED_QUERY_START_LINES)
        for symbol, sha256 in UNCHANGED_FUNCTION_SHA256.items():
            self.assertEqual(symbol_source(self.source, symbol), symbol_source(self.before_source, symbol))
            self.assertEqual(digest(symbol_source(self.source, symbol).encode()), sha256)
        for symbol, line, message in (("line", 242, "Unknown scalar control shape"),
                                      ("parse_settings_activity_absence", 307, "Settings Activity absence traversal is unproved"),
                                      ("OwnedDeveloperPrerequisite.close", 1375, "Original exact state was not acquired")):
            node = symbol_node(after_tree, symbol)
            matches = [item for item in ast.walk(node) if isinstance(item, ast.Call) and
                       isinstance(item.func, ast.Name) and item.func.id == "require" and item.lineno == line]
            self.assertEqual(len(matches), 1)
            self.assertEqual(ast.literal_eval(matches[0].args[1]), message)

    def test_cn08_exact_full_source_inverse_refuses_partial_and_displaced_repairs(self):
        self.assertEqual(admit_console_source(self.source), self.source)
        guarded = NEW_CONDITION + '                "Actual AVD ownership changed before action")\n'
        uid = ('        require(line(self.control("shell", "id", "-u"), 512, rb"2000") == b"2000",\n'
               '                "Shell UID changed before action; never mutate as root")\n')
        self.assertEqual(self.source.count(guarded + uid), 1)
        displaced = self.source.replace(guarded + uid, uid + guarded, 1)
        self.assertEqual(displaced.count(NEW_CONDITION), 6)
        self.assertTrue(displaced.endswith(APPEND_CONSOLE_HELPER))
        cases = (self.before_source, self.source.removesuffix(APPEND_CONSOLE_HELPER), self.source + APPEND_CONSOLE_HELPER,
                 self.source.replace(NEW_CONDITION, OLD_CONDITION, 1), self.source.replace(NEW_CONDITION, "", 1), displaced,
                 self.source.replace('require(display is not None, "Settings Activity absence traversal is unproved")',
                                     'require(True, "Settings Activity absence traversal is unproved")', 1),
                 self.source.replace('re.fullmatch(pattern + rb"(?:\\r?\\n)?", payload) is not None', 'True', 1),
                 self.source.replace('require(self.original is not None, "Original exact state was not acquired")',
                                     'require(True, "Original exact state was not acquired")', 1),
                 self.source.replace('def control(self, *arguments: str, timeout=10,',
                                     'def control(self, *arguments: str, timeout=11,', 1),
                 self.source + "\n", None, self.source.encode())
        for index, candidate in enumerate(cases):
            with self.subTest(source_contract_case=index):
                self.assertNotEqual(candidate, self.source)
                with self.assertRaises(ValueError):
                    admit_console_source(candidate)
                COUNTERS["source_admission_refusals"] += 1

    def test_cn09_owning194_and_operational_native_bindings_are_not_rebased(self):
        self.assertEqual(len(BOUND_SOURCE_BEFORE47), 47)
        self.assertEqual(set(BOUND_SOURCE_BEFORE47), set(BOUND_SOURCE_AFTER47))
        self.assertEqual(set(CAMERA205_DERIVATIVE_SOURCE_SHA256), {
            "scripts/ci/camera_scalar_failfast_source_projection.py",
            "scripts/ci/test_android_camera_pre_reporter_fail_fast.py",
            "scripts/ci/test_android_camera_scalar_control_refusal.py",
        })
        self.assertEqual({relative for relative in BOUND_SOURCE_BEFORE47
                          if BOUND_SOURCE_BEFORE47[relative] != BOUND_SOURCE_AFTER47[relative]},
                         {HELPER_RELATIVE_PATH} | set(CAMERA205_DERIVATIVE_SOURCE_SHA256) |
                         set(CAMERA205_SHARE188_SHARED_SOURCE_SHA256) |
                         set(CAMERA213_DERIVATIVE_SOURCE_SHA256))
        self.assertEqual({relative: BOUND_SOURCE_AFTER47[relative]
                          for relative in CAMERA205_DERIVATIVE_SOURCE_SHA256},
                         {**CAMERA205_DERIVATIVE_SOURCE_SHA256, **CAMERA224_DERIVATIVE_SOURCE_SHA256})
        self.assertEqual(set(CAMERA224_DERIVATIVE_SOURCE_SHA256), {
            "scripts/ci/test_android_camera_pre_reporter_fail_fast.py"})
        self.assertEqual(set(CAMERA205_SHARE188_SHARED_SOURCE_SHA256), {
            ".github/workflows/gradle.yml", "scripts/ci/library_tests.py"})
        self.assertEqual({relative: BOUND_SOURCE_AFTER47[relative]
                          for relative in CAMERA205_SHARE188_SHARED_SOURCE_SHA256},
                         CAMERA205_SHARE188_SHARED_SOURCE_SHA256)
        self.assertEqual(set(CAMERA213_DERIVATIVE_SOURCE_SHA256), {
            "scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py",
            "scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py",
            "scripts/ci/test_android_camera_startup_readiness.py",
        })
        self.assertEqual({relative: BOUND_SOURCE_AFTER47[relative]
                          for relative in CAMERA213_DERIVATIVE_SOURCE_SHA256},
                         CAMERA213_DERIVATIVE_SOURCE_SHA256)
        from camera_ci213_source_projection import historical_source_before_camera213
        # Instance-local historical view: never mutate the held class/current map.
        current_payloads = self.source_payloads
        self.source_payloads = {
            **current_payloads,
            **{relative: historical_source_before_camera213(relative, current_payloads[relative])
               for relative in CAMERA213_DERIVATIVE_SOURCE_SHA256},
        }
        self.addCleanup(delattr, self, "source_payloads")
        for relative in ("scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py",
                         "scripts/ci/test_android_camera_startup_readiness.py"):
            self.assertEqual(digest(self.source_payloads[relative]), BOUND_SOURCE_BEFORE47[relative])
        prefix = self.source_payloads["scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py"].decode().splitlines()
        startup = self.source_payloads["scripts/ci/test_android_camera_startup_readiness.py"].decode().splitlines()
        for row in (prefix[146], prefix[298], startup[365]):
            self.assertIn('"line": 307', row)
        driver = ast.parse(self.source_payloads["scripts/ci/run_android_camera_scalar_failfast_new_only.py"])
        assignments = [node for node in driver.body if isinstance(node, ast.Assign) and
                       any(isinstance(target, ast.Name) and target.id == "EXPECTED_SOURCE_SHA256" for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        old_pins = ast.literal_eval(assignments[0].value)
        self.assertEqual(len(old_pins), 46)
        self.assertEqual(old_pins[HELPER_RELATIVE_PATH], BEFORE_HELPER_SHA256)
        for relative, sha256 in old_pins.items():
            self.assertEqual(sha256, BOUND_SOURCE_BEFORE47[relative])
        for relative in ("scripts/ci/android_device_tests.py", ".github/workflows/gradle.yml",
                         "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt"):
            with self.subTest(unchanged_binding=relative):
                with self.assertRaises(ValueError):
                    admit_bound_payload(relative, self.source_payloads[relative] + b"\n")
                COUNTERS["binding_refusals"] += 1
        self.assertEqual(COUNTERS["existing_accepted_test_methods_selected"], 0)
        self.assertEqual(COUNTERS["native_invocations"], 0)
        self.assertFalse(FORBIDDEN_ACTIONS)
