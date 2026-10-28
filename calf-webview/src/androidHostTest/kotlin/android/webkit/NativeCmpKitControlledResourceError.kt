// Test-only package-local producer: Android's WebResourceError constructor is package-private.
// This controlled input is not a Chromium/provider response and is never part of library artifacts.
package android.webkit

internal class NativeCmpKitControlledResourceError(index: Int) : WebResourceError() {
    private val code = -(index % 16 + 1)
    private val text = "resource-$index: failure é"
    override fun getErrorCode() = code
    override fun getDescription(): CharSequence = text
}
