# Development-phase compatibility contract

This records intended compatibility work and the evidence still required. It is
not a declaration that a candidate is API/ABI-certified or already published.

## Names and artifacts

- Retain public `com.mohamedrejeb.calf.*`, opt-in annotation identities, Android
  namespaces, generated `com.mohamedrejeb.calf.calf_cupertino_icons` resources,
  framework names, original JNI package/method names and native filenames.
- The independent Maven group is `io.github.apdelrahman1911.nativecmpkit`, with
  `nativecmpkit-*` artifact names. Coordinates change intentionally; packages do
  not. Never place old Calf and nativeCmpkit artifacts on the same classpath.
- Keep old constructors/default arguments, launchers and sealed result cases
  where practical. Detailed cancellation/error/capability APIs should be
  additive, with documented adapters. New sealed cases can break exhaustive
  `when` consumers even if old JVM descriptors remain.
- Correcting data-loss/no-op/invalid state is an observable behavior change;
  retain an explicit migration note and regression rather than preserving
  unsafe behavior or silently claiming success.

## Desktop WebView dependency correction (BUILD-001/002)

The old generic desktop artifact hard-coded the publisher's JavaFX native
classifier. The development design removes that incorrect runtime promise:
**the consuming application explicitly selects the six JavaFX 21.0.13
dependencies for its own packaged host**. Producer `compileOnly` selection must
not leak its OS into generic published POM/Gradle metadata.

| Intended desktop host | JavaFX classifier | nativeCmpkit JNI resource slot |
|---|---|---|
| Linux glibc x64 | `linux` | `linux-x64` |
| Linux glibc Arm64 | `linux-aarch64` | `linux-arm64` |
| macOS x64 | `mac` | `macos-x64` |
| macOS Arm64 | `mac-aarch64` | `macos-arm64` |
| Windows x64 | `win` | `windows-x64` |

Use JavaFX `base`, `graphics`, `controls`, `media`, `web`, and `swing` at the same
patch version. A consumer host build can derive the classifier from that build's
actual OS/CPU; an installer cross-packaging for another platform must select the
**destination** explicitly. The independent fixture does host selection only.
Unsupported hosts must fail with a diagnostic rather than silently fall back to
Linux or x64. Windows Arm64/musl support was not established by the original
loader strings and remains unavailable until tested.

This is a **dependency-declaration migration**, not a claim of unchanged drop-in
runtime transitivity. Public JavaFX-exposing signatures need those types on the
consumer compile classpath too. Consumer apps also select their Compose/Skiko
runtime. Application installers must package the corresponding runtime modules
and native libraries. Successful Maven resolution is not a GUI/WebEngine pass.

The chosen JavaFX LTS patch still needs WebView lifecycle/rendering/media/TLS/
cookies/JavaScript regression evidence on each promised host. A clean OSV result
does not certify runtime security or arbitrary untrusted JavaScript policy.

## Verification layers

1. **Immutable source comparison:** baseline Calf commit, migration/sync commit,
   candidate source. Preserve exact historical bytes and additive changes.
2. **Compiler ABI:** KGP's own JVM/KLIB validation against reviewable snapshots,
   with Android target limitations explicitly reported. Never regenerate all
   baselines just to hide a failed comparison.
3. **JVM bytecode:** actual produced baseline/candidate JARs, `javap` descriptors,
   protected/public declarations and constants. The supplemental checker includes
   JVM-public Kotlin internals and flags deltas for classification, not automatic
   severity/compatibility claims.
4. **External source consumers:** no project/friend paths or source fallback;
   representative defaults/constructors/public types and old exhaustive sealed
   branches compiled with supported Kotlin/Compose dependencies.
5. **Old-binary/new-artifact execution:** retain a consumer compiled against the
   baseline, replace only nativeCmpkit implementation artifacts, and run its
   assertions on the new runtime. Compiling the consumer again is not this test.
   The [Java linkage runner](../../tests/consumer/binary/README.md)
   enforces unchanged class hashes and unchanged third-party dependencies for
   six narrow cases. Baseline sanity and two receipt-bound local-JAR candidate
   iterations passed the same **six cases / 31 assertions**; actual staged Maven
   artifact execution is still pending, and neither is Kotlin ABI proof.
   Its explicit local-JAR diagnostic mode provides source-development feedback
   while native license material blocks staged publication: it rechecks actual
   producer JAR/source/receipt bytes but always reports non-distribution scope.
   It neither fabricates static artifact success nor substitutes for the actual
   standalone Maven consumer. Dirty base-commit inputs remain dirty diagnostics.
6. **Platform/native ABI:** exact JNI exports and real loads; KLIB/Swift framework
   linking plus actual minimum-OS runtime/device interactions. JVM reflection or
   framework compilation does not substitute for these checks.

The current independent consumer pins Kotlin2.4.20/Compose1.12.0/AGP9.4.0 and
JDK17/Android minSdk23. It does **not** assert compatibility with older Kotlin or
Compose lines; those need separate declared fixtures if promised. No library
support floor should be raised/lowered solely to produce green tests.

## Executed local-JAR compatibility feedback

The [first diagnostic](evidence/jvm-diagnostic-20261024T223018Z/README.md) checked
700 dirty input hashes and 23 real desktop JARs. Its raw baseline comparison
**failed: 19 removals / 311 additions**. The ordinary six-case fixture passed,
but a separate old-Java-bytecode/reflection and Java-source probe confirmed that
geo's formerly JVM-public `LatLng.EarthRadius` field had become private. Constant
inlining preserved 6371 but did not preserve public field access. Geo is
unpublished and the baseline companion was Kotlin-private; the Java regression
was nevertheless reproducible.

The minimal repair retains a WARNING-deprecated, nonsynthetic, public static
final double field with the same value. The [second diagnostic](evidence/jvm-diagnostic-20261024T224234Z-geo-repair/README.md)
verified **the exact original baseline class bytes**, plus separate fresh Java
source compilation/runtime, against the repaired geo JAR. All 701 captured inputs
and 23 JARs were stable; only geo's JAR and two corresponding source paths changed.
The separate producer suite passed 39 GEO desktop cases, including a public-field
regression. Both source freezes were checked and released.

The second raw comparator **still exits1**: 18 removals remain (four added
synchronization modifiers with unchanged invocation descriptors, four explicit
Kotlin-internal removals and ten generated private/local implementation changes).
All records are individually source-classified; no blanket filter makes the
comparison green. No supported Kotlin-public removal was identified in these
records, but Java/reflection use of internal/generated names can break, and
Kotlin metadata/default/inline/nullability/sealed/overload compatibility remains
unverified. The same dirty base SHA is not an immutable-source attestation.

These are **local feedback, not Maven/distribution/release verification**. The
strict independent 17-method Kotlin consumer is still unexecuted, and native
legal-text/platform gates remain closed. Six repeated Java cases are not 12
independent tests or complete API coverage.

## Unpublished navigation source contract

Navigation remains unpublished. Its development fix retains the legacy
`SnapshotStateList<String>` back-stack getter and erased generic bundle getter
descriptors, with safer additive entry/typed-value APIs. `NavArgument.defaultValue`
changes from nonnullable `Any` to `Any?`: its JVM descriptor remains `Object`, but
Kotlin callers must handle a genuinely absent/null value. This is an intentional
**source nullability change**, not a binary-equivalence argument that source
compatibility is unchanged. See ADR0004 and the navigation owner's exact tests;
no navigation package availability or complete ABI certification follows.
