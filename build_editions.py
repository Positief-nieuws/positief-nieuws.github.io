#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import shutil
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SITE_URL = "https://positief-nieuws.nl"
EDITIONS_DIR = Path("edities")
TOPICS_DIR = Path("onderwerpen")
TOPIC_MANIFEST = TOPICS_DIR / "index.json"
ARTICLES_DIR = Path("artikelen")
ARTICLE_IMAGES_DIR = Path("images") / "artikelen"
PIXABAY_CACHE_PATH = Path("data") / "pixabay-images.json"
PIXABAY_API_URL = "https://pixabay.com/api/"
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


TOPIC_SEO = {
    "Cultuur": {
        "title": "Positief nieuws over cultuur | Positief nieuws",
        "h1": "Positief nieuws over cultuur",
        "description": "Lees positief nieuws over cultuur, erfgoed, media en creatieve ontwikkelingen uit Nederland en de wereld. De nieuwste verhalen staan bovenaan.",
        "lead": "Goed nieuws over cultuur, erfgoed, media en creatieve ontwikkelingen.",
        "intro": [
            "Op deze pagina vind je positief nieuws over cultuur in brede zin: van kunst, erfgoed en media tot boeken, muziek, musea en andere creatieve ontwikkelingen. We selecteren verhalen waarin iets aantoonbaar vooruitgaat, toegankelijker wordt, behouden blijft of nieuwe mensen bereikt.",
            "Je vindt hier zowel Nederlandse als internationale verhalen, steeds met de nieuwste ontwikkelingen bovenaan. Geen losse entertainmentroddels, maar nieuws met inhoud: initiatieven, onderzoek, herstel, vernieuwing en andere ontwikkelingen die laten zien wat er in cultuur óók goed gaat."
        ],
    },
    "Economie": {
        "title": "Positief nieuws over economie | Positief nieuws",
        "h1": "Positief nieuws over economie",
        "description": "Lees positief economisch nieuws over werk, ondernemerschap, inkomen, bedrijven en slimme oplossingen. Nederlandse en internationale verhalen.",
        "lead": "Positieve ontwikkelingen rond economie, werk, ondernemerschap en inkomen.",
        "intro": [
            "Hier verzamelen we positief nieuws over economie: ontwikkelingen rond werk, ondernemerschap, inkomen, bedrijven en economische kansen. Het gaat niet om optimisme om het optimisme, maar om concrete veranderingen die mensen, organisaties of de samenleving verder kunnen helpen.",
            "Denk aan nieuwe bedrijvigheid, betere toegang tot werk, slimme economische oplossingen of ontwikkelingen die zorgen voor meer zekerheid en kansen. Nederlandse verhalen staan bovenaan, gevolgd door relevant positief economisch nieuws uit de rest van de wereld."
        ],
    },
    "Energie & innovatie": {
        "title": "Positief nieuws over energie en innovatie | Positief nieuws",
        "h1": "Positief nieuws over energie en innovatie",
        "description": "Lees positief nieuws over energie, technologie en innovatie: slimme oplossingen, verduurzaming en toepassingen die aantoonbaar vooruitgang brengen.",
        "lead": "Slimme oplossingen en vernieuwing op het gebied van energie en technologie.",
        "intro": [
            "Op deze pagina vind je positief nieuws over energie en innovatie. Van nieuwe technologie en duurzame energie tot praktische toepassingen die problemen slimmer, schoner of efficiënter helpen oplossen. We kijken vooral naar ontwikkelingen die verder gaan dan een mooi idee en waarbij daadwerkelijk vooruitgang zichtbaar is.",
            "Dat kan gaan om energieopslag, duurzame bouw, netwerken, mobiliteit, nieuwe materialen of andere technologische oplossingen. Eerst vind je de nieuwste Nederlandse verhalen, daarna relevante internationale ontwikkelingen."
        ],
    },
    "Gezondheid": {
        "title": "Positief nieuws over gezondheid | Positief nieuws",
        "h1": "Gezondheid",
        "description": "Positief nieuws over gezondheid: ontwikkelingen in preventie, vroegere signalering, gerichtere behandeling en betere toegang tot zorg.",
        "lead": "Van preventie en vroegere signalering tot gerichtere behandeling en betere toegang tot zorg. Hier verzamelen we de gezondheidsontwikkelingen uit onze edities, én kijken we af en toe wat er over meerdere verhalen heen opvalt.",
        "intro": [
            "Positief nieuws over gezondheid gaat niet alleen over nieuwe medicijnen. We volgen ook preventie, vroegere signalering, herstel, toegankelijkheid en andere ontwikkelingen die de gezondheid of kwaliteit van leven kunnen verbeteren.",
            "De verhalen komen uit Nederlandse en internationale bronnen. Bovenaan duiden we alleen patronen die in meerdere recente verhalen terugkomen; daaronder blijft het volledige gezondheidsarchief beschikbaar."
        ],
    },
    "Mens": {
        "title": "Positief nieuws over mensen en samenleving | Positief nieuws",
        "h1": "Positief nieuws over mensen en samenleving",
        "description": "Lees positief nieuws over mensen en samenleving: initiatieven, onderwijs, samenwerking en oplossingen die het dagelijks leven beter maken.",
        "lead": "Verhalen over mensen, samenwerking en maatschappelijke vooruitgang.",
        "intro": [
            "Hier vind je positief nieuws over mensen en samenleving. Verhalen over samenwerking, onderwijs, kansen, buurten, vrijwilligers, inclusie en andere initiatieven die het dagelijks leven concreet beter kunnen maken.",
            "We zoeken geen losse feelgoodmomenten, maar ontwikkelingen met betekenis: mensen die een probleem oplossen, organisaties die iets toegankelijker maken of initiatieven die aantoonbaar verschil maken. Nederlandse verhalen staan bovenaan, gevolgd door inspirerende en relevante ontwikkelingen uit de rest van de wereld."
        ],
    },
    "Natuur & klimaat": {
        "title": "Positief nieuws over natuur en klimaat | Positief nieuws",
        "h1": "Positief nieuws over natuur en klimaat",
        "description": "Lees positief nieuws over natuur en klimaat: natuurherstel, biodiversiteit, bescherming en oplossingen voor een duurzamere leefomgeving.",
        "lead": "Vooruitgang rond natuur, biodiversiteit, klimaat en leefomgeving.",
        "intro": [
            "Op deze pagina verzamelen we positief nieuws over natuur en klimaat. Denk aan natuurherstel, biodiversiteit, bescherming van dieren en ecosystemen, schonere leefomgevingen en oplossingen die helpen om schade te beperken of herstel mogelijk te maken.",
            "We kiezen verhalen waarin resultaten, nieuwe inzichten of concrete maatregelen centraal staan. Niet iedere groene belofte is automatisch goed nieuws: de ontwikkeling moet inhoudelijk iets toevoegen. Je vindt eerst de nieuwste Nederlandse verhalen en daarna positieve ontwikkelingen uit de rest van de wereld."
        ],
    },
    "Wetenschap": {
        "title": "Positief nieuws over wetenschap | Positief nieuws",
        "h1": "Positief nieuws over wetenschap",
        "description": "Lees positief wetenschapsnieuws over onderzoek, ontdekkingen en nieuwe inzichten uit Nederland en de wereld. De nieuwste verhalen eerst.",
        "lead": "Nieuwe ontdekkingen, onderzoek en inzichten die ons verder helpen.",
        "intro": [
            "Hier vind je positief nieuws uit de wetenschap: onderzoek, ontdekkingen en nieuwe inzichten die ons begrip vergroten of nieuwe mogelijkheden openen. Dat kan gaan over ruimtevaart, technologie, biologie, gezondheid, archeologie en veel meer.",
            "We letten op wat een onderzoek daadwerkelijk laat zien en vermijden grotere claims dan de bron ondersteunt. Zo blijft positief wetenschapsnieuws interessant én betrouwbaar. De nieuwste Nederlandse verhalen staan bovenaan, gevolgd door relevante internationale onderzoeken en ontdekkingen."
        ],
    },
    "Sport": {
        "title": "Positief nieuws over sport | Positief nieuws",
        "h1": "Positief nieuws over sport",
        "description": "Lees positief sportnieuws over ontwikkeling, toegankelijkheid, gezondheid en bijzondere prestaties met betekenis buiten alleen de uitslag.",
        "lead": "Sportnieuws over vooruitgang, ontwikkeling en prestaties met bredere betekenis.",
        "intro": [
            "Op deze pagina vind je positief nieuws over sport. Niet iedere overwinning of uitslag komt hier terecht: we zoeken vooral verhalen waarin sport zich ontwikkelt, toegankelijker wordt of op een andere manier blijvende betekenis heeft.",
            "Denk aan groei van vrouwen- of gehandicaptensport, betere begeleiding en gezondheid van sporters, maatschappelijke initiatieven of uitzonderlijke prestaties met een verhaal erachter. Nederlandse sportverhalen staan bovenaan, gevolgd door relevante positieve ontwikkelingen uit de rest van de wereld."
        ],
    },
}



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
  window.sa_event =
    window.sa_event ||
    function () {{
      const args = [].slice.call(arguments);
      window.sa_event.q
        ? window.sa_event.q.push(args)
        : window.sa_event.q = [args];
    }};

  window.sa_metadata = Object.assign({{}}, window.sa_metadata, {metadata_json});

  document.addEventListener("click", function (event) {{
    const articleLink = event.target.closest("[data-article-click]");
    if (articleLink) {{
      window.sa_event(
        "article_click",
        {{
          title: articleLink.dataset.articleTitle || "Zonder titel",
          source: articleLink.dataset.articleSource || "Onbekend",
          category: articleLink.dataset.articleCategory || "Onbekend",
          section: articleLink.dataset.articleSection || "onbekend",
          target_edition: articleLink.dataset.articleEdition || "none",
          url: articleLink.href || "onbekend"
        }}
      );
    }}

    const sourceLink = event.target.closest("[data-source-click]");
    if (sourceLink) {{
      window.sa_event(
        "source_click",
        {{
          title: sourceLink.dataset.articleTitle || window.sa_metadata?.article_title || "Zonder titel",
          source: sourceLink.dataset.articleSource || window.sa_metadata?.source || "Onbekend",
          category: sourceLink.dataset.articleCategory || window.sa_metadata?.category || "Onbekend",
          target_edition: sourceLink.dataset.articleEdition || "none",
          url: sourceLink.href || "onbekend"
        }}
      );
    }}
  }});

  (function () {{
    const analyticsScript = document.createElement("script");
    analyticsScript.async = true;
    analyticsScript.setAttribute("data-hostname", "positief-nieuws.nl");
    analyticsScript.setAttribute("data-metadata-collector", "pnAnalyticsMetadata");
    analyticsScript.src = "https://scripts.simpleanalyticscdn.com/latest.js";
    analyticsScript.addEventListener("load", function () {{
      const autoEventsScript = document.createElement("script");
      autoEventsScript.async = true;
      autoEventsScript.setAttribute("data-full-urls", "true");
      autoEventsScript.src = "https://scripts.simpleanalyticscdn.com/auto-events.js";
      document.body.appendChild(autoEventsScript);
    }});
    document.body.appendChild(analyticsScript);
  }})();
</script>"""


def header_html(active=""):
    def active_class(name):
        return " is-active" if active == name else ""

    return f"""<header class="site-header">
  <div class="header-shell header-row">
    <a class="brand" href="/" aria-label="Positief nieuws homepage">
      <img class="brand-sun" src="/sun-icon-512.png" width="32" height="32" alt="" aria-hidden="true">
      <span>Positief nieuws</span>
    </a>

    <button class="mobile-menu-toggle" type="button" aria-label="Menu openen" aria-expanded="false" aria-controls="mobile-navigation">
      <span class="menu-icon" aria-hidden="true">
        <span class="menu-line"></span>
        <span class="menu-line"></span>
        <span class="menu-line"></span>
      </span>
      <span class="menu-label">Menu</span>
    </button>

    <nav class="app-nav" id="mobile-navigation" aria-label="Hoofdnavigatie">
      <div class="app-nav-inner">
        <a class="nav-link{active_class('today')}" href="/">Vandaag</a>
        <a class="nav-link{active_class('archive')}" href="/edities/">Archief</a>
        <a class="nav-link{active_class('topics')}" href="/onderwerpen/">Onderwerpen</a>
        <a class="nav-link{active_class('about')}" href="/over/">Over</a>
        <a href="/contact/" onclick="if(window.sa_event)window.sa_event('contact_click')">Contact</a>
        <a class="header-cta" href="/#nieuwsbrief"><svg class="header-cta-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3.5 6.5h17a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-9a1 1 0 0 1 1-1Z" stroke="currentColor" stroke-width="1.7"></path><path d="m4.5 8 7.5 6 7.5-6" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"></path></svg><span>In je inbox</span></a>
      </div>
    </nav>
  </div>
</header>
<script>
  (function () {{
    const header = document.querySelector(".site-header");
    const toggle = document.querySelector(".mobile-menu-toggle");
    const nav = document.querySelector(".app-nav");
    if (!header || !toggle || !nav) return;

    function setMenu(open) {{
      header.classList.toggle("menu-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Menu sluiten" : "Menu openen");
    }}

    toggle.addEventListener("click", function () {{
      setMenu(!header.classList.contains("menu-open"));
    }});

    nav.addEventListener("click", function (event) {{
      if (event.target.closest("a")) setMenu(false);
    }});

    document.addEventListener("click", function (event) {{
      if (header.classList.contains("menu-open") && !header.contains(event.target)) setMenu(false);
    }});

    document.addEventListener("keydown", function (event) {{
      if (event.key === "Escape") {{
        setMenu(false);
        toggle.focus();
      }}
    }});

    window.addEventListener("resize", function () {{
      if (window.innerWidth > 760) setMenu(false);
    }});
  }})();
