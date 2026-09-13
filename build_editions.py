#!/usr/bin/env python3
import argparse
import html
import json
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SITE_URL = "https://positief-nieuws.nl"
EDITIONS_DIR = Path("edities")
TOPICS_DIR = Path("onderwerpen")
TOPIC_MANIFEST = TOPICS_DIR / "index.json"
NEWS_PATH = Path("nieuws.json")
SITEMAP_PATH = Path("sitemap.xml")

WEEKDAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]


CATEGORY_ORDER = [
    "Cultuur",
    "Economie",
    "Energie & innovatie",
    "Gezondheid",
    "Mens",
    "Natuur & klimaat",
    "Wetenschap",
    "Sport",
]

# Historische categorieën uit eerdere edities worden bij het bouwen samengevoegd
# naar acht vaste hoofdcategorieën. Bekende oude labels blijven ondersteund zodat
# het bestaande archief en oudere links netjes blijven werken.
CATEGORY_ALIASES = {
    "Archeologie & geschiedenis": "Cultuur",
    "Cultuur & erfgoed": "Cultuur",
    "Cultuur & media": "Cultuur",
    "Geschiedenis & mens": "Cultuur",
    "Economie & geld": "Economie",
    "Economie & onderwijs": "Economie",
    "Energie & innovatie": "Energie & innovatie",
    "Gezondheid": "Gezondheid",
    "Gezondheid & basisvoorzieningen": "Gezondheid",
    "Voeding & leefstijl": "Gezondheid",
    "Gewoon leuk": "Mens",
    "Mens & innovatie": "Mens",
    "Mens & samenleving": "Mens",
    "Onderwijs & ontwikkeling": "Mens",
    "Dieren": "Natuur & klimaat",
    "Dieren & natuur": "Natuur & klimaat",
    "Natuur & klimaat": "Natuur & klimaat",
    "Natuur & landbouw": "Natuur & klimaat",
    "Natuur & samenleving": "Natuur & klimaat",
    "Natuur & wetenschap": "Natuur & klimaat",
    "Technologie & innovatie": "Wetenschap",
    "Wetenschap": "Wetenschap",
    "Wetenschap & duurzaamheid": "Wetenschap",
    "Wetenschap & innovatie": "Wetenschap",
    "Wetenschap & ruimtevaart": "Wetenschap",
    "Sport": "Sport",
}

for _category in CATEGORY_ORDER:
    CATEGORY_ALIASES.setdefault(_category, _category)


def esc(value):
    return html.escape(str(value or ""), quote=True)


def fmt_date(value):
    d = datetime.strptime(value, "%Y-%m-%d")
    return f"{WEEKDAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]} {d.year}"


def fmt_date_short(value):
    d = datetime.strptime(value, "%Y-%m-%d")
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def get_date(data, fallback=""):
    return (
        (data.get("meta") or {}).get("edition_date")
        or (data.get("edition") or {}).get("date")
        or fallback
    )


def items(data, key):
    value = data.get(key)
    return value if isinstance(value, list) else []


def reading_time(item):
    value = (
        item.get("reading_time_minutes")
        or item.get("readingTimeMinutes")
        or item.get("reading_time")
        or item.get("readingTime")
        or item.get("leestijd")
    )
    if value is None:
        return ""
    match = re.search(r"\d+", str(value))
    return f"{int(match.group())} min lezen" if match and int(match.group()) > 0 else ""


def slugify_category(value):
    label = str(value or "").strip()
    if not label:
        return ""
    normalized = unicodedata.normalize("NFKD", label)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower().replace("&", " en ")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def category_label(item):
    return str(item.get("category") or item.get("categorie") or "").strip()



def canonical_category(value):
    label = str(value or "").strip()
    if not label:
        return ""
    return CATEGORY_ALIASES.get(label, "")


def story_count(value):
    return f"{value} verhaal" if value == 1 else f"{value} verhalen"


