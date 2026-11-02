"""Exact resource/all-caps label derivative for the API35 English UI fixture.

The genuine Google DocumentsUI observation in run41498732953 identifies one
enabled, clickable button with the resource label rendered in uppercase. This
is not generic ignore-case, substring, guessed-label or permission admission.
Historical source bridges retain their original native/safety obligations.
"""
from __future__ import annotations

REFUSAL = "System UI ownership, exact controls, ambiguity refusal or flag restoration changed"
DELTAS = (
    (
        '        val pickLabel = stringResource("open_tree_button")\n',
        '        val pickLabel = stringResource("open_tree_button")\n'
        '        // TextView allCaps changes accessibility text, not the installed resource string.\n'
        '        // This fixture requires English; accept only the exact resource or its exact rendering.\n'
        '        val renderedPickLabel = pickLabel.uppercase(java.util.Locale.ENGLISH)\n',
    ),
    (
        '            it.text?.toString() == pickLabel && it.isEnabled && it.isClickable\n',
        '            (it.text?.toString() == pickLabel || it.text?.toString() == renderedPickLabel) &&\n'
        '                it.isEnabled && it.isClickable\n',
    ),
    (
        '        val allowLabel = stringResource("allow")\n',
        '        val allowLabel = stringResource("allow")\n'
        '        val renderedAllowLabel = allowLabel.uppercase(java.util.Locale.ENGLISH)\n',
    ),
    (
        '            it.text?.toString() == allowLabel && it.isEnabled && it.isClickable\n',
        '            (it.text?.toString() == allowLabel || it.text?.toString() == renderedAllowLabel) &&\n'
        '                it.isEnabled && it.isClickable\n',
    ),
)
MARKERS = ("renderedPickLabel", "renderedAllowLabel")


def require(condition: bool) -> None:
    if not condition:
        raise ValueError(REFUSAL)


def rendering_present(value: str) -> bool:
    return isinstance(value, str) and any(marker in value for marker in MARKERS)


def rendering_preimage(current: str) -> str:
    """Require the full exact derivative; never repair an edited native guard."""
    require(type(current) is str)
    original = current
    for before, after in reversed(DELTAS):
        require(original.count(after) == 1)
        original = original.replace(after, before, 1)
    require(not rendering_present(original))
    expected = original
    for before, after in DELTAS:
        require(expected.count(before) == 1)
        expected = expected.replace(before, after, 1)
    require(expected == current)
    return original


def rendering_postimage(original: str) -> str:
    """Exact valid-source bridge only, not a native UI or grant receipt."""
    require(type(original) is str and not rendering_present(original))
    current = original
    for before, after in DELTAS:
        require(current.count(before) == 1)
        current = current.replace(before, after, 1)
    require(rendering_preimage(current) == original)
    return current


def rendering_fixture_postimage(original: str) -> str:
    """Overlay only exact old fragments; deliberately malformed guards survive.

    Legacy mutation fixtures are not source admission. If a predicate/declaration
    was edited, do not overwrite it to a valid one: the live contract must refuse
    the resulting partial derivative. Duplicate fragments are retained too.
    """
    require(type(original) is str and not rendering_present(original))
    current = original
    for before, after in DELTAS:
        if current.count(before) == 1:
            current = current.replace(before, after, 1)
    return current
