// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.navigation

import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.key
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.SaveableStateHolder
import androidx.compose.runtime.saveable.listSaver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.saveable.rememberSaveableStateHolder
import androidx.compose.ui.Modifier

/**
 * Hosts an independent Compose navigation stack. Graph closures are refreshed on
 * recomposition; changing startDestination never resets an existing stack. A new
 * graph must still cover every stacked route and validate its supplied arguments.
 */
@Composable
fun AdaptiveNavHost(
    navController: AdaptiveNavHostController,
    startDestination: String,
    modifier: Modifier = Modifier,
    builder: NavGraphBuilder.() -> Unit
) {
    // Do not remember the builder lambda: it may close over a replacement controller
    // or callback. Entry identity, not graph object identity, owns saved UI state.
    val graph = NavGraphBuilder().apply(builder).destinations.associateBy { it.route }
    require(startDestination in graph) { "Unknown start destination '$startDestination'" }
    val entries = navController.backStackEntries
    entries.forEach { entry ->
        requireNotNull(graph[entry.route]) { "Unknown navigation route '${entry.route}'" }
            .resolveArguments(entry)
    }

    val graphOwner = remember { Any() }
    DisposableEffect(navController) {
        navController.attachGraph(graphOwner)
        onDispose { navController.detachGraph(graphOwner) }
    }
    SideEffect { navController.updateGraph(graphOwner, graph) }

    AndroidBackHandler(enabled = entries.size > 1) { navController.popBackStack() }

    LaunchedEffect(navController, startDestination) {
        if (navController.currentBackStackEntry == null) navController.navigate(startDestination)
    }

    val saveableStateHolder = rememberSaveableStateHolder()
    ForgetPoppedEntries(entries.map { it.id }.toSet(), saveableStateHolder)

    Box(modifier = modifier) {
        entries.lastOrNull()?.let { entry ->
            val destination = graph.getValue(entry.route)
            key(entry.id) {
                saveableStateHolder.SaveableStateProvider(key = entry.id) {
                    destination.content(destination.resolveArguments(entry))
                }
            }
        }
    }
}

/** Drops state only for removed visits, including same-frame pop/revisit. */
@Composable
private fun ForgetPoppedEntries(entryIds: Set<String>, saveableStateHolder: SaveableStateHolder) {
    // Persist the known IDs as well, so cleanup still works after host state restoration.
    val retainedIds = rememberSaveable(
        saver = listSaver<MutableSet<String>, String>(
            save = { it.toList() },
            restore = { it.toMutableSet() },
        )
    ) { mutableSetOf<String>() }

    SideEffect {
        (retainedIds - entryIds).forEach(saveableStateHolder::removeState)
        retainedIds.clear()
        retainedIds.addAll(entryIds)
    }
}
