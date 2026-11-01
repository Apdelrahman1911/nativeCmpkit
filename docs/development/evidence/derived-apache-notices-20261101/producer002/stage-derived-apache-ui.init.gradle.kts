// Source-bound UI-only local artifact verification; never enables public navigation.
import org.gradle.api.publish.maven.tasks.PublishToMavenRepository
import org.gradle.kotlin.dsl.withType
val selectedRootFile = java.io.File(checkNotNull(System.getProperty("nativecmpkit.derivedApacheStagingRoot")))
check(selectedRootFile.isAbsolute && selectedRootFile.isDirectory)
val selectedRoot = selectedRootFile.canonicalFile
gradle.projectsEvaluated {
    val root = rootProject
    if (root.projectDir.canonicalFile != selectedRoot) return@projectsEvaluated
    check(root.name == "NativeCmpKit")
    check(root.providers.gradleProperty("nativecmpkitVerification").orNull == "true")
    check(root.providers.gradleProperty("nativecmpkitVerificationTargets").orNull == "all")
    check(root.providers.gradleProperty("nativeCmpkit.version").orNull == "0.1.0-preview.1")
    val module = root.project(":calf-ui")
    val suffixes = mapOf("kotlinMultiplatform" to "", "android" to "-android", "desktop" to "-desktop",
        "js" to "-js", "wasmJs" to "-wasm-js", "iosArm64" to "-iosarm64", "iosSimulatorArm64" to "-iossimulatorarm64")
    val repository = root.layout.buildDirectory.dir("verification-repo").get().asFile.canonicalFile
    val selected = module.tasks.withType<PublishToMavenRepository>().filter {
        it.repository.name == "NativecmpkitVerification" && it.publication.name in suffixes
    }
    check(selected.size == 7 && selected.map { it.publication.name }.toSet() == suffixes.keys) {
        "Every real UI publication task is required for this source/distribution check"
    }
    selected.forEach { task ->
        val url = task.repository.url
        check(url.scheme == "file" && url.authority.isNullOrEmpty() && java.io.File(url).canonicalFile == repository)
        check(task.publication.groupId == "io.github.apdelrahman1911.nativecmpkit" && task.publication.version == "0.1.0-preview.1")
        check(task.publication.artifactId == "nativecmpkit-ui" + suffixes.getValue(task.publication.name))
        task.doLast {
            println("NATIVECMPKIT_DERIVED_APACHE_UI_STAGE task=${task.path} publication=${task.publication.name} artifact=${task.publication.artifactId} version=${task.publication.version}")
        }
    }
    root.tasks.register("stageDerivedApacheUiVerification") {
        group = "verification"
        description = "PARTIAL: real UI-only local artifact/source notice inspection; no consumer, runtime, legal or release clearance"
        dependsOn(selected)
        doLast { println("NATIVECMPKIT_DERIVED_APACHE_UI_STAGE_COMPLETE selected=7 remote=0 navigationPublication=0") }
    }
}
