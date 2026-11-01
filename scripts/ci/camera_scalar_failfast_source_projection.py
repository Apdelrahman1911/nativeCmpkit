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
