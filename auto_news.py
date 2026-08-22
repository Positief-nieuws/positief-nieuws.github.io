#!/usr/bin/env python3
from __future__ import annotations
import json,re,sys,urllib.request,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'nieuws.json'
TARGET=7; MAX_AGE=72; PREF_AGE=48; MAX_PER_SOURCE=2; MIN_PUBLISH=5
UA='GoedNieuwsBot/0.3'

SOURCES=[
('NOS Nieuws','NOS','nl','https://feeds.nos.nl/nosnieuwsalgemeen'),
('NOS Economie','NOS','nl','https://feeds.nos.nl/nosnieuwseconomie'),
('NOS Cultuur','NOS','nl','https://feeds.nos.nl/nosnieuwscultuurenmedia'),
('NOS Tech','NOS','nl','https://feeds.nos.nl/nosnieuwstech'),
('NOS Opmerkelijk','NOS','nl','https://feeds.nos.nl/nosnieuwsopmerkelijk'),
('NOS Sport','NOS','nl','https://feeds.nos.nl/nossportalgemeen'),
('RIVM','RIVM','nl','https://www.rivm.nl/nieuws/rss.xml'),
('Scientias','Scientias','nl','https://feeds.feedburner.com/scientias-wetenschap'),
('Nature Today','Nature Today','nl','https://www.naturetoday.com/intl/nl/nature-reports/rss'),
('MIT News','MIT News','int','https://news.mit.edu/rss/feed'),
('BBC Science','BBC','int','https://feeds.bbci.co.uk/news/science_and_environment/rss.xml'),
('BBC Business','BBC','int','https://feeds.bbci.co.uk/news/business/rss.xml'),
('Guardian Environment','The Guardian','int','https://www.theguardian.com/environment/rss'),
('Guardian Science','The Guardian','int','https://www.theguardian.com/science/rss'),
('NASA','NASA','int','https://www.nasa.gov/news-release/feed/'),
('UN News','UN News','int','https://news.un.org/feed/subscribe/en/news/all/rss.xml'),
]

