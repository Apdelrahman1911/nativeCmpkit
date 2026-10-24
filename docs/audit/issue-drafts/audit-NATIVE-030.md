# [Medium][NATIVE-030] macOS sharing blocks a coroutine worker for up to five minutes without cancellation integration

<!-- nativecmpkit-item:audit:NATIVE-030 -->
## Classification
- **Finding:** NATIVE-030
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-share`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt:24-35,74-85`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.desktop.kt#L24-L35) — `rememberShareLauncher/showNativeShare`
- [`calf-share/native/src/lib.rs:180-198,298-324`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/native/src/lib.rs#L180-L198) — `dispatch_async_f and Condvar wait`

## Root cause
The JNI function schedules AppKit work then synchronously waits on Condvar with a 300-second timeout. withContext(Dispatchers.IO) does not make this native blocking call cancellable. There is no native cancellation handle or single-flight request guard; spurious wakes restart a full timeout window.

## Impact and preconditions
Leaving composition cancels the coroutine result delivery but cannot close the picker or immediately release the worker. Repeated launches can occupy many workers and show overlapping native UI. Missing/late callbacks turn into Dismissed after a long delay unrelated to actual user dismissal.

## Supporting evidence
- Rust uses Duration::from_secs(300) and wait_timeout in a loop; Kotlin wraps it only with Dispatchers.IO.

## Recommended solution
Expose asynchronous native completion or a cancellable operation handle, serialize appropriate UI requests, and use an absolute deadline with a distinct timeout/error outcome. Keep all AppKit calls on main and ensure completion-state lifetime handles cancellation/late callbacks.

## Risks and compatibility
The existing implementation correctly keeps the blocking wait off the ordinary Compose UI thread. No macOS missing-callback event was reproduced; the non-cancellable wait and timeout behavior are source-confirmed. Avoid waiting on the AppKit main queue through any new entry point.

## Required tests / acceptance criteria
- Cancel scope while picker open and verify prompt cleanup without occupying an IO worker until timeout.
- Repeated requests, unavailable keyWindow/contentView, timeout, spurious wake and late callback.
- Stress a bounded pool and assert exactly-once terminal result with balanced native lifetime.

## Dependencies
- NATIVE-029

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/508
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