def validate_positive_articles(data, source_name="nieuws.json"):
    errors = []
    legacy_labels = set()

    for section in ("nl", "int"):
        section_items = items(data, section)
        if not section_items:
            errors.append(f"{source_name}: sectie '{section}' ontbreekt of is leeg.")
            continue

        for idx, item in enumerate(section_items, start=1):
            title = str(item.get("title") or item.get("headline") or f"artikel {idx}")
            raw_label = category_label(item)
            if not raw_label:
                errors.append(f"{source_name}: {section}[{idx}] '{title}' heeft geen category.")
                continue

            canonical = canonical_category(raw_label)
            if not canonical:
                allowed = ", ".join(CATEGORY_ORDER)
                errors.append(
                    f"{source_name}: onbekende category {raw_label!r} bij '{title}'. "
                    f"Gebruik een van deze acht categorieën: {allowed}."
                )
                continue

            if raw_label != canonical:
                legacy_labels.add((raw_label, canonical))

    if errors:
        raise ValueError("\n".join(errors))

    for old, new in sorted(legacy_labels):
        print(f"INFO: historische categorie {old!r} wordt samengevoegd onder {new!r}.")


def analytics_html(metadata):
    metadata_json = json.dumps(metadata, ensure_ascii=False)
    return f"""<script>
  window.sa_metadata = {metadata_json};
  (function () {{
    const analyticsScript = document.createElement("script");
    analyticsScript.async = true;
    analyticsScript.setAttribute("data-hostname", "positief-nieuws.nl");
    analyticsScript.src = "https://scripts.simpleanalyticscdn.com/latest.js";
    analyticsScript.addEventListener("load", function () {{
      const autoEventsScript = document.createElement("script");
      autoEventsScript.async = true;
      autoEventsScript.src = "https://scripts.simpleanalyticscdn.com/auto-events.js";
      document.body.appendChild(autoEventsScript);
    }});
    document.body.appendChild(analyticsScript);
  }})();
</script>"""


def header_html(active=""):
    def cls(name):
        return ' class="active"' if active == name else ""
    return f"""<header class="header">
  <a class="brand" href="/" aria-label="Positief nieuws homepage">
    <svg class="sun" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="4.2" fill="currentColor"></circle><path d="M12 1.8V5.1M12 18.9V22.2M22.2 12H18.9M5.1 12H1.8M19.2 4.8L16.8 7.2M7.2 16.8L4.8 19.2M19.2 19.2L16.8 16.8M7.2 7.2L4.8 4.8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"></path></svg>
    <span>Positief nieuws.</span>
  </a>
  <nav>
    <a{cls('today')} href="/">Vandaag</a>
    <a{cls('archive')} href="/edities/">Archief</a>
    <a{cls('topics')} href="/onderwerpen/">Onderwerpen</a>
    <a{cls('about')} href="/over/">Over</a>
    <a class="inbox" href="/#nieuwsbrief">In je inbox</a>
  </nav>
</header>"""


