# Offline tooling activation — NativeCmpKit

This is the current integration guide. The preserved
[reuse preparation](offline-tooling-reuse.md) and
[provenance preparation](offline-tooling-provenance.md) describe their historical
source stages; their original wording and source pins are intentionally unchanged.
Source qualification is **not** successful hosted producer/reuse verification.
See the dated development evidence for actual executions and retained failures.

The [2026-11-04 integrated source checkpoint](../development/evidence/current-platform-recovery-20261101/ci668-produce-reuse689-694/README.md)
records the exact CI ingress, targeted controls and actual ROOT preflights. Hosted
producer/reuse and the missing native focus scopes still require actual results.

## What the workflow can reuse

The manual `gradle.yml` workflow supports explicit `off` (default), `produce`,
and `reuse` modes. Only the ten fixed, nonzero, fully successful offline tooling
discoveries are reusable, together, for the exact same frozen commit, complete
raw tracked input map, workflow/actions and observed hosted runtime.

Every dispatch still runs the five migration/audit/index checks and requested
profile preflight afresh. No compiler output, native test, XML, dependency-trust
decision, consumer result, security/legal/API–ABI or release gate is reused or
waived. A documentation-only commit also invalidates this conservative certificate.
Ancestor source views used by historical fixture controls are never signatures.

Actions remain owner-authorized with all actions allowed and **no mandatory SHA
pinning**. An unresolved action identity can refuse explicit reuse eligibility;
it does not prohibit ordinary `off` verification. Only the tooling job adds the
necessary `actions: read`; all other verification permissions remain read-only.

## One frozen producer, then explicit reuse

After source/results review, commit and push **development only**, then dispatch:

```sh
gh workflow run gradle.yml -R Apdelrahman1911/nativeCmpkit \
  --ref development/preview-hardening \
  -f profile=tooling -f offline_tooling_mode=produce
```

Verify the actual run HEAD, original attempt, successful sole `tooling` job,
each of the ten nonzero passing scopes and the sole signature receipt artifact.
There is no eligible producer before that execution; an older green badge or
platform artifact cannot be grandfathered. Record its exact positive run,
attempt, job and artifact IDs from the original metadata.

On the same immutable branch HEAD/runtime, provide those four reviewed IDs:

```sh
gh workflow run gradle.yml -R Apdelrahman1911/nativeCmpkit \
  --ref development/preview-hardening \
  -f profile=tooling -f offline_tooling_mode=reuse \
  -f producer_run_id="$PRODUCER_RUN_ID" \
  -f producer_attempt="$PRODUCER_ATTEMPT" \
  -f producer_job_id="$PRODUCER_JOB_ID" \
  -f producer_artifact_id="$PRODUCER_ARTIFACT_ID"
```

Review the authenticated once-only acquisition ledger, original digest-verified
ZIP, before/after raw signatures and decision: exactly ten reused offline scopes
and **zero** new offline scope executions. A reuser never exports a producer
certificate. No latest/search selection, automatic retry, unknown storage-origin
allowance, token forwarding or silent fallback to fresh tooling is permitted.
Preserve the first refusal and qualify any genuinely changed recovery separately.

After successful reuse verification, missing-only platform profiles can use the
same four IDs on that same HEAD. Do not make intervening documentation commits.
Observe at most two combined hosted-heavy reservations, including queued work;
a two-row profile reserves both even if its jobs run serially. Continue the next
disjoint patch on an isolated branch while these original runs execute.

This workflow does not publish packages, create releases, deploy or enable Pages.
Preview publication remains conditional on every applicable readiness gate.
