# [Low][NAV-017] Showcase reports a successful clipboard action that it never performs

<!-- nativecmpkit-item:audit:NAV-017 -->
## Classification
- **Finding:** NAV-017
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `sample:common`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ShowcaseScreen.kt:127-129`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ShowcaseScreen.kt#L127-L129) — `Material share action`
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ShowcaseScreen.kt:158-162`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ShowcaseScreen.kt#L158-L162) — `UIKit share action`
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ShowcaseScreen.kt:227-235`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/ShowcaseScreen.kt#L227-L235) — `share result dialog`

## Root cause
Both share actions only set showShareDialog=true; the dialog says "Link copied to clipboard!" without any clipboard/share operation.

## Impact and preconditions
The demo gives a false success signal and can lead users to assume a platform integration was tested when only a dialog was exercised.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- There is no clipboard invocation in ShowcaseScreen; action callbacks at128/161 only mutate a Boolean.
- The separate ShareScreen uses rememberShareLauncher and is audited by native features.

## Recommended solution
Either implement a real copy/share operation with result handling or make the dialog explicitly a visual demonstration. Do not conflate it with the separate functional ShareScreen.

## Risks and compatibility
Clipboard changes are externally observable user state and should occur only from the explicit user action; device behavior still needs testing if implemented.

## Required tests / acceptance criteria
- Assert the dialog text is truthful for the chosen demonstration behavior.
- If copy is implemented, verify clipboard content from one explicit user tap on each supported platform.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
