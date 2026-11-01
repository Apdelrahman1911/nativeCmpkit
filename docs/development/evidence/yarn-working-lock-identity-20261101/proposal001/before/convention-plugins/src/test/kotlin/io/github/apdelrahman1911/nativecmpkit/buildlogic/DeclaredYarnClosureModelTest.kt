// Synthetic JVM models only: owned fixture bytes, no Gradle graph, packages or network.
package io.github.apdelrahman1911.nativecmpkit.buildlogic

import org.junit.After
import org.junit.Before
import org.junit.Assume.assumeNoException
import org.junit.Test
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.assertThrows
import org.junit.Assert.fail
import java.nio.file.Files
import java.nio.file.FileSystemException
import java.nio.file.Path
import java.util.Base64
import java.util.Comparator

class DeclaredYarnClosureModelTest {
    private lateinit var fixtureArea: Path
    private lateinit var root: Path
    private val header = "# yarn lockfile v1\n\n"
    private val sri = "sha512-" + Base64.getEncoder().encodeToString(ByteArray(64) { 7 })
    private val lockPath = "store/yarn.lock"
    private val manifestPath = "generated/package.json"

    @Before fun createOwnedSyntheticFixture() {
        // Canonicalize only the ordinary JVM temp parent before creating our exclusive tree.
        // No preexisting lock/manifest, project output, host cache or custom property is read.
        val tempParent = Path.of(checkNotNull(System.getProperty("java.io.tmpdir"))).toRealPath()
        fixtureArea = Files.createTempDirectory(tempParent, "nativecmpkit-yarn-model-")
        root = Files.createDirectory(fixtureArea.resolve("root"))
        write(manifestPath, manifest())
        write(lockPath, header)
    }

    @After fun removeOnlyOwnedSyntheticFixture() {
        if (!::fixtureArea.isInitialized) return
        // Files.walk does not follow links. Root-link fixtures stay within this owned area.
        Files.walk(fixtureArea).use { paths -> paths.sorted(Comparator.reverseOrder()).forEach { Files.delete(it) } }
        assertFalse(Files.exists(fixtureArea))
    }

    private fun requireSymbolicLinkCapability() {
        val probe = root.resolve("symbolic-link-capability")
        try {
            Files.createSymbolicLink(probe, Path.of("store"))
        } catch (error: UnsupportedOperationException) {
            assumeNoException("This one fixture requires symbolic-link creation support", error)
        } catch (error: FileSystemException) {
            assumeNoException("Symbolic-link setup is unavailable for this one fixture", error)
        }
        // Only capability setup may skip. Reader assertions and their failures are never caught.
        Files.delete(probe)
    }

    private fun write(path: String, value: String) = write(path, value.toByteArray(Charsets.UTF_8))
    private fun write(path: String, value: ByteArray) {
        val target = root.resolve(path)
        Files.createDirectories(target.parent)
        Files.write(target, value)
    }
    private fun quote(value: String) = "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
    private fun mapping(values: Map<String, String>) = values.entries.joinToString(",", "{", "}") { quote(it.key) + ":" + quote(it.value) }
    private fun manifest(
        name: String = "FixtureRoot", version: String = "1.0.0",
        normal: Map<String, String> = emptyMap(), dev: Map<String, String> = emptyMap(),
        optional: Map<String, String> = emptyMap(), workspaces: List<String> = emptyList(),
    ): String = """{"name":${quote(name)},"version":${quote(version)},"private":true,"dependencies":${mapping(normal)},"devDependencies":${mapping(dev)},"optionalDependencies":${mapping(optional)},"workspaces":${workspaces.joinToString(",", "[", "]") { quote(it) }}}"""

    private fun workspace(
        name: String, normal: Map<String, String> = emptyMap(), dev: Map<String, String> = emptyMap(),
        optional: Map<String, String> = emptyMap(),
    ) = manifest(name = name, normal = normal, dev = dev, optional = optional).replace(",\"workspaces\":[]", "")

