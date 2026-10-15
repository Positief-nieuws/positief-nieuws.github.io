#!/usr/bin/env python3
"""
Goed nieuws - kandidaten 0.1

Doel:
- dagelijks breed recente potentiële Goed nieuws-verhalen verzamelen;
- simpele technische rommel verwijderen;
- géén definitieve 6+6 redactionele selectie doen;
- kandidaten.json klaarzetten voor een AI-redacteur of handmatige selectie.

Bewust NIET in dit script:
- bepalen of iets "echt goed nieuws" is;
- Nederlands lezersperspectief inhoudelijk beoordelen;
- complexe semantische categorisatie;
- 6+6 forceren.

Dat is precies het werk waar een taalmodel later beter in is.
"""

from __future__ import annotations

import hashlib
import concurrent.futures
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "kandidaten.json"

MAX_AGE_HOURS = 168        # maximaal 7 dagen
PREFERRED_AGE_HOURS = 48   # versheidsbonus
MAX_PER_SOURCE = 6         # voorkom dat 1 bron de lijst overneemt
MAX_PER_REGION = 40        # shortlist voor latere AI-selectie
USER_AGENT = "GoedNieuwsKandidatenBot/0.1"

# Gecureerde HTML-bronnen (nu: NU.nl Goed nieuws) hebben op de overzichtspagina
# niet altijd een publicatiedatum. We proberen daarom de artikelpagina zelf uit te lezen.
CURATED_DATE_FETCH_TIMEOUT = 8
CURATED_DATE_WORKERS = 6
CURATED_UNKNOWN_DATE_BONUS = 5
CURATED_UNKNOWN_DATE_PENALTY = -4

from source_registry import (load_registry, active_channels, canonical_url, load_history,
                             history_matches, due, atomic_json)
from zoneinfo import ZoneInfo
from build_editions import canonical_category

SOURCES = active_channels()
HEALTH_PATH = ROOT / "source_health.json"
STATE_PATH = ROOT / "source_state.json"
CHANNEL_HEALTH = {}
CHANNEL_STATE = {}

# Brede positieve signalen. Dit is alleen VOORSELECTIE.
# Een match betekent dus niet automatisch dat iets in Goed nieuws hoort.
POSITIVE_CUES_NL = [
    "wint", "gewonnen", "goud", "zilver", "brons", "kampioen", "record",
    "doorbraak", "succes", "herstelt", "herstel", "gered", "redding",
    "verbetering", "verbetert", "ontdekking", "ontdekt", "innovatie",
    "helpt", "helpen", "vrijwilligers", "beschermd", "beschermt",
    "daalt", "dalen", "groeit", "toename", "vooruitgang", "oplossing",
    "schoner", "duurzaam", "overlevingskans", "meer banen", "hoop",
]

POSITIVE_CUES_INT = [
    "wins", "won", "gold", "silver", "bronze", "champion", "record",
    "breakthrough", "success", "recovery", "recovers", "rescued", "rescue",
    "improves", "improvement", "discovery", "innovation", "helps",
    "volunteers", "protects", "restored", "saved", "falls", "drops",
    "growth", "progress", "solution", "cleaner", "sustainable", "hope",
]

# Alleen echt evidente rommel/negativiteit. We houden dit bewust beperkt.
HARD_BLOCK = [
    "oorlog", "omgekomen", "moord", "zwaar gewond", "massaontslag",
    "banen weg", "zedenzaak", "seksueel misbruik", "explosie",
    "wapenopslagplaats", "werkloosheid stijgt", "uitstoot stijgt",
    "gaat niet door", "kan niet worden gered",
    "war", "killed", "murder", "mass layoffs", "job cuts",
    "sexual abuse", "explosion", "weapons cache",
    "unemployment rises", "emissions rise", "cancelled", "canceled",
]

JUNK_TERMS = [
    "vacature", "vacancy", "job opening", "fixed term position",
    "fixed-term position", "apply now", "we are hiring", "internship",
    "weather forecast", "weerbericht", "weersverwachting",
    "exports by country", "imports by country", "data - wits",
    "including silver plated with gold",
]

