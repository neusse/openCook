"""Compare a second ChefTap snapshot and preserve recipes missing from the baseline."""

import html
import json
import re
import sqlite3
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "data/cheftap/neussenombox.db"
WIFE = ROOT / "data/cheftap/wife-phone/neussenombox.db"
EXPORT = ROOT / "data/cheftap/wife-phone/cheftap_export.zip"
OUTPUT = ROOT / "data/cheftap/wife-phone/recovered-recipes.json"
REPORT = ROOT / "data/cheftap/wife-phone/recovery-report.json"
TEXT_ONLY = ROOT / "data/cheftap/wife-phone/open-cook-text-only/cheftap-0001.zip"


def normalized(value):
    return re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", value or "").lower())


def html_pages():
    by_pair = defaultdict(list)
    by_title = defaultdict(list)
    by_source = defaultdict(list)
    with zipfile.ZipFile(EXPORT) as archive:
        for name in archive.namelist():
            if not name.lower().endswith(".html"):
                continue
            raw = archive.read(name).decode("utf-8", "replace")
            soup = BeautifulSoup(raw, "html.parser")
            heading = soup.find("h1")
            if heading is None:
                raise RuntimeError(f"HTML export has no title: {name}")
            title = html.unescape(heading.get_text(" ", strip=True))
            anchor = soup.find("a", string=re.compile("Original Article", re.I))
            source = anchor.get("href", "") if anchor else ""
            item = {"filename": name, "title": title, "source": source, "html": raw}
            by_pair[(normalized(title), source)].append(item)
            by_title[normalized(title)].append(item)
            if source:
                by_source[source].append(item)
    return by_pair, by_title, by_source


def match_page(row, tags, indexes):
    by_pair, by_title, by_source = indexes
    title, source = row["title"], row["source_url"] or ""
    for candidates in (by_pair[(normalized(title), source)], by_source[source] if source else [], by_title[normalized(title)]):
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            def matches_tag(page):
                soup = BeautifulSoup(page["html"], "html.parser")
                anchor = soup.find("a", string=re.compile("Original Article", re.I))
                first = anchor.find_next("p") if anchor else None
                value = first.get_text(" ", strip=True) if first else ""
                return value in tags if tags else normalized(value) == normalized(title)
            matched = [page for page in candidates if matches_tag(page)]
            if len(matched) == 1:
                return matched[0]
    raise RuntimeError(f"No unique HTML export page for {row['id']} ({title})")


