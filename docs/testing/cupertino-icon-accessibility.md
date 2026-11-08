# Cupertino icon accessibility (NAV-010 / #97)

The font-backed glyph is visual content. `CupertinoIcon` clears semantics only on its inner `Text`, preserving the caller’s outer modifier. With `contentDescription = null`, the icon is decorative; with a description, its outer node exposes that description and `Role.Image`. An enclosing button keeps its click action and button role. Use a null icon description when adjacent text already labels the button.

## Prepared desktop checks

`CupertinoIconSemanticsTest` has four Compose UI tests at font scales 0.85, 1.0 and 2.0. They query merged and unmerged trees for private-use glyph text; check decorative and labeled icons; verify exactly one icon description; and click text-plus-icon and icon-only buttons while checking their actions and roles. The icon’s caller-supplied test tag must remain available in the unmerged tree.

The scale loop repeats semantics assertions; the icon converts its fixed dp size to sp, so this does not establish enlarged-glyph layout or clipping. There are four JUnit methods, each with three internal scale passes. The glyph-text matcher covers both the private-use range and this catalogue’s additional U+F900–U+F921 glyphs.

Intended resource-admitted task (8 GiB available disk and 6 GiB MemAvailable, serial compiler execution). On a headless Linux host, prefix the Gradle command with `xvfb-run -a` when required:

```sh
./gradlew :calf-cupertino-icons:desktopTest --tests '*CupertinoIconSemanticsTest'
```

No test, compiler or platform accessibility execution has been performed for this patch. Desktop Compose trees do not establish TalkBack, VoiceOver or browser accessibility output.

## Native/manual acceptance still required

For Android TalkBack, iOS VoiceOver, desktop screen readers and browser accessibility inspection, exercise the same four controls at default and enlarged system font scales:

1. A standalone decorative icon: no private-use character or fallback glyph announcement.
2. A standalone labeled icon: one image label and no extra glyph text.
3. A text button containing a decorative icon: the text label and working button action remain.
4. An icon-only labeled button: one useful label, button action and button role remain.

Record the target/OS/browser, font scale, focus order, actual announcement, and activation result. Inspect both merged and unmerged Compose trees where tooling supports them, and inspect the browser accessibility tree separately. Existing icon catalog screens supply the font-backed icons; real screen-reader results have not been collected here. Issue #97 remains open until its original platform criteria are proven.