    private fun stanza(
        name: String, range: String = "1.0.0", version: String = "1.0.0",
        normal: Map<String, String> = emptyMap(), optional: Map<String, String> = emptyMap(),
        selectors: List<String> = listOf("$name@$range"), resolved: String? = null, integrity: String = sri,
    ): String = buildString {
        append(selectors.joinToString(", ") { quote(it) }).append(":\n")
        append("  version ").append(quote(version)).append('\n')
        append("  resolved ").append(quote(resolved ?: "https://registry.yarnpkg.com/$name/-/${name.substringAfterLast('/')}-${version}.tgz")).append('\n')
        append("  integrity ").append(integrity).append('\n')
        for ((key, values) in listOf("dependencies" to normal, "optionalDependencies" to optional)) {
            if (values.isNotEmpty()) {
                append("  $key:\n")
                values.forEach { (edge, value) -> append("    ").append(quote(edge)).append(' ').append(quote(value)).append('\n') }
            }
        }
        append('\n')
    }
    private fun installModel(lock: String, rootManifest: String = manifest(normal = mapOf("parent" to "1.0.0"))) {
        write(lockPath, lock); write(manifestPath, rootManifest)
    }
    private fun check(limits: DeclaredYarnClosure.Limits = DeclaredYarnClosure.Limits()) =
        DeclaredYarnClosure.check(root, lockPath, manifestPath, limits = limits)
    private fun rejected(code: String, action: () -> Unit): DeclaredYarnClosure.Rejection {
        try { action(); fail("Expected fixed policy rejection: $code") }
        catch (error: DeclaredYarnClosure.Rejection) { assertEquals(code, error.code); return error }
        throw AssertionError("Unreachable")
    }

    @Test fun rootNormalDevOptionalSeedsAndGroupedScopedSelectorsAreExact() {
        val lock = header + stanza("parent", normal = mapOf("@scope/leaf" to "^1.0.0")) +
            stanza("@scope/leaf", selectors = listOf("@scope/leaf@^1.0.0", "@scope/leaf@1.0.0")) + stanza("tool") + stanza("opt")
        installModel(lock, manifest(normal = mapOf("parent" to "1.0.0"), dev = mapOf("tool" to "1.0.0"), optional = mapOf("opt" to "1.0.0")))
        val result = check()
        assertEquals("declared-selector-closure", result.outcome)
        assertEquals(3, result.seedCount); assertEquals(4, result.reachableStanzas)
        assertEquals(5, result.selectorCount); assertEquals(4, result.reachableSelectors)
    }

    @Test fun emptyRootMapsDoNotSkipAnyWorkspaceDependencyMap() {
        write(manifestPath, manifest(workspaces = listOf("packages/one", "packages/two", "packages/three")))
        write("generated/packages/one/package.json", workspace(name = "LocalOne", normal = mapOf("normal" to "1.0.0")))
        write("generated/packages/two/package.json", workspace(name = "LocalTwo", dev = mapOf("dev" to "1.0.0")))
        write("generated/packages/three/package.json", workspace(name = "LocalThree", optional = mapOf("optional" to "1.0.0")))
        write(lockPath, header + stanza("normal") + stanza("dev"))
        val missing = rejected("missing-selector") { check() }
        assertEquals("generated/packages/three/package.json", missing.source)
        write(lockPath, header + stanza("normal") + stanza("dev") + stanza("optional"))
        val result = check()
        assertEquals(3, result.workspaceCount); assertEquals(3, result.seedCount); assertEquals(5, result.inputs.size)
    }

    @Test fun missingStoreNeverMeansAnEmptyGraphOrBootstrap() {
        Files.delete(root.resolve(lockPath))
        val failure = rejected("input-missing") { check() }
        assertEquals(lockPath, failure.source); assertTrue(failure.inputs.isEmpty())
        rejected("input-missing") { DeclaredYarnClosure.preflightStoredLock(root, lockPath) }
    }

    @Test fun existingHeaderOnlyStoreRequiresAllExternalSeedsToBeEmpty() {
        val empty = check()
        assertEquals(0, empty.seedCount); assertEquals(0, empty.stanzaCount)
        write(manifestPath, manifest(workspaces = listOf("packages/one")))
        write("generated/packages/one/package.json", workspace(name = "LocalOne", dev = mapOf("tool" to "1.0.0")))
        rejected("missing-selector") { check() }
    }

