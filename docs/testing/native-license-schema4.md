# Exact objc2 schema4 material and original-notice carry-forward

**2026-11-04 — source/material controls only.** This procedure supports the native
consumer prerequisites for #2/BUILD-003, #38/BUILD-004 and #3/BUILD-006. It is not
issue closure, actual candidate staging, native functionality, legal clearance,
security acceptance or authorization to publish. The lead must independently
review the source/results before using it in a genuine clean producer.

## Active format, without changing the inert v2 format

`tests/consumer/native_license_objc2_material.py` implements an explicit schema4
adapter. Its independently source-reviewed index is
`licenses/native-dependency-supplements/objc2-reviewed/manifest.json`, SHA256
`4f10a64a9a62c07484cd1d45512141ea91b5652078b004b6e30e39988b218131`.
There is no producer-supplied digest override. Editing or rehashing that index
requires new independent source review, not an asserted successful report.

All fifteen identities are required in both current conservative Cargo locks:

- `block2@0.6.2`, `dispatch2@0.3.1`, `objc2@0.6.5`, `objc2-encode@4.1.0`;
- `objc2-{app-kit,cloud-kit,core-data,core-foundation,core-graphics,core-image,
  core-text,core-video,foundation,io-surface,quartz-core}@0.3.2`.

The exact two module `Cargo.toml` and `Cargo.lock` inputs must match the reviewed
public index. The adapter keeps all three published Cargo/VCS proofs and original
raw source commit/tree/path/blob and workspace-inheritance proofs. Only bounded
raw-object/workspace/snapshot primitives are reused from
`native_license_material_v2.py`; its pending material API, schema and tests remain
inert and byte-identical. Ordinary schema1 JNI and schema3 WinAPI formats remain
separate. Unknown entries or original identities do not become new fallbacks.

### Grants, credit and unresolved provenance

Four packages (`block2`, `objc2`, `objc2-encode`, `objc2-foundation`) retain only
their original MIT option. The other eleven retain all original
`Zlib OR Apache-2.0 OR MIT` options. No option is selected or widened.

The complete Mads MIT/Apache/Zlib notices come from the distinct later raw origin
`ee9a7ada2131f5944b8750428e265c15632f2a19`, not a fabricated original release
notice. Steven Sheldon's complete inherited MIT notice is genuinely yearless:
`Copyright (c) Steven Sheldon`. Do not invent a date or infer copyright from a
Cargo author field. Additional notices are credit, not added package grants.

The actual published `objc2/src/__macro_helpers/os_version/apple.rs` credit to
Rust PR138944 is preserved with full Rust `LICENSE-MIT`, `LICENSE-APACHE` and
`COPYRIGHT`. Rust MIT does not name a copyright holder; the full contributor
policy cannot be dropped. Three different identities stay different:

| Rust material context | Revision |
|---|---|
| Fixed API-reported notice/source revision | `1e5719bdc40bb553089ce83525f07dfe0b2e71e9` |
| PR merge revision | `349fbba24f0158c1ed293658c31de5c8a0954e5a` |
| PR head revision | `846d6a4466813f3ad12e2bf15db4071f22b8ae0b` |

The supplied Rust commit/tree are API JSON, **not raw commit proof**. The reader
refuses raw-commit/publisher or merged-source promotion. Preserved public
issue23/five comments and issue826/eleven comments are historical context, not
publisher permission notices or all-contributor consent requirements. Existing
license grants are not contingent on obtaining relicensing consent from everyone.

The once-performed locked payload scan holds 1,130 regular files: 309 same-path
Git matches, 30 generated published metadata records, two file-level forwarding
symlinks, 774 Git-absent generated SDK source files and 15 crate `Cargo.lock`
files. The actual forwarding symlink text is
`../../../../crates/objc2/src/rc/retained_forwarding_impls.rs`.
Twelve Git generated-directory symlink targets have not been acquired/verified.
`.gitignore` is not generation/exclusion proof; its Cargo.lock rule is commented
out. Generated SDK source equivalence, Cargo.lock generation provenance, SDK
distribution/applicability, exhaustive contributors, publisher signatures, legal
obligations and release readiness remain explicitly false or unreviewed.

## Execution and output ownership

`native_license_supplements.load_supplements()` captures the active set once for
a requested registry graph, returns recursively immutable owned snapshots, and
rejects duplicate or foreign identities. The shared `_reviewed-objc2/` proof pool
contains exactly147 public files/1,670,040 bytes once per module, not fifteen
physical copies. Reports still bind each package to its full proof/text record.

