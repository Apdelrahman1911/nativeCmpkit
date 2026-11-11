package com.mohamedrejeb.calf.share

import kotlinx.browser.window
import org.w3c.files.File

internal actual fun installShareCapture(): WebShareCapture {
    val navigator = window.navigator.asDynamic()
    val objects = js("Object")
    val previousDescriptor = objects.getOwnPropertyDescriptor(navigator, "share")
    var payload: dynamic = null
    var calls = 0
    val restoreDescriptor = {
        if (previousDescriptor == null) {
            check(js("Reflect").deleteProperty(navigator, "share").unsafeCast<Boolean>())
        } else {
            objects.defineProperty(navigator, "share", previousDescriptor)
        }
        Unit
    }
    val share: (dynamic) -> dynamic = { data ->
        payload = data
        calls += 1
        js("new Promise(function () {})")
    }
    val descriptor = js("({ configurable: true, enumerable: false, writable: true })")
    descriptor.value = share
    return try {
        objects.defineProperty(navigator, "share", descriptor)
        object : WebShareCapture {
            override val callCount: Int
                get() = calls

            override fun fieldNames(): String = objects.keys(payload).sort().join(",").unsafeCast<String>()

            override fun hasOwnField(field: String): Boolean =
                objects.prototype.hasOwnProperty.call(payload, field).unsafeCast<Boolean>()

            override fun stringField(field: String): String? = payload[field] as? String

            override fun fileCount(): Int = payload.files.length.unsafeCast<Int>()

            override fun fileAt(index: Int): File = payload.files[index].unsafeCast<File>()

            override fun isSameFile(index: Int, original: File): Boolean = payload.files[index] === original

            override fun restore() = restoreDescriptor()
        }
    } catch (failure: Throwable) {
        restoreDescriptor()
        throw failure
    }
}

internal actual fun snapshotNavigatorShareDescriptor(): () -> Boolean {
    val navigator = window.navigator.asDynamic()
    val objects = js("Object")
    val previous = objects.getOwnPropertyDescriptor(navigator, "share")
    return {
        val current = objects.getOwnPropertyDescriptor(navigator, "share")
        if (previous == null || current == null) {
            previous === current
        } else {
            previous.value === current.value &&
                previous.get === current.get &&
                previous.set === current.set &&
                previous.writable === current.writable &&
                previous.enumerable === current.enumerable &&
                previous.configurable === current.configurable
        }
    }
}

internal actual fun browserFile(name: String, contents: String, mimeType: String): File =
    js("new File([contents], name, { type: mimeType })").unsafeCast<File>()
