# ChefTap features and openCook gaps

This inventory compares the installed ChefTap app and the recovered owner
snapshot with openCook v0.4. It records confirmed differences that matter for
this migration. openCook already has local recipes, search, source links, likes,
tags, meal planning, shopping, phone sharing, and backups; those are not gaps.

| Priority | ChefTap behavior | openCook v0.4 state | Evidence and impact |
| --- | --- | --- | --- |
| High | A recipe may have several photos, visible as part of its capture. | The ZIP import takes only the first `image` reference, and the detail view selects one image for its header. There is no multi-photo gallery in the current detail screen. | 4,602 recovered photos belong to 3,495 recipes; 764 recipes have more than one. See `RecipeBundle.readZip`, `ImportViewModel.saveOne`, and `RecipeDetailScreen.imageModelFor`. Importing now would leave additional photos unused. |
| High | ChefTap keeps the original captured article/body, including formatting that may not parse as a structured recipe. | The phone share importer accepts schema.org/Recipe JSON-LD; it reports no recipe when a page lacks machine-readable recipe data. File import maps structured fields and does not retain the original HTML body. | The ChefTap HTML ZIP has 4,058 recipe pages. See `JsonLdExtractor`, `RecipeImportParser`, and `docs/wiki/user/recipes-and-cookbooks.md`. Preserve the HTML archive and provide a readable fallback for pages that do not parse. |
| Medium | Multiple named shopping lists. | openCook has one household shopping list. | ChefTap's Shop screen shows a list of lists; its snapshot has 17 active lists and 8 active items. openCook's `ShoppingListScreen` and local shopping model have no list entity. |
| Medium | Named recipe menus or reusable groups. | openCook has cookbooks and a meal plan, but no equivalent menu collection screen or menu entity. | ChefTap has a Menus tab and `food_menus`/`food_menu_items` tables. This owner's snapshot has zero menu records, so the feature matters for future use rather than current migration data. |
| Medium | Month calendar grid for meal planning. | openCook uses a rolling day list grouped by week. | ChefTap's Plan screen shows a month grid and dated agenda; openCook's `MealPlanScreen` builds a rolling list. The snapshot has 4 active meals. |
| Low | Draggable fast-scroll indicator on the main recipe list. | The current openCook recipe list has no corresponding fast-scroll control or setting. | ChefTap Settings exposes “Fast scrolling”; useful with 4,059 recipes. Verify usability after importing the full library before implementing it. |

## Migration compatibility gaps

These are missing migration paths, rather than absent everyday features:

| Gap | What is needed |
| --- | --- |
| ChefTap favorites to openCook likes | openCook supports likes and liked-only filtering, but its recipe file importer does not import them and its backup ZIP deliberately excludes likes. The saved phone state and ChefTap snapshot agree on 311 favorites. Map those 311 real recipe IDs to openCook's per-device likes after recipe import. |
| ChefTap export and snapshot import | openCook accepts schema.org JSON or its own ZIP layout, not ChefTap's HTML/text exports or SQLite snapshot. Add a converter or an in-app migration path that preserves IDs, notes, tags, source URLs, and every photo. |
| Large-library import | `ImportViewModel.importFromUri` reads the entire file into a byte array. A single archive containing 2.13 GB of recovered photos is not viable on the phone. Use bounded batches or streaming and report imported, skipped, and failed recipe IDs. |
| Existing meal and shopping data | The snapshot has 4 active meals, 17 active shopping lists, and 8 active shopping items. Map these only after deciding how multiple lists and the calendar view should work in openCook. |

ChefTap's hosted sync is intentionally outside this local-only project's target.
Phone-to-phone LAN sync and optional self-hosting already exist in openCook.