BASE_CSS = r"""
:root{--paper:#f7f5ec;--ink:#151a17;--green:#1f5b45;--green-dark:#173f31;--accent:#d6a13a;--muted:#68716b;--line:rgba(23,63,49,.22);--line2:rgba(23,63,49,.12);--content:748px;--header:1080px}
*{box-sizing:border-box}html{font-size:17px}body{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,Helvetica,sans-serif;line-height:1.52;-webkit-font-smoothing:antialiased}a{color:inherit}
.header{width:min(calc(100% - 48px),var(--header));margin:auto;padding:26px 0 18px;display:flex;align-items:center;justify-content:space-between;gap:24px}.brand{display:inline-flex;align-items:center;gap:12px;font-weight:800;text-decoration:none;letter-spacing:-.02em}.sun{width:28px;height:28px;color:var(--accent)}nav{display:flex;align-items:center;gap:20px}nav a{font-size:.78rem;font-weight:650;text-decoration:none;white-space:nowrap}nav a.active{color:var(--accent)}.inbox{padding:8px 14px;border:1px solid rgba(214,161,58,.45);border-radius:999px;color:var(--accent)}
.shell{width:min(calc(100% - 48px),var(--content));margin:auto}.hero{position:relative;overflow:hidden;padding:64px 0 34px}.hero:after{content:"";position:absolute;right:max(18px,calc((100vw - 1030px)/2));top:38px;width:110px;height:55px;border-radius:110px 110px 0 0;background:rgba(214,161,58,.12);border-bottom:2px solid rgba(214,161,58,.4);pointer-events:none}.date,.kicker{margin:0;color:var(--green);font-size:.68rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}h1,h2,h3,.archive-title{font-family:Georgia,"Times New Roman",serif}h1{margin:7px 0 0;font-size:clamp(2.8rem,6vw,4rem);line-height:.98;letter-spacing:-.05em}h1 b{color:var(--accent)}.lead{max-width:650px;margin:18px 0 0;color:#313934;font-size:1rem}.rule{margin-top:28px;border-top:1px solid var(--line)}
.section{padding:56px 0 62px}.section.alt{background:#f8f3e8}.heading{display:flex;justify-content:space-between;gap:16px;padding-bottom:10px;border-bottom:1px solid var(--green-dark)}.count{font-size:.67rem}.note{margin:13px 0 3px;color:var(--muted);font-size:.86rem}.article{position:relative;padding:22px 46px 22px 0;border-bottom:1px solid var(--line2)}.article h3{margin:0;max-width:660px;font-size:1.18rem;line-height:1.2;letter-spacing:-.025em}.article h3 a{text-decoration:none}.article h3 a:hover{text-decoration:underline;text-underline-offset:3px}.teaser{max-width:650px;margin:8px 0 0;color:#3f4742;font-size:.88rem;line-height:1.48}.meta{display:flex;flex-wrap:wrap;align-items:center;gap:5px;margin-top:12px;color:var(--green);font-size:.64rem;font-weight:700}.meta .sep{color:#919a94}.meta a{color:var(--green);text-decoration:underline;text-decoration-color:rgba(31,91,69,.28);text-underline-offset:2px}.arrow{position:absolute;top:22px;right:0;width:27px;height:27px;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:50%;text-decoration:none;color:var(--green-dark);font-size:.77rem}.archive-list,.topic-list{margin-top:26px;border-top:1px solid var(--green-dark)}.archive-item,.topic-item{display:grid;grid-template-columns:150px minmax(0,1fr) 28px;gap:18px;align-items:center;padding:20px 0;border-bottom:1px solid var(--line2);text-decoration:none}.archive-date,.topic-count{color:var(--green);font-size:.72rem;font-weight:750}.archive-title,.topic-title{font-family:Georgia,"Times New Roman",serif;font-size:1.12rem;line-height:1.2}.archive-arrow,.topic-arrow{text-align:right;color:var(--green)}.small{color:var(--muted);font-size:.82rem;margin-top:25px}.empty{padding:20px 0;color:var(--muted);font-size:.86rem}footer{padding:0 0 34px;text-align:center;color:#8b928e;font-size:.72rem}
@media(max-width:820px){.header,.shell{width:min(calc(100% - 30px),100%)}.header{padding:18px 0 10px;align-items:flex-start}nav{gap:10px}nav a{font-size:.64rem}nav a[href="/over/"]{display:none}.inbox{padding:6px 9px}.hero{padding-top:48px}.hero:after{right:-40px;top:34px}.section{padding:50px 0 54px}.archive-item,.topic-item{grid-template-columns:90px minmax(0,1fr) 20px;gap:10px}.article h3{font-size:1.14rem}.teaser{display:-webkit-box;overflow:hidden;-webkit-box-orient:vertical;-webkit-line-clamp:3}}
"""


