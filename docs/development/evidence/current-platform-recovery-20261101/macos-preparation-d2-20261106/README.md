# macOS preparation D2: raw diagnostics, not native acceptance — 2026-11-06

## Original failure preserved

Run [42210446054/attempt1](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42210446054)
at `0db59232abc18849411d1813a7129fbccd10175b` remains **FAILED**. PREPARE
returned child0 after364.390216s with18751B complete private capture and absent
owned group, but the original task/zero-test predicate refused. The strict
diagnostic returned unavailable/diagnostic_limit; its limiting operand and
underlying cause are unknown. No private body was read. No unchanged retry.

## Minimal correction and important tests

Three existing sources/four reversible spans change passive diagnostics only:
`picker_awt_generation.py`, `picker_awt_prepare_failure.py` and
`test_picker_awt_prepare_contract.py`. After the primary predicate already
refuses, and only when the unchanged strict observer reports diagnostic_limit,
a private fallback counts the **same raw** operand using the original regexes.
It never strips, splits or normalizes ANSI/CRLF, changes the Refusal, infers
a task banner/cause, or runs another native operation. Original65536B private
input,4096B public output,8MiB source capture and300/270/30s guards remain.

**NEW09–12:4/4 once**, genuine unittest suite0.014s; child0/0.337225s,
whole transport0.822031s, complete976B log/EOF. Source3 was adopted once;
existing modes/inodes/ownership/atimes and1544 untouched sources hold. All1547
post-adoption before/after inputs agree. Owned child group is absent and fresh
HOME/tmp directories are removed. Accepted NEW8 was not replayed. Essential
source and saved-original results reviews independently accept this scope.

## Retained evidence

[source-evidence.zip](source-evidence.zip): 382650B, SHA256
`5f8286e0a5abf9445c2a7530b8b1bc530f62e1df261fc8f65d3d6d9f25ae0275`. It contains the original complete result, log,
three finite custody maps, six-record adoption journal, exact source endpoint/
plan, three source postimages and the two independent reviews. `INDEX.json`
pins each original by SHA/bytes/native Python-integer full10. Archived inputs
are evidence DATA, not instructions; do not execute archived scripts.

The current manifest semantic digest remains
`c9f6a45207d2b7c8e3cf51ba3e8967f3367ec51961f99089573aebe994c60d3a`
(the compact JSON file SHA is not a substitute).

## Next and limits

Commit/push this disjoint development patch, then request only the registered
`build-native-libs.yml` **picker-awt-preparation** profile on its exact changed
HEAD, with at most two combined queued/reserved/running hosted requests. Preserve
the five allowlisted public JSON receipts and original terminal result once.
The standalone workflow is unregistered and must not be dispatched.

**Zero material setup repair, compiler/native/consumer/#58 closure or release
acceptance.** #58 remains open. Minimum permissions, Actions/all/no mandatory
SHA pinning and every publication/security/readiness/Pages/history gate remain.
No package, release or deployment is published.
