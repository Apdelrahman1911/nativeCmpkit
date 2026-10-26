@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package nativecmpkit.probes

import kotlinx.cinterop.ObjCSignatureOverride
import platform.CoreGraphics.CGRectMake
import platform.UIKit.*

// Isolated signature reproduction from DropDownMenuButton before binding review.
// These are real Kotlin 2.4.20 UIKit declarations, not substitute UIKit classes.
class CategoryOverrideBefore : UIButton(frame = CGRectMake(0.0, 0.0, 10.0, 10.0)) {
    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        willDisplayMenuForConfiguration: UIContextMenuConfiguration,
        animator: UIContextMenuInteractionAnimatingProtocol?,
    ) {
        super.contextMenuInteraction(interaction = interaction,
            willDisplayMenuForConfiguration = willDisplayMenuForConfiguration, animator = animator)
    }

    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        willEndForConfiguration: UIContextMenuConfiguration,
        animator: UIContextMenuInteractionAnimatingProtocol?,
    ) {
        super.contextMenuInteraction(interaction = interaction,
            willEndForConfiguration = willEndForConfiguration, animator = animator)
    }
}
