// Test-only NativeCmpKit failed Share188 input observation; PRIVATE/UNEXECUTED source proposal.
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.share.internal

import com.mohamedrejeb.calf.share.IosShareOwner
import com.mohamedrejeb.calf.share.IosShareRequestPhase
import platform.Foundation.NSThread

/**
 * Exact failed-method-only test-owned delegation, NOT a production completion hook.
 * Replacing the installed block changes its native identity and adds observation time.
 * Every received call still invokes the same immutable captured original delegate once,
 * on the incoming thread, with all four original argument values. No result is invented.
 * Counts/order below concern recorded main-thread entries, not UIKit-versus-fixture origin.
 */
internal class ShareTerminalInputObservation private constructor() {
    companion object {
        private const val FILTER = "--ktest_gradle_filter=" +
            "com.mohamedrejeb.calf.share.IosSharePresentationOwnershipTest." +
            "publicRememberedShareMainDefaultIoReentryAndDisposalUseCurrentCallbacks"
        internal fun forExactArguments(arguments: Array<String>): ShareTerminalInputObservation? {
            check(NSThread.isMainThread)
            return if (arguments.size == 3 && arguments.count { it == FILTER } == 1 &&
                arguments.count { it == "--ktest_logger=TEAMCITY" } == 1 &&
                arguments.count { it == "--ktest_no_exit_code" } == 1) ShareTerminalInputObservation() else null
        }
    }

    private class Record(val id: Int, val owner: IosShareOwner, val request: IosShareOwner.Request)
    private val records = mutableListOf<Record>() // At most the original method's four requests.
    private val events = mutableListOf<String>() // At most sixteen fixed bool/count/phase records.
    private var truncated = false
    private var unknown = false
    private var closed = false

    /** Called once after the existing host has retained this exact owner/request/native work. */
    internal fun capture(owner: IosShareOwner, request: IosShareOwner.Request) {
        check(NSThread.isMainThread)
        check(!closed && records.none { it.request === request }) { "Refuse a repeated observation install" }
        check(records.size < 4) { "Refuse an unreviewed fifth Share request observation" }
        val original = checkNotNull(request.controller.completionWithItemsHandler) {
            "Refuse observation without the installed original Share delegate"
        }
        val record = Record(records.size + 1, owner, request)
        records += record
        // A getter/setter/installation refusal propagates unchanged into the host's existing
        // primary/suppressed-error and retained-lease handling. There is no restore/retry guess.
        request.controller.completionWithItemsHandler = { activityType, completed, items, error ->
            try { observe(record, "input", completed, error != null) }
            catch (_: Throwable) { /* A recording failure cannot prevent original forwarding. */ }
            var returned = false
            try {
                original(activityType, completed, items, error)
                returned = true
            } finally {
                // Observation never catches, retries or replaces an original delegate exception.
                try { observe(record, "return", returned = returned) }
                catch (_: Throwable) { /* Preserve the exact original return/exception. */ }
            }
        }
    }

    /** Only an existing, genuinely acknowledged owned-native dismissal calls this marker. */
    internal fun dismissalAcknowledged(request: IosShareOwner.Request?) {
        var observedMain = false
        try {
            observedMain = NSThread.isMainThread
            if (!observedMain || closed || request == null) return
            val record = records.singleOrNull { it.request === request }
            if (record == null) unknown = true else observe(record, "dismissAck")
        } catch (_: Throwable) { if (observedMain) unknown = true }
    }

    private fun observe(record: Record, kind: String, completed: Boolean? = null,
                        errorPresent: Boolean? = null, returned: Boolean? = null) {
        // Do not hop threads or mutate main-confined observation state off main. An off-main
        // input is still forwarded unchanged, but this trace cannot count or diagnose it.
        var observedMain = false
        try {
            observedMain = NSThread.isMainThread
            if (!observedMain || closed) return
            if (events.size >= 16) { truncated = true; return }
            events += "n=${events.size + 1},r=${record.id},k=$kind,c=$completed,e=$errorPresent," +
                "ret=$returned,a=${record.owner.currentRequest === record.request},p=${record.request.phase.name}"
        } catch (_: Throwable) { if (observedMain) unknown = true }
    }

    /** Failure-only ordinary output; never TeamCity/native completion/eligibility evidence. */
    internal fun emitFailure() {
        try {
            if (!NSThread.isMainThread) return
            println("NATIVECMPKIT_SHARE_TERMINAL_FAILURE schema=1 captured=true " +
                "requests=${records.size} events=${events.size} truncated=$truncated " +
                "unknown=${unknown || truncated || events.isEmpty()} main_only=true off_main_observed=false " +
                "origin_observed=false block_identity_changed=true " + events.joinToString("|"))
        } catch (_: Throwable) {
            try { println("NATIVECMPKIT_SHARE_TERMINAL_FAILURE schema=1 captured=false unknown=true") }
            catch (_: Throwable) { /* Reporting cannot replace the original failure. */ }
        }
    }

    /**
     * Called only inside all existing owner/native/root teardown guards, before dropping leases.
     * Never restore a delegate onto a released/disposed controller or overwrite a foreign block.
     * UIKit's original production release/dispose owns clearing the installed wrapper to nil.
     * Captured late wrappers still forward their original delegate once; only recording stops.
     */
    internal fun closeAfterVerifiedTeardown() {
        check(NSThread.isMainThread)
        check(records.all { it.owner.currentRequest == null && it.request.phase == IosShareRequestPhase.Released &&
            it.request.controller.completionWithItemsHandler == null }) { "Unverified observer lifetime retains owner/root leases" }
        closed = true
        records.clear()
        events.clear()
    }
}
