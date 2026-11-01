# #102 / NAV-015 and #118 / PERM-024 — sealed private pre-review

**No native acceptance or closure.** No tests/builds/SDK/API/Git operations or live
edits. #58 stays sealed/unintegrated. Earlier full **1068/1145** readback passed;
final comparison sees only the lead's **two Apple help/guard** changes. All other
frozen entries and all **16 sample-menu inputs** still match. This is explicit
lineage, not a relabeled current whole-source freeze. Literal findings, resolutions
and `local001/original-criteria.json` agree on all six original criteria.

## Original criterion → current source/local result → required actual proof

| Criterion (literal text retained in criteria-map.json) | Source / local result | Actual evidence needed |
|---|---|---|
| #102 C1: merged manifest/every menu permission/expected supported-API declaration/status | General sample24 rows, no Call/all-files/SMS; legacy READ≤32/WRITE≤28. Actual debug/release merge **0/53.01s**, both24-row/16-input correspondences; expected API24–37 status. | Reuse exact XML and unchanged source hashes. Predictions are not OS observations; no extra24-row native suite. |
| #102 C2: fresh Call under explicit approved demo variant | `AndroidPermissionDemoDeviceTest:35–54`; separate signature-controlled public-library variant. Helper **0/107.02s** and offline manifest/signer surface, not install/grant. | API35 `callOnFreshApprovedVariantUsesPublicRequestAndActualSystemGrant`: fresh install/bytes/signature/separate UID, initial denied and no automatic grants, real system Allow, native grant + one true public callback, cleanup. No phone call. |
| #102 C3: file/image picker without all-files/unrelated SMS | Test87–109; public launchers, owned MediaStore seeds, bounded KmpFile read/hash/source checks. Offline helper manifest excludes forbidden declarations. | API35 `pickersReadRealDocumentsAndImagesWithoutAllFilesOrSmsPermissions`: installed forbidden permissions absent, real document/photo UI results, one content URI each, exact bytes/hash/source, media still denied/active reads0, owned cleanup. |
| #102 C4: denial/permanent denial + Android13/14 media | Test56–85 and `AndroidMediaSelectionDeviceTest:31–76`; source/offline exact signer only. | API35 denial method, plus **separate API33/API34** media-method XML. Denial: rationale true→false, third no dialog, one callback/request, Unknown requestability. API33: public-library full image/video request. **API34: actual platform-selected grant, then public-library Available/Limited observation with full media false/legacy denied/zero library callbacks/no lastRequest. Not a library-selected request result or selected/unselected read proof.** |
| #118 C1: API28/29 legacy/scoped, API30+ app-scoped/SAF, all-files absent/present | `AndroidStorageCompatibilityTest:33–125,127–193,213–268` and static source-app flavors. Original storage **FAILED1/73.02s** retained; five-source recovery integrated. **Six storage compiled manifests remain outside four-APK readback.** | Eight exact selectors below; original passing XML + per-route actual compiled/source/installed/signer/UID proofs. Legacy29 native WRITE is separate despite Granted/NotRequired; scoped stays bounded. Real normal-UID257-byte descriptor hash/closure, system SAF result/persist/read/release, manifest-only manager false→explicit owned allowance→restored default/false. Not Settings UI. |
| #118 C2: least permissions/no unrestricted-disk Granted description | `docs/permissions.md:150–154,198–242`; READ≤32/WRITE≤28, no ordinary all-files declaration, explicit NotRequired≠all-files, target/mode caveat and app-scoped/SAF/media alternatives. Production mapping unchanged. | Reuse literal docs/source hashes and correlate native matrix. No new docs-test replay or unrelated physical/consumer/release criterion. |

## Storage per-route contract (not already-inspected compiled surfaces)

| Profile | API / flavor / target | Required original method |
|---|---|---|
| android-storage-api28 |28 / legacy28 /28|api28LegacyPermissionControlsSharedStorage|
| android-storage-api29-target28 |29 / legacyTarget28 /28|api29Target28LegacyAccessStillNeedsNativeWriteDespiteNotRequiredHelper|
| android-storage-api29-legacy |29 / legacy29 /29|api29Target29LegacyAccessStillNeedsNativeWriteDespiteNotRequiredHelper|
| android-storage-api29-scoped |29 / scoped29 /29|api29ScopedAccessStaysBoundedWithNativeWriteGrant|
| android-storage-api30-normal |30 / modern /35|modernAppScopedAndSafDoNotNeedAllFiles|
| android-storage-api30-all-files |30 / allFiles /35|modernManifestAloneDoesNotGrantAllFilesAndOwnedSettingRestores|
| android-storage-api35-normal |35 / modern /35|modernAppScopedAndSafDoNotNeedAllFiles|
| android-storage-api35-all-files |35 / allFiles /35|modernManifestAloneDoesNotGrantAllFilesAndOwnedSettingRestores|

Require `storage-probe/receipt.json`↔`controller.json` fields enforced at
`scripts/ci/android_storage_probe.py:393–435,558–602`: exact profile/API/flavor/target,
source contract, fresh single-APK installed hash/normal UID, no automatic runtime
or manual URI grant; actual compiled helper static-permission/signature/DUMP policy
and reporter no-storage-permission/document-needs-grant policy; common controller
certificate with exact min=max=route API signer checks. Initial state has no record,
Activity, persisted/native URI grant or WRITE; API30+ managerfalse/mode3.
`ordered_saf_activity_cleanup` and `final_native_restoration` must prove those
absences again before owned uninstall, with `cleanup_status=passed`, removal and
no error. Source/XML link proves native operations, not a standalone receipt flag.

Each route needs original library plan/receipt/before-after maps, fresh
hash-matching `routes/<profile>/fresh-reports/*.xml`, exact connected task/selectors,
no skipped/missing/duplicate/substituted methods, and owned helper/emulator/ADB
cleanup. The1145 map remains a local sample-combined freeze, not an invented
uploaded actual combined artifact; use uploaded library maps and exact Git/source
linkage.

## Closure boundary

**No genuine uncovered literal original obligation identified.** #102 needs
**5 target executions/4 methods**; #118 **8/6**: together13 executions/10 methods/
11 original XML reports. The unrelated three IO methods are not substitutes.
**Both fixed batches contribute to both issues.** API35 supplies Call/denial/
pickers + two storage rows; compatibility supplies media33/34, API28, threeAPI29
and twoAPI30 rows. Close an issue only after every original criterion and source/
results/readback review; passing subsets are progress only. Preserve original
failures, refuse missing routes, and do not replay accepted suites/manifests.
