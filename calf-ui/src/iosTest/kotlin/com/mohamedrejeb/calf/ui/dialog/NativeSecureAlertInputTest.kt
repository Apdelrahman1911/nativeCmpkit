// SPDX-License-Identifier: Apache-2.0
// Modified for NativeCmpKit (2026-11-01): genuine native typed input, masked pixels and private bounded capture.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi::class)

package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.sample.alertinput.sampleAlertDialogInputFields
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosAction
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosActionStyle
import com.mohamedrejeb.calf.ui.dialog.uikit.AlertDialogIosProperties
import com.mohamedrejeb.calf.ui.internal.NativeApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.onApplicationMain
import com.mohamedrejeb.calf.ui.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import kotlinx.cinterop.UByteVar
import kotlinx.cinterop.convert
import kotlinx.cinterop.get
import kotlinx.cinterop.reinterpret
import kotlinx.cinterop.useContents
import platform.CoreGraphics.*
import platform.Foundation.NSNotificationCenter
import platform.Foundation.NSOperationQueue
import platform.Foundation.NSThread
import platform.Foundation.NSValue
import platform.UIKit.*
import platform.darwin.NSObjectProtocol
import kotlin.test.Test
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/**
 * Runs public NativeCmpKit dialog composition in the genuine owned UIKit app.
 * UIKeyInput.insertText and native keyboard notifications are not hardware/XCUI
 * key taps. Blurred native hierarchy pixels verify masking at rest, not an OCR
 * assumption, isolated layer fallback, password storage or clipboard policy.
 */
