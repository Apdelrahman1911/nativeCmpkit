# [Low][NATIVE-034] Share subject is not delivered consistently and iOS assigns controller title instead of item subject

<!-- nativecmpkit-item:audit:NATIVE-034 -->
## Classification
- **Finding:** NATIVE-034
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-share`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt:61-70`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt#L61-L70) — `subject mapping`
- [`calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareContentExt.ios.kt:9-24`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareContentExt.ios.kt#L9-L24) — `activity item conversion`
- [`calf-share/src/webMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.web.kt:96-109`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/webMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.web.kt#L96-L109) — `web file sharing`
- [`calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt:66-80,91-96`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt#L66-L80) — `native/fallback content conversion`

## Root cause
iOS assigns activityViewController.title rather than supplying an activity item subject. Raw items do not implement UIActivityItemSource subjectForActivityType. Desktop drops all subject fields; web text/URL use title but file/multiple-file subject is discarded.

## Impact and preconditions
Apps relying on the advertised optional email subject do not get consistent mail/share metadata. This is a functional parity gap rather than a security defect.

## Supporting evidence
- Apple UIActivityItemSource subjectForActivityType documentation identifies the supported subject hook; no item source exists here.
- Desktop tuple conversion and browser file helpers accept no subject.

## Recommended solution
Supply native item-source subject where supported, pass file title/subject to Web Share where applicable, and document which platforms cannot honor the field. Avoid implying MIME override support on systems deriving file type from the URL.

## Risks and compatibility
Email target behavior varies; UIActivityViewController title is not documented as the mail subject API. Verify actual mail/service integrations rather than assuming one native workaround works universally.

## Required tests / acceptance criteria
- iOS Mail subject for text, URL, single and multiple files.
- Web payload inspection verifies title/file fields; unsupported metadata is documented.
- Desktop native/fallback subject behavior is explicit and tested where implementable.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/508
- https://developer.apple.com/documentation/uikit/uiactivityitemsource/activityviewcontroller(_:subjectforactivitytype:)
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
