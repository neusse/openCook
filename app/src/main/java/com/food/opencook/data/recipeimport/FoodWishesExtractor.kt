/*
 *  openCook
 *  Copyright (C) 2026 olie.xdev <olie.xdeveloper@googlemail.com>
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

package com.food.opencook.data.recipeimport

import com.food.opencook.data.remote.dto.RecipeDto
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonPrimitive
import java.net.URI
import java.util.Locale

/** Imports the written ingredient list in Food Wishes' Blogger posts. The method is in the linked video. */
object FoodWishesExtractor {
    private val heading = Regex("^ingredients\\b.*:$", RegexOption.IGNORE_CASE)

    fun extract(domJson: String?, pageUrl: String): ImportedRecipe? {
        val host = runCatching { URI(pageUrl).host?.lowercase(Locale.ROOT) }.getOrNull()
        if (host != "foodwishes.blogspot.com" && host != "www.foodwishes.blogspot.com") return null
        val document = domJson?.let { runCatching { Json.parseToJsonElement(it) as? JsonObject }.getOrNull() }
            ?: return null
        val title = document.string("title")?.trim()?.takeIf { it.isNotEmpty() } ?: return null
        val lines = (document["lines"] as? JsonArray)
            ?.mapNotNull { runCatching { it.jsonPrimitive.contentOrNull?.trim() }.getOrNull() }
            ?.filter { it.isNotEmpty() }
            ?: return null
        val start = lines.indexOfFirst { heading.matches(it) }
        if (start < 0) return null
        val ingredients = lines.drop(start + 1)
            .takeWhile { !it.startsWith("View the complete recipe", ignoreCase = true) && it != "-->" }
            .filterNot { it.endsWith(":") && it.none(Char::isDigit) }
        if (ingredients.isEmpty()) return null
        val image = document.string("image")?.takeIf { it.startsWith("https://") || it.startsWith("http://") }
        return ImportedRecipe(
            dto = RecipeDto(
                name = title,
                recipeIngredient = ingredients,
                image = listOfNotNull(image),
                cookbook = SourceCookbook.fromUrl(pageUrl),
                url = pageUrl,
            ),
            imageUrl = image,
        )
    }

    private fun JsonObject.string(key: String): String? =
        this[key]?.let { runCatching { it.jsonPrimitive.contentOrNull }.getOrNull() }
}
