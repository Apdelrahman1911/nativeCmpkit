@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.picker.internal.*
import platform.Foundation.NSData
import platform.Foundation.NSFileManager
import platform.PhotosUI.PHPickerConfigurationAssetRepresentationModeCompatible
import platform.PhotosUI.PHPickerConfigurationAssetRepresentationModeCurrent
import platform.PhotosUI.PHPickerViewController
import platform.UIKit.UIDocumentPickerViewController
import platform.UIKit.UIViewController
import kotlin.test.*

/** Real UIKit animation/admission and public Compose launchers. No cloud selection/gesture claims. */
class IosPickerRuntimeOwnershipTest {
    @Test fun actualAttachedCompetingAndDetachedPresentersCannotReplaceAnotherNativeOwner() = runApplicationUiTest {
        setContent {}
        val owned = IosDialogSession()
        val refused = IosDialogSession()
        try {
            runOnIdle {
                val parent = assertNotNull(requireOwnedApplicationWindow().rootViewController)
                refused.controller = UIViewController()
                assertFailsWith<IllegalStateException> { presentIosDialog(UIViewController(), refused) }
                assertEquals(IosDialogPhase.Prepared, refused.phase)
                owned.controller = UIViewController()
                presentIosDialog(parent, owned)
            }
            waitForNative { owned.phase == IosDialogPhase.Presented }
            runOnIdle {
                val parent = assertNotNull(requireOwnedApplicationWindow().rootViewController)
                assertTrue(sameNativeObject(parent.presentedViewController, owned.controller))
                assertFailsWith<IllegalStateException> { presentIosDialog(parent, refused) }
                assertEquals(IosDialogPhase.Prepared, refused.phase)
                assertTrue(sameNativeObject(parent.presentedViewController, owned.controller))
                owned.cancel()
            }
            waitForNative { owned.phase == IosDialogPhase.Finished }
        } finally { onApplicationMain { owned.cancel(); refused.cancel() } }
    }

    @Test fun cancellationDuringRealExportPresentationWaitsForNativeCompletionBeforeRemovingStaging() = runApplicationUiTest {
        setContent {}
        val source = assertNotNull(stageExportData(NSData(), "preserved-original.bin"))
        val staged = assertNotNull(stageExportFile(source, "requested-export.bin"))
        val session = IosDialogSession()
        var cleanups = 0
        var completions = 0
        lateinit var picker: UIDocumentPickerViewController
        try {
            runOnIdle {
                picker = UIDocumentPickerViewController(forExportingURLs = listOf(staged), asCopy = true)
                session.controller = picker
                session.cleanup = { cleanups++; assertTrue(removeStaging(staged)) }
                session.onFinished = { completions++ }
                val parent = assertNotNull(requireOwnedApplicationWindow().rootViewController)
                presentIosDialog(parent, session)
                assertEquals(IosDialogPhase.Presenting, session.phase, "Observe actual animated presentation, not a manually assigned phase")
                assertTrue(picker.isBeingPresented())
                session.cancel()
                assertTrue(NSFileManager.defaultManager.fileExistsAtPath(staged.path!!))
                assertEquals(0, cleanups)
                assertEquals(0, completions)
            }
            waitForNative { session.phase == IosDialogPhase.Finished && picker.presentingViewController == null }
            runOnIdle {
                assertEquals(1, cleanups)
                assertEquals(1, completions)
                assertFalse(NSFileManager.defaultManager.fileExistsAtPath(staged.path!!))
                assertTrue(NSFileManager.defaultManager.fileExistsAtPath(source.path!!))
                assertNull(session.controller)
                session.cancel()
                assertEquals(1, cleanups)
            }
        } finally {
            onApplicationMain {
                session.cancel()
                // A failed waiter is not native ownership completion. Never
                // delete a file that an attached export controller may still use.
                if (session.phase == IosDialogPhase.Finished) removeStaging(staged)
            }
            removeStaging(source)
        }
    }

    @Test fun retainedPublicPhotoLauncherUsesFourNativeConfigurationSnapshotsAndCurrentCallback() = runApplicationUiTest {
        val limits = listOf(2, 5, null, 1)
        val mode = mutableStateOf(FilePickerSelectionMode.Multiple(limits.first()))
        val representation = mutableStateOf(ImageRepresentationMode.Compatible)
        val callbackVersion = mutableStateOf(0)
        val deliveries = mutableListOf<Int>()
        val failures = mutableListOf<FilePickerException>()
        lateinit var parent: UIViewController
        lateinit var launcher: FilePickerLauncher
        setContent {
            parent = LocalUIViewController.current
            val version = callbackVersion.value
            val current = rememberFilePickerLauncher(FilePickerFileType.Image, mode.value,
                FilePickerSettings(imageRepresentationMode = representation.value),
                onError = { failures += it }, onResult = { deliveries += version })
            SideEffect { launcher = current }
        }
        waitForIdle()
        val retained = runOnIdle { launcher }
        for ((index, limit) in limits.withIndex()) {
            val requested = if (index % 2 == 0) ImageRepresentationMode.Compatible else ImageRepresentationMode.Current
            runOnIdle { mode.value = FilePickerSelectionMode.Multiple(limit); representation.value = requested }
            waitForIdle()
            runOnIdle { assertSame(retained, launcher); retained.launch() }
            waitForNative { parent.presentedViewController is PHPickerViewController && !parent.presentedViewController!!.isBeingPresented() }
            val picker = runOnIdle { assertIs<PHPickerViewController>(parent.presentedViewController) }
            runOnIdle {
                assertEquals(limit?.toLong() ?: 0L, picker.configuration.selectionLimit)
                assertEquals(if (requested == ImageRepresentationMode.Compatible) PHPickerConfigurationAssetRepresentationModeCompatible
                    else PHPickerConfigurationAssetRepresentationModeCurrent, picker.configuration.preferredAssetRepresentationMode)
                callbackVersion.value = index + 1
                mode.value = FilePickerSelectionMode.Multiple(7)
                representation.value = if (requested == ImageRepresentationMode.Compatible) ImageRepresentationMode.Current else ImageRepresentationMode.Compatible
            }
            waitForIdle()
            runOnIdle {
                assertSame(retained, launcher)
                assertTrue(sameNativeObject(picker, parent.presentedViewController))
                assertEquals(limit?.toLong() ?: 0L, picker.configuration.selectionLimit, "Live recomposition must not mutate an already shown native configuration")
                // Controlled terminal input on the real delegate/controller, not
                // a simulated user gesture or a claim about real asset providers.
                val delegate = assertNotNull(picker.delegate)
                delegate.picker(picker, emptyList<Any>())
                delegate.picker(picker, emptyList<Any>())
            }
            waitForNative { parent.presentedViewController == null && deliveries.size == index + 1 }
            runOnIdle { assertTrue(failures.isEmpty()); assertEquals((1..index + 1).toList(), deliveries) }
        }
    }
}
