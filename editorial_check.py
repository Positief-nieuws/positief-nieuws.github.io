#!/usr/bin/env python3
"""Fail-closed editorial gate. Creates no publication or Buttondown draft."""
import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from source_registry import ROOT, canonical_url, load_history, history_matches, load_registry

def news_digest(news):
    return hashlib.sha256(json.dumps(news,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def article_key(section, item, index):
    return section + ':' + str(item.get('article_slug') or index)

class VisibleText(HTMLParser):
    def __init__(self):super().__init__();self.hidden=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in {'style','script'}:self.hidden+=1
    def handle_endtag(self,tag):
        if tag in {'style','script'} and self.hidden:self.hidden-=1
    def handle_data(self,text):
        if not self.hidden:self.parts.append(text)

def newsletter_words(news):
    import buttondown_draft as bd
    parser=VisibleText()
    parser.feed(bd.build_body(news,news.get('nl',[]),news.get('int',[]),news.get('headlines',[])))
    return len(re.findall(r"\b[\wÀ-ÿ'-]+\b",' '.join(parser.parts)))

def valid_url(value):
    p=urlsplit(str(value or ''))
    return p.scheme in {'http','https'} and bool(p.hostname)

def check(news, dossier, policy=None, history=None, as_of=None, selection_review=None, candidate_pool=None):
    policy=policy or json.loads((ROOT/'editorial_policy.json').read_text(encoding='utf-8'))
    history=load_history() if history is None else history
    today=as_of or datetime.now(ZoneInfo(policy["timezone"])).date()
    errors,warnings=[],[]
    counts=policy['counts']
    edition=news.get('meta',{}).get('edition_date') or news.get('edition',{}).get('date')
    try:edition_day=date.fromisoformat(edition)
    except (ValueError,TypeError):edition_day=None;errors.append('Ongeldige editie-datum.')
    if edition_day and edition_day>today:errors.append('Editiedatum ligt in de toekomst; nog niet publicatieklaar.')
    if dossier.get('edition_date')!=edition:errors.append('Dossier hoort niet bij deze editie.')
    required_from=policy.get('selection_review_required_from')
    if required_from and edition_day and edition_day.isoformat()>=required_from:
        if selection_review is None or candidate_pool is None:
            errors.append('Selectiecontrole vóór eerste concept ontbreekt; volledige bronrun en selectiedossier zijn verplicht.')
        else:
            from selection_check import check_selection
            errors.extend('Selectiecontrole: '+message for message in check_selection(candidate_pool,selection_review,news)['errors'])

    if dossier.get('news_sha256')!=news_digest(news):errors.append('Dossier hoort niet bij deze exacte versie van nieuws.json.')
    if dossier.get('approved') is not True or not str(dossier.get('approved_by') or '').strip():
        errors.append('Expliciete redactionele goedkeuring ontbreekt.')
    entries=dossier.get('articles',{})
    seen_urls,seen_topics,seen_titles=set(),set(),set()
    themes,organizations=Counter(),Counter()
    older=0
    registered={s['source_id']:s for s in load_registry()['sources']}
    all_keys=[]
    for section,count in counts.items():
        items=news.get(section,[])
        if not isinstance(items,list) or len(items)!=count:
            errors.append(f'{section}: verwacht exact {count} berichten.');continue
        for index,item in enumerate(items):
            key=article_key(section,item,index);all_keys.append(key);record=entries.get(key,{})
            def fail(message):errors.append(key+': '+message)
            if not record:fail('redactioneel dossier ontbreekt.');continue
            if not str(item.get('title') or '').strip():fail('titel ontbreekt.')
            if not valid_url(item.get('url')) or record.get('article_url')!=item.get('url'):fail('controleerbare artikel-URL ontbreekt of wijkt af van dossier.')
            if not str(item.get('source') or '').strip():fail('zichtbare bronvermelding ontbreekt.')
            if (section!='headlines' and record.get('region')!=section) or record.get('region') not in {'nl','int'} or record.get('region_checked') is not True:fail('regio van het nieuwsfeit niet bevestigd.')
            if record.get('dates_checked') is not True:fail('datums niet gecontroleerd.')
            publication=None
            for field in ('publication_date','event_date','checked_on'):
                try:
                    d=date.fromisoformat(record.get(field,''))
                    if d>today:fail(f'{field} ligt in de toekomst.')
                    if field=='publication_date':publication=d
                except (ValueError,TypeError):fail(f'{field} ontbreekt of is ongeldig.')
            if publication and edition_day and publication>edition_day:fail('bron verscheen na de editie-datum.')
            if publication and record.get('checked_on','')<publication.isoformat():fail('broncontrole ligt vóór bronpublicatie.')
            if publication and edition_day and (edition_day-publication).days>policy['max_publication_age_days']:
                older+=1
                if not record.get('older_exception_reason'):fail('oude publicatie zonder gemotiveerde uitzondering.')
            if record.get('event_date','')<record.get('publication_date','') and not record.get('new_development'):
                fail('leg vast wat nu nieuw is bij een eerdere gebeurtenis/onderzoeksperiode.')
            evidence=record.get('evidence',{})
            if not valid_url(evidence.get('primary_url')):fail('oorspronkelijke bewijslink ontbreekt.')
            for field in ('claim','support','limitations'):
                if not str(evidence.get(field) or '').strip():fail('bewijsveld ontbreekt: '+field)
            if evidence.get('verified') is not True:fail('kernclaim niet geverifieerd.')
            sid=record.get('source_id')
            if sid not in registered:
                fail('bron-ID ontbreekt in centraal register; voeg bron toe of kies correcte bewijsbron.')
            elif registered[sid]['category']=='C':fail('inspiratiebron kan niet de feitelijke bewijsbron zijn.')
            rights=record.get('rights',{})
            if rights.get('text')!='original_summary':fail('originele eigen tekst niet bevestigd.')
            if rights.get('image') not in {'not_used','licensed','existing_licensed'}:fail('beeldrechten niet bevestigd.')
            if rights.get('image')=='not_used' and any(item.get(k) for k in ('image_query','image','image_url')):fail('beeld ingesteld maar rechtenstatus is not_used.')
            if rights.get('image') in {'licensed','existing_licensed'} and not str(rights.get('image_evidence') or '').strip():fail('bewijs van beeldrechten ontbreekt.')
            review=record.get('duplicate_review',{})
            if review.get('checked') is not True or not review.get('reason'):fail('historische dubbelcontrole niet vastgelegd.')
            topic=record.get('topic_id')
            if not topic:fail('onderwerp-ID ontbreekt.')
            elif topic in seen_topics:fail('dubbel onderwerp binnen editie.')
            seen_topics.add(topic)
            title=re.sub(r'\W+',' ',str(item.get('title','')).lower()).strip()
            if title in seen_titles:fail('dubbele titel binnen editie.')
            seen_titles.add(title)
            urls={canonical_url(item.get('url')),canonical_url(evidence.get('primary_url'))}
            if urls & seen_urls:fail('dezelfde artikel- of bewijs-URL meermaals in editie.')
            seen_urls.update(urls)
            # Same date is a re-review, older dates are publication history.
            historical=[h for h in history if h['edition_date']!=edition]
            matches=history_matches({**item,'primary_url':evidence.get('primary_url'),'topic_id':topic,'doi':record.get('doi'),'report_id':record.get('report_id')},historical)
            if matches and not review.get('new_fact'):fail('historisch nieuwsfeit/bron zonder gemotiveerde nieuwe ontwikkeling.')
            if section!='headlines':
                if record.get('positive_result') is not True or not record.get('positive_result_explanation'):fail('aantoonbare positieve ontwikkeling ontbreekt.')
                scores=record.get('scores',{})
                keys=('positive_value','evidence','recency','relevance','originality')
                if any(type(scores.get(k)) is not int or scores[k] not in (0,1,2) for k in keys):fail('ongeldige score (vijf gehele scores van 0–2).')
                elif sum(scores[k] for k in keys)<policy['minimum_score']:fail('score onder redactionele minimumgrens.')
                theme=item.get('category')
                if theme not in policy['allowed_categories']:fail('ongeldige hoofdcategorie.')
                themes[theme]+=1
                organization=record.get('organization_id')
                if not organization:fail('organisatie-ID ontbreekt.')
                elif sid in registered and organization!=registered[sid]['organization_id']:fail('organisatie-ID wijkt af van bronregister.')
                else:organizations[organization]+=1
    if len(all_keys)!=len(set(all_keys)):errors.append('Dubbele artikelsleutel/slug.')
    if set(entries)!=set(all_keys):errors.append('Dossier bevat ontbrekende of extra artikelen.')
    if older>policy['max_older_exceptions']:errors.append('Te veel uitzonderingen voor oudere publicaties.')
    variation=[]
    if len(themes)<policy['minimum_themes']:variation.append('minder dan vijf thema’s')
    if any(n>policy['max_stories_per_theme'] for n in themes.values()):variation.append('één thema domineert')
    if any(n>policy['max_stories_per_organization'] for n in organizations.values()):variation.append('één organisatie domineert')
    if variation:
        reason=dossier.get('variation_exception_reason')
        if not reason:errors.append('Spreiding vraagt redactionele uitzondering: '+', '.join(variation))
        else:warnings.append('Gemotiveerde spreidingsuitzondering: '+reason)
    words=0
    if all(isinstance(news.get(k),list) and len(news[k])==v for k,v in counts.items()):
        words=newsletter_words(news)
        if words>policy['newsletter_word_budget']:errors.append(f'Nieuwsbrief bevat {words} woorden; budget {policy["newsletter_word_budget"]}.')
    return {'ready':not errors,'edition_date':edition,'newsletter_words':words,'errors':errors,'warnings':warnings}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--news',default=str(ROOT/'nieuws.json'))
    parser.add_argument('--dossier')
    parser.add_argument('--report')
    args=parser.parse_args()
    news=json.loads(Path(args.news).read_text(encoding='utf-8'))
    edition=news.get('meta',{}).get('edition_date') or news.get('edition',{}).get('date')
    path=Path(args.dossier) if args.dossier else ROOT/'redactie'/f'{edition}.json'
    if not path.exists():raise SystemExit(f'Geen redactioneel dossier: {path}. Publicatie tegengehouden.')
    selection_path=ROOT/'selectie'/f'{edition}.json'
    pool_path=ROOT/'selectie'/f'{edition}-kandidaten.json'
    selection=json.loads(selection_path.read_text()) if selection_path.exists() else None
    pool=json.loads(pool_path.read_text()) if pool_path.exists() else None
    result=check(news,json.loads(path.read_text(encoding='utf-8')),selection_review=selection,candidate_pool=pool)
    rendered=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.report:Path(args.report).write_text(rendered,encoding='utf-8')
    print(rendered)
    raise SystemExit(0 if result['ready'] else 1)

if __name__=='__main__':main()