STOPWORDS = {
    "de","het","een","en","van","voor","op","in","met","na","bij","om","te","is","zijn",
    "wordt","worden","dat","die","dit","als","aan","nu","video","weer","the","a","an","and",
    "of","for","to","in","on","with","after","by","from","as","at","new","news","says",
}

CATEGORY_TERMS = {
    "Sport": ["sport","voetbal","football","hockey","tennis","atletiek","athletics","cycling",
              "wielrennen","f1","formula 1","formule 1","race","medaille","medal","kampioen"],
    "Gezondheid": ["gezondheid","health","medical","medisch","kanker","cancer","screening",
                   "patient","patiënt","therapy","therapie","dementia","alzheimer","retina"],
    "Wetenschap": ["wetenschap","science","research","onderzoek","study","studie","space","ruimte",
                   "physics","biology","astronomy"],
    "Natuur & klimaat": ["natuur","nature","klimaat","climate","forest","bos","ocean","oceaan",
                         "biodiversity","biodiversiteit","emission","emissie","ecosystem"],
    "Dieren": ["dier","dieren","animal","animals","bird","vogel","fish","vis","whale","walvis",
               "turtle","schildpad","bee","bij","wolf"],
    "Technologie & innovatie": ["technology","technologie","tech","innovation","innovatie","robot",
                                "chip","software","computer","battery","batterij","ai"],
    "Economie & geld": ["economie","economy","business","bedrijf","banen","jobs","inflatie",
                        "inflation","export","income","inkomen","investment","investering"],
    "Mens & samenleving": ["community","gemeenschap","vrijwillig","volunteer","society","samenleving",
                            "human rights","mensenrechten","refugee","vluchteling","solidarity"],
    "Onderwijs & ontwikkeling": ["onderwijs","education","school","student","leerling","university",
                                  "universiteit","learning","teacher"],
    "Cultuur & media": ["cultuur","culture","art","kunst","museum","muziek","music","film","boek",
                        "book","media","theater","heritage","erfgoed"],
    "Voeding & leefstijl": ["voeding","food","nutrition","groente","fruit","diet","leefstijl",
                             "lifestyle","sleep","slaap"],
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

def google_site_feed(domain, region, language=None, query_scope="broad"):
    language = language or ("nl" if region == "nl" else "en")
    if language == "nl":
        cues = "doorbraak OR succes OR herstel OR verbetering OR ontdekking OR helpt OR oplossing"
        locale = "&hl=nl&gl=NL&ceid=NL:nl"
    elif language == "de":
        cues = "Fortschritt OR Erfolg OR Forschung OR verbessert OR gerettet OR Lösung"
        locale = "&hl=de&gl=DE&ceid=DE:de"
    else:
        cues = "breakthrough OR success OR recovery OR improvement OR discovery OR solution"
        locale = "&hl=en-US&gl=US&ceid=US:en"
    # Broad discovery avoids requiring an optimistic keyword before an editor sees a story.
    query = f"site:{domain} when:7d" if query_scope == "broad" else f"site:{domain} ({cues}) when:7d"
    return "https://news.google.com/rss/search?q=" + urllib.parse.quote_plus(query) + locale


class NuGoodNewsParser(HTMLParser):
    """
    Haalt artikel-links en zichtbare titels uit de NU.nl Goed nieuws-pagina.

    Publisher blijft 'NU.nl', zodat MAX_PER_SOURCE gewoon blijft gelden.
    De curation_bonus beïnvloedt alleen de voorselectie, niet de eindredactie.
    """

    ARTICLE_PATH = re.compile(r"/\d{6,8}/[^/?#]+\.html$")

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self._seen = set()
        self._href = None
        self._label = ""
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return

        attr = dict(attrs)
        href = (attr.get("href") or "").strip()
        if not href:
            return

        absolute = urllib.parse.urljoin("https://www.nu.nl/", href)
        parsed = urlparse(absolute)

        if parsed.netloc.lower() not in {"nu.nl", "www.nu.nl"}:
            return
        if not self.ARTICLE_PATH.search(parsed.path):
            return

        self._href = absolute.split("#", 1)[0]
        self._label = clean(attr.get("aria-label") or attr.get("title") or "")
        self._text = []

    def handle_data(self, data):
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "a" or not self._href:
            return

        title = clean(" ".join(self._text)) or self._label
        href = self._href

        self._href = None
        self._label = ""
        self._text = []

        if len(title) < 12:
            return
        if title.lower() in {"lees meer", "bekijk artikel", "naar artikel"}:
            return

        key = normurl(href)
        if key in self._seen:
            return
        self._seen.add(key)

        self.items.append({
            "title": title,
            "url": href,
            "summary": "",
            "published": None,
        })


def parse_nu_good_news(raw, max_items=30):
    """
    De overzichtspagina is al redactioneel als 'Goed nieuws' gecureerd.
    We nemen alleen de eerste actuele artikel-links mee.
    """
    text = raw.decode("utf-8", errors="replace")
    parser = NuGoodNewsParser()
    parser.feed(text)
    return parser.items[:max_items]


def source_url(src):
    if src["mode"] == "rss":
        return src["url"]
    return google_site_feed(src["domain"], src["region"], src.get("language"), src.get("query_scope", "broad"))

def fetch(url, html=False, timeout=20):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; PositiefNieuwsBot/0.2; +https://positief-nieuws.github.io/)"
            if html else USER_AGENT
        ),
        "Accept": (
            "text/html,application/xhtml+xml,*/*"
            if html else "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*"
        ),
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def extract_published_date_from_html(html_text):
    """
    Zoek de oorspronkelijke publicatiedatum in een artikelpagina.

    Volgorde:
    1. JSON-LD datePublished/dateCreated/uploadDate;
    2. meta-tags zoals article:published_time/datePublished;
    3. <time datetime="..."> als laatste fallback.
    """
    candidates = []

    # JSON-LD is op nieuwssites meestal de betrouwbaarste bron.
    scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html_text,
        flags=re.I | re.S,
    )

    def inspect(value):
        if isinstance(value, dict):
            for key in ("datePublished", "dateCreated", "uploadDate"):
                raw_value = value.get(key)
                if isinstance(raw_value, str) and raw_value.strip():
                    candidates.append(raw_value.strip())
            for child in value.values():
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    for raw_script in scripts:
        try:
            inspect(json.loads(unescape(raw_script).strip()))
        except Exception:
            continue

    # Meta-tags, o.a. Open Graph / schema.org.
    for tag in re.findall(r"<meta\b[^>]*>", html_text, flags=re.I):
        attrs = {
            key.lower(): unescape(value).strip()
            for key, _, value in re.findall(
                r'([:\w-]+)\s*=\s*(["\'])(.*?)\2',
                tag,
                flags=re.I | re.S,
            )
        }
        marker = (
            attrs.get("property")
            or attrs.get("name")
            or attrs.get("itemprop")
            or ""
        ).lower()
        if marker in {
            "article:published_time",
            "datepublished",
            "date",
            "publishdate",
            "publish-date",
            "dc.date",
            "dc.date.issued",
        }:
            content = attrs.get("content")
            if content:
                candidates.append(content)

    # Laatste fallback: een expliciete <time datetime="...">.
    for tag in re.findall(r"<time\b[^>]*>", html_text, flags=re.I):
        attrs = {
            key.lower(): unescape(value).strip()
            for key, _, value in re.findall(
                r'([:\w-]+)\s*=\s*(["\'])(.*?)\2',
                tag,
                flags=re.I | re.S,
            )
        }
        if attrs.get("datetime"):
            candidates.append(attrs["datetime"])

    parsed = []
    for value in candidates:
        dt = parse_date(value)
        if dt is not None:
            parsed.append(dt)

    if not parsed:
        return None

    # Kies de vroegste plausibele datum: bij updates staat soms ook een latere modified-date.
    return min(parsed)


