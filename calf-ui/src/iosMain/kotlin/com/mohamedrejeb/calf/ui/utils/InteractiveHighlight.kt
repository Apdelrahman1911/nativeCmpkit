// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.utils

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.VectorConverter
import androidx.compose.animation.core.VisibilityThreshold
import androidx.compose.animation.core.spring
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ShaderBrush
import androidx.compose.ui.graphics.asComposeShader
import androidx.compose.ui.input.pointer.pointerInput
import com.kyant.backdrop.RuntimeShader
import com.kyant.backdrop.asSkikoRuntimeShader
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import org.jetbrains.skia.RuntimeEffect

/** SkSL compilation capability, not a guarantee about hardware performance or backdrop effects. */
fun isRuntimeShaderSupported(): Boolean = runtimeShaderSupport

private val runtimeShaderSupport: Boolean by lazy {
    try {
        val effect = RuntimeEffect.makeForShader("half4 main(float2 position) { return half4(1.0); }")
        effect.close()
        true
    } catch (_: Exception) {
        false
    }
}

class InteractiveHighlight(
    val animationScope: CoroutineScope,
    val position: (size: Size, offset: Offset) -> Offset = { _, offset -> offset }
) {
    private val pressSpec = spring(.5f, 300f, .001f)
    private val positionSpec = spring(.5f, 300f, Offset.VisibilityThreshold)
    private val pressAnimation = Animatable(0f, .001f)
    private val positionAnimation = Animatable(Offset.Zero, Offset.VectorConverter, Offset.VisibilityThreshold)
    private var startPosition = Offset.Zero
    private var pointerPosition by mutableStateOf(Offset.Zero)
    private var pressed by mutableStateOf(false)
    private var feedbackJob: Job? = null
    private var shader: RuntimeShader? = null
    private var attemptedShader = false
    private var disposed = false
    internal val hasAttemptedShader: Boolean get() = attemptedShader

    val pressProgress: Float get() = pressAnimation.value.coerceIn(0f, 1f)
    val offset: Offset get() = currentPosition - startPosition
    private val currentPosition: Offset get() = if (pressed) pointerPosition else positionAnimation.value

    // The button uses only gestureModifier/animation state. No shader is constructed for that path.
    private fun drawingShader(): RuntimeShader? {
        if (disposed) return null
        if (!attemptedShader) {
            attemptedShader = true
            shader = try {
                RuntimeShader(
                    """
                    layout(color) uniform half4 color;
                    uniform float radius;
                    uniform float2 position;
                    half4 main(float2 coord) {
                        float dist = distance(coord, position);
                        float intensity = smoothstep(radius, radius * 0.5, dist);
                        return color * intensity;
                    }
                    """.trimIndent()
                )
            } catch (_: Exception) {
                null
            }
        }
        return shader
    }

    val modifier: Modifier = Modifier.drawWithContent {
        val progress = pressProgress
        if (progress > 0f && size.width > 0f && size.height > 0f) {
            val effect = drawingShader()
            if (effect != null) {
                drawRect(Color.White.copy(alpha = .08f * progress), blendMode = BlendMode.Plus)
                val requested = position(size, currentPosition)
                val x = if (requested.x.isFinite()) requested.x.coerceIn(0f, size.width) else size.width / 2f
                val y = if (requested.y.isFinite()) requested.y.coerceIn(0f, size.height) else size.height / 2f
                effect.setColorUniform("color", Color.White.copy(alpha = .15f * progress))
                effect.setFloatUniform("radius", size.minDimension * 1.5f)
                effect.setFloatUniform("position", x, y)
                val nativeShader = effect.asSkikoRuntimeShader().makeShader()
                try {
                    drawRect(ShaderBrush(nativeShader.asComposeShader()), blendMode = BlendMode.Plus)
                } finally {
                    nativeShader.close()
                }
            } else {
                drawRect(Color.White.copy(alpha = .25f * progress), blendMode = BlendMode.Plus)
            }
        }
        drawContent()
    }

    val gestureModifier: Modifier = Modifier.pointerInput(this) {
        try {
            inspectDragGestures(
                onDragStart = { down ->
                    startPosition = down.position
                    pointerPosition = down.position
                    pressed = true
                    feedbackJob?.cancel()
                    feedbackJob = animationScope.launch {
                        launch { pressAnimation.animateTo(1f, pressSpec) }
                        launch { positionAnimation.snapTo(startPosition) }
                    }
                },
                onDragEnd = { cancelGesture() },
                onDragCancel = { cancelGesture() },
                onDrag = { change, _ -> pointerPosition = change.position },
            )
        } finally {
            cancelGesture()
        }
    }

    internal fun cancelGesture() {
        if (!pressed) return
        val last = pointerPosition
        pressed = false
        feedbackJob?.cancel()
        feedbackJob = animationScope.launch(start = CoroutineStart.UNDISPATCHED) {
            positionAnimation.snapTo(last)
            launch { pressAnimation.animateTo(0f, pressSpec) }
            launch { positionAnimation.animateTo(startPosition, positionSpec) }
        }
    }

    /** Releases this helper's optional native shader and jobs without cancelling the caller's scope. */
    fun dispose() {
        disposed = true
        feedbackJob?.cancel()
        pressed = false
        shader?.asSkikoRuntimeShader()?.close()
        shader = null
    }
}
