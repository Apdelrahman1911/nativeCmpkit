# Unpublished navigation/geo common consumer

This standalone Gradle project consumes only the public common APIs of the two
**unpublished experiments**, through two explicit composite substitutions to this
checkout. It is **source integration**, never packaged Maven/ABI/release evidence.
The existing independent packaged consumers are unchanged.

The single common file typechecks both adaptive factories, the public host,
the deliberately different legacy platform bridge, and geo's common factory,
result/snapshot/no-fix/lifetime APIs. AndroidX navigation is deliberately not an
explicit consumer dependency, so a hidden public type cannot be masked here.
The Android file also consumes both retained `bind` overloads, `unbind` and the
`LocationResult` override without declaring Google location/fragment/lifecycle
dependencies separately. Their exposed library API dependencies own that contract.
No acquisition backend, native navigation stack or sample app is substituted.

Configured exact Kotlin2.4.20/Compose1.12.0/AGP9.4.0/JDK17/Android37-min23, desktop,
JS/Wasm browsers and both Arm64 Apple targets match the library. From the repo:

```sh
./gradlew -p tests/consumer/navigation-geo-source \
  :compileAndroidMain :compileKotlinDesktop :compileKotlinJs :compileKotlinWasmJs \
  :compileKotlinIosArm64 :compileKotlinIosSimulatorArm64 \
  --no-daemon --no-configuration-cache --max-workers=2 --no-parallel
```

Linux can typecheck these Apple KLIBs; it cannot link/run an Apple application.
Compile begin/end markers must name every requested task. Compilation is **zero
runtime tests**, not proof of Android system back, native location acquisition,
UIKit gestures, browser history or packaged compatibility. Runtime/original-
criteria evidence is recorded separately; this fixture is currently unverified.
The initial actual Android compiler result exposed both hidden public AndroidX
controller and Google location-superclass dependencies. The owning patch changes
the existing declarations to `api`, without a version or public-signature change.