def main():
    for path in (BASELINE, WIFE, EXPORT):
        if not path.is_file():
            raise FileNotFoundError(path)
    baseline = sqlite3.connect(f"file:{BASELINE}?mode=ro", uri=True)
    wife = sqlite3.connect(f"file:{WIFE}?mode=ro", uri=True)
    wife.row_factory = sqlite3.Row
    if wife.execute("pragma quick_check").fetchone()[0] != "ok":
        raise RuntimeError("Wife's ChefTap snapshot failed SQLite integrity check")
    baseline_rows = {row[0]: row for row in baseline.execute("select id,title,date_added,source_url from recipes where date_deleted is null")}
    baseline_ids = set(baseline_rows)
    baseline_latest = max(row[2] for row in baseline_rows.values())
    wife_rows = list(wife.execute("select * from recipes where date_deleted is null order by date_added desc,id"))
    paul_rows = [row for row in wife_rows if row["title"] == "Paul Hollywood’s Iced Gems"]
    if len(paul_rows) != 1:
        raise RuntimeError(f"Expected one Paul Hollywood cutoff recipe; found {len(paul_rows)}")
    after_paul = [row for row in wife_rows if row["date_added"] > paul_rows[0]["date_added"]]
    missing = [row for row in wife_rows if row["id"] not in baseline_ids]
    indexes = html_pages()
    recovered = []
    for row in missing:
        recipe_id = row["id"]
        tags = [tag for (tag,) in wife.execute(
            "select t.tag_text from recipe_tags rt join tags t on t.id=rt.tag_id "
            "where rt.recipe_id=? and t.date_deleted is null", (recipe_id,)
        )]
        page = match_page(row, tags, indexes)
        items = [
            [kind, text.strip()]
            for kind, text in wife.execute(
                "select type,freetext from recipe_items where recipe_id=? order by ordinal", (recipe_id,)
            )
            if kind in (1, 2, 4, 5, 6) and text and text.strip()
        ]
        photos = [
            {"photoId": photo_id, "filename": filename, "cloudUrl": link}
            for photo_id, filename, link in wife.execute(
                "select rp.photo_id,rp.file_name,m.link from recipe_photos rp "
                "left join media_id m on m.photo_id=rp.photo_id "
                "where rp.recipe_id=? and rp.date_deleted is null order by rp.is_main desc,rp.date_added",
                (recipe_id,),
            )
        ]
        if not items:
            raise RuntimeError(f"Missing structured recipe text: {recipe_id}")
        recovered.append({
            "id": recipe_id,
            "title": row["title"],
            "clippedAt": row["date_added"],
            "source": row["source_url"] or "",
            "notes": row["notes"] or "",
            "favorite": bool(row["favorite"]),
            "tags": tags,
            "items": items,
            "originalHtml": page["html"],
            "exportFile": page["filename"],
            "photos": photos,
        })
    if len(missing) != 10 or len(recovered) != len(missing):
        raise RuntimeError(f"Expected the observed 10 wife-only recipes; recovered {len(recovered)}")
    OUTPUT.write_text(json.dumps(recovered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    photo_count = sum(len(item["photos"]) for item in recovered)
    recent = [item for item in recovered if item["clippedAt"] > baseline_latest]
    if len(recent) != 8:
        raise RuntimeError(f"Expected eight new clips after {baseline_latest}; found {len(recent)}")
    for item in recent:
        if baseline.execute(
            "select count(*) from recipes where date_deleted is null and source_url=?", (item["source"],)
        ).fetchone()[0]:
            raise RuntimeError(f"New clip shares a source URL with an earlier recipe: {item['id']}")
    older = [item for item in recovered if item not in recent]
    old_only = [
        {"id": row[0], "title": row[1], "clippedAt": row[2]}
        for row in baseline_rows.values() if row[0] not in {wife_row["id"] for wife_row in wife_rows}
    ]
    date_changed = [
        {"id": row["id"], "title": row["title"], "baselineClippedAt": baseline_rows[row["id"]][2],
         "wifeClippedAt": row["date_added"]}
        for row in wife_rows if row["id"] in baseline_ids and row["date_added"] != baseline_rows[row["id"]][2]
    ]
    report = {
        "baselineRecipes": len(baseline_ids),
        "wifePhoneRecipes": len(wife_rows),
        "baselineLatestClip": baseline_latest,
        "afterPaulHollywood": [
            {"id": row["id"], "title": row["title"], "clippedAt": row["date_added"],
             "alreadyInBaseline": row["id"] in baseline_ids}
            for row in after_paul
        ],
        "recentMissingIds": [item["id"] for item in recent],
        "olderMissingIds": [item["id"] for item in older],
        "baselineOnly": old_only,
        "sharedIdsWithChangedClipDate": date_changed,
        "unavailableLocalPhotoReferences": photo_count,
        "photoBytesRecovered": 0,
        "textOnlyImportBatch": str(TEXT_ONLY),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TEXT_ONLY.parent.mkdir(parents=True, exist_ok=True)
    import_records = []
    for item in recent:
        ingredients = [value for kind, value in item["items"] if kind == 2]
        steps = [
            {"@type": "HowToStep", "text": value}
            for kind, value in item["items"] if kind in (1, 4, 5, 6)
        ]
        import_records.append({
            "recipe": {
                "@context": "https://schema.org", "@type": "Recipe",
                "identifier": item["id"], "name": item["title"],
                "recipeIngredient": ingredients, "recipeInstructions": steps,
                "openCookNotes": [item["notes"]] if item["notes"].strip() else [],
                "openCookTags": item["tags"], "url": item["source"],
            },
            "favorite": item["favorite"],
            "photos": [],
            "originalHtml": item["originalHtml"],
        })
    with zipfile.ZipFile(TEXT_ONLY, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("cheftap.json", json.dumps(import_records, ensure_ascii=False, separators=(",", ":")))
        archive.writestr(
            "PHOTO-GAP.txt",
            f"This batch has {len(recent)} real recent recipes and no image bytes. "
            f"ChefTap has {sum(len(item['photos']) for item in recent)} local photo references for them. "
            "See ../recovered-recipes.json before importing or rebuilding this archive.\n",
        )
    print(f"Saved {len(recovered)} wife-only recipes, {sum(item['favorite'] for item in recovered)} favorite, {photo_count} photo references -> {OUTPUT}")
    print(f"After Paul Hollywood’s Iced Gems: {len(after_paul)} entries, {sum(row['id'] not in baseline_ids for row in after_paul)} IDs missing from baseline")
    for row in after_paul:
        status = "NEW" if row["id"] not in baseline_ids else "ALREADY SAVED"
        print(f"  {status}: {row['date_added']} | {row['title']}")
    print(f"Prepared {len(recent)} recent recipes as an explicitly text-only openCook batch -> {TEXT_ONLY}")
    for item in recovered:
        print(f"{item['clippedAt']} | {item['id']} | {item['title']}")
    if photo_count and not all(photo["cloudUrl"] for item in recovered for photo in item["photos"]):
        print("PHOTO LIMITATION: local ChefTap photos have no URLs in this snapshot; original image bytes are not in either export")


if __name__ == "__main__":
    main()
