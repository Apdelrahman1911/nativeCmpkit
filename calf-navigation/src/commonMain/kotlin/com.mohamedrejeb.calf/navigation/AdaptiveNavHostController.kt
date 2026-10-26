// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.snapshots.Snapshot
import androidx.compose.runtime.snapshots.SnapshotStateList
import kotlin.random.Random

/** Compatibility factory for the independent Compose controller, not AndroidX navigation. */
@Composable
fun rememberNavController(): AdaptiveNavHostController = rememberAdaptiveNavController()

/** Explicitly named factory, distinct from the legacy platform [NavHostController] bridge. */
@Composable
fun rememberAdaptiveNavController(): AdaptiveNavHostController =
    rememberSaveable(saver = AdaptiveNavHostController.Saver()) {
        AdaptiveNavHostController()
    }

/**
 * A UI-thread-confined Compose navigation stack. It is not a native platform stack:
 * browser history, UIKit interactive back and per-entry ViewModel/lifecycle owners
 * are not provided. See docs/decisions/0004-adaptive-navigation-entries.md.
 */
class AdaptiveNavHostController {
    /**
     * Legacy route mirror; the exact getter type is retained for old consumers.
     * Direct changes are imported conservatively at the next observation. Equal
     * remove/reinsert mutations before observation cannot express a new visit;
     * use [navigate]/[popBackStack] for reliable identity, arguments and cleanup.
     */
    @Deprecated("Observe backStackEntries and use navigate/popBackStack; direct list edits cannot preserve entry identity")
    val backStack: SnapshotStateList<String> = mutableStateListOf()

    private val entries = mutableStateListOf<NavBackStackEntry>()
    private var mirroredRoutes: List<String> = emptyList()
    private var namespace: String = Random.nextLong().toString(16) + ":" + Random.nextLong().toString(16)
    private var nextSequence: Long = 0
    private var graphOwner: Any? = null
    private var graph: Map<String, NavDestination>? = null

    /** A read-only snapshot. Entries survive other visits to the same route. */
    val backStackEntries: List<NavBackStackEntry>
        get() {
            importLegacyRoutes()
            return entries.toList()
        }

    val currentBackStackEntry: NavBackStackEntry?
        get() = backStackEntries.lastOrNull()

    val currentDestination: String?
        get() = currentBackStackEntry?.route

    val canNavigateBack: Boolean
        get() = backStackEntries.size > 1

    /**
     * Compatibility value adapter: each supplied NavArgument must have an explicit
     * default, interpreted as this visit's value. Destination definitions belong
     * in the graph, not in this map. Prefer [navigateWithValues] for new callers.
     */
    fun navigate(route: String, arguments: Map<String, NavArgument> = emptyMap()) {
        navigateWithValues(route, arguments.mapValues { (name, argument) ->
            require(argument.defaultValuePresent) {
                "Navigation argument '$name' needs a value; put its schema in the graph"
            }
            argument.defaultValue
        })
    }

    /**
     * Appends a fresh entry with portable built-in values. Arrays/maps are copied.
     * If a host is attached, route and schema validation happen before mutation.
     * Otherwise they happen when a host attaches. Missing defaults are resolved
     * against the current graph; supplied values always remain entry-specific.
     */
    fun navigateWithValues(route: String, arguments: Map<String, Any?> = emptyMap()) {
        importLegacyRoutes()
        val entry = newEntry(route, arguments)
        validateEntry(entry)
        replaceEntries(entries.toList() + entry)
    }

    fun popBackStack(): Boolean {
        importLegacyRoutes()
        if (entries.size <= 1) return false
        replaceEntries(entries.toList().dropLast(1))
        return true
    }

    internal fun attachGraph(owner: Any) {
        check(graphOwner == null || graphOwner === owner) {
            "An AdaptiveNavHostController can be attached to only one host at a time"
        }
        graphOwner = owner
    }

    internal fun updateGraph(owner: Any, destinations: Map<String, NavDestination>) {
        check(graphOwner === owner) { "The navigation graph is not owned by this host" }
        backStackEntries.forEach { entry -> validateEntry(entry, destinations) }
        graph = destinations
    }

    internal fun detachGraph(owner: Any) {
        if (graphOwner === owner) {
            graphOwner = null
            graph = null
        }
    }

    private fun validateEntry(entry: NavBackStackEntry, destinations: Map<String, NavDestination>? = graph) {
        if (destinations == null) return
        val destination = requireNotNull(destinations[entry.route]) {
            "Unknown navigation route '${entry.route}'"
        }
        destination.resolveArguments(entry)
    }