class NativeSecureAlertInputTest {
    @Test fun syntheticNativeInputKeepsRequestedKeyboardMaskedPixelsAndNoCapturedConsoleValues() {
        // Public deterministic probes only. Never accept an owner password,
        // environment input, CLI string, log dump or remotely supplied value.
        val secretProbes = listOf("273946158204", "864105927351")
        val nameProbes = listOf("ExampleAlpha", "ExampleBravo")
        val capture = captureOwnedNativeConsole {
            runApplicationUiTest {
                var presenter: UIViewController? = null
                var showing by mutableStateOf(true)
                var dismissals = 0
                val originals = sampleAlertDialogInputFields()
                check(originals.size == 2)
                val deliveries = originals.map { Delivery(it.onValueChange) }
                val descriptors = originals.mapIndexed { index, field ->
                    field.copy(onValueChange = { value -> deliveries[index].changed(value) })
                }
                val properties = AlertDialogIosProperties(
                    title = "Owned secure input regression",
                    animated = false,
                    actions = listOf(AlertDialogIosAction("Finish", AlertDialogIosActionStyle.Default, { showing = false })),
                    textFields = descriptors,
                )
                val keyboard = KeyboardWitness()
                var primaryFailure: Throwable? = null
                try {
                    runOnIdle { keyboard.start() }
                    setContent {
                        presenter = LocalUIViewController.current
                        if (showing) AdaptiveBasicAlertDialog(
                            onDismissRequest = { dismissals++; showing = false },
                            iosProperties = properties,
                            materialContent = {},
                        )
                    }
                    waitForNative { presenter?.presentedViewController is UIAlertController }
                    val parent = runOnIdle { checkNotNull(presenter) { "The owned native presenter was not composed" } }
                    lateinit var plain: UITextField
                    lateinit var secure: UITextField
                    runOnIdle {
                        val controller = assertNotNull(parent.presentedViewController as? UIAlertController)
                        val fields = assertNotNull(controller.textFields)
                        check(fields.size == 2) { "The actual native dialog must contain the two approved descriptor fields" }
                        plain = fields[0] as UITextField
                        secure = fields[1] as UITextField
                        check(plain.keyboardType == UIKeyboardTypeEmailAddress && !plain.isSecureTextEntry()) {
                            "The unchanged nonsecure example keyboard must reach the native field"
                        }
                        check(secure.keyboardType == UIKeyboardTypeNumberPad && secure.isSecureTextEntry()) {
                            "The unchanged secure example keyboard/secure-entry policy must reach UIKit"
                        }
                        check(plain.placeholder == originals[0].placeholder && secure.placeholder == originals[1].placeholder) {
                            "Actual native fields must preserve the unchanged sample descriptor placeholders"
                        }
                        check(plain.text == "John Doe" && secure.text.orEmpty().isEmpty()) {
                            "Native construction must retain the original harmless name and empty password"
                        }
                        requireAttached(plain, parent); requireAttached(secure, parent)
                    }
                    // An actual blank-field negative control rules out both a
                    // reused blank image and mere disappearance of the placeholder.
                    // Temporarily hide only this owned field's placeholder, never
                    // change descriptor/callback bytes or set the native text.
                    blurOwnedFields(parent, keyboard)
                    val emptySecure = runOnIdle {
                        val retainedPlaceholder = secure.placeholder
                        try {
                            secure.placeholder = null
                            nativePixels(secure, parent)
                        } finally { secure.placeholder = retainedPlaceholder }
                    }
                    val securePixels = secretProbes.map { probe ->
                        typeNative(secure, probe, deliveries[1], parent, keyboard)
                        blurOwnedFields(parent, keyboard)
                        runOnIdle {
                            check(secure.isSecureTextEntry() && secure.keyboardType == UIKeyboardTypeNumberPad)
                            nativePixels(secure, parent)
                        }
                    }
                    val plainPixels = nameProbes.map { probe ->
                        typeNative(plain, probe, deliveries[0], parent, keyboard)
                        blurOwnedFields(parent, keyboard)
                        runOnIdle { nativePixels(plain, parent) }
                    }
                    check(securePixels[0].contentEquals(securePixels[1])) {
                        "Equal-length distinct synthetic inputs must produce the same blurred native secure rendering"
                    }
                    check(!securePixels[0].contentEquals(emptySecure) && !securePixels[1].contentEquals(emptySecure)) {
                        "The secure field must actually render nonempty input, not a blank image or vanished placeholder"
                    }
                    check(!plainPixels[0].contentEquals(plainPixels[1])) {
                        "The actual nonsecure field must distinguish the rendered positive-control inputs"
                    }
                    runOnIdle {
                        deliveries.forEach { it.requireHealthy() }
                        check(deliveries.all { it.edits > 0 && it.matched }) {
                            "Genuine native editing must reach each actual sample callback"
                        }
                        showing = false
                    }
                    waitForNative { parent.presentedViewController == null && secure.window == null && plain.window == null }
                    runOnIdle { check(dismissals == 0) { "Removing composition is not a semantic native dismissal" } }
                } catch (failure: Throwable) {
                    primaryFailure = failure
                    throw failure
                } finally {
                    // Independent teardown stages preserve the original failure.
                    // A missing presenter cannot dereference lateinit state; even
                    // a failed idle check cannot skip Main-confined observer release.
                    var teardownFailure: Throwable? = null
                    fun teardown(action: () -> Unit) {
                        try { action() } catch (failure: Throwable) {
                            val prior = teardownFailure
                            if (prior == null) teardownFailure = failure
                            else if (prior !== failure) prior.addSuppressed(failure)
                        }
                    }
                    teardown { setContent {} }
                    teardown { waitForIdle() }
                    teardown { waitForNative { presenter?.presentedViewController == null } }
                    teardown { onApplicationMain { keyboard.close() } }
                    teardownFailure?.let { failure ->
                        val prior = primaryFailure
                        if (prior == null) throw failure else if (prior !== failure) prior.addSuppressed(failure)
                    }
                    // runApplicationUiTest then independently restores its root.
                }
            }
        }
        // The original native failure is reported only AFTER exact console restore.
        // Never put either expected or actual input into assertion diagnostics.
        capture.result.getOrThrow()
        for (probe in secretProbes + nameProbes) {
            val bytes = probe.encodeToByteArray()
            assertTrue(!capture.stdoutBytes.containsExactBytes(bytes), "Synthetic input bytes were present in captured native stdout")
            assertTrue(!capture.stderrBytes.containsExactBytes(bytes), "Synthetic input bytes were present in captured native stderr")
        }
    }

