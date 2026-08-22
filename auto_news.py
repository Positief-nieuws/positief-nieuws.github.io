#!/usr/bin/env python3
"""
Goed nieuws 0.5 auto

Doel:
- gratis automatische dagelijkse editie
- alleen publiceren bij exact 7 NL + 7 internationaal
- minimaal 5 verschillende bronnen per blok
- zoveel mogelijk 7 verschillende categorieën
- voorkeur <=48 uur, fallback tot maximaal 7 dagen
- strengere positieve selectie dan 0.4

Geen AI en geen betaalde API.
"""

from __future__ import annotations
import json, re, sys, urllib.request, xml.etree.ElementTree as ET
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
MAX_AGE_HOURS = 168   # 7 dagen als fallback
USER_AGENT = "GoedNieuwsBot/0.5"

SOURCES = [
    # Nederland
    {"name":"NOS Nieuws","publisher":"NOS","region":"nl","feed":"https://feeds.nos.nl/nosnieuwsalgemeen"},
    {"name":"NOS Economie","publisher":"NOS","region":"nl","feed":"https://feeds.nos.nl/nosnieuwseconomie"},
    {"name":"NOS Cultuur","publisher":"NOS","region":"nl","feed":"https://feeds.nos.nl/nosnieuwscultuurenmedia"},
    {"name":"NOS Tech","publisher":"NOS","region":"nl","feed":"https://feeds.nos.nl/nosnieuwstech"},
    {"name":"NOS Opmerkelijk","publisher":"NOS","region":"nl","feed":"https://feeds.nos.nl/nosnieuwsopmerkelijk"},
    {"name":"NOS Sport","publisher":"NOS","region":"nl","feed":"https://feeds.nos.nl/nossportalgemeen"},
    {"name":"CBS Nieuws","publisher":"CBS","region":"nl","feed":"https://www.cbs.nl/nl-nl/rss-feeds/alle-nieuwsberichten"},
    {"name":"RIVM","publisher":"RIVM","region":"nl","feed":"https://www.rivm.nl/nieuws/rss.xml"},
    {"name":"Scientias","publisher":"Scientias","region":"nl","feed":"https://feeds.feedburner.com/scientias-wetenschap"},
    {"name":"Nature Today","publisher":"Nature Today","region":"nl","feed":"https://www.naturetoday.com/intl/nl/nature-reports/rss"},
    {"name":"KNMI Nieuws","publisher":"KNMI","region":"nl","feed":"https://www.knmi.nl/rssfeeds/rss_KNMInieuwsberichten"},
    {"name":"KNMI Klimaat","publisher":"KNMI","region":"nl","feed":"https://www.knmi.nl/rssfeeds/rss_KNMIklimaatberichten"},

    # Internationaal
    {"name":"MIT News","publisher":"MIT News","region":"int","feed":"https://news.mit.edu/rss/feed"},
    {"name":"BBC Science","publisher":"BBC","region":"int","feed":"https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"},
    {"name":"BBC Business","publisher":"BBC","region":"int","feed":"https://feeds.bbci.co.uk/news/business/rss.xml"},
    {"name":"The Guardian Environment","publisher":"The Guardian","region":"int","feed":"https://www.theguardian.com/environment/rss"},
    {"name":"The Guardian Science","publisher":"The Guardian","region":"int","feed":"https://www.theguardian.com/science/rss"},
    {"name":"NASA","publisher":"NASA","region":"int","feed":"https://www.nasa.gov/news-release/feed/"},
    {"name":"UN News","publisher":"UN News","region":"int","feed":"https://news.un.org/feed/subscribe/en/news/all/rss.xml"},
]

# Positieve signalen. Titel telt zwaarder dan samenvatting.
POSITIVE = {
    "wint":5,"winnen":5,"winst":4,"goud":5,"kampioen":5,"record":3,
    "groeit":4,"groei":4,"stijgt":2,"toename":3,"herstelt":5,"herstel":5,
    "terugkeer":5,"doorbraak":5,"succes":4,"oplossing":4,"innovatie":4,
    "ontdekt":3,"ontdekking":4,"verbetert":4,"verbetering":4,"helpt":4,
    "gered":5,"redding":4,"beschermt":4,"samenwerking":3,"schoner":4,
    "duurzaam":3,"medaille":4,"hoop":3,"beter":3,"daalt":2,"daling":2,
    "minder faillissementen":5,"meer banen":5,"meer werk":4,"overleven":4,
    "wins":5,"win":5,"gold":5,"champion":5,"growth":4,"grows":4,
    "recovery":5,"recovers":5,"return":4,"breakthrough":5,"success":4,
    "solution":4,"innovation":4,"discovery":4,"improves":4,"helps":4,
    "rescued":5,"protects":4,"cleaner":4,"sustainable":3,"hope":3,
    "better":3,"survival":4,"decline in":2,
}

