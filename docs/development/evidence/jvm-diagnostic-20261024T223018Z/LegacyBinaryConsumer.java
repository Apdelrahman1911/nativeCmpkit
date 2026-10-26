package nativecmpkit.consumer;

import com.mohamedrejeb.calf.core.PlatformContext;
import com.mohamedrejeb.calf.cupertino.icons.CupertinoIcons;
import com.mohamedrejeb.calf.io.KmpFile;
import com.mohamedrejeb.calf.io.KmpFile_desktopKt;
import com.mohamedrejeb.calf.permissions.Permission;
import com.mohamedrejeb.calf.permissions.PermissionStatus;
import com.mohamedrejeb.calf.picker.FilePickerSelectionMode;
import com.mohamedrejeb.calf.picker.FilePickerSettings;
import com.mohamedrejeb.calf.picker.FilePickerSettingsKt;
import com.mohamedrejeb.calf.picker.ImageRepresentationMode;
import com.mohamedrejeb.calf.share.ShareContent;
import com.mohamedrejeb.calf.share.ShareResult;
import com.mohamedrejeb.calf.ui.web.Cookie;
import com.mohamedrejeb.calf.ui.web.WebContent;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

/**
 * Compile ONCE against the source-bound pre-development JARs; run the very same
 * class bytes against candidate JARs. Do not recompile against the candidate.
 *
 * These are six narrow JVM linkage cases, not a Kotlin/Native/Compose ABI or UI
 * certification. Real direct bytecode calls exercise retained owners/descriptors;
 * reflection is limited to checking runtime constants against baseline inlining.
 */
public final class LegacyBinaryConsumer {
    private static int assertions;
    private static int completedCases;

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
        assertions++;
    }

    private static void ioOwnersAndDescriptors() throws Exception {
        Path directory = Files.createTempDirectory("nativecmpkit-old-binary-");
        Path path = directory.resolve("data-資料.txt");
        try {
            Files.write(path, "same public owners".getBytes(StandardCharsets.UTF_8));
            KmpFile file = new KmpFile(path.toFile());
            check(file.getFile().equals(path.toFile()), "KmpFile constructor/getFile descriptor");
            check(KmpFile_desktopKt.exists(file, PlatformContext.INSTANCE), "exists with explicit context");
            check(!KmpFile_desktopKt.isDirectory(file, PlatformContext.INSTANCE), "regular file is not directory");
            check(KmpFile_desktopKt.getName(file, PlatformContext.INSTANCE).equals(path.getFileName().toString()), "getName owner");
            check(KmpFile_desktopKt.getPath(file, PlatformContext.INSTANCE).equals(path.toFile().getPath()), "getPath owner");
            check(KmpFile_desktopKt.toKmpFile(path.toFile()).getFile().equals(path.toFile()), "toKmpFile extension owner");
        } finally {
            Files.deleteIfExists(path);
            Files.delete(directory);
        }
        completedCases++;
    }

    private static void pickerFactoryAndDefaultInterface() {
        FilePickerSettings settings = FilePickerSettingsKt.FilePickerSettings("Export", "/caller/path", ImageRepresentationMode.Current);
        check("Export".equals(settings.getTitle()), "factory title");
        check("/caller/path".equals(settings.getInitialDirectory()), "factory directory");
        check(settings.getImageRepresentationMode() == ImageRepresentationMode.Current, "factory representation");
        check(FilePickerSettingsKt.defaultFilePickerSettings().getImageRepresentationMode() == ImageRepresentationMode.Compatible, "default factory");
        // This implementation is compiled against the OLD default interface method.
        // Adding a required abstract method must not silently break external implementors.
        FilePickerSettings custom = new FilePickerSettings() {
            @Override public String getTitle() { return "Custom"; }
            @Override public String getInitialDirectory() { return null; }
        };
        check(custom.getImageRepresentationMode() == ImageRepresentationMode.Compatible, "old interface implementor default");
        check(new FilePickerSelectionMode.Multiple(3).getMaxItems().equals(3), "multiple constructor descriptor");
        check(FilePickerSelectionMode.Multiple.Companion.getMaxItems() == null, "legacy Multiple companion inheritance");
        completedCases++;
    }

    private static void permissionsAndLegacyStatuses() {
        Permission first = new Permission("consumer-example");
        Permission same = new Permission("consumer-example");
        check(first.equals(same), "Permission equality");
        check(first.hashCode() == same.hashCode(), "Permission hash contract");
        check("consumer-example".equals(first.getName()), "Permission getter descriptor");
        PermissionStatus.Denied denied = new PermissionStatus.Denied(true);
        check(denied.getShouldShowRationale(), "Denied constructor/getter descriptor");
        check(PermissionStatus.Granted.INSTANCE instanceof PermissionStatus, "Granted legacy instance");
        completedCases++;
    }

    private static void shareConstructorsAndResults() {
        ShareContent.Text text = new ShareContent.Text("unchanged contents", "subject");
        check("unchanged contents".equals(text.getText()), "Text getter descriptor");
        check("subject".equals(text.getSubject()), "subject getter descriptor");
        check(text.equals(text.copy(text.getText(), text.getSubject())), "Text data copy");
        check(ShareResult.Success.INSTANCE instanceof ShareResult, "Success legacy instance");
        check(ShareResult.Dismissed.INSTANCE instanceof ShareResult, "Dismissed legacy instance");
        check(ShareResult.Unavailable.INSTANCE instanceof ShareResult, "Unavailable legacy instance");
        completedCases++;
    }

    private static void webValuesAndCookieConstructor() {
        WebContent.Url url = new WebContent.Url("https://example.invalid/", Map.of("X-Test", "value"));
        check("https://example.invalid/".equals(url.getUrl()), "Url getter descriptor");
        check("value".equals(url.getAdditionalHttpHeaders().get("X-Test")), "Url headers descriptor");
        Cookie cookie = new Cookie("session", "test", "example.invalid", "/", null, true, true);
        check(cookie.isSecure() && cookie.isHttpOnly(), "Cookie constructor/flags");
        check(cookie.getExpiresDate() == null, "Cookie nullable expiration");
        check("example.invalid".equals(cookie.getDomain()), "Cookie domain getter");
        completedCases++;
    }

    private static void constantsRemainEqualToBaselineInlining() throws Exception {
        check(CupertinoIcons.class.getField("house").getInt(null) == CupertinoIcons.house, "runtime house differs from old inlined constant");
        check(CupertinoIcons.class.getField("heartFill").getInt(null) == CupertinoIcons.heartFill, "runtime heartFill differs from old inlined constant");
        completedCases++;
    }

    public static void main(String[] args) throws Exception {
        ioOwnersAndDescriptors();
        pickerFactoryAndDefaultInterface();
        permissionsAndLegacyStatuses();
        shareConstructorsAndResults();
        webValuesAndCookieConstructor();
        constantsRemainEqualToBaselineInlining();
        if (completedCases != 6 || assertions != 31) throw new AssertionError("Unexpected verification count");
        System.out.println("{\"completed_cases\":" + completedCases + ",\"assertions\":" + assertions
                + ",\"kmp_abi_certified\":false,\"native_ui_exercised\":false}");
    }
}
