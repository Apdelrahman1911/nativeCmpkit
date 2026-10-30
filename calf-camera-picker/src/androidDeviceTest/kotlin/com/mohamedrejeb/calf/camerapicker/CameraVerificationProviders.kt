// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.camerapicker

import androidx.core.content.FileProvider

// Android identifies local providers by component class, not just authority.
// Distinct per-provider metadata must not share one cached local component.
class CameraLegacyVerificationProvider : FileProvider()
class CameraWrongRootVerificationProvider : FileProvider()
