# Preview changelog draft

## 0.1.0-preview.1 — UNRELEASED candidate

No release date, tag, published packages or completed platform matrix is asserted.
Replace this draft with revision-bound, verified changes only after the release
gates pass. Do not list every open audit finding as fixed merely because a source
patch exists.
The current [contained checkpoint](containment.md) does not publish a preview or
enable remote verification. These are prospective release notes, not an
announcement or a control-policy change.

### Independent identity and preservation

- Independent nativeCmpkit repository, preserved original Git history and public
  metadata, Apache-2.0 license/copyright/attribution and third-party notices.
- New Maven group `io.github.apdelrahman1911.nativecmpkit`, artifacts
  `nativecmpkit-*`; retained `com.mohamedrejeb.calf.*` source/API/JNI/resource names.
- Current upstream open-issue descriptions, labels and relevant public history
  synchronized onto existing destination issues without duplicates.

### Development verification work (not yet release completion)

- Independent package consumer and static POM/module/native/notices checks,
  rather than using the existing sample applications as library test coverage.
- Clean source-bound baseline and two actual local-JAR/JVM comparisons. The first
  revealed a real unpublished-geo `EarthRadius` Java-source/reflection regression;
  the minimal public deprecated constant repair passed the original old-bytecode
  replay and separate source compilation. Raw 18-removal comparison still fails
  after individual internal/generated/modifier classification; compiler/KMP ABI
  and staged consumer verification remain incomplete.
- Exact locked native dependency notice collection and package provenance gates.
- Subsystem regression/fix evidence is tracked under `docs/development/` and its
  resolution records; **only verified resolution records belong in final release
  notes**.

### Compatibility notes to carry into the first release

- Do not combine nativeCmpkit and old Calf Maven artifacts on one classpath.
- Desktop WebView now requires an explicitly consumer-selected JavaFX21.0.13
  runtime/compile dependency set instead of inherited publisher-host classifiers.
  See [the dependency migration](compatibility.md).
- Windows Arm64/musl/Intel-iOS/Node/Kotlin-Native desktop were not established
  working target configurations; no new support is promised by a loader path.
- Any unavoidable behavior/source/binary changes discovered during verification
  must be listed here with exact API, rationale, migration path and tests.

### Final release checklist (pending)

- [ ] All actionable issues have verified dispositions; no unresolved gate hidden.
- [ ] Complete artifact/native/platform test matrix and consumer results linked.
- [ ] API/ABI and runtime dependency changes reviewed and documented.
- [ ] Native/font/copied-code/dependency license obligations reviewed.
- [ ] Actual registry coordinates/visibility/authenticated installs verified.
- [ ] Published byte digests match tested candidate bytes.
- [ ] GitHub prerelease and immutable package/checksum/notice links added.
