// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.navigation

import androidx.compose.runtime.Composable

public open class NavGraphBuilder {
    internal val destinations = mutableListOf<NavDestination>()

    /**
     * Add the destination to the [NavGraphBuilder]
     */
    public fun addDestination(destination: NavDestination) {
        require(destination.route.isNotBlank()) { "A destination route must not be blank" }
        require(destinations.none { it.route == destination.route }) {
            "Duplicate navigation route '${destination.route}'"
        }
        destinations += destination
    }

    public fun composable(
        route: String,
        arguments: Map<String, NavArgument> = emptyMap(),
        content: @Composable (arguments: Map<String, NavArgument>) -> Unit
    ) {
        addDestination(NavDestination(route, arguments, content))
    }
}
