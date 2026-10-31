// Inert build-logic utility. Declared metadata checks are not artifact trust.
package io.github.apdelrahman1911.nativecmpkit.buildlogic

import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.charset.CodingErrorAction
import java.nio.charset.StandardCharsets
import java.nio.file.FileSystems
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.NoSuchFileException
import java.nio.file.Path
import java.nio.file.StandardOpenOption
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest
import java.util.ArrayDeque
import java.util.Base64
import java.util.Collections

/**
 * One JDK-only, bounded Yarn Classic registry profile for actual root/workspace manifests.
 * Exact declared selectors are checked; ranges are not solved and package bytes are not read.
 * Alias/Git/local-protocol semantics are refused pending a separate source-backed review.
 * No Gradle, Python, Node, Yarn, network, writes, cacheable success file or resolver is used.
 *
 * Stable-owned-input precondition: callers must exclusively own the selected input tree
 * and establish stable root/ancestor identities, with no concurrent writers or path substitution.
 * The NIO reader is non-atomic; byte bounds do not make a substituted FIFO open time-bounded.
 * Existing-link refusals are not an adversarial, Windows-reparse or universal host guarantee.
 * This utility is not wired into ordinary root builds. An adapter must establish and verify
 * its input/host contract and mandatory task ordering before calling it as an enforcement gate.
 */
object DeclaredYarnClosure {
    data class Limits(
        val lockBytes: Int = 2 * 1024 * 1024,
        val lineBytes: Int = 64 * 1024,
        val stanzas: Int = 10_000,
        val selectors: Int = 100_000,
        val edges: Int = 100_000,
        val workspaces: Int = 256,
        val manifestBytes: Int = 1024 * 1024,
        val totalManifestBytes: Int = 8 * 1024 * 1024,
        val jsonDepth: Int = 64,
        val jsonNodes: Int = 100_000,
        val traceItems: Int = 12,
    ) {
        init {
            require(lockBytes in 1..2 * 1024 * 1024 && lineBytes in 1..64 * 1024)
            require(stanzas in 0..10_000 && selectors in 0..100_000 && edges in 0..100_000)
            require(workspaces in 0..256 && manifestBytes in 1..1024 * 1024)
            require(totalManifestBytes in 1..8 * 1024 * 1024 && jsonDepth in 1..64)
            require(jsonNodes in 1..100_000 && traceItems in 1..12)
        }
    }

    data class InputReceipt(val path: String, val bytes: Int, val sha256: String, internal val cap: Int)

    class Rejection internal constructor(
        val code: String, val source: String, val line: Int? = null,
        val trace: List<String> = emptyList(), val traceTruncated: Boolean = false,
    ) : IllegalArgumentException(code) {
        var inputs: List<InputReceipt> = emptyList()
            internal set
    }

    class CheckedGraph internal constructor(
        private val root: Path,
        inputs: List<InputReceipt>,
        val workspaceCount: Int, val seedCount: Int,
        val stanzaCount: Int, val selectorCount: Int,
        val reachableStanzas: Int, val reachableSelectors: Int,
        val declaredEdges: Int, val localLinks: Int,
    ) {
        // Kotlin List is only read-only. Neither getter callers nor constructor aliases may alter receipts.
        val inputs: List<InputReceipt> = Collections.unmodifiableList(ArrayList(inputs))
        val outcome: String get() = "declared-selector-closure"
        val profile: String get() = "registry-sha512-v1"

        /** Re-read every checked input at each invocation/store boundary. Never cache this result. */
        fun recheck() {
            withReader(root) { reader ->
                inputs.forEach { expected ->
                    val actual = reader.read(expected.path, expected.cap).receipt
                    requireSame(expected, actual)
                }
            }
        }

        /** Mandatory after restore and before/after install, including warm/direct entry guards. */
        fun requireWorkingLock(workingLock: String): InputReceipt {
            recheck()
            return withReader(root) { reader ->
                val actual = reader.read(workingLock, inputs.first().cap).receipt
                if (actual.bytes != inputs.first().bytes || actual.sha256 != inputs.first().sha256) {
                    refuse("working-lock-mismatch", workingLock)
                }
                actual
            }
        }
    }

