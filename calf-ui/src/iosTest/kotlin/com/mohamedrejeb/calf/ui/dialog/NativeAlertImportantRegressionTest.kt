@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    com.mohamedrejeb.calf.core.InternalCalfApi::class,
    com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi::class)

package com.mohamedrejeb.calf.ui.dialog

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.ui.window.DialogProperties
import com.mohamedrejeb.calf.ui.dialog.uikit.*
import com.mohamedrejeb.calf.ui.internal.NativeApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import platform.UIKit.*
import kotlin.test.*

/**
 * PRIVATE, UNCOMPILED proposal. Supported native accessibility activation is
 * action delivery, not an outside touch, XCUI gesture or physical-key claim.
 * The helper must refuse an unavailable native action; it has no direct
 * activateAction/dismiss/selector/private-handler fallback.
 */
class NativeAlertImportantRegressionTest {
    @Test fun publicRecordSwapUpdatesVisibleIntentAndConfirmsOnlyB() = runApplicationUiTest {
        var parent: UIViewController? = null
        var record by mutableStateOf("A")
        var showing by mutableStateOf(true)
        val confirmed = mutableListOf<String>()
        val cancelled = mutableListOf<String>()
        setContent {
            parent = LocalUIViewController.current
            val displayedRecord = record // The actual callback must capture B, not A.
            if (showing) AdaptiveAlertDialog(
                onConfirm = { confirmed += displayedRecord; showing = false },
                onDismiss = { cancelled += displayedRecord; showing = false },
                confirmText = "Confirm",
                dismissText = "Cancel",
                title = "Record $displayedRecord",
                text = "Delete record $displayedRecord",
            )
        }
        val first = awaitImportantAlert({ parent }, "Record A")
        runOnIdle { record = "B" }
        val updated = awaitImportantAlert({ parent }, "Record B")
        runOnIdle {
            assertTrue(sameNativeObject(first, updated))
            assertEquals("Delete record B", updated.message)
            assertTrue(confirmed.isEmpty() && cancelled.isEmpty())
        }
        activateImportantNativeAction(updated, "Confirm")
        waitForNative { parent?.presentedViewController == null && updated.view.window == null }
        runOnIdle {
            assertEquals(listOf("B"), confirmed)
            assertTrue(cancelled.isEmpty())
        }
    }

    @Test fun publicFieldCallbackAndEnabledChangesKeepControllerAndField() = runApplicationUiTest {
        var parent: UIViewController? = null
        var showing by mutableStateOf(true)
        val oldEdits = mutableListOf<String>()
        val newEdits = mutableListOf<String>()
        val actions = mutableListOf<String>()
        var dismissals = 0
        val firstProperties = AlertDialogIosProperties(
            title = "Field owner", animated = false,
            actions = listOf(AlertDialogIosAction("Finish", AlertDialogIosActionStyle.Default,
                { actions += "A"; showing = false }, enabled = false)),
            textFields = listOf(AlertDialogIosTextField(placeholder = "Owned field", onValueChange = { oldEdits += it })),
        )
        var properties by mutableStateOf(firstProperties)
        setContent {
            parent = LocalUIViewController.current
            if (showing) AdaptiveBasicAlertDialog(
                onDismissRequest = { dismissals++; showing = false },
                iosProperties = properties,
                materialContent = {},
            )
        }
        val first = awaitImportantAlert({ parent }, "Field owner")
        val field = runOnIdle {
            assertFalse(first.actions.filterIsInstance<UIAlertAction>().single().enabled)
            assertTrue(actions.isEmpty())
            first.textFields?.filterIsInstance<UITextField>()?.single()
                ?: error("The actual owned alert must expose its one native field")
        }
        runOnIdle {
            properties = firstProperties.copy(
                actions = listOf(AlertDialogIosAction("Finish", AlertDialogIosActionStyle.Default,
                    { actions += "B"; showing = false }, enabled = true)),
                textFields = listOf(firstProperties.textFields.single().copy(onValueChange = { newEdits += it })),
            )
        }
        waitForNative {
            (parent?.presentedViewController as? UIAlertController)
                ?.actions?.filterIsInstance<UIAlertAction>()?.singleOrNull()?.enabled == true
        }
        runOnIdle {
            val current = parent?.presentedViewController as UIAlertController
            assertTrue(sameNativeObject(first, current))
            assertTrue(sameNativeObject(field, current.textFields?.filterIsInstance<UITextField>()?.single()))
            assertTrue(sameNativeObject(field.window, requireOwnedApplicationWindow()))
            // Deliberately controlled value plus real UIKit EditingChanged target.
            // This is not a synthetic outside touch or hardware-key input claim.
            field.text = "Changed"
            field.sendActionsForControlEvents(UIControlEventEditingChanged)
            assertTrue(oldEdits.isEmpty())
            assertEquals(listOf("Changed"), newEdits)
        }
        activateImportantNativeAction(first, "Finish")
        waitForNative { parent?.presentedViewController == null && field.window == null }
        runOnIdle {
            assertEquals(listOf("B"), actions)
            assertEquals(0, dismissals)
        }
    }

