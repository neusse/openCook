"""Copy real ChefTap recovery data into openCook's ignored local data folder."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "cheftap"
FILES = {
    "cheftap_export.zip": "cheftap_export.zip",
    "cheftap_export text .zip": "cheftap_export_text.zip",
    "data/cheftap-snapshot.zip": "cheftap-snapshot.zip",
    "data/neussenombox.db": "neussenombox.db",
    "data/cheftap_settings.json": "cheftap_settings.json",
    "data/recipetap-local-state.json": "recipetap-local-state.json",
    "app/src/main/assets/recipes.js": "recipetap-recipes.js",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def copy_verified(source: Path, destination: Path) -> dict:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if source.stat().st_size != destination.stat().st_size or digest(source) != digest(destination):
        raise RuntimeError(f"Copy verification failed: {source}")
    return {"bytes": source.stat().st_size, "sha256": digest(destination)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Existing RecipeTap project directory")
    args = parser.parse_args()
    source_root = args.source.resolve(strict=True)
    if source_root == ROOT:
        raise ValueError("Source and destination projects must differ")

    manifest = {"source": str(source_root), "files": {}, "photos": {}}
    for relative, target in FILES.items():
        manifest["files"][target] = copy_verified(source_root / relative, DEST / target)

    source_photos = source_root / "data" / "photos"
    photos = sorted(path for path in source_photos.iterdir() if path.is_file())
    if not photos:
        raise RuntimeError(f"No recovered photos in {source_photos}")
    total = 0
    for photo in photos:
        details = copy_verified(photo, DEST / "photos" / photo.name)
        total += details["bytes"]
    manifest["photos"] = {"count": len(photos), "bytes": total}
    (DEST / "inventory.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Staged {len(photos)} verified photos ({total:,} bytes) and {len(FILES)} data files in {DEST}")


if __name__ == "__main__":
    main()
