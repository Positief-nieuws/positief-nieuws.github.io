#!/usr/bin/env python3
import html
import json
import re
from datetime import datetime
from pathlib import Path

SITE_URL = "https://positief-nieuws.nl"
EDITIONS_DIR = Path("edities")
SITEMAP_PATH = Path("sitemap.xml")

WEEKDAYS = ["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
MONTHS = ["januari","februari","maart","april","mei","juni","juli","augustus","september","oktober","november","december"]

def esc(value):
    return html.escape(str(value or ""), quote=True)

def fmt_date(value):
    d = datetime.strptime(value, "%Y-%m-%d")
    return f"{WEEKDAYS[d.weekday()]} {d.day} {MONTHS[d.month-1]} {d.year}"

def get_date(data, fallback):
    return ((data.get("meta") or {}).get("edition_date")
            or (data.get("edition") or {}).get("date")
            or fallback)

def items(data, key):
    value = data.get(key)
    return value if isinstance(value, list) else []

def reading_time(item):
    value = (item.get("reading_time_minutes")
             or item.get("readingTimeMinutes")
             or item.get("reading_time")
             or item.get("readingTime")
             or item.get("leestijd"))
    if value is None:
        return ""
    match = re.search(r"\d+", str(value))
    return f"{int(match.group())} min lezen" if match and int(match.group()) > 0 else ""

def article(item, number=None):
    title = esc(item.get("title") or item.get("headline") or "")
    teaser = esc(item.get("teaser") or item.get("summary") or item.get("description") or "")
    source = esc(item.get("source") or item.get("bron") or "")
    category = esc(item.get("category") or item.get("categorie") or "")
    url = esc(item.get("url") or item.get("link") or "#")
    rt = esc(reading_time(item))
    meta_parts = [p for p in (category, source, rt) if p]
    meta = ""
    if meta_parts:
        meta = '<div class="meta">' + '<span class="sep">·</span>'.join(
            f"<span>{p}</span>" for p in meta_parts
        ) + "</div>"
    number_html = f'<div class="num">{number:02d}</div>' if number is not None else ""
    extra_class = " briefing" if number is not None else ""
    return f"""<article class="article{extra_class}">
      {number_html}
      <div>
        <h3><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
        {f'<p class="teaser">{teaser}</p>' if teaser else ''}
        {meta}
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

def render(data, date_value):
    date_text = fmt_date(date_value)
    canonical = f"{SITE_URL}/edities/{date_value}/"
    desc = description(data, date_text)
    title = f"Positief nieuws · {date_text}"

    nl_html = "\n".join(article(x) for x in items(data, "nl")[:6])
    int_html = "\n".join(article(x) for x in items(data, "int")[:6])
    head_html = "\n".join(article(x, i) for i, x in enumerate(items(data, "headlines")[:3], 1))

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": desc,
        "url": canonical,
        "datePublished": date_value,
        "dateModified": date_value,
        "isPartOf": {
            "@type": "WebSite",
            "name": "Positief nieuws",
            "url": SITE_URL + "/"
        }
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta name="twitter:card" content="summary">
  <meta name="theme-color" content="#17382b">
  <link rel="manifest" href="/manifest.json?v=4">
  <link rel="apple-touch-icon" href="/icon-192-v3.png">
  <script type="application/ld+json">{schema}</script>
  <style>
    :root{{--paper:#f7f5ec;--ink:#151a17;--green:#1f5b45;--green-dark:#173f31;--accent:#d6a13a;--muted:#68716b;--line:rgba(23,63,49,.22);--line2:rgba(23,63,49,.12);--content:748px;--header:1080px}}
    *{{box-sizing:border-box}} html{{font-size:17px}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,Helvetica,sans-serif;line-height:1.52;-webkit-font-smoothing:antialiased}}
    a{{color:inherit}} .header{{width:min(calc(100% - 48px),var(--header));margin:auto;padding:26px 0 18px;display:flex;align-items:center;justify-content:space-between;gap:24px}}
    .brand{{display:inline-flex;align-items:center;gap:12px;font-weight:800;text-decoration:none;letter-spacing:-.02em}} .sun{{width:28px;height:28px;color:var(--accent)}}
    nav{{display:flex;align-items:center;gap:22px}} nav a{{font-size:.8rem;font-weight:650;text-decoration:none}} .inbox{{padding:8px 14px;border:1px solid rgba(214,161,58,.45);border-radius:999px;color:var(--accent)}}
    .shell{{width:min(calc(100% - 48px),var(--content));margin:auto}} .banner{{margin-top:18px;padding:10px 13px;border:1px solid var(--line);color:var(--green-dark);font-size:.75rem}}
    .hero{{padding:64px 0 34px}} .date{{margin:0 0 5px;color:var(--green-dark);font-size:.77rem}} h1,h3,.end h2{{font-family:Georgia,"Times New Roman",serif}}
    h1{{margin:0;font-size:clamp(2.8rem,6vw,4rem);line-height:.98;letter-spacing:-.05em}} h1 b{{color:var(--accent)}} .copy{{max-width:650px;margin:18px 0 0;color:#2d342f}}
    .hero-meta{{display:flex;justify-content:space-between;gap:20px;margin-top:21px;padding-top:14px;border-top:1px solid var(--line);color:var(--muted);font-size:.69rem}}
    .section{{padding:62px 0 60px}} .nl{{background:#f8f3e8}} .world{{background:#eef3ed}} .briefing-section{{background:#f3efe7}}
    .heading{{display:flex;justify-content:space-between;gap:16px;padding-bottom:10px;border-bottom:1px solid var(--green-dark)}} .kicker{{margin:0;color:var(--green);font-size:.67rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}} .count{{font-size:.67rem}} .note{{margin:13px 0 3px;color:var(--muted);font-size:.86rem}}
    .article{{position:relative;padding:22px 46px 22px 0;border-bottom:1px solid var(--line2)}} .article h3{{margin:0;max-width:660px;font-size:1.18rem;line-height:1.2;letter-spacing:-.025em}} .article h3 a{{text-decoration:none}} .article h3 a:hover{{text-decoration:underline;text-underline-offset:3px}}
    .teaser{{max-width:650px;margin:8px 0 0;color:#3f4742;font-size:.88rem;line-height:1.48}} .meta{{display:flex;flex-wrap:wrap;gap:5px;margin-top:12px;color:var(--green);font-size:.64rem;font-weight:700}} .sep{{color:#919a94}}
    .arrow{{position:absolute;top:22px;right:0;width:27px;height:27px;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:50%;text-decoration:none;color:var(--green-dark);font-size:.77rem}}
    .briefing{{display:grid;grid-template-columns:34px minmax(0,1fr);gap:10px;padding-right:46px}} .num{{padding-top:2px;color:#7f8982;font-size:.66rem;font-weight:700}} .briefing .arrow{{right:0}}
    .end{{padding:76px 0 68px;text-align:center}} .end h2{{max-width:620px;margin:auto;font-size:clamp(2.2rem,5vw,3.3rem);line-height:1;letter-spacing:-.045em}} .end p{{color:var(--muted)}} .back{{display:inline-flex;margin-top:18px;padding:9px 15px;border:1px solid var(--line);border-radius:999px;text-decoration:none;font-size:.72rem;font-weight:700}}
    footer{{padding:0 0 34px;text-align:center;color:#8b928e;font-size:.72rem}}
    @media(max-width:760px){{.header,.shell{{width:min(calc(100% - 30px),100%)}}.header{{padding:18px 0 10px;align-items:flex-start}}nav{{gap:10px}}nav a{{font-size:.65rem}}.hero{{padding-top:48px}}.hero-meta{{flex-direction:column;gap:7px}}.section{{padding:54px 0 52px}}.article h3{{font-size:1.14rem}}.teaser{{display:-webkit-box;overflow:hidden;-webkit-box-orient:vertical;-webkit-line-clamp:3}}}}
  </style>
</head>
<body>
<header class="header">
  <a class="brand" href="/" aria-label="Positief nieuws homepage">
    <svg class="sun" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="4.2" fill="currentColor"></circle><path d="M12 1.8V5.1M12 18.9V22.2M22.2 12H18.9M5.1 12H1.8M19.2 4.8L16.8 7.2M7.2 16.8L4.8 19.2M19.2 19.2L16.8 16.8M7.2 7.2L4.8 4.8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"></path></svg>
    <span>Positief nieuws.</span>
  </a>
  <nav><a href="/">Vandaag</a><a href="/#archief">Archief</a><a href="/#over">Over</a><a class="inbox" href="/#nieuwsbrief">In je inbox</a></nav>
</header>
<div class="shell banner">Je leest de editie van {esc(date_text)}. <a href="/">Ga naar de nieuwste editie →</a></div>
<section class="hero"><div class="shell">
  <p class="date">{esc(date_text.capitalize())}</p>
  <h1>Dit gebeurt ook<b>.</b></h1>
  <p class="copy">In een paar minuten weet je wat er goed gaat én wat je verder moet weten in deze editie. Zonder eindeloos scrollen.</p>
  <div class="hero-meta"><span>Positief nieuws · archiefeditie</span><span>15 verhalen · ongeveer 6 minuten</span></div>
</div></section>
<main>
<section class="section nl"><div class="shell"><div class="heading"><p class="kicker">Goed nieuws uit Nederland</p><span class="count">6 verhalen</span></div>{nl_html}</div></section>
<section class="section world"><div class="shell"><div class="heading"><p class="kicker">Goed nieuws uit de wereld</p><span class="count">6 verhalen</span></div><p class="note">Zes positieve ontwikkelingen van buiten Nederland. De artikelen waar we naar verwijzen zijn Engelstalig.</p>{int_html}</div></section>
<section class="section briefing-section"><div class="shell"><div class="heading"><p class="kicker">Wat je verder moet weten</p><span class="count">3 verhalen</span></div><p class="note">Niet per se positief, wel belangrijk. Drie onderwerpen die op deze editiedatum belangrijk waren om te weten.</p>{head_html}</div></section>
<section class="end"><div class="shell"><h2>Dit was het voor deze editie.<br>Je bent weer bij.</h2><p>Geniet van je dag.</p><a class="back" href="/">Lees de nieuwste editie</a></div></section>
</main>
<footer>Positief nieuws · Dit gebeurt ook.</footer>
</body></html>"""

def main():
    EDITIONS_DIR.mkdir(exist_ok=True)
    entries = []
    dates = []

    for json_path in sorted(EDITIONS_DIR.glob("????-??-??.json"), reverse=True):
        data = json.loads(json_path.read_text(encoding="utf-8"))
        date_value = get_date(data, json_path.stem)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
            print(f"Overslaan: {json_path}")
            continue
        datetime.strptime(date_value, "%Y-%m-%d")
        page_dir = EDITIONS_DIR / date_value
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(render(data, date_value), encoding="utf-8")
        entries.append({"date": date_value, "file": json_path.name, "url": f"/edities/{date_value}/"})
        dates.append(date_value)
        print(f"Gebouwd: {page_dir / 'index.html'}")

    (EDITIONS_DIR / "index.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    latest = max(dates) if dates else datetime.now().strftime("%Y-%m-%d")
    sitemap_urls = [
        f"  <url>\n    <loc>{SITE_URL}/</loc>\n    <lastmod>{latest}</lastmod>\n  </url>"
    ]
    for date_value in sorted(dates, reverse=True):
        sitemap_urls.append(
            f"  <url>\n    <loc>{SITE_URL}/edities/{date_value}/</loc>\n    <lastmod>{date_value}</lastmod>\n  </url>"
        )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(sitemap_urls)
        + "\n</urlset>\n"
    )
    SITEMAP_PATH.write_text(sitemap, encoding="utf-8")
    print(f"Sitemap bijgewerkt met {len(sitemap_urls)} URL(s).")

if __name__ == "__main__":
    main()
