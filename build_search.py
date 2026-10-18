#!/usr/bin/env python3
"""Build a privacy-friendly search index for articles and informational pages."""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import json
import re
from urllib.parse import urlsplit
from categories import CATEGORY_ALIASES

ROOT = Path(__file__).resolve().parent
DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*$")
INFORMATION_PATHS = {
    "/over/": ("Over ons", "Over"),
    "/contact/": ("Contact", "Contact"),
    "/nieuwsbrief/": ("Nieuwsbrief", "Nieuwsbrief"),
    "/steun/": ("Steun Positief nieuws", "Steun"),
    "/tip/": ("Tip de redactie", "Contact"),
    "/onderwerpen/": ("Onderwerpen", "Onderwerpen"),
    "/edities/": ("Eerdere edities", "Edities"),
}


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignore = 0
        self.in_main = False
        self.main_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg", "form", "footer", "nav", "aside"):
            self.ignore += 1
        if tag == "main":
            self.in_main = True
            self.main_depth += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg", "form", "footer", "nav", "aside"):
            self.ignore = max(0, self.ignore - 1)
        if tag == "main":
            self.main_depth = max(0, self.main_depth - 1)
            if not self.main_depth:
                self.in_main = False

    def handle_data(self, data):
        if self.in_main and not self.ignore:
            value = " ".join(data.split())
            if value:
                self.parts.append(value)


def flatten(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(flatten(v) for v in value)
    if isinstance(value, dict):
        return " ".join(flatten(v) for v in value.values())
    return ""


def info_record(url, title, category, kind="pagina"):
    filename = ROOT / url.strip("/") / "index.html"
    if not filename.is_file():
        return None
    markup = filename.read_text(encoding="utf-8")
    parser = VisibleText()
    parser.feed(markup)
    main_text = " ".join(parser.parts)
    meta = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)', markup, re.I)
    description = unescape(meta.group(1)) if meta else ""
    heading = re.search(r"<h1\b[^>]*>(.*?)</h1>", markup, re.I | re.S)
    if heading:
        readable = re.sub("<[^>]*>", " ", heading.group(1))
        heading_text = " ".join(unescape(readable).split()).strip(". ")
        if heading_text:
            title = heading_text
    return {
        "title": title, "teaser": description or main_text[:240],
        "body": main_text[:12000], "category": category,
        "date": "", "source": "Positief nieuws", "region": "",
        "url": url, "image": "", "type": kind,
    }


def build_index():
    results = []
    for path in sorted((ROOT / "edities").glob("????-??-??.json"), reverse=True):
        if not DATE.fullmatch(path.stem):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for region in ("nl", "int"):
            for entry in payload.get(region, []):
                if not isinstance(entry, dict):
                    continue
                title = str(entry.get("title") or entry.get("headline") or "").strip()
                slug = str(entry.get("article_slug") or "").strip("/")
                if not title:
                    continue
                local = bool(SLUG.fullmatch(slug)) and (ROOT / "artikelen" / path.stem / slug / "index.html").exists()
                url = f"/artikelen/{path.stem}/{slug}/" if local else str(entry.get("url") or "").strip()
                if not local:
                    try:
                        source_url = urlsplit(url)
                        if source_url.scheme not in ("http", "https") or not source_url.hostname:
                            continue
                    except ValueError:
                        continue
                category = str(entry.get("category") or entry.get("categorie") or "").strip()
                category = CATEGORY_ALIASES.get(category, category)
                imagepath = ROOT / "images" / "artikelen" / path.stem / (slug + ".jpg")
                results.append({
                    "title": title,
                    "teaser": str(entry.get("teaser") or entry.get("summary") or "").strip(),
                    "body": flatten(entry.get("article_body") or entry.get("body") or "")[:12000],
                    "category": category, "date": path.stem,
                    "source": str(entry.get("source") or "").strip(),
                    "region": region, "url": url,
                    "image": f"/images/artikelen/{path.stem}/{slug}.jpg" if local and imagepath.exists() else "",
                    "type": "artikel",
                })

    for url, (title, category) in INFORMATION_PATHS.items():
        record = info_record(url, title, category)
        if record:
            results.append(record)

    for path in sorted((ROOT / "specials").glob("*/index.html")):
        record = info_record("/" + str(path.parent.relative_to(ROOT)).replace("\\", "/") + "/", "Special", "Specials", "special")
        if record:
            results.append(record)

    output = ROOT / "zoeken" / "index.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"items": results}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Zoekindex bijgewerkt: {len(results)} items")


SEARCH_LINK = '<a class="header-search-link" href="/zoeken/" aria-label="Zoeken op Positief nieuws"><svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.7"></circle><path d="m16 16 4.3 4.3"></path></svg><span>Zoeken</span></a>'


def update_headers():
    count = 0
    for path in ROOT.rglob("*.html"):
        if ".git" in path.parts:
            continue
        html = path.read_text(encoding="utf-8")
        head, sep, tail = html.partition("</header>")
        if not sep or 'class="site-header"' not in head or 'href="/zoeken/"' in head:
            continue
        if 'class="app-nav-inner"' not in head:
            continue
        if 'class="header-cta"' in head:
            head = head.replace('<a class="header-cta"', SEARCH_LINK + '\n        <a class="header-cta"', 1)
        else:
            index = head.find("</div>", head.find('class="app-nav-inner"'))
            if index == -1:
                continue
            head = head[:index] + SEARCH_LINK + "\n" + head[index:]
        path.write_text(head + sep + tail, encoding="utf-8")
        count += 1
    print(f"Zoeklink toegevoegd aan {count} navigaties")


def main():
    build_index()
    update_headers()


if __name__ == "__main__":
    main()
