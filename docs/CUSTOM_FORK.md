# Maintaining the custom openCook Android app

This is the public source for the `neusse/openCook` fork. Its Android debug build
installs as **openCook DEV** (`com.food.opencook.dev`) alongside upstream
openCook (`com.food.opencook`). Normal recipe browsing and the ChefTap import
work without a server, account, or cloud sync.

## Windows development setup

Use PowerShell 7, Python 3, Microsoft OpenJDK 17, and Android SDK Platform 37.0.
`ANDROID_HOME` must point to that SDK. From the repository root:

```powershell
python -m pip install -r scripts\requirements.txt
safe-pwsh --file scripts\build-windows.ps1
safe-pwsh --file scripts\build-windows.ps1 -- -GradleTask testDebugUnitTest
adb devices -l
adb -s <serial> install -r app\build\outputs\apk\debug\openCook-debug.apk
```

The existing DEV installation can be updated only with the same Android signing
key. The optional `debug.keystore` entry in ignored `local.properties` selects
the key used by this checkout. Preserve that key outside Git. Check the package
and signing identity before any future install; never uninstall the populated
DEV app merely to work around a signature mismatch.

GitHub Actions runs the unit tests and builds the source on each push. Its
temporary signing key is different, so it does not publish an installable APK.
Build phone updates locally with the preserved key.

## Private library and phone backup

All owner exports, images, databases, import ZIPs, and phone backups belong under
ignored `data/`. They must never be committed or uploaded to GitHub. The current
recovery paths and counts are in [the migration handoff](CHEFTAP_MIGRATION_HANDOFF.md).

Before an app update or import, connect the phone that holds openCook DEV and run:

```powershell
python scripts\backup_opencook_dev.py --serial <serial>
```

This stops the app, streams its complete private data into a local TAR, verifies
the archive contains the database and image files, and extracts a database copy
for read-only checks. Confirm its SHA-256 and that every database image path is
present with `python scripts\verify_opencook_backup.py <backup-folder>`. Keep
the backup and its `manifest.json` together.

The original 4,059-recipe ChefTap import is reproducible from the private
snapshot, HTML export, and 4,602 recovered photo files with
`scripts/prepare_cheftap_import.py`. The ten wife-only recipe IDs are preserved
in `data/cheftap/wife-phone/recovered-recipes.json`; their one-cover-per-recipe
import is built by `scripts/build_wife_web_covers.py` and documented in that
directory's private `RECOVERY.md`. These ten images are web replacements, not
the original ChefTap local photo bytes.

To import a prepared batch, copy its ZIP into a dedicated folder on the phone,
open **openCook DEV → Import → Import ChefTap folder**, and select that folder.
Use a folder containing only the intended `cheftap-0001.zip` batch. Read the
app's `files/cheftap-import-report.txt` and compare a new database backup with
the source records before considering the merge complete.

## Release state

The existing upstream v0.4 app has a different package and signing identity.
The custom DEV app is the populated installation. A stable, upgrade-compatible
release channel and a complete in-app backup format for likes and multiple
photos remain to be built. Keep the private recovery inputs and phone backups.
