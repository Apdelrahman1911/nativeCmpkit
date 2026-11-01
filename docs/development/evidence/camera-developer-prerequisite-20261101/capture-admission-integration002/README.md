# Private camera012 capture-admission owning proposal002

Actual run 41263840100 at 375123435c remains FAILED: owned AVD creation exit 0 / 2.0 s,
reporter assembly exit 0 / 284.09 s, then pre-launch owned capture refusal with original
`android_camera_developer_prerequisite.py / require:47`. Specific calling guard,
INI/config input and cause remain unknown. No emulator/native/XML ran. Successful
confined removal of the two no-launch roots did not prove graceful emulator exit
or real post-exit ADB removal. Actual 011 and #13 remain failed/open; criterion 1
has no new acceptance, and accepted camera 009 criteria 2/3 are not replayed.

## Minimal owning change; not a guessed admission fix

Apply the three exact literals in `controller-fragments.json`, with modes from
`fragment-modes.json`, and add only
`post/scripts/ci/test_android_camera_capture_admission.py`. The conventional
`capture-admission-forward.patch` is supplemental. No whole-controller overwrite
or matching unrelated #64 source edits are required.

The existing camera AVD-first setup selection stays unchanged. Immediately after
successful `owned-avd-create` exit 0 / no stop, capture the sole newly owned guest
before the expensive following reporter APK assembly. A creation or capture
refusal cannot reach assembly, emulator log creation, Popen or native dispatch.
The existing `guest.before_launch()` and its unchanged `verify_config()` still
revalidate capture after assembly and before the sole emulator launch; a changed
config continues to refuse launch. There is no recapture, retry or fallback.

Keep the original primary `controller_error` and default innermost
`controller_error_origin` unchanged. Only this capture wrapper enables an internal
optional filter which skips exactly the generic prerequisite `require` frame and
records `camera_guest_capture_error_origin`: existing allowlisted basename,
validated public symbol and bounded source line, or unavailable/unavailable/0.
The original exception is re-raised even if this bounded diagnostic fails. No
exception bodies, locals, machine paths, config keys/values, guessed schemas,
SDK inventories or signing material are added. The diagnostic can localize a
future caller; it does not identify or waive the original actual 012 cause.

Helper/native/Settings UI bytes, confinement/FD ownership, master/native/scalar
snapshot and initialization, exact restoration, reboot/new-kernel barrier,
receiver/engine cleanup, disposal and final pass gates are untouched. Whole
original controller except/finally ASTs are identical; the sole _run delta is
its capture wrapper moved into the successful AVD-create setup-loop branch.

## Disjoint held #64 composition

Controller base: `bd31ce4195c31abd7431da65fa3ded2bb963d4ff2e77c267215b6a64694f7d6a`.
Owning camera postimage: `0b1de14d5c38215b5248c3082c598702cf398b87a2b88da217314e8190254e6b`.
Held #64-only postimage: `9630333740eba05d9ff702a647e8274439c233627c824175d55b05d2afcb8abf`.
Composed postimage: `078c96d591da170d7837c14ab9e142614bb4018cd1f0f89a1a68eac620cf7995`.

The two held #64 controller literals (API35 validation and CLI focus membership)
are disjoint. Both exact literal orders and both ordinary no-fuzz patch orders
reconstruct the identical composed controller. Fifty source/integrity/composition
checks pass, including unchanged primary/finally/sole launch and helper bytes.
The new test path is absent from #64 and live source. Read-only whole snapshots
under before/post/combined-post are for review, not whole-file integration.
Repository modes are 100644; all private files 0600 / directories 0700.

## New/affected important mocks only

Three targeted baseline owning methods retain original reds: two ordering
failures and one missing optional-filter interface error; original XML/logs stay
private. `verification/initial-owning-reds-safe-summary.json` contains bounded
public-safe facts, not raw traceback paths or exception bodies.

Exactly 10/10 new owning methods pass once on the composed controller, no skips,
errors or failures, 0.02781 s, one original model XML. They cover successful
AVD-create/capture/assembly/config-reverify/sole-launch ordering; create/capture/
assembly/config refusals; preservation of generic primary require:47; capture-only
safe direct/nested caller facts; diagnostic-failure fallback; noncapture route
ordering/no-op; and the original directory/symbol/line bounds. Test imports are
inert project stubs. Only the real generic require AST is retained for accurate
source-line provenance; its callers are explicit synthetic traceback shapes,
not observations of actual 012 inputs. Every model stops before real boot, APK
install, UI/prerequisite lease, native or restoration work and retains passed=false.
These are boundary mocks, not actual SDK/config/disposal/native acceptance.

The 77 accepted prerequisite methods, three existing wiring methods and seven
accepted #64 joint guards are NOT executed. No SDK/AVD command, local reproduction,
download, Gradle/heavy build, emulator, native execution, hosted request, live edit,
Git mutation or issue closure occurs. The unchanged actual 012 archive and 001
checksum manifests are read back exactly. No further local SDK reproduction is
needed or performed under the latest parent instruction.

Parent owns independent review, live fragment integration/refreeze and any later
request decision. Two hosted slots are occupied; this proposal makes no dispatch.
All native/consumer/minimum/ABI/dependency/legal/security/readiness/publishing/
Pages/main/history and reserve/capacity gates remain unchanged.
