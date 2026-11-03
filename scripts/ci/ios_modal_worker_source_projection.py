# SPDX-License-Identifier: Apache-2.0
"""Exact iOS modal Worker/startup recovery source history, offline readers only.

No native selector imports this inverse, no old pin is refreshed, and no
historical image may replace current source. Full-byte and fragment custody.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

import ios_modal_fixture_reader_projection as fixture_history
import ios_sheet_repeat_source_projection as repeat_history

SPEC_PATH = Path(__file__).parent / "fixtures/ios-modal-worker-source-inverse.json"
SPEC_SHA256 = '8a1f2c4b0f418b9aab96f9d3c8f615acff5efce31fe457886204559fd2448d48'
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024

# Additive exact one-line project-scope repair; the original six/23 manifest is
# immutable. These offline bytes are never used by the native input runner.
XCTEST_PROJECT_SCOPE = {
    "source": "scripts/ci/native_ui_input.py",
    "before_sha256": "a2e95e28f79cf540cfd19351458168ff9cda555bebafe713ae30822fd8b729a5",
    "after_sha256": "7da8c5a573db7730d364b0ced92f649e6bf5d3ec0f84a3726e5855f2d240e77c",
    "before": '        derived = self.scratch / "derived"\n',
    "after": '        project_root = self.scratch / "project"\n        derived = self.scratch / "derived"\n',
    "before_fragment_sha256": "01aa5294e4dca382d787738b57ea61d75fc08a7d1217aeb02be7293179035041",
    "after_fragment_sha256": "5b2d4368c3c0447275607d39c4a382e5605848a1a7d1c4908ddb16848b2fd25a",
}


def source_before_xctest_project_scope(relative, payload, *, current=False):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact iOS modal Worker/startup project source identity and ordinary bytes are required")
    binding = XCTEST_PROJECT_SCOPE
    if relative != binding["source"]:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded iOS modal Worker/startup project source required")
    observed = hashlib.sha256(payload).hexdigest()
    if not current and observed == binding["before_sha256"]:
        return payload
    if observed != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current iOS modal Worker/startup project source")
    before, after = binding["before"].encode(), binding["after"].encode()
    if (hashlib.sha256(before).hexdigest() != binding["before_fragment_sha256"] or
            hashlib.sha256(after).hexdigest() != binding["after_fragment_sha256"] or
            payload.count(after) != 1):
        raise ValueError("Exact unique iOS modal Worker/startup project inverse required")
    restored = payload.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"] or restored.count(before) != 1:
        raise ValueError("Complete original iOS modal Worker/startup project source required")
    if restored.replace(before, after, 1) != payload:
        raise ValueError("Exact iOS modal Worker/startup project round-trip required")
    return restored


def _bindings():
    info = SPEC_PATH.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_SPEC_BYTES:
        raise ValueError("An ordinary bounded exact iOS modal Worker/startup recovery manifest is required")
    raw = SPEC_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact iOS modal Worker/startup recovery manifest changed")
    document = json.loads(raw)
    if document["schema_version"] != 1 or type(document["bindings"]) is not dict:
        raise ValueError("The exact iOS modal Worker/startup recovery manifest schema is required")
    return document["bindings"]


def source_before_modal_worker(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact iOS modal Worker/startup recovery source identity and ordinary bytes are required")
    binding = _bindings().get(relative)
    # Preserve this stage's complete preimage idempotence before the additive
    # project repair. The current reader below never uses this shortcut.
    if binding is not None and hashlib.sha256(payload).hexdigest() == binding["before_sha256"]:
        return payload
    payload = repeat_history.source_before_sheet_repeat(relative, payload)
    payload = source_before_xctest_project_scope(relative, payload)
    payload = fixture_history.source_before_worker_fixture_reader(relative, payload)
    if binding is None:
        return payload
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded iOS modal Worker/startup recovery source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"]:
        return payload
    if observed != binding["after_sha256"]:
        raise ValueError("Unreviewed iOS modal Worker/startup recovery source is not an admitted postimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique iOS modal Worker/startup recovery inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("iOS modal Worker/startup recovery inverse did not restore the complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique iOS modal Worker/startup recovery forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("iOS modal Worker/startup recovery round-trip differs from the actual current bytes")
    return restored


def current_source_before_modal_worker(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact current iOS modal Worker/startup recovery source identity and ordinary bytes are required")
    payload = repeat_history.current_source_before_sheet_repeat(relative, payload)
    payload = source_before_xctest_project_scope(relative, payload, current=True)
    payload = fixture_history.current_source_before_worker_fixture_reader(relative, payload)
    binding = _bindings().get(relative)
    if binding is not None and hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("A historical image cannot replace the exact current iOS modal Worker/startup recovery source")
    return source_before_modal_worker(relative, payload)