    @Test fun actionReorderRebuildsAndRefusesStaleIndexDispatch() = runApplicationUiTest {
        var parent: UIViewController? = null
        setContent { parent = LocalUIViewController.current }
        val deliveries = mutableListOf<String>()
        var dismissals = 0
        var manager: AlertDialogManager? = null
        var primaryFailure: Throwable? = null
        val firstProperties = AlertDialogIosProperties(title = "Before reorder", animated = false,
            actions = listOf(
                AlertDialogIosAction("Save", AlertDialogIosActionStyle.Default, { deliveries += "Save A" }),
                AlertDialogIosAction("Cancel", AlertDialogIosActionStyle.Cancel, { deliveries += "Cancel A" }),
            ))
        try {
            runOnIdle {
                manager = AlertDialogManager(requireNotNull(parent), { dismissals++ }, firstProperties, DialogProperties())
                    .also { it.showAlertDialog() }
            }
            val first = awaitImportantAlert({ parent }, "Before reorder")
            val staleStructure = firstProperties.structure()
            runOnIdle {
                manager!!.iosProperties = firstProperties.copy(title = "After reorder",
                    actions = listOf(
                        AlertDialogIosAction("Cancel", AlertDialogIosActionStyle.Cancel, { deliveries += "Cancel B" }),
                        AlertDialogIosAction("Save", AlertDialogIosActionStyle.Default, { deliveries += "Save B" }),
                    ))
                manager!!.updateDialogProperties()
                // An explicitly controlled old native-closure boundary. It must
                // not reinterpret old Save index0 as newly reordered Cancel B.
                // This call is NOT used to confirm the fresh native action.
                manager!!.activateAction(0, staleStructure)
                assertTrue(deliveries.isEmpty())
            }
            val rebuilt = awaitImportantAlert({ parent }, "After reorder")
            runOnIdle {
                assertFalse(sameNativeObject(first, rebuilt))
                assertNull(first.view.window)
                assertEquals(listOf("Cancel", "Save"), rebuilt.actions.filterIsInstance<UIAlertAction>().map { it.title })
                manager!!.activateAction(0, staleStructure)
                assertTrue(deliveries.isEmpty())
            }
            activateImportantNativeAction(rebuilt, "Save")
            waitForNative { parent?.presentedViewController == null && rebuilt.view.window == null }
            runOnIdle {
                assertEquals(listOf("Save B"), deliveries)
                assertEquals(0, dismissals)
            }
        } catch (failure: Throwable) {
            primaryFailure = failure
            throw failure
        } finally {
            // Library cleanup is not a user cancel; the outer host independently
            // restores its exact root even when an assertion fails.
            try {
                manager?.let { owned -> com.mohamedrejeb.calf.ui.internal.onApplicationMain { owned.dispose() } }
            } catch (cleanup: Throwable) {
                val primary = primaryFailure
                if (primary == null) throw cleanup else if (primary !== cleanup) primary.addSuppressed(cleanup)
            }
        }
    }

