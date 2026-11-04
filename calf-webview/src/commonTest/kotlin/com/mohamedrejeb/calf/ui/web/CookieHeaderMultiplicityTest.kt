// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** NEW missing-only cookie identities; no browser/native-header behavior is inferred from these controls. */
class CookieHeaderMultiplicityTest {
    @Test fun requestCookieParsingRetainsDuplicateNamesAndEqualValues() {
        val parsed = parseCookieHeader("scope=root; scope=child; scope=child; encoded=a=b; \$Path=/")
        assertEquals(listOf("scope" to "root", "scope" to "child", "scope" to "child", "encoded" to "a=b"),
            parsed.map { it.name to it.value })
        assertEquals(3, parsed.count { it.name == "scope" }, "A map keyed by name silently drops native occurrences")
    }

    @Test fun nestedPathAndDomainScopeStillApplyToDuplicateCookieIdentities() {
        for ((path, expected) in listOf("/foo" to true, "/foo/child" to true, "/foobar" to false, "/public" to false)) {
            assertEquals(expected, cookieMatchesRequest("owner.example.test", path, true,
                "owner.example.test", "/foo", false, true))
        }
        for ((path, expected) in listOf("/private" to true, "/private/child" to true, "/private-extra" to false, "/public" to false)) {
            assertEquals(expected, cookieMatchesRequest("owner.example.test", path, true,
                "owner.example.test", "/private", false, true))
        }
        assertTrue(cookieMatchesRequest("sub.owner.example.test", "/foo", true,
            ".owner.example.test", "/foo", true, false))
        assertFalse(cookieMatchesRequest("sub.owner.example.test", "/foo", true,
            "owner.example.test", "/foo", false, true))
        assertFalse(cookieMatchesRequest("notowner.example.test", "/foo", true,
            ".owner.example.test", "/foo", false, false))
        assertFalse(cookieMatchesRequest("owner.example.test", "/foo", false,
            ".owner.example.test", "/foo", true, false))
    }
}
