"""Exact Wasm selection-reporter delta qualification for source guards only.

This helper is not a native/loader fallback. It requires the sole qualified new
reporter and reconstructs the accepted whole childBootstrap bytes, preserving the
original b1b0d9d6 pin. Marker descriptor bits are shape checks, NOT exclusive origin
or ownership authentication: same-bit replacement is indistinguishable.
"""
import hashlib

ORIGINAL_FIXTURE_SHA256 = "0f4ed3ca16c41bbc9d314a504f691810c4d8787c91ec31b03f0ddf3c005c7d41"
QUALIFIED_FIXTURE_SHA256 = "347953a8c9596091c3923a37f564b51a7cd7f6488169718222ffe7c6c99e53c8"
ACCEPTED_CHILD_BOOTSTRAP_SHA256 = "b1b0d9d6e0f1cee9c45176872f849f1e23436c668a6c9afc6ed2703ce0608e18"
QUALIFIED_CHILD_BOOTSTRAP_SHA256 = "46db87a759ac882a71d0611b7ede5734ff0e8c98c0d4e09dc0299041fbf544ca"
# Exact five fixture literals from the independently reviewed six-fragment
# proposal; the sixth is a mechanical owning fixture pin, not executable logic.
DIAGNOSTIC_DELTAS = (
    ("    const sendFailure = error => {\n      const name = String(error && error.name || 'fixture').replace(/[^A-Za-z0-9._-]/g, '?').slice(0, 40);\n      const message = String(error && error.message || 'fixture-failure').replace(/[^A-Za-z0-9 .():=-]/g, '?').slice(0, 160);",
     "    const sendFailure = error => {\n      const name = String(error && error.name || 'fixture').replace(/[^A-Za-z0-9._-]/g, '?').slice(0, 40);\n      // This exact Wasm-owned marker enables bounded state, never suite names or emitted values.\n      const marker = Object.getOwnPropertyDescriptor(h, 'wasmSelectionDiagnostic');\n      let diagnostic = '';\n      if (marker && marker.value === true && marker.writable === false && marker.enumerable === false &&\n          marker.configurable === true && error instanceof Error &&\n          error.message === 'Exact emitted native test method is missing/reused') {\n        const count = value => Number.isSafeInteger(value) && value >= 0 && value <= 16 ? String(value) : 'outside';\n        diagnostic = ' (wasm selectedType=' + typeof selected + ' selections=' + count(selections) +\n          ' invocations=' + count(invocations) + ')';\n      }\n      const message = (String(error && error.message || 'fixture-failure') + diagnostic).replace(/[^A-Za-z0-9 .():=-]/g, '?').slice(0, 160);"),
    ("      if (!h || h.cleaned || typeof restore !== 'function' || typeof boot !== 'function' || '__karma__' in window) {",
     "      if (!h || h.cleaned || typeof restore !== 'function' || typeof boot !== 'function' || '__karma__' in window ||\n          'wasmSelectionDiagnostic' in h) {"),
    ('      const assertReady = () => {\n        if (failed || loaded !== 1 || window.__karma__ !== karma || window.__nativecmpkitClipboardNative !== h) {',
     "      const assertReady = () => {\n        const marker = Object.getOwnPropertyDescriptor(h, 'wasmSelectionDiagnostic');\n        if (failed || loaded !== 1 || window.__karma__ !== karma || window.__nativecmpkitClipboardNative !== h ||\n            !marker || marker.value !== true || marker.writable !== false || marker.enumerable !== false ||\n            marker.configurable !== true) {"),
    ("        if ('__karma__' in window) throw new Error('Owning Wasm loader hook removal failed');\n        window.__nativecmpkitClipboardBoot = boot;",
     "        if ('__karma__' in window) throw new Error('Owning Wasm loader hook removal failed');\n        delete h.wasmSelectionDiagnostic;\n        if ('wasmSelectionDiagnostic' in h) throw new Error('Owning Wasm selection diagnostic removal failed');\n        window.__nativecmpkitClipboardBoot = boot;"),
    ('      window.__karma__ = karma;\n      window.__nativecmpkitClipboardBoot = ownedBoot;\n      h.restore = ownedRestore;',
     "      Object.defineProperty(h, 'wasmSelectionDiagnostic', { value: true, configurable: true });\n      window.__karma__ = karma;\n      window.__nativecmpkitClipboardBoot = ownedBoot;\n      h.restore = ownedRestore;"),
)


def original_js_child_bootstrap_from_diagnostic(block: str) -> str:
    """Remove only the exact qualified reporter delta; never admit a source drift."""
    if type(block) is not str:
        raise ValueError("Exact qualified childBootstrap text is required")
    before, after = DIAGNOSTIC_DELTAS[0]
    if block.count(after) != 1 or before in block:
        raise ValueError("Exactly one qualified selection reporter delta is required")
    restored = block.replace(after, before, 1)
    if (hashlib.sha256(block.encode()).hexdigest() != QUALIFIED_CHILD_BOOTSTRAP_SHA256 or
            hashlib.sha256(restored.encode()).hexdigest() != ACCEPTED_CHILD_BOOTSTRAP_SHA256):
        raise ValueError("Only the exact reporter delta may alter accepted childBootstrap bytes")
    return restored


def original_fixture_from_diagnostic(source: str) -> str:
    """Qualify all five fixture deltas without executing any JS/native function."""
    if type(source) is not str or hashlib.sha256(source.encode()).hexdigest() != QUALIFIED_FIXTURE_SHA256:
        raise ValueError("Exact qualified diagnostic fixture is required")
    restored = source
    for before, after in reversed(DIAGNOSTIC_DELTAS):
        if restored.count(after) != 1:
            raise ValueError("Each exact diagnostic delta must occur once")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored.encode()).hexdigest() != ORIGINAL_FIXTURE_SHA256:
        raise ValueError("Diagnostic inverse must preserve the entire original fixture")
    return restored
