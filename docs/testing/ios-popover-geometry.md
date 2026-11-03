# Native popover OS-geometry tests

These are opt-in **library** tests, not sample-app or synthetic bounds substitutes.
The source preparation is [535–548](../development/evidence/current-platform-recovery-20261101/ios-popover-geometry535-548/README.md).

| Workflow profile | Native focus | Exactly selected method |
|---|---|---|
| `ios-popover-geometry-iphone` | `ui-native-popover-portrait-traits` | `NativePopoverGeometryTest.nativePortraitTraitsAndViewLocalAnchorUseTheOwnedScene` |
| `ios-popover-geometry-ipad` | `ui-native-popover-os-rotation` | `NativePopoverGeometryTest.nativeOSRotationRefreshesOwnedAnchorsAndRestoresTheOriginalOrientation` |

Both use `macos-26`, Arm64, a recorded booted simulator of the exact idiom, and
the genuine `:calf-ui:iosSimulatorArm64ApplicationTest`. Each profile selects one
new method; all previously accepted anchor/bar methods remain excluded.

## Native execution flow

1. The focused init script admits exactly the geometry test, geometry scene
   delegate, existing application host and exact native-object identity helper.
   `iosGeometryTest` is deliberately excluded from ordinary source-set inheritance.
2. The application wrapper verifies source/runtime/owned installation as before.
   Its plist enables one real `UIWindowScene`, the exported geometry delegate and
   public orientation eligibility. `UIRequiresFullScreen=false` is eligibility,
   **not evidence that split view occurred**.
3. Process-local `SIMCTL_CHILD_NATIVECMPKIT_OWNED_POPOVER_GEOMETRY=1` and the recorded
   phone/tablet idiom reach the app. Raw unprefixed host variables do not suffice.
4. Genuine scene connection binds the owned scene/window. Genuine activation
   enters the original timer/readiness/Worker machinery. No manually called UIKit
   scene callback or legacy-activation fallback is admitted in this mode.
5. The phone method verifies portrait/compact traits and real view-local anchoring.
   The iPad method requests public `UIWindowScene` portrait/landscape geometry,
   requires actual orientation and positive native geometry, regular traits and
   automatic owned view/fallback anchor updates while the same alert remains
   presented. No bounds/trait overrides or manually invoked reposition callbacks.
6. Owned alert/view cleanup runs even after failure; the original interface
   orientation is restored after any attempted geometry request. Primary and
   suppressed cleanup failures stay failures. Existing Worker termination, source
   custody, original XML and owned-app cleanup still decide acceptance.

Public geometry requests exercise OS window-scene geometry, not physical device
rotation or independent XCUI touch delivery. The API has an error callback but no
success callback; positive native orientation/bounds are the actual observations.
These tests do **not** establish real split view, every iOS version, physical
devices, packaged consumer integration, ABI compatibility or release readiness.

## Feasible local verification

Use JDK17 and the serial 8-GiB-reserve bounded build runner:

```sh
./gradlew --offline --no-daemon --no-parallel --no-configuration-cache \
  --max-workers=1 --init-script scripts/ci/daemon-jvm.init.gradle.kts \
  --init-script scripts/ci/ios_popover_geometry_compile.init.gradle.kts \
  -PnativecmpkitPopoverGeometryFocus=ui-native-popover-os-rotation \
  :calf-ui:compileTestKotlinIosSimulatorArm64
```

Linux can typecheck this focused test KLIB, **not link or execute UIKit**. See
actual540/544 commands/results for memory flags and resource receipts. Source-only
controls are in `scripts/ci/test_ios_popover_geometry.py`; reuse accepted unchanged
results and select only failed/new/changed obligations rather than blind reruns.

Before hosted dispatch, freeze/push the reviewed development SHA, confirm fresh
active/queued/waiting/pending/requested capacity, preserve main, and read back the
actual run SHA. At most two combined heavy reservations; a pair consumes both.
Acquire each terminal original once, compare actual maps to its own Git, verify
the exact compiler/scene fixture and one-case selector, then native/XML/Worker/
runtime/binary/cleanup agreement. Do not equate a runner-green summary, zero XML,
compile-only receipt or synthetically supplied trait with native acceptance.
