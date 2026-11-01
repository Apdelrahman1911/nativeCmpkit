# Four-APK compiled surfaces — 2026-11-01

Independent **offline/static** readback of two helpers and two library reporters.
This public package contains only sanitized receipts, full typed manifest
projections, correspondence and hash evidence from an immutable sealed review.
**No APKs, key/DER bytes, private signing paths, raw console logs or SDK stdout/
stderr are included.** Output byte lengths and SHA-256 identities remain in the
receipts. This packaging performed no builds, installs, tests or native probes.

| Artifact | APK bytes | declared min/target | projection elements/attributes | exact offline signer APIs | APK SHA-256 |
|---|---:|---:|---:|---|---|
| io | 895573 | 23/37 | 13/38 | 35 | `375ba9b4f208997a237650074e7c61d93dc9cabc8ebdf5a980b1dfa330dec59f` |
| io-reporter | 10223932 | 23/37 | 42/77 | 35 | `a545806553bd9012bdac772faa202556728697e02dc3ffd3e83046b1f457ab2b` |
| permission | 24129569 | 33/37 | 30/54 | 33, 34, 35 | `ef4a71b1f88f049fd4266bf8ec3781979b4c8bc5838f4c4841e25ec3a2dc7dd7` |
| permission-reporter | 9697708 | 23/37 | 52/78 | 33, 34, 35 | `1c7e9331034b47db896f0d6f74e588cf10203636f1861a3c13e0e8f1a654567c` |

## Actual compiled-surface and signing evidence

- All four [manifest projections](evidence-index.json) retain **every** actual
  aapt2 element and attribute, including typed strings, integers/flags, booleans
  and resource references. Adjacent projection JSON preserves the complete typed
  record sequence and source lines. No emitted startup/library node was filtered.
  Projections are not the original binary manifest bytes; binary-manifest,
  actual-tool-tree and projection hashes are distinct in
  [sanitized-review.json](sanitized-review.json).
- Actual APK metadata and badging agree on package/debug/SDK declarations.
  [Reporter source correspondence](reporter-surface-source-correspondence.json)
  also records checksum-validated DEX-defined component and source-derived test
  classes. Defined classes are **not** native test execution or executable-body
  equivalence. AndroidX exported test-invoker Activities are explicitly disclosed;
  they are not mislabeled as signature-protected fixture controls.
- [Exact symbolic SDK receipts](all-tool-receipts.json) preserve **16 distinct
  offline commands**: four manifest dumps, four badgings and eight exact signer
  ranges, plus one guarded PUBLIC-certificate export. The six original successful
  helper commands were not replayed. Official build-tools **36.0.0** inspected
  SDK37 compilation (aapt2 2.20-13193326/apksigner 0.9; explicit JDK17).
- Both IO APK signatures were verified only at exact API35. Permission helper/
  reporter signatures were verified separately at exact API33, API34 and API35,
  each with one verified v2 signer and no warning/stderr. All match the controller
  [public-certificate identity](all-public-certificate-correspondence.json):
  `3b85ff5df7a6ab99cb6a416a60ef4d272e5bf77580bb35c3cbc9485908254616`.
  The export persisted no raw DER/private-key bytes or private signing path.
  These checks do not establish v1/API23 support, installed identity or runtime.

## Successful compilations and failures retained

[Helper readback](helper-compile-facts.json) confirms actual successful assemblies
**0/17.0s** (IO) and **0/107.02s** (permission), with exact APK/metadata mtimes inside
those invocations. These are reused earlier execution facts, not new builds.

The original two-reporter aggregate remains **FAILED: exit1/103.02s/four permission
Kotlin diagnostics**. Its completed IO assembly and fresh reporter do **not** turn
that aggregate into success; see [original IO reporter facts](io-reporter-compile-facts.json).
The later permission reporter independently compiled **exit0/35.01s**, with a
fresh APK and separate [successful invocation facts](permission-reporter-compile-facts.json).
No original failure is rewritten as passed, native failure or SDK/install cause.

The [owning supplied-filename correction](filename-correction.json) is preserved,
not mislabeled actual artifact absence. [Inspection-only refusals](inspection-refusals.json)
retain the resolved local DEX-regex, source-class probe, name-scope and final-freeze
count errors without inferring native failures or replaying successful commands.

## Exact owning manifest-validator recovery

The original permission helper validator refused its real
EmojiCompatInitializer, and independently rejected both emitted optional AndroidX
window libraries. The integrated two-path Python repair admits **only**:

- `androidx.emoji2.text.EmojiCompatInitializer` under the existing exact, private
  AndroidX startup provider/value/attribute constraints;
- `androidx.window.extensions` and `androidx.window.sidecar`, each with exactly
  `name` and `required=false`, no child elements and no duplicate library names.

It does not remove initialization, filter the actual tree, add source components
or weaken permissions, shared-UID refusal, signature controls, provider/receiver
protections or SDK bounds. Exact [source postimages](guard-source-postimages.json)
and [consumed dependency/source/tool pins](guard-dependency-source-tool-pins.json)
are retained. No APK rebuild was performed or needed for this adapter-only change.

The complete actual **30-element/54-attribute** projection strictly passes;
**38 unsafe actual-projection mutations refuse** in
[guard-actual-red-green-and-refusals.json](guard-actual-red-green-and-refusals.json).
Retain [two original modeled errors](guard-original-red.result.json) and reuse
[7/7 new modeled methods/no skips](guard-repaired-green.result.json). These models
and mutation controls overlap; they are not additive native coverage. Packaging
replayed none of them, and no previously accepted method was replayed.

## Frozen phases, unverified criteria and unchanged gates

[Original and later compiler maps](compile-freeze-source-correspondence.json)
independently held **1064 library / 1141 combined** inputs in each phase, but differ
at five owning Kotlin compiler fixes. They are not called identical. The subsequent
completed review snapshot held **1065/1142** after the lead's two exact validator/
test postimages plus one compiler guard; [final-freeze-readback.json](final-freeze-readback.json)
records that historical guard-only phase, not a claim about a later repository
revision or actual CI combined artifact. All four APK identities remained held.

Remaining [scope disclosures](sanitized-review.json) are unchanged: API34 platform
selection plus library-state observation is not a library selected-request result
or selected/unselected read proof; row deletion checks return value, not independent
absence; activeReads lacks independent presence/type readback; WRITE uses injected
owned fixture state and exceptional all-files uses an exact owned-UID app-op, not
Settings UI. IO FileProvider is same UID, open counts returned descriptors, and
ordinary owner-revoked release is idempotent. Its compiled resource reference is
retained, but the actual compiled paths XML was not separately decoded here.

**ZERO new native executions, installation/UID/grant/OS acceptance, issue closure,
minimum/security/dependency-trust clearance, publishing/Pages/main/history or
release acceptance.** Issues #45/#55/#102/#118 and all remaining original criteria
stay open. Six storage-flavor APKs are outside this review. The lead owns any
separate bounded native requests, source freezes and acceptance decisions.
