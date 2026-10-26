// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.navigation

import androidx.compose.runtime.Composable

class NavDestination(
    val route: String,
    arguments: Map<String, NavArgument> = emptyMap(),
    val content: @Composable (arguments: Map<String, NavArgument>) -> Unit,
) {
    /** Argument schema. The content callback receives this entry's resolved values. */
    val arguments: Map<String, NavArgument> = arguments.toMap()
}
