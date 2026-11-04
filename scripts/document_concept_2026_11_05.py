"""Record completed checks and unfinished work honestly; never grants approval."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from editorial_check import news_digest, article_key
from selection_check import pool_digest
from source_registry import canonical_url
DATE='2026-11-05'
CHECKED='2026-11-04'

def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def main():
    news=json.loads((ROOT/'nieuws.json').read_text())
    dossier=json.loads((ROOT/'redactie'/f'{DATE}.json').read_text())
    registry=json.loads((ROOT/'sources.json').read_text())
    if not any(s['source_id']=='tu-berlin' for s in registry['sources']):
        registry['sources'].append(dict(source_id='tu-berlin',organization_id='tu-berlin',name='Technische Universität Berlin',
            website='https://www.tu.berlin/',category='A',topics=['Wetenschap'],geography='int',source_type='university',
            reliability_notes='Oorspronkelijke institutionele onderzoeksmededeling; methode en belangen apart beoordelen.',
            priority='P2',check_frequency='manual',limitations='Persbericht is geen onafhankelijke effectevaluatie.',register_ids=[],channels=[]))
        save(ROOT/'sources.json',registry)
    registered={s['source_id']:s for s in registry['sources']}
    cache=json.loads((ROOT/'data/pixabay-images.json').read_text())
    history=[]
    for p in (ROOT/'edities').glob('????-??-??.json'):
        d=json.loads(p.read_text())
        for section in ['nl','int']:
            for item in d.get(section,[]):history.append((p.stem,canonical_url(item.get('url')),item.get('title')))
    notes={
      'gli-afvallen-kwaliteit-van-leven':('2,5 kilo verschil; kwaliteit van leven verbeterd.','Vergelijkingsgroepen; geen garantie per persoon of bewijs van behoud na afloop.','2025-12-31'),
      'carisia-kees-streekwinkel':('Nieuwe winkel en bestaand klantenbestand beschreven in reportage.','Persoonlijk ondernemersportret; tolkenproblematiek blijft bestaan.','2026-11-04'),
      'palingen-veilig-langs-maurik':('NOS/Omroep Gelderland bevestigen ruim 9.000 kilo overgezet.','Meer overzet door waterstand; geen populatieherstel aangetoond.','2026-11-03'),
      'zonvarken-lagere-emissies':('WUR-praktijkmetingen op drie bedrijven; berekende vergelijking.','Beperkte steekproef en methodevalidatie; geen algemene reductiegarantie.','2026-10-20'),
      'dienstenexport-banen-nederland':('CBS-tabel vergelijkt arbeidsvolume 2010 en 2025.','Voltijdbanen, geen personen; ontwikkeling over vijftien jaar.','2025-12-31'),
      'levensverhalen-psychische-behandeling':('UT beschrijft checklist en eerste evaluaties van Een sterk verhaal.','Vroege evaluaties bij persoonlijkheidsstoornissen; geen brede causaliteitsclaim.','2026-10-29'),
      'corvo-licht-uit-zeevogels':('Reportage beschrijft jaarlijkse verduistering en reddingsacties.','30.000 is meerjarig archipeltotaal, geen effectmeting van verduistering.','2026-10-30'),
      'siliconen-grondstof-terugwinnen':('TU Berlin publicatie beschrijft grondstofterugwinning uit gebruikte producten.','Laboratorium; giftig reagens en opschaling blijven opgaven.','2026-10-28'),
      'belfast-robot-complexe-operaties':('Ministerie bevestigt 130 complexe robotondersteunde operaties sinds mei.','Geen causaal bewijs dat robot alleen wachtlijsten verkort.','2026-11-02'),
      'china-mangroven-vogelsoorten':('Yale beschrijft 148 naar 397 geregistreerde soorten in 1998-2020.','Oorspronkelijke studie niet toegankelijk; aanplant/natuurlijke uitbreiding niet onderscheiden.','2020-12-31'),
      'esk-valley-samen-leven':('Reportage en gemeenschapwebsite bevestigen negentien huishoudens.','Ervaringsreportage, geen vergelijkende effectstudie; gemeenschap bestaat al langer.','2026-11-03'),
      'sensoren-groei-mais':('SDSU-verslag beschrijft kastest met tienminutenmetingen.','Geen veldresultaten, opbrengstwinst of mestbesparing aangetoond.','2026-11-03'),
    }
    reviews=[];triage=[]
    for section in ['nl','int','headlines']:
        for i,item in enumerate(news[section]):
            key=article_key(section,item,i);r=dossier['articles'][key]
            sid=item['source_id'];source=registered[sid]
            support,limitations,event=notes.get(item.get('article_slug'),('NOS-artikel rechtstreeks gelezen; actuele stand 4 november.','Op editiedag actualiseren.','2026-11-04'))
            verified=item.get('article_slug')!='china-mangroven-vogelsoorten'
            r.update(source_id=sid,organization_id=source['organization_id'],region=section if section!='headlines' else ('int' if i==0 else 'nl'),
                region_checked=True,publication_date=item['published'],event_date=event,checked_on=CHECKED,dates_checked=True,
                topic_id=item.get('article_slug') or f'actualiteit-{i}-{CHECKED}',
                new_development='Nieuw bronbericht over beschreven onderzoeksperiode of toepassing.' if event<item['published'] else '')
            r['evidence']=dict(primary_url=item.get('primary_url') or item['url'],claim=item['title'],support=support,limitations=limitations,verified=verified)
            exact=[d for d,u,t in history if u==canonical_url(item['url'])]
            r['duplicate_review']=dict(checked=True,reason='Bron-URLs vergeleken met 228 archiefverhalen; nieuwsfeiten vorige twee edities gelezen. Geen herhaling.' if not exact else 'URL-match: '+','.join(exact),new_fact='')
            image=cache.get(f'{DATE}/{item.get("article_slug")}')
            r['rights']=dict(text='original_summary',image='existing_licensed' if image else ('not_used' if section=='headlines' else ''),
                image_evidence=(image['page_url']+'; bestaande lokale Pixabay-cache; illustratief.') if image else ('Geen beeld bij actualiteit.' if section=='headlines' else 'Pixabay-ophaalstap en visuele controle nog open.'))
            if item.get('article_slug')=='siliconen-grondstof-terugwinnen':r['older_exception_reason']='Oorspronkelijk persbericht 28 oktober, acht dagen vóór editie; gekozen concreet resultaat, recent herontdekt via Goodnews.eu.'
            if section!='headlines':
                r.update(positive_result=True,positive_result_explanation='Gecontroleerd resultaat, nieuw inzicht of beschreven bestaande praktijk; stadium begrensd in artikel.',
                    scores=dict(positive_value=2,evidence=2 if verified else 1,recency=1 if item['published']<'2026-10-29' else 2,relevance=2,originality=2))
                reviews.append(dict(id=item['candidate_id'],region=section,decision='select',rank=i+1,article_url=item['url'],primary_url=item.get('primary_url') or item['url'],
                    source_read=True,scores=dict(reader_value=3 if i<3 or item['article_slug']=='esk-valley-samen-leven' else 2,concrete_result=2,evidence=2 if verified else 1,recency=1 if item['published']<'2026-10-29' else 3 if item['published']=='2026-11-04' else 2,originality=3 if item['article_slug'] in {'zonvarken-lagere-emissies','levensverhalen-psychische-behandeling','sensoren-groei-mais'} else 2),
                    reason='Eigenaar bevestigde deze selectie op 4 november na tweede review.',stronger_than_reserves=''))
                triage.append(dict(id=item['candidate_id'],decision='contender',reason='Door eigenaar bevestigde selectie; brononderzoek hierboven vastgelegd.'))
    dossier['news_sha256']=news_digest(news)
    dossier['approved']=False;dossier['approved_by']=''
    dossier['variation_exception_reason']=''
    dossier['production_status']='concept; 12 beeldkeuzes visueel bekeken en vastgezet; oorspronkelijke mangrovestudie, complete pooltriage, dekking, reserves, visuele paginacontrole en editiedagcontrole nog open'
    save(ROOT/'redactie'/f'{DATE}.json',dossier)
    review=json.loads((ROOT/'selectie'/f'{DATE}.json').read_text())
    review.update(reviewed_by='AI-redacteur; selectie bevestigd door Tom de Haas',triage=triage,article_reviews=reviews,
        owner_confirmed_selection=dict(confirmed_on=CHECKED,confirmed_by='Tom de Haas',full_pool_review_complete=False,coverage_complete=False),
        review_status='incomplete',open_items=['Bevroren bronrun is van 4 november, niet editiedag 5 november.','Overige kandidaten niet individueel inhoudelijk getriageerd.','Volledige coverage-checklist en drie gelezen reserves per regio ontbreken.','Oorspronkelijke mangrovestudie niet gelezen; secundaire samenvatting wel.','Beeldkeuzes visueel bekeken; paginacontrole in browser nog open.'])
    save(ROOT/'selectie'/f'{DATE}.json',review)

if __name__=='__main__':main()
