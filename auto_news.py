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
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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

SOURCES = [{'publisher': 'NOS',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://feeds.nos.nl/nosnieuwsalgemeen',
  'weight': 2.3,
  'hint': None},
 {'publisher': 'NOS',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://feeds.nos.nl/nosnieuwseconomie',
  'weight': 2.3,
  'hint': 'Economie & geld'},
 {'publisher': 'NOS',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://feeds.nos.nl/nosnieuwscultuurenmedia',
  'weight': 2.3,
  'hint': 'Cultuur & media'},
 {'publisher': 'NOS',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://feeds.nos.nl/nosnieuwstech',
  'weight': 2.3,
  'hint': 'Technologie & innovatie'},
 {'publisher': 'NOS',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://feeds.nos.nl/nosnieuwsopmerkelijk',
  'weight': 2.2,
  'hint': 'Gewoon leuk'},
 {'publisher': 'NOS',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://feeds.nos.nl/nossportalgemeen',
  'weight': 2.3,
  'hint': 'Sport'},
 {'publisher': 'PBL',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://www.pbl.nl/feed/article/rss.xml',
  'weight': 2.5,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'PBL',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://www.pbl.nl/feed/topic/20/article/rss.xml',
  'weight': 2.5,
  'hint': 'Mens & samenleving'},
 {'publisher': 'PBL',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://www.pbl.nl/feed/topic/17/article/rss.xml',
  'weight': 2.5,
  'hint': 'Economie & geld'},
 {'publisher': 'PBL',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://www.pbl.nl/feed/topic/13/article/rss.xml',
  'weight': 2.5,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'PBL',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://www.pbl.nl/feed/topic/9/article/rss.xml',
  'weight': 2.5,
  'hint': 'Voeding & leefstijl'},
 {'publisher': 'PBL',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://www.pbl.nl/feed/topic/11/article/rss.xml',
  'weight': 2.5,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'KNMI',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://www.knmi.nl/rssfeeds/rss_KNMInieuwsberichten',
  'weight': 2.5,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'KNMI',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://www.knmi.nl/rssfeeds/rss_KNMIklimaatberichten',
  'weight': 2.5,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'RIVM',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://www.rivm.nl/nieuws/rss.xml',
  'weight': 2.5,
  'hint': 'Gezondheid'},
 {'publisher': 'Scientias',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://feeds.feedburner.com/scientias-wetenschap',
  'weight': 2.0,
  'hint': 'Wetenschap'},
 {'publisher': 'Nature Today',
  'region': 'nl',
  'mode': 'rss',
  'url': 'https://www.naturetoday.com/intl/nl/nature-reports/rss',
  'weight': 2.1,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'CBS',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'cbs.nl',
  'weight': 2.6,
  'hint': 'Economie & geld'},
 {'publisher': 'Wageningen University & Research',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'wur.nl',
  'weight': 2.7,
  'hint': 'Wetenschap'},
 {'publisher': 'Universiteit Twente',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'utwente.nl',
  'weight': 2.6,
  'hint': 'Technologie & innovatie'},
 {'publisher': 'TU Delft',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'tudelft.nl',
  'weight': 2.6,
  'hint': 'Technologie & innovatie'},
 {'publisher': 'Universiteit Utrecht',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'uu.nl',
  'weight': 2.5,
  'hint': 'Wetenschap'},
 {'publisher': 'Radboud Universiteit',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'ru.nl',
  'weight': 2.5,
  'hint': 'Wetenschap'},
 {'publisher': 'TNO',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'tno.nl',
  'weight': 2.6,
  'hint': 'Technologie & innovatie'},
 {'publisher': 'NEMO Kennislink',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'nemokennislink.nl',
  'weight': 2.2,
  'hint': 'Wetenschap'},
 {'publisher': 'RVO',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'rvo.nl',
  'weight': 2.3,
  'hint': 'Economie & geld'},
 {'publisher': 'Rijksoverheid',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'rijksoverheid.nl',
  'weight': 2.4,
  'hint': 'Mens & samenleving'},
 {'publisher': 'Voedingscentrum',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'voedingscentrum.nl',
  'weight': 2.4,
  'hint': 'Voeding & leefstijl'},
 {'publisher': 'Milieu Centraal',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'milieucentraal.nl',
  'weight': 2.1,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'Staatsbosbeheer',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'staatsbosbeheer.nl',
  'weight': 2.2,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'Oranje Fonds',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'oranjefonds.nl',
  'weight': 2.2,
  'hint': 'Mens & samenleving'},
 {'publisher': 'Humanitas',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'humanitas.nl',
  'weight': 2.1,
  'hint': 'Mens & samenleving'},
 {'publisher': 'NU.nl',
  'region': 'nl',
  'mode': 'curated_html',
  'url': 'https://www.nu.nl/goed-nieuws',
  'weight': 2.3,
  'hint': None,
  'curation_bonus': 25,
  'curated_source': 'NU.nl Goed nieuws'},
 {'publisher': 'NU.nl', 'region': 'nl', 'mode': 'google_site', 'domain': 'nu.nl', 'weight': 2.3, 'hint': None},
 {'publisher': 'RTL Nieuws', 'region': 'nl', 'mode': 'google_site', 'domain': 'rtl.nl', 'weight': 2.3, 'hint': None},
 {'publisher': 'RTV Oost', 'region': 'nl', 'mode': 'google_site', 'domain': 'rtvoost.nl', 'weight': 2.2, 'hint': None},
 {'publisher': 'Omroep Brabant',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'omroepbrabant.nl',
  'weight': 2.2,
  'hint': None},
 {'publisher': 'Omroep Gelderland',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'gld.nl',
  'weight': 2.2,
  'hint': None},
 {'publisher': 'Rijnmond', 'region': 'nl', 'mode': 'google_site', 'domain': 'rijnmond.nl', 'weight': 2.2, 'hint': None},
 {'publisher': 'NH Nieuws',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'nhnieuws.nl',
  'weight': 2.2,
  'hint': None},
 {'publisher': 'RTV Noord',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'rtvnoord.nl',
  'weight': 2.2,
  'hint': None},
 {'publisher': 'Omrop Fryslân',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'omropfryslan.nl',
  'weight': 2.2,
  'hint': None},
 {'publisher': 'AT5', 'region': 'nl', 'mode': 'google_site', 'domain': 'at5.nl', 'weight': 2.1, 'hint': None},
 {'publisher': '1Limburg', 'region': 'nl', 'mode': 'google_site', 'domain': '1limburg.nl', 'weight': 2.1, 'hint': None},
 {'publisher': 'Hart van Nederland',
  'region': 'nl',
  'mode': 'google_site',
  'domain': 'hartvannederland.nl',
  'weight': 2.0,
  'hint': None},
 {'publisher': 'MIT News',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://news.mit.edu/rss/feed',
  'weight': 2.7,
  'hint': 'Wetenschap'},
 {'publisher': 'NASA',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://www.nasa.gov/news-release/feed/',
  'weight': 2.7,
  'hint': 'Wetenschap'},
 {'publisher': 'BBC',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
  'weight': 2.5,
  'hint': 'Wetenschap'},
 {'publisher': 'BBC',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://feeds.bbci.co.uk/news/business/rss.xml',
  'weight': 2.5,
  'hint': 'Economie & geld'},
 {'publisher': 'The Guardian',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://www.theguardian.com/environment/rss',
  'weight': 2.4,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'The Guardian',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://www.theguardian.com/science/rss',
  'weight': 2.4,
  'hint': 'Wetenschap'},
 {'publisher': 'UN News',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://news.un.org/feed/subscribe/en/news/all/rss.xml',
  'weight': 2.5,
  'hint': 'Mens & samenleving'},
 {'publisher': 'BBC',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://feeds.bbci.co.uk/news/health/rss.xml',
  'weight': 2.5,
  'hint': 'Gezondheid'},
 {'publisher': 'BBC',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://feeds.bbci.co.uk/news/technology/rss.xml',
  'weight': 2.5,
  'hint': 'Technologie & innovatie'},
 {'publisher': 'The Guardian',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://www.theguardian.com/global-development/rss',
  'weight': 2.4,
  'hint': 'Mens & samenleving'},
 {'publisher': 'Phys.org',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://phys.org/rss-feed/',
  'weight': 2.3,
  'hint': 'Wetenschap'},
 {'publisher': 'Medical Xpress',
  'region': 'int',
  'mode': 'rss',
  'url': 'https://medicalxpress.com/rss-feed/',
  'weight': 2.3,
  'hint': 'Gezondheid'},
 {'publisher': 'ESA', 'region': 'int', 'mode': 'google_site', 'domain': 'esa.int', 'weight': 2.6, 'hint': 'Wetenschap'},
 {'publisher': 'WHO', 'region': 'int', 'mode': 'google_site', 'domain': 'who.int', 'weight': 2.6, 'hint': 'Gezondheid'},
 {'publisher': 'UNICEF',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'unicef.org',
  'weight': 2.5,
  'hint': 'Mens & samenleving'},
 {'publisher': 'OECD',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'oecd.org',
  'weight': 2.5,
  'hint': 'Economie & geld'},
 {'publisher': 'UNEP',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'unep.org',
  'weight': 2.5,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'Smithsonian Magazine',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'smithsonianmag.com',
  'weight': 2.3,
  'hint': 'Geschiedenis & mens'},
 {'publisher': 'ScienceDaily',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'sciencedaily.com',
  'weight': 2.2,
  'hint': 'Wetenschap'},
 {'publisher': 'Positive News',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'positive.news',
  'weight': 2.0,
  'hint': 'Mens & samenleving'},
 {'publisher': 'Mongabay',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'mongabay.com',
  'weight': 2.4,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'Yale Environment 360',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'e360.yale.edu',
  'weight': 2.4,
  'hint': 'Natuur & klimaat'},
 {'publisher': 'Good News Network',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'goodnewsnetwork.org',
  'weight': 1.9,
  'hint': 'Gewoon leuk'},
 {'publisher': 'UNDP',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'undp.org',
  'weight': 2.5,
  'hint': 'Mens & samenleving'},
 {'publisher': 'FAO',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'fao.org',
  'weight': 2.5,
  'hint': 'Voeding & leefstijl'},
 {'publisher': 'European Space Agency',
  'region': 'int',
  'mode': 'google_site',
  'domain': 'esa.int',
  'weight': 2.6,
  'hint': 'Wetenschap'}]

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