def fetch_article_published_date(url):
    try:
        raw = fetch(url, html=True, timeout=CURATED_DATE_FETCH_TIMEOUT)
        html_text = raw.decode("utf-8", errors="replace")
        return extract_published_date_from_html(html_text)
    except Exception:
        return None


def enrich_curated_dates(items):
    """
    Verrijk gecureerde items parallel met hun echte publicatiedatum.
    Een mislukte datumlookup is geen feedfout: het item mag kandidaat blijven,
    maar krijgt later duidelijk minder voorrang.
    """
    if not items:
        return items

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=CURATED_DATE_WORKERS
    ) as executor:
        future_to_item = {
            executor.submit(fetch_article_published_date, item["url"]): item
            for item in items
            if not item.get("published")
        }

        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            try:
                item["published"] = future.result()
            except Exception:
                item["published"] = None

    return items


def parse_feed(raw):
    root = ET.fromstring(raw)
    items = []
    for node in root.iter():
        if lname(node.tag) not in ("item", "entry"):
            continue
        title = child_text(node, {"title"})
        url = node_link(node)
        summary = child_text(node, {"description","summary","content","encoded"})
        published = parse_date(child_text(node, {"pubdate", "published", "date"}))
        updated = parse_date(child_text(node, {"updated"}))
        if title and url:
            items.append({"title": title, "url": url, "summary": summary, "published": published, "updated": updated})
    return items

