import unittest
from unittest.mock import patch
from datetime import datetime, timezone
import fast_concept as fast

class FastConceptTests(unittest.TestCase):
    def test_pool_excludes_history_old_and_duplicate_urls(self):
        now = datetime(2026, 10, 24, tzinfo=timezone.utc)
        def row(key, url, published='2026-10-23T12:00:00+00:00'):
            return dict(id=key, url=url, published=published, source_id='test', region='nl', title='Een duidelijke nieuwstitel voor de test')
        rows = [row('ok', 'https://example.org/new'), row('dup', 'https://example.org/new?tracking=1'),
                row('history', 'https://example.org/old'), row('old', 'https://example.org/ancient', '2020-01-01T00:00:00+00:00'),
                row('search', 'https://news.google.com/rss/articles/opaque')]
        self.assertEqual([x['id'] for x in fast.pool_items({'all_candidates': rows}, now, {'example.org/old'})], ['ok', 'search'])
    def test_article_rejects_invented_evidence_or_numbers(self):
        text = 'Dit is een werkelijk gelezen bronpassage over een resultaat met 12 deelnemers.'
        article = dict(region='nl', region_reason='Nederland', title='Resultaat', teaser='Een resultaat',
                       article_body=['Eigen tekst ' * 70], evidence_quote=text)
        fast.validate_article(article, {'text': text}, 'nl')
        article['title'] = 'Resultaat voor 999 mensen'
        with self.assertRaises(ValueError): fast.validate_article(article, {'text': text}, 'nl')
        article['title'] = 'Resultaat'; article['evidence_quote'] = 'Dit staat helemaal niet in de oorspronkelijke bron.'
        with self.assertRaises(ValueError): fast.validate_article(article, {'text': text}, 'nl')
    def test_deadline_prevents_next_model_request(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from types import SimpleNamespace
        with TemporaryDirectory() as tmp, patch.object(fast, 'ROOT', Path(tmp)):
            runner = fast.Runner(SimpleNamespace(budget=0, model='test'))
            with patch('urllib.request.urlopen') as request:
                with self.assertRaises(TimeoutError): runner.ask('test', '', {}, 10)
                request.assert_not_called()

if __name__ == '__main__': unittest.main()

class WallClockTests(unittest.TestCase):
    def test_wall_clock_deadline_includes_machine_pause(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from types import SimpleNamespace
        with TemporaryDirectory() as tmp, patch.object(fast, 'ROOT', Path(tmp)):
            runner = fast.Runner(SimpleNamespace(budget=300, model='test'))
            runner.wall_start -= 600
            with patch('urllib.request.urlopen') as request:
                with self.assertRaises(TimeoutError): runner.ask('test', '', {}, 10)
                request.assert_not_called()

class RenderSafetyTests(unittest.TestCase):
    def test_preview_has_twelve_own_pages_external_headlines_and_no_scripts(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        import copy
        base = dict(title='Eigen conceptartikel', teaser='Een nieuwe ontwikkeling', article_body=['Eigen alinea.'], category='Mens', source='Testbron', url='https://example.org/source', image_query='')
        news = dict(meta=dict(edition_date='2026-10-24', status='CONCEPT', publication_authorized=False), nl=[], int=[], headlines=[])
        for region in ('nl', 'int'):
            for i in range(6):
                article = copy.deepcopy(base); article['article_slug'] = f'{region}-{i}'; news[region].append(article)
        news['headlines'] = [dict(title=f'Headline {i}', source='Bron', url=f'https://example.org/headline-{i}') for i in range(3)]
        with TemporaryDirectory() as tmp, patch('urllib.request.urlopen') as network:
            site = Path(tmp) / 'site'; fast.render(news, site)
            pages = list((site / 'artikelen').rglob('index.html'))
            self.assertEqual(len(pages), 12)
            for path in pages:
                markup = path.read_text()
                self.assertIn('class="source-button" href="https://example.org/source"', markup)
                self.assertIn('NIET GEPUBLICEERD', markup)
                self.assertNotIn('<script', markup)
                self.assertIn('Positief nieuws · Dit gebeurt ook.</div>', markup)
            index = (site / 'index.html').read_text()
            self.assertEqual(index.count('href="/artikelen/2026-10-24/'), 12)
            for i in range(3): self.assertIn(f'href="https://example.org/headline-{i}"', index)
            network.assert_not_called()
