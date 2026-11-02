# Nonactivated JavaFX dependency patch

`cancel-response-future.patch` modifies OpenJFX's
`com/sun/webkit/network/HTTP2Loader.java`:

> Copyright (c) 2019, 2022, Oracle and/or its affiliates. All rights reserved.

The upstream source is **GPL version 2 with the Classpath exception**, not
Apache-2.0. The generated modified source retains its complete original header.
NativeCmpKit contributors' 2026 cancellation modification retains/extends that
Classpath exception. The exact GPL/exception text is in
`LICENSE-GPLv2-Classpath.txt`; original `ADDITIONAL_LICENSE_INFO` and
`ASSEMBLY_EXCEPTION` are also retained. These legal files were obtained at
OpenJFX21u commit `f5fb746619a202e59585a59ed3b4f4be0e63643e`.

The independently authored regression program and Python runner are part of
NativeCmpKit's Apache-2.0 test tooling. This separation does not relicense
OpenJFX. Its Maven binary/native dependencies retain their upstream licenses.
No dependency classes, JARs, modified packages or source JARs are committed here.

Source provenance: exact official
`org.openjfx:javafx-web:21.0.13:sources` JAR, SHA256
`1e19f7235b5643c9394c0c526daae530268b21ecb16948d0bb2c43114bab5b9e`.
Selected unmodified source SHA256:
`e2413d1ac8cb78be77f97fc6add5e17bee1859e1c5fcbb97481444eb62eac43f`.
See `artifacts.json` and the dated source-acquisition evidence for exact pins.

This test patch is **not activated in Gradle/library builds or publication**.
Any future modified dependency distribution needs its own maintained artifact,
complete corresponding-source/notice obligations, provenance/security review,
API/ABI and consumer/platform verification. Adding these files grants no release
or publication clearance and is not a legal certification of redistribution.
