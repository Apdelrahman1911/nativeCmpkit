import org.jetbrains.kotlin.gradle.targets.native.tasks.KotlinNativeHostTest
import java.time.Duration

plugins { kotlin("multiplatform") version "2.4.20" }
kotlin { linuxX64() }

for ((taskName, flags) in listOf("nativeWorkerPositive" to emptyList<String>(),
    "nativeWorkerIntentionalFailure" to listOf("--nativecmpkit-probe-fail"))) {
    tasks.register<KotlinNativeHostTest>(taskName) {
        executable(layout.projectDirectory.file("owned-worker.kexe").asFile)
        targetName = "linuxNativeParserDiagnostic"
        workingDir = layout.projectDirectory.asFile.absolutePath
        args = flags
        ignoreFailures = false
        ignoreRunFailures = false
        binaryResultsDirectory.set(layout.buildDirectory.dir("test-results/$taskName/binary"))
        reports.html.outputLocation.set(layout.buildDirectory.dir("reports/tests/$taskName"))
        reports.junitXml.required.set(true)
        reports.junitXml.outputLocation.set(layout.buildDirectory.dir("test-results/$taskName"))
        outputs.upToDateWhen { false }
        outputs.cacheIf { false }
        timeout.set(Duration.ofSeconds(120))
        testLogging { showStandardStreams = true; events("passed", "failed", "skipped") }
        doFirst { logger.lifecycle("NATIVECMPKIT_ACTUAL_KGP_HOST_PARSER task=$path") }
    }
}
