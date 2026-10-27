import org.gradle.api.provider.Property
import org.gradle.api.provider.ListProperty
import org.gradle.api.file.DirectoryProperty
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
    tasks.matching { it.name == "connectedAndroidDeviceTest" }.configureEach {
        // AGP9.4.0's inspected DeviceProviderInstrumentTestTask is NOT an
        // AbstractTestTask. Verify its actual XML contract instead of silently
        // treating host-test paths or cached reports as device execution.
        val serial = providers.gradleProperty("nativecmpkitAndroidDeviceSerial")
        outputs.upToDateWhen { false }
        outputs.doNotCacheIf("Connected device verification requires fresh execution") { true }
        javaClass.getMethod("setIgnoreFailures", java.lang.Boolean.TYPE).invoke(this, false)
        doFirst {
            val identifier = serial.orNull ?: error("CI Android-device tests require an explicit owned emulator serial")
            val match = Regex("emulator-([1-9][0-9]{3})").matchEntire(identifier)
                ?: error("Invalid explicit emulator serial")
            val port = match.groupValues[1].toInt()
            check(port in 5554..5682 && port % 2 == 0) { "Expected a valid even emulator console port" }
            // AGP9.4.0 getFilteredDevices consumes its target serial list, but
            // setSerialOption stores a Gradle ListProperty whose value is immutable.
            // Actual JDK17 invocation reproduces that failure even with a mutable
            // setter argument. Use AGP's supported ANDROID_SERIAL provider filter,
            // not an unowned-device fallback or a mutation of dependency internals.
            check(providers.environmentVariable("ANDROID_SERIAL").orNull == identifier) {
                "Gradle must receive the same exact owned-emulator environment selector"
            }
            val factory = javaClass.getMethod("getTestRunnerFactory").invoke(this)
            for (getter in listOf("getDeviceSerialValues", "getConnectedCheckDeviceSerials")) {
                @Suppress("UNCHECKED_CAST")
                val options = factory.javaClass.getMethod(getter).invoke(factory) as ListProperty<String>
                check(options.orNull.orEmpty().isEmpty()) {
                    "CI uses ANDROID_SERIAL; do not populate AGP's mutable target-serial filter options"
                }
            }
            val results = javaClass.getMethod("getXmlResultsDirectory").invoke(this) as DirectoryProperty
            // getResultsDir is the public UTP/protobuf output, NOT the XML tree.
            // Executed inspection of AGP9.4.0's actual tasks establishes this
            // distinct intermediate directory; keep both contracts explicit.
            val expected = layout.buildDirectory.dir("intermediates/android_test_results/androidMain/connectedAndroidDeviceTest").get().asFile.canonicalFile
            check(results.get().asFile.canonicalFile == expected) {
                "AGP XML layout differs from the inspected contract; review the runner, do not guess reports"
            }
            val outputs = javaClass.getMethod("getResultsDir").invoke(this) as DirectoryProperty
            val expectedOutputs = layout.buildDirectory.dir("outputs/androidTest-results/connected/androidMain").get().asFile.canonicalFile
            check(outputs.get().asFile.canonicalFile == expectedOutputs) {
                "AGP UTP output layout differs from the inspected contract; review the runner"
            }
            logger.lifecycle("NATIVECMPKIT_TEST_RUNTIME task=$path gradle=${gradle.gradleVersion} " +
                "java=${System.getProperty("java.version")} vendor=${System.getProperty("java.vendor")} " +
                "os=${System.getProperty("os.name")} arch=${System.getProperty("os.arch")}")
            logger.lifecycle("NATIVECMPKIT_TEST_ANDROID_DEVICE task=$path serial=$identifier")
            logger.lifecycle("NATIVECMPKIT_TEST_ANDROID_REPORT task=$path " +
                "xml=build/intermediates/android_test_results/androidMain/connectedAndroidDeviceTest " +
                "utp=build/outputs/androidTest-results/connected/androidMain")
        }
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