def google_site_feed(domain, region):
    # Gericht zoeken naar mogelijke positieve ontwikkelingen.
    if region == "nl":
        cues = (
            'doorbraak OR succes OR wint OR goud OR gered OR herstel OR verbetert OR '
            'ontdekking OR innovatie OR helpt OR vrijwilligers OR daalt OR groeit OR oplossing'
        )
        q = f"site:{domain} ({cues}) when:7d"
        return "https://news.google.com/rss/search?q=" + urllib.parse.quote_plus(q) + "&hl=nl&gl=NL&ceid=NL:nl"

    cues = (
        'breakthrough OR success OR wins OR gold OR rescued OR recovery OR improves OR '
        'discovery OR innovation OR helps OR volunteers OR falls OR growth OR solution'
    )
    q = f"site:{domain} ({cues}) when:7d"
    return "https://news.google.com/rss/search?q=" + urllib.parse.quote_plus(q) + "&hl=en-US&gl=US&ceid=US:en"


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
    return google_site_feed(src["domain"], src["region"])

def fetch(url, html=False):
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
            items.append({"title": title, "url": url, "summary": summary, "published": published})
    return items

def contains(text, terms):
    t = clean(text).lower()
    return any(term in t for term in terms)

def cue_score(title, summary, region):
    cues = POSITIVE_CUES_NL if region == "nl" else POSITIVE_CUES_INT
    t = clean(title).lower()
    s = clean(summary).lower()
    # Titel weegt zwaarder, maar dit blijft slechts een voorselectiescore.
    return sum(3 for cue in cues if cue in t) + sum(1 for cue in cues if cue in s)

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
        return source_hint or "Onbekend"
    return max(scores, key=scores.get)

