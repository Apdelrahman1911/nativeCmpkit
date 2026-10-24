# [Medium][PERM-014] iOS Bluetooth request lifetime and completion need device-backed hardening

<!-- nativecmpkit-item:audit:PERM-014 -->
## Classification
- **Finding:** PERM-014
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/bluetooth`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/bluetooth/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BluetoothPermissionHelper.kt:25,51-94`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/bluetooth/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BluetoothPermissionHelper.kt#L25) — `centralManager/resolveAndCleanup/centralManagerDidUpdateState`

## Root cause
The central manager is retained, but its delegate is an inline anonymous object with no explicit strong field (CoreBluetooth delegate is weak). A single 2s check does nothing if authorization remains NotDetermined; there is no outer deadline/cancellation. Repeated requests replace centralManager, and old cleanup can clear a newer request. User callback executes before stopScan/cleanup.

## Impact and preconditions
Depending on Kotlin/Native ObjC retention and callback ordering, results may never arrive or scans/helpers may survive longer than intended. Callback exceptions/reentrancy can bypass or misdirect cleanup. These are source-supported risks, not a measured leak or confirmed device failure.

## Supporting evidence
- Explicit callbackFired guard and manager retention are positive existing safeguards; delegate retention and request disposal are absent.
- #339 and commit527cb35 fixed earlier API selection/NotDetermined handling, but do not prove these remaining edge paths.

## Recommended solution
Strongly retain a per-request delegate/context, serialize requests, clear by identity before notifying, stop scan in finally, and provide disposal/timeout as explicit non-denial outcomes. Only scan in a powered-on state.

## Risks and compatibility
The historical PR reports device tests passing common flows; preserve those fixes. Kotlin/Native GC/ObjC lifetime behavior must be measured before claiming the weak delegate is the actual cause of a production failure.

## Required tests / acceptance criteria
- Force Kotlin/Native GC while permission dialog waits, consent after >2s, powered-off/resetting hardware, unsupported BT.
- Repeated/reentrant requests, throwing callbacks, composition disposal; Instruments/leak and scan activity inspection.

## Dependencies
- PERM-007

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/205
- https://github.com/MohamedRejeb/Calf/pull/339
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
