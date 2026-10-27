# NativeCmpKit: explicit pinned-VCS license supplementation

Contained **single-agent** development on `development/preview-hardening`;
`main` and imported history remain unchanged. Verification Actions are authorized
with read-only permissions, all actions allowed and no mandatory SHA pinning.
**No release, package, snapshot, deployment or Pages is authorized by this result.**

## Owning contract and implementation

The [2026-10-24 collection](evidence/native-license-material-20261024T193225Z/README.md)
found 16 archive-text gaps shared by picker/share. Only `jni-sys-macros 0.4.1`
already had complete, independently checked pinned-VCS license material. The
collector lacked an explicit boundary to use it without concealing its origin.

The repair is Python tooling and reviewed public material, **not a Kotlin/Rust
API rewrite or a legal decision**:

| Location/symbol | Contract |
|---|---|
| `tests/consumer/collect_native_licenses.py:collect` | Existing three positional arguments remain compatible. New keyword `vcs_supplements` and CLI `--vcs-supplements` are opt-in; default stays archive-only. |
| `collect_archive` / `MissingLicenseText` | Only the explicitly classified missing-text gap may fall back. Checksum, encoding, declared-file, traversal, symlink and other errors cannot become external-material success. |
| `tests/consumer/native_license_supplements.py:load_supplement` | Read only the exact requested identity. Validate bounded exact schema, package/checksum/license, immutable commit/path, both crate manifests, VCS root/package manifests, full license texts and hashes/Git blob OIDs. No directory scanning, network, extraction or code execution. |
| `verify_crate_correspondence` | Capture bounded real `.crate` bytes, verify their locked checksum and compare all three proof files. Reject invalid prefixes, links, duplicate members and oversized archives. Separately recovered source text cannot replace a missing or incorrect archive. |
| `regular_bytes` | Check every supplied parent and file before/after; reject observed links/hardlinks/replacement/mutation, nonregular/empty/oversized inputs. Close both stream-owned and raw descriptors, including stream-construction failure. This is not a same-UID filesystem sandbox. |
| `Supplement` | Hold the checked bytes once; export per-text `origin` and complete package `external_vcs_material`, including six proof files, without rereading mutable inputs during copying. |
| `tests/consumer/verify_artifacts.py:ArtifactVerifier.native_notices` | Independently compare the complete origin/proof/text records and actual ZIP bytes to the source-reviewed catalog. Reject unknown external material, missing proofs, archive reclassification and self-rehashed substitutions. Existing incomplete-material/lock/notice gates remain strict. |

