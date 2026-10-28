<!-- nativecmpkit-operational:browser-dom-api -->
## Classification
- **Priority:** Medium
- **Evidence:** confirmed source and compiler reproduction; not a vulnerability
- **Scope:** `calf-io`, `calf-file-picker`, Wasm browser consumers; JS happens to supply these types intrinsically
- **Owning revision before repair:** `b9b25fd6`, development branch; additive finding, not one of the immutable 164 audit records

## Exact code and cause
- `calf-io/build.gradle.kts:47-49`: `webMain` declares `kotlinx-browser` as `implementation`.
- `calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.web.kt:5-9,43`: public `File` constructor/property and `File.toKmpFile()` require that dependency on consumer compile classpaths.
- `calf-file-picker/build.gradle.kts:43-45`: the same private dependency; public browser `FileSaverLauncher.launch(File/Blob,...)` also exposes these W3C types.

The private browser dependency lets each owning module compile but is absent from another module's exported Wasm compile classpath. An actual new library-level Coil consumer using only its existing `api(projects.calfIo)` cannot reference the public `KmpFile(File)` API. Adding a dependency only to a test would hide the broken publication/API contract.

## Reproduction and impact
Source-held Gradle compile at `b9b25fd6` plus three new test files, **817 unchanged before/after input hashes**, actual JDK17/Gradle9.7.1/Kotlin2.4.20:
```
:calf-file-picker-coil:compileTestKotlinJs
:calf-file-picker-coil:compileTestKotlinWasmJs
```
Overall **FAILED, exit1 /78.02s**. JS production/test KLIB compilation passes; Wasm reports unresolved `org.w3c`/`kotlinx.browser` and **Cannot access class org.w3c.files.File** at the public `KmpFile` call. Zero browser/runtime tests. This is a real separate project consumer, not yet a packaged Maven consumer.

## Recommended repair and compatibility
Expose the existing exact `kotlinx-browser` dependency as `api` in the owning web source sets; preserve its version, all public packages/types/descriptors, platform targets and native names. Do not substitute DOM stubs, downgrade Kotlin or add only a test dependency. Protect exported Gradle metadata and a consumer with no direct browser dependency.

## Required important verification
1. The no-extra-browser-dependency Coil project compiles real File/Blob/FileReader API use on both JS and Wasm.
2. Exact generated browser target API metadata includes the pinned browser coordinate; native/JVM variants do not acquire a browser dependency.
3. Real browser binary reads, Coil cancellation/reader cleanup, error/callback handling and bounded fetch preflight regressions execute on JS/Wasm; preserve the original failure evidence.

## Independent gates / risks
Widening an exported dependency is additive but changes browser consumer graphs. Complete packaged KMP/ABI/minimum-platform/dependency/security/release gates remain under BUILD-006/007 and do not pass automatically. FileReader error injection is not OS grant revocation. No packages/releases/deployments are authorized by this issue.

Evidence will be committed under `docs/development/evidence/browser-read-coil-important-20261028/`; the baseline 164 findings and imported metadata/history remain unchanged. No upstream mutation or known upstream-specific duplicate was identified.