POS={'wint':4,'winnen':4,'winst':3,'goud':4,'kampioen':4,'record':3,'groei':3,'groeit':3,'herstel':4,'herstelt':4,'terugkeer':4,'doorbraak':4,'succes':3,'oplossing':3,'innovatie':3,'ontdekt':3,'ontdekking':3,'verbetert':3,'verbetering':3,'helpt':3,'gered':4,'beschermt':3,'samenwerking':2,'schoner':3,'duurzaam':2,'medaille':3,'hoop':2,'beter':2,'daalt':2,'daling':2,'wins':4,'win':4,'gold':4,'champion':4,'growth':3,'grows':3,'recovery':4,'recovers':4,'return':3,'breakthrough':4,'success':3,'solution':3,'innovation':3,'discovery':3,'improves':3,'helps':3,'rescued':4,'protects':3,'cleaner':3,'sustainable':2,'hope':2,'better':2}
NEG={'oorlog':-7,'dood':-7,'doden':-7,'omgekomen':-7,'gewond':-5,'moord':-7,'crisis':-5,'failliet':-5,'aanval':-6,'ramp':-7,'explosie':-7,'geweld':-7,'brand':-4,'vermist':-5,'fraude':-5,'staking':-3,'dreigt':-4,'war':-7,'dead':-7,'death':-7,'killed':-7,'wounded':-5,'murder':-7,'crisis':-5,'bankrupt':-5,'attack':-6,'disaster':-7,'explosion':-7,'violence':-7,'wildfire':-4,'missing':-5,'fraud':-5,'strike':-3,'threat':-4}
CATS=[
('Mens & samenleving',['community','gemeenschap','buurt','vrijwillig','volunteer','society','samenleving','poverty','armoede','refugee','vluchteling']),
('Economie & geld',['economie','economy','geld','money','beurs','market','markt','export','import','business','bedrijf','jobs','banen','inflatie','inflation']),
('Natuur & klimaat',['natuur','nature','klimaat','climate','forest','bos','river','rivier','ocean','oceaan','biodivers','emission','emissie','energy','energie','sustainable','duurzaam']),
('Dieren',['dier','animal','bird','vogel','fish','vis','tiger','tijger','whale','walvis','turtle','schildpad','bee','bij']),
('Wetenschap',['wetenschap','science','onderzoek','research','scientist','onderzoeker','study','studie','space','ruimte','physics','biolog']),
('Gezondheid',['gezondheid','health','medical','medisch','medicine','medicijn','patient','patiënt','care','zorg','therapy','therapie','cancer','kanker','vaccine','vaccin']),
('Technologie & innovatie',['technology','tech','innovatie','innovation','ai','robot','chip','software','computer','engineering','battery','batterij']),
('Sport',['sport','football','voetbal','soccer','hockey','tennis','atlet','cycling','wielren','zwem','olympic','medaille','kampioen','goal']),
('Cultuur & media',['cultuur','culture','kunst','art','museum','muziek','music','film','boek','book','media','theater','heritage','erfgoed']),
('Onderwijs & ontwikkeling',['onderwijs','education','school','student','leerling','learning','opleiding','university','universiteit']),
('Voeding & leefstijl',['voeding','food','groente','vegetable','fruit','diet','leefstijl','lifestyle','sleep','slaap','exercise','bewegen']),
('Geschiedenis & mens',['geschiedenis','history','archeolog','archaeolog','ancient','oudheid','fossil','voorouder','ancestor'])]
ICONS={'Mens & samenleving':'🤝','Economie & geld':'📈','Natuur & klimaat':'🌱','Dieren':'🐾','Wetenschap':'🔬','Gezondheid':'❤️','Technologie & innovatie':'💡','Sport':'🏅','Cultuur & media':'🎨','Onderwijs & ontwikkeling':'🎓','Voeding & leefstijl':'🥬','Geschiedenis & mens':'🏛️','Gewoon leuk':'☀️'}

def clean(v):
    if not v:return ''
    return re.sub(r'\s+',' ',unescape(re.sub(r'<[^>]+>',' ',v))).strip()
def lname(t):return t.rsplit('}',1)[-1].lower()
def ctext(n,names):
    for c in list(n):
        if lname(c.tag) in names and c.text and c.text.strip():return clean(c.text)
    return ''
def link(n):
    for c in list(n):
        if lname(c.tag)=='link':
            if c.attrib.get('href') and c.attrib.get('rel','alternate') in ('alternate',''):return c.attrib['href'].strip()
            if c.text and c.text.strip():return c.text.strip()
    return ''
def pdate(v):
    if not v:return None
    try:
        d=parsedate_to_datetime(v); return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except:pass
    try:
        d=datetime.fromisoformat(v.strip().replace('Z','+00:00')); return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except:return None
def fetch(u):
    r=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'application/rss+xml,application/atom+xml,application/xml,text/xml,*/*'})
    with urllib.request.urlopen(r,timeout=20) as x:return x.read()
def parse(raw):
    root=ET.fromstring(raw); out=[]
    for n in root.iter():
        if lname(n.tag) not in ('item','entry'):continue
        t=ctext(n,{'title'}); u=link(n); s=ctext(n,{'description','summary','content','encoded'}); d=pdate(ctext(n,{'pubdate','published','updated','date'}))
        if t and u:out.append((t,u,s,d))
    return out
def cat(t,s):
    x=(t+' '+s).lower(); best=('Gewoon leuk',0)
    for c,ws in CATS:
        h=sum(1 for w in ws if w in x)
        if h>best[1]:best=(c,h)
    return best[0]
def score(t,s,h):
    x=(t+' '+s).lower(); sc=sum(v for w,v in POS.items() if w in x)+sum(v for w,v in NEG.items() if w in x)
    if h is not None: sc+=4 if h<=24 else 2 if h<=48 else 0
    return sc