def compact_summary(text, max_chars=420):
    text = clean(text)
    if not text:
        return ""
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return text

def normurl(url):
    try:
        p = urlparse(url)
        return (p.netloc.lower() + p.path.rstrip("/")).lower()
    except Exception:
        return url.lower().rstrip("/")

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

def collect():
    now = datetime.now(timezone.utc)
    candidates = []
    errors = []
    seen_urls = set()

    for src in SOURCES:
        try:
            if src["mode"] == "curated_html":
                items = parse_nu_good_news(fetch(src["url"], html=True))
            else:
                items = parse_feed(fetch(source_url(src)))
        except Exception as exc:
            errors.append(f'{src["publisher"]}: {type(exc).__name__}: {exc}')
            continue

        for x in items:
            title = clean(x["title"])
            summary = clean(x["summary"])
            combined = f"{title} {summary}"

            if contains(title, HARD_BLOCK) or contains(title, JUNK_TERMS):
                continue

            pub = x["published"]
            age = None
            if pub is not None:
                age = max(0.0, (now - pub).total_seconds() / 3600)
                if age > MAX_AGE_HOURS:
                    continue

            url_key = normurl(x["url"])
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)

            signal = cue_score(title, summary, src["region"])
            # Directe RSS-feeds zijn breed. Zonder enig positief signaal worden ze te groot.
            # Voor Google-site-search en gecureerde Goed nieuws-pagina’s is 0 toegestaan.
            if src["mode"] == "rss" and signal <= 0:
                continue

            candidates.append({
                "id": item_id(src["publisher"], title, x["url"]),
                "region": src["region"],
                "source": src["publisher"],
                "title": title,
                "summary": compact_summary(summary),
                "url": x["url"],
                "published": pub.isoformat() if pub else None,
                "hours_old": round(age, 1) if age is not None else None,
                "category_hint": category_hint(title, summary, src.get("hint")),
                "signal_score": signal,
                "source_weight": src.get("weight", 1.0),
                "curation_bonus": src.get("curation_bonus", 0),
                "curated_source": src.get("curated_source"),
                "discovery": src["mode"],
            })

    return candidates, errors

