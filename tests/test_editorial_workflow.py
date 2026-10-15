import copy
import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch
import auto_news as news
import editorial_check as gate
import source_registry as registry
import buttondown_draft as buttondown

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.register=registry.load_registry()
        self.policy=json.loads((registry.ROOT/'editorial_policy.json').read_text())

    def fixture(self):
        edition={'meta':{'edition_date':'2026-10-12'},'nl':[],'int':[],'headlines':[]}
        dossier={'edition_date':'2026-10-12','approved':True,'approved_by':'UNIT TEST ONLY','articles':{}}
        sources=self.register['sources'][:15]
        themes=['Mens','Gezondheid','Wetenschap','Cultuur','Economie','Natuur & klimaat']
        number=0
        for section,count in self.policy['counts'].items():
            for i in range(count):
                source=sources[number];number+=1
                item={'title':f'UNIT TEST onderwerp {number}','teaser':'Technische testtekst, geen werkelijk nieuws.','source':source['name'],'url':f'https://example.invalid/story/{number}','article_slug':f'test-{number}','category':themes[i%6]}
                edition[section].append(item)
                dossier['articles'][gate.article_key(section,item,i)]={'source_id':source['source_id'],'organization_id':source['organization_id'],'article_url':item['url'],'region':section if section!='headlines' else 'nl','region_checked':True,'publication_date':'2026-10-12','event_date':'2026-10-12','checked_on':'2026-10-12','dates_checked':True,'topic_id':f'test-{number}','positive_result':True,'positive_result_explanation':'Alleen technische test, geen claim over werkelijkheid.','evidence':{'verified':True,'primary_url':f'https://example.invalid/evidence/{number}','claim':'Testclaim','support':'Synthetische testonderbouwing','limitations':'Alleen unit test'},'rights':{'text':'original_summary','image':'not_used'},'scores':{k:2 for k in ('positive_value','evidence','recency','relevance','originality')},'duplicate_review':{'checked':True,'reason':'Synthetische fixture heeft geen publicatiegeschiedenis.'}}
        dossier['news_sha256']=gate.news_digest(edition)
        return edition,dossier

    def check(self,edition,dossier,history=None):return gate.check(edition,dossier,self.policy,history or [],date(2026,10,13))

    def test_55_register_ids_and_no_duplicate_esa_feed(self):
        ids=[i for s in self.register['sources'] for i in s.get('register_ids',[])]
        self.assertEqual(len(ids),55);self.assertEqual(len(set(ids)),55)
        esa=next(s for s in self.register['sources'] if s['source_id']=='esa')
        self.assertEqual(len(esa['channels']),1)

    def test_unverified_new_channel_is_rejected(self):
        r=copy.deepcopy(self.register);s=r['sources'][0];s['channels'][0].update(origin='new',enabled=True,verification_status='pending')
        path=self.root/'sources.json';path.write_text(json.dumps(r))
        with self.assertRaises(ValueError):registry.load_registry(path)

    def test_url_queries_and_case_are_preserved(self):
        self.assertNotEqual(registry.canonical_url('https://x.invalid/Report?id=1'),registry.canonical_url('https://x.invalid/Report?id=2'))
        self.assertNotEqual(registry.canonical_url('https://x.invalid/Report'),registry.canonical_url('https://x.invalid/report'))
        self.assertEqual(registry.canonical_url('https://x.invalid/Report?id=1&utm_source=x'),registry.canonical_url('https://x.invalid/Report?id=1'))

    def test_updated_date_is_not_publication_date(self):
        items=news.parse_feed(b'<feed><entry><title>Test</title><link href="https://example.invalid/a"/><updated>2026-10-12T12:00:00Z</updated></entry></feed>')
        self.assertIsNone(items[0]['published']);self.assertIsNotNone(items[0]['updated'])

    def test_doi_or_query_distinguishes_history(self):
        history=[{'edition_date':'2026-10-08','url':'https://example.invalid/Report?id=1','doi':'10.test/one','title':'Old'}]
        self.assertFalse(registry.history_matches({'url':'https://example.invalid/Report?id=2'},history))
        self.assertTrue(registry.history_matches({'url':'https://example.invalid/new','doi':'10.test/one'},history))

    def test_valid_synthetic_fixture_is_ready(self):
        e,d=self.fixture();report=self.check(e,d)
        self.assertTrue(report['ready'],report['errors']);self.assertGreater(report['newsletter_words'],0)

    def test_changed_text_invalidates_approval(self):
        e,d=self.fixture();e['nl'][0]['title']='Changed';self.assertFalse(self.check(e,d)['ready'])

    def test_counts_cannot_be_silently_truncated(self):
        e,d=self.fixture();e['nl'].append(copy.deepcopy(e['nl'][0]));d['news_sha256']=gate.news_digest(e)
        self.assertTrue(any('exact 6' in x for x in self.check(e,d)['errors']))
        path=self.root/'nieuws.json';path.write_text(json.dumps(e))
        with patch.object(buttondown,'NEWS_FILE',path),self.assertRaises(ValueError):buttondown.load_news()

    def test_unknown_date_unverified_claim_rights_and_region_are_held(self):
        for field,value in [('publication_date',''),('region','int'),('positive_result',False)]:
            e,d=self.fixture();record=next(iter(d['articles'].values()));record[field]=value
            self.assertFalse(self.check(e,d)['ready'],field)
        for group,field,value in [('evidence','verified',False),('rights','image','copied_unlicensed')]:
            e,d=self.fixture();next(iter(d['articles'].values()))[group][field]=value
            self.assertFalse(self.check(e,d)['ready'])

    def test_future_and_old_dates_are_held(self):
        for value in ('2026-10-14','2026-09-01'):
            e,d=self.fixture();next(iter(d['articles'].values()))['publication_date']=value
            self.assertFalse(self.check(e,d)['ready'])

    def test_duplicate_history_requires_new_fact(self):
        e,d=self.fixture();history=[{**e['nl'][0],'edition_date':'2026-10-08'}]
        self.assertFalse(self.check(e,d,history)['ready'])
        next(iter(d['articles'].values()))['duplicate_review']['new_fact']='Test van een aantoonbare vervolgontwikkeling.'
        self.assertTrue(self.check(e,d,history)['ready'])

    def test_variation_requires_reason(self):
        e,d=self.fixture()
        for item in e['nl']+e['int']:item['category']='Mens'
        d['news_sha256']=gate.news_digest(e)
        self.assertFalse(self.check(e,d)['ready'])
        d['variation_exception_reason']='Alleen technische uitzonderingsfixture.'
        self.assertTrue(self.check(e,d)['ready'])

    def test_newsletter_word_budget_is_enforced(self):
        e,d=self.fixture();e['nl'][0]['teaser']='woord '*1300;d['news_sha256']=gate.news_digest(e)
        self.assertTrue(any('budget' in x for x in self.check(e,d)['errors']))

    def test_inspiration_is_not_monitored_and_german_query_has_locale(self):
        active=registry.active_channels(self.register)
        self.assertFalse(any(s['source_category']=='C' for s in active))
        query=news.google_site_feed('example.de','int','de')
        self.assertIn('ceid=DE:de',query);self.assertNotIn('Fortschritt',query)
        self.assertIn('Fortschritt',news.google_site_feed('example.de','int','de','positive'))

    def test_cache_and_failed_channel_retry(self):
        now=datetime(2026,10,13,12,tzinfo=timezone.utc)
        channel={'check_frequency':'weekly'}
        state={'last_success_at':'2026-10-12T12:00:00+00:00','last_error':None}
        self.assertFalse(registry.due(channel,state,now))
        state['last_error']='Timeout';self.assertTrue(registry.due(channel,state,now))

    def test_collector_retains_future_unknown_and_recovery_candidates_as_warnings(self):
        src=registry.active_channels(self.register)[0];src={**src,'mode':'rss','url':'https://example.invalid/feed'}
        xml=b'<rss><channel><item><title>Herstel na oorlog test</title><link>https://example.invalid/a</link><pubDate>Wed, 14 Oct 2026 12:00:00 GMT</pubDate></item><item><title>Onderzoek zonder datum test</title><link>https://example.invalid/b</link></item></channel></rss>'
        with patch.object(news,'STATE_PATH',self.root/'state.json'),patch.object(news,'fetch',return_value=xml):
            items,errors=news.collect(datetime(2026,10,13,12,tzinfo=timezone.utc),[src],[],True)
        self.assertFalse(errors);self.assertEqual(len(items),2)
        self.assertIn('future_publication_date',items[0]['date_warnings'])
        self.assertIn('negative_keyword_requires_context',items[0]['editorial_warnings'])
        self.assertIn('publication_date_unknown',items[1]['date_warnings'])

    def test_configured_image_cannot_be_marked_unused(self):
        e,d=self.fixture();e['nl'][0]['image_query']='forest';d['news_sha256']=gate.news_digest(e)
        self.assertTrue(any('beeld ingesteld' in x for x in self.check(e,d)['errors']))

    def test_unapproved_dossier_never_calls_buttondown_api(self):
        import os
        from contextlib import redirect_stderr
        import io
        e,d=self.fixture();d['approved']=False
        path=self.root/'nieuws.json';path.write_text(json.dumps(e))
        red=self.root/'redactie';red.mkdir();(red/'2026-10-12.json').write_text(json.dumps(d))
        before=Path.cwd()
        try:
            os.chdir(self.root)
            with patch.object(buttondown,'NEWS_FILE',path),patch.dict(os.environ,{'BUTTONDOWN_API_KEY':'unit-test-placeholder'}),patch.object(buttondown,'create_draft') as create,redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):buttondown.main()
                create.assert_not_called()
        finally:os.chdir(before)

    def test_shortlist_gives_other_organizations_a_place(self):
        pool=[]
        for org in range(22):
            for number in range(6):
                pool.append({'region':'nl','source':f'org-{org}','organization_id':f'org-{org}',
                    'title':f'uniekeorg{org} speciaalkandidaat{number} onderwerp{org}',
                    'category_hint':f'thema-{org%6}','signal_score':100-org,'source_weight':2,
                    'hours_old':1,'date_warnings':[]})
        chosen=news.shortlist(pool,'nl')
        self.assertGreaterEqual(len({x['organization_id'] for x in chosen}),20)
        self.assertEqual(len(chosen),40)
        self.assertEqual(news.category_hint('Vogels beschermen natuur',''), 'Natuur & klimaat')

    def test_archived_dossier_identifiers_are_used_for_future_duplicates(self):
        editions=self.root/'edities';editions.mkdir()
        redaction=self.root/'redactie';redaction.mkdir()
        (editions/'2026-10-08.json').write_text(json.dumps({'nl':[{'title':'Eerder bericht','url':'https://example.invalid/old','article_slug':'old'}]}))
        (redaction/'2026-10-08.json').write_text(json.dumps({'articles':{'nl:old':{'topic_id':'same-fact','doi':'10.test/one','evidence':{'primary_url':'https://example.invalid/research'}}}}))
        history=registry.load_history(editions)
        self.assertTrue(registry.history_matches({'url':'https://example.invalid/new','topic_id':'same-fact'},history))
        self.assertTrue(registry.history_matches({'url':'https://example.invalid/research'},history))

    def test_bad_feed_is_an_error_not_an_empty_success(self):
        src=registry.active_channels(self.register)[0];src={**src,'mode':'rss','url':'https://example.invalid/feed'}
        with patch.object(news,'STATE_PATH',self.root/'state.json'),patch.object(news,'fetch',return_value=b'<html>error</html>'):
            items,errors=news.collect(datetime(2026,10,13,12,tzinfo=timezone.utc),[src],[],True)
        self.assertTrue(errors);self.assertFalse(items)

if __name__=='__main__':unittest.main()
