import org.jetbrains.kotlin.gradle.targets.jvm.KotlinJvmTarget

plugins {
    `kotlin-multiplatform`
}

// Application/source-test runtime, deliberately never applied to a published library.
val javaFxRuntime = project.javaFxDependencies()
kotlin.targets.withType<KotlinJvmTarget>().configureEach {
    compilations.named("main") {
        defaultSourceSet.dependencies {
            javaFxRuntime.forEach { implementation(it) }
        }
    }
}
