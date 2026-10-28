// Fixed WebView-only local staging. Does not change the full21-root or Core/IO consumers.
import org.gradle.api.publish.maven.tasks.PublishToMavenRepository
import org.gradle.kotlin.dsl.withType

val selectedRoot = java.io.File(checkNotNull(System.getProperty("nativecmpkit.webviewStagingRoot"))).canonicalFile
check(selectedRoot.isAbsolute && selectedRoot.isDirectory) { "WebView staging requires an existing absolute root" }

gradle.projectsEvaluated {
    val root = rootProject
    if (root.projectDir.canonicalFile != selectedRoot) return@projectsEvaluated
    check(root.name == "NativeCmpKit") { "Unexpected WebView staging root identity" }
    check(root.providers.gradleProperty("nativecmpkitVerification").orNull == "true") { "WebView staging requires local verification mode" }
    check(root.providers.gradleProperty("nativecmpkitVerificationTargets").orNull == "desktop") { "WebView staging requires the desktop-only verification target" }
    check(root.providers.gradleProperty("nativeCmpkit.version").orNull == "0.1.0-preview.1") { "Unexpected WebView staging candidate version" }
    val repository = root.layout.buildDirectory.dir("verification-repo").get().asFile.canonicalFile
    val module = root.project(":calf-webview")
    val selected = module.tasks.withType<PublishToMavenRepository>().filter {
        it.repository.name == "NativecmpkitVerification" && it.publication.name in setOf("kotlinMultiplatform", "desktop")
    }
    check(selected.size == 2) {
        "WebView staging requires exactly root and desktop publications; selected=" + selected.map { it.publication.name }.sorted()
    }
    selected.forEach { task ->
        val url = task.repository.url
        check(url.scheme == "file" && url.authority.isNullOrEmpty() && java.io.File(url).canonicalFile == repository) { "WebView staging must use the exact isolated local repository" }
        check(task.publication.groupId == "io.github.apdelrahman1911.nativecmpkit" && task.publication.version == "0.1.0-preview.1") { "Unexpected WebView publication group/version" }
        check(task.publication.artifactId == "nativecmpkit-webview" + if (task.publication.name == "desktop") "-desktop" else "") { "Unexpected WebView publication artifact identity" }
        task.doLast { println("NATIVECMPKIT_WEBVIEW_STAGE task=${task.path} group=${task.publication.groupId} version=${task.publication.version}") }
    }
    root.tasks.register("stageWebViewVerificationPublications") {
        group = "verification"
        description = "PARTIAL: stage WebView metadata+desktop only into the exact local verification repository"
        dependsOn(selected)
    }
}
