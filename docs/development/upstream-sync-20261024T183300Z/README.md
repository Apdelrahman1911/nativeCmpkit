# Current open-upstream issue reconciliation

Captured 2026-10-24T18:34:54Z–2026-10-24T18:35:38Z (UTC).
Source: `MohamedRejeb/Calf` at `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`. Destination snapshot: `e0724790ed827020970d538928cc25bdc9ea0baa`.

**16 actual open issues; 1 open PR separately excluded.**
**16 proposed context comments, zero new issues, zero state/body/label replacements.**

This is verified read-only reconciliation, not a claim that the lead has posted the drafts. Each draft retains full original description, labels, public discussion and attributed history links.

**Subsequent lead application:** [completion receipt](completion.json) verifies
all 16 comments posted and independently read back, with zero new issues.
[Comment IDs, immutable archive SHA and hashes](apply-receipt.json) and
[additive label readbacks](label-preservation.json) preserve the mutations.
All original destination technical bodies, states and existing labels remained
intact. Production fixes began only after this prerequisite completed.

| Calf | Primary nativeCmpkit | Disposition | Required action |
|---|---|---|---|
| [#27](https://github.com/MohamedRejeb/Calf/issues/27) Add Maps Support | #151 | covered_by_finding | create-context-comment |
| [#34](https://github.com/MohamedRejeb/Calf/issues/34) Camera issue in webview iOS | #168 | needs_reproduction | create-context-comment |
| [#39](https://github.com/MohamedRejeb/Calf/issues/39) Webview not loading html content | #75 | covered_by_finding | create-context-comment |
| [#72](https://github.com/MohamedRejeb/Calf/issues/72) Zoom in/out in browser | #170 | needs_reproduction | create-context-comment |
| [#78](https://github.com/MohamedRejeb/Calf/issues/78) Contacts and OTP feature | #166 | separate_improvement | create-context-comment |
| [#151](https://github.com/MohamedRejeb/Calf/issues/151) Webview not work on Linux | #75 | covered_by_finding | create-context-comment |
| [#245](https://github.com/MohamedRejeb/Calf/issues/245) Custom data source media content | #151 | covered_by_finding | create-context-comment |
| [#259](https://github.com/MohamedRejeb/Calf/issues/259) Demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog | #165 | separate_improvement | create-context-comment |
| [#288](https://github.com/MohamedRejeb/Calf/issues/288) Request this library can take camera | #77 | already_implemented | create-context-comment |
| [#309](https://github.com/MohamedRejeb/Calf/issues/309) firebase compatibility | #51 | covered_by_finding | create-context-comment |
| [#343](https://github.com/MohamedRejeb/Calf/issues/343) Support native file preview | #169 | separate_improvement | create-context-comment |
| [#344](https://github.com/MohamedRejeb/Calf/issues/344) [BUG] WebView throwing error on configuration | #75 | already_implemented | create-context-comment |
| [#346](https://github.com/MohamedRejeb/Calf/issues/346) [BUG] Reentry into ignoringRedrawRequests is not allowed (WebView) | #75 | covered_by_finding | create-context-comment |
| [#471](https://github.com/MohamedRejeb/Calf/issues/471) Feature request: iOS-native styling customization for AdaptiveNavigationBar and AdaptiveTopBar | #167 | separate_improvement | create-context-comment |
| [#530](https://github.com/MohamedRejeb/Calf/issues/530) AdaptiveNavigationBar on iOS - bottom bar is visible when navigating away, and during back navigation gestures | #33 | covered_by_finding | create-context-comment |
| [#548](https://github.com/MohamedRejeb/Calf/issues/548) [Bug]:  AdaptiveTopBar (iOS): content top padding goes stale after device rotation | #32 | covered_by_finding | create-context-comment |

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

- Fresh raw snapshot: `docs/migration/upstream-updates/20261024T183300Z`; original source descriptions and discussions are retained without truncation.
- Original description/label/author/comment equality with the frozen migration archive: **True**. Added timeline entries: **17**; inspect their types and source URLs in `reconciliation.json` separately from user-text changes.
- Assessed implementation-byte equality: **True**. Changed assessed source/build files: `settings.gradle.kts`. The broader all-files-unchanged flag includes build identity files, not only implementations.
- No physical/device runtime reproduction was performed by this synchronization task. Source-addressed means the cited implementation exists, not that every related runtime behavior passes.
- Deleted/private/redacted metadata remains unavailable. Pagination is complete for accessible endpoints, but the observation interval is not an atomic transaction.
- The 2026-10-24 baseline disposition file was reused only with fresh state/discussion capture and current committed source-byte checks; no production fixes were applied during this task.

### This observation's non-content differences

All 16 original descriptions/labels/authors and 14 comments are unchanged. The 17 new timeline items are automatic cross-references from the existing nativeCmpkit tickets, not original-author text edits. Of 23 assessed files, only settings.gradle.kts differs (the existing migration comment and root project rename); the other 22 files are byte-identical to baseline.
