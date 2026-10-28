<!-- nativecmpkit-direct-resolution:NAV-004:20261028 -->
## Verified resolution — important tests reviewed, direct closure

The original four NAV-004 criteria are accepted from immutable `769bf7dea1ca69ac23ef74d7f7140303b130657a` / [run40528445496](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40528445496). Reused the two directly owning classes: **15/15 on JVM, JS, Wasm and actual iOS simulator =60 original target-method executions**, eight fresh original XML, zero failure/error/skip. This is a subset of321 already accepted executions, **not60 new tests**; no successful suite replay. All eight directly owning production/test files remain byte-identical at `9e872623635a71a21a3ba723587a7b752cc01cc2`. Original archive digests, XML hashes, command exits, unchanged source maps and recorded setup Java17 are independently checked. These older receipts predate the later daemon witness; no retroactive daemon attestation is claimed.

- Checked `getOrNull<T>`/typed getters/built-in NavType access return null or the documented fallback for a wrong scalar type; `getString(Int42)` does not stringify it.
- Generic insertion covers all24 documented null/scalar/primitive-array/object-array/ArrayList forms. Checked containers reject incompatible elements, including after caller mutation.
- Explicit null differs from absence; borrowed mutable references/aliasing are deliberate and documented.

**Compatibility choice:** the old erased `get<T>` descriptor remains explicitly deprecated and unchecked; it is **not** claimed type-safe. Migrate wrong-type-sensitive calls to `getOrNull<T>` or typed/container getters. Arbitrary erased generic element types are not checked by `getOrNull`; the map is not defensive, parcelable or thread-safe.

The original technical body, labels and history are retained. Full ABI, packaged consumers, minimum platforms, physical devices, attribution/legal/dependency/security and release gates remain independent. No package/release/deployment publication. Closure follows important source/result review; the persistent ledger is updated afterward.
