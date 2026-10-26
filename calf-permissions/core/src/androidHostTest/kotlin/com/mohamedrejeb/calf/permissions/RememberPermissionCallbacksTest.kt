package com.mohamedrejeb.calf.permissions

import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import kotlin.test.Test

/**
 * The same common helper scenarios, using Android Compose runtime under Robolectric.
 * This runner does not turn Unsupported helpers into Android permission-factory or device tests.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34], manifest = Config.NONE)
class RememberPermissionCallbacksTest {
    @Test fun rememberedSingleUsesLatestCallbackWithoutReplacingState() =
        RememberPermissionCallbacksFixture().rememberedSingleUsesLatestCallbackWithoutReplacingState()

    @Test fun rememberedEmptyBatchStillCallsLatestCallbackExactlyOnce() =
        RememberPermissionCallbacksFixture().rememberedEmptyBatchStillCallsLatestCallbackExactlyOnce()

    @Test fun unsupportedBatchReportsAllDistinctMembersWithOneCallback() =
        RememberPermissionCallbacksFixture().unsupportedBatchReportsAllDistinctMembersWithOneCallback()
}
