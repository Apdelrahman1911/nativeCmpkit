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
package jodd.util

/**
 * Checks whether a string or path matches a given wildcard pattern.
 * Possible patterns allow to match single characters ('?') or any count of
 * characters ('*'). Wildcard characters can be escaped (by an '\').
 * When matching path, deep tree wildcard also can be used ('**').
 *
 *
 * Matching is iterative (no recursive/exponential suffix exploration). At worst it revisits
 * a pattern suffix for each input character; storage is proportional to the pattern length.
 */
internal object Wildcard {
    /**
     * Checks whether a string matches a given wildcard pattern.
     *
     * @param string    input string
     * @param pattern    pattern to match
     * @return            `true` if string matches the pattern, otherwise `false`
     */
    fun match(string: CharSequence, pattern: CharSequence): Boolean {
        // Parse escaping once. A trailing escape, as in the original implementation, cannot match.
        val tokens = ArrayList<Int>(pattern.length)
        var index = 0
        while (index < pattern.length) {
            when (val char = pattern[index++]) {
                '\\' -> { if (index == pattern.length) return false; tokens += pattern[index++].code }
                '*' -> if (tokens.lastOrNull() != STAR) tokens += STAR
                '?' -> tokens += ANY
                else -> tokens += char.code
            }
        }
        var input = 0
        var token = 0
        var star = -1
        var starInput = 0
        while (input < string.length) {
            when {
                token < tokens.size && (tokens[token] == ANY || tokens[token] == string[input].code) -> { input++; token++ }
                token < tokens.size && tokens[token] == STAR -> { star = token++; starInput = input }
                star >= 0 -> { token = star + 1; input = ++starInput }
                else -> return false
            }
        }
        while (token < tokens.size && tokens[token] == STAR) token++
        return token == tokens.size
    }

    private const val STAR = -1
    private const val ANY = -2

    // ---------------------------------------------------------------- utilities
    /**
     * Matches string to at least one pattern.
     * Returns index of matched pattern, or `-1` otherwise.
     * @see .match
     */
    fun matchOne(src: String, vararg patterns: String): Int {
        for (i in patterns.indices) {
            if (match(src, patterns[i])) {
                return i
            }
        }
        return -1
    }
}