    @Test fun retainedParentWithMissingLeafHasAnOwnedBoundedTrace() {
        installModel(header + stanza("parent", normal = mapOf("leaf" to "1.0.0")))
        val error = rejected("missing-selector") { check() }
        assertEquals(listOf(manifestPath, "parent@1.0.0", "leaf@1.0.0"), error.trace)
        assertEquals(lockPath, error.source); assertEquals(8, error.line); assertFalse(error.traceTruncated)
        assertEquals(2, error.inputs.size)
    }

    @Test fun optionalTransitiveEdgeCannotDisappearFromTraversal() {
        installModel(header + stanza("parent", optional = mapOf("optional-leaf" to "1.0.0")))
        rejected("missing-selector") { check() }
        write(lockPath, header + stanza("parent", optional = mapOf("optional-leaf" to "1.0.0")) + stanza("optional-leaf"))
        assertEquals(2, check().reachableStanzas)
    }

    @Test fun exactRangesCannotBeCollapsedByNameOrChosenVersion() {
        installModel(header + stanza("parent", normal = mapOf("leaf" to "^1.0.0")) + stanza("leaf"))
        val error = rejected("missing-selector") { check() }
        assertEquals("leaf@^1.0.0", error.trace.last())
        write(lockPath, header + stanza("parent", normal = mapOf("leaf" to "^1.0.0")) + stanza("leaf", selectors = listOf("leaf@1.0.0", "leaf@^1.0.0")))
        assertEquals(3, check().selectorCount)
    }

    @Test fun cyclicAndSharedSelectorsFinishWithoutDuplicatingStanzas() {
        installModel(header + stanza("parent", normal = mapOf("leaf" to "1.0.0", "shared" to "1.0.0")) +
            stanza("leaf", normal = mapOf("parent" to "1.0.0", "shared" to "1.0.0")) + stanza("shared"))
        val result = check()
        assertEquals(3, result.reachableStanzas); assertEquals(3, result.reachableSelectors)
    }

    @Test fun longMissingChainKeepsOnlyTheConfiguredTraceTail() {
        val blocks = (0..15).joinToString("") { stanza("node-$it", normal = mapOf("node-${it + 1}" to "1.0.0")) }
        installModel(header + blocks, manifest(normal = mapOf("node-0" to "1.0.0")))
        val error = rejected("missing-selector") { check(DeclaredYarnClosure.Limits(traceItems = 3)) }
        assertTrue(error.traceTruncated); assertEquals(3, error.trace.size); assertEquals("node-16@1.0.0", error.trace.last())
    }

    @Test fun duplicateSelectorsFieldsAndEdgesAreRefused() {
        val candidates = listOf(
            "duplicate-selector" to (header + stanza("parent", selectors = listOf("parent@1.0.0", "parent@1.0.0"))),
            "duplicate-selector" to (header + stanza("parent") + stanza("parent")),
            "duplicate-lock-field" to (header + stanza("parent").replace("  version", "  version \"1.0.0\"\n  version")),
            "duplicate-lock-edge" to (header + stanza("parent", normal = mapOf("leaf" to "1.0.0")).replace("    \"leaf\"", "    \"leaf\" \"1.0.0\"\n    \"leaf\"")),
        )
        candidates.forEach { (code, lock) -> installModel(lock); rejected(code) { check() } }
    }

    @Test fun conflictingNormalOptionalDeclarationsRefuseAmbiguity() {
        installModel(header + stanza("parent", normal = mapOf("leaf" to "1.0.0"), optional = mapOf("leaf" to "2.0.0")))
        rejected("conflicting-edge") { check() }
        installModel(header + stanza("parent"), manifest(normal = mapOf("parent" to "1.0.0"), optional = mapOf("parent" to "2.0.0")))
        rejected("conflicting-edge") { check() }
    }

