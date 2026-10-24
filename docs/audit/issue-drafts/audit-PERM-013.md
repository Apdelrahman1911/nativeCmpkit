# [High][PERM-013] iOS Wi-Fi status observation publishes a Bonjour service and conflates timeout/cancellation with denial

<!-- nativecmpkit-item:audit:PERM-013 -->
## Classification
- **Finding:** PERM-013
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/wifi`, `calf-permissions/core`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/wifi/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/WifiPermissionHelper.kt:15-52,67-89,92-117`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/wifi/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/WifiPermissionHelper.kt#L15-L52) — `getPermissionStatus/startCheck/cleanupAndComplete/cancel`
- [`calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.ios.kt:73-75,106-110`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.ios.kt#L73-L75) — `init/refreshPermissionStatus`
- [`docs/permissions.md:537-544`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/docs/permissions.md#L537-L544) — `Wi-Fi Info.plist example`
- [`sample/ios/Calf/Info.plist:29-30`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/ios/Calf/Info.plist#L29-L30) — `local-network description`

## Root cause
getPermissionStatus constructs/publishes _lnp._tcp. NSNetService and is called while remembering the state, before a user request. A fixed three-second timer, inactive app, publication errors and cancelling an older check all complete false/Denied(true). The required Bonjour service declaration is absent from docs/sample.

## Impact and preconditions
Merely observing permission state can trigger a local-network prompt/advertisement. Slow consent or lifecycle changes look permanently denied; overlapping refreshes can complete a user request falsely. Local-network publication does not establish general Wi-Fi configuration/SSID privileges for all three logical Wi-Fi names.

## Supporting evidence
- init immediately calls refresh -> helper.getPermissionStatus -> publish(); no observational/interactive separation.
- cancel() routes through cleanupAndComplete(false); timeout unconditionally false.
- Docs/sample specify NSLocalNetworkUsageDescription only, not NSBonjourServices.

## Recommended solution
Separate passive status/unknown from explicit user-triggered local-network probing, report timeout/unavailable/cancelled separately, declare NSBonjourServices [_lnp._tcp] and the usage string, serialize probes and clean up on disposal. Document that Wi-Fi access/configuration capabilities are distinct from local-network privacy.

## Risks and compatibility
Apple exposes no universal passive local-network authorization query; do not replace this with another undocumented heuristic presented as authoritative. Whether this exact publish operation prompts on each OS/device needs verification.

## Required tests / acceptance criteria
- Remember state without clicking: no network probe/prompt.
- Consent delayed beyond3s, inactive app, publish error, missing Bonjour declaration, denied and granted on real iOS.
- Concurrent refresh/request, three Wi-Fi aliases, disposal and network unavailable; verify cleanup/no advertisement leakage.

## Dependencies
- PERM-007

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/315
- https://github.com/MohamedRejeb/Calf/pull/316
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
