package com.food.opencook.data.recipeimport

import android.content.Context
import android.net.Uri
import com.food.opencook.data.image.ImageStore
import com.food.opencook.data.local.entity.ImageEntity
import com.food.opencook.data.local.entity.IngredientEntity
import com.food.opencook.data.remote.dto.RecipeDto
import com.food.opencook.data.remote.mapper.toMappedRecipe
import com.food.opencook.data.settings.SettingsRepository
import com.food.opencook.repository.RecipeRepository
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.io.File
import java.util.zip.ZipInputStream
import javax.inject.Inject

@Serializable
private data class ChefTapRecord(
    val recipe: RecipeDto,
    val favorite: Boolean,
    val photos: List<String>,
    val originalHtml: String,
)

data class ChefTapResult(val imported: Int, val skipped: List<String>, val photos: Int, val favorites: Int)

/** Imports one bounded ChefTap archive. Opens it twice so photos stream to durable files. */
class ChefTapImporter @Inject constructor(
    @ApplicationContext private val context: Context,
    private val json: Json,
    private val images: ImageStore,
    private val recipes: RecipeRepository,
    private val settings: SettingsRepository,
) {
    suspend fun import(uri: Uri): ChefTapResult = withContext(Dispatchers.IO) {
        val records = readRecords(uri)
        require(records.size in 1..50) { "ChefTap batch must contain 1–50 recipes" }
        val ids = records.map { it.recipe.identifier ?: error("ChefTap recipe has no ID") }
        require(ids.distinct().size == ids.size) { "Duplicate ChefTap ID in batch" }
        val expected = records.flatMap { it.photos }.toSet()
        val restored = mutableMapOf<String, String>()
        open(uri).use { input ->
            ZipInputStream(input).use { zip ->
                var entry = zip.nextEntry
                while (entry != null) {
                    if (!entry.isDirectory && entry.name in expected) {
                        require(entry.name !in restored) { "Duplicate photo ${entry.name}" }
                        restored[entry.name] = images.saveRestoredImage(zip)
                    }
                    zip.closeEntry()
                    entry = zip.nextEntry
                }
            }
        }
        val missing = expected - restored.keys
        require(missing.isEmpty()) { "Missing ChefTap photos: ${missing.take(5)}" }
        var imported = 0
        var favorites = 0
        val skipped = mutableListOf<String>()
        val nodeId = settings.ensureNodeId()
        records.forEach { record ->
            val id = record.recipe.identifier!!
            val mapped = record.recipe.copy(image = emptyList()).toMappedRecipe(null, System.currentTimeMillis())
            // ChefTap may repeat the same ingredient in several sections of one recipe.
            // The ordinary web mapper merges duplicates; migration must retain every line.
            val ingredientRows = record.recipe.recipeIngredient.mapIndexed { index, line ->
                IngredientEntity(
                    id = "cheftap-$id-ingredient-$index",
                    recipeId = id,
                    position = index,
                    quantity = null,
                    unit = null,
                    name = line,
                )
            }
            val photoRows = record.photos.mapIndexed { index, path ->
                ImageEntity(
                    id = "cheftap-$id-$index",
                    recipeId = id,
                    position = index,
                    remoteName = null,
                    localPath = restored.getValue(path),
                    isPrimary = index == 0,
                )
            }
            try {
                recipes.importRecipeById(mapped.recipe, ingredientRows, mapped.instructions, mapped.nutrition, photoRows)
            } catch (failure: Exception) {
                error("ChefTap recipe $id failed: ${failure.message}")
            }
            imported++
            if (record.favorite) {
                recipes.setLiked(id, nodeId, true)
                favorites++
            }
            // Retain the captured page, including formatting absent from structured fields.
            val originalDir = File(context.filesDir, "cheftap-original").apply { mkdirs() }
            File(originalDir, "$id.html").writeText(record.originalHtml, Charsets.UTF_8)
        }
        ChefTapResult(imported, skipped, restored.size, favorites)
    }

    private fun open(uri: Uri) = context.contentResolver.openInputStream(uri)
        ?: error("Cannot open ChefTap archive: $uri")

    private fun readRecords(uri: Uri): List<ChefTapRecord> {
        open(uri).use { input ->
            ZipInputStream(input).use { zip ->
                var entry = zip.nextEntry
                while (entry != null) {
                    if (entry.name == "cheftap.json") {
                        return json.decodeFromString<List<ChefTapRecord>>(zip.readBytes().decodeToString())
                    }
                    zip.closeEntry()
                    entry = zip.nextEntry
                }
            }
        }
        error("Not a ChefTap migration archive: $uri")
    }
}
