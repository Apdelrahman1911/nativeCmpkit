# Native consumer606: genuine staging, current metadata and legacy license prerequisites

**2026-11-04; metadata/source analysis only.** The lead supplied independently
supplied producer revision `7d6b6d5b43f93ae085dc66a3377b3c7967400bf7` and authorized
bounded locked/offline Cargo metadata and public material inspection. This packet
precedes the separately qualified legacy WinAPI adapter; **no adapter, native
build, local publication staging, JNI, consumer acceptance, issue closure or
release occurred here**. It supports the still-open #2/BUILD-003,
#38/BUILD-004 and #3/BUILD-006 preparation work, not their completion.

## 1. Existing local repository is not a genuine complete candidate

The once-recorded [actual inventory](actual-stage-inventory606.json) inspects the
real existing `build/verification-repo`, not constructed success fixtures:

- 355 files / 12,506,337 bytes; candidate spelling `0.1.0-preview.1`.
- Only Core and UI have both selected metadata and desktop publications: **4 of
  42 coordinates**. The other **19 desktop roots**, including IO, picker and
  Share, are absent. All21 artifact names come from unchanged
  `docs/migration/identity.json`, SHA256
  `e22b14ae58bd188e4d8b14d4cf20b1bfeed49a74b8088ee97d309bde7520fb88`.
- The two Core POM names remain `nativeCmpkit - core`, not the current display
  `NativeCmpKit - core`. Matching coordinates do not certify current bytes.
- Picker and Share desktop JARs are absent. The five inspected file types are
  presence observations, **not** the complete verifier's requirements: companion
  `-notices.zip` files and metadata-declared payloads also need inspection.
- Metadata/desktop publication counts are 2 each; Android, JS, Wasm, iOS arm64
  and iOS simulator arm64 counts are 1 each. These are not full21 target sets.
- The complete stage stat map was held before/after. The recorded dirty original
  root `b3d02d96…` is a read-only observation, not independent producer custody.

[Existing host manifest observation](stale-native-resources-observation606.json)
likewise admits nothing. Both linux-x64 manifests claim dirty source revision
`144c586c28b01cfa253b6f09de26ba15771ade1e`, version `0.1.0-SNAPSHOT`, and pinned
Rust1.98. The picker's 28 old inventory entries match immutable7d6 Git bytes, but
wrong version/revision/dirty provenance remain. Share matches only11/13 old
entries and omits both newly added AppKit test paths from the sealed current
input subset. Matching old entries do not prove a complete new source inventory
or native execution. Neither manifest was regenerated, relabeled or installed.

## 2. Genuine current metadata: two new successful metadata-only commands

A fresh detached temporary producer was checked out at exactly7d6. Its Git
status, including untracked/ignored outputs, stayed empty. External output paths
were used; no dependency, source or stage edit was made.

```sh
PATH=/root/.cargo/bin:$PATH \
  timeout --kill-after=5s 60s python3 -B scripts/native/artifacts.py metadata \
  --root "$INDEPENDENT_CLEAN_PRODUCER" --module calf-file-picker \
  --output "$FRESH_EXTERNAL_METADATA/calf-file-picker.json"
# Same owning command for --module calf-share and its own new output.
```

The [actual receipt](metadata-current606/metadata-current-receipt606.json) records
Rust/Cargo1.98.0, **46 owning input hashes held** and unchanged preexisting stage:

| Owner | Exit / seconds | Packages, including local root | Exact sanitized output SHA256 |
|---|---:|---:|---|
| Picker | 0 / 0.365254619 | 93 (92 registry) | `e53bd784aae97aab724d887e7256bac6cf7c0497ef7a0ac9387e11c4060d8524` |
| Share | 0 / 0.214679416 | 48 (47 registry) | `63e8c694ed7cc4a33e6419b7cd9307ca999b118ccd3d2ed980b202f20cda880a` |

These original JSON graphs are retained beside the receipt. Their scope is the
actual conservative unfiltered locked union, including development dependencies,
**not** compiled/linker reachability, complete platform support or legal approval.
The original root's build/native-metadata files were stale; no stale receipt was
substituted for these new commands.

## 3. Genuine current license collection still fails

Each owner's genuine graph was passed once to the existing collector, the actual
checksum-verified public registry cache and the unchanged reviewed JNI catalog:

```sh
timeout --kill-after=5s 90s python3 -B tests/consumer/collect_native_licenses.py \
  --metadata "$FRESH_EXTERNAL_METADATA/calf-file-picker.json" \
  --registry-cache "$EXPLICIT_EXISTING_PUBLIC_REGISTRY_CACHE" \
  --vcs-supplements "$INDEPENDENT_CLEAN_PRODUCER/licenses/native-dependency-supplements" \
  --output "$FRESH_EXTERNAL_NOTICES/calf-file-picker"
# Same owning command and separate empty output for Share.
```

[Original receipt](notices-current606/notices-current-receipt606.json) and both
[Picker](notices-current606/calf-file-picker-licenses-report.json)/
[Share](notices-current606/calf-share-licenses-report.json) failed reports remain:

| Owner | Exit / seconds | Packages | Actual missing-text gaps |
|---|---:|---:|---:|
| Picker | **1** / 1.868765341 | 93 | **17** |
| Share | **1** / 0.765783511 | 48 | **15** |

All12 helper/catalog source inputs, both metadata inputs and92 distinct actual
registry archive stat identities stayed held. The original15 shared objc2-family
identities remain listed verbatim. They are not30 separate dependencies. The two
additional picker gaps are `winapi-i686-pc-windows-gnu 0.4.0` and
`winapi-x86_64-pc-windows-gnu 0.4.0`. Every missing-text reason is retained:
“No license/copyright/notice text found; SPDX declaration alone is insufficient”.
`complete_material_collection=false` and `license_obligations_reviewed=false`.
No report was installed in live build/native-notices.

The [real current dependency lookup](current-winapi-dependency-paths606.json)
shows picker → JNI0.21.1 → libloading0.7.4 → winapi0.3.9 → each GNU import crate.
Picker explicitly enables JNI `invocation` only in **dev-dependencies**. The
unfiltered union includes this feature; it is not evidence that production JNI
or a published host binary links the GNU libraries. Rfd is not assumed to be the
cause. No target filtering or development-dependency exclusion waives notices.

## 4. Exact source-backed WinAPI correspondence; no fabricated VCS proof

Both real archives match the original locked SHA256s:

| Exact package | Archive bytes / members / uncompressed bytes | Locked SHA256 |
|---|---|---|
| `winapi-i686-pc-windows-gnu@0.4.0` | 2,918,815 / 1,391 / 50,931,525 | `ac3b87c63620426dd9b991e5ce0329eff545bccbbb34f3be09ff6fb6ab51b7b6` |
| `winapi-x86_64-pc-windows-gnu@0.4.0` | 2,947,998 / 1,420 / 53,158,180 | `712e227841d057c1ee1cd2fb22fa7e5a5461ae8e48fa2ca79ec42cfc1931183f` |

Neither published archive has `.cargo_vcs_info.json` or license texts. The v1
adapter's three mandatory crate proofs correctly reject this different contract;
no synthetic VCS file was added. Both manifest identities explicitly declare
`MIT/Apache-2.0` and `https://github.com/retep998/winapi-rs`.

The first ad hoc passive comparison refused its research-only1MiB per-member
bound; that [original refusal](winapi-origin606/correspondence-first-refusal.json)
remains. The cached public source reports two libraries per target above1MiB,
with maximum1,658,338/1,670,630 bytes. Recovery uses its own2MiB read/64MiB total
bounds, not a weakened checked-in collector or publication limit. Source/Git,
header/type/link/path/checksum bounds remain. This is research, not a passed
library/unit/native test.

The complete original archives were fingerprinted **once** against source0.3.6
`4ac6c90e…`: 2,809 nonnormalized members compared, 2,807 matching, only the two
original manifests mismatching. The normalized Cargo registry manifests are
separately preserved, not falsely labeled Git blobs. All2,807 accepted payload
fingerprints and both failures remain in the compressed original reports.

[Public immutable file history](winapi-origin606/i686-manifest-history.json)
identifies `fa4e2c5a6dc495c71e6031bdde2e52870ebf6fdf` (2018-06-07),
**“Include licenses in import library crates”**. It adds the two license include
paths after the0.4.0 publish without changing that version. This explains the
missing archive texts and the later manifest mismatch; no current code fix is
inferred from a package version alone.