def rank(item):
    freshness = 0
    if item["hours_old"] is not None:
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
    )

def shortlist(items, region):
    pool = [x for x in items if x["region"] == region]
    pool.sort(key=lambda x: (-rank(x), x["hours_old"] if x["hours_old"] is not None else 9999))

    selected = []
    per_source = {}

    for item in pool:
        if len(selected) >= MAX_PER_REGION:
            break
        if per_source.get(item["source"], 0) >= MAX_PER_SOURCE:
            continue
        if any(near_duplicate(item, other) for other in selected):
            continue
        selected.append(item)
        per_source[item["source"]] = per_source.get(item["source"], 0) + 1

    return selected

def main():
    all_candidates, errors = collect()
    nl = shortlist(all_candidates, "nl")
    intl = shortlist(all_candidates, "int")

    now = datetime.now().astimezone()

    data = {
        "meta": {
            "generated_at": now.isoformat(),
            "generator": "Goed nieuws kandidaten 0.1",
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
        },
        "editorial_brief": {
            "audience": "Nederlandse lezers",
            "target": "Kies later 6 Nederlandse/relevante verhalen en 6 internationale verhalen.",
            "principles": [
                "Echt positief nieuws, niet alleen een positief woord in een negatieve kop.",
                "Nederlandse selectie moet relevant zijn voor Nederlandse lezers.",
                "Universele vooruitgang in gezondheid, wetenschap, natuur, dieren en technologie mag ook.",
                "Geen dubbel nieuwsfeit.",
                "Bron- en categorievariatie.",
                "Gecureerde goed-nieuwsbronnen krijgen extra voorrang in de voorselectie, maar worden niet automatisch geselecteerd.",
                "Geen vacatures, losse weersverwachtingen, celebrity-fluff of puur triviale uitslagen.",
                "Eerste verhaal moet direct prettig en positief voelen.",
            ],
        },
        "nl_candidates": nl,
        "international_candidates": intl,
    }

    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Ruwe kandidaten: {len(all_candidates)}")
    print(f"NL shortlist: {len(nl)} | bronnen: {len({x['source'] for x in nl})}")
    print(f"INT shortlist: {len(intl)} | bronnen: {len({x['source'] for x in intl})}")
    print(f"Feedfouten: {len(errors)}")
    print("GESCHREVEN: kandidaten.json")
    print("nieuws.json is bewust NIET aangepast.")

if __name__ == "__main__":
    main()
