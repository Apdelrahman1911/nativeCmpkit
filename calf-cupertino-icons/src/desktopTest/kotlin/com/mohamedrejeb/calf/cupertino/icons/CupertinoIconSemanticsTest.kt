package com.mohamedrejeb.calf.cupertino.icons

import androidx.compose.material3.IconButton
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assert
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.onAllNodesWithContentDescription
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.v2.runComposeUiTest
import kotlin.test.Test

@OptIn(ExperimentalTestApi::class)
class CupertinoIconSemanticsTest {
    @Test
    fun decorativeIconDoesNotExposePrivateUseText() = runComposeUiTest {
        setContent { CupertinoIcon(CupertinoIcons.house, contentDescription = null) }
        onAllNodes(hasText(Char(CupertinoIcons.house).toString())).assertCountEquals(0)
        onAllNodes(SemanticsMatcher.keyIsDefined(SemanticsProperties.ContentDescription)).assertCountEquals(0)
        onAllNodes(SemanticsMatcher.keyIsDefined(SemanticsProperties.Text)).assertCountEquals(0)
    }

    @Test
    fun labeledIconExposesExactlyOneDescriptionAndNoGlyphText() = runComposeUiTest {
        setContent { CupertinoIcon(CupertinoIcons.heartFill, contentDescription = "Favorite") }
        onAllNodesWithContentDescription("Favorite").assertCountEquals(1)
        onNodeWithContentDescription("Favorite")
            .assert(SemanticsMatcher.expectValue(SemanticsProperties.Role, Role.Image))
        onAllNodes(SemanticsMatcher.keyIsDefined(SemanticsProperties.Text)).assertCountEquals(0)
    }

    @Test
    fun decorativeIconDoesNotReplaceContainingButtonLabelOrAction() = runComposeUiTest {
        setContent {
            IconButton(onClick = {}, modifier = Modifier.semantics { contentDescription = "Open home" }) {
                CupertinoIcon(CupertinoIcons.house)
            }
        }
        onNodeWithContentDescription("Open home").assert(hasClickAction())
        onAllNodes(SemanticsMatcher.keyIsDefined(SemanticsProperties.Text)).assertCountEquals(0)
    }
}
