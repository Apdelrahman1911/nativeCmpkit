# Consumer606 followup — missed native notice-fixture caller recovered

**2026-11-04; parent patch `4d180ab88d8870af13f6aa701b22499b401d233a`.**
The lead's independent610 review found that
`tests/consumer/test_native_license_supplements.py:147` still constructed a
native-owner desktop verifier without the now-required independent revision.
Its fixture identity includes `nativecmpkit-file-picker`, so construction failed
**before** any notice checks. This was a confirmed affected synthetic caller,
not missing legal material, a native failure or a reason to weaken the verifier.

## Minimal recovery and original behavior

The fixture now declares `NATIVE_FIXTURE_REVISION = "c" * 40` separately from its
dependency VCS revision and supplies it to `notice_checks` as
`expected_native_revision`. This is an explicit **synthetic** native producer
identity: the notice-only fixture does not build a Git/native producer or native
provenance manifest. It must not mislabel the unrelated dependency's VCS revision
as native provenance.

Default clean-producer requirements remain unchanged. No dirty diagnostic flag,
constructor bypass, reduced owner/module selection, waived notice assertion or
production change was introduced. All **50 original supplement test bodies**,
fixture setup and every collector/notice gate remain unchanged; only the owning
helper's keyword and a separate fixture constant were added.

## Complete current caller audit

`caller-inventory606.json` records all **16** current executable Python
constructor sites in `tests/` and `scripts/`, with their enclosing declarations,
argument expressions and source hashes. Tracked references and current CLI
examples were also reviewed; documentation/evidence snapshots are historical,
not active callers and were not rewritten.

| Population | Count | Result |
|---|---:|---|
| Native-capable CLI and native fixture sites | 4 | CLI `main`, provenance fixture and native-contract fixture already pass explicit revisions; the notice helper alone needed recovery. |
| Other synthetic sites | 10 | Explicit Core/UI/NAV/Cupertino or invalid-input contexts; no advertised native desktop owner requiring a new revision. |
| Actual partial controllers | 2 | Core/IO declares exactly Core+IO, WebView exactly WebView; neither includes picker/share, so their existing constructor calls need no native option. |

The new inventory regression rejects an unreviewed constructor or omitted
revision at any classified native site. It recognizes direct constructors,
terminal `ArtifactVerifier` attributes and imported constructor aliases; it is
not whole-program analysis of arbitrary dynamically generated Python.
Additional source controls preserve exact nonnative real-controller scopes and
the actual CLI's independent-revision/explicit-diagnostic argument wiring.
No further missing actual property wiring was found: the desktop runtime
artifact binding from the parent patch remains unchanged and still awaits
actual Gradle/JNI verification.

## Important affected tests — accepted once, no unchanged replay

Only **10 of 50** original supplement methods reach `notice_checks` (12 helper
invocations across the original methods); the other **40** are not affected by
this keyword and were **not run**. The exact population is recorded in
`important-green606.json` and independently guarded by the new source control.

| First execution | Result | Scope |
|---|---|---|
| `new-regression-red606.json/.txt` | **1 error / 1 method**, unittest **0.016 s**, wrapper **0.202686 s** | NEW missed-owner regression reproduces the original missing independent revision at construction. Retained as failed; not native/legal behavior. |
| `important-green606.json/.txt` | **15/15**, unittest **6.003 s**, wrapper **6.174845 s** | Affected original10 + NEW5 caller controls, including recovery of the failed NEW1. All nine bound owning/caller inputs held before/after. |
| `REVIEW-followup606.json` | Passive source/results/documentation review | Exact fixture change, original method/assertion preservation, current caller classification, accepted result/input custody and protected parent/production sources. No test execution. |

The wrapped constructor in the new notice regression is the **real verifier**;
the synthetic ZIP/collector/material/notice checks execute unchanged. Four new
controls examine source AST/wiring/population, not platform behavior. No
accepted parent23 controls, Kotlin compiler, real Core/IO/WebView consumer,
Cargo, native/JNI, Gradle, hosted workflow or network operation was replayed.

Private originals remain retained once with hashes in
`retained-originals606.json`. The red traceback's private worktree root is
relabeled `<worktree>` in committed text; its original receipt/log hashes are
preserved. Sanitized evidence is not presented as a new execution.

## Remaining gates and integration

This followup removes the missed synthetic fixture blocker; it does **not**
complete #2 / BUILD-003, #38 / BUILD-004 or #3 / BUILD-006. Use the unchanged
[parent evidence and missing-host plan](../native-package-provenance606/README.md)
for genuine native manifests/JAR assembly, actual intended-host JNI/resource
and dialog lifecycle, full21/minimum-platform/API–ABI and independent
producer/dependency/legal/security acceptance. No support floor or license
requirement was relaxed.

The lead integrates both local commits and owns review/dispatch/issue updates.
No policy/root worktree edit, push, GitHub mutation, issue closure, heavy build,
release, package, deployment or Pages publication occurred here. **No issue
closure is proposed from this followup alone.**
