/*
 * Copyright (C) 2007 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Adapted for Calf and nativeCmpkit. Modified 2026-10-24: document actual map
 * semantics. See licenses/navigation-aosp-provenance.json.
 */
package com.mohamedrejeb.calf.navigation

/**
 * An in-memory, non-thread-safe value map. It does not implement Parcelable,
 * persistence, lazy decoding, structural equality or defensive copying.
 * Navigation entries separately snapshot and save their supported values.
 */
class AdaptiveBundle : AdaptiveBaseBundle()