def matched_terms(text, terms):
    """Match complete terms; 'war' must not match 'award' or 'forward'."""
    value = clean(text).casefold()
    return [term for term in terms if re.search(r"(?<!\w)" + re.escape(term.casefold()) + r"(?!\w)", value)]

def contains(text, terms):
    return bool(matched_terms(text, terms))

def cue_score(title, summary, region):
    cues = POSITIVE_CUES_NL if region == "nl" else POSITIVE_CUES_INT
    t = clean(title).lower()
    s = clean(summary).lower()
    # Titel weegt zwaarder, maar dit blijft slechts een voorselectiescore.
    return 3 * len(matched_terms(t, cues)) + len(matched_terms(s, cues))

def category_hint(title, summary, source_hint=None):
    title_text = clean(title).lower()
    summary_text = clean(summary).lower()
    scores = {}
    for cat, terms in CATEGORY_TERMS.items():
        th = sum(1 for term in terms if term in title_text)
        sh = sum(1 for term in terms if term in summary_text)
        if th or sh:
            scores[cat] = th * 3 + sh
    if source_hint:
        scores[source_hint] = scores.get(source_hint, 0) + 1
    if not scores:
        return canonical_category(source_hint or "") or "Onbekend"
    return canonical_category(max(scores, key=scores.get)) or "Onbekend"

def compact_summary(text, max_chars=420):
    text = clean(text)
    if not text:
        return ""
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return text

def normurl(url):
    return canonical_url(url)


def title_tokens(title):
    words = re.findall(r"[a-z0-9à-ÿ]+", clean(title).lower())
    return {w for w in words if len(w) >= 4 and w not in STOPWORDS}

def near_duplicate(a, b):
    ta, tb = title_tokens(a["title"]), title_tokens(b["title"])
    if not ta or not tb:
        return False
    inter = len(ta & tb)
    union = len(ta | tb)
    return bool(union and inter / union >= 0.58)

def item_id(source, title, url):
    raw = f"{source}|{title}|{url}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:12]


READING_SPEED_WPM = 220
READING_TIME_MAX_MINUTES = 15
READING_TIME_FETCH_TIMEOUT = 8
READING_TIME_WORKERS = 8

class ArticleTextParser(HTMLParser):
    """
    Eenvoudige, bron-onafhankelijke tekstextractie voor een leestijdschatting.
    We tellen vooral tekst uit <p>-blokken en negeren navigatie/footers/scripts.
    """
    SKIP_TAGS = {
        "script", "style", "nav", "footer", "header", "aside",
        "form", "button", "svg", "noscript"
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.in_p = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        if tag == "p" and self.skip_depth == 0:
            self.in_p += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "p" and self.in_p:
            self.in_p -= 1
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.skip_depth == 0 and self.in_p:
            value = clean(data)
            if value:
                self.parts.append(value)


def words_in_text(text):
    return len(re.findall(r"\b[\wÀ-ÿ'-]+\b", clean(text), flags=re.UNICODE))


def json_ld_reading_words(html_text):
    """
    Veel nieuwssites publiceren articleBody of wordCount in JSON-LD.
    Als dat aanwezig is, is dit meestal betrouwbaarder dan generieke HTML-extractie.
    """
    scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html_text,
        flags=re.I | re.S,
    )

    best = 0

    def inspect(value):
        nonlocal best

        if isinstance(value, dict):
            word_count = value.get("wordCount")
            try:
                if word_count is not None:
                    best = max(best, int(float(word_count)))
            except (TypeError, ValueError):
                pass

            article_body = value.get("articleBody")
            if isinstance(article_body, str):
                best = max(best, words_in_text(article_body))

            for child in value.values():
                inspect(child)

        elif isinstance(value, list):
            for child in value:
                inspect(child)

    for raw in scripts:
        try:
            inspect(json.loads(raw.strip()))
        except Exception:
            continue

    return best


