# KVM between-route source review — negative within reviewed scope

Reviewed immutable **eafb10f720393dc3a38b4fd18287718eb49cbaea**, independently
compared with **1c74cb9a7951610fdb8098869f9daadd918b8a39**, used by both API35
actual003 (`41265408309`) and storage actual001 (`41265416289`).

**Finding: no inspected repository operation explicitly changes host `/dev/kvm`
access between child routes. No confirmed owning source gap; no patch or new guard
execution is justified by this review.** This is not proof that host state or
external executable behavior cannot change, and not an actual cause diagnosis.

| Exact pushed source location | Source-backed observation | Lineage |
|---|---|---|
| `.github/workflows/gradle.yml:358–364` | The sole explicit KVM writer is the existing one-time `sudo setfacl -m "u:$(id -un):rw" /dev/kvm`, bounded by character-device/read/write shell checks. It runs before runtime/planning and the single batch invocation at 457–459; no between-route grant/reset/retry is present. | `d849515b` |
| `android_device_tests.py:112–121,619–639` | Original Linux/x64 plus character-device/paired-access admission still runs before output or controller lease. New after-refusal observations are read-only and cannot authorize recovery. | Original `d849515b`; diagnostic `eafb10f7` |
| `android_device_tests.py:261–278,354` and `library_tests.py:3202–3226` | Fresh route paths live below the reviewed output. Child environments are copies; batch child execution inherits the existing user. Popen uses owned sessions, not a user/group/preexec credential change. Emulator launch retains `-accel on`; SDK executables are external boundaries, not reviewed implementations. | Original scoped environment/launch `d849515b`; executor `6eb7c66e`/`d849515b` |
| `android_device_tests.py:130–158,188–209,513–538` | Cleanup sends only owned-serial `emu kill`, waits for that child, and observes an empty ADB device table. It does **not** kill/restart the ADB server, remove a host device or rewrite its ACL. Forced owned-group termination makes cleanup nonacceptable. | Shutdown `d849515b`; transport observation `a2ecd026` |
| `android_io_documents.py:371–381` → `android_share_recipient.py:91–111`; `android_storage_probe.py:597–643` | I/O cleanup is owned guest force-stop/uninstall/readback. Storage cleanup additionally restores the owned guest SAF/WRITE/app-op state through serial-scoped ADB; these are not host-KVM permissions. No-install cleanup only records no mutation. | Shared cleanup `44b9a16f`/`eb6e9d2e`; storage `a18532a4` |
| `android_device_batch.py:80–108,293–327,357–401`; `library_tests.py:1576–1588` | Before the next child, original controller/helper shutdown and lease absence must certify. Reclamation validates both complete nonsymlink, confined trees and deletes only that archived route's `avd` and `android-user` directories. No `/dev`, global SDK, cache or ADB-server deletion is called. A failed route stays failed even if its certified cleanup permits the next route. | Reclamation/batch `a18532a4`; confinement `6eb7c66e`; diagnostic retention `eafb10f7` |

Paths in the table are under `scripts/ci/` except the workflow. Exact earlier line
numbers, per-line Git attribution and SHA256/Git-blob identities are retained in
`SOURCE_LOCATIONS.json`, `LINEAGE.json` and `SOURCE_IDENTITIES.json`.

Nine source pairs were captured directly from Git; **12 exact-byte owning
function/provisioning comparisons** pass. The inspected lifecycle functions and
KVM provisioning block are unchanged from the two actual runs. The broader
controller/routing/parser files have disclosed disjoint changes, not whole-file
identity reuse. A source search found only the workflow's fixed KVM grant and the
controller's original/read-only KVM checks in the reviewed production scope.

Which original admission operand failed and why remain **unknown**. Sequential
after-refusal booleans cannot retroactively identify that operand or prove an ACL,
group, permission-mode, device-node or runner cause. One-time provisioning alone
is not a confirmed gap and does not justify elevation, chmod, ACL reapplication,
retries, relaxation or accepted-suite replay. SDK/emulator/ADB/Gradle dependencies
and runner services were not executed or exhaustively source-reviewed here.

**Zero live edits, proposals, synthetic/native methods, SDK/Gradle work, Git/GitHub
mutations, requests, dispatches or issue-state changes.** Accepted I/O3 is reused,
not replayed; the lead owns the already requested finite remaining-five API35 run.
