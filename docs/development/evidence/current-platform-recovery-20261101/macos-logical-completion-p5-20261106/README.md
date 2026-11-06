# macOS native-build completion contract — P5, 2026-11-06

## Implemented scope

Five existing `scripts/ci/` sources were adopted once on the isolated macOS
development branch: `picker_awt_generation.py`, `picker_awt_preparation.py`,
`test_picker_awt_generation.py`, `test_picker_awt_prepare_contract.py`, and
`test_picker_awt_prepare_failure_diagnostics.py`. All 20 forward/inverse spans
match exactly. Original modes, inodes and atimes were preserved; the other 33
finite source inputs remained unchanged. ROOT's `d968257f` cohort is untouched.

The previous preparation checker treated any rendered task ending in `Test` as
a test execution, including ordinary Compose resource-generation tasks. It also
used a unique rendered native-task heading as its build-completion condition.
P5 admits only the 16 exact resource tasks supplied by the existing source-set
and Gradle convention definitions. Near-neighbor names remain refused.

`_prepare_native_completion` instead requires exactly one clean, strict five-key
native-build result from the existing native artifacts CLI. Duplicate keys,
duplicate/malformed results, wrong owners/platforms and dirty results refuse.
Both controllers call `require_prepare_native_identity` immediately after the
existing native-bundle validator, binding the result's binary/source/platform
before classpath, inventory or JUnit phases. Original commands, runtime/native
assertions, deadline/cleanup guards and five-JSON upload allowlist are unchanged.
This is a preparation-contract repair, not proof of an actual native test.

## Focused verification and preserved failures

* FIRST8 remains **FAILED**: six complete passing source methods and two errored
  methods, represented by eight unittest error entries. Worktree38/proposal5
  identities and all model source bytes held. Two model test-file atimes changed;
  full10 model custody was only36/38 and that original runtime remains retained.
* The carrier incorrectly resolved dirfd-relative mutation names against the
  model cwd. Cleanup failures are directly captured; the matching pre-PREPARE
  mkdir refusal is established by source flow, not an available primary receipt.
  A prebound `tokenize` opener also bypassed the noatime wrapper, a plausible read
  mechanism rather than an exhaustive event-level explanation of atime drift.
* The corrected carrier resolves the event-specific directory descriptor,
  preserves descriptor-relative opens, and fixes that tokenizer alias. Project
  sources and assertions were unchanged. **Only the two failed methods ran**:
  2/2, zero failures/errors/skips, suite0.125170s, total0.495719s, child0, complete
  845-byte capture. Worktree38/proposal5/model38 full10 identities held and the
  new owned process group/runtime are absent. Q300/source270/cleanup30 and the
  1MiB capture limit were not increased.
* Astra/max independently reviewed both source transformations and saved results.
  The six prior passes are narrowly reused as unchanged source-method results;
  they were not replayed and FIRST8 is not relabeled successful.
* An earlier pre-execution report-hash refusal is preserved: the supplied hash
  identified `SEAL.json`, not `REVIEW.json`. The corrected preparation copy binds
  the review's actual hash. That refused attempt created no candidate or tests.

`SHA256SUMS` authenticates the original artifacts copied here. This evidence
contains source-control logs only, not private native output or native binaries.
Model copies removed after successful custody are reproducible from the pinned
source/proposal maps; original failed runtime evidence was not normalized.

## Separate tooling-producer failure

ROOT's new run [42253956931](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42253956931)
at `d968257ff8dd3340f6b4cda2f1b890044679635f` ended `startup_failure` with zero jobs,
zero check runs and zero artifacts. GitHub's run-page annotation reports an
unexpected internal error (request ID `3484d958-da00-11f1-8e18-7eb19d281fff`).
The public status API reports Actions operational; that does not invalidate the
individual failure or establish its underlying cause. There is no test result,
reuse certificate or demonstrated source defect. No unchanged retry occurred.
The original HTML is retained locally; only bounded structured diagnostics and
API originals are archived here, avoiding unrelated page payloads.

## Next verification and holds

After the changed macOS source commit is pushed, use the already registered
`build-native-libs.yml` workflow with `profile=picker-awt-preparation` once.
The standalone preparation workflow remains unregistered. Review original
terminal evidence before any native-generation request; never replay accepted
JNI populations or retry an unchanged failed target. This checkpoint establishes
zero new compiler/native/consumer/API-ABI acceptance and no issue closure.
[#58](https://github.com/Apdelrahman1911/nativeCmpkit/issues/58) remains open.

Actions/all and no mandatory SHA pinning remain owner-authorized. Use minimum
verification permissions and at most two combined hosted reservations including
queued/reserved. Preserve main/history/attribution, protected Windows evidence,
native/consumer/dependency/legal/security/readiness and all publication gates.
No packages, releases, deployments or Pages are authorized by this source result.
