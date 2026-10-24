<!-- Modified for nativeCmpkit migration (2026-10-24). -->
# Installation and source development

## Publication status

**No nativeCmpkit package or release has been published.** The planned coordinates
below identify the renamed build, not a currently downloadable Maven release:

```kotlin
// Future coordinates only — do not expect these to resolve from Maven Central yet.
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-ui:0.1.0-SNAPSHOT")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-file-picker:0.1.0-SNAPSHOT")
implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions-camera:0.1.0-SNAPSHOT")
```

A future publication requires owner authorization, namespace verification,
license packaging, signing, native artifact completeness and release-gate tests.
See [the roadmap](roadmap/README.md). Historical Calf Maven coordinates and tags
do **not** designate nativeCmpkit builds; their history is [archived](migration/legacy/installation.upstream.md).

## Work with the checked-in source

Clone this independent repository and use its sample projects / Gradle project
dependencies (`projects.calfUi`, `projects.calfFilePicker`, etc.). This avoids any
runtime or source-fetch dependency on the original repository.

```sh
git clone https://github.com/Apdelrahman1911/nativeCmpkit.git
cd nativeCmpkit
./gradlew :calf-io:desktopTest :calf-file-picker:desktopTest
# These require an appropriate local graphical / Android / browser environment:
./gradlew :sample:desktop:run
./gradlew :sample:android:assembleDebug
./gradlew :sample:web-wasm:wasmJsBrowserDevelopmentRun
```

Required baseline: JDK 17; Kotlin 2.4.20; Compose 1.12.0; Gradle 9.7.1; Android
SDK 37 and AGP 9.4.0; library minSdk 23, sample minSdk 24. Desktop picker/share
builds need Rust on PATH and native host packages. A Debian/Ubuntu development
host needs `pkg-config`, `libgtk-3-dev` and `libwayland-dev`; headless desktop tests
also need Xvfb. The official SDK package is `platforms;android-37.0`, while the
source remains `compileSdk = 37`. Apple builds require macOS/Xcode and the iOS SDK. Do not assume a
sample compile or an isolated JVM probe verifies a native device flow. Exact
attempts, overrides, results and blocked checks are in [testing](testing/README.md).

## Migration compatibility contract

- Replace Maven **group and artifact** when a verified release becomes available.
- Keep imports under `com.mohamedrejeb.calf.*` for now. Public annotations, JNI
  entry points, generated resource namespace and module paths remain stable.
- Do not combine upstream and independent artifacts in one runtime: they define
  the same classes. Existing users are not forced to migrate before a release.
- The source project paths remain `:calf-*`; coordinate mappings are explicit in
  [identity.json](migration/identity.json). Composite builds need explicit
  substitution because Gradle project names differ from new Maven artifact IDs.
- iOS consumers of native UI must export `projects.calfUi` from their shared
  framework, as the sample does. Existing Swift framework names remain unchanged.
- No binary/API compatibility certification is claimed. Preserve/add API dumps
  and cross-target consumer tests before the first nativeCmpkit release.

See [ADR 0001](decisions/0001-independent-identity.md), [module guides](modules/README.md)
and [platform caveats](platforms/README.md). Historical compatibility tables are
records of upstream claims, not retested support guarantees.
