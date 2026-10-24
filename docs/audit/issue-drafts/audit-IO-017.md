# [Medium][IO-017] Some remembered launchers retain stale selection limits, image representation and parent windows

<!-- nativecmpkit-item:audit:IO-017 -->
## Classification
- **Finding:** IO-017
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt:99-105,147-169`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt#L99-L105) — `remembered launcher/selectionMode`
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.desktop.kt:23-38,49-55`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.desktop.kt#L23-L38) — `resolvedParentWindow capture`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt:226-240`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt#L226-L240) — `settings.imageRepresentationMode capture`

## Root cause
Desktop picker recreates its native handle for current selectionMode but its once-remembered launch lambda truncates using the initial selectionMode. Desktop saver captures resolvedParentWindow directly in remember without keys/state. iOS photo launcher captures settings directly although only UIViewController keys remember.

## Impact and preconditions
Changing maxItems can enforce the old limit despite current native selection settings. Changing parent window can leave dialogs attached to an old/closed window. Switching Compatible/Current image representation is ignored until launcher recreation.

## Supporting evidence
- Desktop line 167 reads selectionMode from remember { } without currentSelectionMode, unlike currentType/currentOnResult.
- Desktop saver resolvedParentWindow at 27 is captured at 38/55; currentSettings does not update that local capture.
- iOS photo imageRepresentationMode is read from the settings parameter captured inside remember(currentUIViewController).
- Historical c0c2278 improved updated-state handling but did not cover these fields.

## Recommended solution
Use rememberUpdatedState for every changing value read by a retained lambda or make the appropriate values remember keys. Snapshot configuration per launch to avoid applying later settings to in-flight results.

## Risks and compatibility
Recreating a launcher while an external dialog is open must not orphan its session. Parent-handle updates interact with native lifetime ownership.

## Required tests / acceptance criteria
- Recompose maxItems 2 to 5 and null to limit
- Swap Compose parent window
- Toggle iOS Compatible/Current
- Change callback while picker open
- No stale/duplicate native handles after update

## Dependencies
- IO-003

## Historical context
- https://github.com/MohamedRejeb/Calf/commit/c0c2278
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
