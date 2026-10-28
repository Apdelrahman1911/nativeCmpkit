// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.navigation

import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.LocalSaveableStateRegistry
import androidx.compose.runtime.saveable.SaveableStateRegistry
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.v2.runComposeUiTest
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.ObjectInputStream
import java.io.ObjectOutputStream
import java.io.Serializable
import kotlin.test.Test
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals
import kotlin.test.assertNotSame
import kotlin.test.assertTrue

private const val HOME = "home"
private const val DETAIL = "detail"

@OptIn(ExperimentalTestApi::class)
class AdaptiveNavHostStateTest {


    @Test
    fun `saveable state of a destination survives navigating away and back`() = runComposeUiTest {
        lateinit var navController: AdaptiveNavHostController
        setContent {
            navController = rememberNavController()
            AdaptiveNavHost(navController = navController, startDestination = HOME) {
                composable(HOME) { Counter(label = HOME) }
                composable(DETAIL) { Text(DETAIL) }
            }
        }
        waitForIdle()

        onNodeWithText("$HOME 0").performClick()
        onNodeWithText("$HOME 1").assertIsDisplayed()

        navController.navigate(DETAIL)
        waitForIdle()
        onNodeWithText(DETAIL).assertIsDisplayed()

        navController.popBackStack()
        waitForIdle()

        onNodeWithText("$HOME 1").assertIsDisplayed()
    }

    @Test
    fun `saveable state of a popped destination is dropped`() = runComposeUiTest {
        lateinit var navController: AdaptiveNavHostController
        setContent {
            navController = rememberNavController()
            AdaptiveNavHost(navController = navController, startDestination = HOME) {
                composable(HOME) { Text(HOME) }
                composable(DETAIL) { Counter(label = DETAIL) }
            }
        }
        waitForIdle()

        navController.navigate(DETAIL)
        waitForIdle()
        onNodeWithText("$DETAIL 0").performClick()
        onNodeWithText("$DETAIL 1").assertIsDisplayed()

        navController.popBackStack()
        waitForIdle()
        navController.navigate(DETAIL)
        waitForIdle()

        onNodeWithText("$DETAIL 0").assertIsDisplayed()
    }

    @Test
    fun `duplicate visits separated by another route keep independent saveable state`() = runComposeUiTest {
        val controller = AdaptiveNavHostController()
        setContent {
            AdaptiveNavHost(controller, HOME) {
                composable(HOME) { Counter(HOME) }
                composable(DETAIL) { Text(DETAIL) }
            }
        }
        onNodeWithText("$HOME 0").performClick()
        runOnIdle { controller.navigate(DETAIL); controller.navigate(HOME) }
        onNodeWithText("$HOME 0").performClick()
        onNodeWithText("$HOME 1").performClick()
        onNodeWithText("$HOME 2").assertIsDisplayed()
        runOnIdle { controller.popBackStack(); controller.popBackStack() }
        onNodeWithText("$HOME 1").assertIsDisplayed()
    }

    @Test
    fun `consecutive duplicate visits reset plain remember and saveable state`() = runComposeUiTest {
        val controller = AdaptiveNavHostController()
        setContent {
            AdaptiveNavHost(controller, HOME) {
                composable(HOME) {
                    var local by remember { mutableStateOf(0) }
                    var saved by rememberSaveable { mutableStateOf(0) }
                    Button(onClick = { local++; saved++ }) { Text("local $local saved $saved") }
                }
            }
        }
        onNodeWithText("local 0 saved 0").performClick()
        runOnIdle { controller.navigate(HOME) }
        onNodeWithText("local 0 saved 0").assertIsDisplayed()
        runOnIdle { controller.popBackStack() }
        // Ordinary remember is not retained offscreen, while rememberSaveable is.
        onNodeWithText("local 0 saved 1").assertIsDisplayed()
    }

    @Test
    fun `pop and repush before an idle frame discards the popped visit state`() = runComposeUiTest {
        val controller = AdaptiveNavHostController()
        setContent {
            AdaptiveNavHost(controller, HOME) {
                composable(HOME) { Text(HOME) }
                composable(DETAIL) { Counter(DETAIL) }
            }
        }
        runOnIdle { controller.navigate(DETAIL) }
        onNodeWithText("$DETAIL 0").performClick()
        runOnIdle { controller.popBackStack(); controller.navigate(DETAIL) }
        onNodeWithText("$DETAIL 0").assertIsDisplayed()
    }

