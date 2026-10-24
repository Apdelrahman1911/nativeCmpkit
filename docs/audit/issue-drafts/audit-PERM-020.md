# [Medium][PERM-020] Android LocationTracker rebinding has no ownership boundary or coroutine cleanup

<!-- nativecmpkit-item:audit:PERM-020 -->
## Classification
- **Finding:** PERM-020
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-geo`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt:31-55,105-121`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt#L31-L55) — `bind/lifecycle observer/trackerScope/stopTracking`

## Root cause
Every bind replaces a shared client and adds an observer to the supplied lifecycle without removing previous observers. Old observers dereference the current client on destruction. isStarted survives destruction; scope/channels are never cancelled/closed and callbacks do not check active generation.

## Impact and preconditions
Destroying an old lifecycle after rebinding can stop/null the new client. Repeated binds and in-flight callbacks can retain tracker/owner references or deliver after stop; scope work has no explicit shutdown contract.

## Supporting evidence
- Observer at lines49-54 captures the tracker and uses mutable locationProviderClient, not the client/owner it was created for.
- trackerScope has no cancel call and channels no close/consume calls anywhere in geo.

## Recommended solution
Have one bound-owner token/observer/client at a time, detach/remove old updates on rebind, use a cancellable lifecycle-owned scope, clear active state on destruction and reject late callbacks by generation. Remove unused fragmentManager argument through a compatibility deprecation.

## Risks and compatibility
Source proves cross-owner interference; actual leak duration depends on FusedLocation callbacks and Android lifecycle GC. Do not close reusable channels without defining restart semantics.

## Required tests / acceptance criteria
- Bind A,start,bind B,destroy A: B continues; destroy B stops exactly once.
- Repeated bind/start/stop, queued callback after stop, destruction/restart, weak-reference/leak checks.

## Dependencies
- PERM-018

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/40
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
