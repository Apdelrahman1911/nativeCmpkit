# Windows one-row observer: hosted 770 refusal and owned-EOF successor

## Original hosted 770 — diagnostic accepted, response still refused

Run **42040119698/attempt1**, job **127288430984**, completed successfully at
`b2fdb17fe2107af6fef0cc3e3ee13df1bb757b00`. Its accepted public3 reports cover
only original row 0 `convention-gradlePlugin-android:pom`: **one attempted request**,
not the unchanged 120-row plan.

The worker observed **HTTP 200 and 9,034 private body bytes**, then **REFUSED** with
primary `transport-settimeout-body` errno/winerror **10038**. Complete-response
and public-text admission remained false. Custody of 18 source inputs, protocol completion,
child exit 0, empty Job/direct-terminal disposition and seven successful cleanup records
were accepted; no private body or transcript is published here. Public3 contains
no response headers, framing or dynamic descriptor state. HTTP 200/count alone are
not EOF, syntax or HTTPS-trust proof; original 766's cause remains **UNKNOWN**.

## Narrow owning EOF fix

A real `HTTPResponse.read1()` can release its owning file/borrowed socket after
the final payload. The successor checks readonly `response.isclosed()` before
each body-loop `transport.settimeout()`, skipping **only that timeout update**
when already closed. It still performs the next `read1()` and genuine empty EOF,
with unchanged deadline, framing/length, byte-cap and refusal checks. It neither
swallows an open-body OSError nor accepts a matching payload count as EOF.

The diagnostic delegates the readonly lifetime check; only the affected mock
lifetime and exact route-inverse fixture are adjusted. Workflow, original 120-row
plan, fixed-row selection, Windows Job/controller/worker bounds, exports,
`NO_ADMISSION`, None/XML policy and all other admission/trust assertions remain
unchanged. Frozen 770 sources and every original result remain intact.

## Actual local source/model results — independent 742 accepted

**Four new + two genuinely affected methods passed once: 6/6 and 27 subtests.** Exact 25
finite model/executor inputs held before/after. Six serial real AF_UNIX socketpairs
and 12 descriptor wraps were used; all owned objects closed, and direct-child,
group absence/reap and empty-only runtime cleanup completed.

Real HTTPResponse ownership/framing tests distinguish full Content-Length EOF
from truncation and full chunked EOF from a missing zero terminator. Closed
lifetime still refuses expired deadlines/exact hard caps; open-body 10038 and
separate cleanup errors are not swallowed. Independent 742 source/executor and
original-results acceptance are reused, not replayed or freshly reacquired here.

## Limits retained

These are offline local source/model results, **not a new Windows request**.
The successor still needs separately authorized hosted observation; no 120-row
replay, HTTPS certificate/proxy/redirect/trust acceptance, ordinary consumer,
compiler/native, API–ABI, dependency/legal/security or release-readiness clearance
follows. **#64, #40 and BUILD remain open/unqualified**; no whole-issue closure,
package, release or deployment is authorized.

Authority: 734's sealed original-public3 actual 770 acceptance and 742's sealed
after 770 source/executor and original six-method results acceptance. Lead retains
integration/adoption/Git/dispatch and any later acceptance or closure.