def category_meta_html(item):
    raw_label = category_label(item)
    label = canonical_category(raw_label) or raw_label
    slug = slugify_category(label)
    source = str(item.get("source") or item.get("bron") or "").strip()
    rt = reading_time(item)
    parts = []
    if label:
        parts.append(f'<a href="/{esc(slug)}/">{esc(label)}</a>')
    if source:
        parts.append(f"<span>{esc(source)}</span>")
    if rt:
        parts.append(f"<span>{esc(rt)}</span>")
    if not parts:
        return ""
    return '<div class="meta">' + '<span class="sep">·</span>'.join(parts) + "</div>"


def article_html(item, date_value=None, show_date=False):
    title = esc(item.get("title") or item.get("headline") or "")
    teaser = esc(item.get("teaser") or item.get("summary") or item.get("description") or "")
    url = esc(item.get("url") or item.get("link") or "#")
    date_html = ""
    if show_date and date_value:
        date_html = f'<p class="date" style="margin:0 0 7px;text-transform:none;letter-spacing:0;font-weight:700">{esc(fmt_date_short(date_value))}</p>'
    return f"""<article class="article">
      <div>
        {date_html}
        <h3><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
        {f'<p class="teaser">{teaser}</p>' if teaser else ''}
        {category_meta_html(item)}
      </div>
      <a class="arrow" href="{url}" target="_blank" rel="noopener noreferrer" aria-label="Lees {title}">↗</a>
    </article>"""


def description(data, date_text):
    titles = [str(x.get("title") or "").strip() for x in items(data, "nl")[:2]]
    titles = [x for x in titles if x]
    if titles:
        text = f"Positief nieuws van {date_text}: {' en '.join(titles)}, plus meer positieve verhalen en 3 belangrijke onderwerpen."
    else:
        text = f"Positief nieuws van {date_text}: 12 positieve verhalen en 3 belangrijke onderwerpen om bij te blijven."
    if len(text) > 158:
        text = text[:157].rstrip(" ,;:") + "…"
    return text