def estimate_reading_time(url):
    """
    Schat de leestijd van het bronartikel.
    Retourneert None als de pagina niet betrouwbaar genoeg uit te lezen is.
    """
    try:
        raw = fetch(url, html=True, timeout=READING_TIME_FETCH_TIMEOUT)
        html_text = raw.decode("utf-8", errors="replace")

        word_count = json_ld_reading_words(html_text)

        if word_count < 120:
            parser = ArticleTextParser()
            parser.feed(html_text)
            word_count = max(
                word_count,
                words_in_text(" ".join(parser.parts))
            )

        # Minder dan 120 woorden is vaak een video-, galerij- of landingspagina.
        if word_count < 120:
            return None

        minutes = max(1, round(word_count / READING_SPEED_WPM))
        return min(minutes, READING_TIME_MAX_MINUTES)

    except Exception:
        return None


def add_reading_times(items):
    """
    Verrijk alleen de shortlist, niet alle ruwe kandidaten.
    Zo blijft de GitHub Action snel en worden hooguit 80 pagina's parallel bekeken.
    """
    if not items:
        return items

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=READING_TIME_WORKERS
    ) as executor:
        futures = {
            executor.submit(estimate_reading_time, item["url"]): item
            for item in items
        }

        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            try:
                item["reading_time_minutes"] = future.result()
            except Exception:
                item["reading_time_minutes"] = None

    return items


