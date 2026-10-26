// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
// Copyright (c) 2003-present, Jodd Team (http://jodd.org)
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice,
// this list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright
// notice, this list of conditions and the following disclaimer in the
// documentation and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
package jodd.net

import jodd.io.IOUtil
import jodd.util.Wildcard
import java.io.IOException
import java.util.Properties
import java.util.Locale

/**
 * Map file extensions to MIME types. Based on the most recent Apache mime.types file.
 * Duplicated extensions (wmz, sub) are manually resolved.
 *
 *
 * See also:
 * http://www.iana.org/assignments/media-types/
 * http://www.webmaster-toolkit.com/mime-types.shtml
 */
internal object MimeTypes {
    const val MIME_APPLICATION_ATOM_XML: String = "application/atom+xml"
    const val MIME_APPLICATION_JAVASCRIPT: String = "application/javascript"
    const val MIME_APPLICATION_JSON: String = "application/json"
    const val MIME_APPLICATION_OCTET_STREAM: String = "application/octet-stream"
    const val MIME_APPLICATION_XML: String = "application/xml"
    const val MIME_TEXT_CSS: String = "text/css"
    const val MIME_TEXT_PLAIN: String = "text/plain"
    const val MIME_TEXT_HTML: String = "text/html"

    private val MIME_TYPE_MAP: LinkedHashMap<String, String> // extension -> mime-type map
    private var reverseIndex: Map<String, List<String>> = emptyMap()

    init {
        val mimes = Properties()

        val inputStream = MimeTypes::class.java.getResourceAsStream(MimeTypes::class.java.simpleName + ".properties")
            ?: throw IllegalStateException("Mime types file missing")

        try {
            mimes.load(inputStream)
        } catch (ioex: IOException) {
            throw IllegalStateException("Can't load properties", ioex)
        } finally {
            IOUtil.close(inputStream)
        }

        MIME_TYPE_MAP = LinkedHashMap<String, String>(mimes.size * 2)

        val keys = mimes.propertyNames()
        while (keys.hasMoreElements()) {
            var mimeType = keys.nextElement() as String
            val extensions = mimes.getProperty(mimeType)

            when {
                mimeType.startsWith("/") ->
                    mimeType = "application$mimeType"

                mimeType.startsWith("a/") ->
                    mimeType = "audio" + mimeType.substring(1)

                mimeType.startsWith("i/") ->
                    mimeType = "image" + mimeType.substring(1)

                mimeType.startsWith("t/") ->
                    mimeType = "text" + mimeType.substring(1)

                mimeType.startsWith("v/") ->
                    mimeType = "video" + mimeType.substring(1)

            }

            val allExtensions = extensions.split(' ').filter { it.isNotBlank() }

            for (extension in allExtensions) {
                require(MIME_TYPE_MAP.put(extension, mimeType) == null) { "Duplicated extension: $extension" }
            }
        }
        rebuildReverseIndex()
    }

    private fun rebuildReverseIndex() {
        reverseIndex = MIME_TYPE_MAP.entries.groupBy({ it.value }, { it.key })
    }

    /**
     * Registers MIME type for provided extension. Existing extension type will be overridden.
     */
    @Synchronized
    fun registerMimeType(ext: String, mimeType: String) {
        MIME_TYPE_MAP[ext.lowercase(Locale.ROOT)] = mimeType.lowercase(Locale.ROOT)
        rebuildReverseIndex()
    }

    /**
     * Returns the corresponding MIME type to the given extension.
     * If no MIME type was found it returns `application/octet-stream` type.
     */
    fun getMimeType(ext: String): String {
        var mimeType = lookupMimeType(ext)
        if (mimeType == null) {
            mimeType = MIME_APPLICATION_OCTET_STREAM
        }
        return mimeType
    }

    /**
     * Simply returns MIME type or `null` if no type is found.
     */
    @Synchronized
    fun lookupMimeType(ext: String): String? {
        return MIME_TYPE_MAP[ext.lowercase(Locale.ROOT)]
    }

    /**
     * Finds all extensions that belong to given mime type(s).
     * If wildcard mode is on, provided mime type is wildcard pattern.
     * @param mimeType list of mime types, separated by comma
     * @param useWildcard if set, mime types are wildcard patterns
     */
    @Synchronized
    fun findExtensionsByMimeTypes(mimeType: String, useWildcard: Boolean): List<String> {
        val patterns = mimeType.lowercase(Locale.ROOT).split(',').map(String::trim).filter(String::isNotEmpty)
        if (!useWildcard) return patterns.flatMap { reverseIndex[it].orEmpty() }.distinct()
        return reverseIndex.flatMap { (mime, extensions) ->
            if (patterns.any { pattern -> Wildcard.match(mime, pattern) }) extensions else emptyList()
        }
    }

    /**
     * Returns `true` if given value is one of the registered MIME extensions.
     */
    @Synchronized
    fun isRegisteredExtension(extension: String): Boolean {
        return MIME_TYPE_MAP.containsKey(extension.lowercase(Locale.ROOT))
    }
}