    @Test fun unsupportedGrammarSectionsIndentationAndJunkAreRefused() {
        val base = header + stanza("parent")
        listOf(
            "unsupported-lock-field" to base.replace("  version", "  unknown"),
            "unsupported-lock-field" to (base + "  peerDependencies:\n    leaf \"1.0.0\"\n"),
            "lock-empty-section" to (base + "  dependencies:\n"),
            "lock-syntax" to base.replace("  version", "   version"),
            "lock-syntax" to base.replace("  version \"1.0.0\"", "  version \"1.0.0\" trailing"),
            "lock-syntax" to base.replace("\"parent@1.0.0\":", "\"parent@1.0.0:\n"),
            "lock-format-version" to base.replace("# yarn lockfile v1", "# yarn lockfile v2"),
        ).forEach { (code, lock) -> installModel(lock); rejected(code) { check() } }
    }

    @Test fun jsonEscapesAreDecodedBeforeExactSelectorComparison() {
        val lock = header + stanza("parent").replace("parent@1.0.0", "parent@\\u0031.0.0")
        installModel(lock)
        assertEquals(1, check().reachableSelectors)
        installModel(lock.replace("\\u0031", "\\uD800"))
        rejected("lock-syntax") { check() }
    }

    @Test fun encodingTabsBomAndUnpairedCrAreRefusedWithoutRewriting() {
        write(lockPath, byteArrayOf(0xC3.toByte(), 0x28))
        rejected("lock-encoding") { check() }
        listOf("\uFEFF$header", header.replace("\n", "\r"), header + "\t").forEach { lock ->
            write(lockPath, lock); rejected("lock-syntax") { check() }
        }
        write(lockPath, "# comment only\n")
        rejected("lock-format-version") { check() }
    }

    @Test fun parserAndManifestBudgetsAreHardCaps() {
        installModel(header + stanza("parent", normal = mapOf("leaf" to "1.0.0")) + stanza("leaf"))
        listOf(
            "input-size-cap" to DeclaredYarnClosure.Limits(lockBytes = 8),
            "lock-line-cap" to DeclaredYarnClosure.Limits(lineBytes = 8),
            "stanza-cap" to DeclaredYarnClosure.Limits(stanzas = 1),
            "selector-cap" to DeclaredYarnClosure.Limits(selectors = 1),
            "edge-cap" to DeclaredYarnClosure.Limits(edges = 1),
            "input-size-cap" to DeclaredYarnClosure.Limits(manifestBytes = 8),
            "manifest-node-cap" to DeclaredYarnClosure.Limits(jsonNodes = 2),
        ).forEach { (code, limits) -> rejected(code) { check(limits) } }
        write(manifestPath, """{"name":"FixtureRoot","version":"1.0.0","description":[[[]]]}""")
        rejected("manifest-depth-cap") { check(DeclaredYarnClosure.Limits(jsonDepth = 3)) }
    }

    @Test fun duplicateJsonKeysAndInvalidUnicodeNumbersAndTypesAreRefused() {
        val cases = listOf(
            "manifest-json" to """{"name":"FixtureRoot","name":"Other","version":"1.0.0"}""",
            "manifest-json" to """{"name":"FixtureRoot","version":"1.0.0","description":null,"description":"x"}""",
            "manifest-json" to """{"name":"FixtureRoot","version":"1.0.0","description":"\uD800"}""",
            "manifest-json" to """{"name":"FixtureRoot","version":"1.0.0","description":NaN}""",
            "manifest-json" to """{"name":"FixtureRoot","version":"1.0.0","description":01}""",
            "manifest-json" to """{"name":"FixtureRoot","version":"1.0.0"}{}""",
            "manifest-type" to "[]",
            "manifest-dependency-type" to manifest().replace("\"dependencies\":{}", "\"dependencies\":null"),
            "workspace-array-or-cap" to manifest().replace("\"workspaces\":[]", "\"workspaces\":null"),
        )
        cases.forEach { (code, body) -> write(manifestPath, body); rejected(code) { check() } }
        write(manifestPath, """{"name":"FixtureRoot","version":"1.0.0","description":"\uD83D\uDE80"}""")
        assertEquals(0, check().seedCount)
    }

