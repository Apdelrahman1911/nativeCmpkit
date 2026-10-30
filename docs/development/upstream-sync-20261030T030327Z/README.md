# Current open-upstream issue reconciliation

Captured 2026-10-30T03:03:27Z–2026-10-30T03:04:04Z (UTC).
Source: `MohamedRejeb/Calf` at `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`. Destination snapshot: `94d2492e99d5cbc060409d94d9f88febd06222d5`.

**16 actual open issues; 1 open PR separately excluded.**
**0 proposed context comments, zero new issues, zero state/body/label replacements.**

This is verified read-only reconciliation, not a claim that the lead has posted the drafts. Each draft retains full original description, labels, public discussion and attributed history links.

| Calf | Primary nativeCmpkit | Disposition | Required action |
|---|---|---|---|
| [#27](https://github.com/MohamedRejeb/Calf/issues/27) Add Maps Support | #151 | covered_by_finding | no-op-context-current |
| [#34](https://github.com/MohamedRejeb/Calf/issues/34) Camera issue in webview iOS | #168 | needs_reproduction | no-op-context-current |
| [#39](https://github.com/MohamedRejeb/Calf/issues/39) Webview not loading html content | #75 | covered_by_finding | no-op-context-current |
| [#72](https://github.com/MohamedRejeb/Calf/issues/72) Zoom in/out in browser | #170 | needs_reproduction | no-op-context-current |
| [#78](https://github.com/MohamedRejeb/Calf/issues/78) Contacts and OTP feature | #166 | separate_improvement | no-op-context-current |
| [#151](https://github.com/MohamedRejeb/Calf/issues/151) Webview not work on Linux | #75 | covered_by_finding | no-op-context-current |
| [#245](https://github.com/MohamedRejeb/Calf/issues/245) Custom data source media content | #151 | covered_by_finding | no-op-context-current |
| [#259](https://github.com/MohamedRejeb/Calf/issues/259) Demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog | #165 | separate_improvement | no-op-context-current |
| [#288](https://github.com/MohamedRejeb/Calf/issues/288) Request this library can take camera | #77 | already_implemented | no-op-context-current |
| [#309](https://github.com/MohamedRejeb/Calf/issues/309) firebase compatibility | #51 | covered_by_finding | no-op-context-current |
| [#343](https://github.com/MohamedRejeb/Calf/issues/343) Support native file preview | #169 | separate_improvement | no-op-context-current |
| [#344](https://github.com/MohamedRejeb/Calf/issues/344) [BUG] WebView throwing error on configuration | #75 | already_implemented | no-op-context-current |
| [#346](https://github.com/MohamedRejeb/Calf/issues/346) [BUG] Reentry into ignoringRedrawRequests is not allowed (WebView) | #75 | covered_by_finding | no-op-context-current |
| [#471](https://github.com/MohamedRejeb/Calf/issues/471) Feature request: iOS-native styling customization for AdaptiveNavigationBar and AdaptiveTopBar | #167 | separate_improvement | no-op-context-current |
| [#530](https://github.com/MohamedRejeb/Calf/issues/530) AdaptiveNavigationBar on iOS - bottom bar is visible when navigating away, and during back navigation gestures | #33 | covered_by_finding | no-op-context-current |
| [#548](https://github.com/MohamedRejeb/Calf/issues/548) [Bug]:  AdaptiveTopBar (iOS): content top padding goes stale after device rotation | #32 | covered_by_finding | no-op-context-current |

## Safety and lifecycle

- Source-addressed #288 (existing mobile camera API) and #344 (JavaFX settings now dispatched with Platform.runLater) are not new confirmed defects. Their distinct current destination bugs stay open.
- #471 and #78 are only partly fulfilled; retain remaining styling / contacts-and-OTP scope. Maps/media and native preview remain scoped roadmap items, not implemented features.
- #551 is an open PR, not an issue. Its source history is archived and the existing IO tickets remain the integration-review owners.
- Original upstream user content is untrusted quoted data. No instructions embedded in it were executed.
- The original `upstream-metadata` archive and its SHA256SUMS were not rewritten. This dated snapshot has its own raw response hashes, pagination evidence, receipt and SHA256SUMS.

## Applying the handoff (lead only)

1. Review `receipt.json`, `reconciliation.json` and `mutation-handoff.json`; do not apply if blockers are present.
2. Commit/push the fresh snapshot, then bind `__UPSTREAM_SYNC_ARCHIVE_COMMIT__` to that 40-hex commit in each body. Recompute each final body hash.
3. Re-read each destination identity and all existing comments. A stable source marker already present must not produce another POST; preserve human changes and existing issue states/labels/bodies.
4. POST only the proposed comments. A lost/unknown response requires marker reconciliation, never blind automatic retry.
5. Store actual comment IDs/URLs/body hashes and perform a fresh read-only verification before declaring synchronization complete or starting production fixes.

## Evidence and limits

- Fresh raw snapshot: `docs/migration/upstream-updates/20261030T030327Z`; original source descriptions and discussions are retained without truncation.
- Original description/label/author/comment equality with the frozen migration archive: **True**. Added timeline entries: **17**; inspect their types and source URLs in `reconciliation.json` separately from user-text changes.
- Assessed implementation-byte equality: **False**. Changed assessed source/build files: `calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt`, `calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt`, `calf-webview/build.gradle.kts`, `settings.gradle.kts`, `calf-camera-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.kt`, `calf-camera-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/camerapicker/CameraPickerLauncher.android.kt`, `calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt`, `calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt`, `calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.kt`, `calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/TabBarManager.kt`, `calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.ios.kt`, `calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveScaffold.ios.kt`, `calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.ios.kt`. The broader all-files-unchanged flag includes build identity files, not only implementations.
- No physical/device runtime reproduction was performed by this synchronization task. Source-addressed means the cited implementation exists, not that every related runtime behavior passes.
- Deleted/private/redacted metadata remains unavailable. Pagination is complete for accessible endpoints, but the observation interval is not an atomic transaction.
- The 2026-10-24 baseline disposition file was reused only with fresh state/discussion capture and current committed source-byte checks; no production fixes were applied during this task.