def render_edition(data, date_value):
    date_text = fmt_date(date_value)
    canonical = f"{SITE_URL}/edities/{date_value}/"
    desc = description(data, date_text)
    title = f"Positief nieuws · {date_text}"

    nl_html = "\n".join(article_html(x) for x in items(data, "nl")[:6])
    int_html = "\n".join(article_html(x) for x in items(data, "int")[:6])
    head_html = "\n".join(_headline_html(x, i) for i, x in enumerate(items(data, "headlines")[:3], 1))

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": desc,
        "url": canonical,
        "datePublished": date_value,
        "dateModified": date_value,
        "isPartOf": {"@type": "WebSite", "name": "Positief nieuws", "url": SITE_URL + "/"}
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html><html lang="nl"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="article"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary"><meta name="theme-color" content="#17382b"><link rel="manifest" href="/manifest.json?v=4"><link rel="apple-touch-icon" href="/icon-192-v3.png"><script type="application/ld+json">{schema}</script><style>{BASE_CSS}.banner{{margin-top:18px;padding:10px 13px;border:1px solid var(--line);color:var(--green-dark);font-size:.75rem}}.briefing-row{{display:grid;grid-template-columns:34px minmax(0,1fr);gap:10px;padding-right:46px}}.num{{padding-top:2px;color:#7f8982;font-size:.66rem;font-weight:700}}.end{{padding:72px 0 64px;text-align:center}}.end h2{{max-width:620px;margin:auto;font-size:clamp(2.2rem,5vw,3.3rem);line-height:1;letter-spacing:-.045em}}.back{{display:inline-flex;margin-top:18px;padding:9px 15px;border:1px solid var(--line);border-radius:999px;text-decoration:none;font-size:.72rem;font-weight:700}}</style></head><body>
{header_html()}
<div class="shell banner">Je leest de editie van {esc(date_text)}. <a href="/">Ga naar de nieuwste editie →</a></div>
<section class="hero"><div class="shell"><p class="date">{esc(date_text)}</p><h1>Dit gebeurt ook<b>.</b></h1><p class="lead">In een paar minuten weet je wat er goed gaat én wat je verder moet weten in deze editie. Zonder eindeloos scrollen.</p><div class="rule"></div></div></section>
<main>
<section class="section alt"><div class="shell"><div class="heading"><p class="kicker">Goed nieuws uit Nederland</p><span class="count">6 verhalen</span></div>{nl_html}</div></section>
<section class="section"><div class="shell"><div class="heading"><p class="kicker">Goed nieuws uit de wereld</p><span class="count">6 verhalen</span></div><p class="note">De artikelen waar we naar verwijzen zijn Engelstalig.</p>{int_html}</div></section>
<section class="section alt"><div class="shell"><div class="heading"><p class="kicker">Wat je verder moet weten</p><span class="count">3 verhalen</span></div><p class="note">Niet per se positief, wel belangrijk.</p>{head_html}</div></section>
<section class="end"><div class="shell"><h2>Dit was het voor deze editie.<br>Je bent weer bij.</h2><p>Geniet van je dag.</p><a class="back" href="/">Lees de nieuwste editie</a></div></section>
</main><footer>Positief nieuws · Dit gebeurt ook.</footer>{analytics_html({'page_type':'edition','edition':date_value})}</body></html>"""


def _headline_html(item, number):
    title = esc(item.get("title") or "")
    teaser = esc(item.get("teaser") or item.get("summary") or "")
    source = esc(item.get("source") or "")
    category = esc(item.get("category") or "")
    url = esc(item.get("url") or "#")
    meta_parts = [p for p in (category, source) if p]
    meta = ""
    if meta_parts:
        meta = '<div class="meta">' + '<span class="sep">·</span>'.join(f"<span>{p}</span>" for p in meta_parts) + "</div>"
    return f"""<article class="article" style="display:grid;grid-template-columns:34px minmax(0,1fr);gap:10px;padding-right:46px"><div class="num">{number:02d}</div><div><h3><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>{f'<p class="teaser">{teaser}</p>' if teaser else ''}{meta}</div><a class="arrow" href="{url}" target="_blank" rel="noopener noreferrer" aria-label="Lees {title}">↗</a></article>"""


def render_archive(entries):
    rows = []
    for entry in entries:
        date_value = entry["date"]
        date_text = fmt_date(date_value)
        short_date = " ".join(date_text.split()[:-1])
        rows.append(f'<a class="archive-item" href="/edities/{date_value}/"><span class="archive-date">{esc(short_date)}</span><span class="archive-title">Positief nieuws · {esc(date_text)}</span><span class="archive-arrow">→</span></a>')
    desc = "Bekijk alle eerdere edities van Positief nieuws: 12 positieve nieuwsverhalen uit Nederland en de wereld, plus 3 belangrijke onderwerpen."
    schema = json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":"Archief van Positief nieuws","url":f"{SITE_URL}/edities/","description":desc,"isPartOf":{"@type":"WebSite","name":"Positief nieuws","url":SITE_URL+"/"}}, ensure_ascii=False)
    return f"""<!DOCTYPE html><html lang="nl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Archief | Eerdere edities van Positief nieuws</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{SITE_URL}/edities/"><meta property="og:title" content="Archief · Positief nieuws"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{SITE_URL}/edities/"><meta name="twitter:card" content="summary"><meta name="theme-color" content="#17382b"><script type="application/ld+json">{schema}</script><style>{BASE_CSS}</style></head><body>{header_html('archive')}<main><section class="hero"><div class="shell"><p class="kicker">Eerdere edities</p><h1>Archief<b>.</b></h1><p class="lead">Lees eerdere edities van Positief nieuws terug.</p><div class="rule"></div></div></section><section class="section"><div class="shell"><div class="archive-list">{''.join(rows)}</div><p class="small">Bekijk ook het overzicht van <a href="/onderwerpen/">onderwerpen</a>.</p></div></section></main><footer>Positief nieuws · Dit gebeurt ook.</footer>{analytics_html({'page_type':'archive'})}</body></html>"""


