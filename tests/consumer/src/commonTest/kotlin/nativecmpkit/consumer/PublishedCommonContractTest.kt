package nativecmpkit.consumer

import com.mohamedrejeb.calf.cupertino.icons.CupertinoIcons
import com.mohamedrejeb.calf.permissions.*
import com.mohamedrejeb.calf.picker.*
import com.mohamedrejeb.calf.share.*
import com.mohamedrejeb.calf.ui.web.*
import kotlin.test.*

/** Small actual artifact-level contract tests. These do not invoke native dialogs or UI. */
@OptIn(ExperimentalPermissionsApi::class)
class PublishedCommonContractTest {
    @Test fun settingsFactoryRetainsNamesAndRepresentation() {
        val settings = FilePickerSettings("Export", "/caller/path", ImageRepresentationMode.Current)
        assertEquals("Export", settings.title)
        assertEquals("/caller/path", settings.initialDirectory)
        assertEquals(ImageRepresentationMode.Current, settings.imageRepresentationMode)
        assertEquals(ImageRepresentationMode.Compatible, defaultFilePickerSettings().imageRepresentationMode)
    }

    @Test fun multipleSelectionPreservesLegacyCompanionAndConstructor() {
        val legacy: FilePickerSelectionMode.Multiple = FilePickerSelectionMode.Multiple
        assertNull(legacy.maxItems)
        assertEquals(3, FilePickerSelectionMode.Multiple(3).maxItems)
    }

    @Test fun customFileTypesRetainMimeAndExtensionValues() {
        assertContentEquals(arrayOf("application/pdf"), FilePickerFileType.Pdf.value)
        assertContentEquals(arrayOf("image/png", "text/plain"),
            FilePickerFileType.Custom(listOf("image/png", "text/plain")).value)
        assertContentEquals(arrayOf("png", "txt"), FilePickerFileType.Extension(listOf("png", "txt")).value)
    }

    @Test fun permissionIdentityIsNameBasedAcrossArtifacts() {
        assertEquals(Permission("example"), Permission("example"))
        assertEquals(Permission("example").hashCode(), Permission("example").hashCode())
        assertNotEquals(Permission("example"), Permission("other"))
        val permissions = allModularPermissions()
        assertEquals(21, permissions.size)
        assertEquals(21, permissions.map { it.name }.toSet().size)
    }

    @Test fun legacyPermissionStatusBranchesAndRationaleRemainUsable() {
        assertTrue(PermissionStatus.Granted.isGranted)
        assertFalse(PermissionStatus.Granted.shouldShowRationale)
        assertTrue(PermissionStatus.Denied(true).isDenied)
        assertTrue(PermissionStatus.Denied(true).shouldShowRationale)
        assertEquals("denied", legacyPermissionBranch(PermissionStatus.Denied(false)))
    }

    @Test fun shareValuesAndLegacyResultsRemainUsable() {
        val text = ShareContent.Text("Keep source intact", "subject")
        assertEquals("subject", text.subject)
        assertEquals(text, text.copy())
        assertEquals("dismissed", legacyShareBranch(ShareResult.Dismissed))
        assertEquals("unavailable", legacyShareBranch(ShareResult.Unavailable))
    }

    @Test fun webContentAndCookieConstructorsRetainNamedArguments() {
        val content = WebContent.Url("https://example.invalid/", additionalHttpHeaders = mapOf("X-Test" to "value"))
        assertEquals("value", content.additionalHttpHeaders["X-Test"])
        assertEquals(content.url, legacyWebContentBranch(content))
        val cookie = Cookie("session", "test", domain = "example.invalid", path = "/", isSecure = true, isHttpOnly = true)
        assertTrue(cookie.isSecure)
        assertTrue(cookie.isHttpOnly)
        assertNull(cookie.expiresDate)
    }

    @Test fun resourceApiNamesAndCoilFactoryAreLinkable() {
        assertTrue(CupertinoIcons.house in 0..0xffff)
        assertNotEquals(CupertinoIcons.house, CupertinoIcons.heartFill)
        assertNotNull(consumeCoilFactory())
    }
}
