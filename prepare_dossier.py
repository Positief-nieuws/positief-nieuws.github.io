#!/usr/bin/env python3
"""Create an unapproved editorial checklist without inventing evidence."""
import argparse
import json
from pathlib import Path
from editorial_check import news_digest, article_key
from source_registry import load_registry

def skeleton(news):
    edition=news.get('meta',{}).get('edition_date') or news.get('edition',{}).get('date')
    sources=load_registry()['sources']
    record={'schema_version':1,'edition_date':edition,'news_sha256':news_digest(news),
        'approved':False,'approved_by':'','variation_exception_reason':'','articles':{}}
    for section in ('nl','int','headlines'):
        for index,item in enumerate(news.get(section,[])):
            # Exact source names only; composite/ambiguous labels need human choice.
            matches=[s for s in sources if (item.get('source_id') and s['source_id']==item['source_id']) or (not item.get('source_id') and s['name'].casefold()==str(item.get('source','')).casefold())]
            source=matches[0] if len(matches)==1 else None
            entry={'source_id':source['source_id'] if source else '',
                'organization_id':source['organization_id'] if source else '',
                'article_url':item.get('url',''),'region':section if section!='headlines' else '',
                'region_checked':False,'publication_date':str(item.get('published') or '')[:10],'event_date':str(item.get('event_date') or '')[:10],'checked_on':'',
                'dates_checked':False,'new_development':'','older_exception_reason':'',
                'topic_id':'','doi':'','report_id':'',
                'evidence':{'primary_url':item.get('primary_url',''),'claim':'','support':'','limitations':'','verified':False},
                'rights':{'text':'','image':'','image_evidence':''},
                'duplicate_review':{'checked':False,'reason':'','new_fact':''}}
            if section!='headlines':entry.update(positive_result=None,positive_result_explanation='',
                scores={k:None for k in ('positive_value','evidence','recency','relevance','originality')})
            record['articles'][article_key(section,item,index)]=entry
    return record

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--news',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();path=Path(args.output)
    if path.exists():raise SystemExit('Bestaand dossier wordt niet overschreven.')
    news=json.loads(Path(args.news).read_text(encoding='utf-8'))
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(skeleton(news),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Ongeaccordeerd dossier: {path}')

if __name__=='__main__':main()
