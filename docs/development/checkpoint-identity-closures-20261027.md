# NativeCmpKit identity and original-acceptance review — 2026-10-27

**Contained development, not release readiness.** Work remains on
`development/preview-hardening`; `main` remains the synchronization checkpoint
`94d2492e99d5cbc060409d94d9f88febd06222d5`. Original findings, roadmap acceptance
requirements, imported Git history, notices and metadata archives are unchanged.

## Owner-requested name

The current library/root/POM display name is **NativeCmpKit**. Repository URL,
lowercase Maven coordinates, public packages, module paths, framework/JNI/resource
names and existing Gradle property keys remain compatible. See
[ADR 0008](../decisions/0008-library-display-name.md). No repository rename,
publication, release, deployment or Pages action accompanies the display change.

## Reviewed actual CI failures at 8ab48555

These immutable runs completed; neither is still running or a release pass.
Original report ZIPs/JSON and all reviewer failures are preserved additively,
without console transcripts or candidate packages.

| Run | Actual result | Root cause / repair scope |
|---|---|---|
| [Consumer 40496991035](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40496991035) | Four real local producer publication tasks exit0/202.07s; 308 partial static checks, four resolved classpaths/109 artifact rows/eight exact candidate rows. Child exit1/40.01s, **zero consumer methods/XML**. | The partial test fixture calls `consumeStream`, a full-consumer test helper whose source was deliberately not copied. Both six-method IO test copies now call the same public `file.source(context)` directly. No new fake library API or unrelated source copying. |
| [UIKit 40496950106](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40496950106) | **121 executed /119 pass /2 fail /0 skip**, 24 XML, overall Gradle exit1/1298.66s. All12 mandatory application methods execute,10 pass; all four alert and four application-host methods pass. | Dropdown and time-picker application fixtures fail at their first native subtree `.single()` lookup with an empty list, before intended functionality assertions. Deferred interop insertion is a source-supported hypothesis, not a proven cause. |

The lead independently binds all741 consumer and719 UIKit selected inputs to Git,
checks before/after maps, exact copied-fixture/resolution/metadata bindings,
testcase/XML/protocol counts, genuine Worker activation and owned cleanup. The
consumer's original Gradle-resolution bytes were not uploaded: its recorded raw
hash is **not** confused with the independently hashed Python-reserialized copy.
Legacy and new report schemas are kept distinct.

- [Consumer independent review](evidence/github-actions/40496991035/lead-independent-review.json)
- [UIKit independent review](evidence/github-actions/40496950106/lead-independent-review.json)

### Owning fixture repairs, not a silent green

UIKit fixtures now await a **unique real attached native view** through the
existing bounded main-thread predicate. Replacement additionally requires a
different native pointer and old picker window detachment. All menu presentation,
dismissal, native `valueChanged`, old/new state and compatibility assertions remain.
There are no elapsed-delay success criteria, mocks, skips or missing-native fallbacks.
If the native view never appears, the fixture fails with bounded diagnostics.

The actual copied root now configures as `NativeCmpKit`; help, the genuine KGP
application model and full UIKit-test KLIB compilation pass **exit0/70.01s** with
**720 selected inputs held**. Production dependencies/compilation caches are
reused; the test compilation task actually executes. This is **zero Apple/native
executions**, not verification of the two repaired application methods.
See [the compile receipt](evidence/current-root-klib-20261027/ui/receipt.json).

The [current-brand/fixture guards](evidence/current-brand-fixture-guards-20261027-001/scoped-checks.json)
pass477 overlapping Python method executions:5 identity,5 native-readiness,
6 sample,151 consumer-tooling and310 CI guards, with457 inputs held. That freeze
predates the later comment/indentation and narrow-profile edits; final staged
preflight is separate. These are **not**477 native/library/packaged methods.
Original helper, identity/POM, native-readiness and matrix reds remain archived.

## Four original findings accepted for scoped closure

The lead re-read the **original issue acceptance criteria**, reviewed owning
current implementation/compatibility, independently rehashed original artifact
ZIPs and695 Git-bound inputs, and recounted actual XML methods. All32 navigation
source/test/build inputs and the relevant shared slider implementation/tests
remain byte-identical to the immutable execution at
`6eb7c66eb01b390353100c63882cd102846c7b8d`.

