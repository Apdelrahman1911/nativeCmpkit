# Direct checked-bundle closure — 2026-10-28

**[NAV-004/#92](https://github.com/Apdelrahman1911/nativeCmpkit/issues/92) is closed/completed.** All four original requirements were reviewed before immediate closure; the original issue body, title, labels and history are preserved. The comment/closure/count readbacks are archived here. **50 issues are confirmed closed.** Documentation follows closure rather than delaying it for another suite.

## Accepted important evidence reused, no successful-suite replay

[Run40528445496](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40528445496) at immutable `769bf7dea1ca69ac23ef74d7f7140303b130657a` already executed the two directly owning classes: `NavArgumentAndBundleTest`10 and `CheckedNavArraysTest`5 methods. **15/15 on JVM, browser JS, browser Wasm and actual iOS simulator =60 original target-method executions**, eight fresh original XML, zero failures/errors/skips. These are a subset of321 previously accepted executions, **not60 new tests**. The selected exact original XML are copied here losslessly in deterministic gzip; original artifacts and hashes remain unchanged.

[Source/criterion/result review](accepted-review.json) verifies the eight owning production/test files remain byte-identical, original artifact digests/XML hashes/command exits, held before/after inputs and actual recorded runtimes. The older original receipts record Java17 setup but predate the actual Gradle-daemon witness: **no retroactive daemon attestation**. The first review script rejected that unsupported newer-field assumption before any GitHub mutation; its original is retained and must not be replayed as a routine test. Neither archived review script should be rerun for already closed issues.

1. Wrong scalar reads through checked `getOrNull<T>`, typed accessors and built-in NavTypes return null/documented fallbacks without caller casts.
2. `getString(Int42)` returns null or a supplied fallback, not `"42"`.
3. All24 supported null/scalar/primitive-array/object-array/ArrayList generic insertion forms and typed/element contracts execute on all four runtimes.
4. Explicit null versus absent keys, intentional borrowed reference sharing and mutable-array/list revalidation are documented and tested.

**Compatibility:** legacy erased `get<T>` remains callable, explicitly deprecated and unchecked for old binaries; it is not claimed type-safe. Use checked or typed/container accessors. `getOrNull` cannot validate arbitrary erased generic element types. Bundles are in-memory nondefensive/non-thread-safe mutable maps, not Android parcelables. See ADR0004 and the owning API KDoc. Whole-library ABI/consumer/minimum-platform/device/legal/dependency/security and release gates remain separate. No packages, release or deployment publication; single-agent only.