    @Test fun publicConfirmAndCancelRemovalRemainOnceAndImmediatelyReopen() {
        for (chooseConfirm in listOf(true, false)) runApplicationUiTest {
            var parent: UIViewController? = null
            var showing by mutableStateOf(true)
            var reopened by mutableStateOf(false)
            var confirms = 0
            var cancels = 0
            setContent {
                parent = LocalUIViewController.current
                if (showing) AdaptiveAlertDialog(
                    onConfirm = { confirms++; showing = false },
                    onDismiss = { cancels++; showing = false },
                    confirmText = "Confirm", dismissText = "Cancel",
                    title = if (reopened) "Immediately reopened" else "Owned lifecycle",
                    text = "Only this caller owns removal",
                )
            }
            val first = awaitImportantAlert({ parent }, "Owned lifecycle")
            activateImportantNativeAction(first, if (chooseConfirm) "Confirm" else "Cancel")
            waitForNative { parent?.presentedViewController == null && first.view.window == null }
            runOnIdle {
                assertEquals(if (chooseConfirm) 1 else 0, confirms)
                assertEquals(if (chooseConfirm) 0 else 1, cancels)
                // Reopen at the observed completion, no fixed animation sleep.
                reopened = true
                showing = true
            }
            val second = awaitImportantAlert({ parent }, "Immediately reopened")
            runOnIdle {
                assertFalse(sameNativeObject(first, second))
                showing = false
            }
            waitForNative { parent?.presentedViewController == null && second.view.window == null }
            runOnIdle {
                assertEquals(if (chooseConfirm) 1 else 0, confirms)
                assertEquals(if (chooseConfirm) 0 else 1, cancels)
            }
        }
    }
}

private fun NativeApplicationUiTest.awaitImportantAlert(
    parent: () -> UIViewController?,
    title: String,
): UIAlertController {
    waitForNative {
        val presenter = parent()
        val alert = presenter?.presentedViewController as? UIAlertController
        alert?.title == title && sameNativeObject(alert?.view?.window, requireOwnedApplicationWindow()) &&
            sameNativeObject(alert?.presentingViewController, presenter)
    }
    return runOnIdle { parent()?.presentedViewController as UIAlertController }
}

private fun UIView.importantAlertDescendants(): List<UIView> =
    listOf(this) + subviews.filterIsInstance<UIView>().flatMap { it.importantAlertDescendants() }

private fun NativeApplicationUiTest.activateImportantNativeAction(alert: UIAlertController, title: String) {
    // Bounded readiness comes from the actual attached, enabled native action,
    // not an animation sleep or a guessed private control class.
    try {
        waitForNative {
            val window = requireOwnedApplicationWindow()
            val action = alert.actions.filterIsInstance<UIAlertAction>().singleOrNull { it.title == title }
            val eligible = alert.view.importantAlertDescendants().filter {
                it.accessibilityLabel == title && (it.accessibilityTraits and UIAccessibilityTraitButton) != 0UL &&
                    !it.hidden && it.alpha > 0.0 && sameNativeObject(it.window, window)
            }
            sameNativeObject(alert.view.window, window) && action?.enabled == true && eligible.size == 1
        }
    } catch (readinessFailure: IllegalStateException) {
        // Observe only this exact owning timeout. Other refusals are untouched.
        try {
            if (readinessFailure.message?.startsWith(
                    "Timed out awaiting native predicate; actual application state: ") == true) {
                recordImportantAlertActionTimeoutDiagnostic(alert, title, readinessFailure)
            }
        } finally {
            // A reporting/suppression failure must never replace this timeout.
            throw readinessFailure
        }
    }
    runOnIdle {
        val window = requireOwnedApplicationWindow()
        assertTrue(sameNativeObject(alert.view.window, window), "Only this attached native alert may receive input")
        val action = alert.actions.filterIsInstance<UIAlertAction>().filter { it.title == title }.single()
        assertTrue(action.enabled, "Refuse input to a disabled native action")
        val eligible = alert.view.importantAlertDescendants().filter {
            it.accessibilityLabel == title && (it.accessibilityTraits and UIAccessibilityTraitButton) != 0UL &&
                !it.hidden && it.alpha > 0.0 && sameNativeObject(it.window, window)
        }
        assertEquals(1, eligible.size, "Require one supported attached native action, never guess a private control")
        assertTrue(eligible.single().accessibilityActivate(),
            "Native accessibility action unavailable; refuse rather than call a manager or private handler")
    }
}

/**
 * Failure-only bounded observation, never input delivery or a gate repair.
 * The non-lifecycle prefix is ordinary console text; it adds no native cases,
 * protocol success, worker completion or acceptance claim.
 */
