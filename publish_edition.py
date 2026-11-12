"""Build and verify an edition before its generated files reach GitHub Pages."""

import argparse
import hashlib
import json
import os
from datetime import date
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

import build_editions as site
import build_search

ROOT = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def preview_record():
    return Path(git("rev-parse", "--git-path", "pn-preview.json"))


def read_edition(path):
    raw = path.read_bytes()
    news = json.loads(raw)
    day = date.fromisoformat(site.get_date(news)).isoformat()
    stories = []
    for section, expected in (("nl", 6), ("int", 6), ("headlines", 3)):
        items = site.items(news, section)
        if len(items) != expected:
            raise ValueError(f"{section}: verwacht {expected} verhalen, kreeg {len(items)}.")
        if section != "headlines":
            stories.extend(items)
    urls = [site.article_page_url(item, day) for item in stories if site.has_article_page(item)]
    if len(set(urls)) != 12:
        raise ValueError("De editie moet twaalf unieke, uitgewerkte artikelpagina’s bevatten.")
    return raw, day, stories, urls


def files_for_preview(day, stories, urls):
    files = [Path("index.html"), Path("edities", day, "index.html")]
    cache = site._load_pixabay_cache()
    for item, url in zip(stories, urls):
        slug = item["article_slug"].strip("/")
        page = Path(urlsplit(url).path.lstrip("/"), "index.html")
        files.append(page)
        query = item.get("image_query")
        if query:
            cached = cache.get(f"{day}/{slug}", {})
            image = cached.get("image_path")
            if cached.get("query") != query or not image or not Path(image.lstrip("/")).is_file():
                raise ValueError(f"Geen opgeslagen beeld voor {slug}.")
            files.append(Path(image.lstrip("/")))
    for path in files:
        if not path.is_file():
            raise ValueError(f"Ontbrekend publicatiebestand: {path}")
    return files


def snapshot(day, files):
    # Approval metadata and evidence can be completed after the visual review.
    excluded = [
        f":(exclude)redactie/{day}.json",
    ]
    staged = git("diff", "--cached", "--raw", "--no-abbrev", "HEAD", "--", ".", *excluded)
    return {
        "base": git("rev-parse", "HEAD"),
        "diff": hashlib.sha256(staged.encode()).hexdigest(),
        "pages": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
    }


def prepare(source):
    if git("status", "--porcelain"):
        raise ValueError("Gebruik een schone, aparte checkout voor de editie.")
    raw, day, stories, urls = read_edition(source)
    archive = Path("edities", f"{day}.json")
    site.NEWS_PATH.write_bytes(raw)
    archive.write_bytes(raw)
    site.build_site()
    build_search.build_index()
    files = files_for_preview(day, stories, urls)
    git("add", "-A")
    record = snapshot(day, files)
    preview_record().write_text(json.dumps(record, indent=2), encoding="utf-8")
    print("Open de preview via python3 -m http.server 8000 --bind 127.0.0.1")
    print(f"Editie {day}: homepage, editiepagina en twaalf artikelpagina’s.")


def check_files():
    raw, day, stories, urls = read_edition(site.NEWS_PATH)
    if Path("edities", f"{day}.json").read_bytes() != raw:
        raise ValueError("Homepage en archief gebruiken verschillende editiebestanden.")
    return day, files_for_preview(day, stories, urls)


def verify():
    day, files = check_files()
    expected = json.loads(preview_record().read_text(encoding="utf-8"))
    git("add", "-A")
    if snapshot(day, files) != expected:
        raise ValueError("De publicatiebestanden wijken af van de preview. Maak een nieuwe preview.")
    subprocess.run([sys.executable, "editorial_check.py", "--website"], check=True)
    print("Publicatiebestanden komen overeen met de preview en de redactiecontrole is geslaagd.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", type=Path, metavar="EDITIE_JSON")
    action.add_argument("--verify", action="store_true")
    action.add_argument("--check-files", action="store_true")
    args = parser.parse_args()
    source = args.prepare.resolve() if args.prepare else None
    os.chdir(ROOT)
    try:
        if source:
            prepare(source)
        elif args.check_files:
            check_files()
        else:
            verify()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Editiecontrole: {exc}\n")


if __name__ == "__main__":
    main()