The collector's explicit schema3/4 paths recheck compressed archive size/SHA256
against already reviewed correspondence. They do **not** open tar payloads again.
The collector refuses conflicting shared bytes before output and copies shared
proofs once. `ArtifactVerifier.native_notices()` independently compares all exact
records, source-controlled origin and complete proof/text bytes; it holds shared
archive proof reads once and still records every package's obligation. A
producer-rehashed report or text cannot replace the reviewed source material.

When collecting a genuinely new graph with schema4, pass `--source-root` along
with the explicit public supplement root. This is not needed for a genuinely
ordinary schema1/schema3 catalog. Do not use a source-free or stale metadata root
as the current four-input witness.

### Repair only the two existing failed original reports

`tests/consumer/carry_forward_native_licenses.py` is deliberately not a general
resume/merge CLI. It admits only the independently pinned original Picker93/17
and Share48/15 reports and metadata. It validates exact conservative package
coverage/current Cargo hashes, complete original ordinary/JNI notice/proof bytes,
the exact known gap set/reason and a finite inventory without foreign entries.
Original failed reports and their accepted public bytes remain untouched.

Only the original17/15 gap rows may receive schema3/4 material. Each exact cached
compressed archive must rebind its own checksum and size, without ordinary/JNI
payload rescan. The helper derives a **new** report from actual complete coverage,
keeps legal/readiness false, and rechecks all four current Cargo inputs before and
after writing. A complete new report is not a native producer revision witness.

The lead's future independently reviewed operation is:

```sh
python3 -B tests/consumer/carry_forward_native_licenses.py \
  --original-notices "$EXACT_ORIGINAL_PUBLIC_NOTICE_ROOT" \
  --module calf-file-picker \
  --source-root "$INDEPENDENTLY_REVIEWED_CLEAN_CURRENT_PRODUCER" \
  --registry-cache "$EXPLICIT_ORIGINAL_PUBLIC_CRATE_CACHE" \
  --output "$NEW_EXTERNAL_MODULE_NOTICE_ROOT"
# A separate new output for --module calf-share, with its exact original input.
```

Output must be a new canonical absolute path, have existing unlinked directory
ancestors, and not overlap original/source/cache inputs or Git metadata. Every
relative file is validated and bounded before creation; file/directory overlap,
symlinks/hardlinks and extra inventory refuse. Refusing partial output is retained
for review, never silently deleted or merged. These observations are not an OS
sandbox against an independently malicious same-UID filesystem writer.

The 2026-11-04 agent qualification did **not** execute that genuine CLI, derive a
real complete report, install notices into live build resources, perform consumer
carriage, stage packages, build native code, execute JNI or publish anything.

## Bounded verification results and future work

The [676–677 packet](../development/evidence/current-platform-recovery-20261101/objc2-adoption676-677/README.md)
retains NEW23/23 controls once (0.402084s), two genuinely affected synthetic-v1
collector/verifier methods once (0.036250s), original verification-only captures
once (0.132618s), and unchanged inert/public consumer source hashes. These are
separate scoped executions, not an unexecuted all-green native/staging suite.

```sh
PYTHONPATH=tests/consumer python3 -B -m unittest -v test_native_license_objc2_material
```

The controls cover exact fifteen/four-input/index custody, changed/raw/self-rehashed
proof refusal, grant/credit distinctions, Rust/generated-source nonpromotion,
immutable snapshots, one shared proof pool, synthetic compressed identity without
tar calls, synthetic collector/verifier record/text/proof corruption, pinned
original report/metadata/text refusal, known-gap foreign/v2 rejection and owned
filesystem preservation. The verifier test exercises the notice method in an
explicit synthetic unit object, **not** the full constructor/native provenance
gate or candidate acceptance. No old Git-based carriage setup is run.

Verification-only real original capture holds Picker154 files/835,391 bytes and
Share74 files/387,903 bytes. Both still have17/15 gaps and material/legal false.
These are files and methods in different scopes, not native methods or new
successful collections. Source/control acceptance must precede a new genuine
gap-only material derivation; only then can the lead schedule full21 genuine
candidate checks and exact host JNI3 with fresh owned XML. All platform/native,
consumer, API–ABI, dependency, security, legal and release gates remain separate.
