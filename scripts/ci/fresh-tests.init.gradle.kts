import org.gradle.api.provider.Property
import org.gradle.api.provider.Provider
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
        // AbstractTestTask. Verify its declared and executed UTP contracts instead of silently
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
            // Check the actual AGP task's arguments before ATE transport. ATE1.0.1
            // flattens its map as CSV, so a comma inside a class/method selector
            // loses all but its first method. Runtime annotation grouping is
            // lossless and the controller still requires every exact XML case.
            val selectorKeys = listOf("class", "annotation", "notAnnotation")
            val requestedSelectors = selectorKeys.mapNotNull { key ->
                providers.gradleProperty("android.testInstrumentationRunnerArguments.$key")
                    .orNull?.let { key to it }
            }.toMap()
            check(requestedSelectors.values.none { ',' in it }) {
                "ATE1.0.1 cannot transport comma-containing selection values losslessly"
            }
            @Suppress("UNCHECKED_CAST")
            val data = (javaClass.getMethod("getTestData").invoke(this) as Property<Any>).get()
            @Suppress("UNCHECKED_CAST")
            val runnerArguments = (data.javaClass.getMethod("getInstrumentationRunnerArguments")
                .invoke(data) as Provider<Map<String, String>>).get()
            check(runnerArguments.filterKeys { it in selectorKeys } == requestedSelectors) {
                "Effective AGP instrumentation selectors differ from the requested exact selection"
            }
            val results = javaClass.getMethod("getXmlResultsDirectory").invoke(this) as DirectoryProperty
            // Executed getter inspection establishes the DECLARED intermediate.
            // Actual run40434024680 has an empty tree there; its UTP producer
            // writes TEST-*.xml alongside protobufs under getResultsDir instead.
            // The collector uses only that source-defined, guarded public tree;
            // do not infer a testcase from a getter, filename or protobuf hash.
            val expected = layout.buildDirectory.dir("intermediates/android_test_results/androidMain/connectedAndroidDeviceTest").get().asFile.canonicalFile
            check(results.get().asFile.canonicalFile == expected) {
                "AGP declared XML layout differs from the inspected contract; review the runner, do not guess reports"
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
                "declaredXml=build/intermediates/android_test_results/androidMain/connectedAndroidDeviceTest " +
                "collectedXml=build/outputs/androidTest-results/connected/androidMain " +
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
