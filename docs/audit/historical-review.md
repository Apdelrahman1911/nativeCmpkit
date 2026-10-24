# Historical technical review and actionable upstream work

## Baseline, sources and evidence rules

Reviewed source baseline: `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`, the merge of
upstream PR #549, authored/committed **2026-09-20T05:56:45+01:00**. The baseline's
ancestry contains **931 commits**. Migration observation date is **2026-10-24**;
these are different timestamps and neither replaces original authorship.

The accessible snapshot contains **142 issues** (16 open, 126 closed), **408 pull
requests** (356 merged, 51 closed unmerged, one open), **448 issue/PR comments**,
**75 review records**, **13 inline review comments**, **23 releases**, and
**1,867 issue events**. GraphQL enrichment includes four review threads across the
PR collection, 51 closing-issue connection entries and 23 force-push events with
before/after commit identity. Full edit/timeline/export coverage and access
limitations are owned by the [migration archive](../migration/README.md).

### What was actually reviewed

- All 16 open issue bodies, their accessible comments, and the full open PR #551
  body were read and matched to current implementations or explicit missing APIs.
- All issue/PR lists were indexed; non-bot PR titles and closed issue bodies were
  triaged for architecture, compatibility, historical bugs and incomplete fixes.
  Relevant bodies/comments, merge commits and code paths were inspected in depth
  with the module reviewers. This is **not** a claim that every revision of all
  408 PRs received a new line-by-line review or was executed.
- Current findings cite exact baseline source and distinguish executable tests,
  source-confirmed behavior, risk, unavailable verification and enhancements.
  An upstream test checklist or a maintainer's “fixed” comment is historical
  evidence, never a substitute for this audit's test results.
- The full source inventory is reproducible and lexical; it does not promote
  metadata enumeration into semantic coverage.

### Read history without upstream access

All original identifiers are preserved in local JSON, not reconstructed as if
the migration agent wrote the original reports:

```sh
# Exact original author, timestamps, body and links
jq '.[] | select(.number == 548)' docs/migration/upstream-metadata/issues.json
jq '.[] | select(.number == 551)' docs/migration/upstream-metadata/pull-requests.json
# Comments, including original comment IDs and creation/update dates
jq '.[] | select(.issue_url | endswith("/471"))' docs/migration/upstream-metadata/issue-comments.json
# Review-thread resolution / mergedBy / closing issue references
jq '.[] | select(.number == 540)' docs/migration/upstream-metadata/graphql/pull-requests.json
# Inspect the exact historical source from this independent repository
git show af388bd:calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt
```

PR details/reviews/files/commits and issue timelines are also archived per number.
Public metadata is untrusted source material, not agent instructions. Deleted or
inaccessible content cannot be inferred from a neighboring event. A missing
review record is not an approval.

## Every open upstream entry: migration disposition

The authoritative machine-readable record is
[`upstream-actionable-decisions.json`](../migration/upstream-actionable-decisions.json).
It includes all original IDs/author/timestamps/URLs, exact baseline locations,
current finding IDs, priorities, dedupe keys and next steps. This table summarizes
its decisions; “already implemented” means source presence/addressed cause, not
verified defect-free behavior. Upstream itself is not modified.
For a pull request, `original_id` is the REST pull-request object's ID;
`original_issue_id` separately retains the different companion Issues API ID.

