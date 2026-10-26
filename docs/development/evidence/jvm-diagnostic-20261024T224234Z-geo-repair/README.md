# Second JVM diagnostic — legacy geo field repair verified

**The narrow Java-source/reflection regression is repaired in the tested local
JAR; full compatibility and distribution are not certified.** The raw comparator
still returns **exit1** for 18 reviewed internal/generated/modifier records.
The [first iteration's 19-removal delta and real failures](../jvm-diagnostic-20261024T223018Z/README.md)
remain preserved.

## Exact iteration boundary

- Same clean baseline `94d2492e99d5cbc060409d94d9f88febd06222d5`; second candidate
  is still **dirty** source at that base, not an immutable release revision.
- **701 input hashes / 23 real local JARs** captured before/after the producer and
  before/after this diagnostic. Both native notice-output directories remained
  absent. Exact source/JAR snapshots remain local only in
  `/tmp/nativecmpkit-jvm-diagnostic-20261024T224234Z-geo-repair/`.
- Exactly **two source paths** differ from the first 700: `LatLng.kt` and the new
  `LatLngJvmCompatibilityTest.kt`. Only the **unpublished geo JAR** changed; all
  other 22 JAR hashes are identical to the first diagnostic.
- Producer exit **0 / 11.00 s**; **23 fresh JAR tasks**, 72 executed / 105
  UP-TO-DATE tasks, no build/configuration cache. The separate producer GEO
  desktop suite passed **39 cases**, including the new public-field regression.
  `producer/geo-test-report-verification.json` independently rechecks all four
  preserved XML reports (39 testcase elements; zero failures/errors/skips).
  These are library desktop tests, **not** Maven consumer or native-device tests.

The minimal GEO owner repair keeps a deprecated, Java-accessible
`public static final double EarthRadius = 6371.0`, with WARNING rather than
HIDDEN deprecation, while retaining the geometry corrections. No mass namespace,
API or implementation rewrite was needed. `delta-review.json` contains exact
snapshot source lines108–118 and hashes.

## Executed evidence

| Check | Actual result |
|---|---|
| 23-JAR `javap` snapshot, JDK17.0.20 | Exit0 / 7.378 s; **513 inspected / 449 exported classes / 10,976 member records** |
| Raw baseline-to-second comparison | **Exit1** / 0.138 s; **18 removals / 311 additions / zero class-declaration changes** |
| Ordinary baseline-compiled Java linkage fixture | Exit0 / 2.406 s; **six candidate cases / 31 assertions passed**, plus baseline sanity; same class hashes as first iteration |
| Original EarthRadius baseline class on original baseline | Exit0 |
| **Same original EarthRadius class on repaired geo JAR** | **Exit0**, public reflective field lookup/value succeeds |
| Same Java source compiled against repaired geo | **Exit0**, separate newly compiled source-check output |
| Separately candidate-compiled source-check runtime | Exit0 |

The field replay uses original baseline class SHA256
`32435e06a00a329efd3c533fcd19ba87297dc6d578902330c0c407ddf52cee82`—**the bytes that
failed on the first candidate**, not newly baseline-compiled replacements.
`earth-radius-replay/result.json` records the exact classpaths, command exits,
class/source/JAR/stdlib hashes and unchanged-bytecode checks. The only third-party
dependency remains the same Kotlin2.4.20 stdlib JAR on every runtime.

The fresh source-compile output is deliberately separated from
`unchanged-baseline-classes`. Even if resulting bytes happen to match, recompiling
source is not substituted for the original-bytecode test. Our own four Java class
files are preserved in `compiled-fixtures.zip` with individual hashes; no native
or library JARs are included.

Supplemental verbose field inspection was performed after freeze release against
the preserved second geo JAR. It confirms `ACC_PUBLIC, ACC_STATIC, ACC_FINAL`,
descriptor `D`, value 6371.0 and a deprecation marker, without a synthetic field flag.
The positive public `getField` test does not override Java accessibility.

## Raw delta review, not a misleading green result

The second delta is **exactly the first delta minus the EarthRadius removal**.
Its 311 additions are identical: 159 class records + 152 member records; zero
class-declaration changes and no added abstract member on a preexisting class.
The two extra member records in the full snapshot reflect the restored field and
the new deprecation annotation accessor within an already added companion class;
the whole-class delta does not enumerate all that class's member records.

`delta-review.json` classifies all remaining 18 records with source evidence:

- **4** descriptor-preserving synchronization-modifier changes in internal MIME
  helpers, paired with matching additions.
- **4** removed Kotlin-internal camera/permission/WebView implementation surfaces.
- **10** compiler-generated private/local bridges, disposal or dispatch holders.

This review found no supported Kotlin-public removal among these raw records,
but direct Java/reflection use of JVM-public internals/generated classes can still
break. Kotlin metadata/inline/default/nullability/overload/sealed semantics and
non-JVM ABI were not validated by this scan. The documented navigation nullability
change is not erased by descriptor equality. No filter suppresses the comparator
failure, and six narrow Java cases do not certify every exported declaration.

## Integrity and what did not pass

`postcheck.json` rechecked all 701 source inputs, 23 JARs, their local snapshots,
receipt/tool bytes, source HEAD/dirtiness, exact API/JAR hashes, both legacy fixture
class sets and absent notice directories. It passed before the second freeze was
explicitly released. Later producer work may legitimately differ from this saved
iteration; its results must not be substituted without fresh receipts.

`result.json` summarizes outcomes and `SHA256SUMS` covers durable evidence. Original
first-failure and second-pass receipts remain separate. Six reused Java cases run
twice are not 12 independent test methods; the GEO producer's 39 are a different
suite, and the field replay is a separate focused compatibility characterization.

**Strict Maven consumer methods executed: zero of 17.** Distribution, static Maven
artifact inspection, native-runtime and whole-API/release certification remain
false. Local JARs do not bypass unresolved native license texts, all-host payload
assembly or real external package consumer tests. No staging, publication,
Actions or Pages mutation occurred in this diagnostic.
