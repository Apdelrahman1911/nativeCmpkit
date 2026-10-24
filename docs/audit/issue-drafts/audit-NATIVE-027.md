# [High][NATIVE-027] Desktop share fallback opens arbitrary files/URLs instead of offering an explicit sharing fallback

<!-- nativecmpkit-item:audit:NATIVE-027 -->
## Classification
- **Finding:** NATIVE-027
- **Priority:** High
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-share`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt:51-64,108-155`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt#L51-L64) — `handleShare/shareUrlFallback/shareFileFallback/shareFilesFallback`

## Root cause
On Windows/Linux or any native-share failure, URLs are sent to Desktop.browse and files to Desktop.open with no MIME, URI-scheme or executable/handler policy. This occurs automatically after swallowed native errors, not after a separate open/preview decision.

## Impact and preconditions
A user asking to share can instead launch a registered URL handler or open an untrusted file in an associated application. Depending on OS associations, opening executable/script/shortcut content can run code; many files can launch many apps. No code execution exploit was demonstrated and user-supplied content/control of the call are required.

## Supporting evidence
- shareFileFallback calls desktop.open(file) at132; Files repeats it at147.
- MIME type passed in ShareContent.File/Files is not used by Desktop fallback.

## Recommended solution
Make fallback behavior explicit/opt-in. Prefer Unavailable, copying shareable data, or a documented export/open-location action over automatically opening content. Validate supported URL schemes and avoid executing/previewing untrusted files as an incidental share operation.

## Risks and compatibility
Current docs disclose opening default apps on Windows/Linux, so this is a safety/design risk rather than hidden malicious behavior. Removing it can be a user-visible compatibility change; offer a policy parameter and deprecation path.

## Required tests / acceptance criteria
- With OS open/browse calls mocked, file share does not execute/open without chosen policy.
- Native-loader failure follows the same safe fallback as unsupported OS.
- Untrusted file extensions/custom URI schemes and multi-file partial failure produce a truthful result without unintended handlers.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/508
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
