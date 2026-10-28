# Direct font-notice and Android-asset acceptance

**NAV-009 / [issue #17](https://github.com/Apdelrahman1911/nativeCmpkit/issues/17)
closed 2026-10-28 at 07:44:37 UTC**, immediately after important artifact checks
and source/results review, before writing this documentation. The original
issue title, body, labels and upstream references were preserved. The readback
confirms `closed` / `completed`; the repository now has **41 closed issues**.

## Owning repairs and compatibility

Immutable `63d1004a851abc92e00c90a9deeff083a1038c9e`:

- `calf-cupertino-icons/src/commonMain/composeResources/files/nativecmpkit/`
  carries the complete, unchanged canonical MIT notice and provenance beside
  the font, including **Copyright (c) 2016 Vladimir Kharlampidi**.
- `verifyCupertinoResourceNotices` checks the original font/license pins and
  exact equality of both resource copies; resource preparation and publication
  notice verification depend on this guard. Missing/changed material fails.
- `Android.kt` previously enabled resources only inside the device-test-host
  branch. The **actual fresh Android AAR had no font or assets**. Production
  Compose/Android resources now enable packaging independently; no instrumentation
  host was added to disguise missing production configuration. Resource-free
  modules retain their resource-free default, and existing device fixtures retain
  resource packaging.
- The owning Maven artifact verifier now rejects a font-free icon AAR and requires
  the exact MIT/provenance for every actual font-bearing resource distribution.
- Documentation explicitly distinguishes Flutter's CupertinoIcons font from
  Apple's system symbols. The public generated-resource package, `sf_symbols.ttf`,
  glyph bytes and existing public constants remain unchanged.

## Important checks, actual results

The [immutable build receipt](after002/receipt.json) records the exact eight tasks,
exit **0 / 56.02 seconds**, stable before/after inputs, and seven fresh inspected
archives. **All 772 recorded inputs match their own Git blobs** at the tested SHA;
see the [source and three-criterion review](after002/source-and-acceptance-review.json).

| Actual built output | Font | Complete MIT and provenance | CRC/freshness |
|---|---|---|---|
| Desktop JAR | Original retained path/bytes | Exact, beside font | Passed |
| Android AAR | Original path under `assets/` | Exact, beside font | Passed |
| iOS Arm64 resource ZIP | Original retained path/bytes | Exact, beside font | Passed |
| iOS simulator Arm64 resource ZIP | Original retained path/bytes | Exact, beside font | Passed |
| JS resource ZIP | Original retained path/bytes | Exact, beside font | Passed |
| WasmJS resource ZIP | Original retained path/bytes | Exact, beside font | Passed |
| Companion-notices ZIP | Not a font archive | Exact canonical texts | Passed |

Font SHA256: `67c44fe9183b002e79dde7f6977e2988661c9a3e4a3c5fce968787efdbed823c`.
MIT SHA256: `310d6ab6483280280c9db122bded0a63c09558bc5743720f61dbcbb494db370a`.
Provenance SHA256: `ad37d4bc96ef68b09dd913be3f32bd4e6871eb6c4af466d954b3da8ccbe2d10d`.
Archives were read without extraction. Private build binaries are **not committed
or uploaded**; entry names, file hashes and source receipts provide the evidence.

Separately, the just-before-commit worktree's unchanged tooling passes
**73/73 artifact-verifier methods** (including six new focused font regressions)
and **9/9 catalogue methods**. Their source matches the committed repair. These
are tooling executions, not library or native runtime tests. The catalogue retains
1,322 constants, 1,234 glyph mappings and 6,984 system-name strings; Apple OS minimum
availability remains explicitly unknown.

## Preserved defects and boundaries

[Before receipt](before001/receipt.json) retains five font-bearing outputs lacking
the notice *inside the copied resource bundle*. The Desktop JAR already had a
complete module-scoped `META-INF` notice; do not misstate it as wholly unlicensed.
The companion ZIP was already exact. The original receipt omitted the font-free
AAR, so its wording does not establish complete seven-artifact coverage; the
[separate actual AAR inventory](before001/android-aar-font-observation.json)
records all its entries and zero assets/fonts.

All three original NAV-009 criteria are accepted: original pinned font bytes;
complete copyright/permission in actual font distributions or their companions;
clear Flutter/Apple documentation. Compiler KLIBs are not rewritten; the
source-reviewed publication convention attaches the canonical notices ZIP to
every coordinate, while copied Apple/browser resource bundles now retain their
own notices. Applications that redistribute resources must retain those files.

This closes this font/notice defect, **not full release readiness**. No packaged
application/framework consumer, native link/runtime, ABI, full legal review or
unrelated dependency/security gate is certified. No packages, deployments or
releases were published; `main` and the original audit/history remain unchanged.
