"""Check the ten real wife-only ChefTap records in an openCook database copy."""

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/cheftap/wife-phone/recovered-recipes.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("--before", action="store_true", help="Require every wife-only ID to be absent")
    args = parser.parse_args()
    if not args.database.is_file() or not SOURCE.is_file():
        raise FileNotFoundError(f"Missing real database or recovery file: {args.database}, {SOURCE}")
    expected = json.loads(SOURCE.read_text(encoding="utf-8"))
    if len(expected) != 10 or len({item["id"] for item in expected}) != 10:
        raise RuntimeError("Expected ten distinct recovered wife-only recipes")
    db = sqlite3.connect(f"file:{args.database}?mode=ro", uri=True)
    if db.execute("pragma quick_check").fetchone()[0] != "ok":
        raise RuntimeError("Phone database failed SQLite quick_check")
    problems = []
    for item in expected:
        recipe_id = item["id"]
        row = db.execute("select name,notes,tags,sourceUrl from recipes where id=?", (recipe_id,)).fetchone()
        if args.before:
            if row is not None:
                problems.append(f"{recipe_id}: already present before import")
            continue
        if row is None:
            problems.append(f"{recipe_id}: missing after import")
            continue
        actual = (row[0], row[1] or "", row[2] or "", row[3] or "")
        wanted = (item["title"], item["notes"], "\n".join(item["tags"]), item["source"])
        if actual != wanted:
            problems.append(f"{recipe_id}: title, notes, tags, or source mismatch")
        ingredients = [value for (value,) in db.execute(
            "select name from ingredients where recipeId=? order by position", (recipe_id,)
        )]
        wanted = [value for kind, value in item["items"] if kind == 2]
        if ingredients != wanted:
            problems.append(f"{recipe_id}: ingredient text/order mismatch")
        photos = db.execute("select count(*) from images where recipeId=?", (recipe_id,)).fetchone()[0]
        if photos != 1:
            problems.append(f"{recipe_id}: expected one image, found {photos}")
        liked = db.execute("select count(*) from recipe_likes where recipeId=? and liked=1", (recipe_id,)).fetchone()[0]
        if bool(liked) != item["favorite"]:
            problems.append(f"{recipe_id}: favorite mismatch")
    count = db.execute("select count(*) from recipes").fetchone()[0]
    print(f"Recipes in database: {count}; wife-only IDs checked: {len(expected)}; issues: {len(problems)}")
    for problem in problems:
        print(problem)
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