    /** Graph-ready lock-only gate; absence is refused even when all manifest maps are empty. */
    fun preflightStoredLock(root: Path, storedLock: String, limits: Limits = Limits()): InputReceipt =
        withReader(root) { reader ->
            val input = reader.read(storedLock, limits.lockBytes)
            parseLock(input.data, storedLock, Budget(limits))
            input.receipt
        }

    /** Run after the real manifest umbrella/root tasks, strictly BEFORE restore. */
    fun check(
        root: Path, storedLock: String, rootManifest: String,
        expectedStored: InputReceipt? = null, limits: Limits = Limits(),
    ): CheckedGraph = withReader(root) { reader ->
        val budget = Budget(limits)
        val lock = reader.read(storedLock, limits.lockBytes)
        if (expectedStored != null) requireSame(expectedStored, lock.receipt)
        val graph = parseLock(lock.data, storedLock, budget)
        val rootInput = reader.read(rootManifest, minOf(limits.manifestBytes, limits.totalManifestBytes))
        val manifest = parseManifest(rootInput.data, rootManifest, limits)
        val seeds = manifestEdges(manifest, rootManifest, budget, isRoot = true).toMutableList()
        val workspaceValue = if ("workspaces" in manifest) manifest["workspaces"] else emptyList<Any?>()
        val workspaces = workspaceValue as? List<*> ?: refuse("workspace-array-or-cap", rootManifest)
        if (workspaces.size > limits.workspaces) refuse("workspace-array-or-cap", rootManifest)
        if (workspaces.isNotEmpty() && manifest["private"] != true) {
            refuse("workspace-root-not-private", rootManifest)
        }
        val manifestParent = literalPath(rootManifest, "manifest-path").dropLast(1)
        val paths = mutableSetOf<String>()
        val names = mutableSetOf(manifest["name"] as String)
        val locals = mutableMapOf<String, String>()
        var totalBytes = rootInput.data.size
        for (entry in workspaces) {
            val path = entry as? String ?: refuse("unsupported-path", rootManifest)
            val parts = literalPath(path, rootManifest)
            if (!paths.add(path)) refuse("duplicate-workspace-path", rootManifest)
            val relative = (manifestParent + parts + "package.json").joinToString("/")
            val cap = minOf(limits.manifestBytes, limits.totalManifestBytes - totalBytes)
            val input = reader.read(relative, cap)
            totalBytes += input.data.size
            val workspace = parseManifest(input.data, relative, limits)
            seeds += manifestEdges(workspace, relative, budget, isRoot = false)
            val name = workspace["name"] as String
            if (!names.add(name)) refuse("duplicate-workspace-name", relative)
            locals[name] = workspace["version"] as String
        }
        val queue = ArrayDeque<String>()
        val previous = mutableMapOf<String, Predecessor>()
        val reached = mutableSetOf<Int>()
        var localLinks = 0
        fun enqueue(edge: Edge, parent: String?) {
            val localVersion = locals[edge.name]
            if (localVersion != null) {
                if (edge.range != localVersion) refuse("unsupported-local-selector", edge.source, edge.line)
                localLinks++ // Each local manifest was independently seeded above.
                return
            }
            selectorParts(edge.selector, edge.source, edge.line)
            if (previous.putIfAbsent(edge.selector, Predecessor(parent, edge)) == null) {
                queue.addLast(edge.selector)
            }
        }
        seeds.forEach { enqueue(it, null) }
        while (queue.isNotEmpty()) {
            val selector = queue.removeFirst()
            val stanza = graph.index[selector]
            if (stanza == null) {
                val trace = mutableListOf<String>()
                var current: String? = selector
                var origin = previous.getValue(selector).edge
                while (current != null && trace.size < limits.traceItems) {
                    trace += current
                    val predecessor = previous.getValue(current)
                    origin = predecessor.edge
                    current = predecessor.parent
                }
                if (current == null) trace += origin.source
                val missing = previous.getValue(selector).edge
                throw Rejection("missing-selector", missing.source, missing.line, trace.reversed(), current != null)
            }
            if (reached.add(stanza.line)) stanza.edges.forEach { enqueue(it, selector) }
        }
        CheckedGraph(reader.root, reader.receipts.toList(), workspaces.size, seeds.size,
            graph.stanzas.size, graph.index.size, reached.size, previous.size, budget.edges, localLinks)
    }

