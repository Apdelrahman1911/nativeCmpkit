@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package nativecmpkit.probes

import kotlinx.cinterop.CValue
import kotlinx.cinterop.ObjCSignatureOverride
import platform.CoreGraphics.CGPoint
import platform.CoreGraphics.CGRectMake
import platform.UIKit.*
import platform.UIKit.contextMenuInteraction as controlContextMenuInteraction

// Protocol adoption supplies real ObjC overridable members. The alias avoids
// the inherited zero-argument contextMenuInteraction member hiding the category.
class CategoryProtocolBridgeProbe :
    UIButton(frame = CGRectMake(0.0, 0.0, 10.0, 10.0)), UIContextMenuInteractionDelegateProtocol {
    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        configurationForMenuAtLocation: CValue<CGPoint>,
    ): UIContextMenuConfiguration? = super.controlContextMenuInteraction(
        interaction = interaction, configurationForMenuAtLocation = configurationForMenuAtLocation)

    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        willDisplayMenuForConfiguration: UIContextMenuConfiguration,
        animator: UIContextMenuInteractionAnimatingProtocol?,
    ) {
        super.controlContextMenuInteraction(interaction = interaction,
            willDisplayMenuForConfiguration = willDisplayMenuForConfiguration, animator = animator)
    }

    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        willEndForConfiguration: UIContextMenuConfiguration,
        animator: UIContextMenuInteractionAnimatingProtocol?,
    ) {
        super.controlContextMenuInteraction(interaction = interaction,
            willEndForConfiguration = willEndForConfiguration, animator = animator)
    }
}
