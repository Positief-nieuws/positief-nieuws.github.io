#!/usr/bin/env python3
"""
Goed nieuws 0.4 auto

Verbeteringen t.o.v. 0.3:
- categorieën gebruiken echte woord-/frase-matches i.p.v. losse substrings;
- sportfeeds krijgen automatisch sterke voorkeur voor categorie Sport;
- expliciete sporttermen zoals atletiek, mountainbike, wielrennen, hockey enz. wegen zwaar;
- 'ai' matcht alleen als los woord, dus niet meer toevallig in andere woorden;
- publiceert ALLEEN bij exact 7 NL + 7 internationaal;
- anders blijft de bestaande nieuws.json onaangeroerd.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "nieuws.json"

MAX_AGE_HOURS = 72
PREFERRED_AGE_HOURS = 48
TARGET_PER_REGION = 7
MIN_DISTINCT_SOURCES = 5
MAX_PER_SOURCE = 2

USER_AGENT = "GoedNieuwsBot/0.4"

SOURCES = [
    # Nederland
    {"name":"NOS Nieuws", "publisher":"NOS", "region":"nl", "feed":"https://feeds.nos.nl/nosnieuwsalgemeen"},
    {"name":"NOS Economie", "publisher":"NOS", "region":"nl", "feed":"https://feeds.nos.nl/nosnieuwseconomie"},
    {"name":"NOS Cultuur", "publisher":"NOS", "region":"nl", "feed":"https://feeds.nos.nl/nosnieuwscultuurenmedia"},
    {"name":"NOS Tech", "publisher":"NOS", "region":"nl", "feed":"https://feeds.nos.nl/nosnieuwstech"},
    {"name":"NOS Opmerkelijk", "publisher":"NOS", "region":"nl", "feed":"https://feeds.nos.nl/nosnieuwsopmerkelijk"},
    {"name":"NOS Sport", "publisher":"NOS", "region":"nl", "feed":"https://feeds.nos.nl/nossportalgemeen"},
    {"name":"RIVM", "publisher":"RIVM", "region":"nl", "feed":"https://www.rivm.nl/nieuws/rss.xml"},
    {"name":"Scientias", "publisher":"Scientias", "region":"nl", "feed":"https://feeds.feedburner.com/scientias-wetenschap"},
    {"name":"Nature Today", "publisher":"Nature Today", "region":"nl", "feed":"https://www.naturetoday.com/intl/nl/nature-reports/rss"},

    # Internationaal
    {"name":"MIT News", "publisher":"MIT News", "region":"int", "feed":"https://news.mit.edu/rss/feed"},
    {"name":"BBC Science", "publisher":"BBC", "region":"int", "feed":"https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"},
    {"name":"BBC Business", "publisher":"BBC", "region":"int", "feed":"https://feeds.bbci.co.uk/news/business/rss.xml"},
    {"name":"The Guardian Environment", "publisher":"The Guardian", "region":"int", "feed":"https://www.theguardian.com/environment/rss"},
    {"name":"The Guardian Science", "publisher":"The Guardian", "region":"int", "feed":"https://www.theguardian.com/science/rss"},
    {"name":"NASA", "publisher":"NASA", "region":"int", "feed":"https://www.nasa.gov/news-release/feed/"},
    {"name":"UN News", "publisher":"UN News", "region":"int", "feed":"https://news.un.org/feed/subscribe/en/news/all/rss.xml"},
]

POSITIVE = {
    "wint":4, "winnen":4, "winst":3, "goud":4, "kampioen":4, "record":3,
    "groeit":3, "groei":3, "herstelt":4, "herstel":4, "terugkeer":4,
    "doorbraak":4, "succes":3, "oplossing":3, "innovatie":3, "ontdekt":3,
    "ontdekking":3, "verbetert":3, "verbetering":3, "helpt":3,
    "gered":4, "redding":4, "beschermt":3, "samenwerking":2, "schoner":3,
    "duurzaam":2, "medaille":3, "hoop":2, "positief":3, "beter":2,
    "daalt":2, "daling":2, "minder":1, "nieuwe":1, "nieuw":1,
    "wins":4, "win":4, "gold":4, "champion":4, "growth":3, "grows":3,
    "recovery":4, "recovers":4, "return":3, "breakthrough":4, "success":3,
    "solution":3, "innovation":3, "discovery":3, "improves":3, "helps":3,
    "rescued":4, "protects":3, "cleaner":3, "sustainable":2, "hope":2,
    "better":2, "falls":1, "decline":1,
}

NEGATIVE = {
    "oorlog":-7, "dood":-7, "doden":-7, "omgekomen":-7, "gewond":-5,
    "moord":-7, "crisis":-5, "failliet":-5, "aanval":-6, "ramp":-7,
    "explosie":-7, "geweld":-7, "brand":-4, "vermist":-5, "fraude":-5,
    "staking":-3, "dreigt":-4, "zorgelijk":-3,
    "war":-7, "dead":-7, "death":-7, "killed":-7, "wounded":-5,
    "murder":-7, "crisis":-5, "bankrupt":-5, "attack":-6, "disaster":-7,
    "explosion":-7, "violence":-7, "wildfire":-4, "missing":-5,
    "fraud":-5, "strike":-3, "threat":-4,
}

CATEGORY_RULES = {
    "Sport": [
        "sport","voetbal","football","soccer","hockey","tennis","atletiek","athletics",
        "wielrennen","cycling","mountainbike","mtb","zwemmen","swimming","olympic",
        "olympics","medaille","medal","kampioen","champion","wedstrijd","match","goal",
        "race","marathon","sprint","finale","final","wereldrecord","record"
    ],
    "Economie & geld": [
        "economie","economy","geld","money","beurs","market","markt","export","import",
        "business","bedrijf","bedrijven","jobs","banen","inflatie","inflation","income",
        "inkomen","investment","investering","investeringen"
    ],
    "Natuur & klimaat": [
        "natuur","nature","klimaat","climate","forest","bos","river","rivier","ocean",
        "oceaan","biodiversiteit","biodiversity","emission","emissie","energy","energie",
        "sustainable","duurzaam","ecosystem","ecosysteem"
    ],
    "Dieren": [
        "dier","dieren","animal","animals","bird","birds","vogel","vogels","fish","vis",
        "tiger","tijger","whale","walvis","turtle","schildpad","bee","bees","bij","bijen",
        "lion","leeuw","wolf","wolves","hond","dog","cat","kat","insect"
    ],
    "Wetenschap": [
        "wetenschap","science","onderzoek","research","scientist","onderzoeker","study",
        "studie","space","ruimte","physics","fysica","biology","biologie","astronomy",
        "astronomie","telescope","telescoop"
    ],
    "Gezondheid": [
        "gezondheid","health","medical","medisch","medicine","medicijn","patient","patiënt",
        "care","zorg","therapy","therapie","cancer","kanker","vaccine","vaccin","screening",
        "diagnosis","diagnose","disease","ziekte"
    ],
    "Technologie & innovatie": [
        "technology","technologie","tech","innovatie","innovation","robot","robots","chip",
        "chips","software","computer","engineering","battery","batterij","artificial intelligence",
        "kunstmatige intelligentie","ai"
    ],
    "Cultuur & media": [
        "cultuur","culture","kunst","art","museum","muziek","music","film","boek","book",
        "media","theater","heritage","erfgoed","painting","schilderij"
    ],
    "Onderwijs & ontwikkeling": [
        "onderwijs","education","school","student","students","leerling","leerlingen",
        "learning","opleiding","university","universiteit","teacher","leraar"
    ],
    "Voeding & leefstijl": [
        "voeding","food","groente","vegetable","fruit","diet","leefstijl","lifestyle",
        "sleep","slaap","exercise","bewegen","nutrition"
    ],
    "Geschiedenis & mens": [
        "geschiedenis","history","archeologie","archaeology","archeoloog","archaeologist",
        "ancient","oudheid","fossil","voorouder","ancestor","prehistoric"
    ],
    "Mens & samenleving": [
        "community","gemeenschap","buurt","vrijwillig","volunteer","samenleving","society",
        "poverty","armoede","refugee","vluchteling","solidarity","solidariteit"
    ],
}

# Hogere waarde wint bij gelijk aantal matches.
CATEGORY_PRIORITY = {
    "Sport": 100,
    "Gezondheid": 90,
    "Dieren": 85,
    "Economie & geld": 80,
    "Technologie & innovatie": 75,
    "Natuur & klimaat": 70,
    "Onderwijs & ontwikkeling": 65,
    "Cultuur & media": 60,
    "Voeding & leefstijl": 55,
    "Geschiedenis & mens": 50,
    "Mens & samenleving": 45,
    "Wetenschap": 40,
}

ICONS = {
    "Mens & samenleving":"🤝",
    "Economie & geld":"📈",
    "Natuur & klimaat":"🌱",
    "Dieren":"🐾",
    "Wetenschap":"🔬",
    "Gezondheid":"❤️",
    "Technologie & innovatie":"💡",
    "Sport":"🏅",
    "Cultuur & media":"🎨",
    "Onderwijs & ontwikkeling":"🎓",
    "Voeding & leefstijl":"🥬",
    "Geschiedenis & mens":"🏛️",
    "Gewoon leuk":"☀️",
}

def clean_html(value):
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()

def lname(tag):
    return tag.rsplit("}", 1)[-1].lower()

def child_text(node, names):
    for child in list(node):
        if lname(child.tag) in names and child.text and child.text.strip():
            return clean_html(child.text)
    return ""

def item_link(node):
    for child in list(node):
        if lname(child.tag) == "link":
            href = child.attrib.get("href")
            if href and child.attrib.get("rel", "alternate") in ("alternate", ""):
                return href.strip()
            if child.text and child.text.strip():
                return child.text.strip()
    return ""

def parse_date(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def fetch_feed(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read()

def parse_feed(raw):
    root = ET.fromstring(raw)
    out = []
    for node in root.iter():
        if lname(node.tag) not in ("item", "entry"):
            continue
        title = child_text(node, {"title"})
        url = item_link(node)
        summary = child_text(node, {"description","summary","content","encoded"})
        date_raw = child_text(node, {"pubdate","published","updated","date"})
        published = parse_date(date_raw)
        if title and url:
            out.append({
                "title": title,
                "url": url,
                "summary": summary,
                "published": published,
            })
    return out

def normalized_url(url):
    try:
        u = urlparse(url)
        return (u.netloc.lower() + u.path.rstrip("/")).lower()
    except Exception:
        return url.lower().rstrip("/")

def phrase_matches(text, phrase):
    """
    Match hele woorden/frases.
    Dus 'ai' matcht 'AI', maar niet 'mountainbike' of 'said'.
    """
    pattern = r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)"
    return bool(re.search(pattern, text.lower()))

def lexical_score(text, lexicon):
    score = 0
    for phrase, pts in lexicon.items():
        if phrase_matches(text, phrase):
            score += pts
    return score

def score_item(title, summary, hours_old):
    text = f"{title} {summary}"
    score = lexical_score(text, POSITIVE) + lexical_score(text, NEGATIVE)

    if hours_old is not None:
        if hours_old <= 24:
            score += 4
        elif hours_old <= 48:
            score += 2

    return score

def category_for(title, summary, feed_name):
    text = f"{title} {summary}".lower()
    feed_lower = feed_name.lower()

    # Bron/feed-signalen zijn sterk.
    if "sport" in feed_lower:
        return "Sport"
    if "economie" in feed_lower or "business" in feed_lower:
        return "Economie & geld"
    if "cultuur" in feed_lower:
        return "Cultuur & media"
    if "tech" in feed_lower:
        return "Technologie & innovatie"

    scores = {}
    for category, terms in CATEGORY_RULES.items():
        hits = sum(1 for term in terms if phrase_matches(text, term))
        if hits:
            scores[category] = hits

    if not scores:
        # Bronspecifieke fallback
        if "nature today" in feed_lower:
            return "Natuur & klimaat"
        if "rivm" in feed_lower:
            return "Gezondheid"
        if "scientias" in feed_lower or "mit news" in feed_lower or "nasa" in feed_lower:
            return "Wetenschap"
        return "Gewoon leuk"

    return max(
        scores,
        key=lambda cat: (scores[cat], CATEGORY_PRIORITY.get(cat, 0))
    )

def compact_summary(text, max_chars=320):
    text = clean_html(text)
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    candidate = " ".join(sentences[:2]).strip() or text
    if len(candidate) > max_chars:
        candidate = candidate[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return candidate

def collect():
    now = datetime.now(timezone.utc)
    items = []
    seen = set()
    errors = []

    for source in SOURCES:
        try:
            feed = parse_feed(fetch_feed(source["feed"]))
        except Exception as exc:
            errors.append(f'{source["name"]}: {type(exc).__name__}: {exc}')
            continue

        for item in feed:
            pub = item["published"]
            hours_old = None
            if pub is not None:
                hours_old = max(0.0, (now - pub).total_seconds() / 3600)
                if hours_old > MAX_AGE_HOURS:
                    continue

            key = normalized_url(item["url"])
            if key in seen:
                continue
            seen.add(key)

            category = category_for(item["title"], item["summary"], source["name"])
            score = score_item(item["title"], item["summary"], hours_old)

            items.append({
                "region": source["region"],
                "source": source["publisher"],
                "feed": source["name"],
                "title": clean_html(item["title"]),
                "url": item["url"],
                "summary": compact_summary(item["summary"]),
                "published": pub.isoformat() if pub else None,
                "hours_old": round(hours_old, 1) if hours_old is not None else None,
                "category": category,
                "icon": ICONS.get(category, "☀️"),
                "score": score,
            })

    return items, errors

def choose(items, region):
    pool = [x for x in items if x["region"] == region]

    pool.sort(
        key=lambda x: (
            -x["score"],
            x["hours_old"] if x["hours_old"] is not None else 9999,
        )
    )

    selected = []
    source_counts = {}
    used_categories = set()

    # 1. Sterke kandidaten <=48 uur, unieke categorie.
    for x in pool:
        if len(selected) >= TARGET_PER_REGION:
            break
        if x["category"] in used_categories:
            continue
        if source_counts.get(x["source"], 0) >= MAX_PER_SOURCE:
            continue
        if x["hours_old"] is not None and x["hours_old"] > PREFERRED_AGE_HOURS:
            continue
        if x["score"] < 1:
            continue

        selected.append(x)
        used_categories.add(x["category"])
        source_counts[x["source"]] = source_counts.get(x["source"], 0) + 1

    # 2. Max 72 uur, nog steeds unieke categorie.
    for x in pool:
        if len(selected) >= TARGET_PER_REGION:
            break
        if x in selected or x["category"] in used_categories:
            continue
        if source_counts.get(x["source"], 0) >= MAX_PER_SOURCE:
            continue
        if x["score"] < 0:
            continue

        selected.append(x)
        used_categories.add(x["category"])
        source_counts[x["source"]] = source_counts.get(x["source"], 0) + 1

    # 3. Alleen als nodig: categorie mag dubbel, bron max 2, score niet negatief.
    for x in pool:
        if len(selected) >= TARGET_PER_REGION:
            break
        if x in selected:
            continue
        if source_counts.get(x["source"], 0) >= MAX_PER_SOURCE:
            continue
        if x["score"] < 0:
            continue

        selected.append(x)
        source_counts[x["source"]] = source_counts.get(x["source"], 0) + 1

    # Brondiversiteit verbeteren.
    distinct = {x["source"] for x in selected}
    if len(distinct) < MIN_DISTINCT_SOURCES:
        for candidate in pool:
            if len(distinct) >= MIN_DISTINCT_SOURCES:
                break
            if candidate in selected or candidate["source"] in distinct or candidate["score"] < 0:
                continue

            for i in range(len(selected) - 1, -1, -1):
                src = selected[i]["source"]
                if sum(1 for y in selected if y["source"] == src) > 1:
                    selected[i] = candidate
                    distinct = {x["source"] for x in selected}
                    break

    return selected[:TARGET_PER_REGION]

def story_for_output(item, international=False):
    source = item["source"]
    if international:
        source += " · English"

    return {
        "category": item["category"],
        "icon": item["icon"],
        "title": item["title"],
        "summary": item["summary"] or "Lees het volledige bericht bij de bron.",
        "source": source,
        "url": item["url"],
    }

def nl_display_date():
    days = ["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
    months = ["januari","februari","maart","april","mei","juni","juli","augustus","september","oktober","november","december"]
    now = datetime.now().astimezone()
    return f"{days[now.weekday()]} {now.day} {months[now.month-1]}"

def main():
    items, errors = collect()
    nl = choose(items, "nl")
    international = choose(items, "int")

    print(f"Verzameld: {len(items)} kandidaten")
    print(f"NL: {len(nl)} | bronnen: {len(set(x['source'] for x in nl))}")
    print(f"INT: {len(international)} | bronnen: {len(set(x['source'] for x in international))}")

    print("\nNL-selectie:")
    for x in nl:
        print(f"- [{x['category']}] {x['source']}: {x['title']}")

    print("\nInternationale selectie:")
    for x in international:
        print(f"- [{x['category']}] {x['source']}: {x['title']}")

    if errors:
        print(f"\nFeedfouten: {len(errors)}")
        for e in errors:
            print(" -", e)

    # Harde publicatieregel.
    if len(nl) != TARGET_PER_REGION or len(international) != TARGET_PER_REGION:
        print(
            f"\nNIET PUBLICEREN: exact 7 + 7 vereist. "
            f"Gevonden: {len(nl)} NL + {len(international)} INT. "
            "Bestaande nieuws.json blijft staan."
        )
        sys.exit(0)

    now = datetime.now().astimezone()
    output = {
        "edition": {
            "date": now.strftime("%Y-%m-%d"),
            "displayDate": nl_display_date(),
            "title": "Goed nieuws",
            "tagline": "Dit gebeurt ook.",
            "intro": "14 korte verhalen. Geen doomscrollen, geen eindeloze feed.",
            "closingTitle": "Dat was het.",
            "closingText": "Ga lekker verder met je dag. ☀️"
        },
        "dutch": [story_for_output(x) for x in nl],
        "international": [story_for_output(x, True) for x in international],
        "_meta": {
            "generated_at": now.isoformat(),
            "generator": "Goed nieuws 0.4 auto",
            "feed_errors": errors,
        }
    }

    OUTPUT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\nNieuwe 7+7-editie geschreven naar {OUTPUT}")

if __name__ == "__main__":
    main()