    @Test fun nonemptyUnreviewedManifestPoliciesAndUnknownFieldsAreRefused() {
        val cases = listOf(
            "unsupported-manifest-policy" to "\"scripts\":{\"install\":\"node ignored.js\"}",
            "unsupported-manifest-policy" to "\"resolutions\":{\"leaf\":\"2.0.0\"}",
            "unsupported-manifest-policy" to "\"peerDependencies\":{\"leaf\":\"1.0.0\"}",
            "unsupported-manifest-policy" to "\"bundledDependencies\":[\"leaf\"]",
            "unsupported-manifest-policy" to "\"os\":[\"linux\"]",
            "unsupported-manifest-policy" to "\"flat\":true",
            "unsupported-manifest-field" to "\"unknownResolver\":{}",
        )
        cases.forEach { (code, field) ->
            write(manifestPath, """{"name":"FixtureRoot","version":"1.0.0",$field}""")
            rejected(code) { check() }
        }
    }

    @Test fun allLocalManifestsAreSeededAndOnlyExactLocalVersionsLink() {
        write(manifestPath, manifest(workspaces = listOf("packages/one", "packages/two")))
        write("generated/packages/one/package.json", workspace(name = "LocalOne", normal = mapOf("LocalTwo" to "1.0.0")))
        write("generated/packages/two/package.json", workspace(name = "LocalTwo", optional = mapOf("external" to "1.0.0")))
        write(lockPath, header + stanza("external"))
        val result = check()
        assertEquals(1, result.localLinks); assertEquals(2, result.seedCount); assertEquals(1, result.reachableStanzas)
        for (range in listOf("^1.0.0", "workspace:1.0.0", "file:../two")) {
            write("generated/packages/one/package.json", workspace(name = "LocalOne", normal = mapOf("LocalTwo" to range)))
            rejected("unsupported-local-selector") { check() }
        }
    }

    @Test fun workspacePathsNamesCapsAndPrivateRootCannotBeAmbiguous() {
        write("generated/packages/one/package.json", workspace(name = "LocalOne"))
        write("generated/packages/two/package.json", workspace(name = "LocalOne"))
        write(manifestPath, manifest(workspaces = listOf("packages/one", "packages/one")))
        rejected("duplicate-workspace-path") { check() }
        write(manifestPath, manifest(workspaces = listOf("packages/one", "packages/two")))
        rejected("duplicate-workspace-name") { check() }
        for (path in listOf("../escape", "packages/*", "/absolute", "packages//one", "packages/./one", "packages\\one")) {
            write(manifestPath, manifest(workspaces = listOf(path)))
            rejected("unsupported-path") { check() }
        }
        write(manifestPath, manifest(workspaces = listOf("packages/one")).replace("\"private\":true", "\"private\":false"))
        rejected("workspace-root-not-private") { check() }
        write(manifestPath, manifest(workspaces = listOf("packages/one")))
        rejected("workspace-array-or-cap") { check(DeclaredYarnClosure.Limits(workspaces = 0)) }
        write("generated/packages/one/package.json", manifest(name = "LocalOne")) // A workspace declaring even an empty nested list is unreviewed.
        rejected("nested-workspaces") { check() }
    }

    @Test fun missingWorkspaceManifestAndAggregateBudgetAreRefused() {
        write(manifestPath, manifest(workspaces = listOf("packages/missing")))
        rejected("input-missing") { check() }
        write("generated/packages/missing/package.json", manifest(name = "LocalOne").replace(",\"workspaces\":[]", ""))
        val rootSize = Files.size(root.resolve(manifestPath)).toInt()
        rejected("input-size-cap") { check(DeclaredYarnClosure.Limits(totalManifestBytes = rootSize)) }
    }

    @Test fun registryOriginPackageVersionAndFragmentIdentityAreExact() {
        val valid = "https://registry.yarnpkg.com/parent/-/parent-1.0.0.tgz"
        for (url in listOf(
            valid.replace("https://", "http://"), valid.replace("yarnpkg.com", "example.invalid"),
            valid.replace("registry.yarnpkg.com", "user@registry.yarnpkg.com"),
            valid.replace("registry.yarnpkg.com", "registry.yarnpkg.com:443"), valid + "?token=fixture",
            valid + "#", valid + "#" + "A".repeat(40), valid.replace("parent-1.0.0", "other-1.0.0"),
            valid.replace("parent-1.0.0", "parent-2.0.0"), valid.replace("/parent/-/", "/%70arent/-/"),
        )) { installModel(header + stanza("parent", resolved = url)); rejected("unsupported-resolved-url") { check() } }
        installModel(header + stanza("parent", resolved = valid.replace("yarnpkg.com", "npmjs.org") + "#" + "a".repeat(40)))
        assertEquals(1, check().reachableStanzas)
    }

