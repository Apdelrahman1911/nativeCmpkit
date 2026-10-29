"""Finite restoring CoreSimulator UI driver; no shell, window override or transcript.

The owning native transport must first bind/verify the exact booted simulator.
This is a test fixture, not a process sandbox or physical-device certification.
"""
from __future__ import annotations

import re
import subprocess
from collections.abc import Callable

STYLES = ("light", "dark")
REQUESTS = ((1, "dark"), (2, "light"))
UUID = re.compile(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}\Z")


class AppearanceDriver:
    def __init__(self, device: str, control: Callable[..., subprocess.CompletedProcess]):
        if not UUID.fullmatch(device):
            raise ValueError("Use the exact preflight-recorded simulator")
        self.device = device
        self.control = control
        self.initial = None
        self.last = None
        self.candidates = set()
        self.receipt = {"schema_version": 1, "simulator_udid": device,
                        "uses_window_override": False, "prepared_light": False,
                        "initial_style": None, "steps": [], "controls": [],
                        "restored": False, "physical_settings_verified": False}

    def _control(self, style: str | None = None) -> subprocess.CompletedProcess:
        if style is not None and style not in STYLES:
            raise ValueError("Unknown finite system appearance")
        argv = ["/usr/bin/xcrun", "simctl", "ui", self.device, "appearance"]
        if style is not None:
            argv.append(style)
        result = self.control(argv, 30)
        if type(result.returncode) is not int:
            raise ValueError("Missing actual CoreSimulator command exit")
        self.receipt["controls"].append({"command": argv, "timeout_seconds": 30,
                                         "exit_code": result.returncode})
        if result.returncode:
            raise RuntimeError("CoreSimulator appearance control failed")
        return result

    def _query(self) -> str:
        result = self._control()
        if not isinstance(result.stdout, bytes) or len(result.stdout) > 128:
            raise ValueError("Invalid or unbounded appearance query")
        style = result.stdout.decode("utf-8", errors="strict").strip()
        if style not in STYLES:
            raise ValueError("Unknown actual simulator system appearance")
        self.receipt["controls"][-1]["observed_style"] = style
        return style

    def _set(self, style: str) -> None:
        self.candidates.add(style)  # Reconcile an uncertain failed command during cleanup.
        self._control(style)
        actual = self._query()
        if actual != style:
            raise ValueError("System appearance change did not read back")
        self.last = actual

    def start(self) -> None:
        if self.initial is not None:
            raise ValueError("Refuse repeated appearance preparation")
        self.initial = self._query()
        self.last = self.initial
        self.candidates.add(self.initial)
        self.receipt["initial_style"] = self.initial
        if self.initial != "light":
            self._set("light")
        self.receipt["prepared_light"] = self._query() == "light"
        if not self.receipt["prepared_light"]:
            raise ValueError("Actual initial light system appearance is unverified")

    def request(self, step: int, style: str) -> None:
        index = len(self.receipt["steps"])
        if (not self.receipt["prepared_light"] or self.receipt["restored"] or
                type(step) is not int or index >= len(REQUESTS) or (step, style) != REQUESTS[index]):
            raise ValueError("Missing, repeated or foreign native appearance request")
        before = self._query()
        if before != self.last or before == style:
            raise ValueError("Appearance ownership changed or requested transition is absent")
        self._set(style)
        self.receipt["steps"].append({"step": step, "style": style,
                                      "before_style": before, "after_style": self.last,
                                      "set_exit_code": 0, "readback_verified": True})

    def restore(self) -> None:
        if self.receipt["restored"]:
            return  # No repeated control mutation after a verified cleanup.
        if self.initial is None:
            return  # No query/lease established, therefore no mutation is authorized.
        before = self._query()
        if before not in self.candidates:
            raise ValueError("Refuse restoring an unknown simulator appearance")
        if before != self.initial:
            self._set(self.initial)
        after = self._query()
        self.receipt["restore_before_style"] = before
        self.receipt["restored_style"] = after
        self.receipt["restored"] = after == self.initial
        if not self.receipt["restored"]:
            raise ValueError("Original simulator appearance is not restored")


def validate_receipt(document: dict, device: str) -> bool:
    """Pure structural contract. A fixture receipt is not an actual native pass."""
    if not isinstance(document, dict) or not UUID.fullmatch(device):
        return False
    if (type(document.get("schema_version")) is not int or document["schema_version"] != 1 or
            document.get("simulator_udid") != device or document.get("uses_window_override") is not False or
            document.get("physical_settings_verified") is not False or document.get("prepared_light") is not True or
            document.get("restored") is not True or document.get("initial_style") not in STYLES or
            document.get("restored_style") != document.get("initial_style") or "error_type" in document):
        return False
    expected = [{"step": step, "style": style, "before_style": "light" if step == 1 else "dark",
                 "after_style": style, "set_exit_code": 0, "readback_verified": True}
                for step, style in REQUESTS]
    steps = document.get("steps")
    if (steps != expected or document.get("restore_before_style") != "light" or
            any(type(row.get("step")) is not int or type(row.get("set_exit_code")) is not int or
                row.get("readback_verified") is not True for row in steps)):
        return False
    controls = document.get("controls")
    base = ["/usr/bin/xcrun", "simctl", "ui", device, "appearance"]
    # Bind every query/set/readback in order, not merely two claimed step rows.
    initial = document["initial_style"]
    sequence = ([(None, "light"), (None, "light")] if initial == "light" else
                [(None, "dark"), ("light", None), (None, "light"), (None, "light")])
    sequence += [(None, "light"), ("dark", None), (None, "dark"),
                 (None, "dark"), ("light", None), (None, "light")]
    sequence += ([(None, "light"), (None, "light")] if initial == "light" else
                 [(None, "light"), ("dark", None), (None, "dark"), (None, "dark")])
    if not isinstance(controls, list) or len(controls) != len(sequence):
        return False
    for row, (requested, observed) in zip(controls, sequence):
        if (not isinstance(row, dict) or type(row.get("exit_code")) is not int or row["exit_code"] != 0 or
                type(row.get("timeout_seconds")) is not int or row["timeout_seconds"] != 30):
            return False
        if row.get("command") != base + ([] if requested is None else [requested]):
            return False
        if (observed is None and "observed_style" in row or
                observed is not None and row.get("observed_style") != observed):
            return False
    return True
