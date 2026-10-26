// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.navigation

/**
 * Legacy platform bridge: Android uses AndroidX's controller, other targets alias
 * [AdaptiveNavHostController]. It is not interchangeable with the independent
 * adaptive controller on Android. New adaptive hosts should use
 * [rememberAdaptiveNavController]; native/browser navigation is not implied.
 */
expect class NavHostController

expect fun NavHostController.navigate(route: String)

expect fun NavHostController.popBackStack(): Boolean
