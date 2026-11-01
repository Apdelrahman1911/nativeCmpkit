# UI-only supplemental JVM diagnostic — actual completion, bounded scope

**Capture exit 0 / 0.939007 s; strict compare exit 0 / 0.124852 s.** Only the two sealed-plan argv ran. No Gradle, build, download, compiler, library class execution, runtime/native/consumer tests, live edits or Git/GitHub mutations.

## Exact retained input/result scope

- Existing producer002 UI desktop JAR: **532333 bytes**, SHA256 `2ab93684a9facdfbb3d0e7908694f16e89e0f02f01104fac812dfb7aed9e5554`. Reused, not rebuilt or restaged.
- Dirty source-bound producer base: `100d43ca0e7c5049631002e2bf6a2db49d4c2573`; not a clean current revision or trusted release artifact. Original producer0/231.05s/1023 library/1100 combined/25 legal inputs is reused, not rerun.
- Retained baseline revision `94d2492e99d5cbc060409d94d9f88febd06222d5`; complete parent snapshot SHA256 `466b41324099954c03703ee0d0af0c6a429f3efedd3232231e762f2978e4ff2e`.
- `baseline-ui-only.json` is **byte-identical to the sealed projection** (SHA256 `ed57d466a9a411d4da6f221a8222b979777c039e460b098eda0e219f23fe7373`). It keeps the entire original UI artifact record, original capture metadata and all **22 explicitly unselected artifacts**. No class/member filters, missing-artifact substitution or baseline regeneration.
- **272 selected input/tool/JDK/source/provenance/artifact hashes match before, after capture, after comparison and final private review.** This includes 142 UI production/build paths +72 UI test paths +7 shared inputs and the selected evidence/tools/JDK. It is not an exhaustive producer-input or signed builder attestation.
- JDK17.0.20 `javap` inspected **111 classes /97 exported classes /7629 member records**; baseline UI was88 /81 /7526. The inherited Calf/Jodd class-selection policy is unchanged.
- Both exact owned command leaders were reaped; `/proc` readback finds no owned process-group members/unknowns, with **zero stop signals**.
- Mandatory **8 GiB disk reserve** passes all three execution readbacks (about40.3 GiB free). MemAvailable is recorded only as observation (about4.7 GiB); no RSS or memory-reserve enforcement is claimed.

## Raw delta and source classification

**Zero removals, zero class-declaration changes;26 raw addition records =16 classes +10 members in existing classes.** New class records contain93 complete member records; total retained member growth is103, not26 tests/API methods.

All26 additions are preserved and individually source-bound in`addition-source-classification.json`:

- **4 public-property accessor records** for3 source properties: `AdaptiveDatePickerState.displayedMonthMillis` (getter/setter), `DateBounds.isEmpty`, and `AdaptiveDatePickerState.isSelectionSelectable`.
- **21 Kotlin-internal/class/facade/owner records**, including new internal slider/presentation/renderer helpers. Their JVM-public representation remains fully recorded; internal classification is not an exclusion or a Java/reflection compatibility guarantee.
- **1 inferred generated annotation-support record** for the public selection property. Source/name correspondence is not compiler metadata certification.

## Limitations and retained preparation observations

This is only a dirty source-bound **javap exported-surface diagnostic**. Exit0 does **not** certify compiler ABI/reference dumps, Kotlin metadata/default/inline/nullability/Compose, JNI/Swift/Android/JS/Wasm/KLIB, old-binary runtime linkage, behavior or demonstrated breakage, complete21-root consumers, native/legal/security provenance or release readiness. No reference was generated, issue closed or other gate bypassed.

Initial pre-execution metadata delay mistakenly interpreted the reserve as MemAvailable; lead clarified the existing disk-only contract. One private source-classification preparer then used an out-of-range line67 and was corrected to the actual line61 by passive readback. Both observations are retained; neither caused a JVM/test failure or a diagnostic rerun.

`identity-ledger.json` retains original-private/safe-file identities. Only known machine/private prefixes in derivative receipts/logs were replaced with explicit placeholders; raw API snapshot, raw delta and full baseline projection are unchanged. `final-evidence-review.json` records passive post-result/source/hash checks, not more tests. `SHA256SUMS` seals these safe bytes, not authenticity or release approval.
