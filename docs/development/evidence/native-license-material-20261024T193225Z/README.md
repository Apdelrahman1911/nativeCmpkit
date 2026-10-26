# Locked native dependency license material — blocked collection

**Not release clearance. No notices were installed into live build inputs, no
native code was compiled or executed, and nothing was published.** This dated
evidence belongs to the dirty development worktree at base `94d2492e`, not an
immutable release candidate. The exact Cargo manifests/locks and tool hashes are
recorded in the invocation receipts.

## Executed sequence and preserved failures

1. `scripts/native/artifacts.py metadata --module <module>` initially failed in
   locked/offline mode: the picker graph lacked `bumpalo 3.20.3`; the share graph
   lacked `winapi-util 0.1.11`. Both original stderr/exit observations remain.
2. A lead-scheduled `rustup run 1.98.0 cargo fetch --locked --manifest-path ...`
   downloaded 22 public crates for picker (151.713 seconds) and zero additional
   crates for share (0.117 seconds). Both returned 0; manifests and lock hashes
   remained unchanged. This was dependency retrieval, **not a build or test**.
3. Sanitized locked/unfiltered metadata then succeeded: **87 picker packages,
   48 share packages**, each including its own local root. An unfiltered target
   union is deliberately conservative; it is not proof every crate is linked
   into each platform's binary.
4. The first archive-only collector reported 15 gaps and 140/66 files. Review
   exposed a tooling defect: `objc2-foundation/src/copying.rs` and
   `src/tests/copying.rs` had been mistaken for COPYING license files. The source
   filename exclusion and independent package-inspector check were repaired and
   regression-tested. **The initial counts are not current evidence.** Original
   reports remain rather than concealing the correction.
5. A fresh corrected collection returned **exit 1 for both modules**: 138 picker
   and 64 share candidate notice/license files, **16 missing-text crate gaps**
   each. `complete_material_collection=false` and
   `license_obligations_reviewed=false`. Exact corrected texts, sanitized metadata
   and reports are preserved in the two `*-corrected-collected-texts.zip` inert
   archives. `preserved-collected-texts.json` binds their bytes; do not execute
   or automatically extract archived dependency content.
6. Read-only GitHub retrieval inspected immutable VCS commits advertised by the
   checksum-verified crates. Local re-verification checked all **16** original
   crate manifests byte-for-byte against exact-commit GitHub manifests; `.cargo_vcs_info.json`,
   normalized identity/license and workspace inheritance also match. Retrieved
   bytes were independently checked against Git blob OIDs and SHA256. The six
   commits span two public repositories. See `verified-vcs-provenance.json`, raw
   `crate-provenance/`, raw `external-vcs/` and both retrieval receipts. These
   prove the observed content correspondence, not author signatures or a legal
   opinion.

## Material disposition

| Dependency | Exact observed material | Disposition |
|---|---|---|
| `jni-sys-macros 0.4.1` | Complete root `LICENSE-MIT` and `LICENSE-APACHE` at `jni-rs/jni-sys@64d77b7a5f119d7b55b4e2c169a4668067ff59e6`; original macro manifest matches, explicitly `MIT OR Apache-2.0` | **This crate's missing material is available from its pinned VCS**, not from its `.crate`; attribution includes “Copyright (c) 2015 The rust-jni-sys Developers”. A future collector adapter must retain external origin and exact bindings. No live installation or aggregate-report rewrite occurred. |
| 15 `objc2` workspace crates | Same 1,339-byte root `LICENSE.md` policy/link document at all five exact commits | **Missing complete license/copyright material remains unresolved**; policy links are not silently substituted with generic templates. |

The 15 unresolved packages are `block2 0.6.2`, `dispatch2 0.3.1`, `objc2 0.6.5`,
`objc2-encode 4.1.0`, and `objc2-{foundation,app-kit,cloud-kit,core-data,
core-foundation,core-graphics,core-image,core-text,core-video,io-surface,
quartz-core} 0.3.2`. These are shared by both conservative locked graphs;
do not count them as 30 distinct missing dependency identities.

Exact supplemental JNI hashes:

- MIT: `1d85bd754b04ceec93e98e890edd1fa3c6a22e81bcb32135806beeccefa51cd1`
- Apache: `c6596eb7be8581c18be736c846fb9173b69eccf6ef94c5135893ec56bd92ba08`
- `objc2` policy document (not full text):
  `7f976f7e9cb2d87df7230606feb932c3f21ac0e664045a775b600046ff850c54`

The exact `objc2` policy says four named crates are MIT and others
Zlib/Apache-2.0/MIT at the user's option. It additionally states uncertainty
about redistributing derived Apple SDK works and links
[upstream licensing issue 23](https://github.com/madsmtm/objc2/issues/23). This is
an **observed upstream uncertainty**, not a finding of unlawful distribution.
The investigation stops here rather than inventing clearance, choosing a new
license, assuming SDK acceptance resolves downstream obligations, or searching
unrelated revisions until a convenient text appears.

## Gates and next action

- Archive-only reports still correctly contain **16 gaps**: the collector has
  no VCS supplement adapter. Separately collected exact JNI texts can address
  **one material gap only**, leaving 15 crate-text gaps plus legal review.
- An adapter, if implemented, must bind crate checksum, VCS commit/path, original
  manifest and immutable license bytes, declare external origin, and be checked
  independently by the static artifact gate. A generic URL/template or boolean
  override is not acceptable.
- The owner/maintainer needs a documented legal-material disposition for the
  `objc2`/Apple-SDK ambiguity before distributions using these dependencies.
  A reviewed dependency change would require fresh lockfiles, native behavior,
  provenance and compatibility tests; it is not justified solely to make this
  report green.
- Keep local source/JVM diagnostics separate from artifact-consumer/release
  verification. The license gate must stay closed; neither this retrieval nor
  a successful JVM diagnostic authorizes candidate distribution.

`SHA256SUMS` covers this frozen directory except itself. It records the observed
bytes, not an external authenticity attestation. The frozen collector/checker
source used for corrected collection is in `tools/`; future attempts belong in
a new dated evidence directory. Prior successful or failing receipts are not to
be overwritten.
