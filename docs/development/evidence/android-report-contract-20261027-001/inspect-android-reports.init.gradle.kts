import org.gradle.api.file.DirectoryProperty

gradle.projectsEvaluated {
    rootProject.tasks.register("inspectNativeCmpkitDeviceReports") {
        doLast {
            listOf("calf-io", "calf-file-picker", "calf-webview").forEach { name ->
                val project = rootProject.project(":$name")
                val task = project.tasks.getByName("connectedAndroidDeviceTest")
                listOf("getXmlResultsDirectory", "getResultsDir", "getReportsDir").forEach { getter ->
                    val directory = task.javaClass.getMethod(getter).invoke(task) as DirectoryProperty
                    logger.lifecycle("NATIVECMPKIT_DEVICE_REPORT_CONTRACT task=${task.path} getter=$getter directory=" +
                        rootProject.projectDir.toPath().relativize(directory.get().asFile.toPath()).toString())
                }
            }
        }
    }
}
