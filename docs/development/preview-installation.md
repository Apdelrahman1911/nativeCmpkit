# First Preview installation — draft, not yet available

**No `0.1.0-preview.1` availability is claimed by this document.** Run the snippets
against a registry only after the lead publishes and verifies the full candidate
set. The proposed first registry is GitHub Packages, **not Maven Central**.
Current [containment](containment.md) also keeps remote publication disabled;
these prospective instructions do not change that control policy.

## Kotlin Multiplatform dependencies

Keep Google and Maven Central for third-party Kotlin/Compose/Android dependencies.
Scope the nativeCmpkit registry exclusively to its group:

```kotlin
// settings.gradle.kts
dependencyResolutionManagement {
    repositories {
        exclusiveContent {
            forRepository {
                maven {
                    name = "NativeCmpkitGitHub"
                    url = uri("https://maven.pkg.github.com/Apdelrahman1911/nativeCmpkit")
                    credentials {
                        username = providers.environmentVariable("NATIVECMPKIT_GITHUB_USER").orNull
                        password = providers.environmentVariable("NATIVECMPKIT_GITHUB_TOKEN").orNull
                    }
                }
            }
            filter { includeGroup("io.github.apdelrahman1911.nativecmpkit") }
        }
        google()
        mavenCentral()
    }
}
```

GitHub's Maven registry generally requires authentication even for public
packages. Use a GitHub-supported read-only package credential (commonly a PAT
classic with `read:packages`) belonging to a user with package access, or an
appropriately authorized Actions `GITHUB_TOKEN` with `packages:read`. Verify
actual package permissions and platform token support. Keep credentials in your
secret store/environment, **never** in source-controlled Gradle files or shell
arguments. Do not reuse a publishing token just to consume public packages.

```kotlin
// build.gradle.kts — DRAFT coordinates until release verification completes
kotlin {
    sourceSets.commonMain.dependencies {
        implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-io:0.1.0-preview.1")
        implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-file-picker:0.1.0-preview.1")
        // Choose only modules used by your application:
        implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-ui:0.1.0-preview.1")
        implementation("io.github.apdelrahman1911.nativecmpkit:nativecmpkit-permissions:0.1.0-preview.1")
    }
}
```

Use KMP **root coordinates** and let Gradle choose Android/desktop/JS/Wasm/Apple
variants; do not hard-code `-desktop` into `commonMain`. The complete 21-module
map is in [`docs/migration/identity.json`](../migration/identity.json). Navigation,
geo and maps are currently unpublished; this document does not create package
support for them. The candidate fixture uses Kotlin2.4.20, Compose1.12.0 and
AGP9.4.0/JDK17. Android library minSdk is23. Actual minimum OS/runtime/device
acceptance remains a release gate rather than a property inferred from a POM.

## Retained source imports

```kotlin
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.source
import com.mohamedrejeb.calf.picker.rememberFilePickerLauncher
```

Keep the public namespaces deliberately. Remove the old `com.mohamedrejeb.calf`
Maven artifacts when replacing them: adding old and new artifacts together
creates duplicate public classes. Core/resource/JNI/framework names are not a
reason to perform a global search-and-replace.

Use explicit Android platform context until the appropriate application-context
initialization has been performed. Opening/consuming filesystem streams blocks
on desktop/mobile; move it to an appropriate IO dispatcher and always close the
returned `RawSource`/buffered source. Browser Blob sources have different buffering
semantics. Native capabilities and OS prerequisites are not uniform merely
because a common function exists.

## Desktop WebView runtime

After adding `nativecmpkit-webview`, select JavaFX for the **consumer/installer
destination**, not the nativeCmpkit publisher. For example, a Linux-x64 desktop
application uses:

```kotlin
kotlin.sourceSets.named("desktopMain") {
    dependencies {
        implementation(compose.desktop.currentOs)
        listOf("base", "graphics", "controls", "media", "web", "swing").forEach {
            implementation("org.openjfx:javafx-$it:21.0.13:linux")
        }
    }
}
```

Replace `linux` using the [five-host classifier table](compatibility.md).
`compose.desktop.currentOs` is appropriate only for the current consuming build
host; cross-built installers require destination-aware packaging. A working
graphics/session environment and the required system libraries remain necessary.
Read missing-runtime diagnostics rather than assuming a successful compile
launched WebKit/JavaFX or loaded a native picker.

## Redistribution and verification

Every planned Maven coordinate carries an accompanying `-notices.zip` with
complete LICENSE/NOTICE/third-party material. Relevant JAR/AAR distributions also
embed notices; compiled KLIBs are not rewritten to inject extra files.
Module-scoped embedded paths avoid duplicate Android/JVM resource names when
several nativeCmpkit modules are used together. Preserve
the accompanying notices when redistributing applications/frameworks/browser
assets, including the CupertinoIcons font's MIT attribution and native crate
licenses. Source-tree notices alone do not automatically enter a consuming app.

The release page must link the final registry bytes/checksums and **verified**
consumer commands. Until those links and receipts exist, use the isolated local
staging instructions in [`tests/consumer`](../../tests/consumer/README.md) and do
not advertise the candidate as downloadable.
