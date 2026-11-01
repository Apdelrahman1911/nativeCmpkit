// SPDX-License-Identifier: Apache-2.0
// Finite owning setup readback and public test-worker boundaries only.
// Not a sandbox, OS-PID/process-exit attestation or TLS/rendering oracle.
import org.gradle.api.tasks.testing.Test
import org.gradle.api.tasks.testing.TestDescriptor
import org.gradle.api.tasks.testing.TestListener
import org.gradle.api.tasks.testing.TestResult

gradle.settingsEvaluated {
    if (rootProject.name == "NativeCmpKit") {
        val securityClass = "com.mohamedrejeb.calf.ui.web.DesktopWebViewTlsRenderingAcceptanceTest"
        val securitySelector = "$securityClass.trustedHttpsPaintsTwoAuthoredDocumentsAndUntrustedCertificateFailsBeforeHttpOnTheSameOwner"
        val cookieSelector = "com.mohamedrejeb.calf.ui.web.JavaFxCookieIntegrationTest.realNativeLoginSurvivesLibraryCookieReadsAndHttpOnlyNeverLeaksIntoDocumentCookie"
        val policySelector = "com.mohamedrejeb.calf.ui.web.DesktopWebViewIdentityAcceptanceTest.actualFxTypedValuesOffMainAndThrowingOrDetachedCallbacksAreExactlyOnce"
        val mediaSelector = "com.mohamedrejeb.calf.ui.web.DesktopWebViewLifetimeTest.disposingARealWindowClosesItsSlowConnectionAndStopsTheLiveMediaDocument"
        val securityFocus = gradle.startParameter.projectProperties["nativecmpkitDesktopSecurityFocus"]
            ?: error("Security observation requires the exact explicit finite focus")
        val securitySelectors = when (securityFocus) {
            "tls-rendering" -> listOf(securitySelector)
            "tls-rendering-cookies-policy" -> listOf(securitySelector, cookieSelector, policySelector)
            "tls-rendering-cookies-policy-media" -> listOf(securitySelector, cookieSelector, policySelector, mediaSelector)
            else -> error("Unknown finite Desktop security observation focus")
        }
        val securityClasses = securitySelectors.map { it.substringBeforeLast('.') }.toSet()
        val workerName = Regex("Gradle Test Executor ([1-9][0-9]{0,8})")

        allprojects {
            tasks.withType<Test>().matching { it.path == ":calf-webview:desktopTest" }.configureEach {
                val selectedTask = this
                doFirst {
                    check(maxParallelForks == 1 && forkEvery == 1L)
                    check(systemProperties["nativecmpkit.desktop.security.worker"] == "one-selected-class")
                    check(filter.includePatterns == securitySelectors.toSet() && filter.excludePatterns.isEmpty())
                    check(filter.isFailOnNoMatchingTests)
                    logger.lifecycle("NATIVECMPKIT_DESKTOP_SECURITY_SETUP task=$path focus=$securityFocus forks=1 forkEvery=1 classes=${securityClasses.size}")
                }
                addTestListener(object : TestListener {
                    private fun worker(descriptor: TestDescriptor): String {
                        var current: TestDescriptor? = descriptor
                        repeat(16) {
                            val node = current ?: error("Selected case has no bounded public worker ancestor")
                            workerName.matchEntire(node.name)?.let { return it.groupValues[1] }
                            current = node.parent
                        }
                        error("Selected case exceeds the bounded public worker ancestry")
                    }
                    private fun counts(result: TestResult) =
                        "tests=${result.testCount} passed=${result.successfulTestCount} failed=${result.failedTestCount} skipped=${result.skippedTestCount} result=${result.resultType}"
                    override fun beforeSuite(suite: TestDescriptor) {
                        val match = workerName.matchEntire(suite.name) ?: return
                        check(suite.className == null)
                        selectedTask.logger.lifecycle("NATIVECMPKIT_DESKTOP_SECURITY_WORKER phase=start worker=${match.groupValues[1]}")
                    }
                    override fun afterSuite(suite: TestDescriptor, result: TestResult) {
                        val match = workerName.matchEntire(suite.name) ?: return
                        check(suite.className == null)
                        selectedTask.logger.lifecycle("NATIVECMPKIT_DESKTOP_SECURITY_WORKER phase=finish worker=${match.groupValues[1]} ${counts(result)}")
                    }
                    override fun beforeTest(test: TestDescriptor) {
                        check(test.className in securityClasses)
                        selectedTask.logger.lifecycle("NATIVECMPKIT_DESKTOP_SECURITY_CASE phase=start worker=${worker(test)} classname=${test.className}")
                    }
                    override fun afterTest(test: TestDescriptor, result: TestResult) {
                        check(test.className in securityClasses)
                        selectedTask.logger.lifecycle("NATIVECMPKIT_DESKTOP_SECURITY_CASE phase=finish worker=${worker(test)} classname=${test.className} ${counts(result)}")
                    }
                })
            }
        }
    }
}
