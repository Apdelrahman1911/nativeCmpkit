# Windows JavaFX candidate: cache observation wiring and receipt recovery

**2026-11-02, solo. No new native/library/compiler execution or issue closure.**

[Actual41416593900](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41416593900)
at `80af3ff8795633ecdb2f691b8bdef743b6b3beef` fails at the cache validation step.
The actual Windows SDK23, current status-index check/source plan, JDK17 runtime,
configured dependency identity and exact dependency-cache restore **pass**. This
is the first hosted confirmation of the earlier Windows index-path correction.
The candidate builder, Gradle and original public Stop method are **unreached**.
Original logs/artifact were acquired once; their checksums are in
[ACQUISITION291](ACQUISITION291.json). No archive is downloaded again.

## Confirmed owning cause and repair

`.github/workflows/javafx-library-candidate.yml`, originally lines89/95, wrote
and loaded `build/ci-runtime/javafx-candidate-dependencies.json`. The unchanged
`scripts/ci/library_dependency_cache.py::main` reads the fixed path
`build/ci-runtime/library-dependencies.json`. The producer and cache-key selection
were correct, but their observation could not reach the consumer. The safe failure
receipt `library-cache-restore.json` was also omitted from the artifact patterns.
The actual original exception type was not uploaded and remains **unobserved**;
the exact current source plus the real isolated CLI reproduction confirms the
filename mismatch, not corrupt cached dependency bytes.

The workflow now writes/loads the validator's existing fixed path and uploads
both `library-dependencies.json` and `library-cache-restore.json`, including on
failure. These are exactly two filename-reference changes and two upload entries.
No cache validator, checksum, recipe, cache home/key, selection, permission or
native assertion changes. No deletion/repair, prefix restore, cache save,
continue-on-error, default dependency adoption or binary upload is introduced.

## Regression and source/results review

- [292](RECEIPT292.json) is an **invalid synthetic fixture red**: its regex also
  counted the runtime observation output. That original failure is retained and
  is not evidence for the filename root cause.
- [293](RECEIPT293.json) corrects only the unaccepted fixture selector. One real
  producer/cache-CLI regression then fails on the held preimage at
  `exact-dependency-observation/FileNotFoundError`, as expected.
- [294](RECEIPT294.json): failed1+NEW3 **4/4 pass**, unittest **0.147s**, wrapper
  **0.316436754s**, actionlint **0**. The real isolated producer-to-cache roundtrip
  succeeds; wrong selection still refuses without editing data; upload patterns
  retain both observations; strict read-only/single-case/no-save order holds.
  All **1,204** canonical library inputs match before/after. These controlled
  synthetic build/checkout/home CLIs are not hosted Gradle/native tests.
- [295](REFUSAL295.json) retains the reviewer's historical README hash mismatch.
  The README had already changed in the committed7445615b documentation. It is
  not an implementation defect or permission to blanket-repin executable source.
- [296](REVIEW296.json) accepts **24 passive checks**. All13 unaffected historical
  executable/legal/pin candidate bindings hold. The explanatory README is bound
  separately to committed80af3ff8, and the workflow has the exact owning delta.
  Accepted27 candidate controls and dependency-native4 populations are reused,
  **not replayed**. Native/public Stop acceptance remains pending.

## Next and limits

Freeze/push on `development/preview-hardening`, then dispatch only the original
failed public Windows Stop method. The workflow does not auto-run for this
workflow/test/documentation-only correction; do not duplicate dispatch. The
original10s/six predicates, pre-cleanup peer EOF, same-owner recovery and native
cleanup remain unchanged. A passing candidate method alone cannot close #64:
other original platform/offline-browser and ordinary dependency adoption remain.
BUILD-006/#3 also retains its full native/consumer/compatibility criteria.

Last verified state remains **97closed/75open/172total**, ledger22implemented/
42partially-verified/95verified/five unresolved. Continue solo, serial local heavy
work with8GiB reserve, at most2 combined hosted-heavy reservations INCLUDING
queued jobs. Every publishing/Pages/main/history/native/consumer/API-ABI/
corresponding-source/legal/security/readiness gate remains; no packages/releases/
deployments or default dependency changes.
