# Contained follow-up: CI documentation and native license material

This is an independent **read-only review**, not another build/test invocation or
release decision. Only new files in this review directory were written. No shared
documentation, production source, lock, live notice directory, GitHub issue,
workflow/control, commit or package was changed.

## Results

1. [CI documentation reconciliation](ci-documentation-review/README.md) confirms
   three stale present-tense helper-nonexecution claims. Actual local IO/NAV
   helper runs passed; two actual JS helper runs failed. All **69 archived XML
   reports** were independently reconciled to their receipts. A small
   [unapplied addendum patch](ci-documentation-review/proposed-addenda.patch)
   updates the living documents without retroactively turning earlier failures
   into passes or claiming hosted CI success.
2. [Native licensing reassessment](native-license-reassessment/README.md) found
   **no complete license text at the five pinned objc2 commits within the
   inspected scope**. Complete recursive trees contain only the already archived
   `LICENSE.md` policy as a genuine conventionally named license document.
   Rechecking all 15 exact crates against both unchanged locks and scanning all
   **1,130 packaged regular files / 14,997,918 bytes** found no standard complete-
   terms markers. This strengthens the material-gap evidence but is not a legal
   opinion or proof that no differently worded licensing statement exists.
3. Referenced upstream issue #23 remains open. It concerns relicensing and removal
   of MIT copyright notices, **not a resolution of the separate Apple-SDK
   derived-work uncertainty**. Four exact packages still declare MIT only;
   eleven declare Zlib/Apache-2.0/MIT alternatives. The previous JNI macro's
   exact-commit supplemental full texts remain a separate available material item.

All first archive/collector failures and earlier execution receipts remain
untouched. No license template was substituted, no notice adapter installed,
and no publication/consumer/legal gate cleared. Current device work was not
modified or evaluated from an incomplete running log.

`SHA256SUMS` identifies the new evidence bytes. It is an integrity inventory, not
an author-signature, build attestation or legal-clearance certificate.
