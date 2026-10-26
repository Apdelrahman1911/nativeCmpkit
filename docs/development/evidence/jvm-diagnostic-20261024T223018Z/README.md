# First candidate JVM diagnostic — regression found

**Executed against real local JARs; not a distributable/Maven candidate.** This
historical iteration found a reproducible Java-source/reflection regression in
unpublished geo. The original negative results below remain unchanged; the
[separate second iteration](../jvm-diagnostic-20261024T224234Z-geo-repair/README.md)
verifies the minimal repair with the **same original baseline class bytes**.

## Source and artifact boundary

- Baseline: clean detached `94d2492e99d5cbc060409d94d9f88febd06222d5`;
  [source-bound baseline receipt](../abi-baseline-94d2492e/README.md).
- First candidate: **dirty development inputs at that base commit**, not the
  immutable commit's contents. The producer and diagnostic checked 700 input
  hashes, 23 actual JARs and the continued absence of both native notice-output
  directories. The 23 JARs represent 21 publication identities plus unpublished
  navigation/geo; no package was staged or published.
- Producer: exit **0**, **36.01 s**, all 23 `desktopJar` tasks forced to execute;
  **112 executed / 60 UP-TO-DATE** tasks, no build/configuration cache, **zero
  tests**. Unchanged dependency tasks were not indiscriminately rebuilt.
- Exact producer receipts, tool sources, inventory and fixture sources are
  preserved here. Native JARs and the 700 source inputs remain **local only** in
  `/tmp/nativecmpkit-jvm-diagnostic-20261024T223018Z/`. No uncleared native binary
  is included in this evidence directory.

The shared base SHA in both API snapshots is **not** evidence of a same-source
comparison. The candidate's explicit dirty provenance and input-receipt digest
identify its different source. External caches, SDKs and compilers were not fully
hermetic/attested inputs.

## Inspected executions

| Command | Result | Meaning |
|---|---|---|
| `jvm_abi.py snapshot`, JDK17.0.20 | Exit0 / 6.555 s; **513 inspected classes, 449 exported classes, 10,974 member records** | Actual 23-JAR public/protected JVM snapshot, including Kotlin internals |
| `jvm_abi.py compare` against clean baseline | **Exit1** / 0.126 s; **19 removals, 311 additions, zero class-declaration changes** | Failed raw-surface comparison; not hidden by exclusions |
| `binary_linkage.py --diagnostic-local-root` | Exit0 / 2.186 s; **six candidate cases / 31 assertions passed**, plus baseline sanity | Same baseline-compiled class bytes and third-party dependencies on old/new runtime |
| Separate EarthRadius characterization | Baseline compile/run exit0; **first-candidate old-binary run and new-source compile both exit1** | Confirmed regression, detailed below |

The six-case fixture reuses the exact class hashes previously observed in
[baseline-only sanity](../legacy-binary-baseline-sanity-20261024T195518Z/README.md).
It touches selected IO/picker/permission/share/WebView/icon contracts, not all 449
classes and not native UI. It deliberately omits unpublished geo, explaining why
that success alone did not catch the field regression.

## Every raw removal classified

`delta-review.json` retains all 19 exact removal records with baseline source
excerpts/line ranges, file hashes, candidate citations where relevant, and matching
addition records for modifier-only changes:

- **1 confirmed Java-source/reflection regression:** `LatLng.EarthRadius`.
- **4 synchronized-modifier-only changes:** `jodd.net.MimeTypes` registration,
  lookup, reverse lookup and membership methods preserve owner/name/descriptor
  and public/final invocation targets. Adding synchronization appears as a raw
  declaration removal plus addition; it is not an absent invocation target.
- **4 explicitly Kotlin-internal removals:** camera/permission implementation
  classes, WebView navigation-event getter and desktop navigation collector.
- **10 compiler-generated/private-local removals:** remembered-state accessors,
  private-helper bridges, disposal classes and `WhenMappings`.

The 311 additions are **159 whole-class records + 152 member records**. No added
abstract member on a preexisting class appears in this delta. New classes carry
their full member inventory in `jvm-api.json`, not one delta record per member.
No supported Kotlin-public removal was identified **among these records**, but
that is not Kotlin metadata/default/inline/nullability/sealed/overload validation.
Java/reflection consumers of JVM-public internal/generated names can still break.
The raw comparator remains failed; there is no broad filter or ABI certification.

## EarthRadius: actual failure, not a const-inlining false positive

Baseline `LatLng.kt:78–80` used a **private companion** with an unqualified public
`const val`. The emitted class nevertheless had:

```text
public static final double EarthRadius;
descriptor: D
flags: ACC_PUBLIC, ACC_STATIC, ACC_FINAL
ConstantValue: double 6371.0d
Deprecated: true
```

The first candidate's `LatLng.kt:108–109` made the companion public and the
constant private, emitting `ACC_PRIVATE, ACC_STATIC, ACC_FINAL`. Java compiled
against the baseline retained the old inlined 6371 value, **but its public-field
reflection failed with `NoSuchFieldException: EarthRadius`**. Compiling the same
Java source against the first candidate failed with **private access**. Thus an
inlined-constant-only test would have missed the regression.

`earth-radius-characterization/result.json` records all four actual commands and
their original exits/log hashes. Supplemental `javap -private -verbose` logs and
`field-inspection.json` were captured **after freeze release using the preserved
first-candidate JAR**, not a later mutable build output. The field is in an
unpublished module and was not Kotlin-accessible at baseline; that limits impact
but does not negate the demonstrated Java-source/reflection break.

The original baseline-compiled field fixture has SHA256
`32435e06a00a329efd3c533fcd19ba87297dc6d578902330c0c407ddf52cee82`.
It and the two ordinary Java linkage classes are preserved in the inert
`compiled-fixtures.zip`; **no library/native JARs** are inside. Follow-up tests
must reuse those bytes, not silently recompile the old field fixture.

## Integrity and remaining gates

`postcheck.json` independently rechecked all 700 inputs, all 23 JARs, local
snapshots, producer receipts, tools, fixture bytes, API/JAR binding and source
HEAD/dirtiness at **22:34:30 UTC**. All checks passed and the freeze was explicitly
released. This historical stability result does not describe a later checkout.

`result.json` summarizes scope; `SHA256SUMS` covers the durable evidence, excluding
loose Git-ignored `.class` copies (their exact bytes are in the checked ZIP).
Commands/logs/deltas/failures are retained, not overwritten by the later repair.

**All distribution, Maven artifact-inspection and release flags remain false.**
The standalone 17-method Kotlin Maven consumer is still unexecuted. Native license
material, full payload matrices, native/device/platform consumers, Kotlin/KLIB/
Swift/Android/JS/Wasm ABI, minimum-runtime behavior and immutable release
verification remain separate gates. No Actions, package or release mutation was
performed by this diagnostic.
