# Current upstream disposition and development roadmap

Reviewed **2026-10-24T20:14:42.184864+00:00**, offline. Source: frozen `docs/migration/upstream-updates/20261024T183300Z`; development base `94d2492e99d5cbc060409d94d9f88febd06222d5` plus uncommitted changes.

**All 16 synced open issues are accounted for, plus PR #551 separately.** This is an additive development assessment, not a new import, live GitHub status query or closure receipt. Original snapshots/descriptions remain unchanged. The structured record is [`upstream-status.json`](upstream-status.json).

## Evidence and interpretation

- Rehashed **170/170** frozen snapshot entries; matched all **16** source-to-primary mappings to their recorded posted/read-back comments. The prior apply receipt records **zero new issues**.
- Compared all **164/164 unique resolution IDs** to the baseline findings. At this review: **91 implemented**, **65 partially-verified**, **8 unresolved**. No `verified` resolution is recorded in this inventory.
- Issue disposition: **6 still applicable, 8 partially addressed, 2 source-superseded only**. PR #551 is separately partially addressed. **Zero runtime-verified upstream resolutions, zero automatic closure recommendations, zero duplicate issue proposals.**
- “Source-superseded” only means camera capture already exists (#288), or the historical direct EDT settings-write path is gone (#344). It does **not** mean their related correctness/runtime findings are resolved.
- Current source/document hashes and exact owner resolution links are in JSON. Passing tests belong only to the recorded command/input hashes; later source repairs, KLIB compilation, headless skips and test source are not new passing runtime evidence.
- No Gradle, device/browser test, network request, source/build edit or GitHub mutation was performed for this document. Containment and publication gates remain unchanged.

Receipts: [applied comments](upstream-sync-20261024T183300Z/apply-receipt.json); [sync completion](upstream-sync-20261024T183300Z/completion.json); [existing issue map](../migration/issue-map.json); [owner resolution records](resolutions).

## Complete issue map

| Calf issue | Existing nativeCmpkit issue | Current disposition | Priority / next-step effort | Phase |
|---|---|---|---|---|
| [#27](https://github.com/MohamedRejeb/Calf/issues/27) Add Maps Support | [#151](https://github.com/Apdelrahman1911/nativeCmpkit/issues/151) | Applicable / still open | Low / L | F1 |
| [#34](https://github.com/MohamedRejeb/Calf/issues/34) Camera issue in webview iOS | [#168](https://github.com/Apdelrahman1911/nativeCmpkit/issues/168) | Applicable / still open | Medium / M | V2 |
| [#39](https://github.com/MohamedRejeb/Calf/issues/39) Webview not loading html content | [#75](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75) | Partially addressed | Medium / M | V2 |
| [#72](https://github.com/MohamedRejeb/Calf/issues/72) Zoom in/out in browser | [#170](https://github.com/Apdelrahman1911/nativeCmpkit/issues/170) | Applicable / still open | Low / M | V2 |
| [#78](https://github.com/MohamedRejeb/Calf/issues/78) Contacts and OTP feature | [#166](https://github.com/Apdelrahman1911/nativeCmpkit/issues/166) | Partially addressed | Low / M | F1 |
| [#151](https://github.com/MohamedRejeb/Calf/issues/151) Webview not work on Linux | [#75](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75) | Partially addressed | Medium / M | V2 |
| [#245](https://github.com/MohamedRejeb/Calf/issues/245) Custom data source media content | [#151](https://github.com/Apdelrahman1911/nativeCmpkit/issues/151) | Applicable / still open | Low / L | F1 |
| [#259](https://github.com/MohamedRejeb/Calf/issues/259) Demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog | [#165](https://github.com/Apdelrahman1911/nativeCmpkit/issues/165) | Applicable / still open | Low / M | D1 |
| [#288](https://github.com/MohamedRejeb/Calf/issues/288) Request this library can take camera | [#77](https://github.com/Apdelrahman1911/nativeCmpkit/issues/77) | Source-superseded only | Medium / M | V1 |
| [#309](https://github.com/MohamedRejeb/Calf/issues/309) firebase compatibility | [#51](https://github.com/Apdelrahman1911/nativeCmpkit/issues/51) | Partially addressed | Medium / M | D1 |
| [#343](https://github.com/MohamedRejeb/Calf/issues/343) Support native file preview | [#169](https://github.com/Apdelrahman1911/nativeCmpkit/issues/169) | Applicable / still open | Low / L | F1 |
| [#344](https://github.com/MohamedRejeb/Calf/issues/344) [BUG] WebView throwing error on configuration | [#75](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75) | Source-superseded only | Medium / S | V2 |
| [#346](https://github.com/MohamedRejeb/Calf/issues/346) [BUG] Reentry into ignoringRedrawRequests is not allowed (WebView) | [#75](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75) | Partially addressed | Medium / M | V2 |
| [#471](https://github.com/MohamedRejeb/Calf/issues/471) Feature request: iOS-native styling customization for AdaptiveNavigationBar and AdaptiveTopBar | [#167](https://github.com/Apdelrahman1911/nativeCmpkit/issues/167) | Partially addressed | Low / M | D1 |
| [#530](https://github.com/MohamedRejeb/Calf/issues/530) AdaptiveNavigationBar on iOS - bottom bar is visible when navigating away, and during back navigation gestures | [#33](https://github.com/Apdelrahman1911/nativeCmpkit/issues/33) | Partially addressed | High / L | V1 |
| [#548](https://github.com/MohamedRejeb/Calf/issues/548) [Bug]:  AdaptiveTopBar (iOS): content top padding goes stale after device rotation | [#32](https://github.com/Apdelrahman1911/nativeCmpkit/issues/32) | Partially addressed | High / M | V1 |
| [PR #551](https://github.com/MohamedRejeb/Calf/pull/551) — **not one of the 16 issues** | [#4](https://github.com/Apdelrahman1911/nativeCmpkit/issues/4), [#5](https://github.com/Apdelrahman1911/nativeCmpkit/issues/5), [#8](https://github.com/Apdelrahman1911/nativeCmpkit/issues/8), [#43](https://github.com/Apdelrahman1911/nativeCmpkit/issues/43), [#44](https://github.com/Apdelrahman1911/nativeCmpkit/issues/44), [#45](https://github.com/Apdelrahman1911/nativeCmpkit/issues/45), [#48](https://github.com/Apdelrahman1911/nativeCmpkit/issues/48), [#49](https://github.com/Apdelrahman1911/nativeCmpkit/issues/49), [#50](https://github.com/Apdelrahman1911/nativeCmpkit/issues/50), [#51](https://github.com/Apdelrahman1911/nativeCmpkit/issues/51) | Selected adaptation; partial | High / L | V1 |

Priorities retain the existing primary issue classification; related camera findings include High-priority NATIVE-019. Effort estimates the **next work package**, not delivery of an entire new cross-platform module. A topic with no direct finding IDs remains its own imported request, not an inferred audit closure.

## Dependency-ordered work packages

### V1. Verify existing destructive IO, camera ownership and native bar behavior

**Topics:** PR #551, #548, #530, #288.

- IO-008 before export/copy-lifetime acceptance for IO-005/013/014; IO-001/020 before streaming consumer claims.
- UI-020 measurement acceptance before UI-021 transition acceptance.
- NATIVE-019/020/024 restoration/ownership repairs before declaring camera capture reliable.

Existing feature correctness. Complete focused held-input retries first, then real Android/Apple behavior and immutable consumer evidence; source implementation statuses do not close this gate.

### V2. Consolidate and reproduce WebView/zoom integration reports

**Topics:** #39, #151, #344, #346, #34, #72.

- BUILD-001/002 documented JavaFX runtime and packaged consumer before interpreting clean-host failures.
- Run live-FX harness after compilation/init corrections; cold Compose bootstrap remains a separate test.
- Determine host/platform and isolate pure Compose/browser behavior before assigning a new library root cause.

Preserve #75 as the shared desktop reproduction ticket; WK camera and zoom retain their distinct existing topic issues. No skipped/headless/common-test substitution for a platform reproduction.

### D1. Finish safe usage and optional native UI contracts

**Topics:** #309, #471, #259.

- IO grant/stream ownership before an upload recipe.
- Native bar ownership/measurement before styling extensions.
- Alert dismissal/callback/accessibility ownership before a busy-dialog example.

Documentation/examples and optional API design; validate the exact consumer scenario. Do not introduce Firebase into core or silently replace UIKit with unsupported Material-only content.

### F1. Keep genuinely new capabilities as explicit future-scope decisions

**Topics:** #27, #245, #78, #343.

- Inventory/availability honesty precedes any new module claim.
- Platform provider/privacy/access-lifetime scope precedes dependencies and implementation.

Maps, media, contacts/OTP data and native preview are not current fixes and are not silently mandatory feature additions to the first preview. Keep their existing requests open unless the owner explicitly dispositions scope.

**Cross-cutting release dependencies:** BUILD-006/007 (verification/supply chain), NAV-009/018 (artifact licensing/attribution), UI-040 (native coverage) and IO-023 (native parent-window lifetime) remain distinct gates. This upstream list is not a substitute for the entire 164-finding roadmap, nor authorization to add every future feature before a preview.

## Per-issue current assessment

### #27 — Add Maps Support

**Applicable / still open:** Unimplemented feature request; availability documentation is not Maps support.

The included calf-maps project still contains only build configuration and no source/API. NATIVE-035 documents this honestly; implementing that audit finding does not implement upstream Maps requirements for Android, iOS, Desktop or Web.

- **Mapping:** [#151](https://github.com/Apdelrahman1911/nativeCmpkit/issues/151); NATIVE-035 (`implemented`)
- **Source:** `calf-maps/build.gradle.kts:1-13` (build-only unpublished module); `settings.gradle.kts:29-61` (included modules).
- **Evidence:** The native owner recorded six passing static availability assertions, including maps included/zero source/no publication. This review also inspected settings and the build-only module.
- **Limits:** No Maps implementation, provider integration, platform runtime or published artifact capability was verified. NATIVE-035 remains a separate documentation/inventory finding; it is not a feature-completion proxy.
- **Related prerequisites:** None beyond the stated scope/runtime requirements.
- **Next required check:** Define optional Maps API/platform/provider scope and ownership/privacy constraints before enabling a provider. Verify the packaged artifact graph continues to exclude an incomplete Maps API; add per-platform rendering/lifecycle tests only when a real implementation is authorized.
- **Compatibility/scope:** Retain the scaffold/history without advertising or shipping a Maps implementation. L estimates scoping/prototyping, not delivery of four native providers.
- **Records:** [feature-availability.json](evidence/native/feature-availability.json), [NATIVE.md](NATIVE.md); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/151#issuecomment-6388057995).

### #34 — Camera issue in webview iOS

**Applicable / still open:** Historical WKWebView camera report still requires a current reproduction.

The report is camera presentation inside WKWebView, not the standalone camera-picker. Current WKWebView creation/configuration, observer ownership and release paths were revised, but no minimal capture/cancel reproduction establishes which callback or host transition caused the reported webview dismissal.

- **Mapping:** [#168](https://github.com/Apdelrahman1911/nativeCmpkit/issues/168); No direct audit finding; preserve the separate imported topic.
- **Source:** `calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:79-139` (WKWebView factory, observer/delegate ownership and release).
- **Evidence:** Source inspection finds WKWebView configuration/delegates set before onCreated and scoped release. The first native receipt contains no WebView iOS compilation or runtime test.
- **Limits:** No current iPhone/iPad camera capture/cancel run, exact causal line or confirmed fix for upstream #34. Standalone camera source, camera KLIB compilation and camera request tests cannot satisfy this WKWebView report.
- **Related prerequisites:** NATIVE-003, NATIVE-017, NATIVE-037
- **Next required check:** Run a minimal allowed-origin camera/upload page on physical iPhone and iPad; record capture, cancel, denied permission, host navigation and presentation/delegate events. Keep the host mounted through camera dismissal and identify whether WKWebView or an enclosing controller is removed; add that exact regression before changing capture delegates.
- **Compatibility/scope:** No new compatibility promise or issue closure.
- **Records:** [NATIVE.md](NATIVE.md), [first-desktop-android.json](evidence/native/first-desktop-android.json), [camera-share-ios-klib.json](evidence/native/camera-share-ios-klib.json); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/168#issuecomment-6388059327).

### #39 — Webview not loading html content

**Partially addressed:** Desktop startup risk reduced in source; old web-loading symptom not re-established.

JFXPanel creation now occurs on a later AWT turn rather than inside remember/composition, with explicit graphical/runtime availability checks. JavaFX dependencies now use the consumer-runtime boundary and configured 21.0.13 version. The old 2023 web-loading claim predates the current iframe implementation and remains an independent reproduction, not a proven current duplicate.

- **Mapping:** [#75](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75); NATIVE-018 (`implemented`), NATIVE-005 (`implemented`)
- **Source:** `calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:20-89` (availability check and deferred JFXPanel creation); `calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:137-177` (state-driven iframe loading); `gradle/libs.versions.toml:16` (JavaFX version).
- **Evidence:** Desktop/Android WebView production compiled in the first native batch. Twenty-five common/JDK-cookie cases passed, but the JavaFX test class produced one initialization failure before all five real-FX scenarios. None of those common passes proves QuantumRenderer startup or browser loading.
- **Limits:** No clean Ubuntu graphics/packaged-consumer or macOS cold Compose startup pass. No current allowed-origin browser reproduction of the historical endless-loading half; browser runtime checks remain separate.
- **Related prerequisites:** BUILD-001, BUILD-002, NATIVE-004, NATIVE-006
- **Next required check:** Share the desktop reproduction matrix with #151/#346: clean packaged consumer, matching JavaFX modules/classifier, X11/Wayland/display and renderer dependencies. Separately load allowed-origin URL and inline HTML in current JS/Wasm browsers; distinguish iframe framing/CSP/network restrictions from library loading-state defects.
- **Compatibility/scope:** JavaFX runtime modules/classifiers are now an explicit consumer responsibility; neither the old JavaFX19 diagnosis nor a POM-free source build proves a packaged consumer works.
- **Records:** [NATIVE.md](NATIVE.md), [first-desktop-android.json](evidence/native/first-desktop-android.json); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75#issuecomment-6388060750).

### #72 — Zoom in/out in browser

**Applicable / still open:** Platform/zoom reproduction remains ambiguous; no library root cause confirmed.

The archived report names browser zoom and wrong hit targets, while the maintainer asked whether it meant Desktop. Current web samples use ComposeViewport; no source evidence shows that the historical rendering-stack defect survives or belongs to nativeCmpkit.

- **Mapping:** [#170](https://github.com/Apdelrahman1911/nativeCmpkit/issues/170); No direct audit finding; preserve the separate imported topic.
- **Source:** `sample/web-js/src/jsMain/kotlin/Main.kt:1-20` (ComposeViewport entrypoint); `sample/web-wasm/src/wasmJsMain/kotlin/Main.kt:1-17` (ComposeViewport entrypoint).
- **Evidence:** Current JS/Wasm sample entrypoints and the complete archived question/comment were inspected. No zoom-specific runtime receipt is present in this review.
- **Limits:** Do not infer browser zoom correctness from test compilation, shared state tests or ordinary pointer input. No Chromium/Firefox/Safari devicePixelRatio/keyboard or desktop-WebView zoom reproduction.
- **Related prerequisites:** BUILD-006
- **Next required check:** Reproduce current browser zoom at multiple devicePixelRatio values with pointer, focus and keyboard targeting in both JS and Wasm. Compare a plain ComposeViewport control against the nativeCmpkit view; if the original host was desktop, reproduce its WebView zoom separately and route a library-independent bug to the rendering stack.
- **Compatibility/scope:** No new compatibility promise or issue closure.
- **Records:** [upstream-0072-comment.md](upstream-sync-20261024T183300Z/drafts/upstream-0072-comment.md); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/170#issuecomment-6388062096).

### #78 — Contacts and OTP feature

**Partially addressed:** Permission prerequisites exist; contacts retrieval and OTP APIs do not.

ReadContacts/WriteContacts and SMS permission properties already exist, and current permission-session hardening is tracked independently. The upstream maintainer promised contacts permission via PR181, not contacts data access or OTP reading/autofill. There is still no complete contacts/OTP API satisfying this request.

- **Mapping:** [#166](https://github.com/Apdelrahman1911/nativeCmpkit/issues/166); No direct audit finding; preserve the separate imported topic.
- **Source:** `calf-permissions/contacts/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/ContactPermissions.kt:3-23` (contact permission properties); `calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/SmsPermissions.kt:3-34` (SMS permission properties).
- **Evidence:** The permission declarations and archived maintainer comment were source-checked. Current permission resolution records are partially verified; their tests do not retrieve contacts or validate OTP flows.
- **Limits:** Authorization is not data retrieval; granting SMS permission is not a supported OTP product. No contact-store, Android retriever/autofill or iOS one-time-code integration was executed.
- **Related prerequisites:** PERM-007, PERM-016, PERM-017
- **Next required check:** Decide separately whether contacts data APIs and OTP UX belong in library scope; retain this one imported topic rather than opening duplicate permission requests. For an approved OTP API prefer least-privilege OS autofill/retriever mechanisms and explicit unsupported outcomes; test denial, limited contact access and no broad SMS collection.
- **Compatibility/scope:** No blanket SMS-reading dependency or new contacts API is implied by the existing permission surface. M covers requirement/privacy design, not all-platform delivery.
- **Records:** [PERM-permissions.json](resolutions/PERM-permissions.json), [upstream-0078-comment.md](upstream-sync-20261024T183300Z/drafts/upstream-0078-comment.md); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/166#issuecomment-6388063390).

### #151 — Webview not work on Linux

**Partially addressed:** Startup/runtime source changes exist; original Ubuntu renderer failure is unverified.

The Ubuntu24.04 QuantumRenderer/no-suitable-pipeline report remains consolidated under NATIVE-018, alongside #39 and #346. Deferred JFXPanel construction and the new JavaFX consumer-runtime boundary address source risk, not proof that the correct Linux graphics/native dependencies are installed.

- **Mapping:** [#75](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75); NATIVE-018 (`implemented`)
- **Source:** `calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:20-89` (availability and cold toolkit initialization); `gradle/libs.versions.toml:16` (configured JavaFX21.0.13).
- **Evidence:** Production Desktop WebView compiled; the first real-FX suite failed JUnit initialization before its five scenarios. The twenty-five common/JDK-cookie passes are not a Linux renderer pass.
- **Limits:** No independently reproduced current QuantumRenderer failure or verified fix on the original Ubuntu24.04 environment. A class-presence/headless check cannot certify graphics driver, display server or platform-native JavaFX dependencies.
- **Related prerequisites:** BUILD-001, BUILD-002
- **Next required check:** Run a clean packaged Ubuntu24.04 consumer with the documented JavaFX21.0.13 modules/classifier and inspect native loader/render-pipeline failures. Cover X11/Wayland, software/hardware rendering and cold/warm remount; share the evidence on existing native issue #75 rather than adding another duplicate.
- **Compatibility/scope:** No new compatibility promise or issue closure.
- **Records:** [NATIVE.md](NATIVE.md), [first-desktop-android.json](evidence/native/first-desktop-android.json); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75#issuecomment-6388064676).

### #245 — Custom data source media content

**Applicable / still open:** Future media resource-injection requirement; no working media module exists.

calf-media remains an excluded build-only experiment. Android DataSource and iOS AVAssetResourceLoader/AVURLAsset injection are valid future requirements, not defects in an existing player. NATIVE-035 records the boundary without enabling the module.

- **Mapping:** [#151](https://github.com/Apdelrahman1911/nativeCmpkit/issues/151); NATIVE-035 (`implemented`)
- **Source:** `calf-media/build.gradle.kts:1-47` (excluded media scaffold); `settings.gradle.kts:29-61` (inclusion list omits calf-media).
- **Evidence:** Static availability evidence records media excluded; settings/module inventory was inspected. No media implementation or player test ran.
- **Limits:** No Android/iOS media pipeline exists to receive a custom source. Maps/media availability documentation must not be used to close their feature requests as delivered.
- **Related prerequisites:** None beyond the stated scope/runtime requirements.
- **Next required check:** Define whether a media module is in scope before choosing player dependencies. If approved, specify stream ownership, seeks/ranges, cancellation, credentials and resource-loader thread affinity before implementing platform adapters.
- **Compatibility/scope:** No excluded experiment is enabled or published. L covers module/provider design, not a complete media implementation.
- **Records:** [feature-availability.json](evidence/native/feature-availability.json), [NATIVE.md](NATIVE.md); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/151#issuecomment-6388066046).

### #259 — Demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog

**Applicable / still open:** Requested busy/progress alert example is still absent.

AdaptiveAlertDialog still distinguishes native iOS text/actions from Material-only composable content. Native alert ownership/callback fixes and Cupertino progress drawing fixes do not introduce an arbitrary UIKit Compose-content slot or a cross-platform busy-dialog example.

- **Mapping:** [#165](https://github.com/Apdelrahman1911/nativeCmpkit/issues/165); No direct audit finding; preserve the separate imported topic.
- **Source:** `calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.kt:65-122` (native dialog descriptors versus materialText/materialContent).
- **Evidence:** The common alert signatures and UI-native owner record were inspected. Existing progress painter tests exercise rendering arithmetic, not progress inside a native alert.
- **Limits:** No authored/executed native busy-dialog integration example. Passing UI control tests or compiling UIAlertController code is not this feature.
- **Related prerequisites:** UI-012, UI-013, UI-014, UI-040
- **Next required check:** Design a documented busy-dialog example with cancellation, task ownership, progress announcements and an explicit iOS native/custom presentation choice. Verify task completion/error/disposal and VoiceOver/TalkBack behavior; do not silently send Material-only content to UIAlertController.
- **Compatibility/scope:** No new compatibility promise or issue closure.
- **Records:** [UI-native.md](UI-native.md), [UI-controls.json](resolutions/UI-controls.json); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/165#issuecomment-6388067536).

### #288 — Request this library can take camera

**Source-superseded only:** Only the request to add Android/iOS camera capture is obsolete: that capability already exists in source. Runtime correctness is NOT resolved.

Android/iOS camera capture was already present at the migration baseline; do not create a second add-camera feature issue. Current detailed results/options add unavailable/busy/cancel/failure contracts while retaining the legacy success-only callback. Actual safety, restoration and setup findings remain tracked in the existing six camera tickets.

- **Mapping:** [#77](https://github.com/Apdelrahman1911/nativeCmpkit/issues/77); NATIVE-021 (`implemented`), NATIVE-019 (`implemented`), NATIVE-020 (`implemented`), NATIVE-022 (`implemented`), NATIVE-023 (`implemented`), NATIVE-024 (`implemented`)
- **Source:** `calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt:7-19` (legacy capture API); `calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerResult.kt:1-63` (detailed camera outcomes/options and pending-state contract).
- **Evidence:** The first native batch compiled Android/Desktop production; camera common tests ran three cases (two passed, one failed); Android host tests did not execute because test compilation failed. The earlier camera iOS KLIB production/common-test compilation ran, with zero native runtime tests.
- **Limits:** No physical capture, denied permission, real process death, FileProvider receiver/grant, memory profile or iOS modal correctness proof. Independent review additionally identified disposal, callback/reentry and context-owner hazards; coordinated source repairs are separate from executed verification and must be read at their own recorded hashes.
- **Related prerequisites:** NATIVE-033
- **Next required check:** Finish and rerun the focused restoration/disposal/reentry repairs under NATIVE-019/020/024; inspect new XML rather than replacing retained failing evidence. Run an actual minimal Android/iOS consumer through capture/cancel/denial/no-camera/provider setup, non-configuration Activity destruction/process restoration and large-image ownership before asserting camera readiness.
- **Compatibility/scope:** Existing Android/iOS feature presence is source-satisfied, not a verified resolution/closure recommendation. The old callback still cannot express failure/cancel; use the additive detailed API.
- **Records:** [NATIVE.md](NATIVE.md), [first-desktop-android.json](evidence/native/first-desktop-android.json), [native-share-camera-independent.md](evidence/review/native-share-camera-independent.md), [camera-share-ios-klib.json](evidence/native/camera-share-ios-klib.json); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/77#issuecomment-6388068901).

### #309 — firebase compatibility

**Partially addressed:** Safer path/stream prerequisites are implemented; Firebase consumer integration remains open.

KmpFile represents a platform handle, not a portable Firebase filesystem path. Current APIs distinguish readable filesystem paths from URI serialization, retain content-provider/security-scope access and offer bounded byte reads/owned streams. These help write an adapter; they neither add Firebase to core nor prove compatibility with a particular Firebase KMP SDK.

- **Mapping:** [#51](https://github.com/Apdelrahman1911/nativeCmpkit/issues/51); IO-014 (`partially-verified`), IO-021 (`partially-verified`)
- **Source:** `calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt:22-105` (path/URI/metadata API contract); `calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.kt:8-40` (caller-owned RawSource and scheduling); `calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt:37-97` (provider reads and metadata).
- **Evidence:** Android KmpFileAndroidTest passed eight path/URI/metadata cases within the 21-case IO host suite. Three desktop Coil/stream bridge cases passed. Those are local IO/ownership checks, not Firebase upload tests. iOS IO/picker test KLIB compilation ran with zero native executions.
- **Limits:** No Firebase-specific recipe/consumer execution exists in the IO implementation scope. A restored URI string is not a restored grant, and a browser filename is not a local path. Coil success is not Firebase evidence.
- **Related prerequisites:** IO-008, IO-001, IO-020
- **Next required check:** Add a dependency-external recipe using Android content URI/native upload, iOS scoped readable copy or bounded bytes/stream as supported by the chosen SDK; specify access lifetime through completion. Verify empty/large/Unicode content, cancellation, failed upload and grant revocation in an isolated SDK consumer (or emulator), with resource closure and no secrets in fixtures.
- **Compatibility/scope:** getPath changed meaning intentionally while keeping its descriptor: content/browser paths are null; switch URI serialization to toUriString. SDK integration stays out of core dependencies.
- **Records:** [IO.md](IO.md), [second-io-perm-and-fourth-ui.summary.json](evidence/gradle/second-io-perm-and-fourth-ui.summary.json), [first-ios-klib.verification.json](evidence/gradle/first-ios-klib.verification.json), [io-android-independent.md](evidence/review/io-android-independent.md); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/51#issuecomment-6388070371).

### #343 — Support native file preview

**Applicable / still open:** A distinct native file-preview capability remains unimplemented.

No dedicated preview module/API appears in the included module graph. Share content/chooser or an OS open action is not a portable preview lifecycle, and the current safer desktop share fallback intentionally avoids arbitrary Desktop.open/browse behavior.

- **Mapping:** [#169](https://github.com/Apdelrahman1911/nativeCmpkit/issues/169); No direct audit finding; preserve the separate imported topic.
- **Source:** `settings.gradle.kts:29-61` (included modules contain no preview module); `calf-share/src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareContent.kt:1-59` (share content is not a preview contract).
- **Evidence:** Included modules and ShareContent were inspected. No Quick Look/native viewer implementation or preview runtime receipt was found.
- **Limits:** No iOS Quick Look, Android preview intent/recipient capability, Desktop or browser preview guarantee. Do not reintroduce unsafe arbitrary file opening merely to label this request implemented.
- **Related prerequisites:** IO-008, NATIVE-027
- **Next required check:** Design an opt-in preview contract with availability/cancel/error outcomes, owner/window lifetime and source access grants. Choose per-target viewer strategy only after threat/privacy review; test missing viewers, hostile file types, temporary/scoped sources and cleanup.
- **Compatibility/scope:** An opt-in future module must not broaden the existing share fallback into automatic file execution. L is design/prototype effort, not complete platform delivery.
- **Records:** [NATIVE.md](NATIVE.md), [IO.md](IO.md); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/169#issuecomment-6388071754).

### #344 — [BUG] WebView throwing error on configuration

**Source-superseded only:** The reported direct EDT-to-WebEngine settings write is source-obsolete; no current real-FX regression pass establishes closure.

Baseline applySettings already used Platform.runLater, so the exact historical direct-write cause was source-addressed before this development phase. Current DesktopWebViewOwner coalesces settingsChanged onto FX, and creation applies settings only from createNow after checking the FX thread.

- **Mapping:** [#75](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75); NATIVE-018 (`implemented`)
- **Source:** `calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:112-126` (FX-thread checked initialization); `calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:206-217` (coalesced Platform.runLater settings writes).
- **Evidence:** Four common WebSettings tests passed in the first native batch, but the actual JavaFX test class failed initialization and executed none of its five scenarios. Shared settings values do not prove thread-affine WebEngine writes.
- **Limits:** No settings-from-EDT plus disposal/remount/queued-update test has been verified on a live FX engine in this reviewed receipt. Do not relabel NATIVE-018 or the whole WebView as resolved because the old cause is absent from source.
- **Related prerequisites:** NATIVE-002, NATIVE-037, NATIVE-039
- **Next required check:** Run a real-FX regression that changes settings from the EDT/common observable state after mount, verifies the engine value, and races queued updates with disposal. Keep this history in native issue #75 and related lifecycle coverage; do not recreate the historical direct-write bug as a newly confirmed defect without reproduction.
- **Compatibility/scope:** Source-obsolete refers to the old call path, not to the reporter being wrong or all current lifecycle/thread paths passing.
- **Records:** [NATIVE.md](NATIVE.md), [first-desktop-android.json](evidence/native/first-desktop-android.json); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75#issuecomment-6388073100).

### #346 — [BUG] Reentry into ignoringRedrawRequests is not allowed (WebView)

**Partially addressed:** Cold nested-loop trigger removed from composition in source; original macOS transition crash remains unverified.

JFXPanel is now created from a LaunchedEffect via the next AWT event instead of remember. This directly targets the historical initFx nested-event-loop trigger, but real-FX helper tests that initialize the toolkit before their scenarios cannot by themselves reproduce first Compose/Skiko/Metal startup.

- **Mapping:** [#75](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75); NATIVE-018 (`implemented`)
- **Source:** `calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:45-89` (deferred toolkit bootstrap and FX dispatch).
- **Evidence:** Desktop WebView production compiled; first JavaFX class initialization failed before any scenario. No cold-first-composition or macOS rendering pass is in the evidence.
- **Limits:** No original ignoringRedrawRequests crash reproduction or demonstrated absence under stress. Deferral is a source risk reduction, not a proof that Swing/FX/Compose reentry is impossible.
- **Related prerequisites:** BUILD-001, NATIVE-002
- **Next required check:** Run fresh-process first WebView composition with FX initially uninitialized on macOS AWT/Metal and Linux graphical hosts. Exercise rapid recomposition/remount, window close/recreate and shared-toolkit lifetime; retain thread/event-loop traces on failure and do not substitute only warmed-up engine tests.
- **Compatibility/scope:** No new compatibility promise or issue closure.
- **Records:** [NATIVE.md](NATIVE.md), [first-desktop-android.json](evidence/native/first-desktop-android.json); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/75#issuecomment-6388074586).

### #471 — Feature request: iOS-native styling customization for AdaptiveNavigationBar and AdaptiveTopBar

**Partially addressed:** Existing colors satisfy only the checked upstream subset; title typography and iOS26 unselected tint remain unsupported.

The archived PR499 follow-up already checked selected tint, pre-iOS26 unselected tint and title color. Current configuration exposes those fields with Color.Unspecified defaults, but no title typography/font-resource field; the tab configuration still explicitly documents iOS26 Liquid Glass ignoring unselectedItemTintColor.

- **Mapping:** [#167](https://github.com/Apdelrahman1911/nativeCmpkit/issues/167); No direct audit finding; preserve the separate imported topic.
- **Source:** `calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitNavigationBarConfiguration.kt:6-22` (titleColor only; no typography field); `calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitTabBarConfiguration.kt:6-24` (colors and explicit Liquid Glass limitation).
- **Evidence:** Current configuration declarations and archived maintainer checklist were inspected. UI-native owner confirms these remaining style features were not introduced by bar ownership fixes.
- **Limits:** No title font/resource mapping or supported iOS26 unselected appearance implementation. No old/current iOS native styling/typography runtime or default-reset comparison was executed.
- **Related prerequisites:** UI-020, UI-021, UI-035
- **Next required check:** Preserve the existing checked subset and specify only the two remaining requirements on native issue #167. Design optional font/typography mapping and a supported iOS26 appearance path; test default preservation, specified-to-unspecified reset, Dynamic Type, accessibility and pre26/26+ behavior.
- **Compatibility/scope:** Keep unspecified native defaults. New optional typography must not force resource/dependency changes on callers who did not opt in.
- **Records:** [UI-native.md](UI-native.md), [upstream-0471-comment.md](upstream-sync-20261024T183300Z/drafts/upstream-0471-comment.md); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/167#issuecomment-6388075997).

### #530 — AdaptiveNavigationBar on iOS - bottom bar is visible when navigating away, and during back navigation gestures

**Partially addressed:** Layout-scoped native bars replace root overlays in source; transition behavior remains a native acceptance gate.

NativeBar now embeds each bar in a UIKitView belonging to its Compose layout; AdaptiveScaffold consumes those actual nodes instead of host-controller overlays plus a second padding channel. This targets the report without replacing the navigation stack, but outgoing/incoming interop behavior still needs the original Navigation3 transition reproduction.

- **Mapping:** [#33](https://github.com/Apdelrahman1911/nativeCmpkit/issues/33); UI-021 (`implemented`)
- **Source:** `calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/NativeBarHost.kt:21-75` (owned native child and UIKitView composable); `calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveScaffold.ios.kt:29-35` (one Scaffold layout/padding channel); `calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.ios.kt:24-41` (layout-scoped tab bar).
- **Evidence:** The third UI iOS diagnostic executed production KLIB compilation; test KLIB compilation failed on native-test bindings. NativeBarOwnershipTest is prepared helper-hosting/measurement coverage, not an executed navigation/gesture integration. Zero native runtime tests ran.
- **Limits:** No push/pop, cancelled interactive back, two coexisting bars, alpha/clipping or VoiceOver transition verification. A layout-scoped UIKitView is not automatic proof that every Compose graphics transform or native transition clips/hides correctly.
- **Related prerequisites:** UI-020, UI-040
- **Next required check:** First verify the scoped hosting/measurement tests on Apple after test KLIB corrections. Run the archived Navigation3 outgoing/incoming-screen scenario, completed and cancelled back gestures, nested scaffolds and simultaneous top/bottom bars; inspect animation, touch/focus and accessibility ownership.
- **Compatibility/scope:** No native-navigation rewrite. Bars now follow their composable/scaffold slot; consumers depending on undocumented root overlays need explicit placement. This visible placement change needs a consumer regression.
- **Records:** [UI-native.md](UI-native.md), [third-ui-ios-klib.verification.json](evidence/gradle/third-ui-ios-klib.verification.json), [NativeBarOwnershipTest.kt](../../calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/navigation/NativeBarOwnershipTest.kt); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/33#issuecomment-6388077773).

### #548 — [Bug]:  AdaptiveTopBar (iOS): content top padding goes stale after device rotation

**Partially addressed:** Finite warmup measurement removed in source; rotation/safe-area behavior is not runtime verified.

NativeBarHost retains layoutSubviews, safeAreaInsetsDidChange and traitCollectionDidChange measurement triggers. Measurements are per owner and feed the actual bar layout; the original one-shot six-stable-frame cache is gone. Native padding correctness after rotation still depends on UIKit interop and real safe-area geometry.

- **Mapping:** [#32](https://github.com/Apdelrahman1911/nativeCmpkit/issues/32); UI-020 (`implemented`)
- **Source:** `calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/NativeBarHost.kt:21-75` (persistent layout/safe-area/trait callbacks); `calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.ios.kt:36-50` (top bar initial height and forwarded window insets); `calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveScaffold.ios.kt:29-35` (measured node feeds Scaffold).
- **Evidence:** The third UI diagnostic compiled production iOS KLIB but failed test KLIB compilation. The planned NativeBarOwnershipTest changes host geometry; it did not run and is not a physical rotation/split-view test. Zero native runtime executions.
- **Limits:** No portrait-to-landscape or reverse device run, Dynamic Type, split view, multiwindow, keyboard or large-title transition verification. KLIB compilation proves signatures, not live safe-area measurements or the absence of gaps/overlap.
- **Related prerequisites:** UI-040
- **Next required check:** Execute the repaired native host-measurement tests, then rotate a mounted AdaptiveScaffold/AdaptiveTopBar in both directions without re-keying. Measure content inset/bar bounds across split view, Dynamic Type, safe-area changes and prefersLargeTitles updates; include nested/multiwindow owners to detect stale global state.
- **Compatibility/scope:** No perpetual per-frame measurement poll. Validate behavior for callers who previously forced re-keying by window size before removing their workaround.
- **Records:** [UI-native.md](UI-native.md), [third-ui-ios-klib.verification.json](evidence/gradle/third-ui-ios-klib.verification.json), [NativeBarOwnershipTest.kt](../../calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/navigation/NativeBarOwnershipTest.kt); [preserved upstream context](https://github.com/Apdelrahman1911/nativeCmpkit/issues/32#issuecomment-6388079171).

## Separate PR #551 — selected adaptation, not an upstream merge

Snapshot head: `66e345a9b291d4d82aa76b1f5f0d05e99b1bb8e1`; **open and unmerged at capture**. Selected source/tests from Mohamed Rejeb's PR tip 66e345a9b291d4d82aa76b1f5f0d05e99b1bb8e1 were adapted with additional nativeCmpkit ownership, cancellation, bounded reading, streaming and save-identity corrections. Original commits/authorship and per-file blob OIDs remain recorded. No branch merge or upstream mutation occurred.

Existing destinations: [#4](https://github.com/Apdelrahman1911/nativeCmpkit/issues/4), [#5](https://github.com/Apdelrahman1911/nativeCmpkit/issues/5), [#8](https://github.com/Apdelrahman1911/nativeCmpkit/issues/8), [#43](https://github.com/Apdelrahman1911/nativeCmpkit/issues/43), [#44](https://github.com/Apdelrahman1911/nativeCmpkit/issues/44), [#45](https://github.com/Apdelrahman1911/nativeCmpkit/issues/45), [#48](https://github.com/Apdelrahman1911/nativeCmpkit/issues/48), [#49](https://github.com/Apdelrahman1911/nativeCmpkit/issues/49), [#50](https://github.com/Apdelrahman1911/nativeCmpkit/issues/50), [#51](https://github.com/Apdelrahman1911/nativeCmpkit/issues/51). These ten audit cross-references are preserved; no new PR-import issue or seventeenth context-comment application is proposed.

Inspected receipts: IO Android21/5 XML, picker desktop43/10 and Coil desktop3/1 passed their scoped suites; enclosing multi-module command failed elsewhere. The later picker Android30/7 had28 passed and2 failed copies, explained by Robolectric zero inode identity. The source/test stat correction and five added identity cases await retry. IO/picker iOS production/test KLIB and Coil production KLIB compiled; zero Apple runtime tests. These counts are separate target/command scopes, not unique test totals.

| Adapted/reviewed boundary | Existing finding IDs | Remaining acceptance check |
|---|---|---|
| **Android pending save and typed error paths** — Shared saveable holder, exactly-once consume/busy ownership, explicit lost-byte restoration and no identity-ambiguous destructive write; strict original copy assertions retained. | IO-002, IO-006 | Corrected host retry, real Activity/process/registry restoration, provider failures/partial writes/close/cancel/disposal and deletion refusal. |
| **iOS export, filename and picked-copy ownership** — Owned named staging and explicit asCopy=true preserve source semantics; accepted selection limits precede staged work and unreturned copies are owned. | IO-005, IO-013 | Real source survival, exact exported names, unreadable/disk-full/scoped providers and cleanup on success/cancel/swipe/disposal. |
| **iOS exactly-once document sessions** — Session/delegate terminal guards and disposal ownership; callback exceptions are not caught as operation failures. | IO-007 | Native early swipe/dismissal, overlapping/reentrant callbacks and old-generation teardown; test KLIB compilation alone is insufficient. |
| **Path/URI/metadata** — Readable path versus URI serialization and metadata are distinct; Android content paths and browser paths are null. | IO-014 | iOS staged-copy/Unicode runtime and browser same-name behavior; immutable API/consumer validation for the changed getPath meaning. |
| **Bookmarks/access leases** — Optional Android persistable grants and iOS bookmarks/per-read scope ownership; reference restoration does not grant access. | IO-008 | Actual process/device restart, revoked/stale/provider grants, concurrent scopes and explicit release semantics. |
| **Browser save capability/events and URL lifetime** — Explicit Saved/Cancelled/DownloadStarted/Failed events; downloads are not reported as completed saves. Rejected native pick/write is not silently converted to fallback success. | IO-011, IO-012 | Real user-activation save dialog, writable abort/close/cancel, download timing and Safari/Firefox fallback; upstream stubbed browser claims are not nativeCmpkit verification. |
| **Additional iOS read-memory safety cross-reference** — nativeCmpkit separately validates length, handles zero and copies the checked size. Existing PR cross-reference does not mean every audit fix came verbatim from PR551. | IO-001 | Native NSData/guarded-buffer/ASan and decoder/cancellation integration; shared length tests are not native memcpy execution. |

### Deliberate differences and evidence limits

- Old public packages/JVM facade locations and launcher overloads are retained, not ABI-certified. getPath semantics intentionally change; toUriString is the migration path. nativeCmpkit deliberately differs from PR partial-success/error and browser-fallback behavior; read IO.md instead of promising PR parity.
- The archived PR author reports emulator/simulator/manual/stub runs. Those are historical author claims, not commands executed or independently verified by this migration/development team.
- Original Android failure evidence is retained. The zero-inode test-harness correction is not a pass until new XML/held-input receipts are inspected.
- Host stat/provider fixtures do not establish universal provider-alias identity, process-death safety, or Android kernel behavior.
- No Apple runtime, real browser picker/download, immutable API/packaged consumer or release qualification is established by this adaptation.

**Next:** Rerun the refrozen Android saver suite and inspect exact distinct/hardlink/unknown-identity plus original copy/restoration cases; keep both failed and corrected receipts. Complete resolver/stream failure, cancellation/disposal, grant and callback reentry tests through actual launcher/session paths. Run Apple device/simulator export/bookmark/early-dismissal and real browser user-activation/download matrices, then immutable API/consumer fixtures.

Records: [IO.md](IO.md), [io-android-independent.md](evidence/review/io-android-independent.md), [second-io-perm-and-fourth-ui.summary.json](evidence/gradle/second-io-perm-and-fourth-ui.summary.json), [first-native-and-third-android-host.summary.json](evidence/gradle/first-native-and-third-android-host.summary.json), [first-ios-klib.verification.json](evidence/gradle/first-ios-klib.verification.json), [pr551-source-provenance.json](evidence/io/pr551-source-provenance.json).

## Issue-progress handoff

- Retain upstream and destination original descriptions, comments, IDs, links and labels. The frozen16-comment apply receipt is evidence of that prior application, not authorization for another mutation.
- Reuse the primary mappings exactly. #39/#151/#344/#346 share native issue75; #27/#245 share151; PR551 already cross-references ten audit issues.
- Attach actual command/source hashes and narrow scope to additive progress comments only after lead review. Do not close source-implemented findings or merge PR history by implication.
- No GitHub mutations, source/build edits, snapshot changes, releases, packages or deployments are performed by this documentation task. Containment remains in effect.

Before any future progress comment, re-read the current owner record and verify whether a newer command supersedes the diagnostic cited here. Append its narrow result and immutable revision when available; preserve failures and historical author claims with their original scope. Never bulk-close all PR-linked issues or treat an unsupported/scaffold declaration as delivery of the requested feature.
