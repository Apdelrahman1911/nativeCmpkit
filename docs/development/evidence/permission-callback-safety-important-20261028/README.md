# Permission callback safety — important checks, 2026-10-28

## Repair and reproduced failure

An application callback exception completed the request gate but cancelled the
remembered composition scope, preventing later requests/status recovery. The
controller now owns a parent-linked `SupervisorJob`: parent cancellation still
propagates, application exceptions remain observable, and disposal cancels the
owned job even if native cleanup throws. Constructor/API identities are retained.

| Evidence | Immutable source | Actual methods | Gradle exit/time |
|---|---|---:|---|
| [Fixture compile failure](local/before/review-compile-failure.json) |6e1f3f40|0|1/42.57s|
| [Runtime reproduction](local/before-fixed-fixture/review.json) |52d1d036|1 failed|1/44.01s|
| [Owning controller verification](local/fixed-desktop/review.json) |d00bd568|11 passed|0/44.02s|

The accepted controller run contains three new callback-error/throwing-disposal/
parent-cancellation methods and eight directly affected existing methods, two
fresh XML, zero errors/skips/failures, actual JDK17 and784 own-Git inputs held.
These are real common controller/Job executions with controlled backend/test
scheduling, **not actual iOS, OS privacy UI or heap/ABI certification**. Eleven
successful methods are reused, not replayed. Test controllers now dispose their
owned jobs in `finally`; no assertions were weakened.

## Native gate passed and issue closed directly

[Run40685630966](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40685630966)
passes exactly2/2 at immutable82d96b87 for actual public iOS factory/
Compose/Foundation/Darwin callback-error/query-race/pending-disposal methods.
**#108/PERM-007 closed/completed at12:37:50UTC**, directly after reviewing all3
original criteria, native results/inputs/runtime/XML/digest, before final ledger
documentation. One fresh XML/0failure-error-skip, exit0/1149.17s,785 own-Git
inputs held. Together with desktop11:13 actual executions/13 authored methods/
three XML. **48 closed issues;53 implemented/59 partial/45 verified/seven unresolved.**
The initial artifact-review snapshot was in-progress; the later workflow completion
readback is success. Neither observation is silently substituted for the other.
GitHub rejected an initial SHA-only dispatch with422/zero workflow starts; the
subsequent frozen-branch dispatch was accepted and its actual run SHA matched.
No repeated uncertain POST and no failed evidence reclassified as successful.

[Focused tooling111/111](tooling-review.json) passed before the dispatch;
these are verifier methods, not native/library executions. Native helpers control
application-native interface completions, not Apple privacy dialogs. All broader
device, ABI, consumer, dependency/legal/security and release gates remain.
No packages, releases or deployments published. Documentation follows important
execution/review, and issue closure preceded this final ledger documentation.