def collect(now=None, sources=None, history=None, force=False):
    global CHANNEL_HEALTH, CHANNEL_STATE
    now = now or datetime.now(timezone.utc)
    history = load_history() if history is None else history
    sources = SOURCES if sources is None else sources
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}
    health, saved = {}, {}
    candidates, errors, seen_urls = [], [], set()
    def read_channel(src):
        cid = src["channel_id"]
        previous = state.get(cid, {})
        use_cache = not force and previous.get("discovery_version") == 3 and not due(src, previous, now)
        source_error = None
        if use_cache:
            items = [{**x, "published":parse_date(x.get("published")), "updated":parse_date(x.get("updated"))} for x in previous.get("items",[])]
        else:
            try:
                if src["mode"] == "curated_html":
                    items = parse_nu_good_news(fetch(src["url"], html=True))
                    enrich_curated_dates(items)
                else:
                    urls = [source_url(src)]
                    if src["mode"] == "google_site":
                        urls.append(google_site_feed(src["domain"], src["region"], src.get("language"), "positive"))
                    items, discovery_errors = [], []
                    for url in dict.fromkeys(urls):
                        try:
                            raw = fetch(url)
                            if lname(ET.fromstring(raw).tag) not in {"rss","feed","rdf"}:
                                raise ValueError("Respons is geen RSS/Atom-feed")
                            items.extend(parse_feed(raw))
                        except Exception as exc:
                            discovery_errors.append(f"{type(exc).__name__}: {exc}")
                    if discovery_errors:
                        source_error = "; ".join(discovery_errors)
                    if len(discovery_errors) == len(set(urls)):
                        raise ValueError(source_error)
                # Search result limits must not silently erase a recently found story.
                fresh_keys = {normurl(x["url"]) for x in items}
                for x in previous.get("items", []):
                    pub = parse_date(x.get("published"))
                    if pub and 0 <= (now-pub).total_seconds()/3600 <= MAX_AGE_HOURS and normurl(x["url"]) not in fresh_keys:
                        items.append({**x, "published":pub, "updated":parse_date(x.get("updated")),
                            "discovery_origin":"prior_recent_metadata", "discovered_at":x.get("discovered_at") or previous.get("last_success_at")})
                        fresh_keys.add(normurl(x["url"]))
                # Cache only discovery metadata, not copied article text.
                serialized = [{"title":x["title"],"url":x["url"],"summary":"",
                    "published":x.get("published").isoformat() if x.get("published") else None,
                    "updated":x.get("updated").isoformat() if x.get("updated") else None,
                    "cached_signal_score":x.get("cached_signal_score",cue_score(x["title"],x.get("summary",""),src["region"])),
                    "cached_category_hint":x.get("cached_category_hint") or category_hint(x["title"],x.get("summary",""),src.get("hint")),
                    "discovery_origin":x.get("discovery_origin", "current_fetch"), "discovered_at":x.get("discovered_at") or now.isoformat()}
                    for x in items]
                previous = {"last_success_at":now.isoformat(),"last_error":source_error,"items":serialized,"discovery_version":3}
            except Exception as exc:
                source_error = f"{type(exc).__name__}: {exc}"
                previous = {**previous,"last_error":source_error}
                items = [{**x,"published":parse_date(x.get("published")),"updated":parse_date(x.get("updated"))} for x in previous.get("items",[])]
        return src, items, previous, source_error, use_cache
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        fetched = list(executor.map(read_channel, sources))
    for src, items, previous, source_error, use_cache in fetched:
        cid = src["channel_id"]
        saved[cid] = previous
        if source_error: errors.append(f'{src["publisher"]} ({cid}): {source_error}')
        health[cid] = {"source_id":src["source_id"],"organization_id":src["organization_id"],
            "mode":src["mode"],"last_success_at":previous.get("last_success_at"),
            "last_error":source_error,"cached":use_cache or bool(source_error),"items":len(items),
            "check_frequency":src["check_frequency"],"checked_at":now.isoformat(),
            "next_check_at":(now if source_error else datetime.fromisoformat(previous["last_success_at"])+timedelta(hours={"every_edition":20,"twice_weekly":72,"weekly":168}[src["check_frequency"]])).isoformat()}
        for x in items:
            title, summary = clean(x["title"]), clean(x.get("summary"))
            # Ambiguous keywords (e.g. weather forecast research) stay available for review.
            pub = x.get("published")
            age = (now-pub).total_seconds()/3600 if pub else None
            if age is not None and age > MAX_AGE_HOURS: continue
            date_warnings=[]
            if age is not None and age < -1: date_warnings.append("future_publication_date")
            if pub is None: date_warnings.append("publication_date_unknown")
            if x.get("discovery_origin") == "prior_recent_metadata": date_warnings.append("prior_discovery_requires_original_check")
            if src["mode"] == "google_site": date_warnings.append("search_date_requires_original_check")
            url_key = normurl(x["url"])
            if url_key in seen_urls: continue
            seen_urls.add(url_key)
            signal = x.get("cached_signal_score", cue_score(title, summary, src["region"]))
            # A source, German feeds and stories about recovery from a crisis must
            # not disappear simply because an NL/EN positive keyword is absent.
            curation_bonus = min(src.get("curation_bonus",0),5)
            penalty = -4 if date_warnings else 0
            if date_warnings: curation_bonus=0
            entry = {"id":item_id(src["source_id"],title,x["url"]), "source_id":src["source_id"],
                "organization_id":src["organization_id"], "channel_id":cid,
                "source_category":src["source_category"], "region":src["region"],
                "region_basis":"source_hint_requires_editorial_check", "source":src["publisher"],
                "title":title,"summary":compact_summary(summary),"url":x["url"],
                "published":pub.isoformat() if pub else None,
                "updated":x.get("updated").isoformat() if x.get("updated") else None,
                "event_date":None,"date_warnings":date_warnings,
                "discovery_origin":x.get("discovery_origin", "current_fetch"), "discovered_at":x.get("discovered_at") or previous.get("last_success_at"),
                "hours_old":round(age,1) if age is not None else None,
                "category_hint":canonical_category(x.get("cached_category_hint") or "") or category_hint(title,summary,src.get("hint")),
                "priority":src.get("priority","P2"),"language":src.get("language","en"),
                "signal_score":signal,"source_weight":src.get("weight",1),
                "curation_bonus":curation_bonus,"freshness_penalty":penalty,
                "curated_source":src.get("curated_source"),"discovery":src["mode"],
                "editorial_warnings":(["negative_keyword_requires_context"] if contains(title,HARD_BLOCK) else []) + (["possible_non_story_requires_review"] if contains(title,JUNK_TERMS) else []),
                "history_matches":history_matches(x,history),"source_error":source_error}
            # Title similarity is a warning; follow-up developments remain possible.
            entry["history_matches"] += [{"edition_date":h["edition_date"],"title":h.get("title",""),"kind":"similar_title"}
                for h in history if near_duplicate(entry,{"title":h.get("title","")})][:5]
            candidates.append(entry)
    CHANNEL_HEALTH, CHANNEL_STATE = health, saved
    return candidates, errors