    @Test
    fun `entry payloads and defaults reach legacy content callbacks`() = runComposeUiTest {
        val controller = AdaptiveNavHostController()
        setContent {
            AdaptiveNavHost(controller, HOME) {
                composable(HOME) { Text(HOME) }
                composable(DETAIL, mapOf(
                    "id" to NavArgument.Builder().setType(AdaptiveNavType.IntType).build(),
                    "label" to NavArgument.Builder().setDefaultValue("item").build(),
                )) { values -> Text("${values.getValue("label").defaultValue} ${values.getValue("id").defaultValue}") }
            }
        }
        runOnIdle { controller.navigate(DETAIL, mapOf("id" to NavArgument.Builder().setDefaultValue(1).build())) }
        onNodeWithText("item 1").assertIsDisplayed()
        runOnIdle { controller.navigateWithValues(DETAIL, mapOf("id" to 2)) }
        onNodeWithText("item 2").assertIsDisplayed()
        runOnIdle { controller.popBackStack() }
        onNodeWithText("item 1").assertIsDisplayed()
    }

    @Test
    fun `replacement controller is initialized and receives updated graph callbacks`() = runComposeUiTest {
        val original = AdaptiveNavHostController()
        var selected by mutableStateOf(original)
        var suffix by mutableStateOf("old")
        setContent {
            val controller = selected
            val label = suffix
            AdaptiveNavHost(controller, HOME) {
                composable(HOME) {
                    Button(onClick = { controller.navigate(DETAIL) }) { Text("open $label") }
                }
                composable(DETAIL) { Text("detail $label") }
            }
        }
        onNodeWithText("open old").assertIsDisplayed()
        val replacement = AdaptiveNavHostController()
        runOnIdle { selected = replacement; suffix = "new" }
        onNodeWithText("open new").performClick()
        onNodeWithText("detail new").assertIsDisplayed()
        runOnIdle {
            assertEquals(HOME, original.currentDestination)
            assertEquals(DETAIL, replacement.currentDestination)
        }
    }

    @Test
    fun `updated closures do not lose entry state or reset a nonempty stack`() = runComposeUiTest {
        val controller = AdaptiveNavHostController()
        var label by mutableStateOf("old")
        var start by mutableStateOf(HOME)
        setContent {
            val currentLabel = label
            AdaptiveNavHost(controller, start) {
                composable(HOME) { Counter(currentLabel) }
                composable(DETAIL) { Text(DETAIL) }
            }
        }
        onNodeWithText("old 0").performClick()
        runOnIdle { label = "new"; start = DETAIL }
        onNodeWithText("new 1").assertIsDisplayed()
        runOnIdle { assertEquals(HOME, controller.currentDestination) }
    }

    @Test
    @Suppress("DEPRECATION")
    fun `changing start route initializes an explicitly emptied stack at the same host`() = runComposeUiTest {
        val controller = AdaptiveNavHostController()
        var start by mutableStateOf(HOME)
        setContent {
            AdaptiveNavHost(controller, start) {
                composable(HOME) { Counter(HOME) }
                composable(DETAIL) { Text(DETAIL) }
            }
        }
        onNodeWithText("$HOME 0").performClick()
        val oldId = runOnIdle { controller.currentBackStackEntry!!.id }
        runOnIdle {
            // popBackStack intentionally retains the root. The compatible legacy
            // mirror is the public way to empty this same, still-attached owner.
            controller.backStack.clear()
            assertTrue(controller.backStackEntries.isEmpty())
            assertEquals(null, controller.currentDestination)
            start = DETAIL
        }
        onNodeWithText(DETAIL).assertIsDisplayed()
        onNodeWithText("$HOME 1").assertDoesNotExist()
        runOnIdle {
            assertEquals(listOf(DETAIL), controller.backStackEntries.map { it.route })
            assertNotEquals(oldId, controller.currentBackStackEntry!!.id)
        }
        // A later start change does not reset the newly initialized nonempty
        // stack. This pairs the empty and nonempty policies in one real host.
        runOnIdle { start = HOME }
        onNodeWithText(DETAIL).assertIsDisplayed()
        runOnIdle { assertEquals(DETAIL, controller.currentDestination) }
    }

    @Test
    fun `replacement controller cannot reuse the old controller saved state keys`() = runComposeUiTest {
        var controller by mutableStateOf(AdaptiveNavHostController())
        setContent { AdaptiveNavHost(controller, HOME) { composable(HOME) { Counter(HOME) } } }
        onNodeWithText("$HOME 0").performClick()
        val oldId = controller.currentBackStackEntry!!.id
        runOnIdle { controller = AdaptiveNavHostController() }
        onNodeWithText("$HOME 0").assertIsDisplayed()
        runOnIdle { assertNotEquals(oldId, controller.currentBackStackEntry!!.id) }
    }

