package com.mohamedrejeb.calf.permissions

import kotlin.test.Test

/** Desktop/Apple/browser runner; no Android framework calls are replaced or silently stubbed. */
class RememberPermissionCallbacksTest {
    @Test fun rememberedSingleUsesLatestCallbackWithoutReplacingState() =
        RememberPermissionCallbacksFixture().rememberedSingleUsesLatestCallbackWithoutReplacingState()

    @Test fun rememberedEmptyBatchStillCallsLatestCallbackExactlyOnce() =
        RememberPermissionCallbacksFixture().rememberedEmptyBatchStillCallsLatestCallbackExactlyOnce()

    @Test fun unsupportedBatchReportsAllDistinctMembersWithOneCallback() =
        RememberPermissionCallbacksFixture().unsupportedBatchReportsAllDistinctMembersWithOneCallback()
}
