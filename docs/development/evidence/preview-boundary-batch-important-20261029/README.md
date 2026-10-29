# Related preview-boundary batch — 2026-10-29

**NATIVE-035/#151 is closed/completed** immediately after shared important tests
and original-criteria review. **BUILD-008/#41 was already closed** on
2026-10-24; it received a verification comment only, **no state mutation**.
Original issue bodies, titles, labels, comments and #41's original `closed_at`
remain preserved. [Both acceptance reviews](closure/NATIVE-035-acceptance.json),
[version-policy acceptance](closure/BUILD-008-acceptance.json),
[new closure readback](closure/NATIVE-035-verified-readback.json) and
[already-closed readback](closure/BUILD-008-verified-readback.json) document each
original criterion. Prior remaining requirements are archived separately.

## Shared actual tests

- Four actual owning convention JUnit methods pass in one fresh
  [sanitized XML](gradle001/TEST-PublicationVersionPolicyTest.xml): eight accepted
  stable/snapshot/preview examples, 24 unsafe and 11 malformed examples, plus a
  diagnostic sentinel. Root configuration uses that same compiled validator;
  the pre-existing version grammar is unchanged.
- [Actual Gradle model](gradle001/preview-boundary-model.json) verifies exactly
  **21 independent publisher projects / 145 configured publications**, mapped
  Maven identities and all publisher Kotlin source directories. These are
  **configured publications, not built or published artifacts**. Maps is included
  but API-empty/unpublished; media and scheduling are excluded. Notification
  permissions are not scheduling. Experimental source-directory reuse is rejected.
- Combined [Gradle execution](gradle001/execution.json): **exit0 / 63.02s**, actual
  JDK17/Gradle9.7.1, 841 held inputs. This positive run preceded the source commit
  in a dirty worktree. [Exact source binding](immutable-source-binding.json)
  subsequently proves every executed input identical to pushed `64e6c2ed`;
  successful tests were **not replayed or called a fresh immutable execution**.
- [Four Python source/policy methods](python001-review.json) pass, including
  explicit original maps#27/media#245 links, deferred-feature gates and inert
  manual/read-only verification workflows.
- A separate **clean immutable** [actual root rejection](root-negative002/review.json)
  supplies command-substitution-shaped input as a safe subprocess argument.
  Expected **Gradle exit1 / 15s** rejects it before a root task executes. This is
  a passing rejection test, not a build success.

Old shell stamp/update helpers are **retired inert archives**, not active
production helpers. They were not executed; no synthetic manifest rewrite is
falsely certified. Any future helper requires its own implementation/tests and
the independent release gate. Maps/media/scheduling are **not implemented
features**; upstream feature issues remain untouched/open.

## Readback, scope and retained failures

[Fresh remote observation](remote-after-review/review.json): **65closed /107open /
172total**. Only #151 is newly closed in this batch. Ledger: **45implemented /
49partially-verified /63verified /7unresolved**. Main remains `94d2492e`.

The initial helper stopped **before any POST/PATCH** because it assumed #41 was
open. [The operation note](archive-tooling-note.json) preserves that failure and
the reconciliation; no reopening/reclosing or uncertain mutation replay occurred.

[Lead review](lead-batch-review.json) is a scoped acceptance review, **not**
whole-platform/native/ABI/packaged-consumer/dependency/provenance/legal/security/
release certification. No packages, releases, staging, deployment or Pages.
The [finite archive manifest](archive-manifest.json) records 37 selected public
JSON/XML/issue records; XML console/stack bodies are excluded with original
hashes. No private logs, credentials, ZIPs, source archives or binaries are stored.
