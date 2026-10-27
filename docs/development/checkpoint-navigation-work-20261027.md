# NativeCmpKit: bounded navigation work and allocation verification

Single-agent contained development on `development/preview-hardening`; `main`
remains at `94d2492e99d5cbc060409d94d9f88febd06222d5`. Verification Actions are
enabled/all allowed with no mandatory SHA pinning and read-only permissions.
Packages, releases, deployments and Pages remain behind all readiness/security
gates. Original findings, history, attribution and failed evidence are preserved.

## Actual library work/allocation tests, not a timing promise

The [independent three-attempt review](evidence/navigation-array-work-20261027/lead-independent-review.json)
preserves two fixture compiler failures followed by **two actual passing JVM
methods in one fresh XML**, zero failures/errors/skips. The final copied actual
root run exits **0 after33.01s** with **726 source/copy inputs held**. The first
two attempts exit1 before runtime: nullable String-array mutation, then nullable
Int-array allocation-lambda result. The only repairs are explicit `requireNotNull`
at these two fixture boundaries; production/API/content assertions are unchanged.

`NavArrayParsingWorkTest` exercises the real library implementation:

- All five array parsers produce correct contents and read every input element
  exactly once at sizes0/1/16/256/4096. Input lists remain unchanged; mutating the
  returned String array does not mutate its source.
- Twelve finite Int-array trials use the actual JDK17 `ThreadMXBean` allocated-byte
  counter at128/512/2048/4096 elements. Bulk and legacy results both escape to
  content assertions. The management flag is restored in `finally`; unsupported
  counters fail, never a passing skip.
- At4096 elements this VM records **79,928 bulk bytes** per trial versus
  **33,699,416 /33,636,440 /33,636,440 legacy bytes**. These are observed thread
  allocations, not peak heap, a portable ratio or a general performance budget.
  Nanosecond observations are recorded but **never determine test success**.

The fixture sizes are **not a library external-input limit**. Legacy repeated
`parseValue(value, previous)` remains copying/quadratic for compatibility. Use
bulk `parseValues` for large inputs; no new deep-link/external-input parser was
adopted. This diagnostic is dirty-source JVM evidence, not immutable/Native/device/
consumer, sanitizer, leak or release certification.

## Original acceptance and efficient next CI

The unchanged codec/inference/name-resolution implementation and common tests
already passed JVM/JS/Wasm/iOS-simulator in
[run40528445496](evidence/github-actions/40528445496/lead-independent-review.json).
The new JVM-only probes require their own immutable desktop execution before
NAV-005/#93 can be closed. NAV-004/#92 stays independent: retaining/deprecating
its erased getter is not a claim that arbitrary legacy reads became type-safe.

The [finite navigation-only profile](evidence/navigation-desktop-profile-20261027/green.json)
adds `navigation-desktop`: one Linux JVM library suite, standard fresh-report/
input/runtime/cache guards, no geo/browser/Apple/consumer repetition. Two new
unknown-profile red errors are preserved;19 matrix/13 workflow-source/15 cache
Python checks and actionlint pass. **These47 overlapping tooling methods are not
hosted cache hits or library runtime results.** Complete profiles and every
supported verification slot remain intact.

Ledger: **68 implemented /81 partially verified /8 unresolved /7 verified**.
NAV-005 is promoted only to partial verification. Its previous remaining
observations are retained verbatim; all530 baseline requirements are unchanged.
[Eleven closed issues](evidence/navgeo-issue-closures-20261027/lead-final-readback.json)
are actual readback-confirmed closures, not eleven new fixes here.

At this checkpoint, the immutable **ios-ui**
[run40540209480](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40540209480)
at `ea79ab8cf30132b4b37985f175d00287382ddca8` is still running. Its725-input/
16-mandatory-method contract is unchanged by this JVM-only work. Do not
redispatch it or claim a pass before source/artifact/XML/application review.

IO-023 genuine native parent leases, Android hardlink feasibility, native-device/
assistive/profiling coverage,15 objc2/SDK legal-material gaps, dependency trust/
locks, full21-root/native/minimum-platform consumers and whole-library API/ABI
remain [release blockers](release-readiness.md). No publication gate is lifted.

## Additive immutable execution and original acceptance

[Run40549350671](evidence/github-actions/40549350671/lead-independent-review.json)
now passes54/54 actual desktop library methods in seven fresh XML at70114ff3,
including both new probes and all52 previous identities.726 own Git inputs held;
Gradle0/239.08s. All four original NAV-005 criteria are accepted using unchanged
four-runtime codecs plus this finite JVM work/allocation evidence. #93 closure
still requires pushed evidence/current checks/exact readback; NAV-004 remains
independent. See the [current checkpoint](checkpoint-navigation-verified-20261027.md).
No timing/Native/device/consumer/ABI/legal/dependency/release clearance is implied.
