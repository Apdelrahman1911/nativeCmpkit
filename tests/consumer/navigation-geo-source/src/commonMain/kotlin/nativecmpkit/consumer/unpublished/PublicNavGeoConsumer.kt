// SPDX-License-Identifier: Apache-2.0
package nativecmpkit.consumer.unpublished

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.remember
import com.mohamedrejeb.calf.geo.LocationStartResult
import com.mohamedrejeb.calf.geo.LocationTracker
import com.mohamedrejeb.calf.geo.LocationTrackingSnapshot
import com.mohamedrejeb.calf.geo.createLocationTracker
import com.mohamedrejeb.calf.navigation.AdaptiveNavHost
import com.mohamedrejeb.calf.navigation.AdaptiveNavHostController
import com.mohamedrejeb.calf.navigation.NavHostController
import com.mohamedrejeb.calf.navigation.navigate as navigatePlatformBridge
import com.mohamedrejeb.calf.navigation.popBackStack as popPlatformBridge
import com.mohamedrejeb.calf.navigation.rememberAdaptiveNavController
import com.mohamedrejeb.calf.navigation.rememberNavController

/** Both factory identities remain adaptive on every target, unlike the legacy bridge. */
@Composable
fun PublicNavGeoHost(onOwners: (AdaptiveNavHostController, AdaptiveNavHostController, LocationTracker) -> Unit) {
    val explicit: AdaptiveNavHostController = rememberAdaptiveNavController()
    val compatibility: AdaptiveNavHostController = rememberNavController()
    val tracker: LocationTracker = remember { createLocationTracker() }
    DisposableEffect(tracker) { onDispose { tracker.close() } }
    SideEffect { onOwners(explicit, compatibility, tracker) }
    AdaptiveNavHost(explicit, startDestination = "home") {
        composable("home") { /* Public host/schema callback, no sample substitute. */ }
        composable("detail") { arguments -> require(arguments.isEmpty()) }
    }
}

/** Public expect/actual receiver must compile without declaring AndroidX separately. */
fun consumeLegacyBridge(controller: NavHostController): Boolean {
    controller.navigatePlatformBridge("detail")
    return controller.popPlatformBridge()
}

/** Unbound Android is not success; all other declared targets are explicitly unsupported. */
suspend fun consumeLocationResult(tracker: LocationTracker): Pair<LocationStartResult, LocationTrackingSnapshot> =
    tracker.startTrackingWithResult() to tracker.snapshotState.value

fun consumeLegacyNoFixView(tracker: LocationTracker): Boolean =
    tracker.fixState.value == null && tracker.locationState.value.latitude.isNaN() &&
        tracker.locationState.value.longitude.isNaN()
