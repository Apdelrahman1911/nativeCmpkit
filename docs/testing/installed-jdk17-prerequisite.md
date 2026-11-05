# Installed JDK17 prerequisite

Use the repository's pinned Gradle **9.7.1** wrapper and an already installed
full **JDK17** (java and javac) matching the actual host architecture. The
supported verification jobs provision Temurin17 before invoking JVM work. This
is a build/verification prerequisite, not a new public NativeCmpKit runtime/API
requirement, and it does not change the Java17 bytecode targets.

Set JAVA_HOME to that JDK17 installation and put its bin directory first on
PATH **before** invoking the wrapper or verification controller. A newer JDK
is not a substitute for a fixture's exact jvmToolchain(17) request or the
recorded actual-JDK17 daemon checks. Do not commit machine-specific Java-home
paths, weaken those checks, or inherit foreign init scripts/user properties.

The root settings deliberately configure **no JVM download repository**.
Gradle's local JDK discovery must find the supplied installed JDK17; missing or
intentionally disabled local discovery is a prerequisite error, not permission
to add a remote resolver, approve observed checksums, or trust a revoked signer.
If using custom local discovery settings, review the explicit installed-JDK
configuration separately. No remote JVM provisioning fallback is provided by
this build. Installing/selecting the JDK remains the user's or CI setup's job.

The convention build and all currently included libraries/samples use Java17
compatibility/targets. Independent artifact consumers explicitly request JDK17
without a Foojay plugin or included producer build. A separate navigation/geo
SOURCE-INTEGRATION fixture deliberately includes ROOT for two unpublished
modules; it shares this installed-JDK17 prerequisite and is NOT ordinary Maven
evidence. Its existing explicit substitutions stay unchanged. The dormant calf-media
and calf-notifications source directories still request JDK11 but are **not
included** in the current root project graph. Their requests are not changed or
qualified by this prerequisite. Re-enabling either requires separate JDK11 and
compatibility evidence; do not silently substitute17 or call those modules N/A.

This removes the redundant Foojay settings-plugin dependency, not Gradle's
built-in toolchain support. Developers without an installed matching JDK lose
only automatic remote JVM provisioning and must install/select the prerequisite.
Kotlin/Compose/AGP versions, repositories, module/API–ABI inputs and publication
interlocks are unchanged. Other dependency artifacts still need independent
trust/coverage review: strict verification metadata, ordinary-consumer/native
acceptance, security/legal and release gates remain mandatory. No build,
publication, deployment or issue closure is authorized by this document.
