@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package nativecmpkit.probes

import kotlinx.cinterop.CValue
import kotlinx.cinterop.ObjCSignatureOverride
import platform.CoreGraphics.CGPoint
import platform.CoreGraphics.CGRectMake
import platform.UIKit.*

class ProtocolSuperProbe :
    UIButton(frame = CGRectMake(0.0, 0.0, 10.0, 10.0)), UIContextMenuInteractionDelegateProtocol {
    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        configurationForMenuAtLocation: CValue<CGPoint>,
    ): UIContextMenuConfiguration? = UIContextMenuConfiguration.configurationWithIdentifier(
        identifier = null, previewProvider = null, actionProvider = { menu })

    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        willDisplayMenuForConfiguration: UIContextMenuConfiguration,
        animator: UIContextMenuInteractionAnimatingProtocol?,
    ) {
        super<UIContextMenuInteractionDelegateProtocol>.contextMenuInteraction(interaction = interaction,
            willDisplayMenuForConfiguration = willDisplayMenuForConfiguration, animator = animator)
    }

    @ObjCSignatureOverride
    override fun contextMenuInteraction(
        interaction: UIContextMenuInteraction,
        willEndForConfiguration: UIContextMenuConfiguration,
        animator: UIContextMenuInteractionAnimatingProtocol?,
    ) {
        super<UIContextMenuInteractionDelegateProtocol>.contextMenuInteraction(interaction = interaction,
            willEndForConfiguration = willEndForConfiguration, animator = animator)
    }
}
