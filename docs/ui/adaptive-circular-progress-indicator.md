<!-- Modified for nativeCmpkit migration (2026-10-24): independent coordinates / project references; inherited APIs retained. -->
# Circular Progress Indicator

> **nativeCmpkit migration:** this inherited API guide is being maintained in the independent repository. New coordinates are **unpublished**; see [installation](../installation.md) and the source audit. Platform behavior and historical version claims are not all verified.

`AdaptiveCircularProgressIndicator` is a circular progress indicator that adapts to the platform it is running on. It is a wrapper around `CircularProgressIndicator` on Android, and it implements similar look to `UIActivityIndicatorView` on iOS.

| Material (Android, Desktop, Web)                                                             | Cupertino (iOS)                                                                      |
|----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| ![Circular Progress Indicator Android](../images/AdaptiveCircularProgressIndicator-android.png) | ![Circular Progress Indicator iOS](../images/AdaptiveCircularProgressIndicator-ios.png) |

```kotlin
AdaptiveCircularProgressIndicator(
    modifier = Modifier.size(50.dp),
    color = Color.Red,
)
```