    @Test
    @Suppress("DEPRECATION")
    fun `observed legacy suffix replacement drops obsolete entry state`() = runComposeUiTest {
        val controller = AdaptiveNavHostController()
        setContent {
            AdaptiveNavHost(controller, HOME) {
                composable(HOME) { Text(HOME) }
                composable(DETAIL) { Counter(DETAIL) }
            }
        }
        runOnIdle { controller.backStack.add(DETAIL) }
        onNodeWithText("$DETAIL 0").performClick()
        runOnIdle { controller.backStack.removeAt(1) }
        onNodeWithText(HOME).assertIsDisplayed()
        runOnIdle { controller.backStack.add(DETAIL) }
        onNodeWithText("$DETAIL 0").assertIsDisplayed()
    }

    @Test
    fun `save restore preserves duplicate entry state identity and payloads`() = runComposeUiTest {
        // Compose 1.12's Skiko StateRestorationTester.platformEncodeDecode is TODO.
        // Use the actual registry and a real byte codec, not a retained object graph.
        val originalRegistry = SaveableStateRegistry(null) { it is Serializable }
        var registry by mutableStateOf(originalRegistry)
        var hostVisible by mutableStateOf(true)
        var activeHosts = 0
        lateinit var controller: AdaptiveNavHostController
        setContent {
            if (hostVisible) {
                CompositionLocalProvider(LocalSaveableStateRegistry provides registry) {
                    controller = rememberAdaptiveNavController()
                    DisposableEffect(Unit) {
                        activeHosts++
                        onDispose { activeHosts-- }
                    }
                    AdaptiveNavHost(controller, HOME) {
                        composable(HOME) { arguments ->
                            RegistrySavedCounter("home ${arguments["id"]?.defaultValue ?: 0}")
                        }
                    }
                }
            }
        }
        onNodeWithText("home 0 0").performClick()
        val payload = mapOf("id" to 1, "note" to "second / ✓", "optional" to null)
        runOnIdle { controller.navigateWithValues(HOME, payload) }
        onNodeWithText("home 1 0").performClick()
        onNodeWithText("home 1 1").performClick()
        onNodeWithText("home 1 2").assertIsDisplayed()
        val originalController = runOnIdle { controller }
        val ids = runOnIdle { controller.backStackEntries.map { it.id } }
        assertEquals(2, ids.toSet().size)
        val savedValues = runOnIdle { registry.performSave() }
        assertTrue(savedValues.isNotEmpty())
        val restoredValues = javaSerializationRoundTrip(savedValues)
        assertNotSame(savedValues, restoredValues)
        assertEquals(savedValues, restoredValues)

        // A later live mutation must not alter the serialized snapshot.
        onNodeWithText("home 1 2").performClick()
        onNodeWithText("home 1 3").assertIsDisplayed()
        runOnIdle { hostVisible = false }
        waitForIdle()
        onNodeWithText("home 1 3").assertDoesNotExist()
        runOnIdle {
            assertEquals(0, activeHosts)
            assertTrue(originalRegistry.performSave().isEmpty())
        }

        val restoredRegistry = SaveableStateRegistry(restoredValues) { it is Serializable }
        assertNotSame(originalRegistry, restoredRegistry)
        runOnIdle {
            registry = restoredRegistry
            hostVisible = true
        }
        waitForIdle()
        onNodeWithText("home 1 2").assertIsDisplayed()
        runOnIdle {
            assertEquals(1, activeHosts)
            assertNotSame(originalController, controller)
            assertEquals(listOf(HOME, HOME), controller.backStackEntries.map { it.route })
            assertEquals(ids, controller.backStackEntries.map { it.id })
            assertEquals(listOf(emptyMap(), payload), controller.backStackEntries.map { it.arguments })
            assertTrue(controller.popBackStack())
        }
        onNodeWithText("home 0 1").assertIsDisplayed()
        runOnIdle {
            assertEquals(listOf(ids.first()), controller.backStackEntries.map { it.id })
            assertEquals(emptyMap(), controller.currentBackStackEntry!!.arguments)
        }
    }

    @Test
    fun `duplicate public host registration reports the exact route rather than choosing first content`() {
        val controller = AdaptiveNavHostController()
        val error = assertFailsWith<IllegalArgumentException> {
            runComposeUiTest {
                setContent {
                    AdaptiveNavHost(controller, HOME) {
                        composable(HOME) { Text("first definition") }
                        composable(HOME) { Text("second definition") }
                    }
                }
                waitForIdle()
            }
        }
        assertEquals("Duplicate navigation route 'home'", error.message)
        assertTrue(controller.backStackEntries.isEmpty())
    }

    @Test
    fun `unknown public start route fails explicitly before initializing or displaying a blank host`() {
        val controller = AdaptiveNavHostController()
        val error = assertFailsWith<IllegalArgumentException> {
            runComposeUiTest {
                setContent { AdaptiveNavHost(controller, "typo") { composable(HOME) { Text(HOME) } } }
                waitForIdle()
            }
        }
        assertEquals("Unknown start destination 'typo'", error.message)
        assertTrue(controller.backStackEntries.isEmpty())
    }

