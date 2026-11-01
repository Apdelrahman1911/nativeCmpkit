# Independent local compiler002 review

Read-only inspection of retained originals; no build, test, SDK, network or Git invocation.

- Original log/header/result agree: exit 0 / 130.03 s. Android reporter assembly and Desktop test compilation completed with bare successful task markers, not cache/up-to-date/skip markers. Console marker counts are separate from the logged 67 actionable tasks.
- Real daemon marker: Gradle 9.7.1 / JDK 17.0.20, configured launcher equals the daemon.
- Frozen 1112 library / 1189 combined before/after maps are byte/entry exact. Current readback matches all except the explicitly recorded later camera017 guard update. No Git or uploaded actual native map was checked.
- Reporter APK: 9697713 bytes, SHA256 06232add37db83bcaca93084f49745a2818127fb96007767fe7fb1af5a934524. Metadata/binary manifest agree on the reporter package and runner; minSdk23/targetSdk37 is packaging identity, not native API-range acceptance.
- Two selected methods retain the new marker in RuntimeVisibleAnnotations. Java/Kotlin RUNTIME retention and METHOD/FUNCTION targets are present in passively parsed classfiles. No class loading, DEX annotation dispatch or instrumentation selector execution occurred.
- Compiler001 remains failed: exact initialization-scope refusal, exit 1 / 11.0 s, zero task/JVM markers. Its 1111/1188 maps differ from compiler002 at only three tooling inputs. It is not a compiler/native failure.
- ZERO native, browser, Desktop, instrumentation, installation or XML test execution. Signing/cache markers do not establish installed identity, runtime/security/dependency trust or speedup acceptance.

Only public-safe scalar review files are delivered. Raw originals, APK, classfiles, source contents and private paths are excluded. Two reviewer collection-assumption refusals remain privately retained and did not cause build/test replay. Root owns integration, requests and issue decisions.
