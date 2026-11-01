# Permission helper installer-reply owning repair — 2026-11-01

## Scope and retained failure

[Actual 41262978370](../native-ci002/compatibility/PUBLIC_REVIEW.md) at
`2cb7dc275e8eaa15ef3545f3345afc439b44563e` remains **FAILED**: API33 helper
preparation refused after matching installed bytes; API34 child exit2 had no
controller artifact and the outer adapter raised `FileNotFoundError`. Actual
installer streams and the precise API33 failed callsite were not captured.
**Both original causes remain unknown.** This patch is not retrospective proof.

The static incompatibility is narrower: the permission helper accepted only the
one-line `Success`, while the storage helper already admitted the exact official
`Performing Streamed Install` followed by `Success` reply. Only
`scripts/ci/android_permission_demo.py` and its owning test file change.

## Owning changes

- Accept exactly the original one-line reply or the two-line streamed-install
  reply using the original byte `splitlines()` behavior. No stripping stdout,
  extra/duplicate lines, unknown prefixes, or “Success anywhere” acceptance.
- Still require integer exit0, the original trimmed-empty stderr criterion,
  actual installed-byte equality, unchanged frozen source/APK, compiled policy,
  private certificate, exact API33/34/35 signer range, and no automatic grants.
- Add bounded byte counts/SHA-256/fixed reply shape and fixed prepare-phase
  diagnostics before readback. No raw installer output, error bodies, paths,
  environment, certificates or keys are added to receipts.
- Source contracts, native Kotlin/manifests, assembly/installer argv, SDK/signer
  policy, prepared-receipt validator and owned cleanup remain unchanged. Cleanup
  success cannot turn a failed preparation into a passed one.

## Only new focused models

| Private execution | Result |
| --- | --- |
| One new prepare method against original helper | Expected source red: 1 error at original strict installer predicate; 0.006s unittest / 0.204s process |
| Eight new owning parser/prepare methods against postimages | 8/8 pass, no skips; 0.073s unittest / 0.360s process |

All SDK/build/signer/device operations are mocked; identity bytes are text,
not a compiled APK. The red method is also one of the eight green methods, not
additional coverage. Refusal models retain 16 unknown/extra/duplicate stdout
shapes, nonzero exit, stderr, source/policy/byte/certificate/signer failures and
failed-prepare/owned-cleanup separation. The original 1501 CI models are reused,
**not replayed**. See `MODELS.json`, sanitized logs, `SOURCE_REVIEW.json`, and
`SOURCE_HASHES.json`; `repair.patch` is bound to the recorded preimages.

All 24 original JSON artifacts, 1162 frozen source files, and 36 sealed original
review-delivery files remain hash-identical. Four uploaded maps remain
1068-library maps; the independently derived 1145-combined map is source-only,
not uploaded actual combined evidence.

**ZERO new builds, installs, native tests, XML or acceptance.** #102/#118 stay
open. API34 scope remains a platform-selected public Limited observation, not
library-selected request/read proof. No release, publishing, security, minimum,
consumer, ABI or readiness gate changes. The lead must recheck live preimages
and new evidence-path absences before integration; neither was assumed here.
