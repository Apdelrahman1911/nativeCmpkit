# ADR 0011: independent supported-tool Apple memory verification

- Status: accepted for **contained verification**, not release clearance
- Date: 2026-10-30

## Evidence and constraint

[40989310808](../development/evidence/image-memory-batch-important-20261030/native-ci002/README.md)
at `35b266c8` successfully compiles/links, then aborts before UIApplication
activation under the opt-in strict Kotlin/Native test-binary settings. The actual
assertion is in Objective-C protocol registration during Compose accessibility
initialization. The exact offending class/protocol is not known. No image method,
GC stress or Instruments profile executed. ASan flags on this exact compiler/Apple
target warn and disable rather than enabling a usable sanitizer.

These results must remain failed. They do not prove that default production
startup crashes, that the library image converter caused the abort, or that
Darwin/Instruments/leaks diagnostics cannot operate independently.

## Decision

Keep **`ios-image-memory` unchanged in meaning**: its command still requests
`nativecmpkitImageMemoryDiagnostics=true`; only that test-binary mode sets
`runtimeAssertionsMode=panic` and `checkStateAtExternalCalls=true`. Do not rerun
it unchanged, override its assertions, patch third-party runtime or downgrade
dependencies merely for a green result.

Add a **separate** finite `ios-image-memory-darwin` / `darwin-tools` request for
the **same three unchanged library memory methods** on the default Kotlin native
binary settings. It requests the existing actual process Malloc diagnostics and
owned Instruments/leaks attempt. A finite `--image-diagnostics darwin-tools`
transport flag distinguishes identical method filters without an ambiguous
environment override; that flag is stripped before invoking the generated native
registry. Receipts explicitly state `strict_runtime_assertions_attested=false`.
Only the three still-unexecuted methods are requested; nine accepted UIImage
methods are not replayed. Public frameworks and source/API remain unchanged.

This is independent diagnostic coverage, **not a fix for or waiver of** the
strict startup failure. Native test/GC/pixel success and profile success remain
separate: actual correlated owned allocation rows and a PID-specific zero-leak
summary are mandatory for a positive profile. Unsupported tools, empty exports,
environment requests, successful compilation/installation and synthetic fixtures
cannot satisfy that profile or establish ASan/strict-runtime checks.

## Consequences and verification

The strict failure stays archived and referenced in #140/#141. Any individual
closure still requires reviewing every original finding criterion; the separate
diagnostic result never clears physical/minimum-platform/ABI/consumer/security
or overall release gates. Tests enforce exact selection, mode-specific command
and receipt binding, rejection of unrelated/wildcard/duplicate/unknown requests,
and all original Worker/runtime/binary/install/XML/owned-cleanup contracts.
Actual supported-tool/native execution is required before claiming acceptance.
