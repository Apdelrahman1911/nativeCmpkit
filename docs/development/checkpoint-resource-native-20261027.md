# Contained resource ownership and native identity — 2026-10-27

Single-agent development; Actions remain enabled/all/no-mandatory-pinning under
the owner decision. Verification is read-only, with no persisted checkout
credentials or package/deployment/release scopes. Publishing and Pages remain
contained. This additive checkpoint preserves earlier failures and does not
replace the164 findings or their530 original acceptance requirements.

Base revision: `cebdc8f206a5e34b39e1cb8053b380ba509707c2` on
`development/preview-hardening`. All local source-held results below describe
dirty inputs at that base, not a release candidate. `main` stays at
`94d2492e99d5cbc060409d94d9f88febd06222d5`.

## Reconciled upstream and issue context

The [read-only open-list observation](evidence/upstream-open-observation-20261027T062000Z/receipt.json)
finds the same16 open upstream numbers/titles/update timestamps as the latest
[full attributed reconciliation](upstream-refresh-20261027T014340Z/README.md).
This is list continuity, not another full description/comment/timeline export.
No new import or duplicate is inferred. Original metadata snapshots remain
immutable. [Two additive progress comments](evidence/issue-progress-20261027-cebdc8f2/receipt.json)
are readback-verified for NATIVE-037/#89 and BUILD-007/#40; issue bodies, labels
and states are retained. No issue is closed by the present work.

## Real detached-daemon leak and owning controlled-fixture repair

[The executable red](evidence/build/dependency-fixtures/owned-daemon-timeout-red-20261027/lead-review.json)
uses a real installed Gradle9.7.1/JDK17, plugin-free finite60s task hold. Original
`integrity.py::_bounded` returns after20s/client143 while the separately live-
validated/pidfd-pinned daemon remains running in its own group/session. The
probe's subsequent exact cleanup is **not original-controller success**.

### Contract, scope and source

- `gradle_process.py` extracts nine pure parser/class declarations unchanged
  from the passive witness; AST signatures, decorators and bodies are compared
  against the base revision. Existing witness names remain import aliases.
- `owned_gradle.py` owns only a dedicated single-threaded, single-root Linux
  **installed** Gradle9.7.1/JDK17 controlled fixture. Bounded no-follow fresh
  private log filenames nominate, never authorize, a daemon. Exact live client
  parent/start/UID/JDK/cwd/full argv/private-environment proofs precede pidfd
  admission and post-pin revalidation. No log-body/PID-receipt authority.
- Signals target exact pinned leases, not guessed daemon groups. Normal return,
  timeout and interruption perform bounded TERM→KILL cleanup, exact adopted-child
  reaping, pidfd/directory closure and restoration of signal handlers and the
  controller's temporary prior subreaper flag. Already-proven leases survive an
  ambiguity failure for cleanup. No global scan, wildcard wait, jcmd or observer
  subreaper is added. Unknown/changed identity fails, never silent success.
- Integration explicitly selects that controlled scope. Ordinary wrappers,
  composites, other hosts, arbitrary descendants and controller SIGKILL remain
  unverified; those paths are not certified by this helper.
- [ADR0007](../decisions/0007-owned-gradle-fixture-processes.md) records the boundary.
  New explicit checkpoint009 binds ten core inputs; its SHA256 is
  `08a00d96d05d14f8dbb188a6ddbd532a3785a5955907dcbc966e5522c6abaa8e`.
  Original008 remains byte-identical. This is input binding, not independent
  dependency trust or acceptance of any later mutable checksum refresh.

### Actually executed verification

[Independent source/ZIP/runtime-schema review](evidence/build/dependency-fixtures/owned-daemon-cleanup-20261027/lead-independent-review.json)
checks92 original byte-paired archive members and all14 frozen fixture/witness
inputs. The controller, **not an external probe**, performs cleanup:

| Actual fresh invocation | Elapsed / expected observation |
|---|---|
| Normal baseline | 8.860s; actual graph summary and normal client/daemon exit |
|20s timeout of finite60s hold | 20.880s; exact client/daemon TERM, adopted daemon reaped |
|SIGINT | 7.625s; interruption retained, exact cleanup/restoration |
|SIGTERM | 7.220s; interruption retained, exact cleanup/restoration |
|TERM-resistant shutdown | 25.393s; actual daemon KILL escalation and exact reaping |