    private fun refuse(code: String, source: String, line: Int? = null): Nothing =
        throw Rejection(code, source, line)

    private fun requireSame(expected: InputReceipt, actual: InputReceipt) {
        if (actual.path != expected.path || actual.bytes != expected.bytes || actual.sha256 != expected.sha256) {
            refuse("checked-input-changed", actual.path)
        }
    }

    private fun literalPath(value: String, source: String): List<String> {
        val parts = value.split('/')
        if (value.isEmpty() || value.length > 1024 || parts.size > 64 || parts.any {
                it in setOf("", ".", "..") || it.length > 255 || !it.matches(Regex("[A-Za-z0-9._-]+"))
            }) refuse("unsupported-path", source)
        return parts
    }

    private data class Input(val data: ByteArray, val receipt: InputReceipt)

    /**
     * Portable JDK APIs: existing ancestor/leaf links and unknown identities are refused.
     * Pre/post identity checks are NOT descriptor-relative/atomic against concurrent writers.
     * Host/provider behavior (especially Windows junctions) still needs disposable native tests.
     */
    private class Reader(requestedRoot: Path) {
        val root = requestedRoot.toAbsolutePath()
        val receipts = mutableListOf<InputReceipt>()

        fun read(relative: String, cap: Int): Input {
            val parts = literalPath(relative, "input-path")
            try {
                if (root.fileSystem != FileSystems.getDefault() || root.any { it.toString() in setOf(".", "..") }) {
                    refuse("unsupported-reader-root", "project-root")
                }
                val parentPaths = mutableListOf<Path>()
                var current = root.root ?: refuse("unsupported-reader-root", "project-root")
                parentPaths.add(current)
                root.forEach { part -> current = current.resolve(part); parentPaths.add(current) }
                var leaf = root
                parts.forEachIndexed { index, part ->
                    leaf = leaf.resolve(part)
                    if (index < parts.lastIndex) parentPaths.add(leaf)
                }
                val parents = parentPaths.map { path -> path to directory(path, relative) }
                val before = attributes(leaf)
                if (before.isSymbolicLink) refuse("input-path-refused", relative)
                if (!before.isRegularFile) refuse("input-not-regular", relative)
                if (before.fileKey() == null) refuse("reader-identity-unavailable", relative)
                if (before.size() == 0L) refuse("input-empty", relative)
                if (cap <= 0 || before.size() > cap) refuse("input-size-cap", relative)
                val buffer = ByteBuffer.allocate(before.size().toInt() + 1)
                FileChannel.open(leaf, StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS).use { channel ->
                    if (channel.size() != before.size()) refuse("input-changed-during-read", relative)
                    while (buffer.hasRemaining()) {
                        val read = channel.read(buffer)
                        if (read < 0) break
                        if (read == 0) refuse("input-changed-during-read", relative)
                    }
                    if (channel.size() != before.size()) refuse("input-changed-during-read", relative)
                }
                val after = attributes(leaf)
                if (!after.isRegularFile || after.isSymbolicLink || before.fileKey() != after.fileKey() ||
                    before.size() != after.size() || before.lastModifiedTime() != after.lastModifiedTime() ||
                    before.creationTime() != after.creationTime() || buffer.position().toLong() != before.size()) {
                    refuse("input-changed-during-read", relative)
                }
                parents.forEach { (path, expected) ->
                    if (directory(path, relative).fileKey() != expected.fileKey()) {
                        refuse("input-changed-during-read", relative)
                    }
                }
                val data = buffer.array().copyOf(buffer.position())
                val sha = MessageDigest.getInstance("SHA-256").digest(data)
                    .joinToString("") { "%02x".format(it.toInt() and 255) }
                val receipt = InputReceipt(relative, data.size, sha, cap)
                receipts += receipt
                return Input(data, receipt)
            } catch (_: NoSuchFileException) {
                refuse("input-missing", relative)
            } catch (_: java.io.IOException) {
                refuse("input-path-refused", relative)
            } catch (_: SecurityException) {
                refuse("input-path-refused", relative)
            } catch (_: UnsupportedOperationException) {
                refuse("unsupported-reader-provider", relative)
            }
        }

