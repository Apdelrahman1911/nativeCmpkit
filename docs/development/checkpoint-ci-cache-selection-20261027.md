# NativeCmpKit — cache selection, ninth closure and setup-failure preservation

## Current closure and containment state

Single-agent work continues on `development/preview-hardening`; main remains
`94d2492e99d5cbc060409d94d9f88febd06222d5`. Actions are enabled/all allowed, no
mandatory SHA pinning, verification permissions read-only. Packages, releases,
deployments and Pages remain gated; no publication occurred in this continuation.

**Nine existing issues have verified closures:** #15/#16/#41/#42/#123/#136/#146/
#155/#171. The new [UI-009/#123 closure receipt](evidence/issue-closure123-20261027/apply/receipt.json)
records one additive comment and one state-only PATCH at14:44:44 UTC, after the
original constructor/Saver acceptance, pushed evidence and held preflight021.
Exact issue/comment readbacks preserve technical body, title and labels. This
is the original range/Saver scope, not rendering/device/locale/ABI clearance.
The original 164-finding ledger stays **84 implemented /67 partially verified /
8 unresolved /5 verified**; migration/Pages closures are outside that ledger.

## Four-runtime cache failure — no library execution

[Navigation/geo40522532291](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40522532291)
at immutable `202059090bbbf896d07d38a3441cf21c8888c63b` is a **completed failure**.
[Independent Git/ZIP/log review](evidence/github-actions/40522532291/lead-independent-review.json)
checks all four artifact digests, source-bound dependency inputs and actual
Linux/Darwin identities. Desktop JVM, JS, Wasm and iPhone all stop at the cache
step with the same confirmed cause: `matrix.test-modules` is raw CSV inside the
key, and **Actions cache rejects commas**. Plan and Gradle/library steps are
skipped: **zero library methods and zero XML**, not four failed test suites.
The same owning defect affects other multi-module profiles (`windows-cache`,
browser-only navigation/geo); no new duplicate audit issue is created. It belongs
to the ongoing BUILD-006/#3 verification work, not an invented baseline finding.

## Owning selection contract and regression evidence

The helper now validates an exact, bounded set of configured canonical module
paths, rejecting duplicates, empty elements, unknown/excluded aliases, controls
and shell-shaped input. The full selector maps to `all`. A nonempty selector is
sorted and SHA-256-bound to versioned JSON, yielding `subset-<64hex>`. Removing
punctuation without hashing would silently risk merging different module sets.
Equal permutations safely share selection identity; distinct identities and
cardinalities stay distinct. These are dependency cache partitions, **not cached
test results**. The previous64hex dependency stdout remains compatible; receipt
fields add the canonical module list and safe selection token.

The workflow checks the helper's64hex digest and `all|subset-64hex` token before
writing outputs. OS/architecture/slot/suite/runtime/dependency binding, exact keys,
no prefix restores, no candidate/test-output cache and read-only permissions
remain. Only the focused four-runtime profile changes to one-way execution, so
it may coexist with one unchanged UIKit diagnostic within two combined library
jobs; complete profiles remain two-way and no target or test is dropped.

[Preserved red and corrected fixture evidence](evidence/cache-selection-20261027/README.md):
**15 focused methods +39 existing dependency/workflow/profile methods pass**,
with four source inputs held. These are synthetic/source Python checks, not
Actions cache or library/runtime verification, and overlap complete preflight.
The inherited `green.*` filenames actually exit1 (one failure/five errors).
Their source bytes are retained: synthetic modules lacked required regular build
files, and the key fixture incorrectly used `runs-on` labels instead of actual
`runner.os`. Correcting those fixtures does **not** weaken module/key validators.
A new immutable four-runtime run is required before claiming the cache repair
works in Actions or closing NAV-003/#91 or PERM-023/#156.

## Separate UIKit setup failure and unchanged-job retry

[UIKit40522929974 attempt1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40522929974/attempts/1)
at the same `202059` SHA also completes **failure before tests**.
[Independent review](evidence/github-actions/40522929974/attempt-1/lead-independent-review.json)
verifies its sole selection artifact. The console reports simulator data migration
failure, then `git status --porcelain --untracked-files=normal` exceeds the existing
60-second subprocess deadline. Cache/plan/Gradle/native steps are skipped; **zero
library methods/XML and no UIImage-GC execution**. The underlying migration/Git
stall cause is unknown; neither source corruption nor memory safety is inferred.

[One failed-job-only retry](evidence/uikit-rerun-20205909-20261027/receipt.json)
requests attempt2 at the **same immutable source SHA**; successful tooling is
reused. No timeout/clean-check/GC/native-ownership requirement was relaxed. Its
acceptance/readback is **not** a runtime pass. Inspect that attempt's finished
transport,63 image phase markers, exact native PID/UUID/time-bound crash summary,
actual XML and owned cleanup before choosing a repair. Do not repeat these
unchanged UIKit diagnostic inputs merely because cache-selection tooling changes.

The [two original dispatch receipts](evidence/ci-dispatch-20205909-20261027/receipt.json)
prove two targeted requests and bounded admission, not their success. Both failed
attempt1 outcomes and raw ZIP bytes are retained; raw job transcripts remain out
of Git. Earlier consumer7/7 and UIKit120/121 partial results keep their own exact
source/time scopes in the [previous checkpoint](checkpoint-gc-diagnostics-navgeo-20261027.md).

## Next verification and release boundaries

Stage the final correction, regenerate status indexes using their owning command,
freeze every captured/staged input and run the full bounded preflight. Commit/push
additively, preserve main, then request repaired `navigation-geo-matrix` once at
the new SHA. All four original runtimes remain required; an earlier zero-test
cache failure cannot be substituted for execution. Keep #91/#156/#140/#141 open
until their complete original acceptance requirements actually pass.

Still separate: complete UIKit/GC/native lifetime, IO-023 genuine parent leases,
Android hardlink fixture provisioning without root/SELinux relaxation,15 objc2
license-text gaps/SDK ambiguity, ordinary dependency locks/trust/cleanup, full
21-root/native/minimum-platform consumers, API/ABI, physical-device/native/security
checks and [release readiness](release-readiness.md). No cache/helper/document pass
waives them or authorizes a preview, package, release, deployment or Pages.

## Held repair preflight — tooling only

[Full held preflight022](evidence/ci-preflight-20261027-022/lead-review.json)
passes **23/23 commands and1,222 overlapping Python tooling executions** at
17,063 unchanged source/stage inputs. This includes the397 current CI methods,
not1,222 library methods. Strict MkDocs/actionlint, inventory/history/index/icon
generation and both whitespace checks pass;26 anchors across13 actual HTML
outputs are inspected. Root capacity stays above8GiB; heavy-build guards remain.
Zero Actions cache/Gradle/library/native/packaged consumer methods are executed
by this preflight. Its archive and these additive links follow the source freeze;
a separate post-freeze readback checks them, not circular certification of the
next commit, the running UIKit attempt2, dependency trust or release readiness.
