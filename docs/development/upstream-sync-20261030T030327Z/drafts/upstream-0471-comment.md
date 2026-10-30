<!-- nativecmpkit-upstream-sync:674932206:471 -->
<!-- source-fingerprint:2df6f6e7b7d7db7d1c1e8f2dd789ec3f0be9083555ae785ed35f4fd7978f140a -->
## Current upstream context: Calf #471

Original: [Feature request: iOS-native styling customization for AdaptiveNavigationBar and AdaptiveTopBar](https://github.com/MohamedRejeb/Calf/issues/471) — [antoniokranjcina](https://github.com/antoniokranjcina); created `2026-03-24T09:43:20Z`, updated `2026-04-03T16:58:23Z`; upstream state **open**.
Original IDs: `4126530434` / `I_kwDOKDql7s719duC`. Original labels: `enhancement` (#a2eeef; New feature or request), `ui` (#1d76db; no description), `ios` (#41022a; no description).

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant improvement/remaining scope; partial existing support is identified below.

PR499 implements selected tint, pre-iOS26 unselected tint and title color only. Maintainer comment4184266309 leaves iOS26 unselected tint and title font/typography unchecked. Baseline configuration has no title typography field and explicitly documents the Liquid Glass unselected-color limitation.

**Next step:** Preserve only the remaining styling requirements; design optional typography/font-resource mapping and iOS26 appearance support without changing unspecified native defaults.

Primary tracking: #167. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitNavigationBarConfiguration.kt:6-22`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitNavigationBarConfiguration.kt#L6-L22) — `UIKitNavigationBarConfiguration`
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitTabBarConfiguration.kt:6-24`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitTabBarConfiguration.kt#L6-L24) — `UIKitTabBarConfiguration`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/TabBarManager.kt:64-87`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/TabBarManager.kt#L64-L87) — `updateConfiguration`

### Original issue description (verbatim Markdown)
````markdown
## Feature Request
After testing the library, I noticed there's currently no way to customize the iOS-native appearance for some adaptive components. 

### AdaptiveNavigationBar (UITabBar)
  - Tint color for **selected** items (icon + label)
  - Tint color for **unselected** items (icon + label)

  ### AdaptiveTopBar (UINavigationBar)
  - Title text color
  - Title font / typography
                                                            
  ### Why
  On iOS, these map directly to `UITabBarAppearance` and `UINavigationBarAppearance`. Without exposing them, apps that use a custom color scheme can't match their branding on iOS while using these adaptive components.
````

### Original public discussion (2 comments)

**[MohamedRejeb](https://github.com/MohamedRejeb)** — created `2026-03-24T10:33:47Z`, updated `2026-03-24T10:33:47Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/471#issuecomment-4117102683); IDs `4117102683` / `IC_kwDOKDql7s71ZgBb`.
````markdown
Hello,

Thanks for the detailed description. That's an important feature to add. You can open PR with these changes and make sure to only apply those properties when the user selects them so title text color for example should be unspecified by default which means that we will keep the default iOS color.

I'm not sure how we can pass the typography from common to iOS, also maybe the user wants to use an existing font in common resources that would be challenging.
````

**[MohamedRejeb](https://github.com/MohamedRejeb)** — created `2026-04-03T16:58:22Z`, updated `2026-04-03T16:58:22Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/471#issuecomment-4184266309); IDs `4184266309` / `IC_kwDOKDql7s75ZtZF`.
````markdown
### AdaptiveNavigationBar (UITabBar)
- [x] Tint color for **selected** items (icon + label)
- [x] Tint color for **unselected** items (icon + label) for iOS < 26
- [ ] Tint color for **unselected** items (icon + label) for iOS >= 26 (Liquid glass)

### AdaptiveTopBar (UINavigationBar)
  - [x] Title text color
  - [ ] Title font / typography

#499 
````

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/source/issues/471/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/source/issues/471/comments.json)
- [Full public timeline: 6 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/source/issues/471/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261030T030327Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-03-24T12:33:47Z`: `labeled` by [MohamedRejeb](https://github.com/MohamedRejeb) ([event](https://api.github.com/repos/MohamedRejeb/Calf/issues/events/23850577695)); label `enhancement`.
- `2026-03-24T12:33:47Z`: `labeled` by [MohamedRejeb](https://github.com/MohamedRejeb) ([event](https://api.github.com/repos/MohamedRejeb/Calf/issues/events/23850577712)); label `ui`.
- `2026-03-31T08:07:07Z`: `labeled` by [MohamedRejeb](https://github.com/MohamedRejeb) ([event](https://api.github.com/repos/MohamedRejeb/Calf/issues/events/24065148482)); label `ios`.
- `2026-10-24T16:25:07Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/471)); [[Low][Upstream #471] Feature request: iOS-native styling customization for AdaptiveNavigationBar and AdaptiveTopBar](https://github.com/Apdelrahman1911/nativeCmpkit/issues/167).
