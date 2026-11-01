# U1 original failure — public-safe derived review

Original `U1-f0db3fb734b3364e` remains **FAILED / STOP AND REVIEW**:
**Gradle 1 / 53.01 s**. The observer returned stop-and-review (exit 2,
reported by the lead). **U2/U3 were not launched.** No retry or U4 replay occurred.

The first actual failure was dependency determination for `:kotlinNodeJsSetup`:
`org.nodejs:node:24.16.0` had no cached version available in offline mode.
Included convention-plugin compilation/jar actions completed; this was not the
expected ordinary-upgrade gate denial.

## Missing original acceptance evidence

Only the original result receipt exists: graph hash null, no observed root
actions and no root-task states. **ZERO graph/gate-action/sentinel receipts**;
the original graph and action files were not reconstructed. The gate denial,
typed graph and U1 negative-case contract are **not accepted**. No strict
classifier was run; no U4 result fills the original U1 gaps.

Static held-KGP inspection localizes the first distribution-file resolution to
`AbstractSetupTask.kt:93–98`: optional Classpath `dist` → lazy download branch
→ `configuration.get().files.single()`. The setup provider mapping itself is
lazy. This pre-action planning access is outside a gate task's doFirst/action.
The original stacktrace was not retained, so no exact dynamic engine frame is
claimed. Source bindings are for the unchanged original frozen slice, not a
claim about later repository inputs.

## Exact intended Node prerequisite

For the held JDK's declared **Linux/x86_64** platform, unchanged KGP 2.4.20 and
the original version-only fixture pins statically derive:

- `org.nodejs:node:24.16.0:linux-x64@tar.gz`
- `https://nodejs.org/dist/v24.16.0/node-v24.16.0-linux-x64.tar.gz`

The actual log observed the module/version, **not** classifier, URL, server
response, release publication, archive bytes, checksum or authenticity. The
URL is source-derived; no request/download was made. KGP uses artifact-only Ivy
metadata, not a required upstream POM/Ivy XML.

Bounded current readbacks find the expected Node installation namespace, module
artifact namespace and inspected conventional coordinate descriptor directory
absent. These are scoped current observations, not global/historical filesystem
absence. Binary metadata indexes were not parsed. The six held runtime hashes
do not cover a Node archive; archive authentication and genuine repository-specific
offline resolver readiness remain **unverified**.

The minimal proposal is an owning **pre-launch Node distribution prerequisite**
beside the existing runtime admission: require a trusted exact-platform archive
and separately reviewed genuine offline resolver proof, or refuse narrowly
before launching Gradle. Filename/hash or installed executable alone is not
resolver-readiness evidence. Any normal trusted provisioning/verification needs
a separate lead-owned prerequisite decision. This proposal is **not applied or
retry authorization**.

Keep download=true/offline and the original source, helper, graph and assertions.
No download=false, ordering/doFirst/configuration-denial substitution, fabricated
cache/metadata, checksum/trust change or new U1 ID.

## Unchanged controls

A previously retained bounded readback found exact wrapper PID30066 and
correlated single-use daemon PID30161 absent; no signals were sent. It is **not**
full detached/composite descendant cleanup. Bounds, cleanup, OS network containment
and RSS remain **null**. #40/BUILD-007 stays open; ordinary adoption and all
dependency/security/legal/native/consumer/ABI/readiness/publishing gates remain.

This is an explicitly **derived public-safe metadata packet**, not an original
receipt or new execution. Private originals are retained separately. It contains
no raw requests/logs, private machine paths or runtime payloads. Lead-owned docs
integration and publishing permissions are unchanged.
