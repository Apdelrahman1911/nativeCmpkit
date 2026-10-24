// Modified for nativeCmpkit migration (2026-10-24): sample identity only.
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import com.mohamedrejeb.calf.picker.ProvideFilePickerParentWindow
import com.mohamedrejeb.calf.sample.App


fun main() {
    System.setProperty("compose.interop.blending", "true")

    application {
        Window(
            title = "nativeCmpkit",
            onCloseRequest = ::exitApplication
        ) {
            ProvideFilePickerParentWindow {
                App()
            }
        }
    }
}
