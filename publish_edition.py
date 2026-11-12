"""Build and verify an edition before its generated files reach GitHub Pages."""

import argparse
import hashlib
import json
import os
from datetime import date
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from urllib.parse import urlsplit

import build_editions as site
import editorial_check

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
    portrait = json.loads(site.NEWS_PATH.read_bytes()).get("meta", {}).get("personal_note", {}).get("portrait_url")
    if portrait and portrait.startswith("/images/redactie/"):
        files.append(Path(portrait.lstrip("/")))
    for path in files:
        if not path.is_file():
            raise ValueError(f"Ontbrekend publicatiebestand: {path}")
    return files


def dossier_path(day):
    return Path("redactie", f"{day}.json")


def snapshot(day, files):
    path = dossier_path(day)
    dossier = json.loads(path.read_bytes())
    # Only the owner's approval fields may change after the preview.
    dossier.pop("approved", None)
    dossier.pop("approved_by", None)
    staged = git("diff", "--cached", "--raw", "--no-abbrev", "HEAD", "--", ".", f":(exclude){path}")
    return {
        "base": git("rev-parse", "HEAD"),
        "diff": hashlib.sha256(staged.encode()).hexdigest(),
        "dossier": editorial_check.news_digest(dossier),
        "pages": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
    }


def prepare(source, evidence):
    if git("status", "--porcelain"):
        raise ValueError("Gebruik een schone, aparte checkout voor de editie.")
    preview_record().unlink(missing_ok=True)
    raw, day, stories, urls = read_edition(source)
    news = json.loads(raw)
    dossier = json.loads(evidence.read_bytes())
    dossier.update(approved=False, approved_by="")
    started = perf_counter()
    report = editorial_check.check(news, dossier, website=True, require_approval=False)
    if not report["ready"]:
        raise ValueError("Redactiecontrole vóór preview:\n" + "\n".join(report["errors"]))
    for warning in report["warnings"]:
        print(f"Waarschuwing: {warning}")
    print(f"Redactioneel dossier gecontroleerd in {perf_counter() - started:.2f} s.", flush=True)

    started = perf_counter()
    site.NEWS_PATH.write_bytes(raw)
    Path("edities", f"{day}.json").write_bytes(raw)
    dossier_path(day).parent.mkdir(exist_ok=True)
    dossier_path(day).write_text(json.dumps(dossier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, "build_editions.py"], check=True)
    files = files_for_preview(day, stories, urls)
    git("add", "-A")
    record = snapshot(day, files)
    preview_record().write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"Bestanden gebouwd en gecontroleerd in {perf_counter() - started:.2f} s.")
    print("Open de preview via python3 -m http.server 8000 --bind 127.0.0.1")
    print(f"Editie {day}: homepage, editiepagina en twaalf artikelpagina’s.")


def check_files():
    raw, day, stories, urls = read_edition(site.NEWS_PATH)
    if Path("edities", f"{day}.json").read_bytes() != raw:
        raise ValueError("Homepage en archief gebruiken verschillende editiebestanden.")
    return day, files_for_preview(day, stories, urls)


def verify():
    started = perf_counter()
    day, files = check_files()
    expected = json.loads(preview_record().read_text(encoding="utf-8"))
    git("add", "-A")
    if snapshot(day, files) != expected:
        raise ValueError("De publicatiebestanden wijken af van de preview. Maak een nieuwe preview.")
    dossier = json.loads(dossier_path(day).read_bytes())
    if dossier.get("approved") is not True or not str(dossier.get("approved_by") or "").strip():
        raise ValueError("Expliciete goedkeuring voor deze preview ontbreekt.")
    print(f"Goedgekeurde bestanden komen overeen met de gecontroleerde preview ({perf_counter() - started:.2f} s).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", type=Path, metavar="EDITIE_JSON")
    action.add_argument("--verify", action="store_true")
    action.add_argument("--check-files", action="store_true")
    parser.add_argument("--dossier", type=Path, metavar="DOSSIER_JSON")
    args = parser.parse_args()
    if bool(args.prepare) != bool(args.dossier):
        parser.error("--prepare en --dossier horen bij elkaar.")
    source = args.prepare.resolve() if args.prepare else None
    evidence = args.dossier.resolve() if args.dossier else None
    os.chdir(ROOT)
    try:
        if source:
            prepare(source, evidence)
        elif args.check_files:
            check_files()
        else:
            verify()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Editiecontrole: {exc}\n")


if __name__ == "__main__":
    main()