</script>"""

BASE_CSS = r"""
:root{--paper:#f7f5ec;--ink:#151a17;--green:#1f5b45;--green-dark:#173f31;--accent:#d6a13a;--muted:#68716b;--line:rgba(23,63,49,.22);--line2:rgba(23,63,49,.12);--content:748px;--header:1080px}
*{box-sizing:border-box}html{font-size:17px}body{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,Helvetica,sans-serif;line-height:1.52;-webkit-font-smoothing:antialiased}a{color:inherit}
.site-header{padding:26px 0 18px}.header-shell{width:min(calc(100% - 48px),var(--header));margin:0 auto}.header-row{display:flex;align-items:center;justify-content:space-between;gap:24px}
.brand{display:inline-flex;align-items:center;gap:12px;color:var(--ink);font-family:Arial,Helvetica,sans-serif;font-size:1.02rem;font-weight:800;text-decoration:none;letter-spacing:-.02em}.brand span{white-space:nowrap}.brand-sun{width:28px;height:28px;color:var(--accent);flex:0 0 auto}
.mobile-menu-toggle{display:none;min-height:42px;padding:0 13px;border:1px solid rgba(23,63,49,.16);border-radius:999px;background:rgba(255,255,255,.3);color:var(--green-dark);align-items:center;justify-content:center;gap:8px;cursor:pointer;-webkit-tap-highlight-color:transparent}.menu-icon{display:inline-flex;width:17px;flex-direction:column;gap:4px}.menu-line{display:block;width:17px;height:1.5px;border-radius:999px;background:currentColor;transition:transform 160ms ease,opacity 160ms ease;transform-origin:center}.menu-label{font-size:.76rem;font-weight:750;line-height:1}.site-header.menu-open .menu-line:nth-child(1){transform:translateY(5.5px) rotate(45deg)}.site-header.menu-open .menu-line:nth-child(2){opacity:0}.site-header.menu-open .menu-line:nth-child(3){transform:translateY(-5.5px) rotate(-45deg)}
.app-nav-inner{display:flex;align-items:center;gap:24px}.app-nav a{color:var(--ink);font-family:Arial,Helvetica,sans-serif;font-size:.86rem;font-weight:600;text-decoration:none;white-space:nowrap;transition:color 120ms ease,border-color 120ms ease,background-color 120ms ease}.app-nav a:hover,.app-nav a.is-active{color:var(--accent)}.header-cta{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:40px;padding:0 16px;border:1px solid rgba(214,161,58,.45);border-radius:999px;background:rgba(255,255,255,.25);color:var(--accent)!important;box-shadow:inset 0 0 0 1px rgba(214,161,58,.08)}.header-cta-icon{width:16px;height:16px;flex:0 0 auto}
.shell{width:min(calc(100% - 48px),var(--content));margin:auto}.hero{position:relative;overflow:hidden;padding:64px 0 34px}.hero:after{content:"";position:absolute;right:max(18px,calc((100vw - 1030px)/2));top:38px;width:110px;height:55px;border-radius:110px 110px 0 0;background:rgba(214,161,58,.12);border-bottom:2px solid rgba(214,161,58,.4);pointer-events:none}.date,.kicker{margin:0;color:var(--green);font-size:.68rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}h1,h2,h3,.archive-title{font-family:Georgia,"Times New Roman",serif}h1{margin:7px 0 0;font-size:clamp(2.8rem,6vw,4rem);line-height:.98;letter-spacing:-.05em}h1 b{color:var(--accent)}.lead{max-width:650px;margin:18px 0 0;color:#313934;font-size:1rem}.rule{margin-top:28px;border-top:1px solid var(--line)}
.section{padding:56px 0 62px}.section.alt{background:#f8f3e8}.heading{display:flex;justify-content:space-between;gap:16px;padding-bottom:10px;border-bottom:1px solid var(--green-dark)}.count{font-size:.67rem}.note{margin:13px 0 3px;color:var(--muted);font-size:.86rem}.article{position:relative;padding:22px 0;border-bottom:1px solid var(--line2)}.article-layout{display:flex;align-items:flex-start;gap:22px;min-width:0}.article-copy{flex:1 1 auto;min-width:0}.article-thumb{display:block;flex:0 0 168px;width:168px;height:116px;overflow:hidden;border-radius:11px;background:rgba(23,63,49,.06);text-decoration:none}.article-thumb img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .18s ease}.article-thumb:hover img{transform:scale(1.025)}.article h3{margin:0;max-width:660px;font-size:1.22rem;line-height:1.18;letter-spacing:-.025em}.article h3 a{text-decoration:none}.article h3 a:hover{text-decoration:underline;text-underline-offset:3px}.teaser{max-width:650px;margin:8px 0 0;color:#3f4742;font-size:.88rem;line-height:1.48}.teaser-one-line{min-width:0;margin:8px 0 0;color:#3f4742;font-size:.88rem;line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.meta{display:flex;flex-wrap:wrap;align-items:center;gap:5px;margin-top:10px;color:var(--green);font-size:.64rem;font-weight:700}.meta .sep{color:#919a94}.meta a{color:var(--green);text-decoration:underline;text-decoration-color:rgba(31,91,69,.28);text-underline-offset:2px}.arrow{position:absolute;top:22px;right:0;width:27px;height:27px;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:50%;text-decoration:none;color:var(--green-dark);font-size:.77rem}.archive-list,.topic-list{margin-top:26px;border-top:1px solid var(--green-dark)}.archive-item,.topic-item{display:grid;grid-template-columns:150px minmax(0,1fr) 28px;gap:18px;align-items:center;padding:20px 0;border-bottom:1px solid var(--line2);text-decoration:none}.archive-date,.topic-count{color:var(--green);font-size:.72rem;font-weight:750}.archive-title,.topic-title{font-family:Georgia,"Times New Roman",serif;font-size:1.12rem;line-height:1.2}.archive-arrow,.topic-arrow{text-align:right;color:var(--green)}.small{color:var(--muted);font-size:.82rem;margin-top:25px}.empty{padding:20px 0;color:var(--muted);font-size:.86rem}footer{padding:0 0 34px;text-align:center;color:#8b928e;font-size:.72rem}
@media(max-width:760px){.header-shell,.shell{width:min(calc(100% - 30px),100%)}.site-header{position:relative;z-index:30;padding:15px 0 9px}.header-row{position:relative;align-items:center;gap:12px}.brand{gap:10px;font-size:.98rem;line-height:1;flex:0 1 auto;min-width:0}.brand-sun{width:31px;height:31px}.mobile-menu-toggle{display:inline-flex;margin-left:auto;flex:0 0 auto}.app-nav{display:none;position:absolute;top:calc(100% + 10px);left:0;right:0;z-index:40;padding:7px;border:1px solid rgba(23,63,49,.14);border-radius:18px;background:rgba(247,245,236,.985);box-shadow:0 18px 44px rgba(23,63,49,.12);backdrop-filter:blur(10px)}.site-header.menu-open .app-nav{display:block}.app-nav-inner{flex-direction:column;align-items:stretch;gap:0}.app-nav a{display:flex;align-items:center;min-height:43px;padding:0 12px;border-radius:12px;font-size:.86rem}.app-nav a:hover,.app-nav a.is-active{background:rgba(214,161,58,.08)}.header-cta{justify-content:flex-start;min-height:43px;margin-top:4px;padding:0 12px;border-radius:12px;background:rgba(214,161,58,.08)}.hero{padding-top:48px}.hero:after{right:-40px;top:34px}.section{padding:50px 0 54px}.archive-item,.topic-item{grid-template-columns:90px minmax(0,1fr) 20px;gap:10px}.article-layout{gap:13px}.article-thumb{flex-basis:112px;width:112px;height:84px;border-radius:9px}.article h3{font-size:1.14rem}.teaser{display:-webkit-box;overflow:hidden;-webkit-box-orient:vertical;-webkit-line-clamp:3}.teaser-one-line{display:none}}
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


def article_html(item, date_value=None, show_date=False, section="onbekend"):
    raw_title = item.get("title") or item.get("headline") or ""
    raw_source = item.get("source") or ""
    raw_category = canonical_category(category_label(item)) or category_label(item) or ""
    raw_source_url = item.get("url") or item.get("link") or "#"

    own_url = article_page_url(item, date_value) if has_article_page(item) else ""
    raw_url = own_url or raw_source_url
    link_attrs = "" if own_url else 'target="_blank" rel="noopener noreferrer"'

    title = esc(raw_title)
    teaser = esc(item.get("teaser") or item.get("summary") or item.get("description") or "")
    url = esc(raw_url)
    source = esc(raw_source)
    category = esc(raw_category)
    edition = esc(date_value or "")
    section_attr = esc(section)

    tracking_attrs = (
        f'data-article-click="true" '
        f'data-article-title="{title}" '
        f'data-article-source="{source}" '
        f'data-article-category="{category}" '
        f'data-article-section="{section_attr}" '
        f'data-article-edition="{edition}"'
    )

    image_data = resolve_pixabay_image(item, date_value) if date_value else None
    thumb_html = ""
    if image_data and image_data.get("image_path"):
        image_src = esc(image_data.get("image_path"))
        image_alt = esc(item.get("image_alt") or raw_title or "Illustratief beeld")
        thumb_html = (
            f'<a class="article-thumb" href="{url}" {link_attrs} aria-label="Lees {title}" {tracking_attrs}>'
            f'<img src="{image_src}" alt="{image_alt}" loading="lazy" decoding="async"></a>'
        )

    date_html = ""
    if show_date and date_value:
        date_html = f'<p class="date" style="margin:0 0 7px;text-transform:none;letter-spacing:0;font-weight:700">{esc(fmt_date_short(date_value))}</p>'
    return f"""<article class="article">
      <div class="article-layout">
        <div class="article-copy">
          {date_html}
          <h3><a href="{url}" {link_attrs} {tracking_attrs}>{title}</a></h3>
          {f'<p class="teaser-one-line">{teaser}</p>' if teaser else ''}
          {category_meta_html(item)}
        </div>
        {thumb_html}
      </div>
    </article>"""



def article_page_url(item, date_value):
    slug = str(item.get("article_slug") or "").strip().strip("/")
    if not slug or not date_value:
        return ""
    return f"{SITE_URL}/artikelen/{date_value}/{slug}/"


def article_body_paragraphs(item):
    body = item.get("article_body")
    if isinstance(body, list):
        return [str(x).strip() for x in body if str(x).strip()]
    if isinstance(body, str):
        return [x.strip() for x in re.split(r"\n\s*\n", body) if x.strip()]
    return []


def has_article_page(item):
    return bool(str(item.get("article_slug") or "").strip() and article_body_paragraphs(item))


def related_article_records(edition_records):
    records = []
    for date_value, data in edition_records:
        for section in ("nl", "int"):
            for position, item in enumerate(items(data, section)):
                if not has_article_page(item):
                    continue
                slug = str(item.get("article_slug") or "").strip().strip("/")
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
                    raise ValueError(f"Ongeldige article_slug '{slug}' in editie {date_value}.")
                records.append({
                    "date": date_value,
                    "section": section,
                    "position": position,
                    "slug": slug,
                    "category": canonical_category(category_label(item)) or category_label(item) or "",
                    "item": item,
                })
    return records


def select_related_articles(item, date_value, candidates, limit=3):
    current_slug = str(item.get("article_slug") or "").strip().strip("/")
    current_category = canonical_category(category_label(item)) or category_label(item) or ""

    eligible = [
        record for record in candidates
        if not (record["date"] == date_value and record["slug"] == current_slug)
    ]

    same_category = [record for record in eligible if record["category"] == current_category]
    other_categories = [record for record in eligible if record["category"] != current_category]
    return (same_category + other_categories)[:limit]


def render_related_articles(records):
    if not records:
        return ""

    cards = []
    for record in records:
        item = record["item"]
        date_value = record["date"]
        slug = record["slug"]
        title_raw = str(item.get("title") or item.get("headline") or "").strip()
        source_raw = str(item.get("source") or "").strip()
        category_raw = record["category"]
        teaser_raw = str(item.get("teaser") or item.get("summary") or item.get("description") or "").strip()
        href = f"/artikelen/{date_value}/{slug}/"

        title = esc(title_raw)
        source = esc(source_raw)
        category = esc(category_raw)
        teaser = esc(teaser_raw)
        edition = esc(date_value)

        tracking_attrs = (
            f'data-article-click="true" '
            f'data-article-title="{title}" '
            f'data-article-source="{source}" '
            f'data-article-category="{category}" '
            f'data-article-section="related" '
            f'data-article-edition="{edition}"'
        )

        image_data = resolve_pixabay_image(item, date_value)
        thumb_html = ""
        if image_data and image_data.get("image_path"):
            image_src = esc(image_data.get("image_path"))
            image_alt = esc(
                item.get("image_alt")
                or f"Illustratief beeld bij {title_raw}"
            )
            thumb_html = f"""
              <a class="related-thumb" href="{href}" aria-label="Lees {title}" {tracking_attrs}>
                <img src="{image_src}" alt="{image_alt}" loading="lazy" decoding="async">
              </a>"""

        rt = reading_time(item)
        meta_parts = [x for x in (category, source, esc(rt) if rt else "") if x]
        meta_html = '<span class="sep">·</span>'.join(
            f"<span>{part}</span>" for part in meta_parts
        )
        cards.append(f"""<article class="related-item">
          <div class="related-core">
            <div class="related-main">
              <h3><a href="{href}" {tracking_attrs}>{title}</a></h3>
              {f'<p class="related-teaser">{teaser}</p>' if teaser else ''}
              {f'<div class="related-meta">{meta_html}</div>' if meta_html else ''}
            </div>
            {thumb_html}
          </div>
        </article>""")

    return f"""<section class="related" aria-labelledby="related-title">
        <p class="related-kicker">Verder lezen</p>
        <h2 id="related-title">Misschien ook interessant</h2>
        <div class="related-list">{''.join(cards)}</div>
      </section>"""


def _load_pixabay_cache():
    if not PIXABAY_CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(PIXABAY_CACHE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"WAARSCHUWING: Pixabay-cache kon niet worden gelezen: {exc}")
        return {}


def _write_pixabay_cache(cache):
    PIXABAY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PIXABAY_CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _image_extension(content_type, image_url):
    content_type = str(content_type or "").lower()
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    path = urllib.parse.urlparse(image_url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return ".jpg"


def resolve_pixabay_image(item, date_value):
    query = str(item.get("image_query") or "").strip()
    if not query:
        return None

    slug = str(item.get("article_slug") or "").strip().strip("/")
    if not slug or not date_value:
        return None

    cache_key = f"{date_value}/{slug}"
    cache = _load_pixabay_cache()
    cached = cache.get(cache_key) if isinstance(cache.get(cache_key), dict) else None
    if cached and cached.get("query") == query and cached.get("image_path"):
        cached_path = Path(str(cached["image_path"]).lstrip("/"))
        if cached_path.exists():
            return cached

    api_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not api_key:
        print(
            f"WAARSCHUWING: image_query aanwezig bij '{item.get('title', slug)}', "
            "maar PIXABAY_API_KEY ontbreekt. Artikel blijft zonder beeld."
        )
        return None

    params = {
        "key": api_key,
        "q": query,
        "lang": "en",
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
        "order": "popular",
        "per_page": 20,
    }
    # Select a specific Pixabay photo when the editor supplies its ID.
    if query.startswith("id:") and query[3:].isdigit():
        params.pop("q", None)
        params["id"] = int(query[3:])
    search_url = PIXABAY_API_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        search_url,
        headers={"User-Agent": "PositiefNieuws/1.0 (+https://positief-nieuws.nl/)"},
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"WAARSCHUWING: Pixabay zoeken mislukt voor '{query}': {exc}")
        return None

    hits = payload.get("hits") if isinstance(payload, dict) else None
    if not isinstance(hits, list) or not hits:
        print(f"WAARSCHUWING: geen Pixabay-foto gevonden voor '{query}'.")
        return None

    pick_raw = item.get("image_pick", 0)
    try:
        pick = max(0, int(pick_raw))
    except (TypeError, ValueError):
        pick = 0
    if pick >= len(hits):
        pick = 0

    hit = hits[pick]
    image_url = str(hit.get("largeImageURL") or hit.get("webformatURL") or "").strip()
    if not image_url:
        print(f"WAARSCHUWING: Pixabay-resultaat voor '{query}' bevat geen bruikbare afbeeldings-URL.")
        return None

    download_request = urllib.request.Request(
        image_url,
        headers={"User-Agent": "PositiefNieuws/1.0 (+https://positief-nieuws.nl/)"},
    )
    try:
        with urllib.request.urlopen(download_request, timeout=30) as response:
            image_bytes = response.read()
            content_type = response.headers.get("Content-Type", "")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"WAARSCHUWING: Pixabay-foto downloaden mislukt voor '{query}': {exc}")
        return None

    if not image_bytes:
        print(f"WAARSCHUWING: lege Pixabay-foto ontvangen voor '{query}'.")
        return None

    ext = _image_extension(content_type, image_url)
    target_dir = ARTICLE_IMAGES_DIR / date_value
    target_dir.mkdir(parents=True, exist_ok=True)
    for old_ext in (".jpg", ".png", ".webp"):
        old_path = target_dir / f"{slug}{old_ext}"
        if old_path.exists() and old_path.suffix != ext:
            old_path.unlink()
    target_path = target_dir / f"{slug}{ext}"
    target_path.write_bytes(image_bytes)

    result = {
        "query": query,
        "pixabay_id": hit.get("id"),
        "image_path": "/" + target_path.as_posix(),
        "page_url": str(hit.get("pageURL") or "https://pixabay.com/").strip(),
        "photographer": str(hit.get("user") or "Pixabay-contributor").strip(),
        "tags": str(hit.get("tags") or "").strip(),
        "width": int(hit.get("imageWidth") or hit.get("webformatWidth") or 0),
        "height": int(hit.get("imageHeight") or hit.get("webformatHeight") or 0),
    }
    cache[cache_key] = result
    _write_pixabay_cache(cache)
    print(f"Pixabay-foto opgeslagen: {target_path} (zoekterm: {query!r})")
    return result


def article_image_html(item, image_data):
    if not image_data:
        return ""
    image_path = esc(image_data.get("image_path") or "")
    if not image_path:
        return ""
    page_url = esc(image_data.get("page_url") or "https://pixabay.com/")
    photographer = esc(image_data.get("photographer") or "Pixabay-contributor")
    alt = esc(item.get("image_alt") or item.get("title") or "Illustratief beeld")
    return f"""<figure class="article-figure">
        <img src="{image_path}" alt="{alt}" loading="eager" fetchpriority="high">
        <figcaption>Illustratief beeld · Foto: {photographer} via <a href="{page_url}" target="_blank" rel="noopener noreferrer">Pixabay</a>.</figcaption>
      </figure>"""


ARTICLE_GROWTH_CSS = '\n.article-growth [hidden]{display:none!important}\n.article-growth{max-width:700px;margin:34px 0 0;border:1px solid var(--line);border-radius:16px;overflow:hidden}\n.article-newsletter{padding:32px;background:var(--green-dark);color:#fff;position:relative}\n.article-newsletter .growth-kicker{margin:0 0 10px;color:#e4bc65;font-size:.66rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase}\n.article-newsletter h2{margin:0;font-family:Georgia,serif;font-size:clamp(1.7rem,4vw,2.2rem);line-height:1.12;letter-spacing:-.03em;color:#fff;max-width:520px}\n.article-newsletter .growth-intro{margin:14px 0 22px;color:#e1e9df;font-size:.9rem;line-height:1.6;max-width:560px}\n.article-newsletter label{display:block;margin-bottom:8px;font-size:.74rem;font-weight:700}\n.growth-form-row{display:flex;gap:10px}.growth-form-row input{flex:1;min-width:0;border:1px solid #aebdae;border-radius:8px;background:#fff;color:var(--ink);padding:13px 14px;font:inherit;font-size:.86rem;min-height:48px}\n.growth-form-row button{border:1px solid #e4bc65;border-radius:8px;background:#e4bc65;color:#173f31;padding:13px 18px;min-height:48px;font:inherit;font-size:.8rem;font-weight:800;cursor:pointer;white-space:nowrap}.growth-form-row button:hover{background:#f0d291}\n.article-newsletter .growth-note{margin:13px 0 0;font-size:.66rem;line-height:1.6;color:#d2decf}.growth-note a{color:inherit;text-underline-offset:3px}\n.article-share{padding:23px 32px;background:#f2eedf}.article-share h2{font-family:Georgia,serif;margin:0;font-size:1.3rem;color:var(--green-dark)}.article-share p{margin:6px 0 15px;font-size:.79rem;color:#58665b}\n.article-share-buttons{display:flex;flex-wrap:wrap;gap:9px}.article-share-buttons a,.article-share-buttons button{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;border:1px solid #aab4a4;border-radius:999px;padding:9px 15px;background:transparent;color:var(--green-dark);font:inherit;font-size:.74rem;font-weight:700;text-decoration:none;cursor:pointer}.article-share-buttons a:hover,.article-share-buttons button:hover{background:#e5e8d9;border-color:var(--green)}.article-share-buttons svg{width:18px;height:18px;flex:none}\n.article-share-status{font-size:.7rem!important;margin:10px 0 0!important}.article-share-status:empty{display:none}.article-copy-fallback{margin-top:12px}.article-copy-fallback label{display:block;font-size:.72rem;margin-bottom:5px}.article-copy-fallback input{width:100%;min-height:44px;padding:9px;border:1px solid var(--line);border-radius:6px;font:inherit;font-size:.75rem}\n.article-growth :focus-visible{outline:3px solid #d6a13a;outline-offset:4px}.article-newsletter :focus-visible{outline-color:#fff}\n@media(max-width:640px){.article-newsletter{padding:25px 22px}.article-share{padding:23px 22px}.growth-form-row{flex-direction:column}.growth-form-row button{width:100%}.article-share-buttons{gap:8px}.article-share-buttons a,.article-share-buttons button{padding:9px 12px}}\n'

ARTICLE_GROWTH_JS = '<script>\n(function () {\n  const block = document.querySelector(\'.article-growth\');\n  if (!block) return;\n  const url = document.querySelector(\'link[rel="canonical"]\').href;\n  const title = document.querySelector(\'h1\').textContent.replace(/\\.$/, \'\');\n  const form = document.querySelector(\'#article-newsletter-form\');\n  const isSpecial = window.sa_metadata?.page_type === \'special\';\n  const metadata = {placement: isSpecial ? \'special_end\' : \'article_end\', article_url: url};\n  function track(name, extra) {\n    if (window.sa_event) window.sa_event(name, Object.assign({}, metadata, extra || {}));\n  }\n  form.addEventListener(\'submit\', function () {\n    track(\'nieuwsbrief_inschrijving\');\n  });\n  if (\'IntersectionObserver\' in window) {\n    const observer = new IntersectionObserver(function (entries) {\n      if (entries.some(entry => entry.isIntersecting)) {\n        track(isSpecial ? \'special_newsletter_view\' : \'article_newsletter_view\');\n        observer.disconnect();\n      }\n    }, {threshold: 0.5});\n    observer.observe(document.querySelector(\'.article-newsletter\'));\n  }\n  block.querySelectorAll(\'[data-share-channel]\').forEach(function (link) {\n    link.addEventListener(\'click\', function () {\n      track(isSpecial ? \'special_share_click\' : \'article_share_click\', {channel: link.dataset.shareChannel});\n    });\n  });\n  const nativeButton = document.querySelector(\'#article-native-share\');\n  if (navigator.share) {\n    nativeButton.hidden = false;\n    nativeButton.addEventListener(\'click\', async function () {\n      track(isSpecial ? \'special_share_click\' : \'article_share_click\', {channel: \'native\'});\n      try { await navigator.share({title: title, text: title, url: url}); }\n      catch (error) {\n        if (error.name !== \'AbortError\') document.querySelector(\'#article-share-status\').textContent = \'Delen lukte niet. Gebruik WhatsApp, e-mail of kopieer de link.\';\n      }\n    });\n  }\n  document.querySelector(\'#article-copy-link\').addEventListener(\'click\', async function () {\n    track(isSpecial ? \'special_share_click\' : \'article_share_click\', {channel: \'copy\'});\n    try {\n      await navigator.clipboard.writeText(url);\n      document.querySelector(\'#article-share-status\').textContent = \'Link gekopieerd. Klaar om door te sturen.\';\n    } catch (_) {\n      document.querySelector(\'#article-copy-fallback\').hidden = false;\n      const field = document.querySelector(\'#article-url\');\n      field.focus(); field.select();\n      document.querySelector(\'#article-share-status\').textContent = \'Selecteer en kopieer de link hieronder.\';\n    }\n  });\n})();\n</script>'


def render_growth_block(canonical, title_raw, page_type="article"):
    placement = "special_end" if page_type == "special" else "article_end"
    whatsapp_url = esc("https://wa.me/?text=" + urllib.parse.quote(title_raw + "\n\n" + canonical, safe=""))
    email_url = esc("mailto:?subject=" + urllib.parse.quote(title_raw, safe="") + "&body=" + urllib.parse.quote(title_raw + "\n\n" + canonical + "\n\nPositief nieuws · Dit gebeurt ook.", safe=""))
    return f"""      <section class="article-growth" aria-label="Ontvang en deel Positief nieuws">
        <div class="article-newsletter" id="nieuwsbrief">
          <p class="growth-kicker">Dit gebeurt ook. In je inbox.</p>
          <h2>Meer van dit soort nieuws?</h2>
          <p class="growth-intro">Ontvang elke maandag en donderdag een selectie positief nieuws uit Nederland en de wereld. Gratis, rustig en in een paar minuten gelezen.</p>
          <form id="article-newsletter-form" action="https://buttondown.com/api/emails/embed-subscribe/positiefnieuws" method="post">
            <label for="article-email">Je e-mailadres</label>
            <div class="growth-form-row"><input id="article-email" type="email" name="email" autocomplete="email" placeholder="jij@voorbeeld.nl" required><button type="submit">Ja, stuur mij Positief nieuws</button></div>
            <input type="hidden" name="embed" value="1">
            <input type="hidden" name="metadata__signup_source" value="{placement}">
            <input type="hidden" name="metadata__signup_{page_type}" value="{esc(canonical)}">
            <p class="growth-note">Je ontvangt een bevestigingsmail. Afmelden kan altijd. <a href="/#privacy">Privacy</a></p>
          </form>
        </div>
        <div class="article-share">
          <h2>Goed nieuws mag verder reizen.</h2>
          <p>Ken je iemand die dit ook wil lezen? Deel dit verhaal.</p>
          <div class="article-share-buttons">
            <a href="{whatsapp_url}" target="_blank" rel="noopener noreferrer" data-share-channel="whatsapp"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M20 11.5a8 8 0 0 1-12 7l-5 1.5 1.5-5A8 8 0 1 1 20 11.5Z"/><path d="M8 8c0 4 4 7 7 7l1-2-3-1-1 1-2-2 1-1-1-3Z"/></svg>WhatsApp</a>
            <a href="{email_url}" data-share-channel="email"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/></svg>E-mail</a>
            <button id="article-copy-link" type="button">Kopieer link</button>
            <button id="article-native-share" type="button" hidden>Meer deelopties</button>
          </div>
          <p id="article-share-status" class="article-share-status" role="status" aria-live="polite"></p>
          <div id="article-copy-fallback" class="article-copy-fallback" hidden><label for="article-url">Link naar dit artikel</label><input id="article-url" value="{esc(canonical)}" readonly></div>
        </div>
      </section>"""


def render_article_page(item, date_value, related_records=None, image_data=None):
    title_raw = str(item.get("title") or item.get("headline") or "").strip()
    source_raw = str(item.get("source") or "Oorspronkelijke bron").strip()
    category_raw = canonical_category(category_label(item)) or category_label(item) or ""
    source_url_raw = str(item.get("url") or item.get("link") or "#").strip()
    teaser_raw = str(item.get("teaser") or item.get("summary") or "").strip()
    why_raw = str(item.get("why_it_matters") or "").strip()
    paragraphs = article_body_paragraphs(item)
    canonical = article_page_url(item, date_value)
    if not canonical or not title_raw or not paragraphs:
        raise ValueError("Artikelpagina mist article_slug, titel of article_body.")

    desc_raw = teaser_raw or paragraphs[0]
    if len(desc_raw) > 158:
        desc_raw = desc_raw[:157].rstrip(" ,;:") + "…"

    date_text = fmt_date(date_value)
    title = esc(title_raw)
    source = esc(source_raw)
    category = esc(category_raw)
    source_url = esc(source_url_raw)
    teaser = esc(teaser_raw)
    body_html = "".join(f"<p>{esc(paragraph)}</p>" for paragraph in paragraphs)
    why_html = f'<aside class="why"><p class="why-label">Waarom dit ertoe doet</p><p>{esc(why_raw)}</p></aside>' if why_raw else ""
    growth_html = render_growth_block(canonical, title_raw)
    related_html = render_related_articles(related_records or [])
    image_html = article_image_html(item, image_data)

    source_attrs = (
        f'data-source-click="true" '
        f'data-article-title="{title}" '
        f'data-article-source="{source}" '
        f'data-article-category="{category}" '
        f'data-article-edition="{esc(date_value)}"'
    )

    schema_data = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title_raw,
        "description": desc_raw,
        "datePublished": date_value,
        "dateModified": date_value,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "publisher": {"@type": "Organization", "name": "Positief nieuws", "url": SITE_URL + "/"},
        "isPartOf": {"@type": "WebSite", "name": "Positief nieuws", "url": SITE_URL + "/"},
        "isBasedOn": source_url_raw,
    }
    if image_data and image_data.get("image_path"):
        schema_data["image"] = SITE_URL + str(image_data["image_path"])
    schema = json.dumps(schema_data, ensure_ascii=False)

    article_css = r"""
.article-page{padding:46px 0 74px}
.article-wrap{max-width:760px}
.article-kicker{margin:0 0 12px;color:var(--green-dark);font-size:.72rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.article-page h1{max-width:760px;margin:0;font-size:clamp(1.95rem,5vw,3.8rem);line-height:1.02;letter-spacing:-.045em}
.article-deck{max-width:700px;margin:22px 0 0;font-size:1.12rem;line-height:1.62;color:#3f4842}
.article-meta{display:flex;flex-wrap:wrap;gap:8px 14px;margin:22px 0 0;color:var(--muted);font-size:.78rem}
.article-figure{max-width:700px;margin:28px 0 26px}
.article-figure img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:12px;background:#ece8dc}
.article-figure figcaption{margin-top:8px;color:var(--muted);font-size:.68rem;line-height:1.45}
.article-figure figcaption a{color:var(--green);text-underline-offset:2px}
.article-rule{height:1px;background:var(--line);margin:30px 0}
.article-copy{max-width:700px;font-size:1.06rem;line-height:1.78;color:#242a26}
.article-copy p{margin:0 0 1.25em}
.why{max-width:700px;margin:34px 0;padding:22px 24px;background:#f8f3e8;border-left:4px solid #d6a13a}
.why-label{margin:0 0 7px!important;color:var(--green-dark);font-size:.72rem!important;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.why p{margin:0;font-size:1rem;line-height:1.65}
.source-box{max-width:700px;margin-top:34px;padding-top:26px;border-top:1px solid var(--line)}
.source-box p{margin:0 0 13px;color:var(--muted);font-size:.82rem;line-height:1.5}
.source-button{display:inline-flex;align-items:center;gap:8px;padding:11px 16px;border:1px solid var(--green-dark);border-radius:999px;color:var(--green-dark);text-decoration:none;font-size:.8rem;font-weight:800}
.source-button:hover{background:var(--green-dark);color:white}
.article-note{max-width:700px;margin-top:24px;color:var(--muted);font-size:.76rem;line-height:1.55}
.support-teaser{max-width:700px;margin:42px 0 0;padding:28px 30px;border:1px solid rgba(214,161,58,.32);border-radius:18px;background:radial-gradient(circle at 92% 18%,rgba(214,161,58,.11),transparent 29%),rgba(255,255,255,.42)}
.support-teaser-grid{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:28px}
.support-teaser .support-kicker{margin:0;color:var(--green);font-size:.68rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.support-teaser h2{margin:7px 0 0;font-family:Georgia,"Times New Roman",serif;color:#111512;font-size:1.55rem;line-height:1.08;letter-spacing:-.035em}
.support-teaser p{max-width:500px;margin:10px 0 0;color:var(--muted);font-size:.84rem;line-height:1.55}
.support-button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 19px;border:1px solid var(--green-dark);border-radius:999px;background:var(--green-dark);color:white;font-size:.76rem;font-weight:800;text-decoration:none;white-space:nowrap;transition:transform .15s ease,background .15s ease}
.support-button:hover{transform:translateY(-1px);background:var(--green)}
.related{max-width:700px;margin-top:48px;padding-top:34px;border-top:1px solid var(--green-dark)}
.related-kicker{margin:0 0 7px;color:var(--green);font-size:.68rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.related h2{margin:0 0 8px;font-size:clamp(1.65rem,4vw,2.25rem);line-height:1.05;letter-spacing:-.035em}
.related-list{border-top:1px solid var(--line);margin-top:20px}
.related-item{position:relative;padding:20px 0;border-bottom:1px solid var(--line2)}
.related-core{display:flex;align-items:flex-start;gap:22px;min-width:0}
.related-main{flex:1 1 auto;min-width:0}
.related-meta{display:flex;flex-wrap:wrap;align-items:center;gap:5px;margin:9px 0 0;color:var(--green);font-size:.64rem;font-weight:750}
.related-meta .sep{color:#919a94}
.related-item h3{margin:0;max-width:610px;font-size:1.16rem;line-height:1.2;letter-spacing:-.022em}
.related-item h3 a{text-decoration:none}
.related-item h3 a:hover{text-decoration:underline;text-underline-offset:3px}
.related-teaser{min-width:0;max-width:610px;margin:7px 0 0;color:#465049;font-size:.84rem;line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.related-thumb{display:block;flex:0 0 168px;width:168px;height:116px;overflow:hidden;border-radius:11px;background:rgba(23,63,49,.06);text-decoration:none}
.related-thumb img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .18s ease}
.related-thumb:hover img{transform:scale(1.025)}
.article-back{margin-top:34px}
.article-back a{color:var(--green-dark);font-weight:700;font-size:.8rem}
@media (max-width:640px){.article-page{padding-top:34px}.article-page h1{font-size:clamp(1.85rem,10vw,2.85rem);line-height:1.03}.article-copy{font-size:1rem}.why{padding:19px}.support-teaser{padding:24px 22px}.support-teaser-grid{grid-template-columns:1fr;gap:20px}.support-teaser h2{font-size:1.45rem}.support-button{width:100%}.related{margin-top:40px;padding-top:28px}.related h2{font-size:1.75rem}.related-core{gap:13px}.related-thumb{flex-basis:112px;width:112px;height:84px;border-radius:9px}.related-item h3{font-size:1.08rem}.related-teaser{display:none}}
"""

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Positief nieuws</title>
  <meta name="description" content="{esc(desc_raw)}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{esc(desc_raw)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="Positief nieuws">
  {f'<meta property="og:image" content="{SITE_URL + str(image_data.get("image_path"))}">' if image_data and image_data.get("image_path") else ''}
  <meta name="twitter:card" content="{'summary_large_image' if image_data and image_data.get('image_path') else 'summary'}">
  <meta name="theme-color" content="#17382b">
  <script type="application/ld+json">{schema}</script>
  <style>{BASE_CSS}{article_css}{ARTICLE_GROWTH_CSS}</style>
</head>
<body>
  {header_html()}
  <main class="article-page">
    <div class="shell article-wrap">
      <p class="article-kicker">{category or 'Positief nieuws'}</p>
      <h1>{title}<b>.</b></h1>
      {f'<p class="article-deck">{teaser}</p>' if teaser else ''}
      <div class="article-meta"><span>{esc(date_text)}</span><span>Bron: {source}</span></div>
      {image_html}
      <div class="article-rule"></div>
      <article class="article-copy">{body_html}</article>
      {why_html}
      <div class="source-box">
        <p>Dit is een redactionele samenvatting van Positief nieuws, gebaseerd op de oorspronkelijke publicatie van {source}.</p>
        <a class="source-button" href="{source_url}" target="_blank" rel="noopener noreferrer" {source_attrs}>Lees het oorspronkelijke artikel ↗</a>
      </div>
      <p class="article-note">Positief nieuws selecteert en vat ontwikkelingen samen in eigen woorden. De oorspronkelijke bron blijft leidend voor de volledige context en details.</p>

      {growth_html}

      <section class="support-teaser" aria-labelledby="article-support-title">
        <div class="support-teaser-grid">
          <div>
            <p class="support-kicker">Steun Positief nieuws</p>
            <h2 id="article-support-title">Help Positief nieuws door te gaan.</h2>
            <p>Positief nieuws is gratis en zonder advertenties. Met een kleine vrijwillige bijdrage help je de site en nieuwsbrief draaiend te houden. Je kiest zelf het bedrag.</p>
          </div>
          <a
            class="support-button"
            href="/steun/"
            onclick="if (window.sa_event) {{ sa_event('steun_teaser_click'); }}"
          >Steun Positief nieuws</a>
        </div>
      </section>

      {related_html}
      <p class="article-back"><a href="/edities/{esc(date_value)}/">← Terug naar de editie van {esc(date_text)}</a></p>
    </div>
  </main>
  <footer>Positief nieuws · Dit gebeurt ook. · <a href="/contact/" onclick="if(window.sa_event)window.sa_event('contact_click')">Contact</a> · <a href="/tip/" onclick="if(window.sa_event)window.sa_event('tip_redactie_click')">Tip de redactie</a></footer>
  {analytics_html({'page_type':'article','edition':date_value,'article_title':title_raw,'source':source_raw,'category':category_raw})}
  {ARTICLE_GROWTH_JS}
</body>
</html>"""


def write_article_pages(edition_records):
    candidates = related_article_records(edition_records)
    built = []

    for record in candidates:
        date_value = record["date"]
        item = record["item"]
        slug = record["slug"]
        related = select_related_articles(item, date_value, candidates, limit=3)
        image_data = resolve_pixabay_image(item, date_value)

        page_dir = ARTICLES_DIR / date_value / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text("\n".join(line.rstrip() for line in render_article_page(item, date_value, related, image_data).split("\n")), encoding="utf-8")
        built.append({
            "date": date_value,
            "slug": slug,
            "url": f"{SITE_URL}/artikelen/{date_value}/{slug}/",
            "title": str(item.get("title") or ""),
        })
        print(f"Gebouwd: {page_dir / 'index.html'}")

    return built


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

    nl_html = "\n".join(article_html(x, date_value, False, "nl") for x in items(data, "nl")[:6])
    int_html = "\n".join(article_html(x, date_value, False, "int") for x in items(data, "int")[:6])
    head_html = "\n".join(_headline_html(x, i, date_value) for i, x in enumerate(items(data, "headlines")[:3], 1))

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
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="article"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary"><meta name="theme-color" content="#17382b"><link rel="manifest" href="/manifest.json?v=5"><link rel="apple-touch-icon" href="/sun-apple-touch-icon.png"><script type="application/ld+json">{schema}</script><style>{BASE_CSS}.banner{{margin-top:18px;padding:10px 13px;border:1px solid var(--line);color:var(--green-dark);font-size:.75rem}}.briefing-row{{display:grid;grid-template-columns:34px minmax(0,1fr);gap:10px;padding-right:46px}}.num{{padding-top:2px;color:#7f8982;font-size:.66rem;font-weight:700}}.end{{padding:72px 0 64px;text-align:center}}.end h2{{max-width:620px;margin:auto;font-size:clamp(2.2rem,5vw,3.3rem);line-height:1;letter-spacing:-.045em}}.back{{display:inline-flex;margin-top:18px;padding:9px 15px;border:1px solid var(--line);border-radius:999px;text-decoration:none;font-size:.72rem;font-weight:700}}</style></head><body>
{header_html()}
<div class="shell banner">Je leest de editie van {esc(date_text)}. <a href="/">Ga naar de nieuwste editie →</a></div>
<section class="hero"><div class="shell"><p class="date">{esc(date_text)}</p><h1>Dit gebeurt ook<b>.</b></h1><p class="lead">In een paar minuten weet je wat er goed gaat én wat je verder moet weten in deze editie. Zonder eindeloos scrollen.</p><div class="rule"></div></div></section>
<main>
<section class="section alt"><div class="shell"><div class="heading"><p class="kicker">Goed nieuws uit Nederland</p><span class="count">6 verhalen</span></div>{nl_html}</div></section>
<section class="section"><div class="shell"><div class="heading"><p class="kicker">Goed nieuws uit de wereld</p><span class="count">6 verhalen</span></div><p class="note">Zes positieve ontwikkelingen van buiten Nederland. Lees de samenvattingen en volledige artikelen in het Nederlands.</p>{int_html}</div></section>
<section class="section alt"><div class="shell"><div class="heading"><p class="kicker">Wat je verder moet weten</p><span class="count">3 verhalen</span></div><p class="note">Niet per se positief, wel belangrijk.</p>{head_html}</div></section>
<section class="end"><div class="shell"><h2>Dit was het voor deze editie.<br>Je bent weer bij.</h2><p>Geniet van je dag.</p><a class="back" href="/">Lees de nieuwste editie</a></div></section>
</main><footer>Positief nieuws · Dit gebeurt ook. · <a href="/contact/" onclick="if(window.sa_event)window.sa_event('contact_click')">Contact</a> · <a href="/tip/" onclick="if(window.sa_event)window.sa_event('tip_redactie_click')">Tip de redactie</a></footer>{analytics_html({'page_type':'edition','edition':date_value})}</body></html>"""


def _headline_html(item, number, date_value=None):
    raw_title = item.get("title") or ""
    raw_source = item.get("source") or ""
    raw_category = item.get("category") or ""
    raw_url = item.get("url") or "#"

    title = esc(raw_title)
    teaser = esc(item.get("teaser") or item.get("summary") or "")
    source = esc(raw_source)
    category = esc(raw_category)
    url = esc(raw_url)
    edition = esc(date_value or "")

    tracking_attrs = (
        f'data-article-click="true" '
        f'data-article-title="{title}" '
        f'data-article-source="{source}" '
        f'data-article-category="{category}" '
        f'data-article-section="headlines" '
        f'data-article-edition="{edition}"'
    )

    meta_parts = [p for p in (category, source) if p]
    meta = ""
    if meta_parts:
        meta = '<div class="meta">' + '<span class="sep">·</span>'.join(f"<span>{p}</span>" for p in meta_parts) + "</div>"
    return f"""<article class="article" style="display:grid;grid-template-columns:34px minmax(0,1fr);gap:10px;padding-right:46px"><div class="num">{number:02d}</div><div><h3><a href="{url}" target="_blank" rel="noopener noreferrer" {tracking_attrs}>{title}</a></h3>{f'<p class="teaser">{teaser}</p>' if teaser else ''}{meta}</div><a class="arrow" href="{url}" target="_blank" rel="noopener noreferrer" aria-label="Lees {title}" {tracking_attrs}>↗</a></article>"""


def render_archive(entries):
    rows = []
    for entry in entries:
        date_value = entry["date"]
        date_text = fmt_date(date_value)
        short_date = " ".join(date_text.split()[:-1])
        rows.append(f'<a class="archive-item" href="/edities/{date_value}/"><span class="archive-date">{esc(short_date)}</span><span class="archive-title">Positief nieuws · {esc(date_text)}</span><span class="archive-arrow">→</span></a>')
    desc = "Bekijk alle eerdere edities van Positief nieuws: 12 positieve nieuwsverhalen uit Nederland en de wereld, plus 3 belangrijke onderwerpen."
    schema = json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":"Archief van Positief nieuws","url":f"{SITE_URL}/edities/","description":desc,"isPartOf":{"@type":"WebSite","name":"Positief nieuws","url":SITE_URL+"/"}}, ensure_ascii=False)
    return f"""<!DOCTYPE html><html lang="nl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Archief | Eerdere edities van Positief nieuws</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{SITE_URL}/edities/"><meta property="og:title" content="Archief · Positief nieuws"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{SITE_URL}/edities/"><meta name="twitter:card" content="summary"><meta name="theme-color" content="#17382b"><script type="application/ld+json">{schema}</script><style>{BASE_CSS}</style></head><body>{header_html('archive')}<main><section class="hero"><div class="shell"><p class="kicker">Eerdere edities</p><h1>Archief<b>.</b></h1><p class="lead">Lees eerdere edities van Positief nieuws terug.</p><div class="rule"></div></div></section><section class="section"><div class="shell"><div class="archive-list">{''.join(rows)}</div><p class="small">Bekijk ook het overzicht van <a href="/onderwerpen/">onderwerpen</a>.</p></div></section></main><footer>Positief nieuws · Dit gebeurt ook. · <a href="/contact/" onclick="if(window.sa_event)window.sa_event('contact_click')">Contact</a> · <a href="/tip/" onclick="if(window.sa_event)window.sa_event('tip_redactie_click')">Tip de redactie</a></footer>{analytics_html({'page_type':'archive'})}</body></html>"""


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


TOPIC_INDEX_CSS = r"""
.topics-shell{width:min(calc(100% - 48px),1040px);margin:0 auto}
.topics-intro{padding:65px 0 38px}.topics-intro-inner>div{min-width:0}.topics-intro-inner{display:grid;grid-template-columns:1fr 220px;align-items:center;gap:40px}
.topics-intro h1{font-family:Georgia,serif;font-size:clamp(3rem,6vw,4.8rem);line-height:1.04;letter-spacing:-.045em;margin:15px 0 22px;color:var(--green-dark)}
.topics-intro h1 b{color:var(--accent)}.topics-intro .lead{max-width:600px;font-size:1.05rem;line-height:1.65;color:#56635b;margin:0}
.topics-seal{width:190px;height:190px;border-radius:50%;background:#e8ecd9;display:grid;place-items:center;position:relative;transform:rotate(-9deg);color:var(--green-dark)}
.topics-seal:before{content:"";position:absolute;inset:10px;border:1px solid #a7b497;border-radius:50%}.topics-seal span{text-align:center;font-family:Georgia,serif;font-size:1.65rem;line-height:1.15}.topics-seal small{display:block;font-family:Arial,sans-serif;font-size:.56rem;letter-spacing:.12em;text-transform:uppercase;margin-bottom:13px}.topics-seal b{color:#b5852c;font-size:2rem}
.topics-divider{display:flex;justify-content:space-between;gap:15px;border-top:1px solid var(--green-dark);padding:15px 0;color:var(--green);font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;margin-top:38px}
.topics-grid-section{padding:0 0 65px}.topics-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}
.topic-card{display:grid;grid-template-columns:minmax(0,1fr) 116px;align-items:center;gap:20px;background:#eeeee2;border:1px solid rgba(23,63,49,.12);padding:30px;text-decoration:none;border-radius:5px;position:relative;min-height:220px;transition:transform .18s,border-color .18s,box-shadow .18s}
.topic-card:nth-child(4n+2),.topic-card:nth-child(4n+3){background:#f2eadc}.topic-card:hover{transform:translateY(-3px);border-color:#819b83;box-shadow:0 8px 20px rgba(23,63,49,.06)}.topic-card:focus-visible{outline:3px solid var(--green);outline-offset:4px}
.topic-card-count{font-size:.63rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#5d7562}.topic-card h2{font-family:Georgia,serif;font-weight:400;font-size:1.65rem;line-height:1.14;color:var(--green-dark);margin:13px 0 10px;letter-spacing:-.025em}.topic-card p{font-size:.78rem;line-height:1.6;color:#5d655e;margin:0}.topic-card-link{display:block;font-size:.66rem;color:var(--green);font-weight:700;margin-top:19px}.topic-card-link span{display:inline-block;margin-left:8px;transition:transform .18s}.topic-card:hover .topic-card-link span{transform:translateX(4px)}
.topic-art{width:116px;height:116px;color:var(--green);background:rgba(255,255,255,.34);border-radius:50%;padding:19px}.topic-art .gold{stroke:#ba8835}
.topics-note{margin-top:28px;font-size:.76rem;color:var(--muted);text-align:center}.topics-index footer{border-top:1px solid var(--line2);padding:25px 15px 32px}
@media(max-width:760px){.topics-shell{width:calc(100% - 30px)}.topics-intro{padding:42px 0 22px}.topics-intro-inner{grid-template-columns:1fr;gap:0}.topics-seal{display:none}.topics-intro h1{font-size:clamp(2.3rem,10.5vw,3.35rem)}.topics-intro .lead{font-size:.93rem}.topics-divider{margin-top:28px;font-size:.58rem}.topics-grid{grid-template-columns:1fr;gap:15px}.topic-card{padding:25px;min-height:195px;grid-template-columns:minmax(0,1fr) 90px;gap:15px}.topic-art{width:90px;height:90px;padding:14px}.topic-card h2{font-size:1.55rem}.topics-grid-section{padding-bottom:42px}}
@media(prefers-reduced-motion:reduce){.topic-card,.topic-card-link span{transition:none}}
"""

TOPIC_INDEX_ART = {
"Cultuur": ('Verhalen die verbinden, inspireren en ons erfgoed laten leven.', '<path d="M12 19h18v43H12zM30 23h18v39H30zM48 16h17v46H48z"/><path class="gold" d="M17 28h8M17 34h8M35 31h8M53 25h7M53 31h7"/>'),
"Economie": ('Nieuwe kansen voor een eerlijkere, veerkrachtige economie.', '<path d="M14 62h51M19 55V42h10v13M34 55V32h10v23M49 55V20h10v35"/><path class="gold" d="m16 31 18-12 12 3 16-12m-10 0h10v10"/>'),
"Energie & innovatie": ('Slimme ideeën en schone energie voor de wereld van morgen.', '<path d="M28 48c-18-17-7-35 11-35s28 18 11 35l-3 7H31zM32 61h14M35 67h8"/><path class="gold" d="m42 24-11 16h13l-7 12M39 3v4M9 21l5 3M64 24l5-3"/>'),
"Gezondheid": ('Vooruitgang die mensen gezonder maakt en zorg verbetert.', '<path d="M39 65 13 39c-17-20 11-38 26-17 15-21 43-3 26 17z"/><path class="gold" d="M12 41h16l6-13 10 24 6-11h17"/>'),
"Mens": ('Mensen die naar elkaar omkijken en samen iets veranderen.', '<circle cx="39" cy="22" r="9"/><circle cx="15" cy="31" r="7"/><circle cx="63" cy="31" r="7"/><path d="M24 62V50c0-20 30-20 30 0v12M4 59V48c0-12 13-15 20-7M74 59V48c0-12-13-15-20-7"/><path class="gold" d="M31 62h16"/>'),
"Natuur & klimaat": ('Herstel van de natuur en hoopvolle stappen voor het klimaat.', '<path d="M39 65V37M39 48C10 51 9 26 12 14c24-3 29 15 27 34zM39 39C38 13 57 9 69 11c3 23-13 30-30 28z"/><path class="gold" d="m19 23 20 25m0-9 21-20M22 66h34"/>'),
"Wetenschap": ('Ontdekkingen die onze blik verruimen en nieuwe deuren openen.', '<ellipse cx="39" cy="39" rx="33" ry="13"/><ellipse cx="39" cy="39" rx="33" ry="13" transform="rotate(60 39 39)"/><ellipse cx="39" cy="39" rx="33" ry="13" transform="rotate(120 39 39)"/><circle class="gold" cx="39" cy="39" r="5"/>'),
"Sport": ('Sport die verbindt, grenzen verlegt en mensen in beweging brengt.', '<path d="M24 14h30v15c0 25-30 25-30 0zM24 20H12v9c0 12 9 16 16 16M54 20h12v9c0 12-9 16-16 16M39 48v15M26 65h26"/><path class="gold" d="m39 21 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z"/>'),
}

def render_topics_index(topics, latest):
    cards = []
    for topic in topics.values():
        total = len(topic["nl"]) + len(topic["int"])
        description, illustration = TOPIC_INDEX_ART.get(topic["label"], ("Ontdek hoopvolle verhalen over dit onderwerp.", ""))
        cards.append(f'<a class="topic-card" href="/{esc(topic["slug"])}/"><div><span class="topic-card-count">{story_count(total)}</span><h2>{esc(topic["label"])}</h2><p>{esc(description)}</p><span class="topic-card-link">Bekijk de verhalen <span aria-hidden="true">→</span></span></div><svg class="topic-art" viewBox="0 0 78 78" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{illustration}</svg></a>')
    desc = "Bekijk positief nieuws per onderwerp. Eerst Nederlandse verhalen, daarna Engelstalige artikelen, steeds met de nieuwste verhalen bovenaan."
    schema = json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":"Onderwerpen · Positief nieuws","description":desc,"url":f"{SITE_URL}/onderwerpen/","isPartOf":{"@type":"WebSite","name":"Positief nieuws","url":SITE_URL+"/"}}, ensure_ascii=False)
    return f"""<!DOCTYPE html><html lang="nl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Onderwerpen | Positief nieuws per thema</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{SITE_URL}/onderwerpen/"><meta property="og:title" content="Onderwerpen · Positief nieuws"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{SITE_URL}/onderwerpen/"><meta name="twitter:card" content="summary"><meta name="theme-color" content="#17382b"><script type="application/ld+json">{schema}</script><style>{BASE_CSS}{TOPIC_INDEX_CSS}</style></head><body class="topics-index">{header_html('topics')}<main><section class="topics-intro"><div class="topics-shell"><div class="topics-intro-inner"><div><p class="kicker">Positief nieuws per thema</p><h1>Onderwerpen<b>.</b></h1><p class="lead">De wereld gaat op allerlei manieren vooruit. Ontdek de verhalen achter die vooruitgang, van een gezondere samenleving tot natuur die zich herstelt.</p></div><div class="topics-seal" aria-hidden="true"><span><small>Een andere blik</small>Dit gebeurt<br>ook<b>.</b></span></div></div><div class="topics-divider"><span>{len(topics)} thema’s om te ontdekken</span><span>Nieuwsgierig blijven.</span></div></div></section><section class="topics-grid-section" aria-label="Alle onderwerpen"><div class="topics-shell"><div class="topics-grid">{''.join(cards) if cards else '<p class="empty">Nog geen onderwerpen beschikbaar.</p>'}</div><p class="topics-note">Nederlandse en internationale verhalen. In elk onderwerp staat het nieuwste nieuws bovenaan.</p></div></section></main><footer>Positief nieuws · Dit gebeurt ook. · <a href="/contact/" onclick="if(window.sa_event)window.sa_event('contact_click')">Contact</a> · <a href="/tip/" onclick="if(window.sa_event)window.sa_event('tip_redactie_click')">Tip de redactie</a></footer>{analytics_html({'page_type':'topics'})}</body></html>"""


TOPIC_DOSSIER_CSS = r"""
.topic-dossier-hero{padding-bottom:46px}
.topic-dossier-hero:after{width:126px;height:126px;border-radius:50%;border:1px solid rgba(139,92,66,.15);background:transparent;box-shadow:0 0 0 22px rgba(139,92,66,.025),0 0 0 44px rgba(214,161,58,.018);top:50px}
.topic-dossier-meta{display:flex;flex-wrap:wrap;gap:9px;margin-top:24px;padding-top:12px;border-top:1px solid var(--green-dark);color:var(--green);font-size:.64rem;font-weight:800;position:relative}
.topic-dossier-meta:before{content:"";position:absolute;left:0;top:-1px;width:50px;height:2px;border-radius:999px;background:var(--accent)}
.topic-dossier-meta .sep{color:#9da49f}
.topic-signals{padding:38px 0 52px;background:#f3efe6;border-top:1px solid var(--line2);border-bottom:1px solid var(--line2)}
.topic-signals-head{display:grid;grid-template-columns:34px minmax(0,1fr);gap:12px;align-items:start;margin-bottom:22px}
.topic-signals-no{padding-top:5px;color:#999f9a;font-family:Georgia,"Times New Roman",serif;font-size:.84rem}
.topic-signals h2{margin:0;font-size:1.62rem;line-height:1.07;letter-spacing:-.04em}
.topic-signals-intro{max-width:680px;margin:9px 0 0;color:var(--muted);font-size:.87rem}
.topic-signal-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.topic-signal{position:relative;min-height:205px;padding:22px 22px 20px;border:1px solid var(--line2);background:rgba(255,255,255,.48);overflow:hidden}
.topic-signal:after{content:"";position:absolute;right:-26px;top:-28px;width:88px;height:88px;border-radius:50%;background:rgba(214,161,58,.055)}
.topic-signal-icon{display:flex;align-items:center;justify-content:center;width:42px;height:42px;margin-bottom:15px;border-radius:50%}
.topic-signal-icon svg{width:26px;height:26px}
.topic-signal:nth-child(1) .topic-signal-icon{background:#dce9df;color:#2f6d4c}
.topic-signal:nth-child(2) .topic-signal-icon{background:#e4e2ef;color:#655a87}
.topic-signal:nth-child(3) .topic-signal-icon{background:#f0e1d6;color:#9a5e3f}
.topic-signal:nth-child(4) .topic-signal-icon{background:#dbe8e8;color:#3f7172}
.topic-signal h3{margin:0;font-size:1.16rem;line-height:1.15;letter-spacing:-.025em}
.topic-signal p{margin:9px 0 0;color:#4b544e;font-size:.84rem;line-height:1.52}
.topic-signal-links{margin-top:14px;padding-top:11px;border-top:1px solid var(--line2);font-size:.68rem;line-height:1.55}
.topic-signal-links a{color:var(--green-dark);font-weight:800;text-underline-offset:3px}
.topic-signal-note{margin:18px 0 0;padding:13px 16px;border-left:3px solid rgba(31,91,69,.34);background:rgba(255,255,255,.34);color:var(--muted);font-size:.76rem;line-height:1.55}
.topic-context{padding:26px 0 0}
.topic-context-copy{max-width:720px;color:#3f4742;font-size:.92rem;line-height:1.68}
.topic-context-copy p{margin:0 0 1.05em}
.topic-archive{padding-top:48px}
.topic-archive-heading{display:flex;align-items:end;justify-content:space-between;gap:20px;padding-bottom:10px;border-bottom:1px solid var(--green-dark)}
.topic-archive-heading h2{margin:0;font-size:1.55rem;line-height:1.05;letter-spacing:-.038em}
.topic-archive-heading span{color:var(--green);font-size:.64rem;font-weight:800}
.topic-region-head{display:flex;align-items:center;gap:10px;margin-top:34px;padding-bottom:8px;border-bottom:1px solid var(--line2)}
.topic-region-head span{color:#9aa09b;font-family:Georgia,"Times New Roman",serif;font-size:.78rem}
.topic-region-head h3{margin:0;font-size:1.08rem;letter-spacing:-.02em}
.topic-why{padding:34px 0 46px;background:#edf2eb;border-top:1px solid var(--line2)}
.topic-why-box{display:grid;grid-template-columns:48px minmax(0,1fr);gap:18px;align-items:start}
.topic-why-sun{display:flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:50%;background:rgba(214,161,58,.12);color:var(--accent)}
.topic-why-sun svg{width:27px;height:27px}
.topic-why h2{margin:0;font-size:1.28rem;letter-spacing:-.028em}
.topic-why p{max-width:680px;margin:8px 0 0;color:#4b554e;font-size:.84rem}
@media(max-width:760px){
  .topic-dossier-hero{padding-bottom:32px}
  .topic-dossier-hero:after{right:-62px;top:35px;width:104px;height:104px}
  .topic-signals{padding:30px 0 38px}
  .topic-signal-grid{grid-template-columns:1fr}
  .topic-signal{min-height:0}
  .topic-context{padding-top:22px}
  .topic-archive{padding-top:38px}
  .topic-archive-heading{align-items:start}
  .topic-why-box{grid-template-columns:40px minmax(0,1fr);gap:14px}
  .topic-why-sun{width:38px;height:38px}
}
"""

TOPIC_DOSSIERS = {'Gezondheid': {'signals_title': 'Dit zien we de afgelopen weken gebeuren',
                'signals_intro': 'Geen algemene conclusie over de gezondheidszorg, wel vier lijnen die terugkomen in de verhalen die '
                                 'Positief nieuws recent selecteerde.',
                'note': 'dit is redactionele duiding op basis van verhalen die eerder op Positief nieuws zijn geselecteerd. Het is geen '
                        'medische trendanalyse en geen gezondheidsadvies. We formuleren alleen wat in meerdere recente verhalen terugkomt.',
                'why_title': 'Zo zie je sneller wat er echt verandert',
                'why_text': 'Losse nieuwsberichten vertellen wat er vandaag gebeurt. Door verhalen over langere tijd naast elkaar te '
                            'zetten, zie je ook de grotere beweging: wat werkt, waar zorg eerder kan ingrijpen en welke verbeteringen '
                            'langzaam breder beschikbaar worden. Zo hoef je niet zelf door weken aan losse artikelen heen om het grotere '
                            'plaatje te zien.',
                'signals': [{'title': 'Preventie laat soms heel meetbaar effect zien',
                             'text': "Na de nieuwe RSV-immunisatie belandden in Nederlandse ziekenhuizen veel minder baby's met het virus "
                                     'op de intensive care. Op Mauritius laten langlopende bevolkingsmetingen zien dat diabetes type 2 na '
                                     'jaren van stijging is gedaald.',
                             'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M16 4 25 8v7c0 6-3.8 10.2-9 '
                                     '13-5.2-2.8-9-7-9-13V8l9-4Z" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/><path '
                                     'd="m11.5 15 3 3 6-7" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
                                     'stroke-linejoin="round"/></svg>',
                             'links': [('RSV-immunisatie',
                                        'https://www.hartvannederland.nl/milieu-gezondheid/zorg/artikelen/babys-rs-virus-daalt-na-invoering-nieuwe-prik',
                                        True),
                                       ('Diabetes op Mauritius', '/artikelen/2026-10-01/mauritius-daling-diabetes-type-2/', False)]},
                            {'title': 'Signaleren schuift steeds verder naar voren',
                             'text': 'Bij een zeldzame kinderspierziekte bleken twee ontstekingseiwitten al ongeveer een jaar vóór een '
                                     'zichtbare opvlamming te kunnen stijgen. Dat is nog geen brede klinische test, maar wel een voorbeeld '
                                     "van zorg die risico's eerder probeert te herkennen.",
                             'icon': '<svg viewBox="0 0 32 32" fill="none"><circle cx="14" cy="14" r="8" stroke="currentColor" '
                                     'stroke-width="2.2"/><path d="m20 20 7 7M8 14h3l2-4 3 8 2-4h3" stroke="currentColor" '
                                     'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
                             'links': [('Bloedwaarden bij kinderspierziekte',
                                        '/artikelen/2026-09-28/bloedwaarden-opvlamming-kinderspierziekte-eerder-signaleren/',
                                        False)]},
                            {'title': 'Behandeling wordt gerichter — en herstel stopt niet altijd vroeg',
                             'text': 'Een fase 3-studie liet een positief effect zien van een nieuw middel bij de zeldzame erfelijke vorm '
                                     'FUS-ALS. En bij jonge volwassenen met aanhoudende knieklachten bleek intensieve revalidatie zelfs '
                                     'één tot drie jaar na een kruisbandoperatie nog verbetering te kunnen geven.',
                             'icon': '<svg viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="11" stroke="currentColor" '
                                     'stroke-width="2"/><circle cx="16" cy="16" r="5.5" stroke="currentColor" stroke-width="2"/><path '
                                     'd="M16 5v5M16 22v5M5 16h5M22 16h5" stroke="currentColor" stroke-width="2.2" '
                                     'stroke-linecap="round"/><circle cx="16" cy="16" r="1.8" fill="currentColor" stroke="none"/></svg>',
                             'links': [('FUS-ALS', 'https://www.als.nl/nieuws/goed-nieuws-als-onderzoek/', True),
                                       ('Kruisbandrevalidatie',
                                        '/artikelen/2026-10-01/gerichte-revalidatie-jaren-na-kruisbandoperatie/',
                                        False)]},
                            {'title': 'Vooruitgang gaat niet alleen over nieuwe medicijnen',
                             'text': 'WHO breidde bewezen anticonceptie-opties uit en publiceerde een strategie om kinderkankermedicijnen '
                                     'betrouwbaarder beschikbaar te maken. Zambia digitaliseert ondertussen vaccinvoorraden, zodat '
                                     'tekorten sneller zichtbaar worden.',
                             'icon': '<svg viewBox="0 0 32 32" fill="none"><rect x="5" y="8" width="10" height="16" rx="2" '
                                     'stroke="currentColor" stroke-width="2"/><rect x="17" y="8" width="10" height="16" rx="2" '
                                     'stroke="currentColor" stroke-width="2"/><path d="M10 13v6M7 16h6M22 12v8M19 16h6M15 16h2" '
                                     'stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
                             'links': [('Anticonceptie',
                                        'https://www.who.int/news/item/23-09-2026-who-expands-safe-options-for-contraception',
                                        True),
                                       ('Kinderkankermedicijnen', 'https://www.who.int/publications/i/item/9789240125087', True),
                                       ('Vaccinvoorraad Zambia',
                                        'https://www.unicef.org/zambia/stories/paper-records-real-time-decision',
                                        True)]}]},
 'Cultuur': {'signals_title': 'Dit zien we de afgelopen weken gebeuren',
             'signals_intro': 'Vier lijnen die terugkomen in recente verhalen over cultuur, erfgoed en media.',
             'why_title': 'Zo zie je cultuur als beweging, niet als losse agenda',
             'why_text': 'Door cultuurverhalen naast elkaar te zetten, zie je meer dan prijzen en vondsten alleen: hoe erfgoed opnieuw '
                         'wordt ontdekt, vrijwilligers culturele plekken dragen en Nederlandse makers en formats ook buiten de '
                         'landsgrenzen opvallen.',
             'signals': [{'title': 'Erfgoed blijft nieuwe verhalen prijsgeven',
                          'text': 'Een zeldzaam fragment van Homerus’ Odyssee dook op in Utrecht, terwijl een vondst van Vikingsilver in '
                                  'Finland nieuwe historische informatie opleverde. Oude bronnen blijken nog steeds letterlijk nieuwe '
                                  'kennis te bevatten.',
                          'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M6 7h8c3 0 5 2 5 5v14c0-3-2-5-5-5H6V7Zm20 0h-8c-3 0-5 2-5 '
                                  '5" stroke="currentColor" stroke-width="2.1" stroke-linejoin="round"/></svg>',
                          'links': [('Odyssee-fragment',
                                     'https://www.uu.nl/nieuws/vierde-eeuws-fragment-van-de-odyssee-ontdekt-in-universiteitsbibliotheek-utrecht',
                                     True),
                                    ('Vikingsilver in Finland',
                                     'https://www.smithsonianmag.com/smart-news/a-finnish-metal-detectorist-was-shocked-to-unearth-a-trove-of-viking-age-silver-in-his-hometown-then-his-detector-went-off-again-180989487/',
                                     True)]},
                         {'title': 'Culturele inzet krijgt zichtbare waardering',
                          'text': 'De Brabant Bokaal voor Willy Koppens onderstreept hoeveel cultureel aanbod leunt op jarenlange '
                                  'vrijwillige inzet. Zulke erkenning maakt zichtbaar dat cultuur niet alleen door instellingen, maar ook '
                                  'door betrokken inwoners wordt gedragen.',
                          'icon': '<svg viewBox="0 0 32 32" fill="none"><circle cx="16" cy="12" r="7" stroke="currentColor" '
                                  'stroke-width="2.1"/><path d="m12 18-2 9 6-4 6 4-2-9" stroke="currentColor" stroke-width="2.1" '
                                  'stroke-linejoin="round"/></svg>',
                          'links': [('Brabant Bokaal',
                                     'https://www.omroepbrabant.nl/nieuws/6024314/willy-koppens-wint-brabant-bokaal',
                                     True)]},
                         {'title': 'Nederlandse formats vinden publiek over de grens',
                          'text': 'De Grannies van Amsterdam werd bij het EBU Formats Forum uitgeroepen tot Format of the Year. Dat laat '
                                  'zien dat een uitgesproken lokaal programma ook internationaal als vernieuwend en aansprekend kan worden '
                                  'gezien.',
                          'icon': '<svg viewBox="0 0 32 32" fill="none"><rect x="5" y="7" width="22" height="15" rx="2" '
                                  'stroke="currentColor" stroke-width="2.1"/><path d="M11 27h10M16 22v5" stroke="currentColor" '
                                  'stroke-width="2.1" stroke-linecap="round"/></svg>',
                          'links': [('De Grannies van Amsterdam',
                                     'https://www.rtl.nl/boulevard/artikel/5649889/internationale-prijs-voor-de-grannies-van-amsterdam',
                                     True)]},
                         {'title': 'Cultuur wordt sterker als mensen zelf blijven meedoen',
                          'text': 'Van filmfestival tot museum en van lokale geschiedenis tot televisie: meerdere verhalen laten zien dat '
                                  'cultuur groeit wanneer makers, vrijwilligers en publiek niet alleen consumeren, maar ook actief '
                                  'bijdragen.',
                          'icon': '<svg viewBox="0 0 32 32" fill="none"><circle cx="11" cy="11" r="4" stroke="currentColor" '
                                  'stroke-width="2"/><circle cx="22" cy="12" r="3.5" stroke="currentColor" stroke-width="2"/><path d="M4 '
                                  '27c1-7 4-11 8-11s7 4 8 11M18 27c1-5 3-8 6-8s5 3 6 8" stroke="currentColor" stroke-width="2" '
                                  'stroke-linecap="round"/></svg>',
                          'links': [('Willy Koppens',
                                     'https://www.omroepbrabant.nl/nieuws/6024314/willy-koppens-wint-brabant-bokaal',
                                     True),
                                    ('De Grannies',
                                     'https://www.rtl.nl/boulevard/artikel/5649889/internationale-prijs-voor-de-grannies-van-amsterdam',
                                     True)]}]},
 'Economie': {'signals_title': 'Dit zien we de afgelopen weken gebeuren',
              'signals_intro': 'Vier economische signalen uit recente edities, van koopkracht tot handel en bredere groei.',
              'why_title': 'Zo krijg je meer gevoel voor richting dan met één groeicijfer',
              'why_text': 'Economie wordt snel gereduceerd tot één percentage. Door meerdere indicatoren naast elkaar te zetten, zie je '
                          'beter of groei ook terugkomt bij huishoudens, handel en andere economieën — en waar de nuance blijft zitten.',
              'signals': [{'title': 'De Nederlandse economie groeide sterker dan eerder gedacht',
                           'text': 'De economie groeide in het tweede kwartaal met 0,6 procent. Tegelijk namen volgens de geselecteerde '
                                   'cijfers zowel het besteedbaar inkomen van huishoudens als de bedrijfswinsten toe.',
                           'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M5 26V7M5 26h22M9 22l5-6 4 3 8-10" stroke="currentColor" '
                                   'stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
                           'links': [('Nederlandse economie',
                                      'https://nos.nl/artikel/2632133-economie-draait-verrassend-goed-huishoudens-meer-te-besteden-bedrijven-betere-winst',
                                      True)]},
                          {'title': 'Koopkracht ging voor het derde jaar op rij omhoog',
                           'text': 'De koopkracht van Nederlanders steeg in 2025 in doorsnee met 1,2 procent. Werknemers gingen gemiddeld '
                                   'sterker vooruit dan zelfstandigen en gepensioneerden, dus het herstel was niet voor iedereen even '
                                   'groot.',
                           'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M5 9h19a3 3 0 0 1 3 3v13H5V9Z" stroke="currentColor" '
                                   'stroke-width="2.1"/><path d="M5 9 21 5v4M20 15h7v6h-7a3 3 0 0 1 0-6Z" stroke="currentColor" '
                                   'stroke-width="2.1" stroke-linejoin="round"/></svg>',
                           'links': [('Koopkracht 2025',
                                      'https://www.cbs.nl/nl-nl/nieuws/2026/38/koopkracht-stijgt-met-1-2-procent-in-2025-werknemers-zien-sterkste-toename',
                                      True)]},
                          {'title': 'Ook de Nederlandse export bleef groeien',
                           'text': 'De goederenexport lag in juli ruim 2 procent hoger dan een jaar eerder. Daarmee kwam naast '
                                   'binnenlandse groei ook vanuit de handel een positief signaal.',
                           'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="m6 11 10-5 10 5-10 5-10-5Z" stroke="currentColor" '
                                   'stroke-width="2.1" stroke-linejoin="round"/><path d="M6 11v11l10 5 10-5V11M16 16v11" '
                                   'stroke="currentColor" stroke-width="2.1" stroke-linejoin="round"/></svg>',
                           'links': [('Export in juli',
                                      'https://www.cbs.nl/nl-nl/nieuws/2026/37/export-groeit-met-ruim-2-procent-in-juli',
                                      True)]},
                          {'title': 'Internationaal is het beeld gemengd, maar niet stilstaand',
                           'text': 'In de OECD als geheel trok de kwartaalgroei in het tweede kwartaal licht aan van 0,4 naar 0,5 procent. '
                                   'Achter dat gemiddelde zitten grote verschillen tussen landen, maar het onderstreept dat groei breder '
                                   'zichtbaar was dan alleen in Nederland.',
                           'icon': '<svg viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="11" stroke="currentColor" '
                                   'stroke-width="2.1"/><path d="M5 16h22M16 5c4 4 5 8 5 11s-1 7-5 11M16 5c-4 4-5 8-5 11s1 7 5 11" '
                                   'stroke="currentColor" stroke-width="1.8"/></svg>',
                           'links': [('OECD-groei Q2',
                                      'https://www.oecd.org/en/data/insights/statistical-releases/2026/08/gdp-growth-second-quarter-2026-oecd.html',
                                      True)]}]},
 'Energie & innovatie': {'signals_title': 'Dit zien we de afgelopen weken gebeuren',
                         'signals_intro': 'Vier lijnen waarin innovatie zichtbaar opschuift van idee naar toepassing.',
                         'why_title': 'Zo zie je welke innovatie echt dichter bij gebruik komt',
                         'why_text': 'Niet ieder technisch experiment verandert meteen de wereld. Door vooral te kijken naar pilots, '
                                     'infrastructuur en opschaling zie je welke ideeën een stap verder komen richting dagelijks gebruik.',
                         'signals': [{'title': 'Testen en opschalen komen dichter bij elkaar',
                                      'text': 'Wageningen University & Research opende CIBIA en TNO een proeffabriek voor biobased '
                                              'bouwmaterialen. Beide faciliteiten zijn juist bedoeld om de kloof tussen onderzoek, testen '
                                              'en toepassing kleiner te maken.',
                                      'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M12 5h8M14 5v8L7 25h18l-7-12V5" '
                                              'stroke="currentColor" stroke-width="2.1" stroke-linecap="round" '
                                              'stroke-linejoin="round"/><path d="M11 21h10" stroke="currentColor" '
                                              'stroke-width="2.1"/></svg>',
                                      'links': [('CIBIA Wageningen',
                                                 '/artikelen/2026-10-01/cibia-wageningen-voedselinnovaties-praktijk/',
                                                 False),
                                                ('BioBuilt TNO',
                                                 'https://www.tno.nl/nl/newsroom/2026/09/minister-opent-tno-biobuilt-proeffabriek/',
                                                 True)]},
                                     {'title': 'Duurzamere mobiliteit wordt ook infrastructuurbeleid',
                                      'text': 'Een akkoord over de snelfietsroute tussen Utrecht en Amsterdam laat zien dat duurzame '
                                              'mobiliteit niet alleen om voertuigen draait, maar ook om comfortabele verbindingen die '
                                              'daadwerkelijk gebruikt kunnen worden.',
                                      'icon': '<svg viewBox="0 0 32 32" fill="none"><circle cx="8" cy="22" r="5" stroke="currentColor" '
                                              'stroke-width="2"/><circle cx="24" cy="22" r="5" stroke="currentColor" '
                                              'stroke-width="2"/><path d="m8 22 6-10 5 10H8Zm6-10h6l4 10M12 8h5" stroke="currentColor" '
                                              'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
                                      'links': [('Snelfietsroute Utrecht–Amsterdam',
                                                 'https://nos.nl/artikel/2631884-snelfietsroute-van-dom-tot-dam-tussen-utrecht-en-amsterdam-stap-dichterbij',
                                                 True)]},
                                     {'title': 'Rekenkracht wordt toegankelijker voor kleinere bedrijven',
                                      'text': 'Met Supercomputing Brabant krijgen startups en mkb-bedrijven toegang tot krachtige '
                                              'AI-rekencapaciteit en expertise. Daarmee komt infrastructuur die normaal vooral voor grote '
                                              'partijen bereikbaar is dichter bij regionale bedrijven.',
                                      'icon': '<svg viewBox="0 0 32 32" fill="none"><rect x="8" y="8" width="16" height="16" rx="2" '
                                              'stroke="currentColor" stroke-width="2"/><path d="M12 12h8v8h-8zM3 11h5M3 16h5M3 21h5M24 '
                                              '11h5M24 16h5M24 21h5M11 3v5M16 3v5M21 3v5M11 24v5M16 24v5M21 24v5" stroke="currentColor" '
                                              'stroke-width="1.8" stroke-linecap="round"/></svg>',
                                      'links': [('Supercomputing Brabant',
                                                 'https://www.omroepbrabant.nl/nieuws/6028408/supercomputing-brabant-gelanceerd-voor-ai-innovatie',
                                                 True)]},
                                     {'title': 'Energieverbetering zit vaak in het systeem rond de techniek',
                                      'text': 'MIT rapporteerde minder energiegebruik per vierkante meter en meer zonne-energie op daken. '
                                              'In Oekraïne richt een nieuwe faciliteit zich juist op het laatste stuk: zorgen dat '
                                              'beschikbare energieapparatuur ook echt wordt ontworpen, aangesloten en in gebruik genomen.',
                                      'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M5 26V7M5 26h22M9 22l5-6 4 3 8-10" '
                                              'stroke="currentColor" stroke-width="2.3" stroke-linecap="round" '
                                              'stroke-linejoin="round"/></svg>',
                                      'links': [('MIT campus',
                                                 'https://news.mit.edu/2026/mit-makes-progress-campus-climate-goals-0915',
                                                 True),
                                                ('Energie-installatie Oekraïne',
                                                 '/artikelen/2026-10-01/oekraine-energieapparatuur-sneller-installeren-undp/',
                                                 False)]}]},
 'Mens': {'signals_title': 'Dit zien we de afgelopen weken gebeuren',
          'signals_intro': 'Vier lijnen waarin meedoen, praktische hulp en lokale gemeenschap centraal staan.',
          'why_title': 'Zo zie je welke maatschappelijke oplossingen mensen echt bereiken',
          'why_text': 'Maatschappelijke vooruitgang zit vaak niet in één grote maatregel, maar in concrete drempels die verdwijnen: tijd, '
                      'geld, toegang of een plek om mee te doen. Door die verhalen samen te bekijken wordt dat patroon zichtbaar.',
          'signals': [{'title': 'Meedoen blijft mogelijk als we kijken naar wat iemand wél kan',
                       'text': 'DemenTalent koppelt mensen met dementie aan passend vrijwilligerswerk. Het uitgangspunt verschuift daarmee '
                               'van alleen zorg ontvangen naar een rol houden, mensen ontmoeten en zelf iets bijdragen.',
                       'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M5 17c4 0 5 3 8 3h6c2 0 3 1 3 3s-2 3-4 3h-7c-3 0-5-2-7-4M27 '
                               '15c-4 0-5 3-8 3h-4" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/><path d="M12 10c0-3 '
                               '2-5 4-5s4 2 4 5c0 4-4 6-4 6s-4-2-4-6Z" stroke="currentColor" stroke-width="2.1"/></svg>',
                       'links': [('DemenTalent', '/artikelen/2026-10-01/dementalent-vrijwilligerswerk-mensen-met-dementie/', False)]},
                      {'title': 'Kleine financiële drempels kunnen grote gevolgen hebben',
                       'text': 'Praktijkscholen krijgen meer ruimte om leerlingen te helpen met zaken als werkschoenen, vervoer of een '
                               'VOG. Juist zulke relatief kleine kosten kunnen anders een stage of opleiding blokkeren.',
                       'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="m4 12 12-6 12 6-12 6-12-6Z" stroke="currentColor" '
                               'stroke-width="2.1" stroke-linejoin="round"/><path d="M9 15v8c4 3 10 3 14 0v-8M28 12v9" '
                               'stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/></svg>',
                       'links': [('Praktijkscholen',
                                  'https://www.jeugdeducatiefonds.nl/actueel/honderd-praktijkscholen-krijgen-extra-budget-om-geldzorgen-van-leerlingen-weg-te-nemen',
                                  True)]},
                      {'title': 'Buurtoplossingen kunnen tegelijk sociaal én praktisch werken',
                       'text': 'De Rotterdamse buurtkoelkast helpt mensen met een kleine beurs en voorkomt voedselverspilling. Na jaren '
                               'gebruik komen er extra locaties bij — een teken dat een klein lokaal initiatief kan doorgroeien.',
                       'icon': '<svg viewBox="0 0 32 32" fill="none"><rect x="9" y="4" width="14" height="24" rx="2" stroke="currentColor" '
                               'stroke-width="2.1"/><path d="M9 13h14M13 8v2M13 17v3" stroke="currentColor" stroke-width="2.1" '
                               'stroke-linecap="round"/></svg>',
                       'links': [('Buurtkoelkast Rotterdam',
                                  'https://eenvandaag.avrotros.nl/artikelen/eten-delen-en-verspilling-tegengaan-rotterdamse-buurtkoelkast-groot-succes-164827',
                                  True)]},
                      {'title': 'Laagdrempelige hulp schuift dichter naar de leefwereld van mensen',
                       'text': 'Bladel maakt geld vrij voor een herstelcentrum waar mensen zonder zware toegangsdrempels aan herstel '
                               'kunnen werken. Dat past bij een bredere lijn waarin ondersteuning eerder en dichterbij wordt '
                               'georganiseerd.',
                       'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M16 27C7 21 5 16 5 11c0-4 3-7 7-7 2 0 4 1 5 3 1-2 3-3 5-3 4 '
                               '0 7 3 7 7 0 5-4 10-13 16Z" stroke="currentColor" stroke-width="2.1" stroke-linejoin="round"/></svg>',
                       'links': [('Herstelzorg Bladel', '/artikelen/2026-10-01/bladel-subsidie-laagdrempelige-herstelzorg/', False)]}]},
 'Natuur & klimaat': {'signals_title': 'Dit zien we de afgelopen weken gebeuren',
                      'signals_intro': 'Vier lijnen waarin bescherming, herstel en slimmer samenleven met natuur terugkomen.',
                      'why_title': 'Zo zie je dat natuurherstel meestal tijd, bescherming én slimme keuzes vraagt',
                      'why_text': 'Een losse natuurfoto zegt weinig over structurele vooruitgang. Door herstelprojecten, '
                                  'soortenbescherming en nieuwe meetmethoden samen te volgen, wordt duidelijker welke aanpakken echt '
                                  'resultaat beginnen te geven.',
                      'signals': [{'title': 'Bescherming kan ecosystemen jaren later zichtbaar veranderen',
                                   'text': 'Na tien jaar bescherming tegen zware bodemberoering herstelde de zeebodem rond de Schotse '
                                           'Summer Isles zichtbaar. Ook langdurig herstel van oesterriffen liet positieve resultaten zien.',
                                   'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M5 25C8 10 17 5 27 5c0 11-6 20-19 22" '
                                           'stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/><path '
                                           'd="M8 25c6-7 11-11 18-17" stroke="currentColor" stroke-width="2.1" '
                                           'stroke-linecap="round"/></svg>',
                                   'links': [('Schotse zeebodem', '/artikelen/2026-10-01/summer-isles-zeeherstel-na-baggerverbod/', False),
                                             ('Oesterriffen', 'https://phys.org/news/2026-09-term-oyster-reef-success-murky.html', True)]},
                                  {'title': 'Technologie kan natuur en menselijke activiteit beter naast elkaar laten bestaan',
                                   'text': 'Slimme radar bij windturbines volgt vleermuizen in real time, terwijl geschilderde ogen op vee '
                                           'roofdieren lijken af te schrikken. Twee heel verschillende voorbeelden van gerichter ingrijpen '
                                           'in plaats van grofweg alles stilleggen of bestrijden.',
                                   'icon': '<svg viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="3" stroke="currentColor" '
                                           'stroke-width="2"/><path d="M16 5a11 11 0 0 1 11 11M16 9a7 7 0 0 1 7 7M16 16l8-8M5 27h22" '
                                           'stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
                                   'links': [('Vleermuisradar',
                                              'https://www.tno.nl/nl/newsroom/insights/2026/09/slimme-radar-beschermt-vleermuizen/',
                                              True),
                                             ('Geschilderde ogen op vee',
                                              '/artikelen/2026-10-01/geschilderde-ogen-vee-roofdieren-zimbabwe/',
                                              False)]},
                                  {'title': 'Bedreigde soorten kunnen weer terrein winnen',
                                   'text': 'Nieuw-Zeeland telde een recordaantal kākāpō-kuikens. In Schotland brachten nieuwe '
                                           'luchtmetingen miljoenen jonge bomen in kaart. Zulke verhalen verschillen sterk, maar hebben '
                                           'gemeen dat herstel meetbaar wordt.',
                                   'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M5 20c6 1 9-2 11-6 3 4 7 5 11 4-3 7-9 9-15 '
                                           '7-3-1-5-3-7-5Z" stroke="currentColor" stroke-width="2.1" stroke-linejoin="round"/><path d="m20 '
                                           '12 3-4 1 5" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/></svg>',
                                   'links': [('Kākāpō',
                                              'https://www.smithsonianmag.com/smart-news/new-zealand-welcomes-a-record-90-kakapo-chicks-helping-the-worlds-chunkiest-parrot-species-rebound-from-the-brink-of-extinction-180989511/',
                                              True),
                                             ('Bosherstel Schotland',
                                              'https://phys.org/news/2026-09-aerial-reveal-successful-woodland-expansion.html',
                                              True)]},
                                  {'title': 'We worden beter in zien waar natuur veerkrachtig is',
                                   'text': 'Een wereldwijde analyse bracht in kaart waar grondwater na droogte relatief goed herstelt. '
                                           'Groene daken laten ondertussen zien dat ook steden extra leefruimte voor soorten kunnen '
                                           'bieden.',
                                   'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M16 4C11 11 8 15 8 20a8 8 0 0 0 16 '
                                           '0c0-5-3-9-8-16Z" stroke="currentColor" stroke-width="2.1"/><path d="M12 21c1 2 2 3 4 3" '
                                           'stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/></svg>',
                                   'links': [('Grondwater na droogte',
                                              '/artikelen/2026-10-01/wereldwijde-analyse-herstel-grondwater-na-droogte/',
                                              False),
                                             ('Groene daken',
                                              'https://www.wur.nl/en/activity/biodivercity-succession-green-roof-ecosystems',
                                              True)]}]},
 'Wetenschap': {'signals_title': 'Dit zien we de afgelopen weken gebeuren',
                'signals_intro': 'Vier lijnen waarin nieuwe meetmethoden, AI en ruimteonderzoek het zicht op complexe systemen vergroten.',
                'why_title': 'Zo zie je hoe wetenschap stap voor stap meer zichtbaar en meetbaar maakt',
                'why_text': 'Wetenschappelijke vooruitgang is vaak geen eureka-moment maar een betere meting, slimmer model of '
                            'nauwkeuriger instrument. Door die verhalen naast elkaar te zetten zie je hoe kennis zich praktisch opbouwt.',
                'signals': [{'title': 'AI wordt steeds vaker een onderzoeksinstrument',
                             'text': 'Virtuele cellen met 4D-AI kunnen reacties op medicijnen voorspellen en AI helpt microscopen sneller '
                                     'relevante nanoschaaldetails te vinden. De gemene deler: minder zoeken op goed geluk, meer gericht '
                                     'meten.',
                             'icon': '<svg viewBox="0 0 32 32" fill="none"><circle cx="11" cy="12" r="6" stroke="currentColor" '
                                     'stroke-width="2"/><circle cx="21" cy="20" r="7" stroke="currentColor" stroke-width="2"/><circle '
                                     'cx="10" cy="11" r="1.5" fill="currentColor"/><circle cx="22" cy="19" r="2" '
                                     'fill="currentColor"/></svg>',
                             'links': [('Virtuele cellen', 'https://phys.org/news/2026-09-virtual-cells-built-4d-ai.html', True),
                                       ('AI-microscopie',
                                        'https://phys.org/news/2026-09-ai-microscopes-nanoscale-features-sample.html',
                                        True)]},
                            {'title': 'Ruimtemissies halen meer informatie uit slimme navigatie',
                             'text': 'Juice gebruikte een aardpassage om met weinig brandstof beter op koers te komen naar Jupiter. '
                                     'Perseverance vond op Mars tegelijk aanwijzingen voor een complexer oud watersysteem dan eerder '
                                     'gedacht.',
                             'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M18 5c5 1 8 4 9 9l-8 8-9-9 8-8Z" stroke="currentColor" '
                                     'stroke-width="2.1" stroke-linejoin="round"/><circle cx="20" cy="12" r="2" stroke="currentColor" '
                                     'stroke-width="1.8"/><path d="m11 19-5 2 5-8M18 22l-2 5 8-5M8 24l-2 2" stroke="currentColor" '
                                     'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/></svg>',
                             'links': [('Juice', '/artikelen/2026-10-01/juice-aardpassage-koers-jupiter/', False),
                                       ('Water op Mars',
                                        'https://www.nasa.gov/solar-system/planets/mars/nasa-discovery-reveals-complex-water-systems-on-early-mars/',
                                        True)]},
                            {'title': 'Techniek helpt expertise toegankelijker te maken',
                             'text': "Slimme beeldbegeleiding hielp onervaren gebruikers betere trauma-echo's te maken. Bij paarden wordt "
                                     'AI onderzocht om subtiele bewegingsafwijkingen en mogelijke kreupelheid eerder te herkennen.',
                             'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="M5 11V6h5M22 6h5v5M27 21v5h-5M10 26H5v-5" '
                                     'stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/><path d="M9 17h4l2-5 4 10 2-5h3" '
                                     'stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/></svg>',
                             'links': [('Trauma-echo',
                                        'https://medicalxpress.com/news/2026-09-anatomical-guidance-novice-users-trauma.html',
                                        True),
                                       ('AI en kreupelheid',
                                        'https://www.uu.nl/nieuws/is-mijn-paard-kreupel-ai-kan-helpen-bij-het-vinden-van-het-antwoord',
                                        True)]},
                            {'title': 'Laboratoriummodellen worden realistischer, maar nuance blijft nodig',
                             'text': 'Onderzoek met een kunstmatige darm liet zien hoe stoffen uit blauwe bessen en bramen een '
                                     'ontstekingsreactie kunnen beïnvloeden. Zulke modellen geven nieuwe aanwijzingen, zonder dat daarmee '
                                     'meteen een effect bij mensen is bewezen.',
                             'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="m13 5 5 5-4 4-5-5 4-4ZM15 13c4 2 6 5 6 8M8 27h18M11 '
                                     '22h13M9 9l-3 5 5 5" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" '
                                     'stroke-linejoin="round"/></svg>',
                             'links': [('Kunstmatige darm',
                                        'https://www.wur.nl/nl/nieuws/blauwe-bessen-en-bramen-remmen-ontstekingsreactie-kunstmatige-darm',
                                        True)]}]},
 'Sport': {'signals_title': 'Dit zien we de afgelopen weken gebeuren',
           'signals_intro': 'Vier lijnen waarin prestaties, professionalisering en sportinfrastructuur elkaar versterken.',
           'why_title': 'Zo zie je sport als meer dan alleen de uitslag van vandaag',
           'why_text': 'Records en titels zijn momentopnames. Door ook investeringen, evenementen en professionalisering mee te nemen zie '
                       'je wat er achter prestaties verandert — en waarom sommige ontwikkelingen langer meegaan dan één wedstrijd.',
           'signals': [{'title': 'Vrouwenvoetbal groeit door structurele investering',
                        'text': 'Clubs in Engeland en de Verenigde Staten investeren in eigen stadions, trainingscomplexen en '
                                'vrouwengezondheid. Dat maakt de groei van vrouwenvoetbal minder afhankelijk van incidenteel succes.',
                        'icon': '<svg viewBox="0 0 32 32" fill="none"><ellipse cx="16" cy="17" rx="11" ry="7" stroke="currentColor" '
                                'stroke-width="2"/><ellipse cx="16" cy="17" rx="6" ry="3" stroke="currentColor" stroke-width="2"/><path '
                                'd="M5 17v6c0 4 22 4 22 0v-6" stroke="currentColor" stroke-width="2"/></svg>',
                        'links': [('Investeringen vrouwenvoetbal',
                                   'https://nos.nl/artikel/2631231-zo-maken-engeland-en-de-vs-vrouwenvoetbal-groot-van-eigen-stadion-tot-beautyruimtes',
                                   True)]},
                       {'title': 'Vrouwen blijven oude records aanscherpen',
                        'text': 'Bij de Dam tot Damloop sneuvelde een vrouwenrecord dat 39 jaar had standgehouden. Eerder verbeterde Femke '
                                'Broeders-Bol haar eigen Nederlandse record op de 800 meter fors.',
                        'icon': '<svg viewBox="0 0 32 32" fill="none"><circle cx="16" cy="18" r="10" stroke="currentColor" '
                                'stroke-width="2.1"/><path d="M13 4h6M16 8V4M24 10l3-3M16 18l5-4" stroke="currentColor" stroke-width="2.1" '
                                'stroke-linecap="round"/></svg>',
                        'links': [('Dam tot Damloop',
                                   'https://nos.nl/artikel/2631728-ethiopische-ayichew-verbreekt-39-jaar-oud-parcoursrecord-dam-tot-damloop',
                                   True),
                                  ('800 meter', 'https://nos.nl/l/2628564', True)]},
                       {'title': 'Nederlandse teams blijven internationaal meedoen om prijzen',
                        'text': 'De Nederlandse 3x3-basketbalsters werden opnieuw Europees kampioen. Zulke prestaties laten zien dat '
                                "succes niet alleen op individueel niveau, maar ook in teamprogramma's terugkomt.",
                        'icon': '<svg viewBox="0 0 32 32" fill="none"><path d="m10 4 6 9 6-9M22 4l-6 9-6-9" stroke="currentColor" '
                                'stroke-width="2.1" stroke-linejoin="round"/><circle cx="16" cy="21" r="7" stroke="currentColor" '
                                'stroke-width="2.1"/></svg>',
                        'links': [('3x3-basketbal', 'https://nos.nl/l/2630825', True)]},
                       {'title': 'Grote sportevenementen worden breder en inclusiever georganiseerd',
                        'text': 'Groningen en Drenthe kregen het WK wielrennen én para-cycling van 2034 toegewezen. Dat koppelt een groot '
                                'internationaal evenement expliciet aan zowel reguliere als aangepaste sport.',
                        'icon': '<svg viewBox="0 0 32 32" fill="none"><circle cx="8" cy="22" r="5" stroke="currentColor" '
                                'stroke-width="2"/><circle cx="24" cy="22" r="5" stroke="currentColor" stroke-width="2"/><path d="m8 22 '
                                '6-10 5 10H8Zm6-10h6l4 10M12 8h5" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
                                'stroke-linejoin="round"/></svg>',
                        'links': [('WK wielrennen en para-cycling',
                                   'https://gemeente.groningen.nl/wk-wielrennen-en-para-cycling-naar-groningen-en-drenthe-2034',
                                   True)]}]}}

def render_topic_signals(label):
    dossier = TOPIC_DOSSIERS.get(label) or {}
    signals = dossier.get("signals") or []
    if not signals:
        return ""

    cards = []
    for signal in signals:
        links = []
        for link_label, href, external in signal.get("links", []):
            attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
            links.append(f'<a href="{esc(href)}"{attrs}>{esc(link_label)}</a>')
        links_html = '&nbsp;·&nbsp;'.join(links)
        card = f"""<article class="topic-signal">
          <div class="topic-signal-icon" aria-hidden="true">{signal.get("icon","")}</div>
          <h3>{esc(signal.get("title",""))}</h3>
          <p>{esc(signal.get("text",""))}</p>
          {f'<div class="topic-signal-links">{links_html}</div>' if links_html else ''}
        </article>"""
        cards.append(card)

    note = dossier.get("note") or (
        "dit is redactionele duiding op basis van verhalen die eerder op Positief nieuws zijn geselecteerd. "
        "We formuleren alleen wat in meerdere recente verhalen terugkomt."
    )

    return f"""
    <section class="topic-signals">
      <div class="shell">
        <div class="topic-signals-head">
          <span class="topic-signals-no">01</span>
          <div>
            <h2>{esc(dossier.get("signals_title") or "Dit zien we de afgelopen weken gebeuren")}</h2>
            <p class="topic-signals-intro">{esc(dossier.get("signals_intro") or "Lijnen die terugkomen in de verhalen die Positief nieuws recent selecteerde.")}</p>
          </div>
        </div>
        <div class="topic-signal-grid">{''.join(cards)}</div>
        <p class="topic-signal-note"><strong>Hoe dit blok werkt:</strong> {esc(note)}</p>
      </div>
    </section>
    """

def render_topic_why(label):
    dossier = TOPIC_DOSSIERS.get(label) or {}
    why_title = dossier.get("why_title") or "Zo zie je sneller wat er echt verandert"
    why_text = dossier.get("why_text") or (
        f"Losse nieuwsberichten laten zien wat er op één moment gebeurt. Door verhalen over {label.lower()} "
        "over langere tijd bij elkaar te zetten, zie je sneller welke ontwikkelingen terugkomen en waar daadwerkelijk beweging ontstaat. "
        "Zo hoef je niet zelf door weken aan losse artikelen heen om het grotere plaatje te zien."
    )
    return f"""
    <section class="topic-why">
      <div class="shell topic-why-box">
        <div class="topic-why-sun" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="4.2" fill="currentColor"/>
            <path d="M12 2v3M12 19v3M22 12h-3M5 12H2M19 5l-2 2M7 17l-2 2M19 19l-2-2M7 7 5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
        </div>
        <div>
          <h2>{esc(why_title)}</h2>
          <p>{esc(why_text)}</p>
        </div>
      </div>
    </section>
    """

def render_topic_page(topic):
    label = topic["label"]
    slug = topic["slug"]
    canonical = f"{SITE_URL}/{slug}/"

    seo = TOPIC_SEO.get(label, {})
    title = seo.get("title") or f"Positief nieuws over {label.lower()} | Positief nieuws"
    h1 = seo.get("h1") or label
    if h1.lower().startswith("positief nieuws over "):
        h1 = label
    desc = seo.get("description") or (
        f"Lees positief nieuws over {label.lower()}. "
        "Nederlandse en internationale verhalen, met de nieuwste ontwikkelingen bovenaan."
    )
    lead = seo.get("lead") or desc
    intro = seo.get("intro") or [desc]
    total = len(topic["nl"]) + len(topic["int"])
    updated = fmt_date_short(topic["latest"]) if topic.get("latest") else ""

    nl_html = "\n".join(article_html(x["item"], x["date"], True, "nl") for x in topic["nl"])
    int_html = "\n".join(article_html(x["item"], x["date"], True, "int") for x in topic["int"])

    regions = []
    if topic["nl"]:
        regions.append(
            f'<div class="topic-region-head"><span>01</span><h3>Nederland</h3></div>{nl_html}'
        )
    if topic["int"]:
        regions.append(
            f'<div class="topic-region-head"><span>02</span><h3>Wereld</h3></div>{int_html}'
        )

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title.replace(" | Positief nieuws", ""),
        "description": desc,
        "url": canonical,
        "about": {"@type": "Thing", "name": label},
        "isPartOf": {"@type": "WebSite", "name": "Positief nieuws", "url": SITE_URL + "/"}
    }, ensure_ascii=False)

    signals_html = render_topic_signals(label)
    intro_html = "".join(f"<p>{esc(paragraph)}</p>" for paragraph in intro)
    context_html = ""
    if not signals_html:
        context_html = f"""
        <section class="topic-context">
          <div class="shell">
            <div class="topic-context-copy">{intro_html}</div>
          </div>
        </section>
        """

    archive_title = f"Het laatste positieve nieuws over {label.lower()}"

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
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="Positief nieuws">
  <meta name="twitter:card" content="summary">
  <meta name="theme-color" content="#17382b">
  <script type="application/ld+json">{schema}</script>
  <style>{BASE_CSS}{TOPIC_DOSSIER_CSS}</style>
