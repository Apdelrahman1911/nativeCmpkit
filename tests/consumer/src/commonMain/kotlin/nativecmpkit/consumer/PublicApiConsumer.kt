package nativecmpkit.consumer

import androidx.compose.runtime.Composable
import coil3.fetch.Fetcher
import com.mohamedrejeb.calf.camerapicker.rememberCameraPickerLauncher
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import com.mohamedrejeb.calf.core.PlatformContext
import com.mohamedrejeb.calf.cupertino.icons.CupertinoIcon
import com.mohamedrejeb.calf.cupertino.icons.CupertinoIcons
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.source
import com.mohamedrejeb.calf.permissions.*
import com.mohamedrejeb.calf.picker.*
import com.mohamedrejeb.calf.picker.coil.KmpFileFetcher
import com.mohamedrejeb.calf.share.*
import com.mohamedrejeb.calf.ui.progress.AdaptiveCircularProgressIndicator
import com.mohamedrejeb.calf.ui.toggle.AdaptiveSwitch
import com.mohamedrejeb.calf.ui.web.*
import kotlinx.io.RawSource

/**
 * Compiled against Maven/KLIB artifacts, never the producer source tree. This is a SOURCE
 * compatibility probe, not a claim that calling it rendered/presented every native control.
 */
@OptIn(ExperimentalCalfApi::class, ExperimentalPermissionsApi::class)
@Composable
fun PublicApiConsumer(onFile: (KmpFile) -> Unit) {
    AdaptiveSwitch(checked = false, onCheckedChange = null)
    AdaptiveCircularProgressIndicator()
    CupertinoIcon(CupertinoIcons.house, contentDescription = "Home")
    rememberFilePickerLauncher(onResult = { it.firstOrNull()?.let(onFile) })
    rememberFileSaverLauncher(onResult = { it?.let(onFile) })
    rememberCameraPickerLauncher(onResult = onFile)
    rememberShareLauncher(onResult = {})
    rememberPermissionState(Permission.Camera)
    WebView(rememberWebViewState("about:blank"))
}

// Public RawSource must be consumable via the IO artifact's API dependency.
suspend fun consumeStream(file: KmpFile, context: PlatformContext): RawSource = file.source(context)
fun consumeCoilFactory(): Fetcher.Factory<KmpFile> = KmpFileFetcher.Factory()

fun allModularPermissions(): List<Permission> = listOf(
    Permission.Camera, Permission.Gallery, Permission.ReadImage, Permission.ReadVideo,
    Permission.FineLocation, Permission.CoarseLocation, Permission.BackgroundLocation,
    Permission.BluetoothLe, Permission.BluetoothScan, Permission.BluetoothConnect, Permission.BluetoothAdvertise,
    Permission.ReadContacts, Permission.WriteContacts, Permission.ReadCalendar, Permission.WriteCalendar,
    Permission.Notification, Permission.RemoteNotification, Permission.WifiAccessState,
    Permission.WifiChangeState, Permission.WifiNearbyDevices, Permission.RecordAudio,
)

// Adding cases to these legacy sealed types is a source break for real exhaustive consumers.
@OptIn(ExperimentalPermissionsApi::class)
fun legacyPermissionBranch(status: PermissionStatus): String = when (status) {
    PermissionStatus.Granted -> "granted"
    is PermissionStatus.Denied -> "denied"
}

fun legacyShareBranch(result: ShareResult): String = when (result) {
    ShareResult.Success -> "success"
    ShareResult.Dismissed -> "dismissed"
    ShareResult.Unavailable -> "unavailable"
}

fun legacyWebContentBranch(content: WebContent): String = when (content) {
    is WebContent.Url -> content.url
    is WebContent.Data -> content.data
    WebContent.NavigatorOnly -> "navigator-only"
}
