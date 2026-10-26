package com.mohamedrejeb.calf.picker

/** A suggested name is one path component, not a destination path. */
internal fun suggestedFileName(baseName: String, extension: String): String {
    require(baseName.isNotBlank() && baseName != "." && baseName != "..") { "baseName must be a non-empty file name" }
    fun valid(component: String) = component.none { it == '/' || it == '\\' || it.code < 32 || it == '\u007f' }
    require(valid(baseName) && valid(extension)) { "File names cannot contain separators or control characters" }
    require(!extension.startsWith('.')) { "extension must not start with a dot" }
    return if (extension.isEmpty()) baseName else "$baseName.$extension"
}

internal fun FilePickerSelectionMode.resultLimit(): Int? = when (this) {
    FilePickerSelectionMode.Single -> 1
    is FilePickerSelectionMode.Multiple -> maxItems
}

internal fun <T> List<T>.limitedTo(mode: FilePickerSelectionMode): List<T> = mode.resultLimit()?.let(::take) ?: this
