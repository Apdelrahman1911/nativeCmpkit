// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

/** Test-only fixed identities and independent expected RFC scopes. Never derive the oracle from production matching. */
internal object CookieWireContract {
    val groups = listOf("scope" to "root", "scope" to "foo", "scope" to "child", "host" to "host",
        "domain" to "domain", "auth" to "auth", "session" to "session", "future" to "future",
        "past" to "past", "secure" to "secure", "managed" to "managed", "equal" to "same")
    val pages = listOf("foo", "foo/child", "foobar", "private", "public")
    fun prefix(token: String): String {
        check(Regex("[0-9a-f]{32}").matches(token)) { "Missing owned cookie nonce" }
        return "nativecmpkit_${token}_"
    }
    fun rootPath(token: String) = "/nativecmpkit-cookie-wire/$token/"
    fun parseVector(text: String): List<Int> {
        check(Regex("[0-3](,[0-3]){11}").matches(text)) { "Unreviewed cookie count-vector protocol" }
        return text.split(',').map(String::toInt)
    }
    fun name(token: String, suffix: String): String {
        check(groups.any { it.first == suffix }) { "Unreviewed owned cookie identity" }
        return prefix(token) + suffix
    }
    fun vector(cookies: List<Cookie>, token: String): List<Int> {
        val prefix = prefix(token)
        val counts = MutableList(groups.size) { 0 }
        cookies.filter { it.name.startsWith(prefix) }.forEach { cookie ->
            val index = groups.indexOf(cookie.name.removePrefix(prefix) to cookie.value)
            check(index >= 0) { "Unexpected owned cookie identity/value; no raw cookie is exported" }
            counts[index]++
            check(counts[index] <= 3) { "Owned cookie multiplicity exceeded its finite budget" }
        }
        return counts
    }
    fun expected(page: String, subhost: Boolean, secure: Boolean, visibleOnly: Boolean = false,
                 managed: Boolean = false, loggedOut: Boolean = false): List<Int> {
        check(page in pages) { "Unreviewed owned cookie path" }
        if (loggedOut) return List(groups.size) { 0 }
        if (subhost) return List(groups.size) { if (it == 4) 1 else 0 }
        val underFoo = page == "foo" || page == "foo/child"
        return listOf(1, if (underFoo || page == "private") 1 else 0, if (page == "foo/child") 1 else 0,
            1, 1, if (visibleOnly) 0 else 1, 1, 1, 0, if (secure) 1 else 0,
            if (managed) 1 else 0, if (underFoo) 2 else 1)
    }
}

/** Test-only independent suspending releases. Never replace the original assertion/cancellation. */
internal suspend fun runCookieWireCleanup(primary: Throwable?, vararg stages: suspend () -> Unit) {
    kotlinx.coroutines.withContext(kotlinx.coroutines.NonCancellable) {
        var failure = primary
        stages.forEach { stage ->
            try { stage() } catch (error: Throwable) {
                val original = failure
                if (original == null) failure = error else if (original !== error) original.addSuppressed(error)
            }
        }
        failure?.let { throw it }
    }
}
