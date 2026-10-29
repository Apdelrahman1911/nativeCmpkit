package io.github.apdelrahman1911.nativecmpkit.buildlogic

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Executable owning build-policy tests; no shell, credentials or remote publication. */
class PublicationVersionPolicyTest {
    @Test
    fun acceptedStableSnapshotAndPreviewVersionsKeepTheirExactBytes() {
        val accepted = listOf(
            "0.0.0", "0.1.0", "1.2.3", "123.456.789", "0.1.0-SNAPSHOT",
            "0.1.0-preview.1", "1.2.3-alpha-beta.2", "1.2.3-rc.42",
        )
        accepted.forEach { version ->
            assertTrue(version, PublicationVersionPolicy.isValid(version))
            assertEquals(version, PublicationVersionPolicy.validate(version))
        }
    }

    @Test
    fun commandSubstitutionQuotesNewlinesSedDelimitersAndBranchPathsAreRejected() {
        val rejected = listOf(
            "", " ", "1.2.3\n", "1.2.3\r\n", "1.2.3\t", " 1.2.3", "1.2.3 ",
            "\$(touch marker)", "1.2.3-\$(touch marker)", "1.2.3-`touch marker`",
            "1.2.3';touch marker;'", "1.2.3\";touch marker;\"", "1.2.3;touch marker",
            "1.2.3/../../main", "../1.2.3", "1.2.3\\..\\main", "1.2.3|marker",
            "1.2.3&marker", "1.2.3:marker", "1.2.3#marker", "1.2.3%marker",
            "1.2.3\u0000marker", "1.2.3\u2028marker", "1.2.3\u2029marker",
        )
        rejected.forEach { version -> assertFalse(PublicationVersionPolicy.isValid(version)) }
    }

    @Test
    fun malformedVersionComponentsAndUndocumentedMetadataAreRejected() {
        listOf(
            "01.2.3", "1.02.3", "1.2.03", "1.2", "1.2.3.4", "v1.2.3",
            "1..3", "1.2.3-", "1.2.3-alpha..1", "1.2.3-alpha/1", "1.2.3+build.1",
        ).forEach { version -> assertFalse(PublicationVersionPolicy.isValid(version)) }
    }

    @Test
    fun rejectedInputNeverReachesDiagnosticsAndCannotChangeSubsequentValidation() {
        val secretLikeSentinel = "1.2.3-\$(synthetic-private-input)\n"
        val failure = try {
            PublicationVersionPolicy.validate(secretLikeSentinel)
            throw AssertionError("Unsafe version must fail before publication configuration")
        } catch (expected: IllegalArgumentException) {
            expected
        }
        assertFalse(failure.message.orEmpty().contains(secretLikeSentinel))
        assertFalse(failure.message.orEmpty().contains("synthetic-private-input"))
        assertEquals("0.1.0-preview.1", PublicationVersionPolicy.validate("0.1.0-preview.1"))
    }
}
