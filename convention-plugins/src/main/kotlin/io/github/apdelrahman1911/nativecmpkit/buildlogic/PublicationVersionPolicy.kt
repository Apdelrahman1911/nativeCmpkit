// NativeCmpKit build-only policy. No library API or publishing authorization.
package io.github.apdelrahman1911.nativecmpkit.buildlogic

/**
 * Deliberately constrained Maven version grammar retained from the root build.
 * Prerelease versions are supported; build metadata, paths and shell syntax are
 * not. Validation neither normalizes input nor interpolates rejected input into
 * diagnostics. A valid version is not permission to publish it.
 */
object PublicationVersionPolicy {
    private val accepted = Regex(
        "(?:0|[1-9][0-9]*)\\.(?:0|[1-9][0-9]*)\\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?",
    )

    fun isValid(version: String): Boolean = accepted.matches(version)

    fun validate(version: String): String {
        require(isValid(version)) {
            "Invalid nativeCmpkit.version; expected major.minor.patch[-prerelease] without shell/path metacharacters."
        }
        return version
    }
}
