# [Medium][NATIVE-025] ShareResult.Success means chooser launch/service selection rather than completed sharing on some targets

<!-- nativecmpkit-item:audit:NATIVE-025 -->
## Classification
- **Finding:** NATIVE-025
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-share`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt:26-30`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt#L26-L30) — `rememberShareLauncher result callback`
- [`calf-share/native/src/lib.rs:136-162`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/native/src/lib.rs#L136-L162) — `did_choose delegate`
- [`calf-share/src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareResult.kt:11-19`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareResult.kt#L11-L19) — `Success/Dismissed semantics`

## Root cause
Android reports Success immediately after startActivity(chooser), before user selection or cancellation. macOS returns Success when NSSharingServicePicker didChooseSharingService reports a non-null service, not when that service completes or fails.

## Impact and preconditions
Consumers may erase source files, show false success, count completed shares or navigate away even if a user cancels or a service later fails. Android Dismissed cannot be produced by this implementation; macOS success is only service selection.

## Supporting evidence
- Android callback at28 follows startActivity immediately.
- Rust chosen=!service.is_null() directly maps to RESULT_SUCCESS.
- iOS completionWithItemsHandler uses the completed flag, illustrating nonuniform semantics.

## Recommended solution
Make result semantics explicit per platform and distinguish Presented/Selected from Completed where native APIs permit. Android cannot generally prove a recipient delivered content; macOS should observe the service delegate for actual completion if claiming it. Preserve existing API through a documented additive result model.

## Risks and compatibility
Do not promise actual delivery through share targets that expose no completion API. A compatibility change to Success meaning requires migration notes. Files must remain available while the recipient/service still reads them.

## Required tests / acceptance criteria
- Dismiss Android chooser and cancel/fail a selected macOS service without reporting completed share.
- Verify callbacks occur at documented stages and exactly once.
- Delay recipient file reads past chooser selection to validate file lifetime.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/508
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
