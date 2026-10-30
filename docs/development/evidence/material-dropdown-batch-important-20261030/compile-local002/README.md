# Failed dropdown test compilation retained

Gradle exits1 after35.01s; zero tests. NavigationEvent imports were missing from
the test compile classpath: Compose UI declares the bridge runtime-only. The
parameter-inference error is consequential, not a separate production defect.
The owning correction adds the exact already-used runtime dependency to
`materialTest` only; no production/public API dependency is exported. See the
[actual compile recovery](../compile-local003/README.md). This failure and the
earlier3-pass/one-failure runtime diagnostic remain unchanged.
