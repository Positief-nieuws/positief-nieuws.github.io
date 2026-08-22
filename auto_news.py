#!/usr/bin/env python3
"""
Goed nieuws 0.7 auto
Gratis dagelijkse editie zonder AI/API.

Belangrijkste wijzigingen:
- positieve discovery-query per niet-RSS-bron, in plaats van blind de laatste headlines ophalen;
- veel extra Nederlandse regionale en gratis nieuwsbronnen;
- een titel moet zelf een duidelijke positieve cue bevatten;
- hard-negatieve patronen zoals 'niet door' blokkeren altijd;
- contextregels voor o.a. werkloosheid, uitstoot en overlevingskans;
- max 2 berichten per bron en minimaal 5 bronnen per blok;
- voorkeur laatste 48 uur, fallback tot 7 dagen;
- publiceert alleen bij 7 NL + 7 internationaal.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "nieuws.json"

TARGET = 7
MIN_SOURCES = 5
MAX_PER_SOURCE = 2
PREFERRED_AGE_HOURS = 48
MAX_AGE_HOURS = 168
USER_AGENT = "GoedNieuwsBot/0.7"

# mode=rss: directe feed
# mode=google_site: gratis Google News RSS site-search als bron geen handige RSS heeft.
SOURCES = [
    # ---------------- NEDERLAND ----------------
    {"publisher":"NOS","region":"nl","mode":"rss","url":"https://feeds.nos.nl/nosnieuwsalgemeen","weight":2.3,"hint":None},
    {"publisher":"NOS","region":"nl","mode":"rss","url":"https://feeds.nos.nl/nosnieuwseconomie","weight":2.3,"hint":"Economie & geld"},
    {"publisher":"NOS","region":"nl","mode":"rss","url":"https://feeds.nos.nl/nosnieuwscultuurenmedia","weight":2.3,"hint":"Cultuur & media"},
    {"publisher":"NOS","region":"nl","mode":"rss","url":"https://feeds.nos.nl/nosnieuwstech","weight":2.3,"hint":"Technologie & innovatie"},
    {"publisher":"NOS","region":"nl","mode":"rss","url":"https://feeds.nos.nl/nosnieuwsopmerkelijk","weight":2.2,"hint":"Gewoon leuk"},
    {"publisher":"NOS","region":"nl","mode":"rss","url":"https://feeds.nos.nl/nossportalgemeen","weight":2.3,"hint":"Sport"},

    {"publisher":"PBL","region":"nl","mode":"rss","url":"https://www.pbl.nl/feed/article/rss.xml","weight":2.5,"hint":"Natuur & klimaat"},
    {"publisher":"PBL","region":"nl","mode":"rss","url":"https://www.pbl.nl/feed/topic/20/article/rss.xml","weight":2.5,"hint":"Mens & samenleving"},
    {"publisher":"PBL","region":"nl","mode":"rss","url":"https://www.pbl.nl/feed/topic/17/article/rss.xml","weight":2.5,"hint":"Economie & geld"},
    {"publisher":"PBL","region":"nl","mode":"rss","url":"https://www.pbl.nl/feed/topic/13/article/rss.xml","weight":2.5,"hint":"Natuur & klimaat"},
    {"publisher":"PBL","region":"nl","mode":"rss","url":"https://www.pbl.nl/feed/topic/9/article/rss.xml","weight":2.5,"hint":"Voeding & leefstijl"},
    {"publisher":"PBL","region":"nl","mode":"rss","url":"https://www.pbl.nl/feed/topic/11/article/rss.xml","weight":2.5,"hint":"Natuur & klimaat"},

    {"publisher":"KNMI","region":"nl","mode":"rss","url":"https://www.knmi.nl/rssfeeds/rss_KNMInieuwsberichten","weight":2.5,"hint":"Natuur & klimaat"},
    {"publisher":"KNMI","region":"nl","mode":"rss","url":"https://www.knmi.nl/rssfeeds/rss_KNMIklimaatberichten","weight":2.5,"hint":"Natuur & klimaat"},
    {"publisher":"RIVM","region":"nl","mode":"rss","url":"https://www.rivm.nl/nieuws/rss.xml","weight":2.5,"hint":"Gezondheid"},
    {"publisher":"Scientias","region":"nl","mode":"rss","url":"https://feeds.feedburner.com/scientias-wetenschap","weight":2.0,"hint":"Wetenschap"},
    {"publisher":"Nature Today","region":"nl","mode":"rss","url":"https://www.naturetoday.com/intl/nl/nature-reports/rss","weight":2.1,"hint":"Natuur & klimaat"},

    # Extra NL-bronnen via site-search
    {"publisher":"CBS","region":"nl","mode":"google_site","domain":"cbs.nl","weight":2.6,"hint":"Economie & geld"},
    {"publisher":"Wageningen University & Research","region":"nl","mode":"google_site","domain":"wur.nl","weight":2.7,"hint":"Wetenschap"},
    {"publisher":"Universiteit Twente","region":"nl","mode":"google_site","domain":"utwente.nl","weight":2.6,"hint":"Technologie & innovatie"},
    {"publisher":"TU Delft","region":"nl","mode":"google_site","domain":"tudelft.nl","weight":2.6,"hint":"Technologie & innovatie"},
    {"publisher":"Universiteit Utrecht","region":"nl","mode":"google_site","domain":"uu.nl","weight":2.5,"hint":"Wetenschap"},
    {"publisher":"Radboud Universiteit","region":"nl","mode":"google_site","domain":"ru.nl","weight":2.5,"hint":"Wetenschap"},
    {"publisher":"TNO","region":"nl","mode":"google_site","domain":"tno.nl","weight":2.6,"hint":"Technologie & innovatie"},
    {"publisher":"NEMO Kennislink","region":"nl","mode":"google_site","domain":"nemokennislink.nl","weight":2.2,"hint":"Wetenschap"},
    {"publisher":"RVO","region":"nl","mode":"google_site","domain":"rvo.nl","weight":2.3,"hint":"Economie & geld"},
    {"publisher":"Rijksoverheid","region":"nl","mode":"google_site","domain":"rijksoverheid.nl","weight":2.4,"hint":"Mens & samenleving"},
    {"publisher":"Voedingscentrum","region":"nl","mode":"google_site","domain":"voedingscentrum.nl","weight":2.4,"hint":"Voeding & leefstijl"},
    {"publisher":"Milieu Centraal","region":"nl","mode":"google_site","domain":"milieucentraal.nl","weight":2.1,"hint":"Natuur & klimaat"},
    {"publisher":"Staatsbosbeheer","region":"nl","mode":"google_site","domain":"staatsbosbeheer.nl","weight":2.2,"hint":"Natuur & klimaat"},
    {"publisher":"Oranje Fonds","region":"nl","mode":"google_site","domain":"oranjefonds.nl","weight":2.2,"hint":"Mens & samenleving"},
    {"publisher":"Humanitas","region":"nl","mode":"google_site","domain":"humanitas.nl","weight":2.1,"hint":"Mens & samenleving"},

    # Extra Nederlandse algemene en regionale bronnen.
    # Juist hier zitten vaak lokale, concrete positieve verhalen.
    {"publisher":"NU.nl","region":"nl","mode":"google_site","domain":"nu.nl","weight":2.3,"hint":None},
    {"publisher":"RTL Nieuws","region":"nl","mode":"google_site","domain":"rtl.nl","weight":2.3,"hint":None},
    {"publisher":"RTV Oost","region":"nl","mode":"google_site","domain":"rtvoost.nl","weight":2.2,"hint":None},
    {"publisher":"Omroep Brabant","region":"nl","mode":"google_site","domain":"omroepbrabant.nl","weight":2.2,"hint":None},
    {"publisher":"Omroep Gelderland","region":"nl","mode":"google_site","domain":"gld.nl","weight":2.2,"hint":None},
    {"publisher":"Rijnmond","region":"nl","mode":"google_site","domain":"rijnmond.nl","weight":2.2,"hint":None},
    {"publisher":"NH Nieuws","region":"nl","mode":"google_site","domain":"nhnieuws.nl","weight":2.2,"hint":None},
    {"publisher":"RTV Noord","region":"nl","mode":"google_site","domain":"rtvnoord.nl","weight":2.2,"hint":None},
    {"publisher":"Omrop Fryslân","region":"nl","mode":"google_site","domain":"omropfryslan.nl","weight":2.2,"hint":None},
    {"publisher":"AT5","region":"nl","mode":"google_site","domain":"at5.nl","weight":2.1,"hint":None},
    {"publisher":"1Limburg","region":"nl","mode":"google_site","domain":"1limburg.nl","weight":2.1,"hint":None},
    {"publisher":"Hart van Nederland","region":"nl","mode":"google_site","domain":"hartvannederland.nl","weight":2.0,"hint":None},

    # ---------------- INTERNATIONAAL ----------------
    {"publisher":"MIT News","region":"int","mode":"rss","url":"https://news.mit.edu/rss/feed","weight":2.7,"hint":"Wetenschap"},
    {"publisher":"NASA","region":"int","mode":"rss","url":"https://www.nasa.gov/news-release/feed/","weight":2.7,"hint":"Wetenschap"},
    {"publisher":"BBC","region":"int","mode":"rss","url":"https://feeds.bbci.co.uk/news/science_and_environment/rss.xml","weight":2.5,"hint":"Wetenschap"},
    {"publisher":"BBC","region":"int","mode":"rss","url":"https://feeds.bbci.co.uk/news/business/rss.xml","weight":2.5,"hint":"Economie & geld"},
    {"publisher":"The Guardian","region":"int","mode":"rss","url":"https://www.theguardian.com/environment/rss","weight":2.4,"hint":"Natuur & klimaat"},
    {"publisher":"The Guardian","region":"int","mode":"rss","url":"https://www.theguardian.com/science/rss","weight":2.4,"hint":"Wetenschap"},
    {"publisher":"UN News","region":"int","mode":"rss","url":"https://news.un.org/feed/subscribe/en/news/all/rss.xml","weight":2.5,"hint":"Mens & samenleving"},

    {"publisher":"ESA","region":"int","mode":"google_site","domain":"esa.int","weight":2.6,"hint":"Wetenschap"},
    {"publisher":"WHO","region":"int","mode":"google_site","domain":"who.int","weight":2.6,"hint":"Gezondheid"},
    {"publisher":"UNICEF","region":"int","mode":"google_site","domain":"unicef.org","weight":2.5,"hint":"Mens & samenleving"},
    {"publisher":"World Bank","region":"int","mode":"google_site","domain":"worldbank.org","weight":2.5,"hint":"Economie & geld"},
    {"publisher":"OECD","region":"int","mode":"google_site","domain":"oecd.org","weight":2.5,"hint":"Economie & geld"},
    {"publisher":"UNEP","region":"int","mode":"google_site","domain":"unep.org","weight":2.5,"hint":"Natuur & klimaat"},
    {"publisher":"Smithsonian Magazine","region":"int","mode":"google_site","domain":"smithsonianmag.com","weight":2.3,"hint":"Geschiedenis & mens"},
    {"publisher":"ScienceDaily","region":"int","mode":"google_site","domain":"sciencedaily.com","weight":2.2,"hint":"Wetenschap"},
    {"publisher":"Positive News","region":"int","mode":"google_site","domain":"positive.news","weight":2.0,"hint":"Mens & samenleving"},
]

POSITIVE_PHRASES = {
    "wint":5, "winnen":5, "winst":4, "goud":5, "kampioen":5,
    "doorbraak":5, "succes":4, "herstelt":5, "herstel":5, "hoopvol":4,
    "terugkeer":5, "gered":5, "redding":5, "beschermt":4,
    "verbetert":4, "verbetering":4, "helpt":4, "helpen":4, "oplossing":4,
    "innovatie":4, "ontdekking":4, "ontdekt":3, "samenwerking":3, "vrijwilligers":3,
    "schoner":4, "duurzaam":3, "medaille":4, "hoop":3, "voorkomen":3, "voorkomt":3,
    "meer banen":6, "werkgelegenheid groeit":6, "levensverwachting stijgt":6,
    "overlevingskans stijgt":6, "uitstoot daalt":6, "armoede daalt":6,
    "criminaliteit daalt":6, "werkloosheid daalt":6, "faillissementen dalen":5,
    "biodiversiteit groeit":6, "populatie groeit":5,
    "wins":5, "gold":5, "champion":5, "breakthrough":5, "success":4,
    "recovery":5, "recovers":5, "return":4, "rescued":5, "protects":4,
    "improves":4, "improvement":4, "helps":4, "solution":4, "innovation":4, "volunteers":3,
    "discovery":4, "cleaner":4, "sustainable":3, "hope":3, "renewed hope":4, "prevents":3,
    "jobs grow":6, "unemployment falls":6, "emissions fall":6,
    "poverty falls":6, "survival improves":6,
}

NEGATIVE_PHRASES = {
    "oorlog":-10, "doden":-10, "dood":-10, "omgekomen":-10, "moord":-10,
    "geweld":-9, "aanval":-9, "ramp":-10, "explosie":-10, "crisis":-8,
    "gewond":-7, "vermist":-7, "fraude":-7, "dreigt":-6, "zorgelijk":-5, "einde van":-8, "niet door":-10,
    "werkloosheid stijgt":-10, "uitstoot stijgt":-9, "armoede stijgt":-9,
    "sterfte stijgt":-10, "temperatuur stijgt":-5, "faillissementen stijgen":-9,
    "gaat niet door":-10, "kan niet worden gered":-10,
    "war":-10, "dead":-10, "death":-10, "killed":-10, "murder":-10,
    "violence":-9, "attack":-9, "disaster":-10, "explosion":-10,
    "crisis":-8, "wounded":-7, "missing":-7, "fraud":-7, "threat":-6, "cancelled":-10, "canceled":-10,
    "unemployment rises":-10, "emissions rise":-9, "poverty rises":-9,
}

HARD_NEGATIVE_TITLE = [
    "oorlog", "doden", "omgekomen", "moord", "explosie", "zwaar gewond",
    "gaat niet door", "kan niet worden gered", "ramp", "fraude",
    "war", "dead", "killed", "murder", "explosion", "disaster",
    "unemployment rises", "werkloosheid stijgt"
]

CATEGORY_TERMS = {
    "Sport":["sport","voetbal","football","soccer","hockey","tennis","atletiek","athletics",
             "wielrennen","cycling","mountainbike","zwemmen","swimming","olympic","medaille",
             "medal","kampioen","champion","wedstrijd","match","goal","race","marathon","sprint"],
    "Economie & geld":["economie","economy","geld","money","beurs","market","markt","export",
                       "import","business","bedrijf","banen","jobs","inflatie","inflation","inkomen",
                       "income","investment","investering","productie","consumptie","werkloosheid"],
    "Natuur & klimaat":["natuur","nature","klimaat","climate","forest","bos","river","rivier",
                        "ocean","oceaan","biodiversiteit","biodiversity","emission","emissie",
                        "energy","energie","sustainable","duurzaam","ecosystem","ecosysteem"],
    "Dieren":["dier","dieren","animal","animals","bird","birds","vogel","vogels","fish","vis",
              "tiger","tijger","whale","walvis","turtle","schildpad","bee","bij","wolf","dog","hond"],
    "Wetenschap":["wetenschap","science","onderzoek","research","scientist","onderzoeker","study",
                   "studie","space","ruimte","physics","biology","biologie","astronomy","astronomie"],
    "Gezondheid":["gezondheid","health","medical","medisch","medicine","medicijn","patient","patiënt",
                   "care","zorg","therapy","therapie","cancer","kanker","vaccine","vaccin","screening",
                   "survival","overleving"],
    "Technologie & innovatie":["technology","technologie","tech","innovatie","innovation","robot",
                               "chip","software","computer","engineering","battery","batterij",
                               "artificial intelligence","kunstmatige intelligentie","ai"],
    "Cultuur & media":["cultuur","culture","kunst","art","museum","muziek","music","film","boek",
                       "book","media","theater","heritage","erfgoed","painting","schilderij"],
    "Onderwijs & ontwikkeling":["onderwijs","education","school","student","students","leerling",
                                "leerlingen","learning","opleiding","university","universiteit","teacher"],
    "Voeding & leefstijl":["voeding","food","groente","vegetable","fruit","diet","leefstijl",
                            "lifestyle","sleep","slaap","exercise","bewegen","nutrition"],
    "Geschiedenis & mens":["geschiedenis","history","archeologie","archaeology","ancient","oudheid",
                            "fossil","voorouder","ancestor","prehistoric"],
    "Mens & samenleving":["community","gemeenschap","buurt","vrijwillig","volunteer","samenleving",
                           "society","poverty","armoede","refugee","vluchteling","solidarity",
                           "solidariteit","mensenrechten","human rights","vrijwilligers"],
}

CATEGORY_PRIORITY = {
    "Sport":100,"Gezondheid":95,"Dieren":90,"Economie & geld":85,
    "Technologie & innovatie":80,"Natuur & klimaat":75,
    "Onderwijs & ontwikkeling":70,"Cultuur & media":65,
    "Voeding & leefstijl":60,"Geschiedenis & mens":55,
    "Mens & samenleving":50,"Wetenschap":45,
}

ICONS = {
    "Mens & samenleving":"🤝","Economie & geld":"📈","Natuur & klimaat":"🌱",
    "Dieren":"🐾","Wetenschap":"🔬","Gezondheid":"❤️",
    "Technologie & innovatie":"💡","Sport":"🏅","Cultuur & media":"🎨",
    "Onderwijs & ontwikkeling":"🎓","Voeding & leefstijl":"🥬",
    "Geschiedenis & mens":"🏛️","Gewoon leuk":"☀️",
}

def clean(value):
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()

def lname(tag):
    return tag.rsplit("}", 1)[-1].lower()

def child_text(node, names):
    for c in list(node):
        if lname(c.tag) in names and c.text and c.text.strip():
            return clean(c.text)
    return ""

def node_link(node):
    for c in list(node):
        if lname(c.tag) == "link":
            href = c.attrib.get("href")
            if href and c.attrib.get("rel", "alternate") in ("alternate", ""):
                return href.strip()
            if c.text and c.text.strip():
                return c.text.strip()
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

def google_site_feed(domain, region):
    # Niet blind de laatste headlines ophalen. We vragen Google News expliciet
    # om recente artikelen met positieve cues op deze bron.
    if region == "nl":
        cues = (
            'doorbraak OR succes OR kampioen OR goud OR wint OR gewonnen OR '
            'gered OR redding OR herstel OR herstelt OR verbetert OR verbetering OR '
            'ontdekking OR ontdekt OR innovatie OR helpt OR vrijwilligers OR '
            '"overlevingskans" OR "werkloosheid daalt" OR "uitstoot daalt" OR '
            '"armoede daalt" OR "meer banen"'
        )
        q = f"site:{domain} ({cues}) when:7d"
        query = urllib.parse.quote_plus(q)
        return f"https://news.google.com/rss/search?q={query}&hl=nl&gl=NL&ceid=NL:nl"

    cues = (
        'breakthrough OR success OR champion OR gold OR wins OR rescued OR recovery OR '
        'improves OR improvement OR discovery OR innovation OR helps OR volunteers OR '
        '"renewed hope" OR "unemployment falls" OR "emissions fall" OR "poverty falls"'
    )
    q = f"site:{domain} ({cues}) when:7d"
    query = urllib.parse.quote_plus(q)
    return f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

def source_url(src):
    if src["mode"] == "rss":
        return src["url"]
    return google_site_feed(src["domain"], src["region"])

def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*"
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def parse_feed(raw):
    root = ET.fromstring(raw)
    items = []
    for node in root.iter():
        if lname(node.tag) not in ("item", "entry"):
            continue
        title = child_text(node, {"title"})
        url = node_link(node)
        summary = child_text(node, {"description","summary","content","encoded"})
        published = parse_date(child_text(node, {"pubdate","published","updated","date"}))
        if title and url:
            items.append({"title":title,"url":url,"summary":summary,"published":published})
    return items

def wordmatch(text, phrase):
    return bool(re.search(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)", text.lower()))

def lexscore(text, lex):
    return sum(points for phrase, points in lex.items() if wordmatch(text, phrase))

HARD_NEGATIVE_PATTERNS = [
    r"\bniet(?:\s+\w+){0,3}\s+door\b",
    r"\bgaat(?:\s+\w+){0,3}\s+niet\s+door\b",
    r"\beinde van\b",
    r"\bwerkloosheid\s+(?:fors\s+)?stijgt\b",
    r"\buitstoot\s+(?:fors\s+)?stijgt\b",
    r"\barmoede\s+(?:fors\s+)?stijgt\b",
    r"\bsterfte\s+(?:fors\s+)?stijgt\b",
    r"\b(?:cancelled|canceled)\b",
]

POSITIVE_CONTEXT_PATTERNS = [
    r"\bkans\b.*\boverleven\b.*\b(?:groter|hoger|toegenomen)\b",
    r"\boverlevingskans\b.*\b(?:stijgt|groter|hoger|toeneemt)\b",
    r"\bwerkloosheid\b.*\b(?:daalt|lager|afgenomen)\b",
    r"\buitstoot\b.*\b(?:daalt|lager|afgenomen|verminderd)\b",
    r"\barmoede\b.*\b(?:daalt|lager|afgenomen)\b",
    r"\b(?:meer|extra)\s+banen\b",
    r"\b(?:survival|survival rate)\b.*\b(?:improves|higher|increases)\b",
    r"\bunemployment\b.*\b(?:falls|lower|drops)\b",
    r"\bemissions?\b.*\b(?:fall|falls|lower|drop|drops)\b",
    r"\bpoverty\b.*\b(?:falls|lower|drops)\b",
]

def hard_negative(title):
    t = clean(title).lower()
    if any(p in t for p in HARD_NEGATIVE_TITLE):
        return True
    return any(re.search(pattern, t) for pattern in HARD_NEGATIVE_PATTERNS)

def title_positive_points(title):
    t = clean(title).lower()
    points = lexscore(t, POSITIVE_PHRASES)
    if any(re.search(pattern, t) for pattern in POSITIVE_CONTEXT_PATTERNS):
        points += 6
    return points

def positivity(title, summary):
    # 0.7-regel: een artikel komt alleen in aanmerking als de KOP zelf
    # een positieve ontwikkeling bevat. Een positieve samenvatting mag een
    # negatieve of neutrale kop niet meer redden.
    title_pos = title_positive_points(title)
    if title_pos <= 0:
        return -999

    return (
        3 * title_pos
        + lexscore(summary, POSITIVE_PHRASES)
        + 3 * lexscore(title, NEGATIVE_PHRASES)
        + lexscore(summary, NEGATIVE_PHRASES)
    )

def category(title, summary, hint):
    text = f"{title} {summary}".lower()
    scores = {}

    for cat, terms in CATEGORY_TERMS.items():
        hits = sum(1 for term in terms if wordmatch(text, term))
        if hits:
            scores[cat] = hits

    # Hint helpt bij gelijkspel, maar domineert niet automatisch de inhoud.
    if hint:
        scores[hint] = scores.get(hint, 0) + 1

    if not scores:
        return hint or "Gewoon leuk"

    return max(scores, key=lambda c:(scores[c], CATEGORY_PRIORITY.get(c,0)))

def compact_summary(text, max_chars=260):
    text = clean(text)
    if not text:
        return ""
    # Google News RSS descriptions zijn vaak linklijsten. Dan liever geen rommel tonen.
    if text.count("<a") or "Google News" in text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    candidate = " ".join(sentences[:2]).strip() or text
    if len(candidate) > max_chars:
        candidate = candidate[:max_chars].rsplit(" ",1)[0].rstrip(" ,;:") + "…"
    return candidate

def normurl(url):
    try:
        p = urlparse(url)
        return (p.netloc.lower() + p.path.rstrip("/")).lower()
    except Exception:
        return url.lower().rstrip("/")

def collect():
    now = datetime.now(timezone.utc)
    out, errors, seen = [], [], set()

    for src in SOURCES:
        try:
            feed_items = parse_feed(fetch(source_url(src)))
        except Exception as e:
            errors.append(f'{src["publisher"]}: {type(e).__name__}: {e}')
            continue

        for x in feed_items:
            pub = x["published"]
            age = None
            if pub:
                age = max(0, (now - pub).total_seconds()/3600)
                if age > MAX_AGE_HOURS:
                    continue

            key = normurl(x["url"])
            if key in seen:
                continue
            seen.add(key)

            if hard_negative(x["title"]):
                continue

            pscore = positivity(x["title"], x["summary"])
            if pscore <= 0:
                continue

            out.append({
                "region":src["region"],
                "source":src["publisher"],
                "weight":src["weight"],
                "title":clean(x["title"]),
                "url":x["url"],
                "summary":compact_summary(x["summary"]),
                "hours_old":round(age,1) if age is not None else None,
                "category":category(x["title"],x["summary"],src.get("hint")),
                "positive_score":pscore,
            })

    return out, errors

def quality(x):
    # Positiviteit dominant, bronkwaliteit tweede, versheid als bonus.
    freshness = 0
    if x["hours_old"] is not None:
        if x["hours_old"] <= 24:
            freshness = 3
        elif x["hours_old"] <= 48:
            freshness = 2
        elif x["hours_old"] <= 96:
            freshness = 1

    return x["positive_score"] * 10 + x["weight"] * 4 + freshness

def choose(items, region):
    pool = [x for x in items if x["region"] == region]
    pool.sort(key=lambda x:(-quality(x), x["hours_old"] if x["hours_old"] is not None else 9999))

    selected = []
    counts = {}
    categories = set()

    # Ronde 1: unieke categorieën, <=48 uur.
    for x in pool:
        if len(selected) >= TARGET:
            break
        if x["category"] in categories:
            continue
        if counts.get(x["source"],0) >= MAX_PER_SOURCE:
            continue
        if x["hours_old"] is not None and x["hours_old"] > PREFERRED_AGE_HOURS:
            continue
        selected.append(x)
        categories.add(x["category"])
        counts[x["source"]] = counts.get(x["source"],0) + 1

    # Ronde 2: unieke categorieën, tot 7 dagen.
    for x in pool:
        if len(selected) >= TARGET:
            break
        if x in selected or x["category"] in categories:
            continue
        if counts.get(x["source"],0) >= MAX_PER_SOURCE:
            continue
        selected.append(x)
        categories.add(x["category"])
        counts[x["source"]] = counts.get(x["source"],0) + 1

    # Ronde 3: kwaliteit boven perfecte categoriediversiteit.
    for x in pool:
        if len(selected) >= TARGET:
            break
        if x in selected:
            continue
        if counts.get(x["source"],0) >= MAX_PER_SOURCE:
            continue
        selected.append(x)
        counts[x["source"]] = counts.get(x["source"],0) + 1

    # Brondiversiteit verbeteren.
    def distinct_sources():
        return {x["source"] for x in selected}

    if len(distinct_sources()) < MIN_SOURCES:
        for cand in pool:
            if len(distinct_sources()) >= MIN_SOURCES:
                break
            if cand in selected or cand["source"] in distinct_sources():
                continue
            # vervang zwakste item van bron die dubbel staat
            dup_indexes = [
                i for i,x in enumerate(selected)
                if sum(1 for y in selected if y["source"] == x["source"]) > 1
            ]
            if dup_indexes:
                weakest = min(dup_indexes, key=lambda i: quality(selected[i]))
                selected[weakest] = cand

    selected.sort(key=lambda x:-quality(x))
    return selected[:TARGET]

def story(x, english=False):
    return {
        "category":x["category"],
        "icon":ICONS.get(x["category"],"☀️"),
        "title":x["title"],
        "summary":x["summary"] or "Een positieve ontwikkeling. Lees het volledige verhaal bij de bron.",
        "source":x["source"] + (" · English" if english else ""),
        "url":x["url"],
    }

def display_date():
    days=["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
    months=["januari","februari","maart","april","mei","juni","juli","augustus",
            "september","oktober","november","december"]
    n=datetime.now().astimezone()
    return f"{days[n.weekday()]} {n.day} {months[n.month-1]}"

def main():
    items, errors = collect()
    nl = choose(items, "nl")
    intl = choose(items, "int")

    nl_pool = [x for x in items if x["region"] == "nl"]
    int_pool = [x for x in items if x["region"] == "int"]
    print(f"Positieve kandidaten totaal: {len(items)}")
    print(f"NL kandidaten vóór selectie: {len(nl_pool)} | bronnen: {len(set(x['source'] for x in nl_pool))}")
    print(f"INT kandidaten vóór selectie: {len(int_pool)} | bronnen: {len(set(x['source'] for x in int_pool))}")
    print(f"NL: {len(nl)} | bronnen: {len(set(x['source'] for x in nl))} | categorieën: {len(set(x['category'] for x in nl))}")
    print(f"INT: {len(intl)} | bronnen: {len(set(x['source'] for x in intl))} | categorieën: {len(set(x['category'] for x in intl))}")

    print("\nNL-selectie:")
    for x in nl:
        print(f"- [{x['category']}] {x['source']} ({quality(x):.1f}): {x['title']}")

    print("\nInternationale selectie:")
    for x in intl:
        print(f"- [{x['category']}] {x['source']} ({quality(x):.1f}): {x['title']}")

    if errors:
        print(f"\nFeedfouten ({len(errors)}):")
        for e in errors:
            print(" -", e)

    if len(nl) != TARGET or len(intl) != TARGET:
        print(f"\nNIET PUBLICEREN: 7 + 7 vereist. Gevonden {len(nl)} NL + {len(intl)} INT.")
        sys.exit(0)

    if len(set(x["source"] for x in nl)) < MIN_SOURCES:
        print("\nNIET PUBLICEREN: Nederlandse selectie heeft minder dan 5 bronnen.")
        sys.exit(0)

    if len(set(x["source"] for x in intl)) < MIN_SOURCES:
        print("\nNIET PUBLICEREN: internationale selectie heeft minder dan 5 bronnen.")
        sys.exit(0)

    now = datetime.now().astimezone()
    data = {
        "edition":{
            "date":now.strftime("%Y-%m-%d"),
            "displayDate":display_date(),
            "title":"Goed nieuws",
            "tagline":"Dit gebeurt ook.",
            "intro":"14 korte verhalen. Geen doomscrollen, geen eindeloze feed.",
            "closingTitle":"Dat was het.",
            "closingText":"Ga lekker verder met je dag. ☀️"
        },
        "dutch":[story(x) for x in nl],
        "international":[story(x,True) for x in intl],
        "_meta":{
            "generated_at":now.isoformat(),
            "generator":"Goed nieuws 0.7 auto",
            "candidate_count":len(items),
            "feed_errors":errors
        }
    }

    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print("\nPUBLICEREN: nieuwe 7+7-editie geschreven.")

if __name__ == "__main__":
    main()
