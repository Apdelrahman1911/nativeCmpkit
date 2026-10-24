# [Medium][NAV-012] Sample secure password text field logs every entered value

<!-- nativecmpkit-item:audit:NAV-012 -->
## Classification
- **Finding:** NAV-012
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `sample:common`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/AlertDialogScreen.kt:248-265`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/AlertDialogScreen.kt#L248-L265) — `AlertDialogIosTextField callbacks`

## Root cause
The password example sets isSecure=true but its onValueChange prints "Password: $it". The adjacent name field also prints user-entered text.

## Impact and preconditions
Real values entered into the demonstration can appear in local/device diagnostic output; copying the example propagates an unsafe pattern. This is a local logging exposure, not evidence of remote exfiltration or an embedded secret.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- isSecure=true at line262 and println("Password: $it") at line264 are in the same text-field descriptor.

## Recommended solution
Remove value logging from secure/user-data examples. If feedback is useful, display a non-sensitive event/count and explicitly teach that secure rendering does not make logging safe.

## Risks and compatibility
Verification must use synthetic test strings, never an owner's actual password or log dump. Avoid overclassifying a demo log as a remote attack.

## Required tests / acceptance criteria
- Type a synthetic password and confirm its bytes never appear in captured test logs.
- Source assertion prevents interpolation of secure-field content into logging calls.
- Verify secure keyboard/display behavior separately on an iOS device.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
