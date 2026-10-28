## Important targeted verification — 2026-10-28

Immutable source **17db28fa56c5a50b1637d8abc0bf471b7e56af2c**:
- [Windows picker/share cache + actual JNI](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40606411532): **89/89 executions**, 15 fresh XML, zero failures/errors/unexpected skips; one exact macOS-only case N/A. The original Windows concurrent sharing failure from failed run40602393181 now passes. Complete private staging is published with a no-replace hard link, never a potentially replacing atomic move; open-reader identity preservation and failed/unsupported publication regressions pass in both modules. Old three-argument descriptors retained. Picker54/share35; actual ABI/diagnostic/borrowed-pointer/unsupported-owner tests executed.
- [Android Coil only](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40606422085): **5/5**, one fresh XML, zero skips. Both extra failed fixtures now complete final descriptor/close/error-origin/null-open assertions. Earlier accepted IO27 reused with **zero new IO executions**; all94 relevant module/toolchain/build inputs match f37bf141. Controlled Robolectric resolver transport is not device/provider Binder IPC.

Independent review verifies all738 exact own-Git inputs, before/after maps, artifact and XML hashes, actual commands and setup/test SDK correspondence. No successful unchanged Linux/macOS/IO suite replay. Prior whole failed runs remain failed and preserved.

**This issue remains open where its original acceptance requirements are incomplete**: Windows cross-process loaded-DLL, old-system-ABI/trusted-packager, foreign-owner/read-only/noexec/native-parent or the broader device/consumer/ABI/legal/dependency matrix are not certified. A passing cache/JNI suite does not waive those tests. No package, release or deployment was published.

Evidence: `docs/development/evidence/github-actions/40606411532/` and `40606422085/`.
<!-- nativecmpkit:targeted-verification:17db28fa:windows-and-coil -->
