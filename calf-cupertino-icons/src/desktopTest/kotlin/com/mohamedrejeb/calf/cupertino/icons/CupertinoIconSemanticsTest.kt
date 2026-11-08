package com.mohamedrejeb.calf.cupertino.icons

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.ComposeUiTest
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assert
import androidx.compose.ui.test.assertContentDescriptionEquals
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertHasClickAction
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.Density
import kotlin.test.Test
import kotlin.test.assertEquals

/** Desktop Compose semantics only; platform screen-reader behavior requires native exercise. */
@OptIn(ExperimentalTestApi::class)
class CupertinoIconSemanticsTest {
    @Test
    fun decorativeIconHasNoGlyphTextOrImageLabelAtDifferentFontScales() = atFontScales(
        content = { CupertinoIcon(CupertinoIcons.heartFill, Modifier.testTag("icon")) },
    ) {
        onNodeWithTag("icon", useUnmergedTree = true)
            .assert(SemanticsMatcher.keyNotDefined(SemanticsProperties.Text))
            .assert(SemanticsMatcher.keyNotDefined(SemanticsProperties.ContentDescription))
            .assert(SemanticsMatcher.keyNotDefined(SemanticsProperties.Role))
        assertNoPrivateUseText()
    }

    @Test
    fun labeledIconHasOneImageDescriptionAndNoGlyphTextAtDifferentFontScales() = atFontScales(
        content = {
            CupertinoIcon(
                CupertinoIcons.heartFill,
                Modifier.testTag("icon"),
                contentDescription = "Favorite",
            )
        },
    ) {
        onNodeWithTag("icon", useUnmergedTree = true)
            .assertContentDescriptionEquals("Favorite")
            .assert(SemanticsMatcher.expectValue(SemanticsProperties.Role, Role.Image))
        for (unmerged in listOf(false, true)) {
            onAllNodes(hasContentDescription("Favorite"), useUnmergedTree = unmerged)
                .assertCountEquals(1)
        }
        assertNoPrivateUseText()
    }

    @Test
    fun decorativeButtonIconKeepsCallerAndButtonSemantics() {
        var clicks = 0
        atFontScales(
            content = {
                Button(onClick = { clicks++ }, modifier = Modifier.testTag("button")) {
                    CupertinoIcon(CupertinoIcons.heartFill, Modifier.testTag("icon"))
                    Text("Favorite")
                }
            },
        ) {
            onNodeWithTag("button", useUnmergedTree = true).assertHasClickAction()
            onNodeWithTag("button")
                .assertHasClickAction()
                .assertTextEquals("Favorite")
                .assert(SemanticsMatcher.expectValue(SemanticsProperties.Role, Role.Button))
                .performClick()
            onNodeWithText("Favorite", useUnmergedTree = true).assertExists()
            onNodeWithTag("icon", useUnmergedTree = true)
                .assert(SemanticsMatcher.keyNotDefined(SemanticsProperties.ContentDescription))
            assertNoPrivateUseText()
        }
        assertEquals(FONT_SCALES.size, clicks)
    }

    @Test
    fun labeledButtonIconKeepsOneLabelAndTheButtonAction() {
        var clicks = 0
        atFontScales(
            content = {
                Button(onClick = { clicks++ }, modifier = Modifier.testTag("button")) {
                    CupertinoIcon(
                        CupertinoIcons.heartFill,
                        Modifier.testTag("icon"),
                        contentDescription = "Favorite",
                    )
                }
            },
        ) {
            onNodeWithTag("button", useUnmergedTree = true).assertHasClickAction()
            onNodeWithTag("button")
                .assertHasClickAction()
                .assertContentDescriptionEquals("Favorite")
                .assert(SemanticsMatcher.expectValue(SemanticsProperties.Role, Role.Button))
                .performClick()
            onNodeWithTag("icon", useUnmergedTree = true)
                .assertContentDescriptionEquals("Favorite")
                .assert(SemanticsMatcher.expectValue(SemanticsProperties.Role, Role.Image))
            for (unmerged in listOf(false, true)) {
                onAllNodes(hasContentDescription("Favorite"), useUnmergedTree = unmerged)
                    .assertCountEquals(1)
            }
            assertNoPrivateUseText()
        }
        assertEquals(FONT_SCALES.size, clicks)
    }
}

@OptIn(ExperimentalTestApi::class)
private fun atFontScales(content: @Composable () -> Unit, check: ComposeUiTest.() -> Unit) = runComposeUiTest {
    var scale by mutableStateOf(FONT_SCALES.first())
    setContent {
        val density = LocalDensity.current
        CompositionLocalProvider(LocalDensity provides Density(density.density, scale)) {
            Column { content() }
        }
    }
    for (fontScale in FONT_SCALES) {
        runOnIdle { scale = fontScale }
        waitForIdle()
        check()
    }
}

@OptIn(ExperimentalTestApi::class)
private fun ComposeUiTest.assertNoPrivateUseText() {
    val privateUseText = SemanticsMatcher("private-use font glyph text") { node ->
        node.config.contains(SemanticsProperties.Text) &&
            node.config[SemanticsProperties.Text].any { text ->
                text.text.any { it in '\uE000'..'\uF8FF' || it in '\uF900'..'\uF921' }
            }
    }
    for (unmerged in listOf(false, true)) {
        onAllNodes(privateUseText, useUnmergedTree = unmerged).assertCountEquals(0)
    }
}

private val FONT_SCALES = listOf(0.85f, 1f, 2f)
