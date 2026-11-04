package com.mohamedrejeb.calf.permissions

/**
 * Main-thread-confined ownership of one native request. Overlapping callers share the
 * prompt, but each receives one result. Clear ownership BEFORE invoking application
 * code so reentrant launches cannot be cleared by the previous completion.
 */
internal class PermissionRequestGate<R> {
    private var generation = 0L
    private var active: Long? = null
    private var disposed = false
    private val callbacks = mutableListOf<(R) -> Unit>()

    val isActive: Boolean get() = active != null

    fun begin(callback: (R) -> Unit): Long? {
        if (disposed) return null
        callbacks += callback
        if (active != null) return null
        return (++generation).also { active = it }
    }

    fun isCurrent(token: Long): Boolean = !disposed && active == token

    fun complete(token: Long, result: R) {
        if (!isCurrent(token)) return
        val completed = callbacks.toList()
        callbacks.clear()
        active = null
        var failure: Throwable? = null
        for (callback in completed) {
            if (disposed) break
            try {
                callback(result)
            } catch (error: Throwable) {
                if (failure == null) failure = error
            }
        }
        failure?.let { throw it }
    }

    fun abort(token: Long) {
        if (!isCurrent(token)) return
        callbacks.clear()
        active = null
    }

    fun dispose() {
        disposed = true
        active = null
        callbacks.clear()
    }
}

/** Serializes asynchronous requests and reports one complete, request-scoped map. */
internal class PermissionBatchRequest(
    permissions: List<Permission>,
    private val request: (Permission, (Boolean) -> Unit) -> Unit,
) {
    private val permissions = permissions.distinct()
    private val gate = PermissionRequestGate<Map<Permission, Boolean>>()

    fun launch(onResult: (Map<Permission, Boolean>) -> Unit) {
        val token = gate.begin(onResult) ?: return
        val result = linkedMapOf<Permission, Boolean>()
        var index = 0
        var waiting = false
        var pumping = false

        fun advance() {
            if (pumping) return
            pumping = true
            try {
                while (gate.isCurrent(token) && !waiting) {
                    if (index == permissions.size) {
                        gate.complete(token, result.toMap())
                        break
                    }
                    val permission = permissions[index++]
                    waiting = true
                    var answered = false
                    request(permission) { granted ->
                        if (!answered && gate.isCurrent(token)) {
                            answered = true
                            result[permission] = granted
                            waiting = false
                            advance()
                        }
                    }
                }
            } catch (error: Throwable) {
                gate.abort(token)
                throw error
            } finally {
                pumping = false
            }
        }
        advance()
    }

    fun dispose() = gate.dispose()
}