private fun recordImportantAlertActionTimeoutDiagnostic(
    alert: UIAlertController,
    title: String,
    primaryFailure: Throwable,
) {
    try {
        com.mohamedrejeb.calf.ui.internal.onApplicationMain {
            val window = requireOwnedApplicationWindow()
            val matchingActions = alert.actions.filterIsInstance<UIAlertAction>().filter { it.title == title }
            val action = matchingActions.singleOrNull()
            val (sample, exhaustive) = alert.view.importantAlertDiagnosticSample()
            val labelled = sample.filter { it.accessibilityLabel == title }
            val buttons = labelled.filter { (it.accessibilityTraits and UIAccessibilityTraitButton) != 0UL }
            val visible = buttons.filter { !it.hidden && it.alpha > 0.0 }
            val eligible = visible.filter { sameNativeObject(it.window, window) }
            // No titles, labels, contents, classes, addresses, owner IDs or errors.
            // An after-timeout/possibly partial snapshot is not the failed operand.
            println("NATIVECMPKIT_ALERT_ACTION_GATE_TIMEOUT captured=true " +
                "main_thread=${platform.Foundation.NSThread.isMainThread} " +
                "alert_attached=${sameNativeObject(alert.view.window, window)} " +
                "matching_actions=${matchingActions.size} action_unique=${action != null} " +
                "action_enabled=${action?.enabled == true} " +
                "sampled_views=${sample.size} hierarchy_complete=$exhaustive " +
                "label_matches=${labelled.size} button_trait_matches=${buttons.size} " +
                "visible_matches=${visible.size} eligible_matches=${eligible.size}")
            recordImportantAlertContainerTimeoutObservation(alert, title, window, sample)
        }
    } catch (observationFailure: Throwable) {
        // Both reporting operations are best-effort; neither may mask the
        // original readiness timeout if console I/O or suppression itself fails.
        try {
            println("NATIVECMPKIT_ALERT_ACTION_GATE_TIMEOUT captured=false")
        } catch (_: Throwable) { /* The outer boundary still throws the original timeout. */ }
        try {
            if (observationFailure !== primaryFailure) primaryFailure.addSuppressed(observationFailure)
        } catch (_: Throwable) { /* Suppression failure is never replacement primary. */ }
    }
}

/** Read at most2048 views on application main; never dump a native hierarchy. */
private fun UIView.importantAlertDiagnosticSample(): Pair<List<UIView>, Boolean> {
    val limit = 2048
    val sampled = mutableListOf<UIView>()
    val pending = ArrayDeque<UIView>()
    pending.addLast(this)
    var exhaustive = true
    while (pending.isNotEmpty()) {
        val view = pending.removeFirst()
        sampled += view
        val children = view.subviews
        val available = limit - sampled.size - pending.size
        if (children.size > available) exhaustive = false
        for (index in 0 until minOf(children.size, available)) {
            val child = children[index]
            if (child is UIView) pending.addLast(child)
        }
    }
    return sampled to exhaustive
}

/**
 * Failure-only public count/index observation from retained alert-descendant views.
 * Counts are edge facts after the timeout, never native input or eligibility.
 * Direct index children only; no list getter, nested expansion or backlink walk.
 * Getter duration/bridging and Objective-C exception handling are not bounded here.
 */