    @Test
    fun `public saver restored removed route is explicitly rejected by the new graph`() {
        val original = AdaptiveNavHostController().apply { navigate(HOME); navigate("removed") }
        val restored = restoredControllerBytes(original)
        val ids = restored.backStackEntries.map { it.id }
        assertNotSame(original, restored)
        val error = assertFailsWith<IllegalArgumentException> {
            runComposeUiTest {
                setContent { AdaptiveNavHost(restored, HOME) { composable(HOME) { Text(HOME) } } }
                waitForIdle()
            }
        }
        assertEquals("Unknown navigation route 'removed'", error.message)
        assertEquals(ids, restored.backStackEntries.map { it.id }, "Fail-fast does not silently delete saved entries")
    }

    @Test
    fun `documented explicit app upgrade fallback renders home with fresh state and rejects later unknown navigation`() = runComposeUiTest {
        val original = AdaptiveNavHostController().apply { navigate(HOME); navigate("removed") }
        val restored = restoredControllerBytes(original)
        val savedIds = restored.backStackEntries.map { it.id }.toSet()
        val knownRoutes = setOf(HOME, DETAIL)
        lateinit var selected: AdaptiveNavHostController
        setContent {
            // Deliberate application policy BEFORE mounting; the library does not auto-drop entries.
            // Keep unsaved business data outside navigation or migrate it before choosing this reset.
            selected = remember(restored, knownRoutes) {
                if (restored.backStackEntries.any { it.route !in knownRoutes }) AdaptiveNavHostController() else restored
            }
            AdaptiveNavHost(selected, HOME) {
                composable(HOME) { Counter(HOME) }
                composable(DETAIL) { Text(DETAIL) }
            }
        }
        onNodeWithText("$HOME 0").assertIsDisplayed()
        runOnIdle {
            assertNotSame(restored, selected)
            assertEquals(listOf(HOME), selected.backStackEntries.map { it.route })
            assertTrue(selected.backStackEntries.none { it.id in savedIds })
            val before = selected.backStackEntries
            val error = assertFailsWith<IllegalArgumentException> { selected.navigate("typo") }
            assertEquals("Unknown navigation route 'typo'", error.message)
            assertEquals(before, selected.backStackEntries, "Unknown route must not mutate the valid stack")
            assertEquals(listOf(HOME, "removed"), restored.backStackEntries.map { it.route })
        }
        onNodeWithText("$HOME 0").assertIsDisplayed()
        onNodeWithText("$HOME 0").performClick()
        onNodeWithText("$HOME 1").assertIsDisplayed()
        runOnIdle { selected.navigate(DETAIL) }
        onNodeWithText(DETAIL).assertIsDisplayed()
        runOnIdle { selected.popBackStack() }
        onNodeWithText("$HOME 1").assertIsDisplayed()
    }

}

@androidx.compose.runtime.Composable
private fun Counter(label: String) {
    var count by rememberSaveable { mutableStateOf(0) }
    Button(onClick = { count++ }) {
        Text("$label $count")
    }
}

@androidx.compose.runtime.Composable
private fun RegistrySavedCounter(label: String) {
    // Desktop MutableState is not Java Serializable. A normal Compose Saver
    // persists its scalar value; the navigation/holder save maps are unmodified.
    var count by rememberSaveable(
        saver = Saver<MutableState<Int>, Int>(
            save = { it.value },
            restore = { mutableStateOf(it) },
        ),
    ) { mutableStateOf(0) }
    Button(onClick = { count++ }) { Text("$label $count") }
}

@Suppress("UNCHECKED_CAST")
private fun javaSerializationRoundTrip(saved: Map<String, List<Any?>>): Map<String, List<Any?>> {
    val bytes = ByteArrayOutputStream().use { output ->
        ObjectOutputStream(output).use { it.writeObject(saved) }
        output.toByteArray()
    }
    assertTrue(bytes.isNotEmpty())
    // Only bytes produced immediately above from this test's registry are read.
    // No external stream, file or untrusted Java-serialized input is accepted.
    return ObjectInputStream(ByteArrayInputStream(bytes)).use {
        it.readObject() as Map<String, List<Any?>>
    }
}

@Suppress("UNCHECKED_CAST")
private fun restoredControllerBytes(original: AdaptiveNavHostController): AdaptiveNavHostController {
    val saver = AdaptiveNavHostController.Saver() as Saver<AdaptiveNavHostController, Any>
    val scope = object : androidx.compose.runtime.saveable.SaverScope { override fun canBeSaved(value: Any) = true }
    val saved = assertNotNull(with(saver) { scope.save(original) })
    val bytes = javaSerializationRoundTrip(mapOf("controller" to listOf(saved)))
    return assertNotNull(saver.restore(assertNotNull(bytes.getValue("controller").single())))
}