The earlier exact publishing source
[`9497609ef44cc9bcd16cd2411c0ee6ccaf5483aa`](https://github.com/retep998/winapi-rs/commit/9497609ef44cc9bcd16cd2411c0ee6ccaf5483aa)
(2018-02-05, “Publish 0.3.4”, with both import crates0.4.0) resolves only those
failed manifest operands. Its root tree is
`8146a2db00f01713763b925d8b5a8f13bf917f7a`. The separately acquired original
commit/tree JSONs and **all16 reconstructed Git tree objects** agree. Source0.3.6
also retains its17-tree check and the API's commit-alias-versus-root distinction.

[Exact earlier-source qualification](winapi-origin606/publish-0.4.0-origin949/correspondence-summary.json)
reuses the once-computed real archive fingerprints, without decompression or
accepted payload comparison replay: **1,390/1,390 + 1,419/1,419** match; two earlier
source-manifest failures recover. This is2,809 member fingerprints, not2,809 tests.
Original source responses were acquired once per distinct URI; no source archive
was extracted or executed.

The older genuine source LICENSE-MIT starts **“Copyright (c) 2015 The winapi-rs
Developers”**, 1,068 bytes, SHA256
`5b19674a1db628a475850a131956ed49521b744e3dda8f5a94141f9aba681219`, Git blob
`796e929aa550bcf4840b199500b7c5bf96edcb75`. LICENSE-APACHE is11,357 bytes, SHA256
`b40930bbcf80744c86c46a12bc9da056641d722716c378f5659b9e555ef833e1`, Git blob
`8dada3edaf50dbc082c9a125058f25def75e625a`. Exact root manifest/license bytes agree
with that earlier source tree. The later2015–2018 text is preserved separately,
**never substituted** for the earlier origin. Source correspondence is not a
signature, registry authenticity assurance or legal obligations decision.

## 5. Custody, retention and the next separate patch

[Producer custody seal](producer-custody-seal606.json) rechecks all46 metadata and
12 collector source hashes and seals **241 original external output files**.
Only the new clean detached temporary producer was removed with lead permission,
after confirming no ignored/untracked outputs. Git7d6 remains preserved; all
other worktrees/caches/stages stayed untouched. Free space rose from9,008,504,832
to10,092,711,936 bytes. Subsequent source/evidence work also stays above8GiB.

[Public originals seal](source-originals-seal606.json) binds46 copied original
files/envelopes. Gzip wrappers use `mtime=0`; the original byte sizes/SHA256s remain
alongside compressed hashes. No completed original is renamed a fresh execution.
The zero-native/zero-staging fields are deliberate; legal gaps remain unwaived.

The lead authorized a **separate** narrow legacy no-VCS adapter proposal backed by
this exact commit/root/checksum/fingerprint record. It must:

1. Keep the existing v1 schema/proofs/fallback/refusals unchanged; no guessed
   `.cargo_vcs_info`, generic missing-origin or SPDX-template fallback.
2. Admit only these two reviewed exact archives and full source/license/proof
   bytes. Reject altered/self-rehashed correspondence, origin/license, absent
   member proof, linked/unsafe/bounded inputs and asserted legal clearance.
3. Reuse the sealed archive payload fingerprints, rechecking only compressed
   archive checksum/identity; do not rescan accepted payloads. Add important new
   negative source/material controls and record genuine narrowly scoped collector
   outputs while keeping unexecuted ordinary dependencies explicitly incomplete.
4. Preserve both real17/15 failed reports. Never merge a partially rechecked
   collector report and claim a fresh full93/48 run or legal/material clearance.

Only after real complete all21 selected metadata/desktop staging, complete legal
materials and independently reviewed clean producer/source/native custody exist
may the lead run the [original missing-three consumer command](../native-consumer-preflight20261104/README.md).
The preparation command below is **NOT EXECUTED** and requires the coordinated
serial heavy slot and fresh producer's own empty build/verification-repo:

```sh
./gradlew stageVerificationPublications \
  -PnativecmpkitVerification=true -PnativecmpkitVerificationTargets=desktop \
  -PnativeCmpkit.version=0.1.0-preview.1 -PnativecmpkitNativeMode=host \
  --max-workers=2 --no-configuration-cache
```

`PublicationNotices.kt:64–99` still requires complete owning reports and exact
manifest/lock hashes before publication. `NativeLibraries.kt:17–117` still
requires real native resource validation; host mode is only a one-host diagnostic,
not full-five release acceptance. No arbitrary repository, Maven-local, remote
publication/allowPublishing flag, main/history mutation or Pages restoration is
part of this work. Other native/minimum-device/dialog/leak/ABI/dependency/legal/
security and release-readiness gates remain independent. **No issue closure or
publication is proposed by this packet.**
