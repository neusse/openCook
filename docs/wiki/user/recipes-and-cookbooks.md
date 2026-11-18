# Recipes, cookbooks & importing

Everything about getting recipes into openCook and finding them again. All of this works offline
(except the first barcode lookup and web import, which need the internet/server).

## Browsing & searching

The **Recipes** screen uses compact rows with a thumbnail, title, and favorite heart, so a large
library is easy to scan. Search matches titles, tags, ingredients, categories, and cookbooks. The
filter control in the search field includes **Liked**, which shows only favorites.

Open any recipe for the full view — ingredients, steps and (if present) nutrition — plus quick
actions: mark as **cooked**, **like** it, add it to the **meal plan**, or delete it.

On a **tablet in landscape** a recipe opens as a cooking-friendly two-column view — ingredients
(with the portions stepper) on the left, the steps on the right — so
you don't scroll between them while cooking. The screen also stays awake while a recipe is open.
Recipes with several photos show a row of thumbnails below the main photo; tap one to view it.

## Import a ChefTap library

The ChefTap migration tool works offline and imports small ZIP batches from one folder. Keep the
original ChefTap export and snapshot as your recovery copy.

1. On a Windows PC, run `python scripts/prepare_cheftap_import.py` from this project. It checks
   the staged records and photos under the ignored `data/cheftap/` directory and writes batches
   under `data/cheftap/open-cook-import/`.
2. Copy the batch ZIPs into a folder in the phone's **Download** directory.
3. In openCook, tap **Add recipe → Import ChefTap folder** and choose that folder.

Each recipe keeps its ChefTap ID, ingredients, steps, notes, tags, source link, and all photos.
ChefTap favorites become openCook likes. The original captured page is available from **Original
ChefTap capture** on the recipe detail screen. The import is additive; repeated titles remain
separate recipes. A batch report is saved in the app's private files.

## Add a recipe by hand

No photo needed:

1. From **Scan**, choose to create a recipe manually (or use the new-recipe action).
2. The **Review** editor opens empty — type the title, add ingredients (with amounts and units),
   steps, servings, times, category and tags.
3. Save. It lands in your library like any other recipe.

## Discover: browse recipe sites in the app

**Discover recipes** is a board of cooking sites you can open without leaving openCook. Tap a tile
and the site loads in a built-in browser view; when a recipe is on screen, **Import this recipe**
saves it to your library through the same reader the share sheet uses.

The English board includes Closet Cooking, Food Network, NYT Cooking, Food.com, and Food Wishes.
For Closet Cooking, Food Network, and Food Wishes, a shared link opens in this browser view so you
can see the page and tap **Import this recipe**. NYT Cooking and Food.com links import directly when
their recipe data is available. Food Wishes posts usually publish ingredients beside a cooking
video rather than written steps; openCook saves the ingredients and source link, leaving steps empty
when the post has none. A site may require you to accept cookies or sign in before its recipe loads.

- The board **follows your content language**, and you can shape it: remove a tile you never use, or
  **Add** any address of your own (`chefkoch.de/rezepte`).
- These are other people's sites, with their own ads and their own cookies — openCook is not
  affiliated with them and saves only the recipe you choose to import, for your personal use.
- Cookies are kept per site, so a consent banner you accepted doesn't come back on every visit. You
  can delete a single site's cookies again from its tile.
- It needs Android's System WebView. Without it the board says so, and photos, files, shared links
  and manual entry all still work.

## Import from the web (browser extension)

A small browser add-on grabs recipes from cooking websites (Chefkoch, Lecker, Eat-this, and any
site that embeds a standard recipe) and sends them straight to your openCook server. At your next
sync they appear in your library on every phone.

- It only reads the recipe data the page already publishes, and sends it **only to your own
  server** — nothing is shared with third parties.
- Setup and usage are in the extension's own guide: [`extension/`](../../extension/README.md).
- Needs a connected server (it's the server's import inbox the extension fills).

## Share to openCook (from your phone's browser)

On your phone you don't need the extension at all. While browsing a recipe on a cooking site
(Chefkoch, Lecker, NDR, Eat-this, and any site that embeds a standard recipe), use the browser's
**Share** button and pick **openCook** from the share sheet.

openCook opens, reads the page's recipe and saves it straight to your library — no server required.
A snackbar confirms the import (or tells you if the page has no machine-readable recipe).

- Works **on-device over the internet only** — the app fetches and parses the page itself, so it
  works even without a server. The imported recipe then syncs to the rest of the family like any
  other (via your server, or directly phone-to-phone at home).
- The recipe is filed under a cookbook named after the source site (e.g. *Chefkoch*), unless the
  page already names its own cookbook.
- If you share the same recipe twice, openCook recognises the duplicate instead of adding it again.

## Scan barcodes

When adding items to your **shopping list** or **pantry**, you can scan a product barcode instead of
typing:

1. Tap the barcode-scan action on the shopping list or pantry.
2. Point the camera at the barcode.
3. openCook looks the product up (via [Open Food Facts](https://world.openfoodfacts.org)) and fills
   in the name for you.

The first time you scan a given product it needs the internet; after that the product is remembered
on the phone, so the same barcode resolves **instantly and offline** next time.

## Likes & "last cooked"

- **Likes** are per person — each family member can like the recipes they enjoy. The meal planner
  uses this (see [Meal planner](meal-planner.md)).
- Marking a recipe **cooked** records when you last made it, which helps the planner avoid serving
  the same thing too often. If you cook it on a day that had a *different* dish planned, the plan
  adjusts to match — see [Meal planner → When you cook something else](meal-planner.md#when-you-cook-something-else).