    @Test fun mixedPackageStanzaAndNonSemverVersionAreRefused() {
        installModel(header + stanza("parent", selectors = listOf("parent@1.0.0", "other@1.0.0")))
        rejected("lock-mixed-package-stanza") { check() }
        for (version in listOf("01.0.0", "1.0", "1.0.0-01", "v1.0.0")) {
            installModel(header + stanza("parent", version = version)); rejected("unsupported-lock-version") { check() }
        }
    }

    @Test fun malformedOrNoncanonicalSha512TokensAreRefused() {
        val canonical = Base64.getEncoder().encodeToString(ByteArray(64))
        for (token in listOf("sha256-$canonical", "sha512-${canonical.dropLast(1)}", "sha512-$canonical ",
            "sha512-" + "!".repeat(86) + "==", "sha512-" + canonical.dropLast(3) + "B==")) {
            installModel(header + stanza("parent", integrity = quote(token)))
            rejected("unsupported-integrity") { check() }
        }
        installModel(header + stanza("parent").replace("  integrity $sri\n", ""))
        rejected("lock-required-field") { check() }
    }

    @Test fun validWrongSriAndUnsatisfiedSemverAreExplicitlyOnlySyntax() {
        val wrongValid = "sha512-" + Base64.getEncoder().encodeToString(ByteArray(64))
        installModel(header + stanza("parent", range = ">=2.0.0", version = "1.0.0", integrity = wrongValid), manifest(normal = mapOf("parent" to ">=2.0.0")))
        val result = check()
        assertEquals("declared-selector-closure", result.outcome)
        assertEquals(1, result.reachableSelectors) // Neither artifact integrity nor range satisfaction is claimed.
    }

    @Test fun aliasesGitAndOtherProtocolsHaveNoImplicitWaiver() {
        for (range in listOf("npm:parent@^1.0.0", "github:Kotlin/karma#6.4.5", "git+https://example.invalid/repo.git#abc")) {
            installModel(header + stanza("parent", normal = mapOf("unreviewed" to range)))
            rejected("unreviewed-reference") { check() }
        }
        for (range in listOf("https://example.invalid/archive.tgz", "file:../local", "workspace:*", "1.0.0,2.0.0")) {
            installModel(header + stanza("parent", normal = mapOf("unreviewed" to range)))
            rejected("unsupported-selector") { check() }
        }
    }

    @Test fun storedRootAndWorkspaceHashesAreCheckedAgainAtEveryBoundary() {
        write(manifestPath, manifest(workspaces = listOf("packages/one")))
        val workspacePath = "generated/packages/one/package.json"
        write(workspacePath, manifest(name = "LocalOne").replace(",\"workspaces\":[]", ""))
        val originalManifest = Files.readAllBytes(root.resolve(manifestPath))
        val originalWorkspace = Files.readAllBytes(root.resolve(workspacePath))
        val result = check()
        result.recheck()
        for ((path, original) in listOf(lockPath to header.toByteArray(), manifestPath to originalManifest, workspacePath to originalWorkspace)) {
            write(path, original + byteArrayOf(10))
            rejected("checked-input-changed") { result.recheck() }
            write(path, original)
        }
        result.recheck()
    }