# Algemene negatieve signalen.
NEGATIVE = {
    "oorlog":-9,"doden":-9,"dood":-9,"omgekomen":-9,"gewond":-7,"moord":-9,
    "crisis":-7,"failliet":-6,"aanval":-8,"ramp":-9,"explosie":-9,"geweld":-9,
    "vermist":-7,"fraude":-7,"dreigt":-6,"zorgelijk":-5,"mislukt":-6,
    "gaat niet door":-10,"einde van":-6,"kan niet worden gered":-10,
    "war":-9,"dead":-9,"death":-9,"killed":-9,"wounded":-7,"murder":-9,
    "crisis":-7,"bankrupt":-6,"attack":-8,"disaster":-9,"explosion":-9,
    "violence":-9,"missing":-7,"fraud":-7,"threat":-6,"toxic":-8,
    "clogs":-7,"axe":-7,"emergency declaration":-6,"disease":-4,
    "hottest year":-5,"stormy":-4,
}

# Als één van deze frases in de TITEL staat, artikel niet selecteren.
HARD_NEGATIVE_TITLE = [
    "gaat niet door","kan niet worden gered","doden","omgekomen","moord",
    "explosie","oorlog","zwaar gewond","crisis","ramp",
    "toxic","clogs","killed","dead","war","murder","disaster",
    "axe climate emergency","hottest year","stormy autumn",
]