</head>
<body>
  {header_html('topics')}
  <main>
    <section class="hero topic-dossier-hero">
      <div class="shell">
        <p class="kicker">Onderwerp · dossier</p>
        <h1>{esc(h1)}</h1>
        <p class="lead">{esc(lead)}</p>
        <div class="topic-dossier-meta">
          <span>{total} recente {'verhalen' if total != 1 else 'verhaal'}</span>
          <span class="sep">·</span>
          <span>Nederland + wereld</span>
          {f'<span class="sep">·</span><span>Bijgewerkt {esc(updated)}</span>' if updated else ''}
        </div>
      </div>
    </section>

    {signals_html}
    {context_html}

    <section class="section topic-archive">
      <div class="shell">
        <div class="topic-archive-heading">
          <h2>{esc(archive_title)}</h2>
          <span>Van nieuw naar oud</span>
        </div>
        {''.join(regions)}
        <p class="small"><a href="/onderwerpen/">← Bekijk alle onderwerpen</a></p>
      </div>
    </section>

    {render_topic_why(label)}
  </main>
  <footer>Positief nieuws · Dit gebeurt ook. · <a href="/contact/" onclick="if(window.sa_event)window.sa_event('contact_click')">Contact</a> · <a href="/tip/" onclick="if(window.sa_event)window.sa_event('tip_redactie_click')">Tip de redactie</a></footer>
  {analytics_html({'page_type':'topic','topic':slug})}