def rank(item):
    freshness = 0
    if item["hours_old"] is not None and item["hours_old"] >= 0:
        if item["hours_old"] <= 24:
            freshness = 5
        elif item["hours_old"] <= 48:
            freshness = 3
        elif item["hours_old"] <= 96:
            freshness = 1
    return (
        item["signal_score"] * 5
        + item["source_weight"] * 3
        + freshness
        + item.get("curation_bonus", 0)
        + item.get("freshness_penalty", 0)
        + {"P1":2,"P2":1,"P3":0}.get(item.get("priority"),0)
    )

def shortlist(items, region):
    """Navigation overview only: all candidates are also exported for editorial review."""
    pool = [x for x in items if x["region"] == region]
    pool.sort(key=lambda x:(bool(x.get("date_warnings")),bool(x.get("history_matches")), -rank(x)))
    selected, per_source, per_theme = [], {}, {}
    # First pass gives varied themes a place. Second fills remaining slots.
    for source_limit, theme_limit in ((2, 10), (MAX_PER_SOURCE, MAX_PER_REGION)):
        for item in pool:
            if len(selected) >= MAX_PER_REGION: break
            if item in selected: continue
            org=item.get("organization_id",item["source"])
            theme=item["category_hint"]
            if per_source.get(org,0)>=source_limit or per_theme.get(theme,0)>=theme_limit: continue
            if any(near_duplicate(item,other) for other in selected): continue
            selected.append(item);per_source[org]=per_source.get(org,0)+1;per_theme[theme]=per_theme.get(theme,0)+1
    return selected

def coverage_report(health, registry):
    """Make incomplete discovery explicit instead of treating HTTP success as coverage."""
    tasks = []
    for cid, channel in sorted(health.items()):
        reasons = []
        if channel.get("last_error"): reasons.append("fetch_failed")
        if channel.get("mode") == "google_site": reasons.append("search_is_not_complete")
        if not channel.get("items"): reasons.append("empty_channel")
        if reasons:
            tasks.append({"id": cid, "source_id": channel["source_id"], "reasons": reasons})
    for source in registry["sources"]:
        if source.get("enabled") and source["category"] != "C" and source["check_frequency"] == "manual":
            tasks.append({"id": "manual:" + source["source_id"], "source_id": source["source_id"], "reasons": ["manual_evidence_source_needs_current_check"]})
    return {"technical_success_is_not_complete_discovery": True, "tasks": tasks}

