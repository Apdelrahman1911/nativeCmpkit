package com.mohamedrejeb.calf.ui.internal

import platform.Foundation.NSThread
import platform.UIKit.UIViewController

/**
 * Only coordinates nativeCmpkit's own modal owners. Never dismisses somebody else's controller.
 * A replacement owner waits for the old owner's native dismissal, not just Compose disposal.
 * Entries retain a controller only while it owns or waits for an actual presentation.
 */
internal object NativePresentationQueue {
    private data class Request(val owner: Any, val start: () -> Unit)
    private val owners = mutableMapOf<UIViewController, Any>()
    private val waiting = mutableMapOf<UIViewController, MutableList<Request>>()

    fun acquire(parent: UIViewController, owner: Any, start: () -> Unit) {
        check(NSThread.isMainThread)
        if (owners[parent] === owner) return
        if (owners[parent] == null) {
            owners[parent] = owner
            start()
        } else {
            waiting.getOrPut(parent) { mutableListOf() }.add(Request(owner, start))
        }
    }

    fun cancelWaiting(parent: UIViewController, owner: Any): Boolean {
        check(NSThread.isMainThread)
        val list = waiting[parent] ?: return false
        val removed = list.removeAll { it.owner === owner }
        if (list.isEmpty()) waiting.remove(parent)
        return removed
    }

    fun release(parent: UIViewController, owner: Any) {
        check(NSThread.isMainThread)
        if (owners[parent] !== owner) return
        owners.remove(parent)
        val list = waiting[parent] ?: return
        val next = list.removeAt(0)
        if (list.isEmpty()) waiting.remove(parent)
        owners[parent] = next.owner
        next.start()
    }
}
