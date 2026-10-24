#!/usr/bin/env python3
"""Reproduce the permissions/geo baseline logic audit without Gradle or devices.

Uses exact original source at the preserved Git commit; CoreLocation/Build/Stable
are explicit test adapters, NOT real platform APIs. Never downloads dependencies.
Requires cached Kotlin compiler 2.4.20 jars and a Java runtime. Writes only to a
fresh temporary directory, deleted on exit. This is audit evidence, not a full
library/native build or a regression suite wired into production CI.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

BASELINE = "af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6"
COMMON = "calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/"
ANDROID = "calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/"
SOURCES = {
    "PermissionsUtil.kt": COMMON + "PermissionsUtil.kt",
    "AndroidPermissionRegistry.kt": ANDROID + "AndroidPermissionRegistry.kt",
    "PermissionHelper.kt": "calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/PermissionHelper.kt",
    "LatLng.kt": "calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LatLng.kt",
    "BackgroundLocationPermissionHelper.kt": "calf-permissions/background-location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BackgroundLocationPermissionHelper.kt",
    "LocationPermissionHelper.kt": "calf-permissions/location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocationPermissionHelper.kt",
}

MAIN = r'''
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)
package com.mohamedrejeb.calf.permissions
import com.mohamedrejeb.calf.geo.LatLng
import com.mohamedrejeb.calf.permissions.helper.*
import kotlin.math.*
import kotlin.random.Random

fun main() {
 var checks = 0
 fun verify(label: String, condition: Boolean) { check(condition) { label }; checks++; println("PASS $label") }
 val read = Permission("ReadStorage")
 val gallery = Permission("Gallery")
 val storageString = "android.permission.READ_EXTERNAL_STORAGE"
 AndroidPermissionRegistry.register(read, AndroidPermissionMapping(storageString, maxSdkVersion=32))
 AndroidPermissionRegistry.register(gallery, AndroidPermissionMapping(storageString, maxSdkVersion=32))
 verify("name equality", Permission("ReadStorage") == read)
 verify("unknown permission collapses to empty mapping", Permission("Unregistered").toAndroidPermission().isEmpty())
 verify("SDK 32 Gallery mapping", gallery.toAndroidPermission() == storageString)
 val result = mapOf(storageString to true).mapKeys { getPermissionFromAndroidPermission(it.key) }.filter { it.key != null }.mapKeys { it.key!! }
 verify("batch result uses earlier global alias rather than requested Gallery", result == mapOf(read to true) && gallery !in result)
 android.os.Build.VERSION.SDK_INT = 33
 verify("SDK 33 legacy Gallery mapping intentionally empty", gallery.toAndroidPermission().isEmpty())
 var requested = 0
 var callback: Boolean? = null
 var state: PermissionStatus = PermissionStatus.Denied(true)
 val helper = object : PermissionHelper {
   override fun launchPermissionRequest(onPermissionResult: (Boolean)->Unit) = Unit
   override fun getPermissionStatus(onPermissionResult: (PermissionStatus)->Unit) = onPermissionResult(state)
 }
 helper.handleLaunchPermissionRequest({callback=it}, {requested++})
 verify("Denied(true) blocks native launch (WhenInUse background mapping)", requested == 0 && callback == false)
 state = PermissionStatus.Granted; callback = null
 helper.handleLaunchPermissionRequest({callback=it}, {requested++})
 verify("Granted bypasses native launch (APNs registration in fresh-grant branch)", requested == 0 && callback == true)
 state = PermissionStatus.Denied(false); callback = null
 helper.handleLaunchPermissionRequest({callback=it}, {requested++})
 verify("Denied(false) invokes native launch", requested == 1 && callback == null)
 val manager = platform.CoreLocation.CLLocationManager
 manager.state = platform.CoreLocation.kCLAuthorizationStatusAuthorizedWhenInUse
 val background = BackgroundLocationPermissionHelper()
 var actualBackgroundResult: Boolean? = null
 background.launchPermissionRequest { actualBackgroundResult = it }
 verify("actual Background helper cannot upgrade WhenInUse", manager.alwaysRequests == 0 && actualBackgroundResult == false)
 manager.state = platform.CoreLocation.kCLAuthorizationStatusNotDetermined
 val foreground = LocationPermissionHelper()
 val foregroundResults = mutableListOf<Boolean>()
 foreground.launchPermissionRequest { foregroundResults.add(it) }
 verify("actual foreground helper invokes requestWhenInUse", manager.foregroundRequests == 1)
 manager.lastCreated!!.deliver(platform.CoreLocation.kCLAuthorizationStatusNotDetermined)
 manager.lastCreated!!.deliver(platform.CoreLocation.kCLAuthorizationStatusAuthorizedWhenInUse)
 verify("actual delegate consumes callback on NotDetermined then drops grant", foregroundResults == listOf(false))
 val origin = LatLng(0.0,0.0)
 verify("equal coordinate distance zero", origin.distanceTo(origin) == 0.0)
 verify("quarter equator distance km", abs(origin.distanceTo(LatLng(0.0,90.0))-6371.0*PI/2) < 1e-8)
 verify("initial north bearing", origin.getAngleTo(LatLng(1.0,0.0), false) == 0.0)
 verify("initial east bearing", origin.getAngleTo(LatLng(0.0,1.0), false) == 90.0)
 verify("dateline short distance", abs(LatLng(0.0,179.0).distanceTo(LatLng(0.0,-179.0))-6371.0*PI/90) < 1e-8)
 val rng = Random(483)
 var example: Pair<LatLng, LatLng>? = null
 for (i in 0 until 5_000_000) {
   val a = LatLng(rng.nextDouble(-90.0,90.0),rng.nextDouble(-180.0,180.0))
   val b = LatLng(-a.latitude, if (a.longitude>=0) a.longitude-180.0 else a.longitude+180.0)
   if (a.distanceTo(b).isNaN()) { example = a to b; break }
 }
 println("Antipodal search result: $example")
 println("TOTAL deterministic checks=$checks")
}
'''

COMPOSE_ANNOTATION = r'''
package androidx.compose.runtime
annotation class Stable
'''

ANDROID_BUILD = r'''
package android.os
object Build { object VERSION { var SDK_INT = 32 } }
'''

CORE_LOCATION = r'''
package platform.CoreLocation
typealias CLAuthorizationStatus = Int
const val kCLAuthorizationStatusAuthorized = 3
const val kCLAuthorizationStatusAuthorizedAlways = 3
const val kCLAuthorizationStatusAuthorizedWhenInUse = 4
const val kCLAuthorizationStatusDenied = 2
const val kCLAuthorizationStatusNotDetermined = 0
interface CLLocationManagerDelegateProtocol {
 fun locationManager(manager: CLLocationManager, didChangeAuthorizationStatus: CLAuthorizationStatus)
}
class CLLocationManager {
 companion object {
  var state = kCLAuthorizationStatusNotDetermined
  var alwaysRequests = 0
  var foregroundRequests = 0
  var lastCreated: CLLocationManager? = null
  fun authorizationStatus() = state
 }
 init { lastCreated = this }
 var delegate: CLLocationManagerDelegateProtocol? = null
 fun requestAlwaysAuthorization() { alwaysRequests++ }
 fun requestWhenInUseAuthorization() { foregroundRequests++ }
 fun deliver(status: Int) { state = status; delegate?.locationManager(this, status) }
}
'''

NSOBJECT = r'''
package platform.darwin
open class NSObject
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--cache", type=Path, default=Path.home() / ".gradle/caches/modules-2/files-2.1")
    args = parser.parse_args()

    def original(path):
        data = subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=args.repo)
        print("BASELINE_SHA256", hashlib.sha256(data).hexdigest(), path, flush=True)
        return data.decode("utf-8")

    def jar(group, artifact, version):
        candidates = sorted((args.cache / group / artifact / version).glob("*/*.jar"))
        candidates = [p for p in candidates if not p.name.endswith(("-sources.jar", "-javadoc.jar", "-all.jar"))]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one cached {group}:{artifact}:{version} jar, found {len(candidates)}; no dependency will be downloaded")
        return str(candidates[0])

    deps = [
        ("org.jetbrains.kotlin", "kotlin-compiler-embeddable", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-stdlib", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-script-runtime", "2.4.20"),
        ("org.jetbrains.kotlin", "kotlin-reflect", "1.6.10"),
        ("org.jetbrains.kotlin", "kotlin-daemon-embeddable", "2.4.20"),
        ("org.jetbrains.kotlinx", "kotlinx-coroutines-core-jvm", "1.8.0"),
        ("org.jetbrains", "annotations", "13.0"),
    ]
    compiler_cp = ":".join(jar(*d) for d in deps)
    stdlib = jar("org.jetbrains.kotlin", "kotlin-stdlib", "2.4.20")
    print("Audit baseline:", BASELINE, flush=True)
    print("Compiler: Kotlin 2.4.20; platform: JVM with explicit Build/CoreLocation/Stable adapters", flush=True)
    print("Command model: java -Xmx512m K2JVMCompiler; java -Xmx128m MainKt", flush=True)
    with tempfile.TemporaryDirectory(prefix="nativecmp-permissions-geo-") as tmp:
        work = Path(tmp)
        for dest, source in SOURCES.items():
            (work / dest).write_text(original(source), encoding="utf-8")
        permission = original(COMMON + "PermissionState.kt")
        # Retain the complete original Permission class, without unrelated Compose facade.
        (work / "Permission.kt").write_text(
            "package com.mohamedrejeb.calf.permissions\n" + permission[permission.index("open class Permission("):],
            encoding="utf-8",
        )
        mapping = original(ANDROID + "PermissionsUtil.android.kt")
        # Original final three mapping helpers; only the Build adapter replaces Android.
        (work / "MappingUtil.kt").write_text(
            "package com.mohamedrejeb.calf.permissions\nimport android.os.Build\n"
            + mapping[mapping.index("internal fun Permission.toAndroidPermission()"):],
            encoding="utf-8",
        )
        for dest, content in {
            "Main.kt": MAIN,
            "ComposeAnnotation.kt": COMPOSE_ANNOTATION,
            "AndroidBuild.kt": ANDROID_BUILD,
            "CoreLocation.kt": CORE_LOCATION,
            "NSObject.kt": NSOBJECT,
        }.items():
            (work / dest).write_text(content, encoding="utf-8")
        result = subprocess.run([
            "java", "-Xmx512m", "-cp", compiler_cp,
            "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler", "-no-stdlib", "-no-reflect",
            "-classpath", stdlib, "-d", str(work / "out"),
            *[str(p) for p in sorted(work.glob("*.kt"))],
        ], capture_output=True, text=True)
        print("Compiler exit:", result.returncode, flush=True)
        print(result.stdout + result.stderr, end="", flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
        result = subprocess.run([
            "java", "-Xmx128m", "-cp", str(work / "out") + ":" + stdlib,
            "com.mohamedrejeb.calf.permissions.MainKt",
        ], capture_output=True, text=True)
        print("Execution exit:", result.returncode, flush=True)
        print(result.stdout + result.stderr, end="", flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
    print("VERIFIED: 16 deterministic checks; 5,000,000 seeded antipodal trials; no device/native API claim.", flush=True)


if __name__ == "__main__":
    main()
