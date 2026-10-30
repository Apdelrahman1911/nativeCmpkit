// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.web

import kotlinx.cinterop.objcPtr
import platform.WebKit.WKWebView

/**
 * KVO and delegate calls may bridge another Kotlin wrapper for the same native view.
 * Ownership is the retained Objective-C object, not wrapper identity or value equality.
 * Two nulls never establish an owner. Compare only while both native references are alive;
 * never retain or export their addresses as identities.
 */
internal fun hasSameNativeWebView(first: WKWebView?, second: WKWebView?): Boolean =
    first != null && second != null && first.objcPtr() == second.objcPtr()