CATEGORY_TERMS = {
    "Sport":[
        "sport","voetbal","football","soccer","hockey","tennis","atletiek","athletics",
        "wielrennen","cycling","mountainbike","mtb","zwemmen","swimming","olympic",
        "medaille","medal","kampioen","champion","wedstrijd","match","goal","race",
        "marathon","sprint","finale","grand prix","formula 1","f1"
    ],
    "Economie & geld":[
        "economie","economy","geld","money","beurs","market","markt","export","import",
        "business","bedrijf","bedrijven","jobs","banen","inflatie","inflation","inkomen",
        "income","investment","investering","faillissementen","productie","consumptie"
    ],
    "Natuur & klimaat":[
        "natuur","nature","klimaat","climate","forest","bos","river","rivier","ocean",
        "oceaan","biodiversiteit","biodiversity","emission","emissie","energy","energie",
        "sustainable","duurzaam","ecosystem","ecosysteem","weer","weather"
    ],
    "Dieren":[
        "dier","dieren","animal","animals","bird","birds","vogel","vogels","fish","vis",
        "tiger","tijger","whale","walvis","turtle","schildpad","bee","bees","bij","bijen",
        "lion","leeuw","wolf","wolves","hond","dog","cat","kat","insect","mier","ant"
    ],
    "Wetenschap":[
        "wetenschap","science","onderzoek","research","scientist","onderzoeker","study",
        "studie","space","ruimte","physics","fysica","biology","biologie","astronomy",
        "astronomie","telescope","telescoop"
    ],
    "Gezondheid":[
        "gezondheid","health","medical","medisch","medicine","medicijn","patient","patiënt",
        "care","zorg","therapy","therapie","cancer","kanker","vaccine","vaccin","screening",
        "diagnosis","diagnose","overleven","survival"
    ],
    "Technologie & innovatie":[
        "technology","technologie","tech","innovatie","innovation","robot","robots","chip",
        "chips","software","computer","engineering","battery","batterij",
        "artificial intelligence","kunstmatige intelligentie","ai"
    ],
    "Cultuur & media":[
        "cultuur","culture","kunst","art","museum","muziek","music","film","boek","book",
        "media","theater","heritage","erfgoed","painting","schilderij"
    ],
    "Onderwijs & ontwikkeling":[
        "onderwijs","education","school","student","students","leerling","leerlingen",
        "learning","opleiding","university","universiteit","teacher","leraar"
    ],
    "Voeding & leefstijl":[
        "voeding","food","groente","vegetable","fruit","diet","leefstijl","lifestyle",
        "sleep","slaap","exercise","bewegen","nutrition"
    ],
    "Geschiedenis & mens":[
        "geschiedenis","history","archeologie","archaeology","archeoloog","archaeologist",
        "ancient","oudheid","fossil","voorouder","ancestor","prehistoric"
    ],
    "Mens & samenleving":[
        "community","gemeenschap","buurt","vrijwillig","volunteer","samenleving","society",
        "poverty","armoede","refugee","vluchteling","solidarity","solidariteit",
        "studentenvereniging","vereniging","campagne","mensenrechten","human rights",
        "buurtbewoners","vrijwilligers"
    ],
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
    if not value: return ""
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()

def lname(tag): return tag.rsplit("}",1)[-1].lower()

def child_text(node,names):
    for c in list(node):
        if lname(c.tag) in names and c.text and c.text.strip():
            return clean(c.text)
    return ""

def link_of(node):
    for c in list(node):
        if lname(c.tag)=="link":
            href=c.attrib.get("href")
            if href and c.attrib.get("rel","alternate") in ("alternate",""):
                return href.strip()
            if c.text and c.text.strip(): return c.text.strip()
    return ""

def parse_date(value):
    if not value: return None
    try:
        dt=parsedate_to_datetime(value)
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception: pass
    try:
        dt=datetime.fromisoformat(value.strip().replace("Z","+00:00"))
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception: return None

def fetch(url):
    req=urllib.request.Request(url,headers={
        "User-Agent":USER_AGENT,
        "Accept":"application/rss+xml,application/atom+xml,application/xml,text/xml,*/*"
    })
    with urllib.request.urlopen(req,timeout=20) as r: return r.read()

def parse_feed(raw):
    root=ET.fromstring(raw); items=[]
    for node in root.iter():
        if lname(node.tag) not in ("item","entry"): continue
        title=child_text(node,{"title"}); url=link_of(node)
        summary=child_text(node,{"description","summary","content","encoded"})
        published=parse_date(child_text(node,{"pubdate","published","updated","date"}))
        if title and url:
            items.append({"title":title,"url":url,"summary":summary,"published":published})
    return items

def wordmatch(text,phrase):
    return bool(re.search(r"(?<!\w)"+re.escape(phrase.lower())+r"(?!\w)",text.lower()))

def lexscore(text,lex):
    return sum(points for phrase,points in lex.items() if wordmatch(text,phrase))

def positivity(title,summary):
    # Titel dubbel laten wegen. Versheid telt hier bewust NIET mee.
    return 2*lexscore(title,POSITIVE)+lexscore(summary,POSITIVE)+2*lexscore(title,NEGATIVE)+lexscore(summary,NEGATIVE)

def hard_negative(title):
    t=title.lower()
    return any(p in t for p in HARD_NEGATIVE_TITLE)

def category(title,summary,feed):
    text=f"{title} {summary}".lower()
    f=feed.lower()

    if "sport" in f: return "Sport"
    if "economie" in f or "business" in f: return "Economie & geld"
    if "cultuur" in f: return "Cultuur & media"
    if "tech" in f: return "Technologie & innovatie"
    if "knmi" in f: return "Natuur & klimaat"
    if "rivm" in f: return "Gezondheid"

    # Expliciete maatschappelijke override.
    if any(wordmatch(text,x) for x in ["studentenvereniging","vrijwilligers","buurtbewoners","human rights","mensenrechten"]):
        return "Mens & samenleving"

    scores={}
    for cat,terms in CATEGORY_TERMS.items():
        hits=sum(1 for term in terms if wordmatch(text,term))
        if hits: scores[cat]=hits

    if not scores:
        if "nature today" in f: return "Natuur & klimaat"
        if "scientias" in f or "mit news" in f or "nasa" in f: return "Wetenschap"
        return "Gewoon leuk"

    return max(scores,key=lambda c:(scores[c],CATEGORY_PRIORITY.get(c,0)))

def compact_summary(text,max_chars=220):
    text=clean(text)
    if not text: return ""
    first=re.split(r"(?<=[.!?])\s+",text)[0].strip()
    if len(first)>max_chars:
        first=first[:max_chars].rsplit(" ",1)[0].rstrip(" ,;:")+"…"
    return first

def normurl(url):
    try:
        p=urlparse(url); return (p.netloc.lower()+p.path.rstrip("/")).lower()
    except Exception: return url.lower().rstrip("/")

def collect():
    now=datetime.now(timezone.utc); out=[]; seen=set(); errors=[]
    for src in SOURCES:
        try: feed=parse_feed(fetch(src["feed"]))
        except Exception as e:
            errors.append(f'{src["name"]}: {type(e).__name__}: {e}'); continue
        for x in feed:
            pub=x["published"]; age=None
            if pub:
                age=max(0,(now-pub).total_seconds()/3600)
                if age>MAX_AGE_HOURS: continue
            key=normurl(x["url"])
            if key in seen: continue
            seen.add(key)

            if hard_negative(x["title"]): continue
            pscore=positivity(x["title"],x["summary"])
            if pscore <= 0: continue

            out.append({
                "region":src["region"],"source":src["publisher"],"feed":src["name"],
                "title":clean(x["title"]),"url":x["url"],
                "summary":compact_summary(x["summary"]),
                "hours_old":round(age,1) if age is not None else None,
                "category":category(x["title"],x["summary"],src["name"]),
                "positive_score":pscore,
            })
    return out,errors

def choose(items,region):
    pool=[x for x in items if x["region"]==region]

    # Kwaliteit eerst, dan versheid.
    pool.sort(key=lambda x:(-x["positive_score"], x["hours_old"] if x["hours_old"] is not None else 9999))

    selected=[]; counts={}; cats=set()

    # Ronde 1: <=48 uur, unieke categorie.
    for x in pool:
        if len(selected)>=TARGET: break
        if x["category"] in cats: continue
        if counts.get(x["source"],0)>=MAX_PER_SOURCE: continue
        if x["hours_old"] is not None and x["hours_old"]>PREFERRED_AGE_HOURS: continue
        selected.append(x); cats.add(x["category"]); counts[x["source"]]=counts.get(x["source"],0)+1

    # Ronde 2: tot 7 dagen, unieke categorie.
    for x in pool:
        if len(selected)>=TARGET: break
        if x in selected or x["category"] in cats: continue
        if counts.get(x["source"],0)>=MAX_PER_SOURCE: continue
        selected.append(x); cats.add(x["category"]); counts[x["source"]]=counts.get(x["source"],0)+1

    # Ronde 3: indien nodig categorie dubbel, bron nog altijd max 2.
    for x in pool:
        if len(selected)>=TARGET: break
        if x in selected: continue
        if counts.get(x["source"],0)>=MAX_PER_SOURCE: continue
        selected.append(x); counts[x["source"]]=counts.get(x["source"],0)+1

    # Brondiversiteit verbeteren.
    def sourceset(): return {x["source"] for x in selected}
    if len(sourceset())<MIN_SOURCES:
        for cand in pool:
            if len(sourceset())>=MIN_SOURCES: break
            if cand in selected or cand["source"] in sourceset(): continue
            for i in range(len(selected)-1,-1,-1):
                oldsrc=selected[i]["source"]
                if sum(1 for y in selected if y["source"]==oldsrc)>1:
                    selected[i]=cand
                    break

    return selected[:TARGET]

def story(x,english=False):
    return {
        "category":x["category"],
        "icon":ICONS.get(x["category"],"☀️"),
        "title":x["title"],
        "summary":x["summary"] or "Lees het volledige bericht bij de bron.",
        "source":x["source"]+(" · English" if english else ""),
        "url":x["url"]
    }

def display_date():
    days=["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
    months=["januari","februari","maart","april","mei","juni","juli","augustus","september","oktober","november","december"]
    n=datetime.now().astimezone()
    return f"{days[n.weekday()]} {n.day} {months[n.month-1]}"

def main():
    items,errors=collect()
    nl=choose(items,"nl"); intl=choose(items,"int")

    print(f"Positieve kandidaten: {len(items)}")
    print(f"NL: {len(nl)} | bronnen: {len(set(x['source'] for x in nl))} | categorieën: {len(set(x['category'] for x in nl))}")
    print(f"INT: {len(intl)} | bronnen: {len(set(x['source'] for x in intl))} | categorieën: {len(set(x['category'] for x in intl))}")

    print("\nNL-selectie:")
    for x in nl: print(f"- [{x['category']}] {x['source']}: {x['title']}")
    print("\nInternationale selectie:")
    for x in intl: print(f"- [{x['category']}] {x['source']}: {x['title']}")

    if errors:
        print("\nFeedfouten:")
        for e in errors: print(" -",e)

    if len(nl)!=TARGET or len(intl)!=TARGET:
        print(f"\nNIET PUBLICEREN: exact 7 + 7 vereist. Gevonden {len(nl)} NL + {len(intl)} INT.")
        sys.exit(0)

    if len(set(x["source"] for x in nl))<MIN_SOURCES or len(set(x["source"] for x in intl))<MIN_SOURCES:
        print("\nNIET PUBLICEREN: minimaal 5 verschillende bronnen per blok vereist.")
        sys.exit(0)

    now=datetime.now().astimezone()
    data={
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
            "generator":"Goed nieuws 0.5 auto",
            "feed_errors":errors
        }
    }
    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print("\nPUBLICEREN: nieuwe 7+7-editie geschreven.")

if __name__=="__main__":
    main()