    private class Delivery(private val original: (String) -> Unit) {
        var expected = ""
        var matched = false
        var edits = 0
        private var offMain = false
        private var callbackFailure: Throwable? = null
        fun changed(value: String) {
            // Never throw an assertion across the Objective-C EditingChanged
            // boundary. The normal worker/main callsite checks these facts later.
            if (!NSThread.isMainThread) { offMain = true; return }
            try { original(value) } catch (failure: Throwable) { callbackFailure = failure; return }
            // Exact extracted callback used by the real sample, not a replacement no-op.
            edits++
            if (value == expected) matched = true
        }
        fun requireHealthy() {
            check(!offMain) { "Native editing callbacks must run on Main" }
            callbackFailure?.let { throw it }
        }
    }

    private class KeyboardWitness {
        private val tokens = mutableListOf<NSObjectProtocol>()
        var visible = false
        var visibleEpoch = 0
        var requestedField: UITextField? = null
        var witnessedField: UITextField? = null
        private var observationFailure: Throwable? = null
        private fun observe(action: () -> Unit) {
            try { action() } catch (failure: Throwable) {
                if (observationFailure == null) observationFailure = failure
            }
        }
        fun requireHealthy() { observationFailure?.let { throw it } }
        fun start() {
            check(NSThread.isMainThread) { "Keyboard observers must be owned on the application Main thread" }
            val center = NSNotificationCenter.defaultCenter
            tokens += center.addObserverForName(UIKeyboardDidShowNotification, null, NSOperationQueue.mainQueue) { note ->
                observe {
                    check(NSThread.isMainThread)
                    val value = note?.userInfo?.get(UIKeyboardFrameEndUserInfoKey) as? NSValue
                    if (value != null) {
                        val window = requireOwnedApplicationWindow()
                        val frame = window.convertRect(value.CGRectValue(), fromWindow = null)
                        val positive = frame.useContents { size.width > 0.0 && size.height > 0.0 }
                        if (positive && CGRectIntersectsRect(window.bounds, frame)) {
                            // Initial UIKit autofocus is real keyboard state too;
                            // never hide it merely because no test field is requested.
                            visible = true; visibleEpoch++
                            witnessedField = requestedField?.takeIf {
                                it.isFirstResponder() && sameNativeObject(it.window, window)
                            }
                        }
                    }
                }
            }
            tokens += center.addObserverForName(UIKeyboardDidHideNotification, null, NSOperationQueue.mainQueue) {
                observe {
                    check(NSThread.isMainThread)
                    visible = false; witnessedField = null
                }
            }
        }
        fun close() {
            check(NSThread.isMainThread)
            val center = NSNotificationCenter.defaultCenter
            tokens.forEach { center.removeObserver(it) }
            tokens.clear(); requestedField = null; witnessedField = null
        }
    }

    private fun NativeApplicationUiTest.blurOwnedFields(parent: UIViewController, keyboard: KeyboardWitness) {
        runOnIdle {
            keyboard.requireHealthy()
            val controller = checkNotNull(parent.presentedViewController as? UIAlertController)
            controller.view.endEditing(true) // The alert, not merely the Compose root, owns the responders.
        }
        waitForNative {
            keyboard.requireHealthy()
            !keyboard.visible && (parent.presentedViewController as? UIAlertController)?.textFields
                ?.filterIsInstance<UITextField>()?.none { it.isFirstResponder() } == true
        }
    }

