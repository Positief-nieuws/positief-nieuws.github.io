#!/usr/bin/env python3
"""Editorial review before the first draft; validates records, never judges truth or publishes."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from source_registry import canonical_url, ROOT, atomic_json

AXES = ('reader_value', 'concrete_result', 'evidence', 'recency', 'originality')

def pool_digest(pool):
    return hashlib.sha256(json.dumps(pool,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def check_selection(pool, review, news=None, preferences=None):
    preferences = preferences or json.loads((ROOT/'selection_preferences.json').read_text())
    errors=[]
    candidates=pool.get('all_candidates',[])
    if not candidates: errors.append('Volledige kandidatenlijst ontbreekt; top40 is onvoldoende.')
    if review.get('pool_sha256') != pool_digest(pool): errors.append('Beoordeling hoort niet bij deze bronrun.')
    if review.get('preferences_sha256') != pool_digest(preferences): errors.append('Redactionele voorkeuren gewijzigd; beoordeel de selectie opnieuw.')
    if not review.get('reviewed_by'): errors.append('Naam/rol van beoordelaar ontbreekt.')
    edition=review.get('edition_date','')
    try:
        generated=datetime.fromisoformat(pool['meta']['generated_at'].replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Amsterdam')).date().isoformat()
        if generated != edition: errors.append('Bronrun is niet van de editiedag; haal bronnen opnieuw op.')
    except (KeyError,TypeError,ValueError):errors.append('Geldige datum van de bronrun ontbreekt.')
    ids={x['id'] for x in candidates}
    if len(ids)!=len(candidates):errors.append('Dubbele kandidaat-ID in bronrun.')
    additional=review.get('additional_candidates',[])
    for x in additional:
        if not x.get('id') or not x.get('url','').startswith('https://') or not x.get('discovery_reason'):
            errors.append('Aanvullend gevonden kandidaat mist ID, URL of herkomstreden.')
    all_by_id={x['id']:x for x in candidates+additional if x.get('id')}
    if len(all_by_id)!=len(candidates)+len(additional):errors.append('Aanvullende kandidaat-ID is niet uniek.')
    triage=review.get('triage',[])
    triage_by_id={x.get('id'):x for x in triage}
    if len(triage_by_id)!=len(triage) or set(triage_by_id)!=set(all_by_id):
        errors.append('Niet iedere kandidaat is eenmalig beoordeeld; lees ook buiten de shortlist.')
    for x in triage:
        if x.get('decision') not in {'reject','contender'} or not x.get('reason','').strip():
            errors.append('Triage bevat onbesliste kandidaten of ontbrekende redenen.');break
    tasks={x['id'] for x in pool.get('coverage',{}).get('tasks',[])}
    coverage=review.get('coverage_checks',[])
    checked={x.get('id'):x for x in coverage}
    if len(checked)!=len(coverage) or set(checked)!=tasks:errors.append('Brondekking: controleer alle zoekkanalen, lege/mislukte kanalen en handmatige bewijsbronnen.')
    for x in coverage:
        if x.get('status')!='checked' or x.get('checked_on')!=edition or not x.get('url','').startswith('https://') or not x.get('finding','').strip():
            errors.append('Brondekking bevat openstaande controles; HTTP-succes alleen is onvoldoende.');break
    contenders={x['id'] for x in triage if x.get('decision')=='contender'}
    records=review.get('article_reviews',[])
    reviews={x.get('id'):x for x in records}
    if len(reviews)!=len(records) or set(reviews)!=contenders:errors.append('Niet alle kanshebbers zijn inhoudelijk vergeleken.')
    selected={'nl':[],'int':[]}; reserves={'nl':[],'int':[]}
    for key,x in reviews.items():
        label=all_by_id.get(key,{}).get('title',key)
        scores=x.get('scores',{})
        if set(scores)!=set(AXES) or any(type(scores.get(a)) is not int or not 0<=scores[a]<=3 for a in AXES):
            errors.append(f'{label}: vul vijf redactionele scores van 0–3 in.');continue
        if x.get('region') not in selected or x.get('decision') not in {'select','reserve','reject'}:
            errors.append(f'{label}: regio of eindbesluit ontbreekt.');continue
        if not x.get('reason') or not x.get('primary_url','').startswith('https://') or x.get('source_read') is not True:
            errors.append(f'{label}: oorspronkelijke bron niet gelezen of afweging ontbreekt.')
        if x['decision']=='select':
            selected[x['region']].append(x)
            if sum(scores.values())<preferences['selected_minimum_total'] or any(scores[a]<v for a,v in preferences['selected_minimum_axes'].items()):
                errors.append(f'{label}: onvoldoende positieve lezerswaarde, resultaat of bewijs.')
            if not x.get('stronger_than_reserves'):errors.append(f'{label}: vergelijking met reserves ontbreekt.')
        if x['decision']=='reserve':reserves[x['region']].append(x)
    for region in selected:
        if len(selected[region])!=6:errors.append(f'{region}: selecteer precies zes sterke verhalen.')
        if len(reserves[region])<preferences['minimum_reserves_per_region']:errors.append(f'{region}: vergelijk ten minste drie inhoudelijk gelezen reserves.')
        ranks=[x.get('rank') for x in selected[region]]
        if sorted(ranks,key=lambda x:(type(x) is not int,str(x)))!=list(range(1,7)):errors.append(f'{region}: rangschik de zes verhalen van 1 tot 6.')
    if news:
        if news.get('meta',{}).get('edition_date')!=edition:errors.append('Selectiedossier en editie hebben verschillende datums.')
        for region in selected:
            ordered=sorted(selected[region],key=lambda x:x.get('rank') if type(x.get('rank')) is int else 99)
            expected=[canonical_url(x.get('article_url') or all_by_id.get(x['id'],{}).get('url')) for x in ordered]
            actual=[canonical_url(x.get('url')) for x in news.get(region,[])]
            if expected!=actual:errors.append(f'{region}: concept wijkt af van de inhoudelijk beoordeelde selectie/volgorde.')
    return {'ready':not errors,'edition_date':edition,'candidates':len(candidates),'triaged':len(triage),'errors':errors}

def prepare(pool, edition):
    return {'schema_version':1,'edition_date':edition,'pool_sha256':pool_digest(pool),'preferences_sha256':pool_digest(json.loads((ROOT/'selection_preferences.json').read_text())),'reviewed_by':'',
            'coverage_checks':[dict(x,status='pending',checked_on='',url='',finding='') for x in pool.get('coverage',{}).get('tasks',[])],
            'additional_candidates':[], 'triage':[{'id':x['id'],'decision':'pending','reason':''} for x in pool.get('all_candidates',[])], 'article_reviews':[]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pool',default=str(ROOT/'kandidaten.json'));parser.add_argument('--review');parser.add_argument('--prepare',metavar='YYYY-MM-DD');parser.add_argument('--report')
    args=parser.parse_args();pool=json.loads(Path(args.pool).read_text())
    if args.prepare:
        target=Path(args.review or ROOT/'selectie'/f'{args.prepare}.json')
        snapshot=target.with_name(f'{args.prepare}-kandidaten.json')
        if target.exists() or snapshot.exists():raise SystemExit('Bestaande beoordeling/snapshot wordt niet overschreven. Kies een nieuwe revisiemap.')
        target.parent.mkdir(parents=True,exist_ok=True);atomic_json(snapshot,pool);atomic_json(target,prepare(pool,args.prepare));print(f'Onbeoordeelde checklist: {target}; bevroren bronrun: {snapshot}');return
    if not args.review:parser.error('--review is verplicht voor controle')
    result=check_selection(pool,json.loads(Path(args.review).read_text()))
    if args.report:atomic_json(Path(args.report),result)
    print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['ready'] else 1)

if __name__=='__main__':main()