def main():
    all_candidates, errors = collect(force="--force" in __import__("sys").argv)
    nl = shortlist(all_candidates, "nl")
    intl = shortlist(all_candidates, "int")

    # Voeg alleen aan de uiteindelijke shortlists een geschatte leestijd toe.
    add_reading_times(nl)
    add_reading_times(intl)

    now = datetime.now(ZoneInfo("Europe/Amsterdam"))

    data = {
        "meta": {
            "generated_at": now.isoformat(),
            "generator": "Positief nieuws kandidaten 0.6",
            "purpose": "Voorselectie voor AI-redactie; dit is NIET de definitieve Goed nieuws-editie.",
            "max_age_hours": MAX_AGE_HOURS,
            "max_per_region": MAX_PER_REGION,
            "stats": {
                "raw_candidates": len(all_candidates),
                "nl_shortlist": len(nl),
                "nl_sources": len({x["source"] for x in nl}),
                "international_shortlist": len(intl),
                "international_sources": len({x["source"] for x in intl}),
                "feed_errors": len(errors),
            },
            "feed_errors": errors,
            "collection_complete": len(errors) == 0 and len(nl) >= 6 and len(intl) >= 6,
            "editorial_coverage_complete": False,
            "collection_complete_meaning": "Technical fetch success only; search feeds do not prove complete source coverage.",
            "source_registry": "sources.json",
            "registry_sha256": hashlib.sha256((ROOT/"sources.json").read_bytes()).hexdigest(),
            "editorial_policy": "editorial_policy.json",
            "active_channels": len(SOURCES),
            "channel_health": CHANNEL_HEALTH,
        },
        "editorial_brief": {
            "audience": "Nederlandse lezers",
            "target": "Kies 6 Nederlandse verhalen, 6 internationale verhalen en 3 actuele headlines voor maandag/donderdag.",
            "output_contract": {
                "news": "Bestaande nieuws.json-structuur behouden; regio bepalen op het nieuwsfeit.",
                "dossier": "Maak tijdens brononderzoek het dossier volgens REDACTIE.txt en prepare_dossier.py; geen tweede handmatige onderzoeksronde.",
                "approval": "approved blijft false totdat de eigenaar de exacte editie heeft beoordeeld.",
                "check": "editorial_check.py moet slagen; live publicatie vraagt afzonderlijke toestemming.",
            },
            "principles": [
                "Echt positief nieuws, niet alleen een positief woord in een negatieve kop.",
                "Nederlandse selectie moet relevant zijn voor Nederlandse lezers.",
                "Universele vooruitgang in gezondheid, wetenschap, natuur, dieren en technologie mag ook.",
                "Geen dubbel nieuwsfeit.",
                "Bron- en categorievariatie.",
                "Nieuwsfilters leveren ideeën; controleer primaire bewijsbronnen en het dossier volgens REDACTIE.txt.",
                "Regionale indeling is een bronhint: stel NL/wereld vast op het nieuwsfeit.",
                "Controleer datumwaarschuwingen en historische matches; geen automatische goedkeuring.",
                "Voer editorial_check.py uit voor iedere publicatie en ieder nieuwsbriefconcept.",
                "Geen vacatures, losse weersverwachtingen, celebrity-fluff of puur triviale uitslagen.",
                "Eerste verhaal moet direct prettig en positief voelen.",
                "Beoordeel de volledige all_candidates-lijst per bron; de top40 is geen redactionele grens.",
                "NL eerst, daarna wereld; volgorde op nieuwsfeit en redactionele kwaliteit, niet op brontaal.",
                "Gebruik selection_preferences.json en rond de brondekkings- en reservecontrole af vóór het eerste concept.",
                "Behoud reading_time_minutes bij geselecteerde artikelen als die waarde beschikbaar is.",
            ],
        },
        "all_candidates": all_candidates,
        "review_index_by_source": {sid:[x["id"] for x in all_candidates if x["source_id"] == sid] for sid in sorted({x["source_id"] for x in all_candidates})},
        "coverage": coverage_report(CHANNEL_HEALTH, load_registry()),
        "review_contract": {"scope": "all_candidates, not only the two shortlists", "required_before_concept": "selection_check.py", "review_file": "selectie/YYYY-MM-DD.json", "shortlist_is_exhaustive": False},
        "nl_candidates": nl,
        "international_candidates": intl,
    }

    atomic_json(OUTPUT, data)
    atomic_json(HEALTH_PATH, {"generated_at":now.isoformat(),"channels":CHANNEL_HEALTH})
    atomic_json(STATE_PATH, CHANNEL_STATE)

    print(f"Ruwe kandidaten: {len(all_candidates)}")
    print(f"NL shortlist: {len(nl)} | bronnen: {len({x['source'] for x in nl})}")
    print(f"INT shortlist: {len(intl)} | bronnen: {len({x['source'] for x in intl})}")
    print(f"Feedfouten: {len(errors)}")
    print("GESCHREVEN: kandidaten.json")
    print("nieuws.json is bewust NIET aangepast.")

if __name__ == "__main__":
    main()
