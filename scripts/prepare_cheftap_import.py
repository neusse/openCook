"""Build small, private openCook import ZIPs from the staged ChefTap recovery data."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "cheftap"
OUTPUT = SOURCE / "open-cook-import"


def load_recipes():
    text = (SOURCE / "recipetap-recipes.js").read_text(encoding="utf-8")
    start = text.index("window.SEED_RECIPES=") + len("window.SEED_RECIPES=")
    recipes, _ = json.JSONDecoder().raw_decode(text[start:])
    return recipes


def convert(record, favorites):
    ingredients = []
    steps = []
    for kind, value in record["items"]:
        value = value.strip()
        if not value:
            continue
        if kind == 2:
            ingredients.append(value)
        elif kind in (1, 5, 6):
            steps.append({"@type": "HowToStep", "text": value})
        elif kind == 4:
            steps.append({"@type": "HowToStep", "text": value})
    notes = [record["notes"]] if record["notes"].strip() else []
    # The source HTML is also retained in the original export and in each manifest.
    dto = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "identifier": record["id"],
        "name": record["title"],
        "recipeIngredient": ingredients,
        "recipeInstructions": steps,
        "openCookNotes": notes,
        "openCookTags": record["tags"],
        "url": record["source"],
    }
    return {
        "recipe": dto,
        "favorite": record["id"] in favorites,
        "photos": ["photos/" + name for name in record["photos"]],
        "originalHtml": record["html"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 50:
        parser.error("batch size must be between 1 and 50")
    recipes = load_recipes()
    favorites = set(json.loads((SOURCE / "recipetap-local-state.json").read_text(encoding="utf-8"))["favorites"])
    ids = [recipe["id"] for recipe in recipes]
    if len(ids) != 4059 or len(set(ids)) != len(ids) or len(favorites) != 311 or not favorites <= set(ids):
        raise RuntimeError("ChefTap recipe/favorite counts or IDs do not match the handoff")
    photos = [name for recipe in recipes for name in recipe["photos"]]
    missing = sorted({name for name in photos if not (SOURCE / "photos" / name).is_file()})
    if len(photos) != 4602 or missing:
        raise RuntimeError(f"Photo count mismatch or missing references: {missing[:10]}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    mapping = []
    for offset in range(0, len(recipes), args.batch_size):
        number = offset // args.batch_size + 1
        path = OUTPUT / f"cheftap-{number:04d}.zip"
        batch = recipes[offset:offset + args.batch_size]
        converted = [convert(item, favorites) for item in batch]
        with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=1, allowZip64=True) as archive:
            archive.writestr("cheftap.json", json.dumps(converted, ensure_ascii=False, separators=(",", ":")))
            for name in dict.fromkeys(name for item in batch for name in item["photos"]):
                archive.write(SOURCE / "photos" / name, "photos/" + name)
        mapping.extend({"cheftapId": item["id"], "openCookId": item["id"], "batch": path.name,
                        "favorite": item["id"] in favorites, "photoCount": len(item["photos"])} for item in batch)
        print(f"{path.name}: {len(batch)} recipes, {sum(len(item['photos']) for item in batch)} photos")
    (OUTPUT / "mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prepared {len(mapping)} recipes, {len(favorites)} favorites, {len(photos)} photos; 0 missing")


if __name__ == "__main__":
    main()