Catalog: `licenses/native-dependency-supplements/jni-sys-macros-0.4.1/` contains
eight reviewed files. Its immutable origin is
[`jni-rs/jni-sys@64d77b7a5f119d7b55b4e2c169a4668067ff59e6`](https://github.com/jni-rs/jni-sys/tree/64d77b7a5f119d7b55b4e2c169a4668067ff59e6),
checksum `38c0b942f458fe50cdac086d2f946512305e5631e720728f2a61aabcd47a6264`.
Exact Apache and MIT text/copyright bytes are retained, including
“Copyright (c) 2015 The rust-jni-sys Developers”. The complete catalog manifest
records individual SHA256/byte counts/Git blob OIDs and explicitly leaves
`license_obligations_reviewed=false`.

Content correspondence with reviewed public source is **not a signature,
registry authenticity assertion, or assurance that every legal obligation is met**.
Do not generalize this narrow explicit-manifest adapter to workspace inheritance,
linked policy pages or another crate without source review and regression tests.
CLI catalog/cache roots must be explicitly public canonical non-symlink paths.
Only the trusted newly created test root is resolved to accommodate macOS's
system `/var`/`/tmp` aliases; input link rejection is not weakened.

## Executed regression and tooling verification

[Preserved evidence](evidence/native-license-supplement-20261027/README.md)
binds each run to its own source hashes at dirty base `cd51e8d6`:

- Original one-method missing-keyword regression failed against the old
  archive-only API, then passed unchanged with an explicit **empty** catalog;
  the missing-text gap and legal gate still fail closed.
- Initial 47-method adversarial suite and full 198-method consumer-tooling suite
  passed before further resource review.
- A new raw-descriptor test reproduced a real reader leak when `os.fdopen`
  raises before a stream owns the descriptor. The first 50-method run also
  exposed a nested test-fixture attribute error; both errors are preserved.
  Repairing that fixture left **one real leak failure**, not a silent green.
- Explicit construction-failure cleanup fixes the leak; **50/50 focused and
  201/201 full Python methods** now pass. All 50 focused methods occur in the
  full 201. File replacement/mutation also use real OS files/descriptors and
  check closure. The unchanged original one-method regression passes again.
- Cases cover exact crate/source correspondence, checksums, missing material,
  path/link/bounds/encoding safety, origin/proof tampering, independent notice
  rejection and no subprocess/network use by supplementation.

These are **Python tooling fixtures**, not JNI/Kotlin/native feature tests or
packaged consumers. Repeated counts overlap; they are not 450 distinct methods.
Exact pre-fix helper and earlier fixture bytes were reconstructed and checked
against their recorded hashes, not described as fresh reruns.
No Windows/macOS reader execution or release-readiness claim follows.

## Byte-preserving checkout policy and preserved preflight failure

[Source-held preflight027](evidence/ci-preflight-20261027-027/lead-review.json)
executes22/23 commands with17,903 source/stage inputs held and1,275 overlapping
Python methods, strict MkDocs and actionlint passing. **Its overall result is
failed**: staged whitespace check exits2 on the pinned author's extra Apache
EOF blank line; the final unstaged check is not executed. The license's exact
SHA256 remains `c6596eb7be8581c18be736c846fb9173b69eccf6ef94c5135893ec56bd92ba08`.
Trimming that observed byte sequence would break the reviewed origin contract.

[Four real Git fixtures](evidence/native-license-checkout-20261027/lead-review.json)
first fail on CRLF checkout conversion and the EOF conflict, then pass unchanged
after a narrow `.gitattributes` repair. All hash-bound catalog material is
`-text`, retaining normal visible diffs. **Only the exact JNI `LICENSE-APACHE`
file's blank-at-EOF check is exempt**; that file's trailing-space guard and
unrelated source EOF guards still detect intentionally invalid fixture bytes.
This specific public-byte preservation exception is explicit, not a claim every
whitespace policy stayed unchanged. No copyright bytes/hash are altered.

The full source-held consumer-tooling suite now passes **205/205 methods**, with
the four checkout and earlier50 supplement methods within205. These actual Git
`core.autocrlf=true` tests run on Linux; they are not Windows/native or packaged
consumer verification. Earlier47/50/198/201 results retain their exact inputs;
their counts overlap this205, not additional unique acceptance evidence.

A subsequent [preflight028 attempt](evidence/ci-preflight-20261027-028/lead-review.json)
is also **failed/incomplete**, not a replacement green: the measured global root
capacity decrease trips its existing128MiB write-budget guard during inventory.
The owner process is stopped with exit-15 after0.906s;1/23 commands attempted,
zero Python/library/native/consumer methods,17,945 inputs/stage held. The cause
of the disk decrease is not attributed. No resource guard is lowered or cache/
other-project cleanup performed. Later measurement is below the **8GiB local
heavy-build reserve**; full verification moves to authorized immutable hosted CI.
Separate source/docs-only checks do not turn this full-preflight attempt green.

## Fresh real collection and independent inspection

At 18:22 UTC on 2026-10-27, locked/offline sanitized metadata was regenerated
from current manifests/locks, not copied from the old receipt. Rust/Cargo 1.98.0
was invoked through the explicit existing Cargo-bin path. Both metadata commands
pass and match the original sanitized graphs byte-for-byte; 17 selected owning
source/material files remain held. Dependency metadata is **not a native build**.

| Observation | File picker | Share |
|---|---:|---:|
| Locked union packages including local root | 87 | 48 |
| Metadata command exit / seconds | 0 / 0.566 | 0 / 0.215 |
| Collector exit / seconds | **1 / 1.369** | **1 / 0.516** |
| Original archive-text gaps → current material gaps | 16 → **15** | 16 → **15** |
| Unchanged ordinary archive license files | 138 | 64 |
| New exact external text / provenance files | 2 / 6 | 2 / 6 |
| Fresh inert material ZIP entries, including metadata/report | 148 | 74 |
| Actual notice-inspector checks / failures | 665 / **16** | 330 / **16** |

The [independent raw-byte review](evidence/native-license-supplement-20261027/real001/lead-independent-review.json)
rechecks the original archive manifest, **86 distinct locked registry archives**,
every collected text against its real archive or pinned source, every JNI proof
and source-held full-suite identities. All original packages are unchanged except
the explicit JNI material record. Each inspector still fails on exactly
collection-incomplete plus 15 missing-text requirements; all JNI-specific checks
pass. This is **not a passing artifact gate**. Actual ZIPs contain license/proof
material only, not Maven/JNI binaries; no live `build/native-notices` installation.

The 15 gaps are shared identities, **not 30 distinct dependencies**:
`block2 0.6.2`, `dispatch2 0.3.1`, `objc2 0.6.5`, `objc2-encode 4.1.0`, and
`objc2-{foundation,app-kit,cloud-kit,core-data,core-foundation,core-graphics,
core-image,core-text,core-video,io-surface,quartz-core} 0.3.2`.
Their policy/link documents are not substituted with generic templates.
The upstream Apple-SDK/licensing uncertainty remains a material/legal blocker.

## Issue state, next verification and release boundary

The independently reconciled [NAV-005 closure](evidence/navcodec-issue-closure-20261027/lead-final-readback.json)
confirms **#93 is closed**, after acceptance was pushed. One additive comment and
one state-only PATCH; original title/body/labels remain. Its first full-list
assertion omitted #93 despite exact closed-state/comment readback; a separate
fresh read-only reconciliation confirms **14 total closures**. The internal
consistency mechanism is unproven; no mutation was repeated or history erased.

Closed totals: #15/#16/#41/#42/#91/#93/#123/#128/#136/#146/#155/#156/#160/#171.
Ledger remains **68 implemented /78 partially verified /8 unresolved /10 verified**.
No additional original finding is promoted by this material/tooling improvement.

Adding the catalog changes future embedded/accompanying notice inputs. Earlier
consumer passes do **not** verify these newly packaged bytes. Next use one new
immutable, narrowly scoped Core/IO packaged-consumer run rather than repeating
unchanged Android/WebView, UIKit or navigation executions. Full 21-root/native/
minimum-platform consumers remain separate. Ordinary dependency trust, actual
parent acquisition/leases, Android/provider/device, API/ABI, native payload
provenance and legal disposition remain [release gates](release-readiness.md).
