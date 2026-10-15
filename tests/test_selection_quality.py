import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import auto_news as collector
import editorial_check
import selection_check as selection

class SelectionTests(unittest.TestCase):
    def fixture(self):
        items=[{'id':str(i),'title':f'Testartikel {i}','url':f'https://example.invalid/{i}'} for i in range(18)]
        pool={'meta':{'generated_at':'2026-10-19T07:00:00+02:00'},'all_candidates':items,'coverage':{'tasks':[{'id':'search','source_id':'test','reasons':['search_is_not_complete']}]}}
        review=selection.prepare(pool,'2026-10-19');review['reviewed_by']='Synthetische testredacteur'
        review['coverage_checks']=[{'id':'search','status':'checked','checked_on':'2026-10-19','url':'https://example.invalid/news','finding':'Alleen test: officiële nieuwspagina gecontroleerd.'}]
        review['triage']=[{'id':x['id'],'decision':'contender','reason':'Synthetische testkandidaat.'} for x in items]
        review['article_reviews']=[]
        for i,x in enumerate(items):
            pos=i%9;review['article_reviews'].append({'id':x['id'],'region':'nl' if i<9 else 'int','decision':'select' if pos<6 else 'reserve','rank':pos+1 if pos<6 else None,'scores':{a:3 for a in selection.AXES},'primary_url':x['url'],'source_read':True,'reason':'Technische fixture, geen echte bronclaim.','stronger_than_reserves':'Vergelijking uitsluitend voor deze synthetische test.'})
        return pool,review

    def test_valid_review_is_ready(self):
        p,r=self.fixture();self.assertTrue(selection.check_selection(p,r)['ready'])

    def test_first_draft_requires_review_outside_the_shortlist(self):
        p,r=self.fixture();r['triage'].pop();self.assertFalse(selection.check_selection(p,r)['ready'])

    def test_shortlist_without_full_pool_is_not_enough(self):
        p,r=self.fixture();p.pop('all_candidates');r['pool_sha256']=selection.pool_digest(p)
        self.assertFalse(selection.check_selection(p,r)['ready'])

    def test_changed_pool_or_profile_invalidates_review(self):
        p,r=self.fixture();p['all_candidates'][0]['title']='Nieuwe kop'
        self.assertFalse(selection.check_selection(p,r)['ready'])
        p,r=self.fixture();prefs=json.loads((selection.ROOT/'selection_preferences.json').read_text());prefs['updated_on']='2026-10-20'
        self.assertFalse(selection.check_selection(p,r,preferences=prefs)['ready'])

    def test_open_source_coverage_blocks_first_draft(self):
        p,r=self.fixture();r['coverage_checks'][0]['status']='pending'
        self.assertFalse(selection.check_selection(p,r)['ready'])

    def test_routine_or_weak_positive_value_cannot_be_compensated_by_recency(self):
        p,r=self.fixture();r['article_reviews'][0]['scores']['concrete_result']=1
        self.assertFalse(selection.check_selection(p,r)['ready'])

    def test_reserves_must_be_read_and_compared(self):
        p,r=self.fixture();r['article_reviews'][6]['source_read']=False
        self.assertFalse(selection.check_selection(p,r)['ready'])
        p,r=self.fixture();r['article_reviews'][0].pop('stronger_than_reserves')
        self.assertFalse(selection.check_selection(p,r)['ready'])

    def test_concept_must_match_reviewed_order_and_region(self):
        p,r=self.fixture();news={'meta':{'edition_date':'2026-10-19'},'nl':p['all_candidates'][:6],'int':p['all_candidates'][9:15]}
        self.assertTrue(selection.check_selection(p,r,news)['ready'])
        news['nl'].reverse();self.assertFalse(selection.check_selection(p,r,news)['ready'])

    def test_prepare_does_not_approve_or_choose(self):
        p,r=self.fixture();pending=selection.prepare(p,'2026-10-19')
        self.assertFalse(selection.check_selection(p,pending)['ready'])
        self.assertTrue(all(x['decision']=='pending' for x in pending['triage']))

    def test_search_no_longer_requires_an_optimistic_keyword(self):
        q=parse_qs(urlsplit(collector.google_site_feed('tue.nl','nl')).query)['q'][0]
        self.assertEqual(q,'site:tue.nl when:7d')

    def test_substrings_do_not_create_false_signal_or_war_warning(self):
        self.assertFalse(collector.contains('Award moves research forward',['war']))
        self.assertEqual(collector.cue_score('Herstelling in een woord zonder echt signaal','','nl'),0)
        self.assertTrue(collector.contains('Recovery after war',['war']))

    def test_research_about_forecasts_is_retained_and_only_flagged(self):
        src={**collector.SOURCES[0],'mode':'rss','url':'https://example.invalid/feed'}
        xml=b'<rss><channel><item><title>Researchers improve weather forecast accuracy</title><link>https://example.invalid/weather</link><pubDate>Mon, 19 Oct 2026 05:00:00 GMT</pubDate></item></channel></rss>'
        with tempfile.TemporaryDirectory() as td,patch.object(collector,'STATE_PATH',Path(td)/'state.json'),patch.object(collector,'fetch',return_value=xml):
            items,errors=collector.collect(datetime(2026,10,19,6,tzinfo=timezone.utc),[src],[],True)
        self.assertEqual(len(items),1);self.assertFalse(errors)
        self.assertIn('possible_non_story_requires_review',items[0]['editorial_warnings'])

    def test_manual_sources_are_not_misreported_as_monitored(self):
        reg={'sources':[{'source_id':'manual','enabled':True,'category':'A','check_frequency':'manual'}]}
        self.assertEqual(collector.coverage_report({},reg)['tasks'][0]['id'],'manual:manual')

    def test_main_exports_zero_signal_overflow_without_approval(self):
        items=[{'id':str(i),'source_id':f'source{i}','source':f'Source {i}','region':'nl','title':f'bericht{chr(97+i//26)}{chr(97+i%26)} onderwerp{chr(97+i//26)}{chr(97+i%26)}','url':f'https://example.invalid/{i}','category_hint':'Mens','signal_score':0,'source_weight':1,'hours_old':1,'date_warnings':[]} for i in range(60)]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'sources.json').write_text('{"schema_version":1,"sources":[]}')
            with patch.object(collector,'ROOT',root),patch.object(collector,'OUTPUT',root/'kandidaten.json'),patch.object(collector,'HEALTH_PATH',root/'health.json'),patch.object(collector,'STATE_PATH',root/'state.json'),patch.object(collector,'load_registry',return_value={'sources':[]}),patch.object(collector,'collect',return_value=(items,[])),patch.object(collector,'add_reading_times'):
                collector.main()
            output=json.loads((root/'kandidaten.json').read_text())
            self.assertEqual(len(output['nl_candidates']),40);self.assertEqual(len(output['all_candidates']),60)
            self.assertFalse(output['meta']['editorial_coverage_complete'])
            self.assertNotIn('approved',output)

    def test_next_edition_requires_selection_gate(self):
        policy=json.loads((selection.ROOT/'editorial_policy.json').read_text())
        result=editorial_check.check({'meta':{'edition_date':'2026-10-19'}},{},policy,[],datetime(2026,10,19).date())
        self.assertTrue(any('Selectiecontrole' in error for error in result['errors']))

if __name__=='__main__':unittest.main()
