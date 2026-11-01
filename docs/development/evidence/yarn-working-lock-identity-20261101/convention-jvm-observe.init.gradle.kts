// Owning, standalone convention-build observation; no paths or environment values.
gradle.settingsEvaluated {
    check(rootProject.name == "convention-plugins") {
        "This observation belongs only to the standalone convention build"
    }
    val major = Runtime.version().feature()
    check(major == 17) { "The owning convention verification requires JDK17" }
    println("NATIVECMPKIT_CONVENTION_JVM {\"major\":" + major +
        ",\"gradle_version\":\"" + gradle.gradleVersion + "\"}")
}
