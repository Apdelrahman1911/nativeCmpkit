# ADR 0012: explicit debugger prerequisite for the owned failed-profile recovery

- Status: accepted for contained **verification**, not release clearance
- Date: 2026-10-30

## Evidence

[41008502211](../development/evidence/image-memory-batch-important-20261030/target-recovery-ci001/README.md)
executes its real native workload, but UUID/PID-specific Instruments recording
times out150s. There are zero exports/owned rows/leaks commands. Neither signed
debug flag exists. No fixed refusal category matched; **the cause is unknown**.
Do not relabel that failure as a signing diagnosis or rerun it unchanged.

## Decision

Make one explicit debugger prerequisite for **only** the existing finite
`ios-image-profile-recovery` / `ios-native-image-allocation-profile-recovery`
request. Its disposable locally ad-hoc-signed test app requests exactly
`get-task-allow=true`. Observe the actual signed flag before installation. The
flag is not proof of attachment authorization, an Instruments pass or zero leaks.

The temporary static plist is exclusive/no-follow0600, under that invocation's
owned verification output. Verify its bytes/node before deleting it; changed or
foreign inputs fail and are preserved, never claimed cleaned. A reused signing
receipt cannot silently retry. Signing/readback failure prevents installation;
normal application identity/runtime/Worker/XML and owned cleanup gates remain.

No new credentials, host elevation, global debugger configuration, remote signing,
framework/package signing, publication or additional workflow token permissions.
All other full, strict, UIKit, picker and WebView modes keep their exact former
ad-hoc signer. [ADR0011](0011-independent-apple-memory-diagnostics.md) remains:
the original strict-startup failure is preserved and unwaived.

Only the still-failed profiler's one necessary workload is requested. Its earlier
functional pass does not supply new allocation evidence; two accepted stress and
nine conversion methods must not be replayed. Actual correlated owned-library
allocation rows plus a same-PID zero-leak summary remain mandatory. Unsupported
tools, no exports, signed flags, synthetic fixtures and a green native workflow
cannot close#141 or satisfy independent physical/minimum/ABI/consumer/security/
release gates. None of this modifies public Kotlin APIs or native payloads.

## Verification

Eight synthetic scope/exclusive-input/signed-readback/tamper/failure guards and
two default lifecycle guards pass; two new caller-branch integration guards pass
separately. These12 methods execute neither real Codesign nor Apple/native code.
Read [the held-input candidate evidence](../development/evidence/image-profile-debug-prerequisite-20261030/README.md).
A new immutable one-case Apple request and independent actual profile review are
required. No prior result is silently upgraded and no release is authorized.