All15 exact controller/client/daemon PIDs are absent at independent review.
There are zero jcmd or library/native/strict packaged-consumer executions.
The original owner53-method suite overlaps the final61. The complete dependency
Python suite passes **380/380**:171 core,148 passive observer and61 owner methods.
An initial review's wrong `process_id` runtime-schema assumption is preserved;
the corrected review uses the real strict `gradle_jvm_process_id` schema.

BUILD-007 remains **unresolved**: ordinary root/composite/convention locking and
artifact verification, complete script/tool graphs, all applicable empty-cache/
frozen/tamper scenarios, independent advisory/license/provenance review and other
host/consumer/native gates remain. The selected forced-cleanup gap is now tested;
it must not be generalized to unowned wrapper or descendant processes.

## UIKit failed attempts, exact identity repair and honest verification

[Run40460102044 attempt1](evidence/github-actions/40460102044/attempt-1/lead-independent-review.json)
fails before testing at hosted simulator migration/60s service timeout. Only
its failed job is rerun at unchanged base SHA; tooling is reused with original
timestamps. [Attempt2](evidence/github-actions/40460102044/attempt-2/lead-independent-review.json)
links/signs/installs and cleans up, but reaches startup deadline with active/key/
visible true, Kotlin wrapper identity false, native value equality true and
worker not started. Gradle exits1/737.94s; **zero activation/testcase/XML**.
Delaying activation alone is not a fix. Neither value equality nor the failed
runner exit is a native ownership proof.

[Exact native identity](native-ui-application-host.md#exact-native-object-identity-after-the-persistent-startup-timeout)
is test-host-only and compares nonnull retained NSObject pointers through the
configured public `objcPtr` API. New real-native adversarial coverage rejects
equal-content/different-allocation objects and null owners, and checks the actual
window getter. Seven presenter plus four host methods/three source files are
mandatory; active/key/visible/main/deadline/worker/transport/cleanup gates remain.

[Local red/green review](evidence/uikit-native-object-identity-20261027/lead-independent-review.json)
preserves the first KLIB import failure1/39.68s and corrected fresh full-test
KLIB/model compile0/37.01s. Both hold712 selected/copied inputs; unchanged
production caches are reused, not test XML. Corrected CI Python guards pass226/
226. Earlier9-method red and225-method fixture failure remain; earlier226 runs
overlap. This is **zero Apple/library/native/device/strict consumer executions**.
Only new immutable affected `ios-ui` CI can establish native runtime behavior.

## Capacity, dispositions and release boundaries

When root available capacity slipped below8GiB, no new heavy build was started.
Only this project's obsolete `build/docs-verification/locked-001` installation/
cache was relocated losslessly to owned tmpfs; all20,953 entries/130,983,972 file
bytes match before/after. Its root path remains a local symlink. No source,
archives, other projects or unrelated caches were removed. Capacity was rechecked
before the fresh compile; the8GiB reserve held at completion. Relocation receipt
remains local in `/dev/shm/nativecmpkit-owned-docs-cache-relocation-20261027/`.

The ledger stays **87 implemented /69 partially-verified /8 unresolved /
0 verified**. No original acceptance requirement is dropped and no issue is
closed. Android hard-link/SELinux fixture, IO-023 native parent leases, complete
device/minimum-platform/payload coverage, objc2-family licensing/SDK material,
ordinary dependency policy/trust, ABI and **zero strict packaged Kotlin consumer
executions** still block release. No package, release, snapshot or deployment.

## Source-held full preflight, not runtime certification

[Preflight013 independent review](evidence/ci-preflight-20261027-013/lead-review.json)
passes22 bounded commands and1014 Python methods:226 CI,171 dependency core,
148 observer,61 owner, plus408 other tooling methods. Strict MkDocs, actionlint,
all164 resolution/index/530 original requirements, source/migration history and
generator checks pass; six actual HTML targets/anchors are independently checked.
All15,384 captured inputs stay held and are rechecked before/after archive. Input
maps are losslessly compressed to protect disk reserve. The archive and this
additive link follow that freeze; they are **not circularly self-certified**.
Counts overlap earlier runs and are zero library/native/strict consumer methods.
Immutable hosted affected-profile runtime evidence remains required.
