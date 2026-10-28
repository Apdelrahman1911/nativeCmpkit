@file:OptIn(kotlin.js.ExperimentalWasmJsInterop::class)

package com.mohamedrejeb.calf.permissions

import kotlinx.coroutines.test.TestResult
import kotlin.test.Test

/** Real public platform factories; six finite scenarios, not helper/preview substitutes. */
class UnsupportedPublicFactoryTest {
    @Test fun allNamedSingleRequestsCompleteOnceWithoutImplyingAuthorization(): TestResult =
        UnsupportedPublicFactoryFixture().allNamedSingleRequestsCompleteOnceWithoutImplyingAuthorization()

    @Test fun publicBatchChildAndEmptyRequestsReturnExactUnsupportedMaps(): TestResult =
        UnsupportedPublicFactoryFixture().publicBatchChildAndEmptyRequestsReturnExactUnsupportedMaps()

    @Test fun publicCallbacksFollowRecompositionAndPreserveTheState(): TestResult =
        UnsupportedPublicFactoryFixture().publicCallbacksFollowRecompositionAndPreserveTheState()

    @Test fun publicPermissionChangesCannotLeakThePreviousSelection(): TestResult =
        UnsupportedPublicFactoryFixture().publicPermissionChangesCannotLeakThePreviousSelection()

    @Test fun throwingAndReentrantCallbacksHaveExactlyOneSynchronousResult(): TestResult =
        UnsupportedPublicFactoryFixture().throwingAndReentrantCallbacksHaveExactlyOneSynchronousResult()

    @Test fun environmentAndLegacyFlagsCannotManufactureAuthorization(): TestResult =
        UnsupportedPublicFactoryFixture().environmentAndLegacyFlagsCannotManufactureAuthorization(::installServiceGuard)

}

@JsFun("""function(mode) {
    const restores = [];
    let reads = 0, calls = 0;
    const denied = {
        permissions: {query: () => { calls++; return Promise.resolve({state: 'denied'}); }},
        mediaDevices: {getUserMedia: () => { calls++; return Promise.reject(new Error('Denied fixture')); }},
        geolocation: {getCurrentPosition: () => { calls++; }, watchPosition: () => { calls++; return 1; }},
        Notification: {permission: 'denied', requestPermission: () => { calls++; return Promise.resolve('denied'); }}
    };
    const entries = [[navigator, 'permissions'], [navigator, 'mediaDevices'],
                     [navigator, 'geolocation'], [window, 'Notification'], [window, 'isSecureContext']];
    const restore = () => { for (let i = restores.length - 1; i >= 0; i--) restores[i](); };
    try {
        for (const [owner, name] of entries) {
            const previous = Object.getOwnPropertyDescriptor(owner, name);
            Object.defineProperty(owner, name, {configurable: true, get: () => {
                reads++;
                if (name === 'isSecureContext') return mode === 'denied';
                return mode === 'missing' ? undefined : denied[name];
            }});
            restores.push(() => { if (previous) Object.defineProperty(owner, name, previous); else delete owner[name]; });
        }
    } catch (error) { restore(); throw error; }
    return () => {
        restore();
        if (reads !== 0 || calls !== 0) throw new Error('Explicit Unsupported must not query/prompt services: reads=' + reads + ', calls=' + calls);
    };
}""")
private external fun installNativeServiceGuard(mode: String): kotlin.js.JsAny

@JsFun("function(restore) { restore(); }")
private external fun restoreNativeServiceGuard(restore: kotlin.js.JsAny)

private fun installServiceGuard(mode: String): () -> Unit {
    val restore = installNativeServiceGuard(mode)
    return { restoreNativeServiceGuard(restore) }
}
