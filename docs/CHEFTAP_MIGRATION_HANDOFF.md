# ChefTap migration handoff

## Current state

- Repository: `C:\Users\georg\Codex_Projects\open-cook`, fork `neusse/openCook`, upstream `oliexdev/openCook`, branch `main`.
- Windows build: Android SDK Platform 37.0 and Build-Tools 37.0.0 are installed. Run `safe-pwsh --file scripts\build-windows.ps1` from the project root; the script selects Microsoft OpenJDK 17 and builds `assembleDebug`.
- The connected phone is a Samsung SM-S926U (`R5CX71W34AT`, Android 17). ChefTap and openCook v0.4 are installed. RecipeTap was removed after its local state was captured.
- openCook v0.4 was tested in phone-only mode. Three real ChefTap recipes and their first photos imported successfully (`3 imported, 0 skipped`). The rest of the library has **not** been imported into openCook.
- The private recovery data is under ignored `data/cheftap/`. `data/cheftap/inventory.json` records byte counts and SHA-256 hashes for the copied files. Keep this directory out of Git.

## Real data available locally

| Path under `data/cheftap/` | Meaning |
| --- | --- |
| `cheftap_export.zip` | ChefTap HTML export; 4,058 HTML recipe pages. |
| `cheftap_export_text.zip` | Separate ChefTap text export. |
| `cheftap-snapshot.zip` | Developer Snapshot from ChefTap. |
| `neussenombox.db` | Extracted SQLite snapshot: 4,059 nondeleted recipes, 311 favorites. It also has shopping, meal, photo, tag, and menu tables. Treat it as private; `recipe_boxes` includes account-related columns. |
| `recipetap-recipes.js` | Real merged RecipeTap seed: 4,059 recipes, IDs, structured items, notes, tags, source URLs, and photo filenames. |
| `recipetap-local-state.json` | Captured from the phone before RecipeTap uninstall: 311 liked IDs, one shopping list, no custom recipes, edits, deletions, plans, or menus. Its liked ID set equals the snapshot favorite set. |
| `cheftap_settings.json` | Recovered ChefTap settings. |
| `photos/` | 4,602 verified photo files, 2,131,059,201 bytes. Every photo referenced by `recipetap-recipes.js` is present. 764 recipes reference more than one photo. |

The old RecipeTap project remains at `C:\Users\georg\Codex_Projects\cheftap-ng` as another copy of the recovery material. `scripts/stage_cheftap_data.py` can repeat and verify staging from that project. It fails if an expected file or photo is absent.

## Next work in this fork

1. Read [`CHEFTAP_FEATURE_GAPS.md`](CHEFTAP_FEATURE_GAPS.md) and the existing openCook import/backup implementation. Choose a migration path that processes photos in bounded batches; do not load one 2.13 GB ZIP on the phone.
2. Convert the real ChefTap records while preserving recipe IDs, titles, ingredients, steps, notes, tags, source URLs, and all associated photos. Keep the original HTML available for recipes whose structure is incomplete. Produce a mapping and explicit counts for skipped or failed records.
3. Transfer the 311 favorites into openCook likes using the recorded IDs. Validate the liked-only filter and spot-check favorites, notes, source links, and multi-photo recipes on the phone.
4. Build the fork with a supported JDK and Android SDK Platform 37. The `debug` build uses package `com.food.opencook.dev`, separate from the installed v0.4 release package `com.food.opencook`; decide whether to migrate into the dev build or arrange an upgrade-compatible release signature before importing everything.
5. Preserve openCook's local-only, account-free path. An optional local server may add AI photo reading later, but is not required for viewing or importing existing recipes.

## Verification before any full import

Count 4,059 nondeleted recipes, 311 favorites, and 4,602 photos from the staged inputs. Confirm 0 missing referenced photos. Trial-import a small batch first, then check the imported recipe count, like count, notes, source URLs, and multi-photo display. Back up the target openCook data before changing import behavior or loading the full set.
