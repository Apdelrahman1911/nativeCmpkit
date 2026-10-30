// SPDX-License-Identifier: Apache-2.0
package nativecmpkit.consumer.unpublished

import android.content.Context
import androidx.fragment.app.FragmentManager
import androidx.lifecycle.Lifecycle
import com.google.android.gms.location.LocationResult
import com.mohamedrejeb.calf.geo.LocationTracker

/** Retained Android signatures must typecheck through the library's API dependencies. */
@Suppress("DEPRECATION")
fun consumeAndroidBindings(
    tracker: LocationTracker,
    lifecycle: Lifecycle,
    context: Context,
    fragments: FragmentManager,
    result: LocationResult,
) {
    tracker.bind(lifecycle, context, fragments)
    tracker.bind(lifecycle, context)
    tracker.onLocationResult(result)
    tracker.unbind()
}
