"""Verify a local openCook DEV TAR contains every database-referenced image."""

import argparse
import hashlib
import json
import sqlite3
import tarfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    folder = args.folder
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    archive = folder / manifest["archive"]
    digest = hashlib.sha256()
    with archive.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
    if digest.hexdigest() != manifest["sha256"]:
        raise RuntimeError("Backup TAR SHA-256 differs from its capture manifest")
    with tarfile.open(archive, "r") as saved:
        names = {member.name.lstrip("./") for member in saved.getmembers()}
    database = sqlite3.connect(f"file:{folder / 'opencook.db'}?mode=ro", uri=True)
    if database.execute("pragma quick_check").fetchone()[0] != "ok":
        raise RuntimeError("Backed-up SQLite database failed quick_check")
    package_root = f"/data/user/0/{manifest['package']}/"
    rows = database.execute("select id,localPath from images").fetchall()
    missing = []
    for image_id, path in rows:
        if not path:
            continue
        if not path.startswith(package_root) or path[len(package_root):] not in names:
            missing.append((image_id, path))
    print(f"Backup SHA-256: {digest.hexdigest()}")
    print(f"Recipes: {database.execute('select count(*) from recipes').fetchone()[0]}")
    print(f"Image records: {len(rows)}; missing image files: {len(missing)}")
    print(f"Likes: {database.execute('select count(*) from recipe_likes').fetchone()[0]}")
    if missing:
        raise RuntimeError(f"Backup does not contain database-referenced images: {missing[:5]}")


if __name__ == "__main__":
    main()
