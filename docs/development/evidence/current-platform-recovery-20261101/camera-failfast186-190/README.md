# Camera scalar custody/fail-fast — actual186, integration189, plan190

**30/30 new synthetic source controls pass once; ZERO new native/compiler/browser outcomes. #13 stays open.**

The previous [camera41344349446](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41344349446) remains failed: scalar admission and original-state cleanup were separate failures, with zero native methods. This patch does **not** identify or silently fix that unknown scalar cause.

## Exact owning changes

- The sole `android-camera-restoration-dont-keep` profile now captures genuine read-only original state **before costly reporter APK assembly**; other profiles keep their existing order.
- Postcompile completion is one-shot and separately bounded; it revalidates original identity, runtime, ownership, state and compiled reporter rather than recapturing or retrying.
- Scalar-shape failures may publish only a closed set of allowlisted query identities plus bounded byte counts/hashes/shape facts. Original result/regex refusals still run first. Optional reporting cannot replace the primary error, authorize unknown state or erase a failed original-state cleanup.
- A terminal120s timeout marks an incomplete phase failed; a later master failure cannot erase a genuinely completed phase. Generic source discovery needs no private environment and owns its fresh0700 temporary custody/cleanup.
- Historical mutation readers use exact full-source inverses, preserving all original readers/actions/cleanup checks. No production Kotlin/API/dependency/native assertion/workflow change.

[Integration189](integration.json) applies exactly30 ordered singleton fragments to eight existing paths and five absent-only additions. Forty-two metadata scalar corrections repaired duplicated stage-hash fields; all candidate/control/driver/inverse bytes remained unchanged. Both prior source refusals remain refusals. Shared workflow/library references were **not overlaid**.

## Verification and reuse

[Original186](verification.json) executes exactly12 scalar and18 fail-fast controls against the independently qualified private candidate: failures/errors/skips/drift0, exit0. Times: unittest1.694s, driver1.820064234s, wrapper1.969752049s. The independent original-result review accepted exactly these30; live integration then matched all [47 accepted source/driver hashes](source-bindings.json), **without replay**.

A separate passive305-source compatibility inspection found no stale external file/definition pin, IO/permission ordering break, KVM pin break or new mandatory private environment; this is not full CI execution. [Plan190](source-plan.json) accepts only one still-unverified actual API35 C1. Accepted camera009's three scenarios are excluded; unchanged compiler/native populations are not replayed locally.

Library/canonical maps advance1179/1257→1184/1262 solely at the13 owning source paths. Share188 was already dispatched at its original6c8684a3 SHA before integration. Next freeze/push on development only, then finite camera C1 within **max2 combined hosted-heavy reservations including queued**. Local heavy work remains serial with8GiB disk reserve. Private proposals/raw transcripts are withheld; only qualified code and sanitized evidence are published.

No original #13 criterion, issue disposition, API-ABI/consumer/platform/security/readiness/publishing/Pages/main/history restriction is weakened.
