import unittest
from pathlib import Path
from tip_invitation import apply_home, apply_article, block

class TipInvitationTests(unittest.TestCase):
    def test_static_home_and_article_idempotence(self):
        for func, marker, placement in (
            (apply_home, '<!-- social-share:home:end -->', 'home'),
            (apply_article, '<p class="article-back">Terug</p>', 'article'),
        ):
            original = '<article>Oorspronkelijke tekst</article>' + marker
            result = func(original)
            self.assertIn('Oorspronkelijke tekst', result)
            self.assertEqual(result.count('class="pn-tip-invitation"'), 1)
            self.assertIn('href="/tip/"', result)
            self.assertIn("placement:'" + placement + "'", result)
            self.assertEqual(func(result), result)
    def test_public_tip_page_needs_no_backend(self):
        markup = Path('tip/index.html').read_text(encoding='utf-8')
        self.assertIn('mailto:redactie@positief-nieuws.nl', markup)
        self.assertIn('niet verplicht', markup)
        self.assertIn('niets automatisch verstuurd', markup)
    def test_future_article(self):
        from build_editions import render_article_page
        item = {'title':'Goed nieuws', 'article_slug':'voorbeeld', 'article_body':['Een verhaal.'], 'category':'Mens', 'url':'https://example.org/'}
        page = render_article_page(item, '2026-11-23')
        self.assertIn(block('article'), page)
        self.assertLess(page.index('class="article-newsletter"'), page.index('class="pn-tip-invitation"'))
