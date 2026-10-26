# Exact-commit objc2 license material reassessment

**No same-commit complete license text was located in the inspected scope. No
live notices were installed and no legal or distribution gate was cleared.**
The prior archived collector failures remain correct as historical archive-only
observations; this follow-up does not silently rewrite them.

## Evidence chain rechecked

The [prior frozen collection](../../../native-license-material-20261024T193225Z/README.md)
contains 118 hash-verified files, including checksum-verified crate manifests,
`.cargo_vcs_info.json`, exact GitHub manifests and root license policy bytes.
All 118 were independently checked again before using those mappings.

`crate-reverification.json` records the following checks for each of 15 distinct
objc2-family package identities present in **both** conservative locked graphs:

- Current native Cargo manifests and locks still equal the hashes in the original
  locked metadata; no re-resolution or graph change was used to find easier terms.
- Crate SHA256 equals both corresponding lock entries and the archived mapping.
- Normalized name/version/license, original manifest and VCS metadata bytes match
  the exact public `.crate` from the existing cache.
- Original package/workspace manifests and root policy bytes recompute to the
  same Git blob IDs in newly retrieved exact-commit trees.
- Every packaged regular file was read within explicit size/member bounds,
  without archive-directed filesystem extraction, symlink following, build
  scripts or execution. Selected README bytes were copied as inert data to
  predetermined review paths, not to live build inputs.

The all-target graphs are conservative unions, **not proof every package is
linked into every host binary**. No such distinction was used to bypass the
existing full-matrix material gate.

## Exact trees: where could a complete text have been missed?

All five unauthenticated public recursive Git-tree requests returned HTTP200 and
`truncated=false`; original JSON and retrieval metadata are in `trees/` and
`tree-retrieval.json`.

| Package group | Exact source commit | Tree entries |
|---|---|---:|
| Eleven framework crates at 0.3.2 | `7b1abfd750a2cacaea71d6a56ecfb83cb7de560b` | 2,294 |
| dispatch2 0.3.1 | `8852b424193ca41602281b3d7540d7c8ed51e49a` | 2,173 |
| objc2-encode 4.1.0 | `8d214f5477365ffcbcbb7de058c86ed9a518efb7` | 1,595 |
| block2 0.6.2 | `b4167b582b2f75f9a1be75495c41b765344fd03c` | 2,169 |
| objc2 0.6.5 | `d7d2fa23ceaa5e6096c923b081040e5d81b3b9df` | 2,173 |

Each tree contains only root `LICENSE.md` as a genuine conventionally named
license/copyright/notice/DEP5 file. Other substring hits are copying-related
Rust source/test/expected-stderr files, **not licenses**. In particular,
`objc2-foundation/src/copying.rs` is not accepted as COPYING material—the exact
false positive already repaired in the first collector stays rejected.

The root policy has the same bytes at all five commits:

```text
bytes: 1339
Git blob: 540ae4c81adb5f64a9f61e222b688880da24300e
SHA256: 7f976f7e9cb2d87df7230606feb932c3f21ac0e664045a775b600046ff850c54
```

It declares license choices and links to OSI's MIT page, zlib's license page and
Apache's 2.0 text. Those external URLs are **not complete text stored in the
pinned commit**. The actual links and declarations are retained as evidence;
this is not a claim that the crates have no license.

The packaged READMEs are separately preserved. Most link to `../../LICENSE.md`.
The older objc2-encode README links to floating `master/LICENSE.txt`; that file
is absent from its complete pinned tree. No unrelated later/earlier revision or
generic copyright placeholder was silently substituted.

## Packaged content search, and its limit

Across all 15 exact packages, **1,130 regular files / 14,997,918 bytes** were read.
No MIT permission/warranty, Apache complete-terms start/end, or Zlib origin/
notice-retention marker was found. The exact byte-pattern rules and per-crate
counts are in `crate-reverification.json`.

This is a bounded lexical check, not a semantic proof that no differently worded
license-like statement can exist. Arbitrary **non-packaged** source blobs were
not downloaded and content-searched in full; the complete tree check establishes
the conventional license-file search boundary. Git/checksum correspondence is
integrity evidence, not a verified publisher signature or legal opinion.

## License choices and distinct unresolved questions

Four exact package manifests and root policy declare **MIT only**:

- block2 0.6.2
- objc2 0.6.5
- objc2-encode 4.1.0
- objc2-foundation 0.3.2

The remaining eleven declare `Zlib OR Apache-2.0 OR MIT`. A workspace-level OR
expression must not be applied to the four MIT-only exceptions.

The policy's referenced [issue #23](https://github.com/madsmtm/objc2/issues/23)
was read back in `upstream-license-discussion/` with its **three** comments;
pagination was not truncated. It remains **open** and is specifically about
relicensing under MIT/Apache-2.0/Zlib and removing MIT copyright notices. The
original issue identifies outstanding contributor permissions; the final comment
retracts an apparent confirmation and asks for clarity. This mutable discussion
does not supply an immutable license text, confer permission on our project or
establish that the four exceptions became trio-licensed.

Separately, pinned `LICENSE.md` says the crates are derived from Apple SDKs,
links the Xcode license and states uncertainty about distributing derived works.
Its practical Xcode/linking explanation is an **upstream explanation**, not our
legal conclusion that SDK acceptance discharges every downstream obligation.
Issue #23 does not resolve that separate question. Nothing here establishes an
actual unlawful distribution or exploit.

## What is still available, and what remains blocked?

The previously preserved **jni-sys-macros 0.4.1** supplement is different:
complete MIT and Apache texts exist at its exact `jni-rs/jni-sys` commit
`64d77b7a5f119d7b55b4e2c169a4668067ff59e6`, with the original macro manifest
matched. Those bytes remain available; this follow-up did not retrieve or replace
them. The archive-only collector still reports 16 gaps because it has no external
VCS supplement adapter: one JNI text gap is independently addressable, while
the 15 objc2-family complete-text gaps were **not resolved by this review**.

Potential next work requires an explicit, reviewed material/provenance policy:

1. For JNI, bind any adapter to the existing crate checksum, VCS path/commit,
   matching manifest and exact supplemental text digests; preserve external origin.
2. For objc2, obtaining a canonical standard text externally would be a **new
   externally sourced supplement**, not a same-commit file. It must not invent
   copyright holders/years from an author field or imply that outstanding notice
   or relicensing permissions were granted. Preserve the exact project declarations.
3. Obtain a documented maintainer/legal disposition for the remaining notice and
   SDK-derived-work questions before claiming distribution clearance. Do not
   waive a gate or change dependency versions solely to make the report green.

No automatic live installation, generic-text substitution, lock change, release
publication or claim of legal clearance follows from this research.
