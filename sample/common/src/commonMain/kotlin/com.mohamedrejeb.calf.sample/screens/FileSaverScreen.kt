// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.sample.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.input.TextFieldState
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Image
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.SaveAlt
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Canvas
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Paint
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import com.mohamedrejeb.calf.core.ExperimentalCalfApi
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.readByteArray
import com.mohamedrejeb.calf.picker.FilePickerFileType
import com.mohamedrejeb.calf.picker.FilePickerSelectionMode
import com.mohamedrejeb.calf.picker.FilePickerSettings
import com.mohamedrejeb.calf.picker.ImageRepresentationMode
import com.mohamedrejeb.calf.picker.rememberFilePickerLauncher
import com.mohamedrejeb.calf.picker.rememberFileSaverLauncher
import com.mohamedrejeb.calf.sample.components.SampleScreenScaffold
import com.mohamedrejeb.calf.sample.utils.toByteArray
import com.mohamedrejeb.calf.sample.utils.MAX_SAMPLE_IMAGE_BYTES
import com.mohamedrejeb.calf.sample.utils.SAMPLE_AVATAR_SIZE
import com.mohamedrejeb.calf.sample.utils.decodeSampleImage
import com.mohamedrejeb.calf.sample.utils.releaseSampleBitmap
import com.mohamedrejeb.calf.ui.button.AdaptiveButton
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlin.math.min

@OptIn(ExperimentalCalfApi::class)
@Composable
fun FileSaverScreen(navigateBack: () -> Unit) {
    var selectedFile by remember { mutableStateOf<KmpFile?>(null) }
    var selectionVersion by remember { mutableStateOf(0) }
    var preparedImage by remember { mutableStateOf<ByteArray?>(null) }
    val fileNameState = remember { TextFieldState("profile_picture") }
    var saveMessage by remember { mutableStateOf<String?>(null) }
    var saveFailed by remember { mutableStateOf(false) }
    var isPreparing by remember { mutableStateOf(false) }
    var isSaving by remember { mutableStateOf(false) }
    val isBusy = isPreparing || isSaving

    val pickerLauncher = rememberFilePickerLauncher(
        type = FilePickerFileType.Image,
        selectionMode = FilePickerSelectionMode.Single,
        settings = FilePickerSettings(
            title = "Choose a profile picture",
            imageRepresentationMode = ImageRepresentationMode.Compatible,
        ),
        onResult = { files ->
            selectedFile = files.firstOrNull()
            isPreparing = selectedFile != null
            selectionVersion++
            preparedImage = null
            saveMessage = null
            saveFailed = false
        },
    )

    val saverLauncher = rememberFileSaverLauncher(
        onResult = { file ->
            isSaving = false
            saveFailed = file == null
            saveMessage = if (file != null) "Saved successfully" else "Save cancelled"
        },
    )

    // Read/decode only once per selection, before exposing even the preview to Coil.
    // An encoded-size cap alone is insufficient: decodeSampleImage also checks
    // header dimensions before allocating pixels. Browser Default is still its
    // event loop; the bounded synchronous decode is not a promise of worker offload.
    LaunchedEffect(selectedFile, selectionVersion) {
        val generation = selectionVersion
        preparedImage = null
        val file = selectedFile ?: return@LaunchedEffect
        isPreparing = true
        saveMessage = "Preparing preview…"
        try {
            preparedImage = withContext(Dispatchers.Default) {
                val bytes = file.readByteArray(maxBytes = MAX_SAMPLE_IMAGE_BYTES)
                currentCoroutineContext().ensureActive()
                circleCropSampleImage(bytes).also { currentCoroutineContext().ensureActive() }
            }
            saveMessage = "Ready to export"
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (_: Exception) {
            saveFailed = true
            saveMessage = "Image could not be prepared. Choose a valid image within the demo limits."
        } finally {
            if (selectionVersion == generation) isPreparing = false
        }
    }

    SampleScreenScaffold(
        title = "File Saver",
        navigateBack = navigateBack,
    ) { padding ->
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
        ) {
            Text(
                text = "Pick an image up to 8 MiB, 8 megapixels and 4096 pixels per side. Export a circle-cropped PNG up to 512×512 pixels.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Circle avatar preview
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier
                    .size(200.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.surfaceVariant),
            ) {
                if (preparedImage != null) {
                    AsyncImage(
                        model = preparedImage,
                        contentDescription = "Profile picture",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize(),
                    )
                } else {
                    Icon(
                        imageVector = Icons.Outlined.Person,
                        contentDescription = "Placeholder",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(80.dp),
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                state = fileNameState,
                label = { Text("File name") },
                lineLimits = androidx.compose.foundation.text.input.TextFieldLineLimits.SingleLine,
                modifier = Modifier.fillMaxWidth(),
            )

            Spacer(modifier = Modifier.height(16.dp))

            AdaptiveButton(
                onClick = { pickerLauncher.launch() },
                enabled = !isBusy,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Outlined.Image,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp),
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(if (selectedFile == null) "Choose Photo" else "Change Photo")
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            AdaptiveButton(
                onClick = {
                    // Preparation owns a bounded PNG; saving never rereads the original.
                    val bytes = preparedImage
                    if (bytes != null && !isPreparing && !isSaving) {
                        isSaving = true
                        saveFailed = false
                        saveMessage = "Waiting for save destination…"
                        try {
                            saverLauncher.launch(
                                bytes = bytes,
                                baseName = fileNameState.text.toString().ifBlank { "profile_picture" },
                                extension = "png",
                            )
                        } catch (_: Exception) {
                            isSaving = false
                            saveFailed = true
                            saveMessage = "Export could not be started. Try again."
                        }
                    }
                },
                enabled = preparedImage != null && !isBusy,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Outlined.SaveAlt,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp),
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(if (isBusy) "Export in progress…" else "Export Photo")
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = saveMessage ?: "Export status",
                style = MaterialTheme.typography.bodyMedium,
                color = when {
                    saveMessage == null -> Color.Transparent
                    saveFailed -> MaterialTheme.colorScheme.error
                    else -> MaterialTheme.colorScheme.onSurface
                },
                modifier = Modifier.alpha(if (saveMessage != null) 1f else 0f),
            )
        }
    }
}

/** Bounded sample transformation, not an unrestricted image editor or decoder API. */
internal fun circleCropSampleImage(bytes: ByteArray): ByteArray {
    val source = bytes.decodeSampleImage()
    try {
        val cropSize = min(source.width, source.height)
        val outputSize = min(cropSize, SAMPLE_AVATAR_SIZE)
        val output = ImageBitmap(outputSize, outputSize)
        try {
            val canvas = Canvas(output)
            val path = Path().apply {
                addOval(
                    androidx.compose.ui.geometry.Rect(
                        offset = Offset.Zero,
                        size = Size(outputSize.toFloat(), outputSize.toFloat()),
                    )
                )
            }
            canvas.clipPath(path)
            canvas.drawImageRect(
                image = source,
                srcOffset = IntOffset((source.width - cropSize) / 2, (source.height - cropSize) / 2),
                srcSize = IntSize(cropSize, cropSize),
                dstOffset = IntOffset.Zero,
                dstSize = IntSize(outputSize, outputSize),
                paint = Paint(),
            )
            return output.toByteArray()
        } finally {
            output.releaseSampleBitmap()
        }
    } finally {
        source.releaseSampleBitmap()
    }
}