def collect_topics(edition_records):
    topics = {}
    seen_urls = defaultdict(set)

    for date_value, data in edition_records:
        for lang_key in ("nl", "int"):
            for item in items(data, lang_key):
                raw_label = category_label(item)
                label = canonical_category(raw_label)
                if not label:
                    print(
                        f"WAARSCHUWING: {date_value} / {lang_key}: onbekende categorie "
                        f"{raw_label!r} overgeslagen bij: {item.get('title','(zonder titel)')}"
                    )
                    continue

                slug = slugify_category(label)
                topic = topics.setdefault(
                    slug,
                    {"label": label, "slug": slug, "nl": [], "int": [], "latest": date_value},
                )
                if date_value > topic["latest"]:
                    topic["latest"] = date_value

                url_key = str(item.get("url") or item.get("link") or "").strip() or f"{date_value}:{item.get('title','')}"
                if url_key in seen_urls[(slug, lang_key)]:
                    continue
                seen_urls[(slug, lang_key)].add(url_key)
                topic[lang_key].append({"date": date_value, "item": item})

    for topic in topics.values():
        topic["nl"].sort(key=lambda x: x["date"], reverse=True)
        topic["int"].sort(key=lambda x: x["date"], reverse=True)

    order = {label: idx for idx, label in enumerate(CATEGORY_ORDER)}
    return dict(sorted(topics.items(), key=lambda kv: (order.get(kv[1]["label"], 999), kv[1]["label"].lower())))


def render_topics_index(topics, latest):
    cards = []
    for topic in topics.values():
        total = len(topic["nl"]) + len(topic["int"])
        cards.append(f'<a class="topic-item" href="/{esc(topic["slug"])}/"><span class="topic-count">{story_count(total)}</span><span class="topic-title">{esc(topic["label"])}</span><span class="topic-arrow">→</span></a>')
    desc = "Bekijk positief nieuws per onderwerp. Eerst Nederlandse verhalen, daarna Engelstalige artikelen, steeds met de nieuwste verhalen bovenaan."
    schema = json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":"Onderwerpen · Positief nieuws","description":desc,"url":f"{SITE_URL}/onderwerpen/","isPartOf":{"@type":"WebSite","name":"Positief nieuws","url":SITE_URL+"/"}}, ensure_ascii=False)
    return f"""<!DOCTYPE html><html lang="nl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Onderwerpen | Positief nieuws per thema</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{SITE_URL}/onderwerpen/"><meta property="og:title" content="Onderwerpen · Positief nieuws"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{SITE_URL}/onderwerpen/"><meta name="twitter:card" content="summary"><meta name="theme-color" content="#17382b"><script type="application/ld+json">{schema}</script><style>{BASE_CSS}</style></head><body>{header_html('topics')}<main><section class="hero"><div class="shell"><p class="kicker">Positief nieuws per thema</p><h1>Onderwerpen<b>.</b></h1><p class="lead">Positief nieuws geordend in acht vaste categorieën. Zo vind je makkelijker oudere en nieuwe verhalen over hetzelfde onderwerp.</p><div class="rule"></div></div></section><section class="section"><div class="shell"><div class="topic-list">{''.join(cards) if cards else '<p class="empty">Nog geen onderwerpen beschikbaar.</p>'}</div></div></section></main><footer>Positief nieuws · Dit gebeurt ook.</footer>{analytics_html({'page_type':'topics'})}</body></html>"""


