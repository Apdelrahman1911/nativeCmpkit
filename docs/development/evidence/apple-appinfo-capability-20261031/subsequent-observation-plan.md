# Separate subsequent exact-owned-app observation plan

**Not executable authorization. No appinfo bundle or registration query has been
performed, and the capability-only job cannot perform one.**

## Prerequisites

1. The lead accepts an actual immutable `ios-appinfo-capability` result from the
   selected `macos-26` Xcode/simctl identities. Unknown/nonzero/ambiguous help or a
   different usage stops for review. Do not interpret unavailable help as absent
   registration, or run a broad inventory fallback.
2. Review the actual supported interface and its documented/observed output
   serialization/schema before accepting any registration parser or semantic
   claim. This help collector does not supply an appinfo payload schema. Do not
   invent JSON/plist/OpenStep formats, fields, nesting, `--json`, bundle selectors,
   or success/missing-app semantics. Record unknown schema as unavailable.
3. Any later exact-app query needs separate explicit owner-approved scope: one
   current owned source/session bundle and one explicitly selected simulator,
   correlated to a successfully verified installed app container. The app from
   failed run 41242777493 was cleaned up; do not query its old removed bundle,
   guess a current bundle, or use a default/Booted/alternate simulator selector.
   A later disposable app must retain existing installation/identity ownership
   evidence; this plan does not authorize booting, installing, launching, or
   profiling a new app.

The capability collector assumes fixed, trusted source/tool filesystem inputs.
Its regular-file/size preflight and before/after identity checks are not
adversarial replacement-FIFO or growth/time-bounded-read certification. No
cleanup, detached-process or security gate is waived by these offline controls.

## Minimal separately reviewed query

Only after the preceding interface/schema and ownership decisions, permit **one
bounded read-only exact-bundle appinfo query** using the accepted running SDK's
exact syntax. Bind it to the already-selected simulator UUID and exact current
source/session bundle, after existing successful install identity and before the
already-authorized genuine launch. Do not add a new launch/install/profile,
repeat the prior owned log query, or read other apps' records.

Keep raw payload private and bounded. The actual schema must be reviewed before
semantic registration facts are accepted; capability-help recognition alone is
insufficient. Retain only approved fixed facts/counts/hashes. A registered-path
claim must equal the exact already-verified installed container. An executable
correlation may be made only if the real schema provides that fact. Unsupported,
missing, duplicate, ambiguous, truncated, nonzero, or foreign results remain
unavailable/failed and never permit foreign cleanup or automatic remediation.

No `listapps`, registry-file, private API, alternate simulator, inventory, logging,
reinstall, database mutation, permission change, launcher-flag/plist repair,
entitlement change, timeout increase, or automatic retry is a fallback. If the
SDK lacks the exact supported interface, a new owner/source decision is required;
there is no authorized next command in this proposal.

## Preserve original gates

A diagnostic failure must not suppress existing owned cleanup or turn the actual
failed launch/profile green. Keep genuine UIKit launch, real PID/Worker/protocol,
fresh nonzero native XML, same-PID Instruments/allocation ownership and zero-leak
requirements unchanged. The debug-signing prerequisite stays ADR0012-scoped.

Registration state remains **unobserved, not proved absent**. Error-domain/code
observations are not root-cause evidence. **#141 remains open**; strict startup
40989310808, profile timeout 41008502211, and all subsequent pre-PID failures remain
failed/unfixed/unwaived. No native, heap, attachment, consumer/ABI, dependency,
legal/security, publication, Pages, main/history, release-readiness, or capacity
restriction is waived by a help or registration observation.
