# [Low][Upstream #78] Contacts and OTP feature

<!-- nativecmpkit-item:upstream-topic:5d3f0dfd1811a8c8d3dd -->
## Imported actionable historical item
- **Original:** https://github.com/MohamedRejeb/Calf/issues/78 (#78, issue)
- **Original author:** `Lilytreasure`
- **Original ID:** `2213460082`; node ID `I_kwDOKDql7s6D7rhy`
- **Original creation / update:** `2024-03-28T15:01:04Z` / `2026-03-16T13:03:18Z`
- **Original state at observation:** `open`
- **Priority:** Low
- **Assessment:** `separate_improvement` — not a newly confirmed bug unless separately demonstrated.

This is a newly created nativeCmpkit issue. GitHub author/timestamp/number metadata cannot be transplanted faithfully. The original full text, comments, timelines and public revisions remain in the independent [raw archive](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata).

## Current-source assessment / evidence
Read/write contacts and SMS permission properties exist, but permission authorization is not contacts retrieval or OTP reading/autofill. The upstream maintainer comment 2378840675 promised a contacts permission via PR181, not a complete contacts/OTP API.

- [`calf-permissions/contacts/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/ContactPermissions.kt:1-23`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/contacts/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/ContactPermissions.kt#L1-L23) — `ReadContacts and WriteContacts properties`
- [`calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/SmsPermissions.kt:1-34`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/SmsPermissions.kt#L1-L34) — `SMS permission properties`

## Recommended next step
Document partial fulfillment and decide separately whether contacts/OTP data APIs belong in scope; use least-privilege platform autofill/retriever approaches rather than blanket SMS reading.

## Risks and required verification
Do not treat the historical report as a current reproduction, or an implemented permission as a complete data API. Define explicit platform capability, unsupported/error/cancel behavior and compatibility before implementing. Add a minimal current-baseline reproduction or a scoped acceptance test matrix; record runtime/OS/browser versions and classify confirmed behavior separately from assumptions. No major rewrite or release is authorized by this issue.

## Deduplication / rationale
Stable topic key: `contacts-otp-scope`. Disposition and code references are preserved in [upstream-actionable-decisions.json](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/migration/upstream-actionable-decisions.json). Already implemented requests and requests covered by audit findings are not blindly recreated.
