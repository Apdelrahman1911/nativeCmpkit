import org.gradle.api.provider.Property
import org.gradle.api.tasks.testing.AbstractTestTask
import org.gradle.api.tasks.testing.Test

// Explicit CI invocation only. Keep compilation/dependency caches but never
// treat cached/up-to-date XML as a fresh execution of changed candidate tests.
allprojects {
    val simulatorDevice = providers.gradleProperty("nativecmpkitSimulatorDevice")
    tasks.withType<AbstractTestTask>().configureEach {
        outputs.upToDateWhen { false }
        outputs.doNotCacheIf("CI requires fresh test execution, not cached JUnit reports") { true }
        ignoreFailures = false
        doFirst {
            logger.lifecycle("NATIVECMPKIT_TEST_RUNTIME task=$path gradle=${gradle.gradleVersion} " +
                "java=${System.getProperty("java.version")} vendor=${System.getProperty("java.vendor")} " +
                "os=${System.getProperty("os.name")} arch=${System.getProperty("os.arch")}")
        }
    }
    tasks.withType<Test>().configureEach {
        maxParallelForks = 1
        maxHeapSize = "1024m"
        jvmArgs("-Xcheck:jni")
    }
    tasks.matching { it.name == "iosSimulatorArm64Test" }.configureEach {
        if (simulatorDevice.isPresent) {
            val identifier = simulatorDevice.get()
            check(Regex("[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}").matches(identifier)) {
                "nativecmpkitSimulatorDevice must be an actual recorded simulator UDID"
            }
            // Init scripts cannot statically import the later project KGP classpath.
            // KGP2.4.20's inspected public API exposes Property<String> getDevice().
            @Suppress("UNCHECKED_CAST")
            val device = javaClass.getMethod("getDevice").invoke(this) as Property<String>
            device.set(identifier)
            doFirst {
                check(device.get() == identifier) { "Effective simulator differs from recorded selection" }
                logger.lifecycle("NATIVECMPKIT_TEST_SIMULATOR task=$path device=${device.get()}")
            }
        } else {
            doFirst { error("CI iOS tests require an explicitly selected, booted and recorded simulator UDID") }
        }
    }
}