        private fun attributes(path: Path): BasicFileAttributes =
            Files.readAttributes(path, BasicFileAttributes::class.java, LinkOption.NOFOLLOW_LINKS)

        private fun directory(path: Path, source: String): BasicFileAttributes {
            val attr = attributes(path)
            if (!attr.isDirectory || attr.isSymbolicLink) refuse("input-path-refused", source)
            if (attr.fileKey() == null) refuse("reader-identity-unavailable", source)
            return attr
        }
    }

    private inline fun <T> withReader(root: Path, block: (Reader) -> T): T {
        val reader = Reader(root)
        try {
            return block(reader)
        } catch (error: Rejection) {
            error.inputs = reader.receipts.toList()
            throw error
        }
    }

    private const val NUM = "(?:0|[1-9][0-9]*)"
    private val versionSyntax = Regex("$NUM\\.$NUM\\.$NUM(?:-[0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*)?(?:\\+[0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*)?")
    private val publicName = Regex("(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*")
    private val privateName = Regex("(?:@[A-Za-z0-9][A-Za-z0-9._-]*/)?[A-Za-z0-9][A-Za-z0-9._-]*")

    private fun validName(name: String, local: Boolean = false): Boolean =
        name.length <= 214 && name !in setOf("node_modules", "favicon.ico") &&
            (if (local) privateName else publicName).matches(name)

    private fun validVersion(value: String): Boolean {
        if (value.length > 128 || !versionSyntax.matches(value)) return false
        val pre = value.substringBefore('+').substringAfter('-', "")
        return pre.split('.').none { token ->
            token.length > 1 && token[0] == '0' && token.all { it in '0'..'9' }
        }
    }

    private fun rangeVersion(value: String): Boolean {
        if (validVersion(value)) return true
        val parts = value.split('.')
        if (parts.size !in 1..3) return false
        var wildcard = false
        for (part in parts) {
            if (part in setOf("x", "X", "*")) wildcard = true
            else if (wildcard || !part.matches(Regex(NUM))) return false
        }
        return true
    }

    private fun validRange(value: String): Boolean {
        if (value.isEmpty() || value.length > 512 || value != value.trim() || value.any { it.code !in 32..126 }) return false
        if (value.matches(Regex("[a-z][a-z0-9._-]*"))) return true // Syntax only; no tag resolution.
        return value.split(" || ").all { branch ->
            if (" - " in branch) {
                val endpoints = branch.split(" - ")
                endpoints.size == 2 && endpoints.all { rangeVersion(it) }
            } else branch.split(' ').all { rangeVersion(it.replaceFirst(Regex("^(?:<=|>=|[<>=~^])"), "")) }
        }
    }

    private fun selectorParts(selector: String, source: String, line: Int?): Pair<String, String> {
        val start = if (selector.startsWith('@')) selector.indexOf('/', 1) + 1 else 0
        val marker = selector.indexOf('@', start)
        if (selector.length > 728 || marker <= 0) refuse("unsupported-selector", source, line)
        val name = selector.substring(0, marker)
        val range = selector.substring(marker + 1)
        if (range.startsWith("npm:") || range.startsWith("github:") || range.startsWith("git:") ||
            range.startsWith("git+") || range.startsWith("git@")) refuse("unreviewed-reference", source, line)
        if (!validName(name) || !validRange(range)) refuse("unsupported-selector", source, line)
        return name to range
    }