| Finding / existing issue | Original acceptance satisfied |
|---|---|
| **NAV-001 /[#15](https://github.com/Apdelrahman1911/nativeCmpkit/issues/15)** | Independent visit payloads reach content; missing/null/type/default validation; portable argument/entry-ID saver roundtrip and predictable unsupported rejection. |
| **NAV-002 /[#16](https://github.com/Apdelrahman1911/nativeCmpkit/issues/16)** | A→B→A and consecutive duplicate counters; same-frame pop/repush freshness; real registry→Java bytes→dispose/recreate duplicate restoration/pop; both original upstream #542 tests retained **byte-identically** and passing. |
| **UI-033 /[#136](https://github.com/Apdelrahman1911/nativeCmpkit/issues/136)** | Actual Compose semantic `setProgress(-0.7)` snaps to−0.5 with exactly one completion; all-negative/tie/endpoint/zero/positive numeric-domain coverage. Shared Cupertino implementation, not physical accessibility-service certification. |
| **NAV-017 /[#155](https://github.com/Apdelrahman1911/nativeCmpkit/issues/155)** | Both illustrative share taps only show truthful “No link was copied or shared” text. The six-method current source guard passes. Clipboard testing is **conditionally inapplicable** because no copy is implemented; real native sharing remains separate. |

NAV reports pass51 Linux/37 Android-host/51 macOS/39 iOS; these178 target
executions reuse51 source methods. Both desktop hosts also pass12 real Compose
slider interaction methods and8 numeric methods. The overall historical Apple
run **failed elsewhere**; only its passed NAV scope is accepted. Android host is
not a physical device or process-death test, and common native NAV tests are not
rendered UIKit navigation integration.

Earlier successful marker counters were not serialized by the legacy collector;
the Git-bound original collector enforces exactly one fresh marker and its
reports contain no scoped collection errors. No unavailable counter field or
console observation is invented. See the complete
[verbatim per-requirement review](evidence/closure-review-20261027-001/lead-original-acceptance-review.json).

Ledger: **84 implemented /68 partially verified /8 unresolved /4 verified**.
Every previous remaining note is retained verbatim in the acceptance record and
`previous_remaining_at_acceptance`. Minimum-platform, Android Bundle/process
death, native-stack/UI, consumer, ABI, legal/dependency and all other issue gates
remain independent release requirements, **not waived by these four closures**.

At this observation the four issues are accepted locally; GitHub closure still
requires a passing current staged preflight, a pushed immutable evidence commit,
additive technical comments and exact state/body/title/label readback. The four
previously closed issues (#41/#42/#146/#171) are historical, not new closures here.
Do not infer GitHub state from this offline ledger.

## Next bounded verification

- Fresh immutable `consumer-core-io`: require all seven named packaged methods,
  two XML, exact loaded/staged/resolved JARs and current **NativeCmpKit** root/
  target POM names. Old308 static checks predate the new display-name requirement.
- Fresh immutable `ios-ui`: execute all12 mandatory methods, preserve earlier
  failures, inspect real menu/replacement and owned resource teardown outcomes.
- New finite `navigation-geo` profile: only JS/Wasm navigation+geo methods,
  without repeating unrelated19-module suites or successful desktop/native work.
  Full `browser`/`all` coverage is unchanged. This is incomplete surface coverage,
  not a new support declaration. NAV-003/#91 and PERM-023/#156 stay open pending
  their immutable browser scope and separate recorded remaining requirements.
- IO-016/#148 remains open: existing MIME regressions do not verify packaged
  picker resources or its independent consumer scope.

The [fresh upstream refresh](upstream-refresh-20261027T110822Z/README.md) still
reconciles all16 open Calf issues uniquely; no missing imports or duplicate issues.
Always explicitly target `Apdelrahman1911/nativeCmpkit` in GitHub operations:
bare `gh repo view` selected upstream in a read-only observation despite `origin`.
Upstream was not modified. No routine verification approval is needed; Actions
remain enabled/all allowed, exact action refs optional, minimum read permissions.
Heavy local builds remain serial with an8GiB reserve. All publication gates stay.

## Source-held staged preflight019

The [independent preflight review](evidence/ci-preflight-20261027-019/lead-review.json)
recounts **23/23 commands and1,137 overlapping Python executions** from actual
logs, with **16,258 captured inputs** and the staged index unchanged. Both staged
and worktree whitespace checks, preserved history/bundles, audit/index/generator,
strict MkDocs and actionlint pass. The reviewer inspects17 real HTML anchors in
11 output files, including this checkpoint and ADR0008. Recorded root capacity
before/after exceeds8GiB; no heavy-build guard is lowered. Lossless input maps
and raw tooling logs are archived additively after the freeze.

This is zero Gradle/native/library/packaged-consumer execution and no dependency
trust, release or whole-library certification. Documentation linking this receipt
follows its captured inputs; a separate delivery guard checks those additions.
GitHub issue closure and new immutable CI still require actual remote readback.
