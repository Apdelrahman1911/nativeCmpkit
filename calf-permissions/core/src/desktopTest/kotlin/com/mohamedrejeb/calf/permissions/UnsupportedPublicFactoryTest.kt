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
        UnsupportedPublicFactoryFixture().environmentAndLegacyFlagsCannotManufactureAuthorization { mode ->
            if (mode == "missing") UnsupportedPermissionSandboxProbe.verifyOnMacOs()
            val restore: () -> Unit = {}
            restore
        }

}