    private data class Edge(val name: String, val range: String, val source: String, val line: Int? = null) {
        val selector get() = "$name@$range"
    }
    private data class Predecessor(val parent: String?, val edge: Edge)
    private data class Stanza(val selectors: List<String>, val line: Int, val edges: List<Edge>)
    private data class LockGraph(val index: Map<String, Stanza>, val stanzas: List<Stanza>)
    private class Budget(val limits: Limits) {
        var edges: Int = 0
        fun edge(source: String, line: Int? = null) {
            if (edges >= limits.edges) refuse("edge-cap", source, line)
            edges++
        }
    }

    private fun decode(data: ByteArray, source: String, code: String): String = try {
        StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(data)).toString()
    } catch (_: java.nio.charset.CharacterCodingException) { refuse(code, source) }

    private class LockCursor(val text: String, val source: String, val line: Int) {
        var pos = 0
        fun syntax(): Nothing = refuse("lock-syntax", source, line)
        fun token(delimiters: String = " "): String {
            val start = pos
            if (start >= text.length) syntax()
            if (text[pos] == '"') {
                val json = JsonReader(text, source, Limits(), "lock-syntax", line, pos)
                val value = json.string()
                pos = json.pos
                if (value.any { it.code < 32 }) syntax()
                return value
            }
            while (pos < text.length && text[pos] !in delimiters) {
                if (text[pos].code < 33 || text[pos] in "\\\"'") syntax()
                pos++
            }
            if (pos == start) syntax()
            return text.substring(start, pos)
        }
        fun consume(value: String) {
            if (!text.startsWith(value, pos)) syntax()
            pos += value.length
        }
        fun end() { if (pos != text.length) syntax() }
    }

    private fun lockPair(text: String, source: String, line: Int, section: Boolean): Pair<String, String?> {
        val cursor = LockCursor(text, source, line)
        val key = cursor.token(" :")
        if (section && cursor.text.startsWith(":", cursor.pos)) {
            cursor.consume(":"); cursor.end()
            return key to null
        }
        cursor.consume(" ")
        val value = cursor.token()
        cursor.end()
        return key to value
    }

    private fun registryFields(selectors: List<String>, fields: Map<String, String>, source: String, line: Int) {
        if (fields.keys != setOf("version", "resolved", "integrity")) refuse("lock-required-field", source, line)
        val names = selectors.map { selectorParts(it, source, line).first }.toSet()
        if (names.size != 1) refuse("lock-mixed-package-stanza", source, line)
        val version = fields.getValue("version")
        if (!validVersion(version)) refuse("unsupported-lock-version", source, line)
        val name = names.single()
        val resolved = fields.getValue("resolved")
        val path = "/$name/-/${name.substringAfterLast('/')}-${version}.tgz"
        // Exact textual identity avoids URL normalization, credentials, ports, encoding and queries.
        val origins = listOf("https://registry.yarnpkg.com", "https://registry.npmjs.org")
        if (resolved.length > 2048 || origins.none { origin ->
                resolved == origin + path ||
                    (resolved.startsWith(origin + path + "#") &&
                        resolved.substring((origin + path + "#").length).matches(Regex("[0-9a-f]{40}")))
            }) refuse("unsupported-resolved-url", source, line)
        val integrity = fields.getValue("integrity")
        if (!integrity.startsWith("sha512-") || integrity.length != 95) refuse("unsupported-integrity", source, line)
        val token = integrity.substring(7)
        val decoded = try { Base64.getDecoder().decode(token) } catch (_: IllegalArgumentException) {
            refuse("unsupported-integrity", source, line)
        }
        if (decoded.size != 64 || Base64.getEncoder().encodeToString(decoded) != token) {
            refuse("unsupported-integrity", source, line)
        }
    }

    private fun parseLock(data: ByteArray, source: String, budget: Budget): LockGraph {
        val limits = budget.limits
        if (data.isEmpty() || data.size > limits.lockBytes) refuse("lock-size-cap", source)
        var lineBytes = 0
        data.forEach { byte ->
            if (byte == 10.toByte()) lineBytes = 0 else {
                lineBytes++
                if (lineBytes > limits.lineBytes) refuse("lock-line-cap", source)
            }
        }
        val text = decode(data, source, "lock-encoding")
        if (text.startsWith('\uFEFF') || '\t' in text || Regex("\\r(?!\\n)").containsMatchIn(text)) {
            refuse("lock-syntax", source)
        }
        val index = linkedMapOf<String, Stanza>()
        val stanzas = mutableListOf<Stanza>()
        var selectors = emptyList<String>()
        var scalar = linkedMapOf<String, String>()
        var maps = linkedMapOf<String, LinkedHashMap<String, Edge>>()
        var section: String? = null
        var blockLine = 0
        var seenHeader = false
        var selectorCount = 0
        fun finish() {
            if (selectors.isEmpty()) return
            registryFields(selectors, scalar, source, blockLine)
            if (maps.values.any { it.isEmpty() }) refuse("lock-empty-section", source, blockLine)
            val normal = maps["dependencies"].orEmpty()
            val optional = maps["optionalDependencies"].orEmpty()
            normal.keys.intersect(optional.keys).forEach { name ->
                if (normal.getValue(name).range != optional.getValue(name).range) {
                    refuse("conflicting-edge", source, optional.getValue(name).line)
                }
            }
            val stanza = Stanza(selectors, blockLine, maps.values.flatMap { it.values })
            stanzas += stanza
            selectors.forEach { index[it] = stanza }
        }
        text.split('\n').forEachIndexed { offset, raw ->
            val number = offset + 1
            val line = raw.removeSuffix("\r")
            if (line.isEmpty()) return@forEachIndexed
            if (line.startsWith('#')) {
                if (line.startsWith("# yarn lockfile")) {
                    if (line != "# yarn lockfile v1" || seenHeader || selectors.isNotEmpty()) {
                        refuse("lock-format-version", source, number)
                    }
                    seenHeader = true
                }
                return@forEachIndexed
            }
            if (line.endsWith(' ') || line.any { it.code < 32 }) refuse("lock-syntax", source, number)
            val indent = line.indexOfFirst { it != ' ' }.let { if (it < 0) line.length else it }
            when {
                indent == 0 -> {
                    if (!seenHeader) refuse("lock-format-version", source, number)
                    finish()
                    if (stanzas.size >= limits.stanzas) refuse("stanza-cap", source, number)
                    val cursor = LockCursor(line, source, number)
                    val header = mutableListOf<String>()
                    while (true) {
                        if (selectorCount + header.size >= limits.selectors) refuse("selector-cap", source, number)
                        header += cursor.token(" ,:")
                        if (cursor.text.startsWith(":", cursor.pos)) {
                            cursor.consume(":"); cursor.end(); break
                        }
                        cursor.consume(", ")
                    }
                    if (header.toSet().size != header.size) refuse("duplicate-selector", source, number)
                    header.forEach { selector ->
                        selectorParts(selector, source, number)
                        if (selector in index) refuse("duplicate-selector", source, number)
                    }
                    selectors = header.toList()
                    selectorCount += selectors.size
                    scalar = linkedMapOf(); maps = linkedMapOf(); section = null; blockLine = number
                }
                indent == 2 && selectors.isNotEmpty() -> {
                    val (name, value) = lockPair(line.substring(2), source, number, section = true)
                    if (name in scalar || name in maps) refuse("duplicate-lock-field", source, number)
                    if (value == null) {
                        if (name !in setOf("dependencies", "optionalDependencies")) refuse("unsupported-lock-field", source, number)
                        maps[name] = linkedMapOf(); section = name
                    } else {
                        if (name !in setOf("version", "resolved", "integrity")) refuse("unsupported-lock-field", source, number)
                        scalar[name] = value; section = null
                    }
                }
                indent == 4 && selectors.isNotEmpty() && section != null -> {
                    val (name, value) = lockPair(line.substring(4), source, number, section = false)
                    val range = value ?: refuse("lock-syntax", source, number)
                    selectorParts("$name@$range", source, number)
                    val mapping = maps.getValue(section!!)
                    if (name in mapping) refuse("duplicate-lock-edge", source, number)
                    budget.edge(source, number)
                    mapping[name] = Edge(name, range, source, number)
                }
                else -> refuse("lock-syntax", source, number)
            }
        }
        finish()
        if (!seenHeader) refuse("lock-format-version", source)
        return LockGraph(index, stanzas)
    }

    private class JsonNumber(val text: String)
    private class JsonReader(
        val text: String, val source: String, val limits: Limits,
        val code: String = "manifest-json", val line: Int? = null, var pos: Int = 0,
    ) {
        private var nodes = 0
        private fun syntax(): Nothing = refuse(code, source, line)
        private fun whitespace() { while (pos < text.length && text[pos] in " \r\n\t") pos++ }
        private fun expect(char: Char) { if (pos >= text.length || text[pos++] != char) syntax() }
        private fun word(word: String, value: Any?): Any? {
            if (!text.startsWith(word, pos)) syntax()
            pos += word.length
            return value
        }
        fun document(): Any? {
            val result = value(0)
            whitespace()
            if (pos != text.length) syntax()
            return result
        }
        fun string(): String {
            expect('"')
            val out = StringBuilder()
            fun hex(): Char {
                if (pos + 4 > text.length) syntax()
                val digits = text.substring(pos, pos + 4)
                if (digits.any { it !in "0123456789abcdefABCDEF" }) syntax()
                pos += 4
                return digits.toInt(16).toChar()
            }
            while (pos < text.length) {
                val char = text[pos++]
                if (char == '"') return out.toString()
                if (char.code < 32) syntax()
                if (char != '\\') { out.append(char); continue }
                if (pos >= text.length) syntax()
                when (val escape = text[pos++]) {
                    '"', '\\', '/' -> out.append(escape)
                    'b' -> out.append('\b')
                    'f' -> out.append('\u000C')
                    'n' -> out.append('\n')
                    'r' -> out.append('\r')
                    't' -> out.append('\t')
                    'u' -> {
                        val first = hex()
                        if (Character.isHighSurrogate(first)) {
                            if (!text.startsWith("\\u", pos)) syntax()
                            pos += 2
                            val second = hex()
                            if (!Character.isLowSurrogate(second)) syntax()
                            out.append(first).append(second)
                        } else {
                            if (Character.isLowSurrogate(first)) syntax()
                            out.append(first)
                        }
                    }
                    else -> syntax()
                }
            }
            syntax()
        }
        private fun value(depth: Int): Any? {
            whitespace()
            if (++nodes > limits.jsonNodes) refuse("manifest-node-cap", source)
            if (pos >= text.length) syntax()
            return when (text[pos]) {
                '{' -> {
                    if (depth >= limits.jsonDepth) refuse("manifest-depth-cap", source)
                    pos++; whitespace()
                    val obj = linkedMapOf<String, Any?>()
                    if (pos < text.length && text[pos] == '}') { pos++; return obj }
                    while (true) {
                        whitespace()
                        val key = string()
                        if (key in obj) syntax()
                        whitespace(); expect(':')
                        obj[key] = value(depth + 1)
                        whitespace()
                        if (pos < text.length && text[pos] == '}') { pos++; break }
                        expect(',')
                    }
                    obj
                }
                '[' -> {
                    if (depth >= limits.jsonDepth) refuse("manifest-depth-cap", source)
                    pos++; whitespace()
                    val list = mutableListOf<Any?>()
                    if (pos < text.length && text[pos] == ']') { pos++; return list }
                    while (true) {
                        list += value(depth + 1)
                        whitespace()
                        if (pos < text.length && text[pos] == ']') { pos++; break }
                        expect(',')
                    }
                    list
                }
                '"' -> string()
                't' -> word("true", true)
                'f' -> word("false", false)
                'n' -> word("null", null)
                else -> {
                    val start = pos
                    if (text[pos] == '-') pos++
                    if (pos >= text.length) syntax()
                    if (text[pos] == '0') pos++ else {
                        if (text[pos] !in '1'..'9') syntax()
                        while (pos < text.length && text[pos] in '0'..'9') pos++
                    }
                    if (pos < text.length && text[pos] == '.') {
                        pos++
                        val digits = pos
                        while (pos < text.length && text[pos] in '0'..'9') pos++
                        if (pos == digits) syntax()
                    }
                    if (pos < text.length && text[pos] in "eE") {
                        pos++
                        if (pos < text.length && text[pos] in "+-") pos++
                        val digits = pos
                        while (pos < text.length && text[pos] in '0'..'9') pos++
                        if (pos == digits) syntax()
                    }
                    if (pos - start > 128) syntax()
                    JsonNumber(text.substring(start, pos))
                }
            }
        }
    }

    @Suppress("UNCHECKED_CAST")
    private fun parseManifest(data: ByteArray, source: String, limits: Limits): Map<String, Any?> {
        if (data.isEmpty() || data.size > limits.manifestBytes) refuse("manifest-size-cap", source)
        val text = decode(data, source, "manifest-json")
        if (text.startsWith('\uFEFF')) refuse("manifest-json", source)
        return JsonReader(text, source, limits).document() as? Map<String, Any?> ?: refuse("manifest-type", source)
    }

    private val dependencyMaps = setOf("dependencies", "devDependencies", "optionalDependencies")
    private val emptyMaps = setOf("peerDependencies", "peerDependenciesMeta", "resolutions", "overrides", "scripts",
        "engines", "config", "installConfig", "publishConfig", "customFields")
    private val emptyLists = setOf("bundledDependencies", "bundleDependencies", "os", "cpu", "libc")
    private val falseFlags = setOf("flat", "engineStrict", "gypfile", "preferGlobal")
    private val inertFields = setOf("name", "version", "private", "main", "module", "browser", "types", "typings",
        "type", "exports", "files", "description", "keywords", "license", "author", "contributors", "repository",
        "bugs", "homepage", "readme", "man")

    private fun manifestEdges(obj: Map<String, Any?>, source: String, budget: Budget, isRoot: Boolean): List<Edge> {
        if (obj.keys.any { it !in dependencyMaps + emptyMaps + emptyLists + falseFlags + inertFields + "workspaces" }) {
            refuse("unsupported-manifest-field", source)
        }
        val name = obj["name"] as? String ?: refuse("manifest-identity", source)
        val version = obj["version"] as? String ?: refuse("manifest-identity", source)
        if (!validName(name, local = true) || !validVersion(version)) refuse("manifest-identity", source)
        if ("private" in obj && obj["private"] !is Boolean) refuse("manifest-type", source)
        if (!isRoot && "workspaces" in obj) refuse("nested-workspaces", source)
        emptyMaps.forEach { key ->
            if (key in obj && (obj[key] !is Map<*, *> || (obj[key] as Map<*, *>).isNotEmpty())) {
                refuse("unsupported-manifest-policy", source)
            }
        }
        emptyLists.forEach { key ->
            if (key in obj && (obj[key] !is List<*> || (obj[key] as List<*>).isNotEmpty())) {
                refuse("unsupported-manifest-policy", source)
            }
        }
        falseFlags.forEach { if (it in obj && obj[it] != false) refuse("unsupported-manifest-policy", source) }
        val edges = mutableListOf<Edge>()
        val values = mutableMapOf<String, String>()
        dependencyMaps.forEach { key ->
            val map = if (key in obj) obj[key] as? Map<*, *> ?: refuse("manifest-dependency-type", source) else emptyMap<Any, Any>()
            map.forEach { (rawName, rawRange) ->
                val edgeName = rawName as? String ?: refuse("manifest-dependency-type", source)
                val range = rawRange as? String ?: refuse("manifest-dependency-type", source)
                if (!validName(edgeName, local = true) || range.length > 512) refuse("manifest-dependency-type", source)
                if (edgeName in values && values[edgeName] != range) refuse("conflicting-edge", source)
                values[edgeName] = range
                budget.edge(source)
                edges += Edge(edgeName, range, source)
            }
        }
        return edges
    }
}
