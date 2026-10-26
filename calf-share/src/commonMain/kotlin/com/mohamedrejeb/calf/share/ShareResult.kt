// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.share

import androidx.compose.runtime.Immutable

/**
 * The result of a share operation initiated by [ShareLauncher].
 */
@Immutable
sealed interface ShareResult {

    /**
     * Legacy success stage: Android chooser presented, platform completion reported, or clipboard
     * copied. This does not prove recipient delivery. Use ShareOutcome to distinguish these stages.
     */
    data object Success : ShareResult

    /**
     * The user dismissed the share sheet without sharing.
     */
    data object Dismissed : ShareResult

    /**
     * Sharing is not available on this platform or in this context.
     * No successful fallback was reported. A completed clipboard copy maps to Success.
     */
    data object Unavailable : ShareResult
}
