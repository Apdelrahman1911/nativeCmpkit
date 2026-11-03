// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class, kotlinx.cinterop.BetaInteropApi::class)

package com.mohamedrejeb.calf.ui.internal

import kotlinx.cinterop.ExportObjCClass
import kotlinx.cinterop.ObjCObjectBase.OverrideInit
import platform.Foundation.NSThread
import platform.UIKit.UIApplication
import platform.UIKit.UIScene
import platform.UIKit.UISceneConnectionOptions
import platform.UIKit.UISceneSession
import platform.UIKit.UIWindowScene
import platform.UIKit.UIWindowSceneDelegateProtocol
import platform.darwin.NSObject

@ExportObjCClass(name = "NativeCmpKitPopoverGeometrySceneDelegate")
class NativePopoverGeometrySceneDelegate : NSObject, UIWindowSceneDelegateProtocol {
    @OverrideInit
    constructor() : super()

    private var connected: UIWindowScene? = null

    private fun owner(): NativeUiApplicationDelegate {
        check(NSThread.isMainThread && ownedPopoverGeometryRequested())
        return checkNotNull(UIApplication.sharedApplication.delegate as? NativeUiApplicationDelegate)
    }

    override fun scene(scene: UIScene, willConnectToSession: UISceneSession, options: UISceneConnectionOptions) {
        check(NSThread.isMainThread)
        check(connected == null) { "A second scene cannot replace this test's window" }
        val windowScene = checkNotNull(scene as? UIWindowScene)
        check(sameNativeObject(windowScene.session, willConnectToSession))
        connected = windowScene // Own the binding before window creation can re-enter UIKit.
        owner().connectOwnedPopoverGeometryScene(windowScene)
    }

    override fun sceneDidBecomeActive(scene: UIScene) {
        check(NSThread.isMainThread)
        check(sameNativeObject(connected, scene)) { "Only the connected owned scene may activate generated tests" }
        owner().activateOwnedPopoverGeometryScene(checkNotNull(connected))
    }
}
