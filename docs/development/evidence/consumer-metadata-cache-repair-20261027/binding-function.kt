/** Exact metadata-to-Maven binding; a retained Gradle display name is not a Maven URL. */
fun bindCandidateArtifact(id: ModuleComponentIdentifier, resolved: File): Map<String, Any> {
    val suffixes = setOf("", "-desktop", "-android", "-js", "-wasm-js", "-iosarm64", "-iossimulatorarm64")
    val matchingRoots = candidateRoots.filter { root -> suffixes.any { id.module == root + it } }
    check(id.group == candidateGroup && id.version == candidateVersion && matchingRoots.size == 1) {
        "Unselected candidate coordinate: $id"
    }
    val root = matchingRoots.single()
    check(resolved.isFile && resolved.extension in setOf("jar", "aar", "klib")) {
        "Only directly published primary candidate files are eligible: $id/${resolved.name}"
    }
    val relativeDirectory = "${candidateGroup.replace('.', '/')}/${id.module}/$candidateVersion/"
    val metadataRelative = relativeDirectory + "${id.module}-$candidateVersion.module"
    val metadataFile = candidateRepository.resolve(metadataRelative)
    check(metadataFile.isFile && metadataFile.length() in 1..(2L * 1024 * 1024))
    val metadata = JsonSlurper().parse(metadataFile) as? Map<*, *> ?: error("Invalid module metadata: $id")
    val component = metadata["component"] as? Map<*, *> ?: error("Missing metadata component: $id")
    check(metadata["formatVersion"] == "1.1" && component["group"] == candidateGroup &&
        component["module"] == root && component["version"] == candidateVersion)
    val rootMetadataRelative = "${candidateGroup.replace('.', '/')}/$root/$candidateVersion/$root-$candidateVersion.module"
    check(candidateRepository.resolve(rootMetadataRelative).isFile)
    val rootUrl = if (id.module == root) null else "../../$root/$candidateVersion/$root-$candidateVersion.module"
    check(component["url"] == rootUrl) { "Module metadata redirects outside the exact candidate root: $id" }
    val canonicalName = "${id.module}-$candidateVersion.${resolved.extension}"
    // These explicit roots/target suffixes map to the retained public Calf Gradle project names.
    // Never accept an arbitrary filename, another group/module, sources or a URL/path alias.
    val retainedName = "calf-${id.module.removePrefix("nativecmpkit-")}-$candidateVersion.${resolved.extension}"
    val variants = metadata["variants"] as? List<*> ?: error("Missing metadata variants: $id")
    check(variants.size in 1..128)
    val primaryBindings = variants.mapNotNull { entry ->
        val variant = entry as? Map<*, *> ?: error("Invalid metadata variant: $id")
        val attributes = variant["attributes"] as? Map<*, *> ?: error("Missing variant attributes: $id")
        if (attributes["org.gradle.category"] != "library") return@mapNotNull null
        // KMP root available-at variants have no local files; they are not payload substitutions.
        val files = variant["files"] as? List<*> ?: return@mapNotNull null
        check(files.size == 1)
        val declared = files.single() as? Map<*, *> ?: error("Invalid primary metadata file: $id")
        check(declared["name"] in setOf(canonicalName, retainedName) && declared["name"] == resolved.name &&
            declared["url"] == canonicalName) { "Resolved name/metadata URL do not bind to the exact candidate: $id" }
        val stagedRelative = relativeDirectory + canonicalName
        val staged = candidateRepository.resolve(stagedRelative)
        val hash = artifactSha256(resolved)
        check(staged.isFile && artifactSha256(staged) == hash && staged.length() == resolved.length()) {
            "Resolved candidate bytes do not match the actual staged Maven file: $id/${resolved.name}"
        }
        check((declared["size"] is Int || declared["size"] is Long) &&
            (declared["size"] as Number).toLong() == resolved.length() && declared["sha256"] == hash) {
            "Module metadata size/hash does not match staged/resolved bytes: $id"
        }
        mapOf("declared_file_name" to resolved.name, "declared_file_url" to canonicalName,
            "staged_file" to stagedRelative, "metadata_file" to metadataRelative,
            "metadata_sha256" to artifactSha256(metadataFile), "bytes" to resolved.length(), "sha256" to hash)
    }.distinct()
    check(primaryBindings.size == 1) { "Missing or conflicting primary metadata bindings: $id" }
    return primaryBindings.single()
}

