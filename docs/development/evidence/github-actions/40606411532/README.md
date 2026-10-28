# Focused Windows cache/JNI verification — 2026-10-28

[Run40606411532](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40606411532)
at immutable `17db28fa56c5a50b1637d8abc0bf471b7e56af2c` passes **89/89 executions**,
15 fresh XML. One exact macOS-only case is N/A; zero unexpected skips. Picker54/share35.

[Important source/result review](important-result-review.json) verifies all738 exact Git inputs,
before/after maps, artifact/every XML digest, fresh commands, and setup/test SDK correspondence.
The Windows concurrent sharing failure from failed run40602393181 now passes. Both
no-replace late-publisher/open-reader regressions and both failed-publication fallbacks pass.
Actual JNI ABI/diagnostic/borrowed-pointer/unsupported-owner scenarios execute. The one
old differing-byte test deliberately now requires old-byte preservation and verified
unique fallback; the old failure/contract remains preserved.

**IO-022/#149 and NATIVE-031/#86 remain open**: no multi-process loaded-DLL, foreign-owner,
read-only/noexec/trusted-old-ABI/full native acceptance. No unchanged successful Linux/macOS
replay or sanitizer/device/legal/dependency/full-consumer/API-ABI/release claim.

One accepted selected-job dispatch; archive contains reports/receipts, not private logs.
No packages, releases or deployments published.