def render_topic_page(topic):
    label = topic["label"]
    slug = topic["slug"]
    canonical = f"{SITE_URL}/{slug}/"
    desc = f"Positief nieuws over {label}. Eerst Nederlandse verhalen, daarna Engelstalige artikelen. Nieuwste verhalen eerst."
    nl_html = "\n".join(article_html(x["item"], x["date"], True) for x in topic["nl"])
    int_html = "\n".join(article_html(x["item"], x["date"], True) for x in topic["int"])
    sections = []
    if topic["nl"]:
        sections.append(f'<section class="section alt"><div class="shell"><div class="heading"><p class="kicker">Nederlandstalig</p><span class="count">{story_count(len(topic["nl"]))}</span></div>{nl_html}</div></section>')
    if topic["int"]:
        sections.append(f'<section class="section"><div class="shell"><div class="heading"><p class="kicker">Engelstalig</p><span class="count">{story_count(len(topic["int"]))}</span></div><p class="note">De bronartikelen in dit blok zijn Engelstalig.</p>{int_html}</div></section>')
    schema = json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":f"{label} · Positief nieuws","description":desc,"url":canonical,"isPartOf":{"@type":"WebSite","name":"Positief nieuws","url":SITE_URL+"/"}}, ensure_ascii=False)
    return f"""<!DOCTYPE html><html lang="nl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{esc(label)} | Positief nieuws</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}"><meta property="og:title" content="{esc(label)} · Positief nieuws"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary"><meta name="theme-color" content="#17382b"><script type="application/ld+json">{schema}</script><style>{BASE_CSS}.crumb{{margin-top:12px;color:var(--muted);font-size:.75rem}}.crumb a{{color:var(--green-dark)}}</style></head><body>{header_html('topics')}<main><section class="hero"><div class="shell"><p class="kicker">Onderwerp</p><h1>{esc(label)}<b>.</b></h1><p class="lead">{esc(desc)}</p><p class="crumb"><a href="/onderwerpen/">← Alle onderwerpen</a></p><div class="rule"></div></div></section>{''.join(sections)}</main><footer>Positief nieuws · Dit gebeurt ook.</footer>{analytics_html({'page_type':'topic','topic':slug})}</body></html>"""


def load_previous_topic_slugs():
    if not TOPIC_MANIFEST.exists():
        return set()
    try:
        data = json.loads(TOPIC_MANIFEST.read_text(encoding="utf-8"))
        return {str(x.get("slug")) for x in data if isinstance(x, dict) and x.get("slug")}
    except Exception:
        return set()


def render_topic_redirect(old_label, new_label):
    target_slug = slugify_category(new_label)
    target = f"/{target_slug}/"
    return (
        '<!DOCTYPE html>\n'
        '<html lang="nl">\n<head>\n'
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '  <meta name="robots" content="noindex,follow">\n'
        f'  <link rel="canonical" href="{SITE_URL}{target}">\n'
        f'  <meta http-equiv="refresh" content="0; url={target}">\n'
        f'  <title>{esc(old_label)} is nu {esc(new_label)} | Positief nieuws</title>\n'
        f'  <script>window.location.replace({json.dumps(target)});</script>\n'
        '</head>\n<body>\n'
        f'  <p>Dit onderwerp valt nu onder <a href="{target}">{esc(new_label)}</a>.</p>\n'
        '</body>\n</html>\n'
    )


def write_legacy_topic_redirects():
    canonical_slugs = {slugify_category(label) for label in CATEGORY_ORDER}
    redirects = {}
    for old_label, new_label in CATEGORY_ALIASES.items():
        old_slug = slugify_category(old_label)
        new_slug = slugify_category(new_label)
        if old_slug and old_slug != new_slug and old_slug not in canonical_slugs:
            redirects[old_slug] = (old_label, new_label)

    for old_slug, (old_label, new_label) in sorted(redirects.items()):
        page_dir = Path(old_slug)
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(render_topic_redirect(old_label, new_label), encoding="utf-8")
        print(f"Redirect gebouwd: /{old_slug}/ → /{slugify_category(new_label)}/")
    return set(redirects)