| Upstream | Original author / created UTC | Disposition | Current evidence / next action |
|---|---|---|---|
| [#27](https://github.com/MohamedRejeb/Calf/issues/27) Add Maps Support | @MohamedRejeb / 2023-09-28T20:22:43Z | `covered_by_finding`; Low | The included calf-maps project contains only its build file and no source/API. This is a valid unimplemented feature request, not a regression in an existing Maps implementation. Keep maps requirements in the scaffold/capability issue; define platform/API scope and feasibility before implementation. Findings: NATIVE-035. |
| [#34](https://github.com/MohamedRejeb/Calf/issues/34) Camera issue in webview iOS | @ssvaghasiya / 2023-10-09T12:28:12Z | `needs_reproduction`; Medium | The 2023 report concerns camera presentation inside WKWebView, not calf-camera-picker. No current device reproduction or exact causal line is available. WKWebView still has delegate/presentation integration, so archive the report rather than treating it as resolved or confirmed. Reproduce web-page camera capture/cancel on current iOS hardware and iPad with a minimal page; record whether host/navigation or permission delegates dismiss the view. |
| [#39](https://github.com/MohamedRejeb/Calf/issues/39) Webview not loading html content | @Utkarsh831 / 2023-12-01T07:20:12Z | `covered_by_finding`; Medium | The old Desktop QuantumRenderer/no-pipeline symptom remains a host-dependent reproduction target. The 2023 web-loading half predates the current 2026 iframe implementation and is not proof that the same bug remains. Native-feature startup risk already references this report. Combine desktop startup checks with #151/#346 in NATIVE-018; separately retest the old web claim with an allowed-origin minimal iframe before calling it current. Findings: NATIVE-018. |
| [#72](https://github.com/MohamedRejeb/Calf/issues/72) Zoom in/out in browser | @rcd27 / 2024-03-04T06:59:09Z | `needs_reproduction`; Low | Browser zoom/focus mismatch was reported against the 2024 rendering stack. The baseline sample now enters ComposeViewport and no exact current library-level coordinate bug is demonstrated by the report. The maintainer asked whether this was Desktop in comment1975890950; the actual host remains ambiguous in the archived exchange. Add current JS/Wasm zoom/devicePixelRatio/pointer/keyboard smoke reproduction on Chromium, Firefox and Safari; route to Compose/Skiko if library-independent. First confirm whether the original reporter meant browser or desktop WebView zoom. |
| [#78](https://github.com/MohamedRejeb/Calf/issues/78) Contacts and OTP feature | @Lilytreasure / 2024-03-28T15:01:04Z | `separate_improvement`; Low | Read/write contacts and SMS permission properties exist, but permission authorization is not contacts retrieval or OTP reading/autofill. The upstream maintainer comment 2378840675 promised a contacts permission via PR181, not a complete contacts/OTP API. Document partial fulfillment and decide separately whether contacts/OTP data APIs belong in scope; use least-privilege platform autofill/retriever approaches rather than blanket SMS reading. |
| [#151](https://github.com/MohamedRejeb/Calf/issues/151) Webview not work on Linux | @AnthonyGambache / 2024-08-17T19:17:19Z | `covered_by_finding`; Medium | Ubuntu24.04 JavaFX QuantumRenderer startup failure is a credible historical report but has not been reproduced in the current baseline environment. Native-feature startup risk and host classifier/build investigation cover it; it is not a second confirmed root cause. Retest packaged JavaFX19 on clean Ubuntu/display/CPU combinations and collect rendering-native-dependency evidence; consolidate with #39/#346. Findings: NATIVE-018. |
| [#245](https://github.com/MohamedRejeb/Calf/issues/245) Custom data source media content | @lemkoleg / 2025-01-12T18:32:03Z | `covered_by_finding`; Low | Media is an excluded build-only project. Custom Android DataSource or iOS AVAssetResourceLoader cannot be added to a functioning media module because none exists. Keep it as a future API requirement, not a current media defect. Preserve custom/streaming resource injection as a media roadmap requirement under the scaffold/capability issue; evaluate module scope first. Findings: NATIVE-035. |
| [#259](https://github.com/MohamedRejeb/Calf/issues/259) Demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog | @lemkoleg / 2025-02-18T17:11:00Z | `separate_improvement`; Low | Common alert exposes materialText/materialContent slots but iOS uses native UIAlertController descriptors and text. The requested adaptive busy/progress-dialog example is not available as a uniform arbitrary native Compose content slot. Design/document an explicit busy-dialog example with cancel/accessibility semantics and a deliberate iOS presentation strategy; avoid silently inserting unsupported Material content into UIKit. |
| [#288](https://github.com/MohamedRejeb/Calf/issues/288) Request this library can take camera | @hafizkloudius014 / 2025-05-08T01:19:11Z | `already_implemented`; Low | Android and iOS camera capture code exists in the baseline (PR274 and later PR326). The feature request is source-satisfied, but capture has separately tracked correctness/setup/lifecycle risks; no device pass is claimed. Point documentation to existing camera API/setup and native camera findings; do not recreate a duplicate request to add the already existing Android/iOS module. Findings: NATIVE-019, NATIVE-020, NATIVE-021, NATIVE-022, NATIVE-023, NATIVE-024. |
| [#309](https://github.com/MohamedRejeb/Calf/issues/309) firebase compatibility | @Puskistolero92 / 2025-05-27T16:08:46Z | `covered_by_finding`; Medium | KmpFile is a platform handle, not a portable Firebase filesystem path. readByteArray and source are available, but mobile URI/path metadata and eager-buffer guidance are already audited. Firebase integration itself is a consumer adapter/documentation question, not a confirmed Firebase defect. Add an integration recipe distinguishing Android URI, iOS readable copy and byte/stream upload; keep Firebase out of core dependencies and link IO-014/IO-021. Findings: IO-014, IO-021. |
| [#343](https://github.com/MohamedRejeb/Calf/issues/343) Support native file preview | @MohamedRejeb / 2025-07-20T12:41:26Z | `separate_improvement`; Low | No dedicated native file-preview API/module exists. Desktop share opening a file is not a portable preview abstraction or iOS Quick Look implementation. Record native preview as an opt-in future module: define unsupported/cancel/error behavior, file-access lifetime and platform viewer capabilities before selecting dependencies. |
| [#344](https://github.com/MohamedRejeb/Calf/issues/344) [BUG] WebView throwing error on configuration | @StefanOltmann / 2025-07-22T09:14:46Z | `already_implemented`; Medium | The historical stack shows direct JavaFX settings writes on AWT-EventQueue. Baseline applySettings now wraps writes in Platform.runLater at lines215-221, so this specific cause is source-addressed. That does not prove all current JavaFX lifecycle/thread paths are correct. Keep a settings-on-EDT regression test in the desktop matrix; do not recreate the old wrong-thread-settings bug as confirmed. Track distinct startup/lifecycle risks through NATIVE-018/NATIVE-002. |
| [#346](https://github.com/MohamedRejeb/Calf/issues/346) [BUG] Reentry into ignoringRedrawRequests is not allowed (WebView) | @StefanOltmann / 2025-07-24T10:18:02Z | `covered_by_finding`; Medium | The historical stack traces JFXPanel.initFx nested Swing event-loop reentry during Compose render. Baseline still constructs JFXPanel inside remember at line50, but the crash has not been reproduced with current Compose/Skiko/JavaFX/host versions. Retain as risk/reproduction in NATIVE-018 with #39/#151; test cold/warm engine startup, composition reentry and explicit preinitialization on the correct threads. Findings: NATIVE-018. |
| [#471](https://github.com/MohamedRejeb/Calf/issues/471) Feature request: iOS-native styling customization for AdaptiveNavigationBar and AdaptiveTopBar | @antoniokranjcina / 2026-03-24T09:43:20Z | `separate_improvement`; Low | PR499 implements selected tint, pre-iOS26 unselected tint and title color only. Maintainer comment4184266309 leaves iOS26 unselected tint and title font/typography unchecked. Baseline configuration has no title typography field and explicitly documents the Liquid Glass unselected-color limitation. Preserve only the remaining styling requirements; design optional typography/font-resource mapping and iOS26 appearance support without changing unspecified native defaults. |
| [#530](https://github.com/MohamedRejeb/Calf/issues/530) AdaptiveNavigationBar on iOS - bottom bar is visible when navigating away, and during back navigation gestures | @raudonikis / 2026-06-08T15:40:19Z | `covered_by_finding`; Medium | Native bars are subviews of the shared host UIViewController while navigation transitions can keep multiple Compose destinations alive. The report and maintainer comment4967506597 describe a genuine integration gap; replacing navigation architecture was suggested, not implemented or authorized by this audit. Link UI transition/overlay finding; first reproduce Navigation3 outgoing/incoming-screen and cancelled-back-gesture cases, then evaluate scoped host/visibility fixes before a native-navigation redesign. Findings: UI-021. |
| [#548](https://github.com/MohamedRejeb/Calf/issues/548) [Bug]:  AdaptiveTopBar (iOS): content top padding goes stale after device rotation | @EEseka / 2026-09-14T18:37:32Z | `covered_by_finding`; Medium | Source corroborates the report: native top-bar measurement uses LaunchedEffect(Unit), stops after stable frames, and has no rotation/window-size restart. Initial safe-area and cached heights are remembered, so later orientation changes can leave padding stale. Link UI geometry finding and test portrait↔landscape, split view, safe-area changes and prefersLargeTitles transitions; observe view geometry rather than a one-shot warmup loop. Findings: UI-020. |
| [#551](https://github.com/MohamedRejeb/Calf/pull/551) Fix file picker export and getPath; add onError, bookmarks and web save dialog | @MohamedRejeb / 2026-10-16T06:25:13Z | `covered_by_finding`; High | Open, unmerged upstream work. It proposes fixes to baseline export/data-loss/naming/path/cancel issues plus onError, metadata, bookmarks and a browser save dialog. It changes getPath semantics on mobile and includes author-reported tests; none of those claims or new APIs are baseline verification. Keep preserved branch/ref; after audit triage, independently review commits/tests and cherry-pick narrowly scoped fixes where appropriate. Evaluate getPath deprecation/compatibility and real iOS/browser/device tests; do not bulk-merge or publish automatically. Findings: IO-001, IO-002, IO-005, IO-006, IO-007, IO-008, IO-011, IO-012, IO-013, IO-014. |

## Historical fixes checked against the baseline

The following are cross-cutting evidence summaries, not duplicate new findings.
Exact root cause/impact/fix/tests are in the linked area JSON/reports. “Present”
is a source observation; runtime verification is separately recorded in testing.

### Files, native dialogs and provider lifetime

| History | Baseline observation | Remaining work / why closure is not enough |
|---|---|---|
| #3 → #18, folder selection | `FilePickerFileType.Folder` and native platform branches exist | Web explicitly returns an empty list; Android directory metadata uses single-document helpers (`IO-019`). A cross-platform request was not implemented identically everywhere. |
| #53 → #55, iOS callback thread | iOS picker code has explicit `Dispatchers.Main` handoffs | Check cancellation, callback exceptions and each completion path rather than assuming every path is exactly once (`IO-007`). |
| #54 → #85/#86; #90 → #95; #495 → #496 | App-owned copied URL and original URL coexist; directories are treated specially | Scoped folder access, temporary-file cleanup/name/path semantics and retained metadata still matter (`IO-008`, `IO-013`, `IO-014`). Copies cannot simply be removed as an allocation optimization. |
| #56 → #159, old Photos APIs | Historical unsupported PHPicker setters were removed | Does not validate all supported iOS versions or current representation/native availability. Current SDK/link/device matrix still needed. |
| #74/#81/#89 → extension/MIME support (#94 onward) | Extension and custom MIME types exist; desktop has vendored MIME mapping | Modern image formats/unknown custom mappings can disable filters; iOS Document maps an application wildcard to an application-bundle UTI (`IO-015`, `IO-016`, `IO-025`). |
| #108 → #483 | `Multiple(maxItems)` is present | Invalid limits, platform fallback behavior and eager copies before truncation remain (`IO-018`, `IO-013`). |
| #114/#255 → #480/#493 | Settings and initial-directory support exist, especially desktop/Android folder flow | iOS baseline does not apply a directory URL. The stronger picked-folder API is in unmerged #551; closure did not establish universal capability. |
| #141, file size question | Historical response suggested `byteArray.size` | That loads the entire file; baseline has no common `getSize()` API. #551 proposes metadata. Do not turn the old workaround into recommended large-file behavior. |
| #178 → #477; #473 → #479 | JNI/rfd and warmup replace AWT/JNA; source is no longer the old AWT picker | Raw handle disposal races survive “memory management improvements” (#478; `IO-003`). Old AWT coroutine stack reports #279/#280 are not proof of the same current backend bug. |
| #207/#254 → #286/#319/#491/#492 | Compatible image representation and live-photo handling changes exist | Keep HEIC/current/compatible mode explicit; unsafe reads, lifetime and stale remembered settings still need tests (`IO-001`, `IO-017`). |
| #277 → #482 | Android has a media/document fallback | Missing activity handler and exception reporting are not comprehensively modeled; #551 adds onError handling. Device API level is not proof a handler exists. |
| #534 → #540, PR #535 closed as superseded | `NativeLibCache` uses content-aware names and reuses identical cached binaries; tests cover cache behavior | Share has a different loader, still using a mutable shared filename (`NATIVE-031`). System-path trust and extraction isolation need their own checks (`IO-022`). |
| #537 → #545 | `RawSource` API and six desktop source tests exist; Android/iOS/JVM can open streams | Web buffers the whole file, Coil still eagerly copies; scheduling/size guidance remains (`IO-021`). Source opening remains blocking. |
| Open #551 | Eleven fixes/features exist only on its preserved branch | Export/path/bookmark tests and claimed emulator/simulator runs belong to the PR author, not to baseline verification. Compatibility needs review before cherry-picking. |

### Permissions and geolocation

| History | Baseline observation | Remaining work / finding |
|---|---|---|
| #26 → #40, “Add geolocation support”; issue later closed | Android tracker constructs FusedLocation callbacks; other targets have print-only actuals | Public Android states are never updated; non-Android reports zeros. Closure is not implementation completeness (`PERM-018`–`PERM-022`). |
| #31, permissions support; comment 2500574630 | Desktop is explicitly denied/no-op, just as the 2024 commenter observed | No callback, refresh or OS integration on desktop/JS/Wasm (`PERM-017`); do not say desktop automatically grants permissions. |
| #150 → #152, iOS snapshot crash | Native helper results have had main-thread/state fixes | Current callbacks can still precede status refresh or outlive composition (`PERM-007`). The old crash report is historical, current root causes are separately sourced. |
| #154/#175/#258/#276/#282/#284 → #244/#300 and related gating changes | `Granted` vs `Denied(shouldShowRationale)` remains the shared model | Android and iOS requestability differ; limited/precise/write-only states are lost (`PERM-016`). Request gating can reject valid background upgrades (`PERM-009`). |
| #173/#184 → #174/#195/#263; #386 → #413 | API-ranged storage mapping and empty-request guards exist | Reverse-mapping aliases and missing completion callbacks remain (`PERM-002`/`003`); broad all-files-access documentation is not implemented by WriteStorage (`PERM-024`). |
| #168/#191 → #171 and later notification changes | Notification mapping changes by Android SDK; remote notifications are iOS-specific | An unregistered Android logical permission can be reported granted (`PERM-001`). A default grant is not a functioning push registration API. |
| #176 → #200 | Compose inspection uses inert preview permission state | Useful preview support is present, but preview's granted result is not a platform test. |
| #187 → #183/#424 | iOS settings opening migrated to newer APIs and notification-specific settings | Still test actual device return/revocation behavior; settings launch alone does not refresh correct state. |
| #205 → #339 | OS version/auth handling and a retry exist for Bluetooth | Native delegate retention, powered-off/not-determined and overlapping requests require device validation (`PERM-014`). |
| #229 → #244 and location helpers | Foreground location request/status implementations exist | Nonterminal callbacks can consume pending requests; overlaps overwrite callbacks (`PERM-010`). |
| #248 → #422 | iOS multiple requests no longer throw the original NotImplementedError | They run concurrently and report singleton maps instead of one coherent batch (`PERM-008`). “No longer throws TODO” is not a complete multi-request contract. |
| #253 → #421 | Permission feature artifacts isolate many native references | The umbrella intentionally brings them all back. App Store submission still needs relevant purpose strings; calendar full-access guards/keys remain incorrect (`PERM-011`/`012`). |
| #281 → #298/#421 | Background-location type and platform helpers exist | Android prerequisite orchestration and iOS WhenInUse→Always upgrade are incomplete (`PERM-004`/`009`). |
| #313/#411 → #331 | Lifecycle resume observers were added | Previously granted states are skipped, so revocation stays stale (`PERM-006`). |
| #315 → #316 | Wi-Fi permission mappings and an NSNetService probe exist | Status observation itself publishes a Bonjour service; timeout/cancel/inactive app become denial (`PERM-013`). |
| #382 → #384; #398 → #401/#432 | Contacts-write and SMS permission declarations exist | They are permission APIs, not contact-data or OTP APIs. The open #78 request is only partially fulfilled. |
| #523 APNs registration | Freshly granted remote-notification path calls registration | Already-authorized fast path skips registration (`PERM-015`). |

### UI, navigation and web engines

| History | Baseline observation | Remaining work / caution |
|---|---|---|
| #9/#37/#75/#77/#133/#363/#408, sheets/scrolling/theme | Sheet managers/composition-local propagation and multiple historical fixes exist | Current native sheet sizing, detents, interaction, disposal and selection handling need the UI report's exact tests. Old closed scroll issues do not prove every nested WebView/gesture layout is correct. |
| #115/#122/#123/#131/#163/#172/#397, picker colors/selection/timezone | Initial selection, theme/tint, layout and date conversion were changed across releases | Preserve tests for UTC day vs local display, old device fallback, native tint and padding. Not every Material color is representable by UIKit. |
| #116 → #119, confirmValueChange/reset | Historical state-key issue has a dedicated fix | Saver inputs and callback freshness must still be reviewed when state is restored or a lambda changes. |
| #189/#210 → #230; #330/#341/#381 → #414 | Selector/target patterns were repaired | Consumer framework export, target retention and device/runtime linkage still matter; source-symbol availability alone is not a UIKit action test. |
| #206 → #267, alert styles/actions | Native action styles/descriptors are exposed | The default destructive-dismiss choice is API behavior; consumers can configure it. More composable content is still a separate native capability question (#259). |
| #249 → #270, drag handle | iOS has a path to hide the handle when requested | Does not prove every sheet detent/gesture or presentation API is portable. |
| #264 → #269 | Hour/minute constructor order was fixed | Keep time-state restore/zone/initial selection tests; do not report the old swapped arguments solely from history. |
| #318/#380 → glass/button work (#438–#444) | UIKit/Compose glass controls and adaptive buttons now exist | Distinguish custom drawing from native UIKit, version gates and missing fallbacks; no “all native widgets” claim. |
| #328 → #541 | Real `SelectableDates` / `DateBounds` replaced the nonexistent documented dateValidator | Reconciliation cost, mutable rule invalidation and native fallback limits remain; full source/state analysis is in UI findings. |
| #471 → #499 | Selected tint, pre-iOS26 unselected tint and title color are present | iOS26 unselected tint and title typography remain explicitly incomplete; keep only those requirements in the migrated enhancement. |
| #476, native bar padding | Padding CompositionLocals and measured-height logic exist | Measurement stops after stability and native overlay lifetime is outside Compose layout; #548/#530 map to `UI-020`/`UI-021`. |
| #519 → #524/#525 | Properties refresh without recreating UIAlertController; text-field targets are retained | Callback replacement remains incomplete (`UI-012`), so do not close all recomposition concerns because properties update. |
| #520 → #521 | ImageVector rasterization uses density instead of always low resolution | Remaining vector rendering fidelity is distinct (`UI-036`); don't claim density repair reproduces every path/stroke. |
| #536 → #539 | Optional/blank dismiss text enables one-button dialogs; tests exist | iOS actions are fixed at first presentation, a documented limit; dynamic action-set changes need deliberate tests. |
| #542 | SaveableStateHolder stores each route's content state | The key is a route, not a unique entry; duplicate routes and full controller recreation still lose/alias state (navigation audit). |
| #549/#550 | Combined click/long/double click and parallel Gradle sync are on main after v0.14.0 | The latest tagged release and the audited main commit are not identical; preserve exact baselines when testing or publishing later. |
| #2/#6/#10/#22 → #15/#16 and later WebView APIs | Script, HTML content and engine-specific navigation exist | Common headers/base/history options and JS failures are not consistent across actuals (`NATIVE-015`/`016`); cross-origin browser restrictions are not native engine bugs. |
| #240 → #425/#429 | Cookie APIs exist on every target | Store ownership, matching, expiry and browser semantics have concrete defects (`NATIVE-011`–`014`). Existence of an API is not a compliant shared cookie jar. |
| #203/#426/#428, desktop WebView fixes | Listeners/settings/native view integration changed | Native resource disposal and stopLoading self-enqueue remain (`NATIVE-001`/`002`); do not infer old “state management fixed” means all commands are correct. |
| #344 | Current `applySettings` queues work onto FX thread | Exact old direct-EDT cause is source-addressed; retain a regression, not a duplicate confirmed bug. Startup risk #346 is separate (`NATIVE-018`). |
| PR #412 “Fix Web View document title” | Commit `7e1cac6` changes the documentation heading from File Picker to Web View | **Not a runtime page-title fix.** PR title alone would have produced a false historical conclusion. |
| #139 and version/linkage reports #138/#180/#186/#188/#190/#352/#358/#361 | Reports involve differing Kotlin/Compose/Material/Coil versions and obsolete native ABI shapes | Preserve exact version combinations; current min/max compatibility must be tested against current artifacts. #139's linked discussion is not proof of a bug in the common adaptive navigator. |

## Closed-unmerged proposals: preserve the reason, not the patch by default

The 51 closed-unmerged PRs include dependency-bot updates, toolchain experiments
and superseded feature/fix proposals. Closing is not equivalent to applying their
code. Important non-bot cases:

| PR | Evidence of disposition | Current interpretation |
|---|---|---|
| #179, richer permission callbacks | Maintainer explicitly declined an unnecessary breaking signature change, comment 2352600192 | Keep the Boolean callback for compatibility; current status/result-ordering design needs improvement independently. |
| #246 / #324 / #512 / #513, Kotlin RC/Beta bumps | Unmerged experimental branches preserved; no detailed rejection rationale in accessible bodies | Do not invent a compatibility failure or accepted target version from branch names. |
| #296, version catalog update | Comment 2880784094 says versions were already updated and permission rationale changes were being tested | Supersession/context, not proof that the PR's entire patch landed. |
| #311, camera OriginalImage/temp file fix | Author's comment 2929957537 still says image not received; later #326 implements OriginalImage/PNG/main-thread handling | Preserve earlier work, but do not cherry-pick blindly over the later implementation. |
| #400, image representation parameter | Breaking Image singleton change rejected (3868097447); default Compatible chosen later (4177737733), then #492 settings added | Requested capability source-present through another API; stale proposal need not become a new issue. |
| #535, namespace workaround for shared DLL collision | Maintainer explicitly points to #540 and closes it (5632775548) | Preserve namespace compatibility; use the content-aware loader fix rather than the superseded workaround. |

The archive includes review submissions and review-thread resolution. Four
threads/75 review records are not an exhaustive independent review of every
change. No approval is inferred for a PR with no reviews, and an approved old
patch is still checked against current source.

## Open PR #551: independent review/cherry-pick dossier

- Author: **MohamedRejeb**; created **2026-10-16T06:25:13Z**, last updated
  **2026-10-18T05:40:27Z**; original ID and full body are in the actionable JSON.
- Head: `66e345a9b291d4d82aa76b1f5f0d05e99b1bb8e1`, branch
  `fix/file-picker-export-and-path`; `merged_at` is null.
- Compared with `af388bd`, it changes 64 files (2,748 insertions/305 deletions).
  This is not a small identity patch and has not been merged by this audit.
- There are 11 branch commits absent from the baseline:

| Commit | Authored date (original offset) | Subject |
|---|---|---|
| `675d049` | 2026-10-13T06:24:17+01:00 | Keep requested filename in iOS save sheet |
| `e2ded9f` | 2026-10-15T11:24:54+01:00 | getPath returns filesystem path or null |
| `be274cc` | 2026-10-15T11:25:02+01:00 | Android save writes file; iOS exports copy |
| `211d3ad` | 2026-10-15T11:45:53+01:00 | Report swipe dismissal and keep picked names |
| `b82e19d` | 2026-10-15T11:54:24+01:00 | iOS getPath is readable-copy path |
| `03cbf0c` | 2026-10-15T11:54:28+01:00 | Open dialogs in a picked KmpFile folder |
| `ed7e1e6` | 2026-10-15T12:04:15+01:00 | fromUriString/getSize/getMimeType |
| `ff62e5b` | 2026-10-15T12:07:12+01:00 | Browser save dialog where available |
| `1a20b60` | 2026-10-15T12:17:14+01:00 | onError overloads |
| `c70d35c` | 2026-10-15T15:02:22+01:00 | Persistent file-access bookmarks |
| `66e345a` | 2026-10-18T06:40:10+01:00 | Keep download Blob URL alive for Safari |

Recommended sequence: preserve the branch; inspect standalone correctness fixes
against current `IO-*` findings; port deterministic regression tests; separate
new API/bookmark/metadata features from urgent data-loss fixes; check binary and
source compatibility; then obtain actual mobile/native/browser verification.
`getPath()` changing meaning on Android/iOS requires a deprecation/migration
strategy. Bookmark access must balance permissions/security scopes and not leak
native access indefinitely. New error overloads must define exactly-once outcome
semantics without treating application callback exceptions as picker errors.

The PR author reports host tests, a Pixel emulator pass, iOS simulator tests/UI
interaction and a Chromium Wasm test with a stubbed save API. Those are **author
claims preserved in metadata**, not tests run by nativeCmpkit's audit. The author
explicitly leaves real Chrome chooser, Safari download and desktop manual UI
verification incomplete. No approved review thread is recorded for #551 in the
accessible GraphQL snapshot. Its provisional `merge_commit_sha` is a GitHub
preview, not proof it was merged.

## Release and compatibility history

There are 23 archived upstream release objects, all authored by MohamedRejeb,
with no attached release assets listed in this snapshot. Git tags, release
objects, Maven artifacts and branch heads are distinct records. Preserve their
original dates independently; do not recreate them as newly published
nativeCmpkit releases. In particular v0.14.0 predates #549/#550 on main.

| Original tag | Published UTC | Original release URL |
|---|---|---|
| `v0.1.1` | 2023-08-23T14:48:55Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.1.1) |
| `v0.2.0` | 2023-09-24T16:30:40Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.2.0) |
| `v0.3.0` | 2023-12-02T11:35:07Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.3.0) |
| `v0.3.1` | 2024-01-29T13:49:08Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.3.1) |
| `v0.4.0` | 2024-03-04T06:26:59Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.4.0) |
| `v0.4.1` | 2024-05-29T16:46:51Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.4.1) |
| `v0.5.0` | 2024-06-23T12:18:35Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.5.0) |
| `v0.5.1` | 2024-06-30T08:55:40Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.5.1) |
| `v0.5.2` | 2024-07-24T06:57:03Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.5.2) |
| `v0.5.3` | 2024-08-07T16:51:45Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.5.3) |
| `v0.5.4` | 2024-08-20T18:48:19Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.5.4) |
| `v0.5.5` | 2024-08-28T08:31:24Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.5.5) |
| `v0.6.0` | 2024-11-09T21:43:46Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.6.0) |
| `v0.6.1` | 2024-11-10T10:48:36Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.6.1) |
| `v0.7.0` | 2024-12-29T19:39:59Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.7.0) |
| `v0.7.1` | 2025-03-08T22:15:17Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.7.1) |
| `v0.8.0` | 2025-05-25T22:00:26Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.8.0) |
| `v0.9.0` | 2026-03-16T12:33:20Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.9.0) |
| `v0.10.0` | 2026-03-22T14:41:19Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.10.0) |
| `v0.11.0` | 2026-04-04T05:39:11Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.11.0) |
| `v0.12.0` | 2026-04-16T07:55:07Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.12.0) |
| `v0.13.0` | 2026-07-27T20:06:24Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.13.0) |
| `v0.14.0` | 2026-09-13T10:53:48Z | [upstream release](https://github.com/MohamedRejeb/Calf/releases/tag/v0.14.0) |


Older resolution/ABI incidents are especially relevant to future releases:
#23 missing calf-io 0.2.0, #528 missing calf-file-picker 0.12.0, the material3
TimePickerState class/interface change (#169), native UIKitView ABI changes
(#138/#188/#190), and Material DatePicker NoSuchMethodError (#361). The lesson is
to verify all target artifacts and consuming version combinations, not just
update a badge or rely on a successful single-module publish task. No package
publication was attempted or authorized as part of this historical review.

## Preserving histories that branch mirrors alone do not show

GitHub can expose force-push before/after commit objects and edit history that a
mirror of today's branch tips does not contain. `graphql/history-events.json`
preserves 23 force-push events with actor/time/before/after identity. The history
review flagged force-pushed revisions missing from the initial advertised-ref
import. The migration check was expanded to metadata-referenced commit OIDs from
all archived datasets, including public deployment SHAs. Consult the authoritative
[commit-recovery receipt](../migration/git/referenced-commits-verification.json)
for its final candidate count, existing/fetched/unavailable outcomes, completion
time and bundle verification; do not freeze an intermediate count from the
incremental metadata export into a completeness claim. Additional
`refs/archive/upstream/referenced-commits/*` and the self-contained
`referenced-commits.bundle` preserve recovered commits without changing the
original advertised-ref bundle or rewriting history. Coverage of enumerated
accessible references is not recovery of unknown/deleted history that no
accessible API exposes. A current branch mirror alone would not provide that
coverage.

Release descriptions, timelines, public content-edit diffs and discussions are
metadata, not Git commits. Their timestamps/IDs/authors are not recreated exactly
by creating new GitHub issues. The new issue must say it is migrated/derived,
link the archived original, and carry current diagnosis and priority. GitHub
accepting an API request is not proof that every thread/attachment was recovered;
use the archive agent's integrity report and documented access limitations.

## Deliberately unverified and out-of-scope historical claims

- No iOS/macOS/Windows device history is replayed solely because a PR checklist
  says tested. Historical screenshots/videos do not prove the current baseline.
- #34 and #72 need a current minimal reproduction. #39/#151/#346 are consolidated
  startup/reentry risks, not three independently proven new vulnerabilities.
- #538 concerns the unrelated Calf audio plugin/Ardour/GTK project, not this
  Kotlin library; its closed report must not become a nativeCmpkit runtime bug.
- Closed media feature issues #29/#30 and geo #26 are not evidence working media
  or complete geolocation exists. Maps was historically deferred until media
  (maintainer comment1976875624, 2024-03-04T15:42:32Z); neither became a completed
  module in this baseline.
- External linked projects/issues may explain symptoms but are not automatically
  imported source or verified dependencies. Inaccessible/deleted/private history
  is described as a limitation, not guessed.
- Old no-op/experimental APIs remain compatibility concerns; the audit does not
  silently implement them or approve architectural replacement during migration.

## Deduplication and resulting work

`HIST.json` is intentionally an empty findings array: the concrete current
source defects discovered through history are recorded once in IO/NATIVE/PERM/
UI/NAV/BUILD findings, not inflated into duplicate cross-cutting bug tickets.
Separate surviving feature requests and genuine reproduction tasks are preserved
in the actionable migration decisions. The lead's generated issues/roadmap link
those IDs; this review did not modify upstream or mutate GitHub itself.

Use [ADR 0002](../decisions/0002-upstream-design-history.md) for durable design
rationale, [architecture](../architecture/README.md) for current execution flows,
and the [roadmap](../roadmap/README.md) for sequencing. High-impact correctness,
data integrity, native lifetime and release-verification work precedes new maps,
media, preview or native-navigation architecture.
