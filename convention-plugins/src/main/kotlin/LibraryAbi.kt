import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure
import org.jetbrains.kotlin.gradle.dsl.KotlinMultiplatformExtension
import org.jetbrains.kotlin.gradle.dsl.abi.BinariesSource
import org.jetbrains.kotlin.gradle.dsl.abi.ExperimentalAbiValidation

/** Compiler-backed JVM/KLIB ABI checks; lexical indexes and javap are supplemental only. */
@OptIn(ExperimentalAbiValidation::class)
fun Project.configureLibraryAbi() {
    if (path.startsWith(":sample")) return
    extensions.configure<KotlinMultiplatformExtension> {
        abiValidation {
            // Invoking this DSL enables ABI validation in KGP 2.4; the old
            // enabled property remains in bytecode but is a Kotlin error.
            // AGP Android publication analysis is unsupported by this KGP version.
            // Main-compilation inputs include the JVM/API surface without pretending
            // that POM inspection or signatures certify Android/Swift runtime ABI.
            binariesSource.set(BinariesSource.MAIN_COMPILATION)
            referenceDumpDir.set(layout.projectDirectory.dir("api"))
            keepLocallyUnsupportedTargets.set(true)
        }
    }
}
