"""Deterministic, conservative content matching; no category-only fallback."""
import re
import math
import unicodedata
from collections import Counter
from pathlib import Path

STOP = set('de het een en van voor met op in om te die dat dit deze door bij naar aan als ook meer minder nieuwe nieuw heeft hebben wordt worden zijn is tot uit over na dan nog maar er hun ze zo kan kunnen moet eerste onderzoek onderzoekers nederland nederlandse wereldwijd wereld mensen jaar jaren helpt maken maakt goed nieuws positief ontwikkeling ontwikkelingen'.split())
# Shared subject vocabulary connects Dutch inflections and common synonyms.
STOP.update('laat zien brengt nieuwe nieuw geeft krijgen krijgt miljoen euro twee drie vier vijf zes zeven acht negen tien beter sneller samen ruimte mogelijk goed grote flink minder opnieuw beschikbaar vrij vrije dagen'.split())
CONCEPTS = {
 'wetland': 'moeras moerassen graslanden vogelterritoria grutto kievit rivieroever poelen overstromingsvlakte',
 'drinkwater': 'drinkwater kraan watercontainers watersysteem wateraanvoer drinkwatervoorziening',
 'transplantatie': 'nierdonor donorharten transplantatie transplantaties orgaandonatie donor',
 'vrijwilliger': 'vrijwilligers vrijwilligerswerk vrijwilliger dorpsbus',
 'onderwijs': 'basisschoolleraren basisonderwijs leerlingen scholen school schooldag schooltelefoons',
 'natuurbehoud': 'reservaat reservaten natuurgebieden natuurgebied natuurbehoud beschermd beschermde leefgebied natuurverbinding',
 'energie': 'stroomnet stroomgebruik netbeheerders elektriciteitsnet netcongestie transformatoren generatoren',
}

def flatten(value):
    if isinstance(value, dict): return ' '.join(flatten(v) for v in value.values())
    if isinstance(value, list): return ' '.join(map(flatten, value))
    return str(value or '')

def tokens(text):
    words = re.findall(r'[a-z]{4,}', unicodedata.normalize('NFKD', text.lower()).encode('ascii','ignore').decode())
    result = {w.rstrip('en') if len(w)>6 else w for w in words if w not in STOP}
    for concept, terms in CONCEPTS.items():
        if set(words) & set(terms.split()): result.add('@'+concept)
    return result

def features(item):
    title = flatten(item.get('title') or item.get('headline'))
    summary = ' '.join(flatten(item.get(k)) for k in ('teaser','summary','description','tags','topics','subjects','onderwerpen'))
    return tokens(title), tokens(title+' '+summary)

def special_records():
    from build_search import info_record
    records = []
    for path in sorted(Path('specials').glob('*/index.html')):
        markup = path.read_text()
        if re.search(r'noindex|http-equiv=["\']refresh', markup, re.I): continue
        url = '/'+path.parent.as_posix()+'/'
        item = info_record(url, 'Special', 'Specials', 'special')
        if item: records.append({'item':item,'path':url,'type':'special','category':''})
    return records

def select(item, origin, candidates, limit=3):
    title, all_terms = features(item)
    documents = [features(r['item'])[1] for r in candidates]
    counts = Counter(t for terms in documents for t in terms)
    ranked = []
    seen = {origin}
    for record, terms in zip(candidates, documents):
        path = record.get('path') or f"/artikelen/{record['date']}/{record['slug']}/"
        if path in seen: continue
        target_title, _ = features(record['item'])
        shared = all_terms & terms
        specific = {t for t in shared if counts[t] <= max(3, len(candidates)*.18)}
        # Two subject terms and a title anchor prevent generic category matches.
        anchors = title & target_title
        concepts = {t for t in shared if t.startswith('@') and t in title and t in target_title}
        if not (concepts or len(anchors & specific) >= 2): continue
        if len(specific)<2: continue
        score = sum(math.log(1+len(candidates)/(1+counts[t])) * (2 if t in title or t in target_title else 1) for t in specific)
        if score < 6: continue
        ranked.append((score, path, dict(record, path=path, type=record.get('type','article'))))
    ranked.sort(key=lambda r: (-r[0],r[1]))
    specials = [r for r in ranked if r[2]['type']=='special']
    ordered = specials[:1]+[r for r in ranked if r[2]['type']=='article']
    result=[]
    for _, path, record in ordered:
        if path not in seen:
            result.append(record);seen.add(path)
        if len(result)>=limit: break
    return result
