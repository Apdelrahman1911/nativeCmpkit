import org.gradle.api.provider.Property
import org.gradle.api.provider.Provider
val selectedRoot = java.io.File(checkNotNull(System.getProperty("nativecmpkit.selectorProbeRoot"))).canonicalFile
gradle.projectsEvaluated {
    if (rootProject.projectDir.canonicalFile != selectedRoot) return@projectsEvaluated
    rootProject.tasks.register("verifyNativeSaveSelectorConfiguration") {
        doLast {
            val task = rootProject.project(":calf-file-picker").tasks.named("connectedAndroidDeviceTest").get()
            @Suppress("UNCHECKED_CAST")
            val data = (task.javaClass.getMethod("getTestData").invoke(task) as Property<Any>).get()
            @Suppress("UNCHECKED_CAST")
            val arguments = (data.javaClass.getMethod("getInstrumentationRunnerArguments").invoke(data) as Provider<Map<String,String>>).get()
            val expected = mapOf("annotation" to "com.mohamedrejeb.calf.picker.SaveIdentityAcceptance", "notAnnotation" to "com.mohamedrejeb.calf.picker.SaveIdentityCalibration")
            check(arguments.filterKeys { it in setOf("class", "annotation", "notAnnotation") } == expected)
            check(expected.values.none { ',' in it })
            println("NATIVECMPKIT_SAVE_SELECTOR_PROBE actualAGP=9.4.0 selectors=annotation+notAnnotation commaFree=true matched=true nativeTestsExecuted=0")
        }
    }
}
