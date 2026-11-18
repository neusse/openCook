# ChefTap migration handoff

## Current state

- Repository: this checkout, fork `neusse/openCook`, upstream `oliexdev/openCook`, branch `main`.
- Windows build: Android SDK Platform 37.0 and Build-Tools 37.0.0 are installed. Run `safe-pwsh --file scripts\build-windows.ps1` from the project root; the script selects Microsoft OpenJDK 17 and builds `assembleDebug`.
- The original import target is a Samsung Android 17 phone. ChefTap and openCook v0.4 are installed. RecipeTap was removed after its local state was captured. Confirm the connected device with `adb devices -l` before further work.
- The fork's debug app (`com.food.opencook.dev`, shown as **openCook DEV**) is installed alongside the untouched v0.4 release app. It runs phone-only, without an account or server.
- As of the November 17, 2026 local merge, openCook DEV has **4,070 recipes, 4,616 image records, and 313 likes**. A fresh private app-data TAR before the merge had 4,060 recipes, 4,606 images, and 312 likes; ten wife-only recipes, ten web covers, and one favorite were added with zero skipped IDs. No earlier recipe or image record was removed or changed by this merge. The original captured HTML is retained per recipe in the dev app's private files. The release app still has only the earlier three trial recipes.
- The debug app now has a compact thumbnail/title recipe list, liked-only filter, multi-photo detail gallery, and **Import ChefTap folder** action. Search matched two distinct recipes with the same title in the phone test.
- The private recovery data is under ignored `data/cheftap/`. `data/cheftap/inventory.json` records byte counts and SHA-256 hashes for the copied files. Keep this directory out of Git.
- A second phone's fresh ChefTap snapshot and HTML export are staged under ignored `data/cheftap/wife-phone/`. Its ten wife-only recipe IDs were imported with one verified web cover each from `web-covers/cheftap-0001.zip`. The original 21 local ChefTap photo bytes remain unavailable. Keep ChefTap installed on that phone and read its private `RECOVERY.md` for provenance.
- Complete pre-merge and post-merge copies of openCook DEV's private data, including database, referenced images, settings, and original HTML, are under ignored `data/phone-backups/`. `scripts/verify_opencook_backup.py` verified both TAR hashes and every database image path. See [the maintainer guide](CUSTOM_FORK.md) for future backup and build commands.

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

The old RecipeTap project is a sibling checkout at `../cheftap-ng` with another copy of the recovery material. `scripts/stage_cheftap_data.py` can repeat and verify staging from that project. It fails if an expected file or photo is absent.

## Completed migration in this fork

- `scripts/prepare_cheftap_import.py` produced 203 bounded ZIP batches under ignored `data/cheftap/open-cook-import/` plus an ID mapping. No 2.13 GB ZIP is loaded into phone memory.
- The app imported all batches through Android's folder picker. It preserved ChefTap IDs and repeated ingredient lines, plus titles, steps, notes, tags, source links, every photo, favorites, and original HTML. `files/cheftap-import-report.txt` in the dev app lists every batch and any skipped IDs or failures.
- `scripts/verify_cheftap_import.py data/cheftap/final-db/opencook.db` compared the phone database with every staged source record and reported **0 issues**. The private database copy remains under ignored `data/cheftap/final-db/`.
- `scripts/verify_wife_merge.py` checked the ten new records in the post-merge database: IDs, titles, notes, tags, sources, ingredient text/order, one image each, and the favorite flag. It reported **0 issues**. `scripts/compare_opencook_databases.py` showed exactly ten recipes, ten image records, and one like added between the full backups.
- The phone's liked-only filter displayed 311 recipes. A multi-photo recipe displayed two thumbnails and its source link.

## Remaining decisions

- The imported library is in the fork's separate dev app. The installed v0.4 release cannot be overwritten with the debug signature. Keep both apps and the staged recovery data until an upgrade-compatible release signing path is arranged.
- openCook's standard backup format still excludes likes and only exports one image per recipe. Keep the ChefTap recovery data and migration batches; do not treat a standard openCook backup as a complete copy of this migration yet.

## Earlier plan (completed for the dev app)

1. Read [`CHEFTAP_FEATURE_GAPS.md`](CHEFTAP_FEATURE_GAPS.md) and the existing openCook import/backup implementation. Choose a migration path that processes photos in bounded batches; do not load one 2.13 GB ZIP on the phone.
2. Convert the real ChefTap records while preserving recipe IDs, titles, ingredients, steps, notes, tags, source URLs, and all associated photos. Keep the original HTML available for recipes whose structure is incomplete. Produce a mapping and explicit counts for skipped or failed records.
3. Transfer the 311 favorites into openCook likes using the recorded IDs. Validate the liked-only filter and spot-check favorites, notes, source links, and multi-photo recipes on the phone.
4. Build the fork with a supported JDK and Android SDK Platform 37. The `debug` build uses package `com.food.opencook.dev`, separate from the installed v0.4 release package `com.food.opencook`; the migration was performed in the dev build.
5. Preserve openCook's local-only, account-free path. An optional local server may add AI photo reading later, but is not required for viewing or importing existing recipes.

## Verification before any full import

Count 4,059 nondeleted recipes, 311 favorites, and 4,602 photos from the staged inputs. Confirm 0 missing referenced photos. Trial-import a small batch first, then check the imported recipe count, like count, notes, source URLs, and multi-photo display. Back up the target openCook data before changing import behavior or loading the full set.