private fun recordImportantAlertContainerTimeoutObservation(
    alert: UIAlertController,
    title: String,
    window: UIWindow,
    sampledViews: List<UIView>,
) {
    try {
        val ownerLimit = 16
        val perOwnerIndexLimit = 4L
        val totalIndexLimit = 32
        val mainThread = platform.Foundation.NSThread.isMainThread
        val owners = mutableListOf<UIView>()
        val retained = mutableListOf<platform.darwin.NSObject>()
        var admitted = false
        var attachmentsHeld = false
        var unknown = false
        var duplicateOwners = 0
        var detachedOwners = 0
        var countOwners = 0
        var negativeCounts = 0
        var zeroCounts = 0
        var indexTruncated = false
        var indexReads = 0
        var nilChildren = 0
        var unsupportedChildren = 0
        var viewChildren = 0
        var elementChildren = 0
        var otherObjectChildren = 0
        var duplicateChildren = 0
        var selfChildren = 0
        var labelMatches = 0
        var buttonMatches = 0
        var backlinkSourceOwner = 0
        var backlinkNil = 0
        var backlinkOther = 0
        var backlinkUnsupported = 0
        val ownerPrefixTruncated = sampledViews.size > ownerLimit
        if (mainThread) {
            val root = sampledViews.firstOrNull()
            val alertRoot = alert.view
            admitted = sameNativeObject(root, alertRoot) &&
                sameNativeObject(root?.window, window) && sameNativeObject(alertRoot.window, window)
        }
        attachmentsHeld = admitted
        unknown = !admitted || ownerPrefixTruncated
        if (admitted) {
            for (position in 0 until minOf(sampledViews.size, ownerLimit)) {
                val owner = sampledViews[position]
                if (owners.any { sameNativeObject(it, owner) }) {
                    duplicateOwners++
                } else {
                    owners += owner
                    retained += owner
                }
            }
            for (owner in owners) {
                if (!sameNativeObject(owner.window, window)) {
                    detachedOwners++
                    attachmentsHeld = false
                    unknown = true
                    continue
                }
                val count = owner.accessibilityElementCount()
                countOwners++
                if (count < 0L) {
                    negativeCounts++
                    unknown = true
                } else {
                    if (count == 0L) zeroCounts++
                    val inspectCount = minOf(count, perOwnerIndexLimit, (totalIndexLimit - indexReads).toLong())
                    if (count > inspectCount) {
                        indexTruncated = true
                        unknown = true
                    }
                    var index = 0L
                    while (index < inspectCount) {
                        val child = owner.accessibilityElementAtIndex(index)
                        index++
                        indexReads++
                        when (child) {
                            null -> { nilChildren++; unknown = true }
                            is UIView -> viewChildren++
                            is UIAccessibilityElement -> elementChildren++
                            is platform.darwin.NSObject -> otherObjectChildren++
                            else -> { unsupportedChildren++; unknown = true }
                        }
                        val native = child as? platform.darwin.NSObject
                        if (native != null) {
                            if (sameNativeObject(native, owner)) selfChildren++
                            if (retained.any { sameNativeObject(it, native) }) {
                                duplicateChildren++
                            } else {
                                check(retained.size < ownerLimit + totalIndexLimit)
                                retained += native
                            }
                            if (native.accessibilityLabel == title) {
                                labelMatches++
                                if ((native.accessibilityTraits and UIAccessibilityTraitButton) != 0UL) buttonMatches++
                            }
                        } else if (child is UIAccessibilityElement || child is UIView) {
                            unknown = true // A type classification cannot invent NSObject metadata availability.
                        }
                        if (child is UIAccessibilityElement) {
                            val backlink = child.accessibilityContainer
                            val nativeBacklink = backlink as? platform.darwin.NSObject
                            when {
                                backlink == null -> { backlinkNil++; unknown = true }
                                nativeBacklink == null -> { backlinkUnsupported++; unknown = true }
                                sameNativeObject(nativeBacklink, owner) -> backlinkSourceOwner++
                                else -> backlinkOther++
                            }
                        }
                    }
                }
                if (!sameNativeObject(owner.window, window)) { attachmentsHeld = false; unknown = true }
            }
            if (!sameNativeObject(sampledViews.firstOrNull(), alert.view) ||
                !sameNativeObject(alert.view.window, window)) { attachmentsHeld = false; unknown = true }
        }
        // Never emit an object, label, title, error, address, class name or path.
        println("NATIVECMPKIT_ALERT_ACTION_CONTAINER_TIMEOUT captured=true " +
            "main_thread=$mainThread admitted=$admitted attachments_held=$attachmentsHeld unknown=$unknown " +
            "sampled_view_owners=${owners.size} duplicate_view_owners=$duplicateOwners detached_view_owners=$detachedOwners " +
            "count_owners=$countOwners negative_count_owners=$negativeCounts zero_count_owners=$zeroCounts " +
            "owner_prefix_truncated=$ownerPrefixTruncated index_truncated=$indexTruncated index_children=$indexReads " +
            "nil_children=$nilChildren unsupported_children=$unsupportedChildren view_children=$viewChildren " +
            "element_children=$elementChildren other_object_children=$otherObjectChildren " +
            "duplicate_children=$duplicateChildren self_children=$selfChildren retained_objects=${retained.size} " +
            "label_match_children=$labelMatches button_match_children=$buttonMatches " +
            "element_backlink_source_owner=$backlinkSourceOwner element_backlink_nil=$backlinkNil " +
            "element_backlink_other=$backlinkOther element_backlink_unsupported=$backlinkUnsupported " +
            "list_observed=false nested_containers_observed=false child_visibility_observed=false child_window_observed=false")
    } catch (_: Throwable) {
        // Discard the observation error; the existing outer finally retains its exact primary.
        try {
            println("NATIVECMPKIT_ALERT_ACTION_CONTAINER_TIMEOUT captured=false")
        } catch (_: Throwable) { /* Reporting cannot replace the original readiness timeout. */ }
    }
}
