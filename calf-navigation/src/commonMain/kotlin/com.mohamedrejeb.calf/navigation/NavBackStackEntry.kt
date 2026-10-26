package com.mohamedrejeb.calf.navigation

/**
 * One visit to a destination, independent of other visits to the same [route].
 * [arguments] contains supplied values, not the destination's schema/defaults.
 * Built-in arrays are copied on insertion and access. Saved arguments are not a
 * suitable place for passwords, tokens or other secrets.
 */
class NavBackStackEntry internal constructor(
    val id: String,
    val route: String,
    arguments: Map<String, Any?>,
) {
    private val suppliedArguments = copyNavValues(arguments)

    val arguments: Map<String, Any?>
        get() = copyNavValues(suppliedArguments)
}

/** Resolves the current graph schema while retaining the legacy content callback type. */
internal fun NavDestination.resolveArguments(entry: NavBackStackEntry): Map<String, NavArgument> {
    val supplied = entry.arguments
    val missing = arguments.missingRequiredArguments { it !in supplied }
    require(missing.isEmpty()) { "Missing required arguments for route '$route': ${missing.joinToString()}" }

    val resolved = linkedMapOf<String, NavArgument>()
    arguments.forEach { (name, definition) ->
        val value = when {
            name in supplied -> supplied[name]
            definition.defaultValuePresent -> definition.defaultValue
            else -> null // A missing required/non-nullable argument was rejected above.
        }
        resolved[name] = NavArgument(
            type = definition.type,
            isNullable = definition.isNullable,
            defaultValue = value,
            defaultValuePresent = true,
        )
    }
    supplied.forEach { (name, value) ->
        if (name !in resolved) {
            resolved[name] = NavArgument.Builder()
                .setType(portableNavType(value))
                .setIsNullable(value == null)
                .setDefaultValue(value)
                .build()
        }
    }
    return resolved
}