def summary(s):
    s=clean(s)
    if not s:return 'Lees het volledige bericht bij de bron.'
    z=' '.join(re.split(r'(?<=[.!?])\s+',s)[:2]).strip()
    if len(z)>320:z=z[:320].rsplit(' ',1)[0].rstrip(' ,;:')+'…'
    return z
def norm(u):
    try:
        p=urlparse(u);return (p.netloc.lower()+p.path.rstrip('/')).lower()
    except:return u.lower().rstrip('/')

def collect():
    now=datetime.now(timezone.utc); items=[]; seen=set(); errs=[]
    for feedname,publisher,region,url in SOURCES:
        try: rows=parse(fetch(url))
        except Exception as e: errs.append(f'{feedname}: {type(e).__name__}: {e}'); continue
        for t,u,s,d in rows:
            h=max(0,(now-d).total_seconds()/3600) if d else None
            if h is not None and h>MAX_AGE:continue
            k=norm(u)
            if k in seen:continue
            seen.add(k); c=cat(t,s)
            items.append({'region':region,'source':publisher,'title':clean(t),'url':u,'summary':summary(s),'hours':round(h,1) if h is not None else None,'category':c,'icon':ICONS.get(c,'☀️'),'score':score(t,s,h)})
    return items,errs

def choose(items,region):
    pool=[x for x in items if x['region']==region]
    pool.sort(key=lambda x:(-x['score'],x['hours'] if x['hours'] is not None else 9999))
    sel=[]; counts={}; cats=set()
    def add(x):
        sel.append(x);counts[x['source']]=counts.get(x['source'],0)+1;cats.add(x['category'])
    for x in pool:
        if len(sel)>=TARGET:break
        if x['category'] in cats or counts.get(x['source'],0)>=MAX_PER_SOURCE or x['score']<1:continue
        if x['hours'] is not None and x['hours']>PREF_AGE:continue
        add(x)
    for x in pool:
        if len(sel)>=TARGET:break
        if x in sel or x['category'] in cats or counts.get(x['source'],0)>=MAX_PER_SOURCE or x['score']<0:continue
        add(x)
    for x in pool:
        if len(sel)>=TARGET:break
        if x in sel or counts.get(x['source'],0)>=MAX_PER_SOURCE or x['score']<0:continue
        add(x)
    return sel[:TARGET]

def dispdate():
    n=datetime.now().astimezone(); days=['maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag','zondag']; months=['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december']
    return f'{days[n.weekday()]} {n.day} {months[n.month-1]}'
def story(x,eng=False):
    return {'category':x['category'],'icon':x['icon'],'title':x['title'],'summary':x['summary'],'source':x['source']+(' · English' if eng else ''),'url':x['url']}
def main():
    items,errs=collect(); nl=choose(items,'nl'); inte=choose(items,'int')
    print('Kandidaten:',len(items),'NL:',len(nl),'INT:',len(inte),'feedfouten:',len(errs))
    if len(nl)<MIN_PUBLISH or len(inte)<MIN_PUBLISH:
        print('Te weinig bruikbare artikelen. Bestaande nieuws.json blijft staan.');return
    n=datetime.now().astimezone(); data={'edition':{'date':n.strftime('%Y-%m-%d'),'displayDate':dispdate(),'title':'Goed nieuws','tagline':'Dit gebeurt ook.','intro':f'{len(nl)+len(inte)} korte verhalen. Geen doomscrollen, geen eindeloze feed.','closingTitle':'Dat was het.','closingText':'Ga lekker verder met je dag. ☀️'},'dutch':[story(x) for x in nl],'international':[story(x,True) for x in inte],'_meta':{'generated_at':n.isoformat(),'generator':'Goed nieuws 0.3 auto','feed_errors':errs}}
    OUTPUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print('Nieuwe editie geschreven.')
if __name__=='__main__':main()