    @Test fun checkedInputReceiptsAreAnUnmodifiableOwnedSnapshot() {
        val workspacePath = "generated/packages/one/package.json"
        write(manifestPath, manifest(workspaces = listOf("packages/one")))
        write(workspacePath, workspace(name = "LocalOne"))
        val result = check()
        val expected = result.inputs.toList()
        assertEquals(listOf(lockPath, manifestPath, workspacePath), expected.map { it.path })

        // The JVM getter exposes java.util.List even when Kotlin's property type is read-only.
        val writable = result.inputs as MutableList<DeclaredYarnClosure.InputReceipt>
        assertThrows(UnsupportedOperationException::class.java) { writable.removeAt(1) }
        assertThrows(UnsupportedOperationException::class.java) { writable[0] = writable[0].copy(sha256 = "0".repeat(64)) }
        assertThrows(UnsupportedOperationException::class.java) { writable.clear() }
        val iterator = writable.listIterator()
        iterator.next()
        assertThrows(UnsupportedOperationException::class.java) { iterator.remove() }
        assertEquals(expected, result.inputs)

        // An unmodifiable view without a copy would still retain this writable constructor alias.
        val supplied = expected.toMutableList()
        val copied = DeclaredYarnClosure.CheckedGraph(root, supplied,
            result.workspaceCount, result.seedCount, result.stanzaCount, result.selectorCount,
            result.reachableStanzas, result.reachableSelectors, result.declaredEdges, result.localLinks)
        supplied.clear()
        assertEquals(expected, copied.inputs)
        val working = "generated/yarn.lock"
        write(working, header)
        copied.requireWorkingLock(working)
        write(workspacePath, workspace(name = "LocalOne") + "\n")
        rejected("checked-input-changed") { copied.recheck() }
        rejected("checked-input-changed") { copied.requireWorkingLock(working) }
    }

    @Test fun graphReadyReceiptCannotBeReplacedBeforeClosure() {
        val expected = DeclaredYarnClosure.preflightStoredLock(root, lockPath)
        write(lockPath, header + "# changed valid lock bytes\n")
        rejected("checked-input-changed") { DeclaredYarnClosure.check(root, lockPath, manifestPath, expected) }
    }

    @Test fun workingBoundaryChecksAlwaysRunAndDoNotNormalizeCrLf() {
        installModel((header + stanza("parent")).replace("\n", "\r\n"))
        val result = check()
        val working = "generated/yarn.lock"
        write(working, Files.readAllBytes(root.resolve(lockPath)))
        result.requireWorkingLock(working)
        result.requireWorkingLock(working) // A second warm model call is not skipped through a cached success output.
        write(working, (header + stanza("parent")))
        rejected("working-lock-mismatch") { result.requireWorkingLock(working) }
        Files.delete(root.resolve(working))
        rejected("input-missing") { result.requireWorkingLock(working) }
    }

    @Test fun existingLeafAndAncestorSymlinksAreRefused() {
        requireSymbolicLinkCapability()
        val originalLock = Files.readAllBytes(root.resolve(lockPath))
        write("real-lock", originalLock)
        Files.delete(root.resolve(lockPath)); Files.createSymbolicLink(root.resolve(lockPath), Path.of("../real-lock"))
        rejected("input-path-refused") { check() }
        Files.delete(root.resolve(lockPath)); write(lockPath, originalLock)
        val realDirectory = root.resolve("real-manifests"); Files.createDirectory(realDirectory)
        Files.write(realDirectory.resolve("package.json"), manifest().toByteArray())
        Files.delete(root.resolve(manifestPath)); Files.delete(root.resolve("generated"))
        Files.createSymbolicLink(root.resolve("generated"), Path.of("real-manifests"))
        rejected("input-path-refused") { check() }
        Files.delete(root.resolve("generated")); write(manifestPath, manifest())
        val rootLink = root.resolveSibling(root.fileName.toString() + "-link")
        Files.createSymbolicLink(rootLink, root.fileName)
        try { rejected("input-path-refused") { DeclaredYarnClosure.check(rootLink, lockPath, manifestPath) } }
        finally { Files.delete(rootLink) }
    }

    @Test fun existingNonregularStoredInputIsRefusedWithoutSymlinkCapability() {
        Files.delete(root.resolve(lockPath)); Files.createDirectory(root.resolve(lockPath))
        rejected("input-not-regular") { check() }
    }

    @Test fun removingBothAnEdgeAndItsStanzaDemonstratesDeclaredMetadataLimit() {
        installModel(header + stanza("parent", normal = mapOf("leaf" to "1.0.0")) + stanza("leaf"))
        assertEquals(2, check().reachableStanzas)
        write(lockPath, header + stanza("parent"))
        assertEquals(1, check().reachableStanzas) // A lock checker cannot independently recover omitted metadata.
    }
}
