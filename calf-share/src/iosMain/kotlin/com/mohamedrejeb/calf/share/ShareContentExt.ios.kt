// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.share

import kotlinx.cinterop.ObjCSignatureOverride
import platform.Foundation.NSURL
import platform.UIKit.UIActivityItemSourceProtocol
import platform.UIKit.UIActivityViewController
import platform.darwin.NSObject

/** Subject belongs to each activity item, not the view controller's navigation title. */
internal fun ShareContent.toActivityItems(): List<Any> {
    val items: List<Any> = when (this) {
        is ShareContent.Text -> listOf(text)
        is ShareContent.Url -> listOf(NSURL.URLWithString(url) ?: url)
        is ShareContent.File -> listOf(file.url)
        is ShareContent.Files -> files.map { it.url }
    }
    val subject = when (this) { is ShareContent.Text -> subject; is ShareContent.Url -> subject; is ShareContent.File -> subject; is ShareContent.Files -> subject }
    return if (subject == null) items else items.map { ShareActivityItemSource(it, subject) }
}

private class ShareActivityItemSource(private val item: Any, private val subject: String) : NSObject(), UIActivityItemSourceProtocol {
    override fun activityViewControllerPlaceholderItem(activityViewController: UIActivityViewController): Any = item
    @ObjCSignatureOverride
    override fun activityViewController(activityViewController: UIActivityViewController, itemForActivityType: String?): Any = item
    @ObjCSignatureOverride
    override fun activityViewController(activityViewController: UIActivityViewController, subjectForActivityType: String?): String = subject
}
