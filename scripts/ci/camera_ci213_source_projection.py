"""CI213 current-source admission for retained camera source-control history only.

Not used by production/native runners. Whole current and historical byte hashes,
unique fragments and a forward round-trip are mandatory; no arbitrary fallback.
"""
from __future__ import annotations
import hashlib

REPAIRS = {
    "scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py": {
        "before_sha256": "bd539b328cdf586cca655b7a34e5006f7417ee21724308f906fa1d5199d4224e",
        "after_sha256": "048b40f6976fc6af2160c9934b39d620bbdac466d912edfbb9e315dfa92f8bf7",
        "fragments": [
            {
                "before": "def pre_startup_helper_source(source: str) -> str:\n    \"\"\"Normalize only the pinned exact initial-readiness fragments, never an AST.\"\"\"\n    contract_path = Path(__file__).parent / \"fixtures/android-camera-startup-readiness-inverse.json\"\n    payload = contract_path.read_bytes()\n    if hashlib.sha256(payload).hexdigest() != STARTUP_INVERSE_SHA256:\n        raise AssertionError(\"Exact owning startup-inverse fixture is changed\")\n    contract = json.loads(payload)\n    if type(source) is not str or hashlib.sha256(source.encode()).hexdigest() != contract[\"after_sha256\"]:\n        raise AssertionError(\"Full current helper bytes differ from the qualified afterimage\")\n    restored = source\n    for fragment in contract[\"inverse_fragments\"]:\n        if restored.count(fragment[\"new\"]) != 1:\n            raise AssertionError(\"The exact owning startup inverse is missing or ambiguous\")\n        restored = restored.replace(fragment[\"new\"], fragment[\"old\"], 1)\n    if hashlib.sha256(restored.encode()).hexdigest() != contract[\"before_sha256\"]:\n        raise AssertionError(\"Full pre-startup helper bytes were not exactly restored\")\n    return restored",
                "after": "def pre_startup_helper_source(source: str) -> str:\n    \"\"\"Normalize only the pinned exact initial-readiness fragments, never an AST.\"\"\"\n    contract_path = Path(__file__).parent / \"fixtures/android-camera-startup-readiness-inverse.json\"\n    payload = contract_path.read_bytes()\n    if hashlib.sha256(payload).hexdigest() != STARTUP_INVERSE_SHA256:\n        raise AssertionError(\"Exact owning startup-inverse fixture is changed\")\n    contract = json.loads(payload)\n    # CI213: the exact owned-console repair precedes the untouched startup inverse.\n    from camera_scalar_failfast_source_projection import camera197_helper_source_before_owned_console\n    try:\n        source = camera197_helper_source_before_owned_console(source)\n    except AssertionError as error:\n        raise AssertionError(\"Full current helper bytes differ from the qualified afterimage\") from error\n    if type(source) is not str or hashlib.sha256(source.encode()).hexdigest() != contract[\"after_sha256\"]:\n        raise AssertionError(\"Full current helper bytes differ from the qualified afterimage\")\n    restored = source\n    for fragment in contract[\"inverse_fragments\"]:\n        if restored.count(fragment[\"new\"]) != 1:\n            raise AssertionError(\"The exact owning startup inverse is missing or ambiguous\")\n        restored = restored.replace(fragment[\"new\"], fragment[\"old\"], 1)\n    if hashlib.sha256(restored.encode()).hexdigest() != contract[\"before_sha256\"]:\n        raise AssertionError(\"Full pre-startup helper bytes were not exactly restored\")\n    return restored"
            }
        ]
    },
    "scripts/ci/test_android_camera_startup_readiness.py": {
        "before_sha256": "056711d56c8cdf02866d2d013be34be2e2dc90b6bc197ea7c046c6c488fb5c86",
        "after_sha256": "239bbde00bd8deb728119aa2d76395f4e01615ab25092a3fe2a6dd57f8a274bf",
        "fragments": [
            {
                "before": "EXPECTED_INPUT_SHA256 = {'scripts/ci/android_camera_developer_prerequisite.py': 'da07bedb680e9ce36842bbf581f22bf7b3ebf8ab1c5d307b05745069c77bb5a4', 'scripts/ci/test_android_camera_developer_prerequisite.py': '4a78c909420383a59cb453c1ca58ab3c0ca909a08f17201ddc0bcea657a061bb', 'scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py': 'bd539b328cdf586cca655b7a34e5006f7417ee21724308f906fa1d5199d4224e', 'scripts/ci/fixtures/android-camera-startup-readiness-inverse.json': '43a8963e59a7851e968fbbeeaafa19944956cbc6a6f0b5cb8924a4dba0342e2c', 'scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json': 'e7b0e9a3e361e39d1732ed33cd5e1d4e51a3e30ed377adf487001b742754c953'}",
                "after": "EXPECTED_INPUT_SHA256 = {'scripts/ci/android_camera_developer_prerequisite.py': '0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26', 'scripts/ci/test_android_camera_developer_prerequisite.py': '4a78c909420383a59cb453c1ca58ab3c0ca909a08f17201ddc0bcea657a061bb', 'scripts/ci/test_android_camera_settings_activity_refusal_diagnostics.py': '048b40f6976fc6af2160c9934b39d620bbdac466d912edfbb9e315dfa92f8bf7', 'scripts/ci/fixtures/android-camera-startup-readiness-inverse.json': '43a8963e59a7851e968fbbeeaafa19944956cbc6a6f0b5cb8924a4dba0342e2c', 'scripts/ci/fixtures/android-camera-settings-absence-observation-inverse.json': 'e7b0e9a3e361e39d1732ed33cd5e1d4e51a3e30ed377adf487001b742754c953'}"
            }
        ]
    },
    "scripts/ci/test_android_camera_settings_activity_reference_prefix_diagnostics.py": {
        "before_sha256": "09fcbc6e7b9af1e6cac0cfcd3feae048a5d8e3a5d10b49a222b534f2aa0874df",
        "after_sha256": "9c2ee35603ccc5c30a49fd91d438fa88584386637bb550ab2557d44760d1bbe5",
        "fragments": [
            {
                "before": "EXPECTED_HELPER_SHA256 = \"da07bedb680e9ce36842bbf581f22bf7b3ebf8ab1c5d307b05745069c77bb5a4\"",
                "after": "EXPECTED_HELPER_SHA256 = '0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26'"
            },
            {
                "before": "EXPECTED_GUARD_SHA256 = \"bd539b328cdf586cca655b7a34e5006f7417ee21724308f906fa1d5199d4224e\"",
                "after": "EXPECTED_GUARD_SHA256 = '048b40f6976fc6af2160c9934b39d620bbdac466d912edfbb9e315dfa92f8bf7'"
            }
        ]
    }
}


def historical_source_before_camera213(relative: str, payload: bytes) -> bytes:
    if type(relative) is not str or relative not in REPAIRS or type(payload) is not bytes:
        raise ValueError("An exact owning CI213 source identity and bytes are required")
    binding = REPAIRS[relative]
    if not 0 < len(payload) <= 4 * 1024 * 1024 or hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("Full current CI213 source differs from the qualified postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if restored.count(after) != 1:
            raise ValueError("The exact unique CI213 owning inverse is required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("The original complete CI213 source was not restored")
    roundtrip = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if roundtrip.count(before) != 1:
            raise ValueError("The exact unique CI213 forward fragment is required")
        roundtrip = roundtrip.replace(before, after, 1)
    if roundtrip != payload:
        raise ValueError("The exact CI213 forward round-trip was not restored")
    return restored
