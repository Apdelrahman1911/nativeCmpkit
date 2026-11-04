# Related macOS Share ownership / cancellation batch604

**Prepared and compile-qualified; not native-verified or closure-ready.**
Owned worktree/branch: `development/batch-resource-lifecycle-20261104`, based on
`f566078507bbfc000244561ed925565913c3342b`. Lead integration, GitHub mutation,
CI dispatch/review and issue closure remain separate. No subagents were spawned
by604; no pushes, workflows, issues, release/package/deployment/Pages actions occurred.
The copied owner amendments in `AGENTS.md`/`containment.md` are deliberately excluded
from this patch. The serial heavy-build slot was released immediately after the
successful narrowly authorized compiler recovery; the 8 GiB **disk** reserve held.

## Root-cause assessment and scoped patch

The current production registry/retained Main operation design already replaces
the original raw-Arc/forgotten-delegate leak and five-minute blocking new JNI call.
**This review has not demonstrated another production defect.** What remains for
[#84](https://github.com/Apdelrahman1911/nativeCmpkit/issues/84)/
[#85](https://github.com/Apdelrahman1911/nativeCmpkit/issues/85) is genuine AppKit
lifetime, callback, cancellation, worker/concurrency and memory instrumentation
verification, not a one-line production change. The original requirements are
copied unchanged in [review604.json](review604.json); historical audit/resolution
files and previously accepted registry/JNI evidence are not rewritten or replayed.

Seven scoped source inputs: three existing paths, four additions. Cargo adds a
default-disabled test feature and one explicit harness-free target, without changing
original dependencies, package/JNI identity or release profiles. Production
`macos.rs` adds only a test+feature-guarded six-line helper inclusion; removing that
block reproduces every original byte. The helper includes actual native library
code on actual process Main, with eight finite cases and a separate 2,048-cycle
cancel stress selector. Real native owners, weak lifetime witnesses, independently
red dispatched-assertion detection and exclusive fresh per-reached-case XML are
used. Native objects are never made Send or dereferenced off Main.

Three Kotlin library-level tests invoke the **default** DesktopShareOwner -> actual
JNI -> AppKit path, using owned JFrame/single-worker coroutine fixtures and no
fake native operation, virtual scheduler, sample application, clipboard mutation
or recipient. Their exact finite classifier requires all three cases and leaves
macOS opt-out/headless/failure red. Original four-case focused fixtures remain
unchanged. Shared selectors/workflow/matrix were not edited by604; their exact
lead-owned integration route is described in
[the execution procedure](../../../../testing/macos-share-lifecycle.md).

## Verification: actual scope, failures and scoped recoveries

All local receipt input maps contain **1,340 selected source inputs**, held before
and after their respective invocation. The final Cargo and Kotlin compilers have
exactly the same current map, archived once as [compiler-inputs.json](compiler-inputs.json).
These are **compiler/source maps, not native runtime maps**.

| Original invocation | Outcome | Actual boundary |
|---|---|---|
| `important604` | NEW11/11, unittest0.003s, wrapper0.360798s | Source/classifier controls only, before later native dismissal/XML changes. |
| `important604-final-new3` | NEW3/3, unittest0.003s, wrapper0.383993s | Exact eighth dismissal, finite catalogue and fresh/red XML source controls. |
| First Cargo target-discovery review | Ungated helper target discovered | Actual offline metadata, zero compiler/runtime. Root helper could have become an unrelated default integration target. |
| `important604-final-targets-affected5` | 1NEW+4owning affected,5/5, unittest0.057s, wrapper0.435743s | Helper moved under a subdirectory; actual Cargo metadata now permits only the one explicit feature-gated target. Remaining accepted methods not replayed. |
| `cargo604` | FAILED, exit101 | Two test-only Apple compiler diagnostics: missing MainThreadOnly import and missing native delegate MainThreadMarker. |
| `cargo604-failed-only` | Passed, exit0/0.672040s | Only failed test compiler after correcting those two diagnostics; earlier source stage, no Apple link/runtime. |
| `cargo604-final-affected` | Passed, exit0/0.753977s; Cargo action0.41s | Final changed Apple-target harness compiler after dismissal/XML/formatting and gated target recovery. Linux host, aarch64 Apple target; zero Apple links/native/JNI/test executions. |
| `desktop604-dryrun` | Passed, exit0/21.713097s | Task discovery/JDK17 daemon; no Kotlin test compiler. Identified implicit native build/resource tasks before actual execution. |
| `desktop604-compile-only` | FAILED, exit1/11.221368s | Private capture-init map type inference failed before projects/compiler. No actual compiler or classpath capture. |
| `desktop604-compile-only-failed-init-recovery` | FAILED, exit1/13.198023s | Corrected map types; private init then attempted calf-share in included convention-plugins build. No root compiler or classpath capture. |
| `desktop604-compile-only-failed-included-build-recovery` | Passed, exit0/40.294633s | Private NativeCmpKit root guard; actual NEW desktop test compiler executes. Authorized native build/resource exclusions remain. Supporting production compilation is FROM-CACHE, not fresh verification. |

**Fifteen unique Python controls / nineteen invocations**, not nineteen independent
new methods or native executions. Ten unchanged original control bodies are reused;
the exact pre-addition/path original control projection matches its accepted source
hash. A first projection whitespace/hash refusal is retained rather than suppressed.
Twelve additional passive source/original-result checks pass without test replay.

The final daemon is actually JDK17.0.20, Ubuntu, Gradle9.7.1, with launcher/daemon
home agreement. Actual test compiler libraries are captured immediately before and
after the task: **43 identical entries;42 exist; one explicitly absent `desktopMain`
entry remains absent**, with owning Java task NO-SOURCE. No absent artifact is
manufactured as present. Both actual collections are archived; phase differences
explain their different raw JSON hashes. Sixteen new class files are emitted,
including the exact three compiled test methods; hashes are recorded in the review.
This is compilation, **not Kotlin test execution** or release/consumer certification.

Retained warnings: one original operation.rs `super::*` import from harness-free
`cfg(test)` compilation, and one original NativeLoaderBoundaryIntegrationTest.kt221
unused-expression warning. Neither unrelated source was changed to suppress them.
Supporting production JAR/embedded-notice tasks executed as compiler dependencies;
no packages were published and these are not consumer-integrated/native-verified
artifacts. No unrelated cache/process was removed or manually changed; normal
authorized Gradle/Cargo task cache writes retain their expected scope.

Original logs/results are archived in [results/](results/) with only known checkout
and private-evidence path prefixes normalized. [archive604.json](archive604.json)
records original and archived hashes/normalization. Original before/after maps and
all three frozen private init stages are retained separately in private604. The
initial init/reviewer/source-stage failures are historical failures, not converted
to successes by the later scoped recoveries.

## Missing original gates; next related batch

**ZERO actual macOS/AppKit/JNI/Kotlin native tests, Apple links, Instruments/leaks,
ASan, service/recipient integrations or stress executions were performed by604.**
Retained operation counters prove ownership, not a **visibly open** picker.
Controlled native terminal callbacks are not actual OS/user completion. Native
subject property readback is not Mail subject delivery. #150 remains independently
open for actual iOS Mail/service metadata and its other platform requirements.

Next: lead integrates/reviews exact bytes, adds the documented exact NEW3 desktop
focus and NEW8 Cargo route, then reserves one macOS host initially and executes
only these missing cases with real generated native resources and fresh XML/own-Git
runtime custody. A strict outer process deadline is mandatory: actual nested menu /
Main dispatch behavior is not proved by cooperative internal run-loop bounds.
Review the original result ONCE; recover only failed/unreached cases after qualifying
the cause. Do not replay accepted original suites, weaken a native precondition,
or label cross-check/source/NA as a native pass.

Even if finite batches pass, #84 still needs thousands of actual cycles with
Instruments/leaks and actual ASan/concurrent stress; #85 needs genuine visible-picker
cancellation and prolonged bounded-worker/lifetime validation. No closure is
recommended at this source-only checkpoint. All original API–ABI, compatibility,
consumer, native, dependency, legal/security, release-readiness, publication/main/
history and Pages gates remain. All Actions are allowed, no mandatory SHA pinning
is introduced, and required verification permissions remain read-only.
