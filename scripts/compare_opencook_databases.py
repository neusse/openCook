"""Report recipe, image, and like changes between two private openCook databases."""

import argparse
import sqlite3
from pathlib import Path


def open_db(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    database = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    database.row_factory = sqlite3.Row
    if database.execute("pragma quick_check").fetchone()[0] != "ok":
        raise RuntimeError(f"SQLite integrity check failed: {path}")
    return database


def rows(database, table, key):
    return {row[key]: dict(row) for row in database.execute(f"select * from {table}")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()
    before, after = open_db(args.before), open_db(args.after)
    for table, key, name in (("recipes", "id", "name"), ("images", "id", "localPath")):
        old, new = rows(before, table, key), rows(after, table, key)
        added, removed = sorted(new.keys() - old.keys()), sorted(old.keys() - new.keys())
        changed = sorted(item for item in new.keys() & old.keys() if new[item] != old[item])
        print(f"{table}: {len(old)} -> {len(new)}; added {len(added)}, removed {len(removed)}, changed {len(changed)}")
        for item in added:
            print(f"  + {item}: {new[item].get(name, '')}")
        for item in removed:
            print(f"  - {item}: {old[item].get(name, '')}")
        if changed:
            print(f"  changed IDs: {changed[:20]}")
    old_likes = {tuple(row) for row in before.execute("select * from recipe_likes")}
    new_likes = {tuple(row) for row in after.execute("select * from recipe_likes")}
    print(f"recipe_likes: {len(old_likes)} -> {len(new_likes)}; added {len(new_likes - old_likes)}, removed {len(old_likes - new_likes)}")
    for row in new_likes - old_likes:
        print(f"  + {row}")
    for row in old_likes - new_likes:
        print(f"  - {row}")


if __name__ == "__main__":
    main()
