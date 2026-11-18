"""Build a private openCook batch with one real source-page cover per recovered recipe."""

import hashlib
import io
import json
import sqlite3
import zipfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "data/cheftap/wife-phone"
RECIPES = PRIVATE / "recovered-recipes.json"
COVERS = PRIVATE / "web-covers"
MANIFEST = COVERS / "manifest.json"
BATCH = COVERS / "cheftap-0001.zip"
OVERRIDES = PRIVATE / "web-cover-urls.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
TIMEOUT = 30


def image_urls(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [url for item in value for url in image_urls(item)]
    if isinstance(value, dict):
        return image_urls(value.get("url") or value.get("contentUrl") or value.get("@id"))
    return []


def recipe_images(node):
    if isinstance(node, list):
        return [url for item in node for url in recipe_images(item)]
    if not isinstance(node, dict):
        return []
    types = node.get("@type", [])
    if isinstance(types, str):
        types = [types]
    found = image_urls(node.get("image")) if "Recipe" in types else []
    return found + [url for value in node.values() if isinstance(value, (dict, list)) for url in recipe_images(value)]


def candidates(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            urls.extend(recipe_images(json.loads(tag.string or tag.get_text())))
        except json.JSONDecodeError:
            continue
    for key in ("og:image", "twitter:image", "twitter:image:src"):
        urls.extend(tag.get("content", "") for tag in soup.select(f'meta[property="{key}"],meta[name="{key}"]'))
    urls.extend(tag.get("href", "") for tag in soup.select('link[rel="image_src"]'))
    result = []
    for url in urls:
        absolute = urljoin(page_url, url.strip()) if isinstance(url, str) else ""
        if urlsplit(absolute).scheme in ("http", "https") and absolute not in result:
            result.append(absolute)
    return result


def fetch_cover(session, recipe, override=None):
    source = recipe["source"]
    if override:
        choices = [override]
        referer = source
    else:
        response = session.get(source, timeout=TIMEOUT)
        response.raise_for_status()
        choices = candidates(response.text, response.url)
        referer = response.url
    if not choices:
        raise RuntimeError(f"No recipe image metadata at {source}")
    problems = []
    for url in choices:
        try:
            image_response = session.get(url, headers={"Referer": referer}, timeout=TIMEOUT)
            image_response.raise_for_status()
            data = image_response.content
            if len(data) > 20_000_000:
                raise ValueError("image exceeds 20 MB")
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
            with Image.open(io.BytesIO(data)) as image:
                width, height = image.size
                format_name = image.format
            if width < 400 or height < 300 or format_name not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError(f"unsuitable image {width}x{height} {format_name}")
            extension = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[format_name]
            return data, extension, url, (width, height)
        except (requests.RequestException, OSError, ValueError) as error:
            problems.append(f"{url}: {error}")
    raise RuntimeError(f"No usable cover for {recipe['title']}: " + " | ".join(problems[:4]))


def existing_cover(recipe):
    """Reuse a verified earlier web download when the source URL is the same."""
    database = ROOT / "data/cheftap/neussenombox.db"
    directory = ROOT / "data/cheftap/photos"
    if not database.is_file():
        return None
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        photos = connection.execute(
            "select p.photo_id,m.link from recipes r "
            "join recipe_photos p on p.recipe_id=r.id and p.date_deleted is null "
            "left join media_id m on m.photo_id=p.photo_id "
            "where r.source_url=? and r.date_deleted is null "
            "order by p.is_main desc,p.date_added", (recipe["source"],)
        ).fetchall()
    for photo_id, url in photos:
        for extension in ("jpg", "png", "webp"):
            path = directory / f"{photo_id}.{extension}"
            if path.is_file():
                data = path.read_bytes()
                with Image.open(io.BytesIO(data)) as image:
                    image.verify()
                with Image.open(io.BytesIO(data)) as image:
                    width, height = image.size
                if width >= 400 and height >= 300:
                    return data, extension, url, (width, height)
    return None


def main():
    if not RECIPES.is_file():
        raise FileNotFoundError(RECIPES)
    recipes = json.loads(RECIPES.read_text(encoding="utf-8"))
    if len(recipes) != 10 or len({recipe["id"] for recipe in recipes}) != 10:
        raise RuntimeError("Expected ten distinct wife-only ChefTap recipes")
    COVERS.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.is_file() else {}
    records, manifest = [], []
    for recipe in recipes:
        try:
            result = fetch_cover(session, recipe, overrides.get(recipe["id"]))
        except (requests.RequestException, RuntimeError) as error:
            result = existing_cover(recipe)
            if result is None:
                raise RuntimeError(f"No web or previously verified cover for {recipe['title']}: {error}") from error
        data, extension, image_url, size = result
        filename = f"{recipe['id']}.{extension}"
        (COVERS / filename).write_bytes(data)
        manifest.append({"id": recipe["id"], "title": recipe["title"], "source": recipe["source"],
                         "imageUrl": image_url, "file": filename, "width": size[0], "height": size[1],
                         "sha256": hashlib.sha256(data).hexdigest()})
        records.append({
            "recipe": {
                "@context": "https://schema.org", "@type": "Recipe",
                "identifier": recipe["id"], "name": recipe["title"],
                "recipeIngredient": [value for kind, value in recipe["items"] if kind == 2],
                "recipeInstructions": [
                    {"@type": "HowToStep", "text": value}
                    for kind, value in recipe["items"] if kind in (1, 4, 5, 6)
                ],
                "openCookNotes": [recipe["notes"]] if recipe["notes"].strip() else [],
                "openCookTags": recipe["tags"], "url": recipe["source"],
            },
            "favorite": recipe["favorite"],
            "photos": [f"photos/{filename}"],
            "originalHtml": recipe["originalHtml"],
        })
        print(f"{recipe['title']}: {size[0]}x{size[1]} {image_url}", flush=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(BATCH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("cheftap.json", json.dumps(records, ensure_ascii=False, separators=(",", ":")))
        for item in manifest:
            archive.write(COVERS / item["file"], f"photos/{item['file']}")
        archive.writestr("IMAGE-SOURCES.txt", "One dish image per recipe, downloaded from the web.\n"
                         "These are web replacements, not the original ChefTap local photo bytes.\n"
                         "The football board uses a comparable dish photo because Food Network blocked its image.\n"
                         "See manifest.json next to this ZIP for each source URL and SHA-256.\n")
    with zipfile.ZipFile(BATCH) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Built ZIP failed integrity check")
    print(f"Built {BATCH} with {len(records)} recipes and {len(manifest)} real web covers")


if __name__ == "__main__":
    main()
