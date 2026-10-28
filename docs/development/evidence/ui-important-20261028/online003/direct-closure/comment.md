## Verified fix — direct closure after important actual indication lifecycle tests

Both **original UI-043 acceptance criteria** pass at immutable **ca349b19a0e53901909cf32bc74e95936b367a1f**. The focused Linux/Xvfb command executes **3/3 actual library methods**, one fresh XML, zero failures/errors/skips, exit0/48.63seconds. Only CupertinoIndicationTest runs; the already accepted indicator4 and every unrelated suite are **not replayed**.

- Actual public CupertinoButton composition: release at exactly**20ms**, re-press at exactly**40ms**, before100ms on the controlled Compose mainClock. Explicit clock-delta assertions prohibit frame-rounded20ms requests. The new press remains visibly highlighted through the hold; only its final release returns to normal pixels.
- Two actual PressInteraction instances: cancelling the first does not clear the second's highlight.
- New actual production **IndicationNode lifecycle** regression: the real node collects Release before deactivation while feedback is pending; actual isAttached becomes false, then the **same factory-created node** reattaches. It resets the previous appearance, does not replay a detached stale Cancel, retains the current press beyond the old release window, restores after the current Cancel and detaches again. Factory/Flow wrappers only observe actual production node identity and actual event collection; no replacement renderer or fake lifecycle is used.

Owning production repair: each new press cancels the single prior feedback job; only matching active-press removal can release the last highlight; onDetach cancels feedback and resets alpha. Public APIs and the100ms minimum-duration policy are preserved. This continuation verifies the earlier production repair and adds/strengthens the important regressions, not an unrelated refactor.

Review checks745 exact own-Git inputs, before/after equality, exact three authored testcase identities with desktop target markers, fresh XML and actual Gradle9.7.1/JDK17.0.20(Ubuntu)/Linux runtime. The prior seven-case pass remains7/7;744 unchanged inputs substantiate not repeating the accepted indicator4. These two successful attempts execute**10 fresh cases from7 authored method names**, not10 unique tests. Earlier offline/configuration and fixture-compilation failures retain zero executed tests; stale reports were never accepted.

Important tests → source/results review → **direct closure now** → archive/index afterward. Evidence will be retained under `docs/development/evidence/ui-important-20261028/online003/`. Original issue body/title/labels preserved.

This is actual Compose/Skia rendering and production interaction objects on Linux, not physical multi-touch/UIKit/native-device/assistive or other OS/branch certification.20/40ms are controlled-clock values, not wall-clock latency/performance measurements. No consumer/ABI/dependency/legal/native/security/release gate cleared; nothing published or deployed.

<!-- nativecmpkit:direct-acceptance:UI-043:ca349b19 -->
