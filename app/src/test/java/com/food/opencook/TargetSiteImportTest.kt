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

package com.food.opencook

import com.food.opencook.data.recipeimport.BrowserFirstSites
import com.food.opencook.data.recipeimport.FoodWishesExtractor
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class TargetSiteImportTest {
    @Test
    fun routesBrowserOnlySitesToTheBrowser() {
        assertTrue(BrowserFirstSites.contains("https://www.closetcooking.com/creamy-white-chicken-chili/"))
        assertTrue(BrowserFirstSites.contains("https://www.foodnetwork.com/recipes/example"))
        assertTrue(BrowserFirstSites.contains("https://foodwishes.blogspot.com/2012/11/example.html"))
        assertTrue(!BrowserFirstSites.contains("https://www.food.com/recipe/example"))
        assertTrue(!BrowserFirstSites.contains("https://cooking.nytimes.com/recipes/example"))
        assertTrue(!BrowserFirstSites.contains("https://foodnetwork.com.evil.example/recipe"))
    }

    @Test
    fun foodWishesExtractsOnlyWrittenIngredients() {
        val page = """{"title":"Make-Ahead Turkey Wing Gravy","lines":["Introduction","Ingredients:","For the stock:","1 large onion, chopped","2 carrots, chopped","View the complete recipe"],"image":"https://example.com/gravy.jpg"}"""
        val recipe = FoodWishesExtractor.extract(
            page,
            "https://foodwishes.blogspot.com/2012/11/make-ahead-turkey-wing-gravy-because.html",
        )
        assertEquals("Make-Ahead Turkey Wing Gravy", recipe?.dto?.name)
        assertEquals(listOf("1 large onion, chopped", "2 carrots, chopped"), recipe?.dto?.recipeIngredient)
        assertEquals("https://example.com/gravy.jpg", recipe?.imageUrl)
        assertTrue(recipe?.dto?.recipeInstructions.isNullOrEmpty())
    }

    @Test
    fun foodWishesRejectsUnrelatedPagesAndMissingIngredients() {
        val page = """{"title":"Example","lines":["No written recipe"],"image":""}"""
        assertNull(FoodWishesExtractor.extract(page, "https://foodwishes.blogspot.com/2026/example.html"))
        assertNull(FoodWishesExtractor.extract(page, "https://example.com/recipe"))
    }
}