def write_topic_pages(topics):
    TOPICS_DIR.mkdir(exist_ok=True)
    previous = load_previous_topic_slugs()
    current = set(topics)
    redirect_slugs = {
        slugify_category(old_label)
        for old_label, new_label in CATEGORY_ALIASES.items()
        if slugify_category(old_label) != slugify_category(new_label)
    }

    for stale_slug in sorted(previous - current):
        if stale_slug in redirect_slugs:
            continue
        stale_dir = Path(stale_slug)
        if stale_dir.is_dir() and (stale_dir / "index.html").exists():
            shutil.rmtree(stale_dir)
            print(f"Oude onderwerp-pagina verwijderd: /{stale_slug}/")

    manifest = []
    for slug, topic in topics.items():
        page_dir = Path(slug)
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(render_topic_page(topic), encoding="utf-8")
        manifest.append({
            "label": topic["label"],
            "slug": slug,
            "url": f"/{slug}/",
            "nl_count": len(topic["nl"]),
            "int_count": len(topic["int"]),
            "latest": topic["latest"],
        })
        print(f"Gebouwd: {page_dir / 'index.html'}")

    write_legacy_topic_redirects()

    TOPIC_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest = max((t["latest"] for t in topics.values()), default=datetime.now().strftime("%Y-%m-%d"))
    (TOPICS_DIR / "index.html").write_text(render_topics_index(topics, latest), encoding="utf-8")
    print(f"Gebouwd: {TOPICS_DIR / 'index.html'}")


def build_site():
    EDITIONS_DIR.mkdir(exist_ok=True)
    if NEWS_PATH.exists():
        current = json.loads(NEWS_PATH.read_text(encoding="utf-8"))
        validate_positive_articles(current, "nieuws.json")

    entries = []
    edition_records = []
    dates = []
    for json_path in sorted(EDITIONS_DIR.glob("????-??-??.json"), reverse=True):
        data = json.loads(json_path.read_text(encoding="utf-8"))
        date_value = get_date(data, json_path.stem)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
            print(f"WAARSCHUWING: overslaan wegens ongeldige datum: {json_path}")
            continue
        datetime.strptime(date_value, "%Y-%m-%d")
        page_dir = EDITIONS_DIR / date_value
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(render_edition(data, date_value), encoding="utf-8")
        entries.append({"date": date_value, "file": json_path.name, "url": f"/edities/{date_value}/"})
        edition_records.append((date_value, data))
        dates.append(date_value)
        print(f"Gebouwd: {page_dir / 'index.html'}")

    (EDITIONS_DIR / "index.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (EDITIONS_DIR / "index.html").write_text(render_archive(entries), encoding="utf-8")
    print(f"Gebouwd: {EDITIONS_DIR / 'index.html'}")

    topics = collect_topics(edition_records)
    write_topic_pages(topics)

    latest = max(dates) if dates else datetime.now().strftime("%Y-%m-%d")
    sitemap_urls = [
        (f"{SITE_URL}/", latest),
        (f"{SITE_URL}/over/", None),
        (f"{SITE_URL}/edities/", latest),
        (f"{SITE_URL}/onderwerpen/", latest),
    ]
    for date_value in sorted(dates, reverse=True):
        sitemap_urls.append((f"{SITE_URL}/edities/{date_value}/", date_value))
    for topic in topics.values():
        sitemap_urls.append((f"{SITE_URL}/{topic['slug']}/", topic["latest"]))

    sitemap_parts = []
    for loc, lastmod in sitemap_urls:
        lm = f"\n    <lastmod>{lastmod}</lastmod>" if lastmod else ""
        sitemap_parts.append(f"  <url>\n    <loc>{loc}</loc>{lm}\n  </url>")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(sitemap_parts) + "\n</urlset>\n"
    SITEMAP_PATH.write_text(sitemap, encoding="utf-8")
    print(f"Sitemap bijgewerkt met {len(sitemap_urls)} URL(s), waarvan {len(topics)} onderwerp-pagina's.")


def validate_current():
    if not NEWS_PATH.exists():
        raise FileNotFoundError("nieuws.json niet gevonden.")
    data = json.loads(NEWS_PATH.read_text(encoding="utf-8"))
    validate_positive_articles(data, "nieuws.json")
    print("nieuws.json is geldig: alle positieve artikelen vallen onder een van de acht vaste categorieën.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-current", action="store_true", help="Valideer alleen nieuws.json en stop daarna.")
    args = parser.parse_args()
    try:
        if args.validate_current:
            validate_current()
        else:
            build_site()
    except Exception as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
