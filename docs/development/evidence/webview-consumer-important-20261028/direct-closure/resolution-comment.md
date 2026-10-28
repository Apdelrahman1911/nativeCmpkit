<!-- nativecmpkit-resolution:BUILD-001:important-20261028-direct -->
## Resolved — required important tests reviewed, closing directly

JavaFX is no longer selected transitively from the **publisher's OS**. The public API/packages remain compatible; applications explicitly supply their six aligned JavaFX runtime dependencies as documented in `docs/modules/native-features.md` and `tests/consumer/webview-desktop/README.md`.

All **three original acceptance criteria** have passed:
- Actual root/desktop **POM and Gradle-module dependency selectors are identical on Linux x64, macOS arm64/x64 and Windows x64**, with no producer-selected `org.openjfx` dependency.
- **16/16 real consumer executions**, two authored public/native and staged-JAR-origin methods × module/POM mode × the four required hosts; eight fresh XML, **zero failures/errors/skips**. Public Compose → attached JFXPanel/WebEngine → Unicode HTML → typed JavaScript → exactly-once disposal and released embedding Scene all passed. Source/staging/fixture/cache fences and actual JDK17 producer/consumer daemons were inspected.
  - Linux x64: [40766415004](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40766415004), immutable `a0eba4ef23d35be1d8063ba43eb696306f60a56c`, whole workflow SUCCESS.
  - Both macOS architectures and Windows x64: [40768437205](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40768437205), immutable `71ed2c3bd9b8723cf2b753312a8f404cd270a660`, each required host job SUCCESS. All 837 own-Git inputs matched and held; 60 directly owning current source/docs files remain unchanged.
- Exact JavaFX21.0.13 native availability: preserved **30/30 HTTP200** checks (six modules × five advertised classifiers); all four required runtime hosts additionally resolved their own classifier on four classpaths. Successful unchanged tests were **not rerun**.

**Explicit retained limitation:** the extra Linux-arm64 job in40768437205 FAILED during producer staging (exit1/162.05s, `Check failed`, zero consumer methods/XML). This does not invalidate the four original required host passes and is **not** a Linux-arm64 native runtime pass or a green whole-workflow claim. Its failure is preserved and only that failed host is being diagnosed. The larger CI/platform/release gates remain open (including #5/BUILD-006); no dependency, ABI, minimum-platform or complete21-root release certificate is inferred.

This closure addresses BUILD-001, not overall Preview Release readiness. No registry packages, releases or deployments were published. Additive reviewed receipts are being persisted under `docs/development/evidence/webview-consumer-important-20261028/`; baseline findings/history remain unchanged.
