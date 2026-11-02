"""Exact full-source historical controller projection for inert owning fixtures only.

The old fixture methods retain their old setup order. They do not qualify the
new sole-C1 order, which has separately declared new-only source controls.
Production does not import this module. No source or policy gate is weakened.
"""
from pathlib import Path
import hashlib
import json

CONTROLLER_INVERSE_SHA256 = "9a3479f92b05e1bffda3b408ad9f5833ca655b0c913af813e888209de9b2828c"


def historical_controller_source(source: str) -> str:
    path = Path(__file__).parent / "fixtures/android-camera-scalar-failfast-controller-inverse.json"
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != CONTROLLER_INVERSE_SHA256:
        raise AssertionError("Exact owning compiler-boundary controller inverse is changed")
    contract = json.loads(payload)
    from android_external328_source_projection import text_before_android_external328
    try:
        source = text_before_android_external328("scripts/ci/android_device_tests.py", source)
    except (ValueError, UnicodeError) as error:
        raise AssertionError("Full current controller bytes differ from the qualified afterimage") from error
    if type(source) is not str or hashlib.sha256(source.encode()).hexdigest() != contract["after_sha256"]:
        raise AssertionError("Full current controller bytes differ from the qualified afterimage")
    restored = source
    for fragment in contract["inverse_fragments"]:
        if restored.count(fragment["new"]) != 1:
            raise AssertionError("Exact historical controller inverse is missing or ambiguous")
        restored = restored.replace(fragment["new"], fragment["old"], 1)
    if hashlib.sha256(restored.encode()).hexdigest() != contract["before_sha256"]:
        raise AssertionError("Full historical controller bytes were not exactly restored")
    return restored


# Camera197 is an outer exact helper inverse, never a historical hash rebase.
CAMERA197_BEFORE_HELPER_SHA256 = 'da07bedb680e9ce36842bbf581f22bf7b3ebf8ab1c5d307b05745069c77bb5a4'
CAMERA197_AFTER_HELPER_SHA256 = '0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26'
CAMERA197_SOURCE_BYTES = 4194304
CAMERA197_OLD_CONDITION = '        require(line(self.control("emu", "avd", "name"), 512,\n                     re.escape(self.guest.name.encode()) + rb"\\nOK") == self.guest.name.encode() + b"\\nOK",\n'
CAMERA197_NEW_CONDITION = '        require(owned_avd_console_name(self.control("emu", "avd", "name"), self.guest.name)\n                == self.guest.name.encode(),\n'
CAMERA197_APPEND_HELPER = '\n\ndef owned_avd_console_name(result: subprocess.CompletedProcess, expected_name: str) -> bytes:\n    """Exact owned console name/OK framing only; never a general scalar normalization."""\n    require(type(expected_name) is str and\n            re.fullmatch(r"nativecmpkit-api35-[a-f0-9]{12}", expected_name) is not None,\n            "Unknown owned AVD name contract")\n    name = expected_name.encode("ascii")\n    payload = result_bytes(result, 512)\n    require(payload in (name + b"\\nOK\\n", name + b"\\r\\nOK\\r\\n"),\n            "Unknown owned AVD console-name frame")\n    return name\n'


def camera197_helper_source_before_owned_console(source: str) -> str:
    """Undo only the exact Camera197 full afterimage before older inverse chains."""
    if type(source) is not str or not 0 < len(source) <= CAMERA197_SOURCE_BYTES:
        raise AssertionError("An exact bounded Camera197 helper source is required")
    try:
        payload = source.encode("utf-8")
    except UnicodeError as error:
        raise AssertionError("An exact bounded Camera197 helper source is required") from error
    if len(payload) > CAMERA197_SOURCE_BYTES or hashlib.sha256(payload).hexdigest() != CAMERA197_AFTER_HELPER_SHA256:
        raise AssertionError("Full current Camera197 helper bytes differ from the qualified afterimage")
    if not source.endswith(CAMERA197_APPEND_HELPER):
        raise AssertionError("The exact late Camera197 console helper suffix is required")
    restored = source.removesuffix(CAMERA197_APPEND_HELPER)
    if restored.count(CAMERA197_NEW_CONDITION) != 6 or CAMERA197_OLD_CONDITION in restored:
        raise AssertionError("All six exact Camera197 caller substitutions are required")
    restored = restored.replace(CAMERA197_NEW_CONDITION, CAMERA197_OLD_CONDITION, 6)
    if (hashlib.sha256(restored.encode("utf-8")).hexdigest() != CAMERA197_BEFORE_HELPER_SHA256 or
            restored.count(CAMERA197_OLD_CONDITION) != 6 or
            restored.replace(CAMERA197_OLD_CONDITION, CAMERA197_NEW_CONDITION, 6) + CAMERA197_APPEND_HELPER != source):
        raise AssertionError("Full original Camera197 helper bytes and exact forward roundtrip were not restored")
    return restored
