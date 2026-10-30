# Android camera restoration verification — 2026-10-30

Original [#13/NATIVE-019](https://github.com/Apdelrahman1911/nativeCmpkit/issues/13)
requires actual don't-keep-activities, rotation/process death and restored
cancellation. **It remains open: compilation and synthetic guards are not device
executions.** Provider #78 is separately [verified and closed](evidence/android-camera-provider-20261030/closure001/README.md).

## Four important native scenarios

`AndroidCameraRestorationTest` uses the public
`rememberCameraPickerResultLauncher`, real Compose saved state and Android's
ActivityResultRegistry. Its nonexported consumer Activity runs in a separate
same-UID process from the surviving instrumentation reporter. No injected
registry result/state or manual URI grant is used.

The disabled-by-default, signature/UID/nonce-bound `CameraDelayedReceiverActivity`
is enabled as the sole implicit handler on a controller-owned API35 AVD. It
holds the real foreground external request while the OS destroys the caller via
don't-keep-activities, actual display rotation or same-UID kernel process death.
Finite completion writes only its real incoming EXTRA_OUTPUT using the actual
granted descriptor, then returns Android's result. The fourth method cancels
after process death and checks no stale result or sibling-cache loss.

Assertions require exactly one readable returned KmpFile/terminal result, genuine
Activity/PID/orientation changes as applicable, saved request restoration, native
grants/closed descriptors, unchanged sibling and no cancellation orphan. Task
ownership uses the client's committed nonce/UID/task ID plus its exact component;
missing task information is refused, never inferred absent. Native committed
preferences are read directly rather than from a stale cross-process cache.

Cleanup preserves primary errors and attempts all owned restorations. Only the
actual nonce-bound output can be removed, after verified task/external termination;
there is no cache sweep, foreign process kill or silent success. Shell reads are
bounded/deadlined/descriptor-owned; original package/component states, settings
and display rotation require exact readback. Provider/API23 accepted results are
not replayed.

## Reviewed preflight, not runtime proof

[Source/compile evidence](evidence/android-camera-provider-20261030/restoration-source001/README.md)
preserves three initial synthetic reds and an actual failed reporter compilation
(five SDK37 nullable-task-info errors, exit1/31.02s, receiver not started).
The minimal correction refuses null and reads each task snapshot once.
Held **987 library / 1064 combined inputs** then compile reporter APK0/34.01s
and independent receiver APK0/11.0s, **zero native executions**.128 important
camera/controller/matrix/workflow synthetic methods and Actionlint1.7.12 pass.

Finite profile `android-camera-restoration` selects only these four new methods
on API35, retains all11 full slots/eight Android modules and refuses an API23
restoration substitution. Actual immutable-CI outcomes still need inspection.
Synthetic camera bytes/recipient selection are not hardware/vendor/minimum-API,
packaged-consumer/API-ABI/heap/security or release certification. All publishing,
Pages, main/history and single-agent/capacity restrictions remain.