    private fun newEntry(route: String, arguments: Map<String, Any?> = emptyMap()): NavBackStackEntry {
        require(route.isNotBlank()) { "A navigation route must not be blank" }
        arguments.forEach { (name, value) ->
            require(name.isNotBlank()) { "A navigation argument name must not be blank" }
            // Fail before storing an unsupported/unrestorable value, including malformed Unicode.
            portableNavType(value).serializeAsValue(value)
        }
        check(nextSequence < Long.MAX_VALUE) { "Navigation entry ID sequence exhausted" }
        return NavBackStackEntry("$namespace:${nextSequence++}", route, arguments)
    }

    @Suppress("DEPRECATION")
    private fun replaceEntries(updated: List<NavBackStackEntry>) {
        val routes = updated.map { it.route }
        Snapshot.withMutableSnapshot {
            entries.clear()
            entries.addAll(updated)
            backStack.clear()
            backStack.addAll(routes)
        }
        mirroredRoutes = routes
    }

    /** Best-effort legacy bridge; cannot infer event history from an equal list. */
    @Suppress("DEPRECATION")
    private fun importLegacyRoutes() {
        val routes = backStack.toList()
        if (routes == mirroredRoutes) return
        val previous = entries.toList()
        var commonPrefix = 0
        while (commonPrefix < minOf(previous.size, routes.size) &&
            previous[commonPrefix].route == routes[commonPrefix]
        ) commonPrefix++
        val updated = previous.take(commonPrefix) + routes.drop(commonPrefix).map { newEntry(it) }
        updated.forEach { validateEntry(it) }
        replaceEntries(updated)
    }

    internal fun saveState(): List<Any> {
        val savedEntries = backStackEntries // Import legacy edits before reading the sequence.
        return listOf(
            1, namespace, nextSequence,
            savedEntries.map { entry ->
                listOf(entry.id, entry.route, entry.arguments.map { (name, value) ->
                    val type = portableNavType(value)
                    listOf(name, type.name, type.serializeAsValue(value))
                })
            },
        )
    }

    companion object {
        fun Saver(): Saver<AdaptiveNavHostController, *> = Saver<AdaptiveNavHostController, Any>(
            save = { it.saveState() },
            restore = { restoreState(it) },
        )

        /** Returns null for a corrupt/unknown format instead of partially restoring it. */
        internal fun restoreState(saved: Any): AdaptiveNavHostController? {
            return try {
                val controller = AdaptiveNavHostController()
                if (saved is Array<*>) {
                    // Version zero saved only routes. Route-keyed UI state is not migrated.
                    require(saved.all { it is String })
                    saved.forEach { controller.navigate(it as String) }
                } else {
                    val fields = saved as? List<*> ?: return null
                    require(fields.size == 4 && fields[0] == 1)
                    controller.namespace = fields[1] as? String ?: return null
                    require(controller.namespace.isNotBlank())
                    controller.nextSequence = fields[2] as? Long ?: return null
                    require(controller.nextSequence >= 0)
                    val rows = fields[3] as? List<*> ?: return null
                    val ids = mutableSetOf<String>()
                    val restored = rows.map { row ->
                        val values = row as? List<*> ?: error("Invalid saved entry")
                        require(values.size == 3)
                        val id = values[0] as? String ?: error("Invalid saved entry ID")
                        val sequence = id.removePrefix(controller.namespace + ":").toLongOrNull()
                        require(id.startsWith(controller.namespace + ":") && sequence != null &&
                            id == "${controller.namespace}:$sequence" &&
                            sequence >= 0 && sequence < controller.nextSequence && ids.add(id))
                        val route = values[1] as? String ?: error("Invalid saved route")
                        require(route.isNotBlank())
                        val arguments = linkedMapOf<String, Any?>()
                        (values[2] as? List<*> ?: error("Invalid saved arguments")).forEach { argument ->
                            val parts = argument as? List<*> ?: error("Invalid saved argument")
                            require(parts.size == 3)
                            val name = parts[0] as? String ?: error("Invalid argument name")
                            require(name.isNotBlank() && name !in arguments)
                        val typeName = parts[1] as? String ?: error("Invalid argument type")
                        require(typeName.isNotBlank())
                            val encoded = parts[2] as? String ?: error("Invalid argument encoding")
                            arguments[name] = AdaptiveNavType.fromArgType(typeName, null).parseSerializedValue(encoded)
                        }
                        NavBackStackEntry(id, route, arguments)
                    }
                    controller.replaceEntries(restored)
                }
                controller
            } catch (_: IllegalArgumentException) {
                null
            } catch (_: IllegalStateException) {
                null
            }
        }
    }
}
