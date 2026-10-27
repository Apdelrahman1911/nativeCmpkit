# ADR 0006 — Own a genuine UIKit application for native library tests

- Date: 2026-10-27
- Status: accepted for contained test integration; **Apple runtime verification pending**
- Scope: library-test host and evidence transport, not public API or production architecture

## Context

Compose1.12 v2's Skiko scene is not UIApplication/ComposeUIViewController. KGP's
simulator task uses `simctl spawn`, not app launch. Seven existing presenter tests
need a real active key-window hierarchy; substituting Skiko, skipping them or
constructing unattached UIKit objects cannot establish native correctness.

Actual Linux Kotlin/Native/KGP diagnostics prove explicit entry plus generated
Worker suites and real TeamCity/JUnit failure propagation. They prove no Apple
application lifecycle. KGP deliberately passes `--ktest_no_exit_code`; failed
testcases, not a normal runner-exit-zero, decide the test task outcome.

## Decision

Add a separate application test binary/task sharing the actual test compilation,
leaving default/public binaries and names unchanged. `UIApplicationMain` and an
owned key window/root run on main; generated tests run on an owned Worker while
the real UIKit event loop remains live. Native operations dispatch synchronously
to main. Idle requires actual attachment, committed composition generation and
no pending Recomposer work; polling sleep alone is not evidence.

Actual application activation later exposed an eager root-attachment assertion.
Startup must return to the main loop and require observed active/key/visible/root
attachment before exactly-once worker admission. A10s deadline does not reset on
repeated activation. The strict native identity contract is retained; bounded
false-predicate booleans explain timeout without silently accepting another root.
A retained startup timeout permanently fails transport and claimed-success
receipts; it cannot replace real XML or count as an executed testcase.

The subsequent immutable timeout establishes a persistent disagreement between
Kotlin wrapper `===` and native value equality, not exact pointer identity.
For test-host native ownership, compare **nonnull retained NSObject pointers**
through the configured public `kotlinx.cinterop.objcPtr` API. Never substitute
NSObject value equality, cache addresses, or accept two null objects as owners.
Attachment, root replacement, idle and foreign-root cleanup share that contract.
An additional mandatory native test rejects equal-content/different-allocation
NSMutableData objects and null owners, and checks the actual window getter.
The first import attempt failed compilation and is preserved; corrected imports
pass full-test KLIB compilation, **not Apple runtime verification**. See the
[exact-identity evidence](../development/native-ui-application-host.md#exact-native-object-identity-after-the-persistent-startup-timeout).

Install/launch only a fresh source/session-bound disposable application on the
exact recorded Arm64 simulator. Verify actual Mach-O/header and installed bytes,
forward real native TeamCity frames verbatim into **KGP's existing parser**, then
cross-check all fresh XML identities/statuses against the complete native protocol
and source/runtime/ownership/cleanup receipt. Eleven explicit genuine-host/presenter
methods cannot disappear. Crashes, timeouts, unknown control errors, stale/zero/
duplicate evidence or cleanup uncertainty fail; matching failed cases stay failed.

No fabricated JUnit, arbitrary filters, sample-app substitution, foreign-app/device
mutation, unverified native fallback, package upload, deployment or permission
expansion. Only report JSON/XML are uploaded. Current all-actions/no-mandatory-SHA
owner policy and read-only verification permissions remain unchanged.

## Alternatives and consequences

- `simctl spawn`, including KGP `standalone`, cannot supply the required app lease.
- Skiko remains useful for its own scene/object tests, not presenter acceptance.
- Replacing KGP's parser with custom fabricated XML would add an unverified result
  producer. We retain its proven real parser and add agreement checks instead.
- The test transport and cleanup contracts need their own adversarial tests;
  their synthetic SDK/native records must never be counted as library/device tests.
- Actual Apple linking, application launch and native execution remain required.
  Full simulator/device/VoiceOver, legal, dependency, consumer and ABI gates remain
  open. A compiled KLIB/model or accepted app launch is not release readiness.

See [implementation/evidence](../development/native-ui-application-host.md),
[containment](../development/containment.md) and
[release gates](../development/release-readiness.md).
