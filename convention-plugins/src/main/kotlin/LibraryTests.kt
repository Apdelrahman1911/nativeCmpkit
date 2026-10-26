import org.gradle.accessors.dm.LibrariesForLibs
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.the
import org.jetbrains.kotlin.gradle.dsl.KotlinMultiplatformExtension

/** Test-only dependencies never become published production requirements. */
fun Project.configureLibraryTests() {
    val libs = the<LibrariesForLibs>()
    extensions.configure<KotlinMultiplatformExtension> {
        sourceSets.named("commonTest") {
            dependencies { implementation(libs.kotlin.test) }
        }
    }
}
