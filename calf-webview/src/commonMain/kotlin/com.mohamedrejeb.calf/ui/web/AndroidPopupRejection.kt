// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.ui.web

/**
 * An Android child-window request explicitly rejected by the common WebView wrapper.
 *
 * Android does not supply a trustworthy destination URL to `onCreateWindow`.
 * These flags describe the request, not its origin, URI, or an authorization.
 * [requestNumber] only distinguishes successive events within these settings;
 * it is neither persisted nor an identity/security token. No child is created.
 */
data class AndroidPopupRejection(
    val requestNumber: Long,
    val isDialog: Boolean,
    val isUserGesture: Boolean,
)
