// Modified for NativeCmpKit (2026-10-29): sample selection cancellation and ownership.
package com.mohamedrejeb.calf.sample.utils

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/** One screen-owned selection job. Calls and the supplied scope belong to the UI thread. */
internal class SampleStreamingOwner(private val scope: CoroutineScope) {
    private var request: Any? = null
    private var activeJob: Job? = null

    fun cancel() {
        request = null
        activeJob?.cancel()
        activeJob = null
    }

    fun <T, R> replace(
        selection: List<T>,
        describe: suspend (T) -> R,
        publish: (List<R>) -> Unit,
    ): Job {
        cancel()
        if (!scope.isActive) return Job().also { it.cancel() }
        val token = Any()
        request = token
        val inputs = selection.toList() // Never read a later selection from a mutable UI state.
        val job = scope.launch(start = CoroutineStart.LAZY) {
            try {
                val results = inputs.map { input ->
                    currentCoroutineContext().ensureActive()
                    describe(input)
                }
                currentCoroutineContext().ensureActive()
                if (request === token) publish(results)
            } finally {
                if (request === token) {
                    request = null
                    activeJob = null
                }
            }
        }
        // Establish ownership before a synchronous transform/publication can reenter replace().
        activeJob = job
        job.start()
        return job
    }
}

@Composable
internal fun rememberSampleStreamingOwner(): SampleStreamingOwner {
    val scope = rememberCoroutineScope()
    val owner = remember(scope) { SampleStreamingOwner(scope) }
    DisposableEffect(owner) { onDispose { owner.cancel() } }
    return owner
}
