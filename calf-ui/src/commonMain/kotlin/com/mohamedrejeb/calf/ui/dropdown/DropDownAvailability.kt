package com.mohamedrejeb.calf.ui.dropdown

/** Lexicographic major/minor comparison; malformed versions fail closed to Material. */
internal fun supportsProgrammaticNativeMenu(systemVersion: String): Boolean {
    val components = systemVersion.split('.')
    val major = components.firstOrNull()?.toIntOrNull()?.takeIf { it >= 0 } ?: return false
    val minor = if (components.size > 1) components[1].toIntOrNull()?.takeIf { it >= 0 } ?: return false else 0
    return major > 17 || (major == 17 && minor >= 4)
}