    private fun NativeApplicationUiTest.typeNative(
        field: UITextField, probe: String, delivery: Delivery, parent: UIViewController, keyboard: KeyboardWitness,
    ) {
        val beforeEpoch = runOnIdle {
            requireAttached(field, parent)
            keyboard.requestedField = field
            keyboard.witnessedField = null
            val before = keyboard.visibleEpoch
            check(field.becomeFirstResponder()) { "The actual owned native field must accept first responder" }
            before
        }
        waitForNative {
            keyboard.requireHealthy()
            field.isFirstResponder() && keyboard.visible && keyboard.visibleEpoch > beforeEpoch &&
                sameNativeObject(keyboard.witnessedField, field)
        }
        runOnIdle {
            requireAttached(field, parent)
            delivery.expected = probe; delivery.matched = false
            val beforeEdits = delivery.edits
            field.selectedTextRange = field.textRangeFromPosition(field.beginningOfDocument, field.endOfDocument)
            field.deleteBackward()
            // UIKeyInput is the genuine UIKit editing path. Do not set field.text,
            // manually emit EditingChanged, call a sample callback or fake a key tap.
            probe.forEach { character -> field.insertText(character.toString()) }
            delivery.requireHealthy()
            check(field.text == probe && delivery.edits > beforeEdits && delivery.matched) {
                "Native input must update the actual field and deliver the typed synthetic value"
            }
        }
    }

    private fun requireAttached(field: UITextField, parent: UIViewController) {
        check(NSThread.isMainThread)
        val window = requireOwnedApplicationWindow()
        check(sameNativeObject(parent.view.window, window) && sameNativeObject(field.window, window) &&
            parent.presentedViewController is UIAlertController && !field.hidden && field.alpha > 0.0) {
            "Masking evidence must belong to the visible attached native alert field"
        }
    }

    private fun nativePixels(field: UITextField, parent: UIViewController): ByteArray {
        requireAttached(field, parent)
        check(!field.isFirstResponder()) { "Capture masking at rest without a transient last-character reveal or caret" }
        field.layoutIfNeeded()
        val scale = assertNotNull(field.window).screen.scale
        check(scale.isFinite() && scale > 0.0) { "Actual native pixel scale must be finite and positive" }
        val nativeSize = field.bounds.useContents { CGSizeMake(this.size.width, this.size.height) }
        nativeSize.useContents {
            check(width.isFinite() && height.isFinite() && width > 0.0 && height > 0.0 &&
                width * scale <= 4096 && height * scale <= 4096) { "Actual native field geometry must remain bounded" }
        }
        UIGraphicsBeginImageContextWithOptions(nativeSize, false, scale)
        try {
            assertNotNull(UIGraphicsGetCurrentContext())
            check(field.drawViewHierarchyInRect(field.bounds, afterScreenUpdates = false)) {
                "A failed actual native hierarchy draw is not masked rendering evidence"
            }
            return assertNotNull(UIGraphicsGetImageFromCurrentImageContext()).rgba()
        } finally { UIGraphicsEndImageContext() }
    }

    private fun UIImage.rgba(): ByteArray {
        val image = assertNotNull(CGImage)
        val nativeWidth = CGImageGetWidth(image); val nativeHeight = CGImageGetHeight(image)
        check(nativeWidth in 1uL..4096uL && nativeHeight in 1uL..4096uL)
        check(nativeWidth * nativeHeight <= 4_194_304uL) { "Native field pixels must stay bounded before allocation" }
        val width = nativeWidth.toInt(); val height = nativeHeight.toInt()
        val space = assertNotNull(CGColorSpaceCreateWithName(kCGColorSpaceSRGB))
        try {
            val context = assertNotNull(CGBitmapContextCreate(null, width.convert(), height.convert(), 8u,
                (width * 4).convert(), space, CGImageAlphaInfo.kCGImageAlphaPremultipliedLast.value or kCGBitmapByteOrder32Big))
            try {
                val rect = CGRectMake(0.0, 0.0, width.toDouble(), height.toDouble())
                CGContextSetBlendMode(context, CGBlendMode.kCGBlendModeCopy)
                CGContextSetRGBFillColor(context, 0.0, 0.0, 0.0, 0.0)
                CGContextFillRect(context, rect)
                CGContextSetBlendMode(context, CGBlendMode.kCGBlendModeNormal)
                CGContextDrawImage(context, rect, image)
                val bytes = assertNotNull(CGBitmapContextGetData(context)).reinterpret<UByteVar>()
                return ByteArray(width * height * 4) { bytes[it].toByte() }
            } finally { CGContextRelease(context) }
        } finally { CGColorSpaceRelease(space) }
    }
}