</body>
</html>"""

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


def homepage_story_url(item, edition_date):
    if has_article_page(item):
        return article_page_url(item, edition_date)
    url = str(item.get("url") or item.get("link") or "")
    parsed = urllib.parse.urlsplit(url)
    return url if parsed.scheme in {"https", "http"} and parsed.netloc else ""


def homepage_story_html(item, edition_date, section, index):
    title = item.get("title") or item.get("headline") or ""
    url = homepage_story_url(item, edition_date)
    attrs = "" if url.startswith(SITE_URL + "/") else 'target="_blank" rel="noopener noreferrer"'
    link = f'<a href="{esc(url)}" {attrs}>{esc(title)}</a>' if url else esc(title)
    teaser = item.get("teaser") or item.get("summary") or item.get("description") or ""
    category = canonical_category(category_label(item)) or category_label(item)
    meta = category_meta_html(item)
    region = "Nederland" if section == "nl" else "Wereld"
    badge = f'<div class="badge">{region} · {esc(category)}</div>'
    image = ""
    slug = str(item.get("article_slug") or "").strip().strip("/")
    cached = _load_pixabay_cache().get(f"{edition_date}/{slug}") or {}
    path = cached.get("image_path") if cached.get("query") == item.get("image_query") else None
    if section != "headlines" and path and Path(str(path).lstrip("/")).is_file():
        eager = section == "nl" and index == 0
        image = f'<a class="article-thumb" href="{esc(url)}" {attrs} aria-label="Lees {esc(title)}"><img class="story-photo" src="{esc(path)}" alt="{esc(item.get("image_alt") or title)}" loading="{"eager" if eager else "lazy"}" decoding="async"></a>'
    if section == "headlines":
        return f'<article class="short"><span class="count">{index+1:02d} / 03</span><h3 class="article-title">{link}</h3><p class="teaser">{esc(teaser)}</p>{meta}</article>'
    if section == "nl" and index < 3:
        hero = index == 0
        cls, body, heading = ("hero-card", "hero-body", "h2") if hero else ("side-card", "side-body", "h3")
        return f'<article class="{cls}">{image}<div class="{body}">{badge}<{heading} class="article-title">{link}</{heading}>' + (f'<p>{esc(teaser)}</p>' if hero else "") + meta + '</div></article>'
    return f'<article class="list-item">{image}<div>{badge}<h3 class="article-title">{link}</h3><p class="teaser-one-line">{esc(teaser)}</p>{meta}</div></article>'


def homepage_cards_html(stories, edition_date, section):
    cards = [homepage_story_html(item, edition_date, section, i) for i, item in enumerate(stories)]
    if section == "nl":
        top = '<section class="homepage-top" aria-label="Uitgelichte verhalen">' + ''.join(cards[:1]) + '<div class="sidecol">' + ''.join(cards[1:3]) + '</div></section>'
        rest = '<section class="block"><div class="blocktitle"><div><h2>Meer goed nieuws uit Nederland</h2><div class="accent"></div></div><p>' + str(len(cards[3:])) + ' verhalen</p></div><div class="story-grid">' + ''.join(cards[3:]) + '</div></section>' if len(cards) > 3 else ""
        return top + rest
    return '<div class="' + ("shorts" if section == "headlines" else "story-grid") + '">' + ''.join(cards) + '</div>'


def update_homepage(data):
    homepage = Path("index.html")
    if not homepage.exists():
        raise FileNotFoundError("index.html ontbreekt voor de homepage-build.")
    edition_date = get_date(data)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(edition_date or "")):
        raise ValueError("Homepage vereist een geldige meta.edition_date of edition.date.")
    datetime.strptime(edition_date, "%Y-%m-%d")
    markup = homepage.read_text(encoding="utf-8")
    graph = [
        {"@type": "Organization", "@id": SITE_URL + "/#publisher", "name": "Positief nieuws", "url": SITE_URL + "/", "logo": {"@type": "ImageObject", "url": SITE_URL + "/sun-icon-512.png", "width": 512, "height": 512}},
        {"@type": "WebSite", "@id": SITE_URL + "/#website", "url": SITE_URL + "/", "name": "Positief nieuws", "inLanguage": "nl-NL", "publisher": {"@id": SITE_URL + "/#publisher"}},
        {"@type": "CollectionPage", "@id": SITE_URL + "/#homepage", "url": SITE_URL + "/", "name": "Positief nieuws uit Nederland en de wereld", "description": "Twaalf positieve nieuwsverhalen uit Nederland en de wereld, plus drie belangrijke nieuwsitems. Elke maandag en donderdag een nieuwe editie.", "inLanguage": "nl-NL", "isPartOf": {"@id": SITE_URL + "/#website"}, "publisher": {"@id": SITE_URL + "/#publisher"}, "dateModified": edition_date, "relatedLink": f"{SITE_URL}/edities/{edition_date}/", "mainEntity": {"@id": SITE_URL + "/#edition-stories"}},
    ]
    story_list = []
    for section, limit in [("nl", 6), ("int", 6), ("headlines", 3)]:
        stories = [item for item in items(data, section) if item.get("title") or item.get("headline")][:limit]
        if section == "nl" and edition_date == "2026-10-08":
            stories.sort(key=lambda item: item.get("article_slug") != "berghof-verbindt-limburgse-natuur")
        cards = homepage_cards_html(stories, edition_date, section)
        block = f'<!-- homepage-{section}:start --><div id="{section}-grid" class="article-list"' + ("" if stories else " hidden") + f'>{cards}</div><!-- homepage-{section}:end -->'
        markup, count = re.subn(rf'<!-- homepage-{section}:start -->.*?<!-- homepage-{section}:end -->', lambda _: block, markup, flags=re.S)
        if count != 1:
            raise ValueError(f"Homepage-marker voor {section} ontbreekt of is dubbel.")
        markup = re.sub(rf'<div id="{section}-state" class="state"(?: hidden)?>.*?</div>', f'<div id="{section}-state" class="state" hidden>Nieuws laden…</div>', markup)
        if section == "headlines":
            markup = markup.replace('id="headlines-section" hidden', 'id="headlines-section"') if stories else markup.replace('id="headlines-section">', 'id="headlines-section" hidden>')
        for item in stories:
            url = homepage_story_url(item, edition_date)
            if url:
                story_list.append({"@type": "ListItem", "position": len(story_list) + 1, "name": item.get("title") or item.get("headline"), "url": url})
    graph.append({"@type": "ItemList", "@id": SITE_URL + "/#edition-stories", "name": "Verhalen in de nieuwste editie", "numberOfItems": len(story_list), "itemListElement": story_list})
    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    markup, count = re.subn(r'<script id="homepage-schema" type="application/ld\+json">.*?</script>', lambda _: f'<script id="homepage-schema" type="application/ld+json">\n{schema}\n  </script>', markup, flags=re.S)
    if count != 1:
        raise ValueError("Homepage-schema ontbreekt of is dubbel.")
    date_html = f'<!-- homepage-date:start --><p class="hero-date" id="edition-date"><time datetime="{edition_date}">Editie van {esc(fmt_date(edition_date))}</time></p><!-- homepage-date:end -->'
    markup, count = re.subn(r'<!-- homepage-date:start -->.*?<!-- homepage-date:end -->', lambda _: date_html, markup, flags=re.S)
    if count != 1:
        raise ValueError("Homepage-datummarker ontbreekt of is dubbel.")
    homepage.write_text(markup, encoding="utf-8")
    print(f"Homepage bijgewerkt: editie {edition_date}, {len(story_list)} direct leesbare verhalen.")


def build_site():
    EDITIONS_DIR.mkdir(exist_ok=True)
    current = None
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
    article_pages = write_article_pages(edition_records)
    if current is not None:
        update_homepage(current)

    latest = max(dates) if dates else datetime.now().strftime("%Y-%m-%d")
    sitemap_urls = [
        (f"{SITE_URL}/", latest),
        (f"{SITE_URL}/over/", None),
        (f"{SITE_URL}/contact/", None),
        (f"{SITE_URL}/tip/", None),
        (f"{SITE_URL}/edities/", latest),
        (f"{SITE_URL}/onderwerpen/", latest),
    ]
    for date_value in sorted(dates, reverse=True):
        sitemap_urls.append((f"{SITE_URL}/edities/{date_value}/", date_value))
    for topic in topics.values():
        sitemap_urls.append((f"{SITE_URL}/{topic['slug']}/", topic["latest"]))
    for article_page in article_pages:
        sitemap_urls.append((article_page["url"], article_page["date"]))

    sitemap_parts = []
    for loc, lastmod in sitemap_urls:
        lm = f"\n    <lastmod>{lastmod}</lastmod>" if lastmod else ""
        sitemap_parts.append(f"  <url>\n    <loc>{loc}</loc>{lm}\n  </url>")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(sitemap_parts) + "\n</urlset>\n"
    SITEMAP_PATH.write_text(sitemap, encoding="utf-8")
    print(f"Sitemap bijgewerkt met {len(sitemap_urls)} URL(s), waarvan {len(topics)} onderwerp-pagina's en {len(article_pages)} eigen artikelpagina's.")


def validate_current():
    if not NEWS_PATH.exists():
        raise FileNotFoundError("nieuws.json niet gevonden.")
    data = json.loads(NEWS_PATH.read_text(encoding="utf-8"))
    validate_positive_articles(data, "nieuws.json")
    print("nieuws.json is geldig: alle positieve artikelen vallen onder een van de acht vaste categorieën.")


def refresh_edition_analytics():
    """Apply the same edition context and measurement to existing and future pages."""
    for page in Path('.').rglob('*.html'):
        if any(part.startswith('.') for part in page.parts):
            continue
        markup = page.read_text(encoding='utf-8')
        relative = str(page).replace('\\', '/')
        match = re.match(r'(?:artikelen|edities)/(\d{4}-\d{2}-\d{2})(?:/|\.)', relative)
        date = match.group(1) if match else ''
        kind = 'article' if relative.startswith('artikelen/') else 'edition' if date else 'special' if relative.startswith('specials/') else 'other'
        if relative == 'index.html':
            kind = 'homepage'
            date_match = re.search(r'<time datetime="(\d{4}-\d{2}-\d{2})"', markup)
            date = date_match.group(1) if date_match else ''
        markup = re.sub(r'<!-- edition-analytics:start -->.*?<!-- edition-analytics:end -->\s*', '', markup, flags=re.S)
        tag = f'<!-- edition-analytics:start --><script src="/edition-analytics.js?v=1" data-page-type="{kind}" data-edition="{date}"></script><!-- edition-analytics:end -->'
        markup = re.sub(r'</head\s*>', lambda _: tag + '</head>', markup, count=1, flags=re.I)
        markup = re.sub(r'window\.sa_metadata = (\{.*?\});', r'window.sa_metadata = Object.assign({}, window.sa_metadata, \1);', markup, flags=re.S)
        markup = markup.replace('edition: articleLink.dataset.articleEdition || window.sa_metadata?.edition || "onbekend",', 'target_edition: articleLink.dataset.articleEdition || "none",')
        markup = markup.replace('edition: sourceLink.dataset.articleEdition || window.sa_metadata?.edition || "onbekend",', 'target_edition: sourceLink.dataset.articleEdition || "none",')
        if 'simpleanalyticscdn.com/latest.js' in markup and 'data-metadata-collector' not in markup:
            markup = markup.replace('analyticsScript.async = true;', 'analyticsScript.async = true;\n      analyticsScript.setAttribute("data-metadata-collector", "pnAnalyticsMetadata");')
        if relative == 'index.html':
            # Initial context exists before pageview; update from the actual fetched edition.
            markup = markup.replace('function loadAnalytics(editionDate) {', 'function loadAnalytics(editionDate) {\n      if (window.pnSetEdition) window.pnSetEdition(editionDate);') if 'window.pnSetEdition(editionDate)' not in markup else markup
            markup = markup.replace('edition: editionDate || "onbekend"', 'edition: editionDate || "none"')
        page.write_text(markup, encoding='utf-8')
    print('Editiemeting bijgewerkt op bestaande pagina’s.')


def refresh_branding():
    """Apply the same crawlable sun favicon and brand name to every public HTML page."""
    tags = ('<link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48 64x64">'
            '<link rel="icon" type="image/png" href="/favicon.png" sizes="96x96">'
            '<link rel="apple-touch-icon" href="/sun-apple-touch-icon.png" sizes="180x180">'
            '<link rel="manifest" href="/manifest.json?v=5">'
            '<meta property="og:site_name" content="Positief nieuws">'
            '<meta name="application-name" content="Positief nieuws">')
    count = 0
    for page in Path('.').rglob('*.html'):
        if any(part.startswith('.') for part in page.parts):
            continue
        markup = page.read_text(encoding='utf-8')
        markup = re.sub(r'<svg class="brand-sun".*?</svg>', lambda _: '<img class="brand-sun" src="/sun-icon-512.png" width="32" height="32" alt="" aria-hidden="true">', markup, flags=re.S)
        if not re.search(r'</head\s*>', markup, re.I):
            continue
        markup = re.sub(r'<link\b(?=[^>]*\brel\s*=\s*[\'"](?:icon|shortcut icon|apple-touch-icon|manifest)[\'"])[^>]*>\s*', '', markup, flags=re.I)
        markup = re.sub(r'<meta\b(?=[^>]*\b(?:property|name)\s*=\s*[\'"](?:og:site_name|application-name)[\'"])[^>]*>\s*', '', markup, flags=re.I)
        markup = re.sub(r'</head\s*>', tags + '</head>', markup, count=1, flags=re.I)
        if page == Path('index.html'):
            schema_pattern = r'(<script id="homepage-schema" type="application/ld\+json">)(.*?)(</script>)'
            def enrich_schema(match):
                schema = json.loads(match.group(2))
                for entity in schema.get('@graph', []):
                    if entity.get('@type') == 'WebSite':
                        entity.update(name='Positief nieuws', url=SITE_URL + '/')
                    if entity.get('@type') == 'Organization':
                        entity['logo'] = {'@type': 'ImageObject', 'url': SITE_URL + '/sun-icon-512.png', 'width': 512, 'height': 512}
                return match.group(1) + '\n' + json.dumps(schema, ensure_ascii=False, indent=2) + '\n' + match.group(3)
            markup = re.sub(schema_pattern, enrich_schema, markup, flags=re.S)
        if markup != page.read_text(encoding='utf-8'):
            page.write_text(markup, encoding='utf-8')
            count += 1
    print(f'Favicon en sitenaam bijgewerkt op {count} pagina(s).')
    refresh_edition_analytics()


def refresh_special_growth():
    """Use the same signup/share component on static specials and generated articles."""
    for page in Path("specials").rglob("index.html"):
        markup = page.read_text(encoding="utf-8")
        canonical_match = re.search(r'<link rel="canonical" href="([^"]+)"', markup)
        heading_match = re.search(r'<h1[^>]*>(.*?)</h1>', markup, re.S)
        if not canonical_match or not heading_match:
            raise ValueError(f"Special mist canonical of titel: {page}")
        title = html.unescape(re.sub(r'<[^>]+>', '', heading_match.group(1))).strip().rstrip('.')
        component = '<!-- special-growth:start -->\n' + render_growth_block(canonical_match.group(1), title, "special") + '\n<!-- special-growth:end -->'
        if '<!-- special-growth:start -->' in markup:
            markup = re.sub(r'<!-- special-growth:start -->.*?<!-- special-growth:end -->', lambda _: component, markup, flags=re.S)
        else:
            markup, count = re.subn(r'(?=\s*<section class="support-teaser")', lambda _: '\n' + component + '\n', markup, count=1)
            if count != 1:
                raise ValueError(f"Special mist steunblok als invoegpunt: {page}")
        styles = '/* special-growth:start */\n' + ARTICLE_GROWTH_CSS + '\n/* special-growth:end */'
        if '/* special-growth:start */' in markup:
            markup = re.sub(r'/\* special-growth:start \*/.*?/\* special-growth:end \*/', lambda _: styles, markup, flags=re.S)
        else:
            markup = markup.replace('</style>', styles + '\n</style>', 1)
        script = '<!-- special-growth-script:start -->\n' + ARTICLE_GROWTH_JS + '\n<!-- special-growth-script:end -->'
        if '<!-- special-growth-script:start -->' in markup:
            markup = re.sub(r'<!-- special-growth-script:start -->.*?<!-- special-growth-script:end -->', lambda _: script, markup, flags=re.S)
        else:
            markup = markup.replace('</body>', script + '\n</body>', 1)
        page.write_text(markup, encoding="utf-8")
        print(f"Nieuwsbrief en delen bijgewerkt: {page}")


def refresh_articles():
    records = []
    for path in sorted(EDITIONS_DIR.glob("????-??-??.json"), reverse=True):
        data = json.loads(path.read_text(encoding="utf-8"))
        records.append((get_date(data, path.stem), data))
    write_article_pages(records)
    refresh_branding()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-current", action="store_true", help="Valideer alleen nieuws.json en stop daarna.")
    parser.add_argument("--refresh-branding", action="store_true", help="Werk alleen favicon en merkgegevens op bestaande pagina’s bij.")
    parser.add_argument("--refresh-specials", action="store_true", help="Werk nieuwsbrief en delen op specialpagina’s bij.")
    parser.add_argument("--refresh-articles", action="store_true", help="Werk bestaande artikelpagina’s bij zonder de editie te wijzigen.")
    args = parser.parse_args()
    try:
        if args.refresh_specials:
            refresh_special_growth()
            refresh_edition_analytics()
        elif args.refresh_articles:
            refresh_articles()
        elif args.refresh_branding:
            refresh_branding()
        elif args.validate_current:
            validate_current()
        else:
            build_site()
            refresh_special_growth()
            refresh_branding()
    except Exception as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
