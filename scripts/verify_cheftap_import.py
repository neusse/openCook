"""Compare an openCook database copy with the real staged ChefTap records."""

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "cheftap"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    args = parser.parse_args()
    text = (SOURCE / "recipetap-recipes.js").read_text(encoding="utf-8")
    start = text.index("window.SEED_RECIPES=") + len("window.SEED_RECIPES=")
    source, _ = json.JSONDecoder().raw_decode(text[start:])
    favorites = set(json.loads((SOURCE / "recipetap-local-state.json").read_text(encoding="utf-8"))["favorites"])
    db = sqlite3.connect(args.database)
    rows = {row[0]: row for row in db.execute("SELECT id,name,notes,tags,sourceUrl FROM recipes")}
    ingredients = Counter(dict(db.execute("SELECT recipeId,COUNT(*) FROM ingredients GROUP BY recipeId")))
    ingredient_lines = {}
    for rid, line in db.execute("SELECT recipeId,name FROM ingredients ORDER BY recipeId,position"):
        ingredient_lines.setdefault(rid, []).append(line)
    photos = Counter(dict(db.execute("SELECT recipeId,COUNT(*) FROM images GROUP BY recipeId")))
    liked = {row[0] for row in db.execute("SELECT recipeId FROM recipe_likes WHERE liked=1")}
    problems = []
    for record in source:
        rid = record["id"]
        row = rows.get(rid)
        if row is None:
            problems.append(f"{rid}: missing recipe")
            continue
        if row[1] != record["title"]:
            problems.append(f"{rid}: title mismatch")
        if (row[2] or "") != (record["notes"] if record["notes"].strip() else ""):
            problems.append(f"{rid}: notes mismatch")
        if (row[3] or "") != "\n".join(record["tags"]):
            problems.append(f"{rid}: tags mismatch")
        if (row[4] or "") != (record["source"] or ""):
            problems.append(f"{rid}: source URL mismatch")
        expected_ingredients = sum(kind == 2 and bool(value.strip()) for kind, value in record["items"])
        if ingredients[rid] != expected_ingredients:
            problems.append(f"{rid}: {ingredients[rid]}/{expected_ingredients} ingredient lines")
        expected_lines = [value.strip() for kind, value in record["items"] if kind == 2 and value.strip()]
        if ingredient_lines.get(rid, []) != expected_lines:
            problems.append(f"{rid}: ingredient text/order mismatch")
        if photos[rid] != len(record["photos"]):
            problems.append(f"{rid}: {photos[rid]}/{len(record['photos'])} photos")
    if liked != favorites:
        problems.append(f"favorites mismatch: {len(liked)} imported, {len(favorites)} expected")
    print(f"Recipes: {len(rows)}; favorites: {len(liked)}; photos: {sum(photos.values())}; issues: {len(problems)}")
    for problem in problems[:30]:
        print(problem)
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
