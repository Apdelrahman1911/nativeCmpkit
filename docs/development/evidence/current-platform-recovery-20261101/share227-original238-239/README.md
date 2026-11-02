# Share227: original failure and source/results review238–239

Run [41390900453](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41390900453),
attempt1 at `8a2b307e1b30f8702e7ef68d456c06f06ef0ba1a`, remains **FAILED**:
one remembered-public method, **0 pass/1 fail/one original XML; Gradle1/1177.32s**.
Logs and artifact13118471305 were acquired once after terminal; reuse them.

The shared tooling job passes. All **1195 actual before/after inputs** equal the
immutable dispatch freeze;1273 combined inputs remain predispatch-only. Original
native/XML inventories and hashes agree. Genuine application transport11.24s,
Worker termination, installed byte identity and owned app/bundle cleanup pass
independently; none turns the JUnit failure green. **23 passive review checks**
are recorded in [REPORT.json](REPORT.json), not additional native tests.

## Exact observed ordering

The first/Main assertion again expects `[(1, Completed)]` but receives
`[(1, Dismissed)]`. The bounded main-only trace records:

1. Input `completed=false,error=false`, active request, phase `Presented`.
2. Original delegate returns; request is inactive and `Released`.
3. The fixture records its genuine native dismissal acknowledgment.
4. The fixture then sends `completed=true` twice through the saved block; the
   released generation correctly ignores both.

The trace is complete within its seven-entry bound, but **does not independently
attribute UIKit-versus-fixture origin**; installing the observer changes block
identity and timing. Source shows the two controlled true calls live *inside*
the programmatic dismissal completion. Expecting those later calls to override
an already accepted first terminal input is an invalid fixture stimulus.
Do not force `Completed`, ignore an ordinary false input, or weaken once-only
result assertions. Default/IO/reentry/composition-disposal tail is unreached.

## Separate, source-confirmed lifecycle gap

At this exact head, `IosShareOwner.launch`'s activity completion handler directly
clears `active` and calls `Request.release()` before any presentation/dismissal
completion barrier. `Request.release()` clears the native block and closes file
scopes. In this trace that release precedes the fixture's native acknowledgment.
This establishes the **unconditional source release path**, not a measured
use-after-close, a positive security-scope start, external resource liveness or
OS-recipient completion. The existing deferred-disposal barrier does not cover
terminal callbacks. Terminal input handling needs the same real native barriers
and must keep the first result, suppress owner-disposed results, and release
before application reentry.

Next is a focused terminal-barrier correction with controlled phase/duplicate/
throwing-callback regressions and the existing public remembered assertions.
Real native cancellation/recipient/service outcomes and positive scope balancing
remain separate verification requirements. **#81/#88/#48/#100 stay open**; no
issue closure, consumer/API-ABI/security/readiness or publication inference.
