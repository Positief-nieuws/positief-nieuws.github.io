"""Refresh related-reading blocks without changing article bodies or images."""
import json
import re

from build_editions import (
    EDITIONS_DIR, ARTICLES_DIR, get_date, related_article_records,
    select_related_articles, render_related_articles,
)
from related_content import special_records


def update_article_markup(markup, related_markup):
    # Old recommendations might have appeared above the newsletter.
    cleaned = re.sub(
        r'\s*<section\b[^>]*class="article-related"[^>]*>.*?</section>\s*',
        '\n', markup, flags=re.S,
    )
    if not related_markup:
        return cleaned
    anchor = re.search(r'<p class="article-back">', cleaned)
    if not anchor or 'class="article-growth"' not in cleaned:
        raise ValueError("Article page lacks share/newsletter component or back link")
    before = cleaned[:anchor.start()].rstrip()
    if before.rfind('class="article-growth"') > before.rfind('</section>'):
        raise ValueError("Article growth component is not closed")
    return before + '\n\n      ' + related_markup + '\n\n      ' + cleaned[anchor.start():]


def main():
    editions = []
    for path in sorted(EDITIONS_DIR.glob("????-??-??.json"), reverse=True):
        data = json.loads(path.read_text(encoding="utf-8"))
        editions.append((get_date(data, path.stem), data))
    candidates = related_article_records(editions)
    all_candidates = candidates + special_records()
    changed = 0
    for record in candidates:
        path = ARTICLES_DIR / record["date"] / record["slug"] / "index.html"
        if not path.is_file():
            raise FileNotFoundError(f"Published article page missing: {path}")
        original = path.read_text(encoding="utf-8")
        recommendations = select_related_articles(
            record["item"], record["date"], all_candidates, limit=3
        )
        updated = update_article_markup(
            original, render_related_articles(recommendations)
        )
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
        if recommendations:
            pos = []
            for name in ("article-share", "article-newsletter", "article-related"):
                matches = list(re.finditer(
                    r'<(?:section|div)\\b[^>]*class="[^"]*\\b' + re.escape(name) +
                    r'\\b[^"]*"[^>]*>', updated
                ))
                if len(matches) != 1:
                    raise ValueError(f"Expected one {name} block on {path}")
                pos.append(matches[0].start())
            if not pos[0] < pos[1] < pos[2]:
                raise ValueError(f"Incorrect article action order on {path}")
    print(f"Checked {len(candidates)} articles; updated {changed}.")


if __name__ == "__main__":
    main()
