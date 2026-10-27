# ADR0007 — Own proven detached Gradle fixture processes

- Date: 2026-10-27
- Status: accepted for contained verification tooling; **actual repair verification required**
- Scope: controlled single-root Linux Gradle9.7.1/JDK17 fixtures, not library/public API

## Evidence and cause

An actual finite60s task-graph hold reproduces the original controller's leak at
its20s timeout. It signals the client group and returns143; the exact previously
validated/pinned direct-child Gradle daemon remains live in its own group/session.
The probe later cleans up its own known pinned daemon. That separate cleanup is
not original-controller success. [Preserve the original red](../development/evidence/build/dependency-fixtures/owned-daemon-timeout-red-20261027/lead-review.json).

## Decision

Acquire explicit client/daemon process leases in the owning runner, before the
client exits. Fresh bounded no-follow private daemon-log filenames nominate a
candidate **only**; contents, runtime receipts and arbitrary PIDs never authorize
signaling. Exact live client-parent/start/UID/JDK/cwd/full argv/private-environment
proof, pidfd admission and post-pin revalidation remain mandatory. Share the
existing unchanged pure grammars with the passive witness rather than inventing
a weaker command suffix check or circularly importing the observer into the core.

Stop/wait/reap on normal return, timeout, SIGINT/SIGTERM and failures. A temporary
single-threaded controller subreaper restores its previous flag after exact
adopted-daemon reaping; never `waitpid(-1)`, globally scan, or signal guessed groups.
Previously proven leases remain eligible for cleanup when another candidate is
ambiguous; such ambiguity never becomes success. Revalidate live leases before
pidfd TERM/KILL and bound total cleanup to10s. Close all known pidfds/directory
handles and restore signal handlers. Preserve the original shared total deadline
and8GiB disk reserve. No unsafe observer workaround or cleanup-by-log-PID.

009 is a new predecessor-hash-bound ten-input core manifest. The original008
manifest/inputs and all failed results remain unchanged. The passive witness
explicitly selects009 and preserves its original attach/binding requirements.
The additive010 EOF/staged-preflight correction preserves009 as its explicit
predecessor and leaves the entire shared-parser AST and ownership implementation
unchanged. Future observer selection is010, not an in-place009 checksum refresh.
Prior five actual009 results are reused only in their original scope/counts.

## Alternatives and limits

- `--no-daemon` still uses a single-use daemon; it does not establish group ownership.
- Killing a receipt PID or fresh log filename is unsafe without live ancestry,
  full command/environment and pinning. Host-wide Gradle stop/process scans can
  affect unrelated work and are forbidden.
- A passive observer never becomes the fixture's resource owner. Subreaping does
  not fix missing `/proc/.../children` files or expand diagnostic authority.
- Scope is deliberately narrow. Ordinary wrappers/composites, other hosts,
  arbitrary forked descendants and controller SIGKILL remain unverified gaps.
  This is a resource guard, not a hostile-code/kernel sandbox or trust evidence.

## Required verification

Adversarial tests cover foreign/reused/exited/ambiguous candidates, argv/JDK/cwd/
private-environment changes, no-follow/private/bounded log nomination, pin failure,
signal revalidation, exact reaping, descriptor/flag/handler restoration and honest
unsupported scope. Existing core/observer regressions must still pass.

Real fresh local-Maven invocations must separately exercise normal completion,
the preserved finite-hold timeout, SIGINT, SIGTERM and TERM-resistant escalation.
The owning controller—not a probe cleanup—must finish with exact processes absent
and all resources restored. Preserve failures and held sources. These are zero
library/native/strict packaged-consumer tests and cannot close BUILD-007's ordinary
dependency/trust requirements or any release gate.
