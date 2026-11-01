# #82 / NATIVE-026 — four missing clipboard context paths prepared

The library's public APIs and production implementation are unchanged. Four new
library-level methods exercise the same JS/Wasm test bundle in fresh owned browser
realms: capability absence, actual insecure HTTP, document-policy permission denial,
and a trusted native mouse gesture invoking one real clipboard write.

**ZERO new browser-native executions. #82 remains open.** Existing accepted
controlled-Promise C1/C2 results are reused, not replayed. The new observer calls the
saved real method and returns its original Promise, but consumes a rejection in
its observation branch; it is not replacement C1 unhandled-rejection evidence.
Zero absent-API counters are not independent proof of zero attempted calls.
No clipboard reads, synthetic clicks, manual grants or fabricated activation.

## Actual qualification

- Eight important source/adversarial methods pass0/0.497s.
-97 affected existing routing methods pass0/2.954s, reusing the one already accepted
  choice/profile guard.105 unique methods total, not105 browser tests.
- Serial JS compiler0/59.01s and Wasm compiler0/50.01s each hold1129 library/1206
  combined inputs; actual JDK17.0.20/Gradle9.7.1 and both compile task markers pass.
- A subsequent one-literal capacity guard genuine red then green is preserved.
  The profile retains both targets but runs them serially, allowing one job to
  coexist with one other native job under global max2. Other profiles are unchanged.
  Current maps differ from compilers only at that CI guard and workflow, not Kotlin/
  build/dependency/native method bytes; no current whole-map equality is claimed.
- Current Actionlint and two literal source-only CLI plans pass; no native result
  follows planning. [Report](REPORT.json), [compilers](ACTUAL-COMPILERS.json),
  [capacity recovery](CAPACITY-GUARD-GREEN.json) and [source plans](SOURCE-ONLY-PLANS.json).

Use immutable `share-clipboard-native`, exactly four cases per target/one fresh XML.
Inspect actual emitted bundle, native origin/permission/isTrusted/activation/focus,
Promise settlement and complete owned CDP/browser/frame/listener/profile cleanup.
Native clipboard completion is not OS paste/readback. Global publishing, Pages,
main/history, consumer/API-ABI/dependency/legal/security/readiness gates stay.

[Execution design](../../../share-clipboard-native-contexts.md). API33's separately
accepted original is preserved byte-exact [here](../android-media-api33-original078/README.md);
its failed batch remains failed and API34 recovery has its own original review.
