<!-- nativecmpkit-upstream-sync:674932206:530 -->
<!-- source-fingerprint:5fd7ad24f5834cf9227d4cc0335169a275ac575da6409de183a07c88da1cb6b6 -->
## Current upstream context: Calf #530

Original: [AdaptiveNavigationBar on iOS - bottom bar is visible when navigating away, and during back navigation gestures](https://github.com/MohamedRejeb/Calf/issues/530) — [raudonikis](https://github.com/raudonikis); created `2026-06-08T15:40:19Z`, updated `2026-09-30T14:29:04Z`; upstream state **open**.
Original IDs: `4614295234` / `I_kwDOKDql7s8AAAABEwiOwg`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant; tracked by the existing nativeCmpkit finding rather than a duplicate issue.

Native bars are subviews of the shared host UIViewController while navigation transitions can keep multiple Compose destinations alive. The report and maintainer comment4967506597 describe a genuine integration gap; replacing navigation architecture was suggested, not implemented or authorized by this audit.

**Next step:** Link UI transition/overlay finding; first reproduce Navigation3 outgoing/incoming-screen and cancelled-back-gesture cases, then evaluate scoped host/visibility fixes before a native-navigation redesign.

Primary tracking: #33. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.ios.kt:53-204`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.ios.kt#L53-L204) — `native bar overlay and disposal`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveScaffold.ios.kt:25-85`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveScaffold.ios.kt#L25-L85) — `native padding merged into Compose scaffold`

### Original issue description (verbatim Markdown)
````markdown
### Description

1. The `BottomNavigationBar` disappears only after a delay, when navigating to a screen without a bottom bar.
2. When navigating back from a screen without the bottom navigation bar, -> it becomes visible immediately, even if the gesture is not completed yet.

> Only on iOS. Issue is not present when using material scaffold and navigation bar.
>
> Usecase example: logout functionality from within a menu tab.

```kotlin
# Navigation
NavDisplay(
    backStack = backstack,
    entryProvider = entryProvider {
         entry<Route.Tabs> {
             TabsScreen(onButtonClick = { backstack.add(Route.Example) })
         }
         entry<Route.Example> {
              ExampleScreen()
          }
    }
)

# Screen with bottom navigation
@Composable
private fun TabsScreen() {
    AdaptiveScaffold(
        bottomBar = {
            AdaptiveNavigationBar(
                iosSelectedIndex = 0,
                iosItems = listOf(
                    UIKitUITabBarItem(title = "Tab 1"),
                    UIKitUITabBarItem(title = "Tab 2"),
                ),
                iosOnItemSelected = {},
            ) {
                NavigationBar { ... }
            }
        },
    ) {
        ...
    }
}

# Screen without navigation bar
@Composable
private fun ExampleScreen() {
    AdaptiveScaffold {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
            Text("Example Screen")
        }
    }
}
```

### Environment

> Compose Multiplatform project with Android/iOS targets.

```kotlin
# libs.versions.toml
agp = "9.0.1"
composeMultiplatform = "1.11.1"
kotlin = "2.4.0"
calf = "0.12.0"
compose-navigation3 = "1.1.1"
```

### Screen recording

https://github.com/user-attachments/assets/2db09b34-7061-43db-aec5-6e132ce980bb

### Reproducible sample project

https://github.com/raudonikis/Example-CMP-project
````

### Original public discussion (3 comments)

**[MohamedRejeb](https://github.com/MohamedRejeb)** — created `2026-07-14T09:30:37Z`, updated `2026-07-14T09:30:37Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/530#issuecomment-4967506597); IDs `4967506597` / `IC_kwDOKDql7s8AAAABKBYipQ`.
````markdown
Hello, thanks for reporting this issue
I'm still checking the best way to address this, for now I think you can hide the navigation bar when there's a transition.
The right fix for this would be supporting native iOS navigation which wraps each compose screen inside a UIViewController and that should fix this issue and bring native iOS transitions.
````

**[ayitinya](https://github.com/ayitinya)** — created `2026-09-30T03:57:40Z`, updated `2026-09-30T03:57:40Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/530#issuecomment-5903746122); IDs `5903746122` / `IC_kwDOKDql7s8AAAABX-QESg`.
````markdown
not confirmed but i believe i am having similar issues with the topbar instead.

the two topappbars of both screens are displayed (overlayed on each other) when navigating

````

**[raudonikis](https://github.com/raudonikis)** — created `2026-09-30T14:29:04Z`, updated `2026-09-30T14:29:04Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/530#issuecomment-5913339820); IDs `5913339820` / `IC_kwDOKDql7s8AAAABYHZnrA`.
````markdown
> not confirmed but i believe i am having similar issues with the topbar instead.
> 
> the two topappbars of both screens are displayed (overlayed on each other) when navigating
> 

Yeah I went with native navigation instead. Although this library is really great, this specific use case with top/bottom navigation is not usable.
````

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/source/issues/530/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/source/issues/530/comments.json)
- [Full public timeline: 6 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/source/issues/530/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261024T183300Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-06-22T10:28:08Z`: `referenced` by [MohamedRejeb](https://github.com/MohamedRejeb) ([event](https://api.github.com/repos/MohamedRejeb/Calf/issues/events/27035931645)); commit `17555cfb517cbc6680faea6e030be4c3fa9406ef`.
- `2026-07-26T19:48:00Z`: `referenced` by [MohamedRejeb](https://github.com/MohamedRejeb) ([event](https://api.github.com/repos/MohamedRejeb/Calf/issues/events/28506208273)); commit `1ca5e1db47472a1eee88b085b429020ceabef8ac`.
- `2026-10-24T16:16:23Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/530)); [[High][UI-021] Native bars live outside the Compose layout/transition hierarchy](https://github.com/Apdelrahman1911/nativeCmpkit/issues/33).
